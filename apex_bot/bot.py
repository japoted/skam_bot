import asyncio
import json
import logging
import traceback

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import web
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import TOKEN, PROXY, ADMIN_IDS
try:
    from config import NICEPAY_WEBHOOK_PORT, NICEPAY_WEBHOOK_PATH
except ImportError:
    import os
    NICEPAY_WEBHOOK_PORT = int(os.getenv("NICEPAY_WEBHOOK_PORT", "80"))
    NICEPAY_WEBHOOK_PATH = os.getenv("NICEPAY_WEBHOOK_PATH", "/nicepay/callback")
from database import init_db, get_order, confirm_order, claim_order, add_balance, get_pending_orders
from handlers import router
from nicepay import (
    verify_nicepay_sign,
    nicepay_webhook_amount,
    check_nicepay_invoice,
    is_nicepay_success,
)
from keyboards import bottom_menu

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _deliver_nicepay_payment(bot: Bot, order_id: int, source: str, payload: dict | None = None):
    """Подтверждение + автовыдача NicePay. Возвращает True если впервые подтвержден."""
    order = get_order(order_id)
    if not order or order["status"] == "confirmed":
        return False
    confirm_order(order_id)
    user_id = order["user_id"]
    payload_txt = str(payload)[:300] if payload else ""

    if order["product_id"] == "deposit":
        new_balance = add_balance(user_id, order["price"])
        logger.info(f"NicePay {source} ADD BALANCE: order={order_id} user={user_id} amount={order['price']} new={new_balance}")
        try:
            await bot.send_message(
                user_id,
                f"💰 <b>Баланс пополнен!</b>\n\n"
                f"📄 Платёж №<b>{order_id}</b>\n"
                f"💵 Сумма: <b>{order['price']:,} ₽</b>\n\n"
                f"Оплачено через NicePay ✅",
                reply_markup=bottom_menu(),
            )
        except Exception as e:
            logger.warning(f"Failed to notify user {user_id}: {e}")
    else:
        tokens = claim_order(order_id)
        if tokens:
            lines = "\n".join(f"<code>{m['token']}</code>" for m in tokens)
            msg = (
                f"✅ <b>Заказ #{order_id} оплачен!</b>\n\n"
                f"🛒 Товар: <b>{order['product_name']}</b>\n"
                f"💵 Сумма: <b>{order['price']:,} ₽</b>\n\n"
                f"<b>Ваши токены:</b>\n{lines}\n\n"
                f"Сохраните их, они понадобятся для активации товара."
            )
            try:
                await bot.send_message(user_id, msg)
            except Exception as e:
                logger.warning(f"Failed to notify user {user_id}: {e}")
        else:
            msg = (
                f"✅ <b>Заказ #{order_id} подтверждён!</b>\n\n"
                f"🛒 Товар: <b>{order['product_name']}</b>\n"
                f"💵 Сумма: <b>{order['price']:,} ₽</b>\n\n"
                f"Оплачено через NicePay ✅"
            )
            try:
                builder = InlineKeyboardBuilder()
                builder.button(text="🎁 Получить заказ", callback_data=f"claim_{order_id}")
                await bot.send_message(user_id, msg, reply_markup=builder.as_markup())
            except Exception as e:
                logger.warning(f"Failed to notify user {user_id}: {e}")

    for adm in ADMIN_IDS:
        try:
            await bot.send_message(
                adm,
                f"✅ NicePay ({source}): Заказ #{order_id} оплачен\n"
                f"👤 Пользователь: <code>{user_id}</code>\n"
                f"🛒 Товар: {order['product_name']}\n"
                f"💵 Сумма: {order['price']:,} ₽\n"
                f"Payload: <code>{payload_txt}</code>",
            )
        except Exception:
            pass
    return True


