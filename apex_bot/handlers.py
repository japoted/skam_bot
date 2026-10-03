import os
import logging

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, FSInputFile,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# NewsEmoji animated premium — https://t.me/addemoji/NewsEmoji
CUSTOM_EMOJI = [
    "5210956306952758910", "5461117441612462242", "5456140674028019486",
    "5224607267797606837", "5229064374403998351", "5409048419211682843",
    "5233326571099534068", "5424972470023104089", "5427168083074628963",
    "5438496463044752972", "5447410659077661506", "5231200819986047254",
    "5244837092042750681", "5206607081334906820", "5210952531676504517",
    "5458603043203327669", "5334544901428229844", "5296369303661067030",
    "5406683434124859552", "5251203410396458957", "5416081784641168838",
    "5422439311196834318", "5461151367559141950", "5409048419211682843",
]

# смысловые алиасы для Supermarket_cash
E_SHOP = "5406683434124859552"  # 🛍
E_MONEY = "5409048419211682843"  # 💵
E_MONEY_FLY = "5233326571099534068"  # 💸
E_FIRE = "5424972470023104089"  # 🔥
E_DIAMOND = "5427168083074628963"  # 💎
E_STAR = "5438496463044752972"  # ⭐
E_GLOBE = "5447410659077661506"  # 🌐
E_CHART = "5231200819986047254"  # 📊
E_CHART_UP = "5244837092042750681"  # 📈
E_CHECK = "5206607081334906820"  # ✔️
E_CROSS = "5210952531676504517"  # ❌
E_BELL = "5458603043203327669"  # 🔔
E_INFO = "5334544901428229844"  # ℹ️
E_LOCK = "5296369303661067030"  # 🔒
E_SHIELD = "5251203410396458957"  # 🛡
E_GREEN = "5416081784641168838"  # 🟢
E_LIGHT = "5422439311196834318"  # 💡
E_LIGHTNING = "5456140674028019486"  # ⚡️
E_PARTY = "5461151367559141950"  # 🎉

PRODUCT_EMOJI = {
    "turbo_lite": "5406683434124859552",
    "turbo": "5456140674028019486",
    "x_turbo": "5424972470023104089",
    "giga_turbo": "5427168083074628963",
    "proxy_ipv4": "5251203410396458957",
    "proxy_ipv6": "5447410659077661506",
    "proxy_mobile": "5416081784641168838",
    "manual_p2p_start": "5231200819986047254",
    "manual_p2p_pro": "5244837092042750681",
    "manual_airdrop": "5438496463044752972",
    "manual_tiktok": "5458603043203327669",
    "manual_cards": "5233326571099534068",
    "manual_anon": "5296369303661067030",
    "manual_binance_guide": "5409048419211682843",
    "manual_bybit_guide": "5402186569006210455",
    "manual_traffic_fb": "5422439311196834318",
    "manual_combo_lite": "5461151367559141950",
    "acc_binance": "5206607081334906820",
    "acc_bybit": "5397782960512444700",
    "acc_okx": "5222079954421818267",
    "sim_rf": "5443038326535759644",
    "dedik_usa": "5282843764451195532",
    "antidetect": "5271604874419647061",
    "vpn_premium": "5334544901428229844",
    "card_virtual": "5278751923338490157",
    "selfreg_fb": "5325547803936572038",
    "wallet_clean": "5290017777174722330",
    "cert_clean": "5229064374403998351",
    "cert_express": "5231012545799666522",
    "cert_guarantee": "5375338737028841420",
    "cart_filter": "5440660757194744323",
    "cash_converter": "5210952531676504517",
}


CATEGORY_EMOJI = {
    "cash_boxes": "5456140674028019486",  # ⚡️
    "shelf_proxies": "5406683434124859552",  # 🛍
    "market_certs": "5397782960512444700",  # 📌
    "cart_filter": "5231012545799666522",  # 🔍
    "market_converter": "5375338737028841420",  # 🔄
    "manuals": "5231200819986047254",  # 📊
    "accounts": "5206607081334906820",  # ✔️
    "services": "5282843764451195532",  # 🖥
    "cards": "5233326571099534068",  # 💸
}
def _category_premium(cat: str) -> str:
    eid = CATEGORY_EMOJI.get(cat, E_INFO)
    fb = {"cash_boxes":"⚡️","shelf_proxies":"🛍","market_certs":"📌","cart_filter":"🔍","market_converter":"🔄","manuals":"📊","accounts":"✔️","services":"🖥","cards":"💸"}.get(cat,"📁")
    return _ce(eid, fb)

def _premium_for(pid: str) -> str:
    eid = PRODUCT_EMOJI.get(pid, E_STAR)
    fb_map = {"turbo_lite": "🛍", "turbo": "⚡️", "x_turbo": "🔥", "giga_turbo": "💎", "proxy_ipv4": "🛡", "proxy_ipv6": "🌐", "proxy_mobile": "🟢", "manual_p2p_start": "📊", "manual_p2p_pro": "📈", "manual_airdrop": "⭐", "manual_tiktok": "🔔", "manual_cards": "💸", "manual_anon": "🔒", "manual_binance_guide": "💵", "manual_bybit_guide": "💱", "manual_traffic_fb": "💡", "manual_combo_lite": "🎉", "acc_binance": "✔️", "acc_bybit": "📌", "acc_okx": "🆒", "sim_rf": "💬", "dedik_usa": "🖥", "antidetect": "🔗", "vpn_premium": "ℹ️", "card_virtual": "💸", "selfreg_fb": "✨", "wallet_clean": "💸", "cert_clean": "🛍", "cert_express": "🔍", "cert_guarantee": "🔄", "cart_filter": "‼️", "cash_converter": "❌"}
    fallback = fb_map.get(pid, "⭐")
    return _ce(eid, fallback)

E_LIGHTNING = "5456140674028019486"  # ⚡️



def _ce(eid: str, fallback: str = "⭐") -> str:
    return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'

pending_crypto_order: dict[int, int] = {}

import config
from config import ADMIN_IDS, PRODUCTS, CRYPTO_WALLET, OFFER_URL, MAIN_ADMIN
from database import (
    register_user, get_user, get_user_orders, get_order_stats,
    create_order, get_pending_orders, confirm_order, reject_order,
    get_order_user_id, get_promocode, use_promocode,
    list_promocodes, create_promocode, delete_promocode,
    get_all_users, add_balance, claim_order, get_order,
    get_token_meta, apply_converter, set_order_invoice,
    get_setting, set_setting, get_required_channel, set_required_channel,
)
from nicepay import create_nicepay_invoice, check_nicepay_invoice, is_nicepay_success, format_requisites
from keyboards import (
    main_menu, bottom_menu, catalog_menu, category_products,
    product_actions, quantity_selector, payment_methods,
    admin_panel, admin_order_actions,
    deposit_amounts, deposit_payment_methods,
    NEWS_URL,
)

waiting_promo: dict[int, str] = {}
waiting_deposit: dict[int, bool] = {}

logger = logging.getLogger(__name__)
pending_quantity: dict[int, int] = {}
waiting_converter: dict[int, str] = {}

router = Router()

BANNER = os.path.join(os.path.dirname(__file__), "5438570968302427672.jpg")
BANNERS = {
    "support": os.path.join(os.path.dirname(__file__), "5379983559935860452.jpg"),
    "profile": os.path.join(os.path.dirname(__file__), "провиль.jfif"),
    "deposit": os.path.join(os.path.dirname(__file__), "пополнение.jfif"),
    "cash_boxes": os.path.join(os.path.dirname(__file__), "5442751204137048819.jpg"),
    "shelf_proxies": os.path.join(os.path.dirname(__file__), "баннер прокси.jfif"),
    "market_certs": os.path.join(os.path.dirname(__file__), "лицензия.jfif"),
    "info": os.path.join(os.path.dirname(__file__), "информация.jfif"),
    "catalog": os.path.join(os.path.dirname(__file__), "каталог.jfif"),
    "accounts": os.path.join(os.path.dirname(__file__), "cat_accounts.jpg"),
    "services": os.path.join(os.path.dirname(__file__), "cat_services.jpg"),
    "cards": os.path.join(os.path.dirname(__file__), "cat_cards.jpg"),
    "manuals": os.path.join(os.path.dirname(__file__), "cat_services.jpg"),
    "cart_filter": os.path.join(os.path.dirname(__file__), "cat_services.jpg"),
    "market_converter": os.path.join(os.path.dirname(__file__), "cat_services.jpg"),
}


async def _nav(callback: CallbackQuery, text: str, reply_markup, answer_text="", show_alert=False):
    try:
        if callback.message.caption is not None:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=reply_markup)
        else:
            await callback.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        pass
    try:
        if show_alert:
            await callback.answer(answer_text, show_alert=True)
        else:
            await callback.answer()
    except Exception:
        pass


admin_give_balance_state: dict[int, dict] = {}


