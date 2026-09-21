import asyncio
import json
import logging
import traceback

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import web

from config import TOKEN, PROXY, ADMIN_IDS
# Совместимость: если на хосте старый config.py без NicePay — не падать с ImportError
try:
    from config import NICEPAY_WEBHOOK_PORT, NICEPAY_WEBHOOK_PATH, NICEPAY_SECRET
except ImportError:
    import os
    NICEPAY_WEBHOOK_PORT = int(os.getenv("NICEPAY_WEBHOOK_PORT", "8080"))
    NICEPAY_WEBHOOK_PATH = os.getenv("NICEPAY_WEBHOOK_PATH", "/nicepay/callback")
    NICEPAY_SECRET = os.getenv("NICEPAY_SECRET", "")
from database import init_db, get_order, confirm_order, claim_order, add_balance, get_pending_orders
from handlers import router
from nicepay import extract_nicepay_order_id, check_nicepay_payment, is_nicepay_success
from keyboards import bottom_menu
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def nicepay_webhook_handler(request: web.Request):
    bot: Bot = request.app["bot"]
    try:
        # NicePay может слать JSON или form-urlencoded
        try:
            payload = await request.json()
        except Exception:
            try:
                data = await request.post()
                payload = dict(data)
            except Exception:
                text = await request.text()
                logger.warning(f"NicePay webhook raw text: {text[:1000]}")
                try:
                    payload = json.loads(text)
                except Exception:
                    payload = {"raw": text}
        logger.info(f"NicePay webhook payload: {payload}")

        order_id_str = extract_nicepay_order_id(payload)
        if not order_id_str:
            order_id_str = request.query.get("order_id") or request.query.get("orderId")
        if not order_id_str:
            logger.warning(f"NicePay webhook: order_id not found. Payload keys: {list(payload.keys()) if isinstance(payload, dict) else type(payload)}")
            return web.json_response({"status": "error", "message": "order_id not found"}, status=400)

        order_id = None
        if str(order_id_str).isdigit():
            order_id = int(order_id_str)
        else:
            for nested_key in ("data", "payment", "result", "payload", "metadata", "extra"):
                if isinstance(payload, dict) and nested_key in payload and isinstance(payload[nested_key], dict):
                    inner = payload[nested_key]
                    for k in ("order_id", "orderId", "id"):
                        if k in inner and str(inner[k]).isdigit():
                            order_id = int(inner[k])
                            break
                if order_id:
                    break
            if not order_id:
                for k in ("order_id", "orderId"):
                    v = request.query.get(k)
                    if v and str(v).isdigit():
                        order_id = int(v)
                        break
        if not order_id:
            logger.warning(f"NicePay webhook: could not extract numeric order_id. order_id_str={order_id_str} payload_keys={list(payload.keys()) if isinstance(payload, dict) else 'N/A'}")
            return web.json_response({"status": "error", "message": "invalid order_id"}, status=400)

        order = get_order(order_id)
        if not order:
            logger.warning(f"NicePay webhook order #{order_id} not found")
            return web.json_response({"status": "error", "message": "order not found"}, status=404)

        if order["status"] == "confirmed":
            logger.info(f"NicePay webhook order #{order_id} already confirmed")
            return web.json_response({"status": "ok", "message": "already confirmed"})

        # TODO: проверка подписи по NICEPAY_SECRET если NicePay шлет signature
        # Сейчас эвристика: любой webhook считаем успешной оплатой, т.к. NicePay вызывает webhook только при успехе
        # Можно добавить проверку amount если payload содержит сумму

        confirm_order(order_id)
        user_id = order["user_id"]

        if order["product_id"] == "deposit":
            new_balance = add_balance(user_id, order["price"])
            logger.info(f"NicePay webhook ADD BALANCE: user_id={user_id} amount={order['price']} new_balance={new_balance}")
            msg = (
                f"💰 <b>Баланс пополнен!</b>\n\n"
                f"📄 Платёж №<b>{order_id}</b>\n"
                f"💵 Сумма: <b>{order['price']:,} ₽</b>\n\n"
                f"Оплачено через NicePay ✅"
            )
            try:
                await bot.send_message(user_id, msg, reply_markup=bottom_menu())
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
            else:
                msg = (
                    f"✅ <b>Заказ #{order_id} подтверждён!</b>\n\n"
                    f"🛒 Товар: <b>{order['product_name']}</b>\n"
                    f"💵 Сумма: <b>{order['price']:,} ₽</b>\n\n"
                    f"Оплачено через NicePay ✅"
                )
            # кнопка получить если токен еще не выдан — альтернатива
            try:
                if tokens:
                    await bot.send_message(user_id, msg)
                else:
                    builder = InlineKeyboardBuilder()
                    builder.button(text="🎁 Получить заказ", callback_data=f"claim_{order_id}")
                    await bot.send_message(user_id, msg, reply_markup=builder.as_markup())
            except Exception as e:
                logger.warning(f"Failed to notify user {user_id}: {e}")

            # уведомить админов
            for adm in ADMIN_IDS:
                try:
                    await bot.send_message(
                        adm,
                        f"✅ NicePay: Заказ #{order_id} оплачен\n"
                        f"👤 Пользователь: <code>{user_id}</code>\n"
                        f"🛒 Товар: {order['product_name']}\n"
                        f"💵 Сумма: {order['price']:,} ₽\n"
                        f"Payload: <code>{str(payload)[:400]}</code>",
                    )
                except:
                    pass

        return web.json_response({"status": "ok"})
    except Exception as e:
        logger.exception(f"NicePay webhook error: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def start_webhook_server(bot: Bot):
    app = web.Application()
    app["bot"] = bot
    app.router.add_post(NICEPAY_WEBHOOK_PATH, nicepay_webhook_handler)
    app.router.add_get(NICEPAY_WEBHOOK_PATH, nicepay_webhook_handler)  # для теста GET
    app.router.add_get("/", lambda r: web.json_response({"status": "ok", "service": "apex_bot nicepay webhook"}))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", NICEPAY_WEBHOOK_PORT)
    await site.start()
    logger.info(f"NicePay webhook listening on 0.0.0.0:{NICEPAY_WEBHOOK_PORT}{NICEPAY_WEBHOOK_PATH}")
    while True:
        await asyncio.sleep(3600)


async def auto_check_nicepay(bot: Bot):
    while True:
        try:
            await asyncio.sleep(30)
            pending = get_pending_orders()
            nicepay_pending = [o for o in pending if o["payment_method"] == "nicepay"]
            if not nicepay_pending:
                continue
            logger.info(f"Auto-check NicePay: {len(nicepay_pending)} pending orders")
            for order in nicepay_pending:
                try:
                    result = await check_nicepay_payment(order["id"])
                    if is_nicepay_success(result):
                        confirm_order(order["id"])
                        user_id = order["user_id"]
                        if order["product_id"] == "deposit":
                            new_balance = add_balance(user_id, order["price"])
                            logger.info(f"Auto-check: deposit #{order['id']} confirmed, user_id={user_id}, new_balance={new_balance}")
                            msg = f"💰 <b>Баланс пополнен!</b>\n\n📄 Платёж №<b>{order['id']}</b>\n💵 Сумма: <b>{order['price']:,} ₽</b>\n\nОплачено через NicePay ✅"
                            try:
                                await bot.send_message(user_id, msg, reply_markup=bottom_menu())
                            except Exception as e:
                                logger.warning(f"Failed to notify user {user_id}: {e}")
                        else:
                            tokens = claim_order(order["id"])
                            if tokens:
                                lines = "\n".join(f"<code>{m['token']}</code>" for m in tokens)
                                msg = f"✅ <b>Заказ #{order['id']} оплачен!</b>\n\n🛒 Товар: <b>{order['product_name']}</b>\n💵 Сумма: <b>{order['price']:,} ₽</b>\n\n<b>Ваши токены:</b>\n{lines}\n\nСохраните их, они понадобятся для активации товара."
                            else:
                                msg = f"✅ <b>Заказ #{order['id']} подтверждён!</b>\n\n🛒 Товар: <b>{order['product_name']}</b>\n💵 Сумма: <b>{order['price']:,} ₽</b>\n\nОплачено через NicePay ✅"
                            try:
                                await bot.send_message(user_id, msg, reply_markup=bottom_menu())
                            except Exception as e:
                                logger.warning(f"Failed to notify user {user_id}: {e}")
                        for adm in ADMIN_IDS:
                            try:
                                await bot.send_message(adm, f"✅ NicePay (автопроверка): Заказ #{order['id']} подтверждён\n👤 Пользователь: <code>{user_id}</code>\n🛒 Товар: {order['product_name']}\n💵 Сумма: {order['price']:,} ₽")
                            except:
                                pass
                        logger.info(f"Auto-check: order #{order['id']} confirmed via NicePay API")
                except Exception as e:
                    logger.exception(f"Auto-check NicePay: error checking order #{order['id']}: {e}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception(f"Auto-check NicePay: loop error: {e}")
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
    autocheck_task = asyncio.create_task(auto_check_nicepay(bot))
    try:
        await dp.start_polling(bot)
    finally:
        webhook_task.cancel()
        autocheck_task.cancel()
        try:
            await webhook_task
        except asyncio.CancelledError:
            pass
        try:
            await autocheck_task
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
