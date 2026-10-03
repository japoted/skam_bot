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
    """Хендлер NicePay: GET ?result=success&payment_id=..&order_id=..&amount=..&hash=..

    По доке https://nicepay.io/docs/merchant/handler hash = sha256(sorted values + secret).
    """
    bot: Bot = request.app["bot"]
    try:
        # NicePay шлёт GET с query-параметрами
        q = dict(request.query)
        try:
            body = await request.json()
            if not isinstance(body, dict):
                body = {}
        except Exception:
            try:
                form = await request.post()
                body = dict(form)
            except Exception:
                body = {}
        payload = {**body, **q}
        logger.info(f"NicePay webhook payload: {payload}")

        order_id_str = (
            q.get("order_id") or q.get("orderId")
            or body.get("order_id") or body.get("orderId")
        )
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

        # только success выдаём
        result = str(payload.get("result", "success")).lower()
        if result not in ("success", "paid"):
            logger.warning(f"NicePay webhook order #{order_id}: result={result}, игнор")
            return web.json_response({"status": "ok", "message": f"ignored {result}"})

        # проверка hash обязательна
        if not verify_nicepay_sign(payload):
            logger.warning(f"NicePay webhook order #{order_id}: bad hash")
            return web.json_response({"status": "error", "message": "invalid hash"}, status=403)

        paid = nicepay_webhook_amount(payload)
        if paid and paid != order["price"]:
            logger.warning(f"NicePay webhook order #{order_id}: amount mismatch paid={paid} expected={order['price']} (автовыдача всё равно выполняется)")

        await _deliver_nicepay_payment(bot, order_id, "webhook", payload)
        # по примеру PHP отвечаем {"result": {"message": "Success"}}
        return web.json_response({"result": {"message": "Success"}})
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
    """У мерчанта нет H2H-доступа, polling недоступен — автовыдача только через webhook.

    Оставляем задачу живой для bothost, но ничего не опрашиваем.
    """
    logger.info("NicePay auto-check disabled (no H2H access) — delivery via webhook only")
    while True:
        try:
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            break


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