@router.callback_query(F.data == "admin_give_balance")
async def cb_admin_give_balance_start(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    admin_give_balance_state[callback.from_user.id] = {"step": "user_id"}
    await callback.message.edit_text(
        "💰 <b>Выдать баланс</b>\n\n"
        "Отправьте ID пользователя (числовой):",
        reply_markup=InlineKeyboardBuilder().button(text="❌ Отмена", callback_data="admin_cancel_give").as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_cancel_give")
async def cb_admin_cancel_give(callback: CallbackQuery):
    admin_give_balance_state.pop(callback.from_user.id, None)
    await callback.message.edit_text("🔧 Панель администратора", reply_markup=admin_panel())
    await callback.answer()


@router.message(F.text, F.from_user.id.in_(ADMIN_IDS), lambda m: admin_give_balance_state.get(m.from_user.id))
async def cb_admin_give_balance_process(message: Message):
    state = admin_give_balance_state.get(message.from_user.id)
    if not state:
        return
    text = message.text.strip()

    if state["step"] == "user_id":
        if not text.isdigit():
            await message.answer("❌ ID должен быть числом. Попробуйте ещё раз:")
            return
        state["target_user_id"] = int(text)
        state["step"] = "amount"
        await message.answer(
            f"👤 Пользователь: <code>{text}</code>\n\n"
            "💵 Введите сумму (число, например 500):",
            reply_markup=InlineKeyboardBuilder().button(text="❌ Отмена", callback_data="admin_cancel_give").as_markup(),
        )
        return

    if state["step"] == "amount":
        if not text.isdigit() or int(text) <= 0:
            await message.answer("❌ Сумма должна быть положительным числом. Попробуйте ещё раз:")
            return
        target_user_id = state["target_user_id"]
        amount = int(text)
        new_balance = add_balance(target_user_id, amount)
        admin_give_balance_state.pop(message.from_user.id, None)
        await message.answer(
            f"✅ <b>Баланс выдан!</b>\n\n"
            f"👤 Пользователь: <code>{target_user_id}</code>\n"
            f"💵 Сумма: +{amount:,} ₽\n"
            f"💰 Новый баланс: {new_balance:,} ₽",
            reply_markup=admin_panel(),
        )
        try:
            await message.bot.send_message(
                target_user_id,
                f"💰 <b>Баланс пополнен администратором!</b>\n\n💵 Сумма: +{amount:,} ₽\n💰 Баланс: {new_balance:,} ₽",
                reply_markup=bottom_menu(),
            )
        except:
            pass


async def _send_with_banner(target: Message, banner_key: str, text: str, reply_markup=None):
    path = BANNERS.get(banner_key)
    if path and os.path.isfile(path):
        photo = FSInputFile(path)
        await target.answer_photo(photo=photo, caption=text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await target.answer(text, reply_markup=reply_markup)


async def _send_main_menu(target: Message | CallbackQuery):
    user_first = target.from_user.first_name or ""
    text = (
        f"{_ce(E_PARTY,'🎉')} <b>Привет, {user_first}!</b> {_ce(E_STAR,'⭐')}\n\n"
        f"{_ce(E_SHOP,'🛒')} <b>Supermarket_cash — первый супермаркет кэша в Telegram</b> {_ce(E_MONEY,'💵')}\n\n"
        f"{_ce(E_FIRE,'🔥')} <b>Мы уже помогли 5 200+ клиентам заработать</b> — бери ТУРБО-бокс с полки и иди к кассе!\n\n"
        f"{_ce(E_CHECK,'✔️')} Выдача за 2 минуты • чистые чеки • без холда\n"
        f"{_ce(E_CHART_UP,'📈')} Оборот 200M+ ₽ • цены от 490₽ • гарант\n"
        f"{_ce(E_SHIELD,'🛡')} Поддержка {_ce(E_BELL,'🔔')} 24/7 • полки всегда в наличии • {_ce(E_DIAMOND,'💎')} топ-качество\n\n"
        f"{_ce(E_GREEN,'🟢')} <b>Бери тележку и заглядывай в каталог 👇</b>\n"
        f"{_ce(E_LIGHT,'💡')} <i>Выбери отдел — забери товар по оптовой цене. Сегодня скидки на ТУРБО!</i>"
    )
    if os.path.isfile(BANNER):
        photo = FSInputFile(BANNER)
        if isinstance(target, CallbackQuery):
            await target.message.delete()
            await target.bot.send_photo(chat_id=target.message.chat.id, photo=photo, caption=text, reply_markup=main_menu())
            await target.bot.send_message(chat_id=target.message.chat.id, text="👇", reply_markup=bottom_menu())
        else:
            await target.answer_photo(photo=photo, caption=text, reply_markup=main_menu())
            await target.answer("👇", reply_markup=bottom_menu())
    else:
        if isinstance(target, CallbackQuery):
            await target.message.edit_text(text, reply_markup=main_menu())
        else:
            await target.answer(text, reply_markup=main_menu())


@router.message(CommandStart())
async def cmd_start(message: Message):
    register_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    # обязательная подписка
    ch = get_required_channel()
    if ch:
        try:
            member = await message.bot.get_chat_member(ch, message.from_user.id)
            if member.status in ("left", "kicked"):
                builder = InlineKeyboardBuilder()
                # ch may be @username or -100 id; handle invite link
                if ch.startswith("@"):
                    url = f"https://t.me/{ch[1:]}"
                else:
                    url = f"https://t.me/{str(ch).replace('@','')}"
                builder.button(text="📢 Подписаться на канал", url=url)
                builder.button(text="✅ Проверить подписку", callback_data="check_sub")
                builder.adjust(1)
                await message.answer(f"🔒 <b>Подпишись на канал {ch} чтобы пользоваться Supermarket_cash!</b>", reply_markup=builder.as_markup())
                return
        except Exception as e:
            # если бот не админ в канале — пропускаем проверку (логируем)
            logger.warning(f"check_sub failed {ch}: {e}")
    await _send_main_menu(message)

@router.callback_query(F.data == "check_sub")
async def cb_check_sub(callback: CallbackQuery):
    ch = get_required_channel()
    if not ch:
        await _send_main_menu(callback)
        return
    try:
        member = await callback.bot.get_chat_member(ch, callback.from_user.id)
        if member.status in ("left", "kicked"):
            await callback.answer("❌ Ты ещё не подписался!", show_alert=True)
            return
    except:
        pass
    await callback.message.delete()
    await _send_main_menu(callback)
    await callback.answer("✅ Подписка подтверждена!", show_alert=True)


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(f"🆔 Твой Telegram ID: <code>{message.from_user.id}</code>")


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("🔧 Панель администратора", reply_markup=admin_panel())


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    await _send_main_menu(callback)
    await callback.answer()


@router.callback_query(F.data == "catalog")
async def cb_catalog(callback: CallbackQuery):
    # premium list of categories for wow
    cat_list = "\n".join([f"{_category_premium(k)} {v}" for k,v in config.CATEGORIES.items()])
    text = f"{_ce(E_SHOP,'🛒')} <b>Каталог Supermarket_cash</b> {_ce(E_FIRE,'🔥')}\n\n{cat_list}\n\n{_ce(E_DIAMOND,'💎')} Выбери отдел:"
    path = BANNERS.get("catalog")
    if path and os.path.isfile(path):
        await callback.message.delete()
        photo = FSInputFile(path)
        await callback.bot.send_photo(
            chat_id=callback.message.chat.id, photo=photo,
            caption=text, reply_markup=catalog_menu(),
        )
    else:
        await _nav(callback, text, catalog_menu())
    await callback.answer()


@router.callback_query(F.data.startswith("cat_"))
async def cb_category(callback: CallbackQuery):
    cat_key = callback.data[4:]
    cat_name = config.CATEGORIES.get(cat_key, cat_key)
    prem = _category_premium(cat_key)
    text = f"{prem} <b>{cat_name}</b>\n\nВыбери нужный товар:"
    path = BANNERS.get(cat_key)
    if path and os.path.isfile(path):
        await callback.message.delete()
        photo = FSInputFile(path)
        await callback.bot.send_photo(
            chat_id=callback.message.chat.id, photo=photo,
            caption=text, reply_markup=category_products(cat_key),
        )
    else:
        await _nav(callback, text, category_products(cat_key))
    await callback.answer()


@router.callback_query(F.data.startswith("product_"))
async def cb_product(callback: CallbackQuery):
    pid = callback.data[8:]
    p = PRODUCTS.get(pid)
    if not p:
        await callback.answer("Товар не найден", show_alert=True)
        return

    stock = f"{_ce(E_CHECK,'✅')} В наличии" if p["in_stock"] else f"{_ce(E_CROSS,'❌')} Нет в наличии"
    # remove leading unicode emoji from name/desc for clean premium display (exactly one premium)
    import re as _re
    clean_name = _re.sub(r'^[^\w<]+\s*', '', p['name'])
    clean_desc = _re.sub(r'^[^\w<]+\s*', '', p['desc'])
    prem = _premium_for(pid)
    text = (
        f"{prem} <b>{clean_name}</b>\n\n"
        f"<b>Описание:</b> {clean_desc}\n\n"
        f"<b>Цена:</b> {p['price']:,} ₽\n"
        f"<b>Статус:</b> {stock}"
    )
    # если есть персональная картинка товара — шлём её
    prod_img = os.path.join(os.path.dirname(__file__), "products", f"{pid}.jpg")
    if os.path.isfile(prod_img):
        try:
            await callback.message.delete()
            photo = FSInputFile(prod_img)
            await callback.bot.send_photo(chat_id=callback.message.chat.id, photo=photo, caption=text, reply_markup=product_actions(pid))
            await callback.answer()
            return
        except Exception as e:
            logger.warning(f"product img send fail {pid}: {e}")
    await _nav(callback, text, product_actions(pid))


@router.callback_query(F.data.startswith("qty_"))
async def cb_qty(callback: CallbackQuery):
    pid = callback.data[4:]
    p = PRODUCTS.get(pid)
    if not p:
        await callback.answer("Товар не найден", show_alert=True)
        return
    text = (
        f"<b>{p['name']}</b>\n\n"
        f"💰 Цена за 1 шт.: <b>{p['price']:,} ₽</b>\n\n"
        "Выберите количество:"
    )
    await _nav(callback, text, quantity_selector(pid))


@router.callback_query(F.data.startswith("sel_qty_"))
async def cb_sel_qty(callback: CallbackQuery):
    rest = callback.data[8:]
    *pid_parts, qty_str = rest.rsplit("_", 1)
    pid = "_".join(pid_parts)
    qty = int(qty_str)

    p = PRODUCTS.get(pid)
    if not p:
        await callback.answer("Товар не найден", show_alert=True)
        return
    if not p["in_stock"]:
        await callback.answer("Товара нет в наличии", show_alert=True)
        return

    pending_quantity[callback.from_user.id] = qty
    total = p["price"] * qty
    user = get_user(callback.from_user.id)
    balance = user["balance"] if user else 0
    text = (
        f"<b>{p['name']}</b> x{qty}\n\n"
        f"💳 <b>Выберите способ оплаты:</b>\n\n"
        f"Сумма к оплате: <b>{total:,} ₽</b>\n"
        f"💰 Ваш баланс: <b>{balance:,} ₽</b>"
    )
    await _nav(callback, text, payment_methods(pid, total, balance))


@router.callback_query(F.data.startswith("buy_"))
async def cb_buy(callback: CallbackQuery):
    raw = callback.data[4:]
    if "_" in raw and raw.split("_")[-1].isdigit():
        *pid_parts, price_str = raw.rsplit("_", 1)
        pid = "_".join(pid_parts)
        price = int(price_str)
    else:
        pid = raw
        p = PRODUCTS.get(pid)
        if not p:
            await callback.answer("Товар не найден", show_alert=True)
            return
        price = p["price"]

    p = PRODUCTS.get(pid)
    if not p:
        await callback.answer("Товар не найден", show_alert=True)
        return
    if not p["in_stock"]:
        await callback.answer("Товара нет в наличии", show_alert=True)
        return

    tag = " (со скидкой)" if price != p["price"] else ""
    user = get_user(callback.from_user.id)
    balance = user["balance"] if user else 0
    text = (
        f"<b>{p['name']}</b>\n\n"
        f"💳 <b>Выберите способ оплаты:</b>\n\n"
        f"Сумма к оплате: <b>{price:,} ₽</b>{tag}\n"
        f"💰 Ваш баланс: <b>{balance:,} ₽</b>"
    )
    await _nav(callback, text, payment_methods(pid, price, balance))


def _back_to_payment(product_id: str, price: int = 0):
    p = config.PRODUCTS.get(product_id)
    final = price if price else (p["price"] if p else 0)
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад к способам оплаты", callback_data=f"buy_{product_id}_{final}")
    builder.button(text="Отмена", callback_data="catalog")
    builder.adjust(1)
    return builder.as_markup()


def _parse_pid_price(data: str):
    *pid_parts, price_str = data.rsplit("_", 1)
    return "_".join(pid_parts), int(price_str)


@router.callback_query(F.data.startswith("pay_card_"))
async def cb_pay_card(callback: CallbackQuery):
    pid, price = _parse_pid_price(callback.data[len("pay_card_"):])
    p = PRODUCTS.get(pid)
    if not p:
        await callback.answer("Товар не найден", show_alert=True)
        return

    qty = pending_quantity.pop(callback.from_user.id, 1)
    order_id = create_order(callback.from_user.id, pid, p["name"], price, "nicepay", qty)
    pending_crypto_order[callback.from_user.id] = order_id

    await callback.answer("⏳ Создаю платёж NicePay...")
    customer = callback.from_user.username or str(callback.from_user.id)
    result = await create_nicepay_invoice(order_id=order_id, amount=price, description=p["name"], customer=customer)

    if result.get("id") or result.get("paymentUrl") or result.get("redirect_url") or result.get("url"):
        inv_id = result.get("id") or result.get("orderId") or result.get("_id") or str(order_id)
        set_order_invoice(order_id, str(inv_id))
        pay_url = result.get("paymentUrl") or result.get("redirect_url") or result.get("url") or result.get("payUrl")
        if pay_url:
            text = (
                f"💳 <b>Оплата через NicePay (СБП)</b>\n\n"
                f"Товар: <b>{p['name']}</b> x{qty}\n"
                f"Сумма: <b>{price:,} ₽</b>\n"
                f"Номер заказа: <b>#{order_id}</b>\n\n"
                f"📌 Нажмите кнопку ниже и оплатите по СБП/карте.\n"
                f"✅ Заказ выдастся <b>автоматически</b> после оплаты.\n\n"
                f"👤 @Supermarket_cash_support — поддержка"
            )
            builder = InlineKeyboardBuilder()
            builder.button(text="💳 Оплатить через NicePay", url=pay_url)
            builder.button(text="🔄 Проверить оплату", callback_data=f"check_nicepay_{order_id}")
            builder.button(text="❌ Отмена", callback_data="catalog")
            builder.adjust(1)
            await _nav(callback, text, builder.as_markup())
        else:
            req = format_requisites(result)
            text = (
                f"💳 <b>Оплата через NicePay</b>\n\n"
                f"Товар: <b>{p['name']}</b> x{qty}\n"
                f"Сумма к переводу: <b>{price:,} ₽</b>\n"
                f"Номер заказа: <b>#{order_id}</b>\n\n"
                f"{req}\n\n"
                f"📌 Переведите <b>точную сумму {price:,} ₽</b> по реквизитам.\n"
                f"✅ Заказ выдастся <b>автоматически</b> после оплаты.\n\n"
                f"👤 @Supermarket_cash_support — поддержка"
            )
            builder = InlineKeyboardBuilder()
            builder.button(text="🔄 Проверить оплату", callback_data=f"check_nicepay_{order_id}")
            builder.button(text="❌ Отмена", callback_data="catalog")
            builder.adjust(1)
            await _nav(callback, text, builder.as_markup())
    else:
        err = result.get("message") or str(result)[:300]
        text = (
            f"❌ <b>Ошибка NicePay</b>\n\n"
            f"Товар: <b>{p['name']}</b> x{qty}\n"
            f"Сумма: <b>{price:,} ₽</b>\n"
            f"Заказ: <b>#{order_id}</b>\n\n"
            f"Ошибка: <code>{err}</code>\n\n"
            f"Попробуйте позже или пишите @Supermarket_cash_support"
        )
        await _nav(callback, text, _back_to_payment(pid, price))


@router.callback_query(F.data.startswith("pay_balance_"))
async def cb_pay_balance(callback: CallbackQuery):
    pid, price = _parse_pid_price(callback.data[len("pay_balance_"):])
    p = PRODUCTS.get(pid)
    if not p:
        await callback.answer("Товар не найден", show_alert=True)
        return

    user = get_user(callback.from_user.id)
    balance = user["balance"] if user else 0
    if balance < price:
        await callback.answer("❌ Недостаточно средств на балансе", show_alert=True)
        return

    qty = pending_quantity.pop(callback.from_user.id, 1)
    add_balance(callback.from_user.id, -price)
    order_id = create_order(callback.from_user.id, pid, p["name"], price, "balance", qty)
    confirm_order(order_id)

    order = get_order(order_id)
    username = callback.from_user.username or "—"
    text = (
        f"✅ <b>Заказ оформлен!</b>\n\n"
        f"📦 Номер заказа: <b>#{order_id}</b>\n"
        f"👤 Покупатель: @{username} (<code>{callback.from_user.id}</code>)\n"
        f"🛒 Товар: <b>{p['name']}</b> x{qty}\n"
        f"💵 Сумма: <b>{price:,} ₽</b>\n"
        f"🕐 Время: <b>{order['created_at']}</b>"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🎁 Получить заказ", callback_data=f"claim_{order_id}")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    await _nav(callback, text, builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("claim_"))
async def cb_claim_order(callback: CallbackQuery):
    order_id = int(callback.data[6:])
    order = get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    if order["user_id"] != callback.from_user.id:
        await callback.answer("Это не ваш заказ", show_alert=True)
        return

    if order["token"]:
        await callback.answer("Заказ уже получен", show_alert=True)
        return

    if order["status"] != "confirmed":
        await callback.answer("Заказ ещё не подтверждён", show_alert=True)
        return

    tokens = claim_order(order_id)
    if not tokens:
        await callback.answer("Ошибка получения заказа", show_alert=True)
        return

    qty = len(tokens)
    token_strs = [m["token"] for m in tokens]
    product_name = order["product_name"]
    pid = order["product_id"]
    # мануалы — отдаём реальный PDF из папки manuals/
    if pid.startswith("manual_"):
        pdf_path = os.path.join(os.path.dirname(__file__), "manuals", f"{pid}.pdf")
        if os.path.isfile(pdf_path):
            # сначала показываем текст
            text_manual = (
                f"🎉 <b>Благодарим за покупку!</b>\n\n"
                f"📦 Заказ <b>#{order_id}</b>\n\n"
                f"<b>Ваш {product_name}:</b> готов!\n"
                f"📄 Файл <b>{os.path.basename(pdf_path)}</b> ниже 👇\n\n"
                f"Сохраните его, автор — Supermarket_cash."
            )
            try:
                await callback.message.edit_text(text_manual)
            except:
                pass
            # отправляем PDF как документ (реальный файл, не фейк-ссылка)
            try:
                doc = FSInputFile(pdf_path)
                await callback.bot.send_document(chat_id=callback.from_user.id, document=doc, caption=f"📚 {product_name}")
            except Exception as e:
                logger.warning(f"manual send fail {pid}: {e}")
                # fallback: показать токен
                await callback.message.answer(f"<code>{token_strs[0]}</code>")
            await callback.answer("🎉 Мануал отправлен!", show_alert=True)
            return
    if qty == 1:
        text = (
            f"🎉 <b>Благодарим за покупку!</b>\n\n"
            f"📦 Заказ <b>#{order_id}</b>\n\n"
            f"<b>Ваш {product_name}:</b>\n"
            f"<code>{token_strs[0]}</code>\n\n"
            f"Сохраните его, он понадобится для активации товара."
        )
    else:
        lines = "\n".join(f"<code>{t}</code>" for t in token_strs)
        text = (
            f"🎉 <b>Благодарим за покупку!</b>\n\n"
            f"📦 Заказ <b>#{order_id}</b> x{qty}\n\n"
            f"<b>Ваши {product_name}:</b>\n"
            f"{lines}\n\n"
            f"Сохраните их, они понадобятся для активации товара."
        )
    is_converter = config.PRODUCTS.get(order["product_id"], {}).get("category") == "market_converter"
    if is_converter:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Применить конвертер к токену", callback_data=f"convert_{order_id}")
        builder.button(text="🏠 Главное меню", callback_data="main_menu")
        builder.adjust(1)
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text, reply_markup=None)
    await callback.answer("🎉 Заказ получен!", show_alert=True)


@router.callback_query(F.data.startswith("convert_"))
async def cb_convert(callback: CallbackQuery):
    order_id = int(callback.data[8:])
    order = get_order(order_id)
    if not order or order["user_id"] != callback.from_user.id:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    waiting_converter[callback.from_user.id] = order_id
    text = "🔄 <b>Применение конвертера</b>\n\nОтправьте токен, который хотите улучшить:"
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data.startswith("pay_wallet_"))
async def cb_pay_wallet(callback: CallbackQuery):
    pid, price = _parse_pid_price(callback.data[len("pay_wallet_"):])
    p = PRODUCTS.get(pid)
    if not p:
        await callback.answer("Товар не найден", show_alert=True)
        return

    qty = pending_quantity.pop(callback.from_user.id, 1)
    order_id = create_order(callback.from_user.id, pid, p["name"], price, "wallet", qty)
    pending_crypto_order[callback.from_user.id] = order_id

    text = (
        f"💎 <b>Оплата криптовалютой (кошелёк)</b>\n\n"
        f"Товар: <b>{p['name']}</b> x{qty}\n"
        f"Сумма: <b>{price:,} ₽</b>\n"
        f"Номер заказа: <b>#{order_id}</b>\n\n"
        f"📌 <b>Адрес кошелька USDT (TRC20):</b>\n"
        f"<code>{CRYPTO_WALLET}</code>\n\n"
        f"После перевода отправьте скриншот оплаты в этот чат.\n"
        f"Администратор проверит и подтвердит заказ.\n\n"
        f"👤 @Supermarket_cash_support — по всем вопросам писать администратору"
    )
    await _nav(callback, text, _back_to_payment(pid, price))


@router.callback_query(F.data.startswith("pay_stars_"))
async def cb_pay_stars(callback: CallbackQuery):
    pid, price = _parse_pid_price(callback.data[len("pay_stars_"):])
    p = PRODUCTS.get(pid)
    if not p:
        await callback.answer("Товар не найден", show_alert=True)
        return

    qty = pending_quantity.pop(callback.from_user.id, 1)
    prices = [LabeledPrice(label=p["name"], amount=price)]
    await callback.message.answer_invoice(
        title=p["name"],
        description=p["desc"][:255],
        payload=f"tg_stars_{pid}_{qty}",
        provider_token="",
        currency="XTR",
        prices=prices,
        reply_markup=_back_to_payment(pid),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dep_pay_card_"))
async def cb_dep_pay_card(callback: CallbackQuery):
    amount = int(callback.data.split("_")[-1])
    order_id = create_order(callback.from_user.id, "deposit", "Пополнение баланса", amount, "nicepay")
    pending_crypto_order[callback.from_user.id] = order_id

    await callback.answer("⏳ Создаю платёж NicePay...")
    customer = callback.from_user.username or str(callback.from_user.id)
    result = await create_nicepay_invoice(order_id=order_id, amount=amount, description="Пополнение баланса", customer=customer)

    if result.get("id") or result.get("paymentUrl") or result.get("redirect_url") or result.get("url"):
        inv_id = result.get("id") or result.get("orderId") or str(order_id)
        set_order_invoice(order_id, str(inv_id))
        pay_url = result.get("paymentUrl") or result.get("redirect_url") or result.get("url") or result.get("payUrl")
        if pay_url:
            text = (
                f"💳 <b>Пополнение через NicePay</b>\n\n"
                f"📄 Платёж №<b>{order_id}</b>\n"
                f"💵 Сумма: <b>{amount:,} ₽</b>\n\n"
                f"📌 Нажмите кнопку ниже и оплатите.\n"
                f"✅ Баланс пополнится <b>автоматически</b> после оплаты.\n\n"
                f"👤 @Supermarket_cash_support — поддержка"
            )
            builder = InlineKeyboardBuilder()
            builder.button(text="💳 Оплатить через NicePay", url=pay_url)
            builder.button(text="🔄 Проверить оплату", callback_data=f"check_nicepay_{order_id}")
            builder.button(text="❌ Отмена", callback_data="deposit")
            builder.adjust(1)
            await _nav(callback, text, builder.as_markup())
        else:
            req = format_requisites(result)
            text = (
                f"💳 <b>Пополнение через NicePay</b>\n\n"
                f"📄 Платёж №<b>{order_id}</b>\n"
                f"💵 Сумма к переводу: <b>{amount:,} ₽</b>\n\n"
                f"{req}\n\n"
                f"📌 Переведите <b>точную сумму</b>.\n"
                f"✅ Баланс пополнится <b>автоматически</b>.\n\n"
                f"👤 @Supermarket_cash_support — поддержка"
            )
            builder = InlineKeyboardBuilder()
            builder.button(text="🔄 Проверить оплату", callback_data=f"check_nicepay_{order_id}")
            builder.button(text="❌ Отмена", callback_data="deposit")
            builder.adjust(1)
            await _nav(callback, text, builder.as_markup())
    else:
        err = result.get("message") or str(result)[:300]
        text = (
            f"❌ <b>Ошибка NicePay</b>\n\n"
            f"Сумма: <b>{amount:,} ₽</b>\n"
            f"Заказ: <b>#{order_id}</b>\n\n"
            f"Ошибка: <code>{err}</code>\n\n"
            f"Попробуйте позже или пишите @Supermarket_cash_support"
        )
        await _nav(callback, text, None)


@router.callback_query(F.data.startswith("dep_pay_wallet_"))
async def cb_dep_pay_wallet(callback: CallbackQuery):
    amount = int(callback.data.split("_")[-1])
    order_id = create_order(callback.from_user.id, "deposit", "Пополнение баланса", amount, "wallet")
    pending_crypto_order[callback.from_user.id] = order_id
    text = (
        f"💎 <b>Оплата криптовалютой (кошелёк)</b>\n\n"
        f"📄 Платёж №<b>{callback.from_user.id}-{amount}</b>\n"
        f"💵 Сумма: <b>{amount:,} ₽</b>\n\n"
        f"📌 <b>Адрес кошелька USDT (TRC20):</b>\n"
        f"<code>{CRYPTO_WALLET}</code>\n\n"
        f"После перевода отправьте скриншот в этот чат.\n"
        f"Администратор проверит и зачислит средства.\n\n"
        f"👤 @Supermarket_cash_support — по всем вопросам писать администратору"
    )
    await _nav(callback, text, None)


@router.callback_query(F.data.startswith("dep_pay_stars_"))
async def cb_dep_pay_stars(callback: CallbackQuery):
    amount = int(callback.data[14:])
    prices = [LabeledPrice(label="Пополнение баланса", amount=amount)]
    await callback.message.answer_invoice(
        title="Пополнение баланса",
        description=f"Пополнение баланса на {amount:,} ₽",
        payload=f"tg_stars_deposit_{amount}",
        provider_token="",
        currency="XTR",
        prices=prices,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("check_nicepay_"))
async def cb_check_croco(callback: CallbackQuery):
    order_id = int(callback.data[len("check_nicepay_"):])
    order = get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    if order["user_id"] != callback.from_user.id and callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Это не ваш заказ", show_alert=True)
        return
    if order["status"] == "confirmed":
        tok = order.get("token")
        if tok:
            lines = tok.split(",")
            lines_txt = "\n".join(f"<code>{t}</code>" for t in lines)
            text = (
                f"✅ <b>Заказ #{order_id} уже оплачен!</b>\n\n"
                f"🛒 Товар: <b>{order['product_name']}</b>\n"
                f"💵 Сумма: <b>{order['price']:,} ₽</b>\n\n"
                f"<b>Ваши токены:</b>\n{lines_txt}"
            )
            try:
                await callback.message.edit_text(text)
            except:
                pass
            await callback.answer("Оплата подтверждена!", show_alert=True)
            return
        else:
            if order["product_id"] == "deposit":
                await callback.answer("✅ Баланс пополнен!", show_alert=True)
                try:
                    await callback.message.edit_text(f"✅ <b>Баланс пополнен!</b>\n\n💵 Сумма: <b>{order['price']:,} ₽</b>")
                except:
                    pass
            else:
                builder = InlineKeyboardBuilder()
                builder.button(text="🎁 Получить заказ", callback_data=f"claim_{order_id}")
                builder.button(text="🏠 Главное меню", callback_data="main_menu")
                builder.adjust(1)
                try:
                    await callback.message.edit_text(
                        f"✅ <b>Заказ #{order_id} оплачен!</b>\n\nНажмите чтобы получить товар:",
                        reply_markup=builder.as_markup(),
                    )
                except:
                    pass
                await callback.answer("Оплата подтверждена!", show_alert=True)
            return
    if order["status"] == "rejected":
        await callback.answer("❌ Заказ отклонён", show_alert=True)
        return

    invoice_id = (order.get("invoice_id") or "").strip()
    if not invoice_id:
        # Express-форма: статуса через API нет, ждём webhook-автовыдачу
        await callback.answer("⏳ Оплата через форму проверяется автоматически. Подождите 1-2 мин после оплаты.", show_alert=True)
        return

    await callback.answer("⏳ Проверяю оплату в NicePay...", show_alert=False)
    result = await check_nicepay_invoice(invoice_id)
    if is_nicepay_success(result):
        confirm_order(order_id)
        user_id = order["user_id"]
        if order["product_id"] == "deposit":
            add_balance(user_id, order["price"])
            msg = (
                f"💰 <b>Баланс пополнен!</b>\n\n"
                f"📄 Платёж №<b>{order_id}</b>\n"
                f"💵 Сумма: <b>{order['price']:,} ₽</b>\n\n"
                f"Оплачено через NicePay ✅"
            )
            try:
                await callback.bot.send_message(user_id, msg, reply_markup=bottom_menu())
            except:
                pass
            await callback.answer("✅ Баланс пополнен!", show_alert=True)
            try:
                await callback.message.edit_text(f"✅ <b>Баланс пополнен!</b>\n\n💵 Сумма: <b>{order['price']:,} ₽</b>")
            except:
                pass
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
                    await callback.bot.send_message(user_id, msg)
                except:
                    pass
            await callback.answer("✅ Оплата подтверждена!", show_alert=True)
            try:
                builder = InlineKeyboardBuilder()
                builder.button(text="🎁 Получить заказ", callback_data=f"claim_{order_id}")
                builder.button(text="🏠 Главное меню", callback_data="main_menu")
                builder.adjust(1)
                await callback.message.edit_text(
                    f"✅ <b>Заказ #{order_id} оплачен!</b>\n\nНажмите чтобы получить товар:",
                    reply_markup=builder.as_markup(),
                )
            except:
                pass
        for adm in ADMIN_IDS:
            try:
                await callback.bot.send_message(
                    adm,
                    f"✅ NicePay (ручная проверка): Заказ #{order_id} оплачен\n"
                    f"👤 Пользователь: <code>{user_id}</code>\n"
                    f"🛒 Товар: {order['product_name']}\n"
                    f"💵 Сумма: {order['price']:,} ₽",
                )
            except:
                pass
    else:
        st = str(result.get("status", "")) if isinstance(result, dict) else ""
        if st.lower() in ("expired", "cancelled", "failed"):
            await callback.answer(f"❌ Счёт {st}. Создайте заказ заново.", show_alert=True)
        elif st.lower() in ("not_supported",):
            await callback.answer("⏳ NicePay подтверждает автоматически. Подождите 1-2 мин после оплаты — товар выдастся сам.", show_alert=True)
        else:
            await callback.answer("❌ Оплата ещё не поступила. Попробуйте через минуту.", show_alert=True)





@router.pre_checkout_query()
async def pre_checkout(pre_checkout_q: PreCheckoutQuery):
    await pre_checkout_q.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    if payload.startswith("tg_stars_deposit_"):
        amount = int(payload[17:])
        add_balance(message.from_user.id, amount)
        text = (
            f"✅ <b>Баланс пополнен!</b>\n\n"
            f"💰 Сумма: <b>{amount:,} ₽</b>\n"
            f"⭐ Оплачено звёздами Telegram.\n\n"
            f"Средства уже на вашем балансе."
        )
        await message.answer(text, reply_markup=bottom_menu())
        return

    if payload.startswith("tg_stars_"):
        rest = payload[9:]
        if "_" in rest and rest.split("_")[-1].isdigit():
            *pid_parts, qty_str = rest.rsplit("_", 1)
            pid = "_".join(pid_parts)
            qty = int(qty_str)
        else:
            pid = rest
            qty = 1
        p = PRODUCTS.get(pid)
        if p:
            total = p["price"] * qty
            order_id = create_order(
                message.from_user.id, pid, p["name"], total, "stars", qty
            )
            confirm_order(order_id)
            order = get_order(order_id)
            username = message.from_user.username or "—"
            text = (
                f"✅ <b>Заказ оформлен!</b>\n\n"
                f"📦 Номер заказа: <b>#{order_id}</b>\n"
                f"👤 Покупатель: @{username} (<code>{message.from_user.id}</code>)\n"
                f"🛒 Товар: <b>{p['name']}</b> x{qty}\n"
                f"💵 Сумма: <b>{total:,} ₽</b>\n"
                f"🕐 Время: <b>{order['created_at']}</b>"
            )
            builder = InlineKeyboardBuilder()
            builder.button(text="🎁 Получить заказ", callback_data=f"claim_{order_id}")
            builder.button(text="🏠 Главное меню", callback_data="main_menu")
            builder.adjust(1)
            await message.answer(text, reply_markup=builder.as_markup())
            return

    text = "✅ <b>Оплата прошла успешно!</b>"
    await message.answer(text, reply_markup=bottom_menu())


@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = get_user(user_id)
    cnt, total = get_order_stats(user_id)
    all_orders = get_user_orders(user_id)
    pending = [o for o in all_orders if o["status"] == "pending"]
    confirmed = [o for o in all_orders if o["status"] == "confirmed"]

    registered = user["registered_at"][:10] if user else "—"

    text = (
        f"{_ce(E_INFO,'ℹ️')} <b>Твой профиль в Supermarket_cash</b> {_ce(E_SHOP,'🛒')}\n\n"
        f"{_ce(E_CHECK,'✔️')} <b>Личная информация</b>\n"
        f"├ { _ce(E_STAR,'⭐')} Имя: @{callback.from_user.username or 'NOT_FOUND_NICKNAME'}\n"
        f"├ 🆔 ID: <code>{user_id}</code>\n"
        f"└ 📅 Регистрация: {registered}\n\n"
        f"{_ce(E_MONEY,'💵')} <b>Финансы</b>\n"
        f"├ Баланс: <b>{user['balance'] if user else 0}₽</b> {_ce(E_MONEY_FLY,'💸')}\n"
        f"└ Статус: {user['status'] if user else 'Активен'} {_ce(E_GREEN,'🟢')}\n\n"
        f"{_ce(E_CHART,'📊')} <b>Статистика</b>\n"
        f"├ Заказов: <b>{cnt}</b>\n"
        f"└ Сумма: <b>{total:,} ₽</b> {_ce(E_CHART_UP,'📈')}"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text=f"{_ce(E_CROSS,'🏠')} Главное меню", callback_data="main_menu")
    await _nav(callback, text, builder.as_markup())


@router.callback_query(F.data == "admin_orders")
async def cb_admin_orders(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        try:
            await callback.answer("Нет доступа", show_alert=True)
        except Exception:
            pass
        return

    pending = get_pending_orders()
    if not pending:
        await _nav(callback, "Нет заявок на оплату.", admin_panel())
        return

    await _nav(callback, "📋 <b>Заявки на оплату:</b>", None)
    for order in pending:
        text = (
            f"📦 <b>Заказ #{order['id']}</b>\n"
            f"Пользователь: <code>{order['user_id']}</code>\n"
            f"Товар: {order['product_name']}\n"
            f"Сумма: {order['price']:,} ₽\n"
            f"Способ: {order['payment_method']}\n"
            f"Создан: {order['created_at']}"
        )
        await callback.message.answer(text, reply_markup=admin_order_actions(order["id"]))

    try:
        await callback.answer()
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin_confirm_photo_"))
async def cb_admin_confirm_photo(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    parts = callback.data[len("admin_confirm_photo_"):].split("_")
    user_id = int(parts[0])
    embedded_order_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    if embedded_order_id:
        target = get_order(embedded_order_id)
        if not target or target["user_id"] != user_id or target["status"] != "pending":
            embedded_order_id = None
    if not embedded_order_id:
        orders = get_pending_orders()
        user_orders = [o for o in orders if o["user_id"] == user_id and o["payment_method"] in ("wallet", "nicepay")]
        if not user_orders:
            user_orders = [o for o in orders if o["user_id"] == user_id]
        if not user_orders:
            await callback.answer("Нет заявок от этого пользователя", show_alert=True)
            return
        target = max(user_orders, key=lambda o: o["id"])
    order_id = target["id"]
    confirm_order(order_id)
    logger.info(f"CONFIRM PHOTO: order_id={order_id} user_id={user_id} product_id={target['product_id']} price={target['price']} payment={target['payment_method']} status={target['status']}")
    if target["product_id"] == "deposit":
        new_balance = add_balance(user_id, target["price"])
        logger.info(f"ADD BALANCE: user_id={user_id} amount={target['price']} new_balance={new_balance}")
        msg = f"💰 <b>Баланс пополнен!</b>\n\n📄 Платёж №<b>{order_id}</b>\n💵 Сумма: <b>{target['price']:,} ₽</b>"
        try:
            await callback.bot.send_message(user_id, msg, reply_markup=bottom_menu())
        except:
            pass
    else:
        tokens = claim_order(order_id)
        if tokens:
            lines = "\n".join(f"<code>{m['token']}</code>" for m in tokens)
            msg = (
                f"✅ <b>Заказ #{order_id} подтверждён!</b>\n\n"
                f"🛒 Товар: <b>{target['product_name']}</b>\n"
                f"💵 Сумма: <b>{target['price']:,} ₽</b>\n\n"
                f"<b>Ваши токены:</b>\n{lines}"
            )
            try:
                await callback.bot.send_message(user_id, msg, reply_markup=bottom_menu())
            except:
                pass
    pending_left = [o for o in get_pending_orders() if o["user_id"] == user_id and o["id"] != order_id]
    info = f"\n\n✅ Подтверждён заказ #{order_id}"
    if pending_left:
        info += f"\n⏳ Осталось pending: {len(pending_left)} шт."
    text = callback.message.html_text + info
    try:
        await callback.message.edit_caption(caption=text, reply_markup=None)
    except:
        pass
    await callback.answer("Заказ подтверждён", show_alert=True)


@router.callback_query(F.data.startswith("admin_reject_photo_"))
async def cb_admin_reject_photo(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    parts = callback.data[len("admin_reject_photo_"):].split("_")
    user_id = int(parts[0])
    embedded_order_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    if embedded_order_id:
        target = get_order(embedded_order_id)
        if not target or target["user_id"] != user_id or target["status"] != "pending":
            embedded_order_id = None
    if not embedded_order_id:
        orders = get_pending_orders()
        user_orders = [o for o in orders if o["user_id"] == user_id and o["payment_method"] in ("wallet", "nicepay")]
        if not user_orders:
            user_orders = [o for o in orders if o["user_id"] == user_id]
        if not user_orders:
            await callback.answer("Нет заявок от этого пользователя", show_alert=True)
            return
        target = max(user_orders, key=lambda o: o["id"])
    reject_order(target["id"])
    msg = f"❌ <b>Заказ #{target['id']} отклонён администратором.</b>\n\nСвяжитесь с @Supermarket_cash_support по вопросам."
    try:
        await callback.bot.send_message(user_id, msg, reply_markup=bottom_menu())
    except:
        pass
    text = callback.message.html_text + "\n\n❌ <b>Отклонено</b>"
    try:
        await callback.message.edit_caption(caption=text, reply_markup=None)
    except:
        pass
    await callback.answer("Заказ отклонён", show_alert=True)


@router.callback_query(F.data.startswith("admin_confirm_"))
async def cb_admin_confirm(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    order_id = int(callback.data[14:])
    confirm_order(order_id)
    logger.info(f"CONFIRM PANEL: order_id={order_id}")
    text = callback.message.html_text + "\n\n✅ <b>Подтверждено</b>"
    await _nav(callback, text, None, answer_text="Заказ подтверждён", show_alert=True)

    user_id = get_order_user_id(order_id)
    if user_id:
        order = get_order(order_id)
        logger.info(f"CONFIRM PANEL: user_id={user_id} product_id={order['product_id'] if order else 'NONE'} price={order['price'] if order else 0}")
        if order and order["product_id"] == "deposit":
            new_balance = add_balance(user_id, order["price"])
            logger.info(f"CONFIRM PANEL ADD BALANCE: user_id={user_id} amount={order['price']} new_balance={new_balance}")
            msg = (
                f"💰 <b>Баланс пополнен!</b>\n\n"
                f"📄 Платёж №<b>{order_id}</b>\n"
                f"💵 Сумма: <b>{order['price']:,} ₽</b>\n\n"
                f"Средства уже на вашем балансе."
            )
            try:
                await callback.bot.send_message(user_id, msg, reply_markup=bottom_menu())
            except:
                pass
        else:
            tokens = claim_order(order_id)
            if tokens:
                qty = len(tokens)
                token_strs = [m["token"] for m in tokens]
                lines = "\n".join(f"<code>{t}</code>" for t in token_strs)
                msg = (
                    f"✅ <b>Заказ #{order_id} подтверждён и оплачен!</b>\n\n"
                    f"🛒 Товар: <b>{order['product_name']}</b>\n"
                    f"💵 Сумма: <b>{order['price']:,} ₽</b>\n\n"
                    f"<b>Ваши токены:</b>\n"
                    f"{lines}\n\n"
                    f"Сохраните их, они понадобятся для активации товара."
                )
                for adm in ADMIN_IDS:
                    try:
                        await callback.bot.send_message(
                            adm,
                            f"✅ Заказ #{order_id} подтверждён\n"
                            f"👤 Пользователь: <code>{user_id}</code>\n"
                            f"🛒 Товар: {order['product_name']}\n"
                            f"💵 Сумма: {order['price']:,} ₽\n"
                            f"🔑 Токены выданы: {qty} шт.",
                        )
                    except:
                        pass
            else:
                msg = (
                    f"✅ <b>Заказ #{order_id} подтверждён администратором!</b>\n\n"
                    f"📦 Номер заказа: <b>#{order_id}</b>\n"
                    f"🛒 Товар: <b>{order['product_name']}</b>\n"
                    f"💵 Сумма: <b>{order['price']:,} ₽</b>\n"
                    f"🕐 Время: <b>{order['created_at']}</b>"
                )
            try:
                await callback.bot.send_message(user_id, msg, reply_markup=bottom_menu())
            except:
                pass


@router.callback_query(F.data.startswith("admin_reject_"))
async def cb_admin_reject(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    order_id = int(callback.data[13:])
    reject_order(order_id)
    text = callback.message.html_text + "\n\n❌ <b>Отклонено</b>"
    await _nav(callback, text, None, answer_text="Заказ отклонён", show_alert=True)


@router.message(F.text == "📁 Каталог товаров")
async def menu_catalog(message: Message):
    text = f"{_ce(E_SHOP,'🛒')} <b>Каталог Supermarket_cash</b> {_ce(E_FIRE,'🔥')}\n\n{_ce(E_DIAMOND,'💎')} Выбери отдел:"
    await _send_with_banner(message, "catalog", text, catalog_menu())


@router.message(F.text == "👤 Профиль")
async def menu_profile(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    cnt, total = get_order_stats(user_id)
    all_orders = get_user_orders(user_id)
    pending = [o for o in all_orders if o["status"] == "pending"]
    confirmed = [o for o in all_orders if o["status"] == "confirmed"]

    registered = user["registered_at"][:10] if user else "—"

    text = (
        f"{_ce(E_INFO,'ℹ️')} <b>Твой профиль в Supermarket_cash</b> {_ce(E_SHOP,'🛒')}\n\n"
        f"{_ce(E_CHECK,'✔️')} <b>Личная информация</b>\n"
        f"├ { _ce(E_STAR,'⭐')} Имя: @{message.from_user.username or 'NOT_FOUND_NICKNAME'}\n"
        f"├ 🆔 ID: <code>{user_id}</code>\n"
        f"└ 📅 Регистрация: {registered}\n\n"
        f"{_ce(E_MONEY,'💵')} <b>Финансы</b>\n"
        f"├ Баланс: <b>{user['balance'] if user else 0}₽</b> {_ce(E_MONEY_FLY,'💸')}\n"
        f"└ Статус: {user['status'] if user else 'Активен'} {_ce(E_GREEN,'🟢')}\n\n"
        f"{_ce(E_CHART,'📊')} <b>Статистика</b>\n"
        f"├ Заказов: <b>{cnt}</b>\n"
        f"└ Сумма: <b>{total:,} ₽</b> {_ce(E_CHART_UP,'📈')}"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    await _send_with_banner(message, "profile", text, builder.as_markup())


@router.message(F.text == "💰 Пополнить баланс")
async def menu_deposit(message: Message):
    text = "💰 <b>Пополнение баланса</b>\n\nВыберите сумму пополнения или введите свою:"
    await _send_with_banner(message, "deposit", text, deposit_amounts())


@router.callback_query(F.data.startswith("deposit_"))
async def cb_deposit_amount(callback: CallbackQuery):
    raw = callback.data[8:]
    if raw == "custom":
        text = "💰 <b>Пополнение баланса</b>\n\nВведите сумму пополнения цифрами (от 1 до 200 000 ₽):"
        await _nav(callback, text, None)
        waiting_deposit[callback.from_user.id] = True
        return

    amount = int(raw)
    text = (
        f"💰 <b>Пополнение баланса</b>\n\n"
        f"📄 Платёж №<b>{callback.from_user.id}-{amount}</b>\n"
        f"💵 Сумма к оплате: <b>{amount:,} ₽</b>\n\n"
        f"❗️ Сумма пополнения указана без учета комиссии платежной системы, "
        f"но мы рады разделить комиссию с вами, чтобы сохранить низкие цены и качественный сервис."
    )
    await _nav(callback, text, deposit_payment_methods(amount))


@router.callback_query(F.data == "deposit")
async def cb_deposit_back(callback: CallbackQuery):
    text = "💰 <b>Пополнение баланса</b>\n\nВыберите сумму пополнения или введите свою:"
    await _nav(callback, text, deposit_amounts())


@router.message(F.text == "📢 Новостной канал")
async def menu_news(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Подписаться", url="https://t.me/supermarket_cash_news")
    await message.answer(
        "📢 <b>Новостной канал Supermarket_cash</b>\n\n"
        "Подпишись, чтобы быть в курсе новинок и акций!",
        reply_markup=builder.as_markup(),
    )


@router.message(F.text == "🆘 Поддержка")
async def menu_support(message: Message):
    text = (
        "🆘 <b>Поддержка</b>\n\n"
        "Свяжись с нами по любым вопросам.\n"
        "Нажми на кнопку ниже, чтобы написать администратору."
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🆘 Написать поддержке", url="https://t.me/Supermarket_cash_support")
    await _send_with_banner(message, "support", text, builder.as_markup())


@router.message(F.text == "ℹ️ Информация")
async def menu_info(message: Message):
    text = (
        "👋 <b>Добро пожаловать в Supermarket_cash!</b>\n\n"
        "🛍️ <b>Кто Мы?</b>\n"
        "Supermarket_cash — магазин расходников, который занимается продажей "
        "цифровых товаров в больших количествах.\n\n"
        "💵 <b>Цена.</b>\n"
        "Весь наш товар идет строго от поставщиков со всего мира, "
        "именно поэтому у нас самые низкие цены, которых нету ни в одном магазине.\n\n"
        "⌛️ <b>Дата основания:</b> январь 2022 год.\n"
        "За это время мы обрели клиентскую базу и базу поставщиков. "
        "Поддержка отвечает за 5 минут — этим славится наш магазин\n\n"
        "📤 <b>Оборот.</b>\n"
        "За время работы продано кэш-боксов на 200.000.000₽+ — чеки на кассе не врут"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Политика конфиденциальности", url="https://telegra.ph/Politika-konfidencialnosti-07-06-72")
    await _send_with_banner(message, "info", text, builder.as_markup())


@router.message(F.text, ~F.text.startswith("/"))
async def msg_text_handler(message: Message):
    user_id = message.from_user.id

    if user_id in waiting_converter:
        token = message.text.strip()
        order_id = waiting_converter.pop(user_id, 0)
        meta = apply_converter(token)
        if not meta:
            await message.answer("❌ Токен не найден в системе. Убедитесь, что скопировали его правильно.")
            return
        if meta.get("already_premium"):
            await message.answer("❌ Этот токен уже премиум-качества. Конвертер можно применить только один раз.")
            return
        parts = []
        if meta["needs_proxy"]:
            parts.append(f"🔌 Прокси {meta['proxy_type']}")
        if meta["needs_cert"]:
            parts.append(f"📜 Сертификат {meta['cert_type']}")
        parts_text = ", ".join(parts) if parts else "нет"
        text = (
            f"✅ <b>Конвертер успешно применён!</b>\n\n"
            f"<b>Токен улучшен:</b>\n"
            f"<code>{token}</code>\n\n"
            f"📊 <b>Новые характеристики:</b>\n"
            f"├ Качество: {meta['quality']} ({meta['quality_pct']}%)\n"
            f"├ Цена выкупа: <b>{meta['buyback_price']:,} ₽</b>\n"
            f"└ Требуемые запчасти: {parts_text}\n\n"
            f"Теперь токен можно выкупить в боте выкупа."
        )
        await message.answer(text, reply_markup=bottom_menu())
        return

    if user_id in waiting_deposit and waiting_deposit.get(user_id) is not True and waiting_deposit.get(user_id) != "BROADCAST_WAIT":
        # deposit custom handled elsewhere, skip broadcast mode
        pass
    if user_id in waiting_deposit and waiting_deposit.get(user_id) == True:
        if not message.text.isdigit():
            await message.answer("❌ Введите число, например: 500")
            return
        amount = int(message.text)
        if amount < 1 or amount > 200000:
            await message.answer("❌ Сумма от 1 до 200 000 ₽")
            return
        del waiting_deposit[user_id]
        text = (
            f"💰 <b>Пополнение баланса</b>\n\n"
            f"📄 Платёж №<b>{message.from_user.id}-{amount}</b>\n"
            f"💵 Сумма к оплате: <b>{amount:,} ₽</b>\n\n"
            f"❗️ Сумма пополнения указана без учета комиссии платежной системы, "
            f"но мы рады разделить комиссию с вами, чтобы сохранить низкие цены и качественный сервис."
        )
        await message.answer(text, reply_markup=deposit_payment_methods(amount))
        return

    pid = waiting_promo.get(user_id)
    if pid == "SET_CHANNEL":
        return  # handled by set_channel handler
    pid = waiting_promo.pop(user_id, None)
    if not pid:
        return

    code = message.text.strip()
    promo = get_promocode(code)
    if not promo:
        await message.answer("❌ Промокод не найден.")
        return

    if promo["used_count"] >= promo["max_activations"]:
        await message.answer("❌ Промокод уже использован максимальное количество раз.")
        return

    p = PRODUCTS.get(pid)
    if not p:
        await message.answer("❌ Товар не найден.")
        return

    if not use_promocode(code):
        await message.answer("❌ Не удалось активировать промокод.")
        return

    price = p["price"] * (100 - promo["discount_percent"]) // 100
    user = get_user(message.from_user.id)
    balance = user["balance"] if user else 0
    await message.answer(
        f"✅ <b>Промокод применён!</b> Скидка {promo['discount_percent']}%\n"
        f"Новая цена: <b>{price:,} ₽</b>",
        reply_markup=payment_methods(pid, price, balance),
    )


@router.callback_query(F.data.startswith("promo_"))
async def cb_promo(callback: CallbackQuery):
    pid = callback.data[6:]
    waiting_promo[callback.from_user.id] = pid
    text = (
        "🎟 <b>Введите промокод</b>\n\n"
        "Отправьте промокод в этот чат."
    )
    await callback.message.edit_text(text)
    await callback.answer()


@router.message(F.photo)
async def handle_photo(message: Message):
    await message.answer(
        "📸 Скриншот получен. Ожидайте подтверждения администратором."
    )
    user_id = message.from_user.id
    order_info = ""
    order_id_str = ""
    known_order_id = pending_crypto_order.pop(user_id, None)
    if known_order_id:
        target_order = get_order(known_order_id)
        if target_order and target_order["user_id"] == user_id and target_order["status"] == "pending":
            order_id_str = f"_{target_order['id']}"
            order_info = (
                f"\n\n📦 <b>Заказ #{target_order['id']}</b>\n"
                f"├ Товар: {target_order['product_name']}\n"
                f"├ Сумма: {target_order['price']:,} ₽\n"
                f"├ Способ: {target_order['payment_method']}\n"
                f"└ Создан: {target_order['created_at']}"
            )
    if not order_id_str:
        pending = get_pending_orders()
        user_pending = [o for o in pending if o["user_id"] == user_id and o["payment_method"] in ("wallet", "nicepay")]
        if user_pending:
            target_order = max(user_pending, key=lambda o: o["id"])
            order_id_str = f"_{target_order['id']}"
            order_info = (
                f"\n\n📦 <b>Заказ #{target_order['id']}</b>\n"
                f"├ Товар: {target_order['product_name']}\n"
                f"├ Сумма: {target_order['price']:,} ₽\n"
                f"├ Способ: {target_order['payment_method']}\n"
                f"└ Создан: {target_order['created_at']}"
            )
    caption = (
        f"📸 <b>Скриншот оплаты от пользователя</b>\n"
        f"👤 ID: <code>{user_id}</code>\n"
        f"├ Юзернейм: @{message.from_user.username or '—'}\n"
        f"└ Имя: {message.from_user.first_name or '—'}"
        f"{order_info}"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, подтвердить", callback_data=f"admin_confirm_photo_{user_id}{order_id_str}")
    builder.button(text="❌ Нет, отклонить", callback_data=f"admin_reject_photo_{user_id}{order_id_str}")
    builder.adjust(2)
    for admin_id in ADMIN_IDS:
        try:
            await message.forward(chat_id=admin_id)
            await message.bot.send_message(chat_id=admin_id, text=caption, reply_markup=builder.as_markup())
        except:
            pass


@router.message(Command("addpromo"))
async def cmd_addpromo(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    if len(parts) != 4:
        await message.answer("Использование: /addpromo КОД ПРОЦЕНТ КОЛ_ВО\nПример: /addpromo SAVE20 20 5")
        return
    try:
        code = parts[1].upper()
        percent = int(parts[2])
        uses = int(parts[3])
        create_promocode(code, percent, uses)
        await message.answer(f"✅ Промокод <b>{code}</b> создан: {percent}% на {uses} активаций.")
    except:
        await message.answer("❌ Ошибка. Формат: /addpromo КОД ПРОЦЕНТ КОЛ_ВО")


@router.message(Command("listpromo"))
async def cmd_listpromo(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    promos = list_promocodes()
    if not promos:
        await message.answer("Нет промокодов.")
        return
    lines = ["📋 <b>Промокоды:</b>\n"]
    for p in promos:
        left = p["max_activations"] - p["used_count"]
        lines.append(
            f"<b>{p['code']}</b> — {p['discount_percent']}% | \n"
            f"осталось: {left}/{p['max_activations']}\n"
        )

@router.message(Command("delpromo"))
async def cmd_delpromo(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    code = message.text.removeprefix("/delpromo").strip()
    if not code:
        await message.answer("Использование: /delpromo КОД")
        return
    delete_promocode(code)
    await message.answer(f"✅ Промокод <b>{code}</b> удалён.")


@router.message(Command("users"))
async def cmd_users(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    users = get_all_users()
    if not users:
        await message.answer("Нет пользователей.")
        return
    lines = ["👥 <b>Пользователи:</b>\n"]
    for u in users:
        name = u["first_name"] or u["username"] or str(u["user_id"])
        lines.append(
            f"ID: <code>{u['user_id']}</code> | {name} | "
            f"Баланс: {u['balance']}₽ | {u['status']}"
        )
    for i in range(0, len(lines), 20):
        await message.answer("\n".join(lines[i:i+20]))


@router.message(Command("addbalance"))
async def cmd_addbalance(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /addbalance USER_ID СУММА\nПример: /addbalance 123456789 500")
        return
    try:
        user_id = int(parts[1])
        amount = int(parts[2])
        add_balance(user_id, amount)
        user = get_user(user_id)
        await message.answer(
            f"✅ Пользователю <code>{user_id}</code> начислено <b>{amount}₽</b>.\n"
            f"Текущий баланс: <b>{user['balance'] if user else 0}₽</b>"
        )
    except:
        await message.answer("❌ Ошибка. Формат: /addbalance USER_ID СУММА")

# ── Админ: обязательная подписка ──
@router.callback_query(F.data == "admin_set_channel")
async def cb_admin_set_channel(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    cur = get_required_channel() or "не установлен"
    await callback.message.edit_text(
        f"🔒 <b>Обязательная подписка</b>\n\nТекущий канал: <code>{cur}</code>\n\nОтправь @username канала или ID (например @supermarket_cash). Для отключения отправь <code>off</code>",
        reply_markup=InlineKeyboardBuilder().button(text="❌ Отмена", callback_data="admin_cancel_give").as_markup()
    )
    waiting_promo[callback.from_user.id] = "SET_CHANNEL"  # reuse dict for state
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.message.edit_text(
        "📢 <b>Рассылка</b>\n\nОтправь сообщение (текст/фото/видео) для рассылки всем пользователям.\nДля отмены — /cancel",
        reply_markup=InlineKeyboardBuilder().button(text="❌ Отмена", callback_data="admin_cancel_give").as_markup()
    )
    waiting_deposit[callback.from_user.id] = "BROADCAST_WAIT"  # reuse
    await callback.answer()

broadcast_state: dict[int, bool] = {}

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    text = message.text.removeprefix("/broadcast").strip()
    if not text:
        await message.answer("Использование: /broadcast ТЕКСТ\nИли просто отправь сообщение после нажатия кнопки Рассылка")
        return
    users = get_all_users()
    sent = 0
    for u in users:
        try:
            await message.bot.send_message(u["user_id"], text)
            sent += 1
        except:
            pass
    await message.answer(f"✅ Рассылка завершена: {sent}/{len(users)}")

# обработка broadcast из состояния ожидания
@router.message(F.text | F.photo | F.video | F.document, lambda m: m.from_user.id in ADMIN_IDS and waiting_deposit.get(m.from_user.id) == "BROADCAST_WAIT")
async def handle_admin_broadcast_message(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    # check for channel setting mode
    if waiting_promo.get(message.from_user.id) == "SET_CHANNEL":
        txt = message.text.strip() if message.text else ""
        if txt.lower() == "off":
            set_required_channel("")
            waiting_promo.pop(message.from_user.id, None)
            await message.answer("✅ Обязательная подписка отключена", reply_markup=admin_panel())
            return
        if txt and (txt.startswith("@") or txt.lstrip("-").isdigit()):
            set_required_channel(txt)
            waiting_promo.pop(message.from_user.id, None)
            waiting_deposit.pop(message.from_user.id, None)
            await message.answer(f"✅ Канал установлен: <code>{txt}</code>", reply_markup=admin_panel())
            return
        # не канал — тогда считаем что это broadcast текст, но SET_CHANNEL приоритет
        waiting_promo.pop(message.from_user.id, None)

    # broadcast mode
    if waiting_deposit.get(message.from_user.id) == "BROADCAST_WAIT":
        waiting_deposit.pop(message.from_user.id, None)
        users = get_all_users()
        if not users:
            await message.answer("Нет пользователей для рассылки")
            return
        await message.answer(f"⏳ Рассылка {len(users)} пользователям...")
        sent = 0
        failed = 0
        for u in users:
            try:
                await message.copy_to(chat_id=u["user_id"])
                sent += 1
            except Exception as e:
                failed += 1
            # антифлуд
        await message.answer(f"✅ Рассылка завершена\nОтправлено: {sent}\nОшибок: {failed}", reply_markup=admin_panel())

@router.callback_query(F.data == "admin_list")
async def cb_admin_list(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    txt = "👑 <b>Админы Supermarket_cash</b>\n\n"
    for aid in ADMIN_IDS:
        mark = " 👑 главный" if aid == MAIN_ADMIN else ""
        txt += f"• <code>{aid}</code>{mark}\n"
    txt += "\nКоманды:\n/addadmin ID — добавить\n/deladmin ID — удалить (только главный)"
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить", callback_data="admin_add_prompt")
    builder.button(text="➖ Удалить", callback_data="admin_del_prompt")
    builder.button(text="⬅️ Назад", callback_data="admin_back")
    builder.adjust(2)
    builder.row(InlineKeyboardBuilder().button(text="⬅️ Назад", callback_data="admin_back").as_markup().inline_keyboard[0][0])
    # simplify
    b2 = InlineKeyboardBuilder()
    b2.button(text="⬅️ Назад", callback_data="admin_back")
    await callback.message.edit_text(txt, reply_markup=b2.as_markup())
    await callback.answer()

@router.callback_query(F.data == "admin_back")
async def cb_admin_back(callback: CallbackQuery):
    await callback.message.edit_text("🔧 Панель администратора", reply_markup=admin_panel())
    await callback.answer()

@router.message(Command("addadmin"))
async def cmd_addadmin(message: Message):
    if message.from_user.id != MAIN_ADMIN:
        await message.answer("❌ Только главный админ может добавлять админов")
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /addadmin USER_ID")
        return
    nid = int(parts[1])
    if nid in ADMIN_IDS:
        await message.answer("Уже админ")
        return
    # динамически добавляем (в памяти до рестарта, + предлагаем в .env)
    ADMIN_IDS.append(nid)
    # также обновим .env для сохранения
    try:
        import os
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        txt = open(env_path, encoding="utf-8").read()
        if str(nid) not in txt:
            txt = txt.replace(f"ADMIN_IDS={','.join(map(str, ADMIN_IDS[:-1]))}", f"ADMIN_IDS={','.join(map(str, ADMIN_IDS))}")
            # fallback if not matched, just append
            if str(nid) not in txt:
                txt = txt.replace("ADMIN_IDS=", f"ADMIN_IDS={nid},")
            open(env_path, "w", encoding="utf-8").write(txt)
    except Exception as e:
        logger.warning(f"addadmin env write fail {e}")
    await message.answer(f"✅ Админ <code>{nid}</code> добавлен", reply_markup=admin_panel())

@router.message(Command("deladmin"))
async def cmd_deladmin(message: Message):
    if message.from_user.id != MAIN_ADMIN:
        await message.answer("❌ Только главный админ может удалять")
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /deladmin USER_ID")
        return
    nid = int(parts[1])
    if nid == MAIN_ADMIN:
        await message.answer("❌ Нельзя удалить главного")
        return
    if nid not in ADMIN_IDS:
        await message.answer("Не админ")
        return
    ADMIN_IDS.remove(nid)
    try:
        import os
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        txt = open(env_path, encoding="utf-8").read()
        # rewrite ADMIN_IDS line
        import re
        txt = re.sub(r"ADMIN_IDS=.*", f"ADMIN_IDS={','.join(map(str, ADMIN_IDS))}", txt)
        open(env_path, "w", encoding="utf-8").write(txt)
    except Exception as e:
        logger.warning(f"deladmin env write fail {e}")
    await message.answer(f"✅ Админ <code>{nid}</code> удалён", reply_markup=admin_panel())

@router.message(Command("setchannel"))
async def cmd_setchannel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    arg = message.text.removeprefix("/setchannel").strip()
    if not arg:
        cur = get_required_channel() or "не установлен"
        await message.answer(f"Текущий канал: <code>{cur}</code>\nИспользование: /setchannel @username или /setchannel off")
        return
    if arg.lower() == "off":
        set_required_channel("")
        await message.answer("✅ Обязательная подписка отключена")
    else:
        set_required_channel(arg)
        await message.answer(f"✅ Канал установлен: <code>{arg}</code>")

# Перехват SET_CHANNEL через обычный текст (когда админ в режиме ожидания)
@router.message(F.text, lambda m: m.from_user.id in ADMIN_IDS and waiting_promo.get(m.from_user.id) == "SET_CHANNEL")
async def handle_set_channel_text(message: Message):
    txt = message.text.strip()
    if txt.lower() == "off":
        set_required_channel("")
        waiting_promo.pop(message.from_user.id, None)
        waiting_deposit.pop(message.from_user.id, None)
        await message.answer("✅ Обязательная подписка отключена", reply_markup=admin_panel())
        return
    if txt.startswith("@") or txt.lstrip("-").isdigit() or "t.me" in txt:
        # extract @username if t.me link
        if "t.me/" in txt:
            txt = "@" + txt.split("t.me/")[-1].split("/")[0].split("?")[0]
            if not txt.startswith("@"):
                txt = "@"+txt
        set_required_channel(txt)
        waiting_promo.pop(message.from_user.id, None)
        waiting_deposit.pop(message.from_user.id, None)
        await message.answer(f"✅ Канал установлен: <code>{txt}</code>", reply_markup=admin_panel())
    else:
        await message.answer("❌ Отправь @username или off")