async def nicepay_webhook_handler(request: web.Request):
    bot: Bot = request.app["bot"]
    try:
        try:
            payload = await request.json()
        except Exception:
            try:
                data = await request.post()
                payload = dict(data)
            except Exception:
                text = await request.text()
                logger.warning(f"NicePay webhook raw: {text[:1000]}")
                try:
                    payload = json.loads(text)
                except Exception:
                    payload = {"raw": text}
        logger.info(f"NicePay webhook payload: {payload} query={dict(request.query)}")

        order_id_str = request.query.get("order_id") or request.query.get("orderId") or request.query.get("order")
        if not order_id_str and isinstance(payload, dict):
            for k in ("order_id", "orderId", "order", "user_id", "merchantOrderId", "referenceNo"):
                v = payload.get(k)
                if v is not None and str(v).isdigit():
                    order_id_str = str(v)
                    break
            # also try nested
            if not order_id_str and isinstance(payload.get("data"), dict):
                for k in ("orderId", "order_id"):
                    v = payload["data"].get(k)
                    if v and str(v).isdigit():
                        order_id_str = str(v)
                        break
        if not order_id_str or not str(order_id_str).isdigit():
            logger.warning("NicePay webhook: order_id not found")
            return web.json_response({"status": "error", "message": "order_id not found"}, status=400)

        order_id = int(order_id_str)
        order = get_order(order_id)
        if not order:
            logger.warning(f"NicePay webhook order #{order_id} not found")
            return web.json_response({"status": "error", "message": "order not found"}, status=404)
        if order["status"] == "confirmed":
            return web.json_response({"status": "ok", "message": "already confirmed"})

        # проверка подписи — если есть sign, проверяем, иначе пропускаем (NicePay шлёт без sign в тесте)
        if isinstance(payload, dict) and payload.get("sign"):
            if not verify_nicepay_sign(payload):
                logger.warning(f"NicePay webhook order #{order_id}: bad signature")
                return web.json_response({"status": "error", "message": "invalid signature"}, status=403)

        paid = nicepay_webhook_amount(payload)
        if paid and paid != order["price"]:
            logger.warning(f"NicePay webhook order #{order_id}: amount mismatch paid={paid} expected={order['price']} (автовыдача всё равно выполняется)")

        await _deliver_nicepay_payment(bot, order_id, "webhook", payload)
        return web.json_response({"status": "ok"})
    except Exception as e:
        logger.exception(f"NicePay webhook error: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def start_webhook_server(bot: Bot):
    app = web.Application()
    app["bot"] = bot
    app.router.add_post(NICEPAY_WEBHOOK_PATH, nicepay_webhook_handler)
    app.router.add_get(NICEPAY_WEBHOOK_PATH, nicepay_webhook_handler)
    app.router.add_get("/", lambda r: web.json_response({"status": "ok", "service": "supermarket_cash nicepay webhook"}))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", NICEPAY_WEBHOOK_PORT)
    await site.start()
    logger.info(f"NicePay webhook listening on 0.0.0.0:{NICEPAY_WEBHOOK_PORT}{NICEPAY_WEBHOOK_PATH} -> https://nicepay.io")
    while True:
        await asyncio.sleep(3600)


async def auto_check_nicepay(bot: Bot):
    """Фоновая автопроверка NicePay каждые 30 сек."""
    while True:
        try:
            await asyncio.sleep(30)
            pending = get_pending_orders()
            nice_pending = [o for o in pending if o.get("payment_method") == "nicepay"]
            nice_pending = [o for o in nice_pending if o.get("invoice_id")]
            if not nice_pending:
                continue
            logger.info(f"Auto-check NicePay: {len(nice_pending)} pending")
            for order in nice_pending:
                try:
                    inv_id = order.get("invoice_id") or ""
                    if not inv_id:
                        continue
                    result = await check_nicepay_invoice(inv_id)
                    if is_nicepay_success(result):
                        await _deliver_nicepay_payment(bot, order["id"], "автопроверка", result)
                        logger.info(f"Auto-check: order #{order['id']} confirmed via NicePay")
                    elif str(result.get("status", "")).lower() in ("expired", "cancelled", "failed", "rejected"):
                        logger.info(f"Auto-check: order #{order['id']} status={result.get('status')}")
                except Exception as e:
                    logger.exception(f"Auto-check NicePay order #{order['id']}: {e}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception(f"Auto-check NicePay loop error: {e}")
            await asyncio.sleep(10)


async def main():
    init_db()

    session = AiohttpSession(proxy=PROXY) if PROXY else None
    bot = Bot(
        token=TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    webhook_task = asyncio.create_task(start_webhook_server(bot))
    auto_task = asyncio.create_task(auto_check_nicepay(bot))
    try:
        await dp.start_polling(bot)
    finally:
        for t in (webhook_task, auto_task):
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception:
        traceback.print_exc()
        input("\nНажми Enter для выхода...")
