import os

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, FSInputFile,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

CUSTOM_EMOJI = [
    "5210935566555714476", "5208444283660571410", "5211209302001355411",
    "5211219901980643543", "5210733157631952350", "5210997770567062009",
    "5210838989921106328", "5208610193952248503", "5208509635882947404",
    "5211096541929968385", "5211226456100738227", "5208651176530185025",
    "5210782897648212515", "5211204787990730015", "5208511706057184373",
    "5208752507693601793", "5210889687715059785", "5210970420215320683",
    "5211051638046887847", "5211010719893460599", "5208723615448602039",
    "5208759023158988404", "5436040291507247633", "5461117441612462242",
    "5431897022456145283", "5375296873982604963", "5472055112702629499",
    "5357080225463149588", "5985472565508832112",
]


def _ce(eid: str, fallback: str = "⭐") -> str:
    return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'

import config
from config import ADMIN_IDS, PRODUCTS, CARD_NUMBER, CARD_HOLDER, BANK_NAME, PHONE_NUMBER, CRYPTO_WALLET, OFFER_URL
from database import (
    register_user, get_user, get_user_orders, get_order_stats,
    create_order, get_pending_orders, confirm_order, reject_order,
    get_order_user_id, get_promocode, use_promocode,
    list_promocodes, create_promocode, delete_promocode,
    get_all_users, add_balance, claim_order, get_order,
    get_token_meta, apply_converter,
)
from keyboards import (
    main_menu, bottom_menu, catalog_menu, category_products,
    product_actions, quantity_selector, payment_methods,
    admin_panel, admin_order_actions,
    deposit_amounts, deposit_payment_methods,
    NEWS_URL,
)

waiting_promo: dict[int, str] = {}
waiting_deposit: dict[int, bool] = {}
pending_quantity: dict[int, int] = {}
waiting_converter: dict[int, str] = {}

router = Router()

BANNER = os.path.join(os.path.dirname(__file__), "5438570968302427672.jpg")
BANNERS = {
    "support": os.path.join(os.path.dirname(__file__), "5379983559935860452.jpg"),
    "profile": os.path.join(os.path.dirname(__file__), "провиль.jfif"),
    "deposit": os.path.join(os.path.dirname(__file__), "пополнение.jfif"),
    "dns_tokens": os.path.join(os.path.dirname(__file__), "5442751204137048819.jpg"),
    "proxies": os.path.join(os.path.dirname(__file__), "баннер прокси.jfif"),
    "licenses": os.path.join(os.path.dirname(__file__), "лицензия.jfif"),
    "info": os.path.join(os.path.dirname(__file__), "информация.jfif"),
    "catalog": os.path.join(os.path.dirname(__file__), "каталог.jfif"),
}


async def _nav(callback: CallbackQuery, text: str, reply_markup, answer_text="", show_alert=False):
    if callback.message.caption is not None:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=reply_markup)
    else:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    if show_alert:
        await callback.answer(answer_text, show_alert=True)
    else:
        await callback.answer()


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
        f"<b>👋 Добро пожаловать, {user_first}!</b>\n\n"
        "<b>Добро пожаловать в RICH MARKET!</b>\n\n"
        "<b>У нас ты найдешь самые дешевые материалы для заработка!</b>\n\n"
        "<b>Заглядывай в каталог 👇</b>\n"
        "<b>Выбери раздел и выбирай товары по самым приятным ценам</b>"
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
    await _send_main_menu(message)


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
    text = "📁 <b>Каталог товаров</b>\n\nВыбери необходимую категорию товаров:"
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
    text = f"📂 <b>{cat_name}</b>\n\nВыбери нужный товар:"
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

    stock = "✅ В наличии" if p["in_stock"] else "❌ Нет в наличии"
    text = (
        f"<b>{p['name']}</b>\n\n"
        f"<b>Описание:</b> {p['desc']}\n\n"
        f"<b>Цена:</b> {p['price']:,} ₽\n"
        f"<b>Статус:</b> {stock}"
    )
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
    order_id = create_order(callback.from_user.id, pid, p["name"], price, "card", qty)

    text = (
        f"💳 <b>Оплата банковской картой</b>\n\n"
        f"Товар: <b>{p['name']}</b> x{qty}\n"
        f"Сумма: <b>{price:,} ₽</b>\n"
        f"Номер заказа: <b>#{order_id}</b>\n\n"
        f"📌 <b>Реквизиты для перевода:</b>\n"
        f"<code>{CARD_NUMBER}</code>\n"
        f"🏦 {BANK_NAME}\n"
        f"👤 {CARD_HOLDER}\n"
        f"📞 {PHONE_NUMBER}\n\n"
        f"После перевода отправьте скриншот оплаты в этот чат.\n"
        f"Администратор проверит и подтвердит заказ."
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
    is_converter = config.PRODUCTS.get(order["product_id"], {}).get("category") == "dns_converter"
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

    text = (
        f"💎 <b>Оплата криптовалютой (кошелёк)</b>\n\n"
        f"Товар: <b>{p['name']}</b> x{qty}\n"
        f"Сумма: <b>{price:,} ₽</b>\n"
        f"Номер заказа: <b>#{order_id}</b>\n\n"
        f"📌 <b>Адрес кошелька USDT (TON):</b>\n"
        f"<code>{CRYPTO_WALLET}</code>\n\n"
        f"После перевода отправьте скриншот оплаты в этот чат.\n"
        f"Администратор проверит и подтвердит заказ.\n\n"
        f"👤 @richhelper1 — по всем вопросам писать администратору"
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
    create_order(callback.from_user.id, "deposit", "Пополнение баланса", amount, "card")
    text = (
        f"💳 <b>Оплата банковской картой</b>\n\n"
        f"📄 Платёж №<b>{callback.from_user.id}-{amount}</b>\n"
        f"💵 Сумма: <b>{amount:,} ₽</b>\n\n"
        f"📌 <b>Реквизиты для перевода:</b>\n"
        f"<code>{CARD_NUMBER}</code>\n"
        f"🏦 {BANK_NAME}\n"
        f"👤 {CARD_HOLDER}\n"
        f"📞 {PHONE_NUMBER}\n\n"
        f"После перевода отправьте скриншот в этот чат.\n"
        f"Администратор проверит и зачислит средства."
    )
    await _nav(callback, text, None)


@router.callback_query(F.data.startswith("dep_pay_wallet_"))
async def cb_dep_pay_wallet(callback: CallbackQuery):
    amount = int(callback.data.split("_")[-1])
    create_order(callback.from_user.id, "deposit", "Пополнение баланса", amount, "wallet")
    text = (
        f"💎 <b>Оплата криптовалютой (кошелёк)</b>\n\n"
        f"📄 Платёж №<b>{callback.from_user.id}-{amount}</b>\n"
        f"💵 Сумма: <b>{amount:,} ₽</b>\n\n"
        f"📌 <b>Адрес кошелька USDT (TON):</b>\n"
        f"<code>{CRYPTO_WALLET}</code>\n\n"
        f"После перевода отправьте скриншот в этот чат.\n"
        f"Администратор проверит и зачислит средства.\n\n"
        f"👤 @richhelper1 — по всем вопросам писать администратору"
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

    registered = user["registered_at"][:10] if user else "—"

    text = (
        "👤 <b>Ваш профиль</b>\n\n"
        "├ <b>Личная информация</b>\n"
        f"├ Имя: @{callback.from_user.username or 'NOT_FOUND_NICKNAME'}\n"
        f"├ ID: <code>{user_id}</code>\n"
        f"└ Дата регистрации в боте: {registered}\n\n"
        "├ <b>Финансы</b>\n"
        f"├ Баланс: {user['balance'] if user else 0}₽\n"
        f"└ Статус: {user['status'] if user else 'Активен'}\n\n"
        "├ <b>Статистика</b>\n"
        f"├ Количество заказов: {cnt}\n"
        f"└ Общая сумма покупок: {total:,} ₽"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    await _nav(callback, text, builder.as_markup())


@router.callback_query(F.data == "admin_orders")
async def cb_admin_orders(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
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

    await callback.answer()


@router.callback_query(F.data.startswith("admin_confirm_"))
async def cb_admin_confirm(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    order_id = int(callback.data[14:])
    confirm_order(order_id)
    text = callback.message.html_text + "\n\n✅ <b>Подтверждено</b>"
    await _nav(callback, text, None, answer_text="Заказ подтверждён", show_alert=True)

    user_id = get_order_user_id(order_id)
    if user_id:
        order = get_order(order_id)
        if order and order["product_id"] == "deposit":
            add_balance(user_id, order["price"])
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


@router.callback_query(F.data.startswith("admin_confirm_photo_"))
async def cb_admin_confirm_photo(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    user_id = int(callback.data[20:])
    orders = get_pending_orders()
    target = None
    for o in orders:
        if o["user_id"] == user_id:
            target = o
            break
    if not target:
        await callback.answer("Нет заявок от этого пользователя", show_alert=True)
        return
    order_id = target["id"]
    confirm_order(order_id)
    if target["product_id"] == "deposit":
        add_balance(user_id, target["price"])
        msg = f"💰 <b>Баланс пополнен!</b>\n\n💵 Сумма: <b>{target['price']:,} ₽</b>"
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
    text = callback.message.html_text + "\n\n✅ <b>Подтверждено</b>"
    await callback.message.edit_caption(caption=text, reply_markup=None)
    await callback.answer("Заказ подтверждён", show_alert=True)


@router.callback_query(F.data.startswith("admin_reject_photo_"))
async def cb_admin_reject_photo(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    user_id = int(callback.data[18:])
    orders = get_pending_orders()
    target = None
    for o in orders:
        if o["user_id"] == user_id:
            target = o
            break
    if not target:
        await callback.answer("Нет заявок от этого пользователя", show_alert=True)
        return
    reject_order(target["id"])
    msg = f"❌ <b>Заказ #{target['id']} отклонён администратором.</b>\n\nСвяжитесь с @richhelper1 по вопросам."
    try:
        await callback.bot.send_message(user_id, msg, reply_markup=bottom_menu())
    except:
        pass
    text = callback.message.html_text + "\n\n❌ <b>Отклонено</b>"
    await callback.message.edit_caption(caption=text, reply_markup=None)
    await callback.answer("Заказ отклонён", show_alert=True)


@router.message(F.text == "📁 Каталог товаров")
async def menu_catalog(message: Message):
    text = "📁 <b>Каталог товаров</b>\n\nВыбери необходимую категорию товаров:"
    await _send_with_banner(message, "catalog", text, catalog_menu())


@router.message(F.text == "👤 Профиль")
async def menu_profile(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    cnt, total = get_order_stats(user_id)

    registered = user["registered_at"][:10] if user else "—"

    text = (
        "👤 <b>Ваш профиль</b>\n\n"
        "├ <b>Личная информация</b>\n"
        f"├ Имя: @{message.from_user.username or 'NOT_FOUND_NICKNAME'}\n"
        f"├ ID: <code>{user_id}</code>\n"
        f"└ Дата регистрации в боте: {registered}\n\n"
        "├ <b>Финансы</b>\n"
        f"├ Баланс: {user['balance'] if user else 0}₽\n"
        f"└ Статус: {user['status'] if user else 'Активен'}\n\n"
        "├ <b>Статистика</b>\n"
        f"├ Количество заказов: {cnt}\n"
        f"└ Общая сумма покупок: {total:,} ₽"
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
    builder.button(text="📢 Подписаться", url="https://t.me/+BqGzk8yKg7RkM2Vi")
    await message.answer(
        "📢 <b>Новостной канал RICH MARKET</b>\n\n"
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
    builder.button(text="🆘 Написать поддержке", url="https://t.me/richhelper1")
    await _send_with_banner(message, "support", text, builder.as_markup())


@router.message(F.text == "ℹ️ Информация")
async def menu_info(message: Message):
    text = (
        "👋 <b>Приветствуем в магазине Rich Market!</b>\n\n"
        "🛍️ <b>Кто Мы?</b>\n"
        "Rich Market — магазин расходников, который занимается продажей "
        "цифровых товаров в больших количествах.\n\n"
        "💵 <b>Цена.</b>\n"
        "Весь наш товар идет строго от поставщиков со всего мира, "
        "именно поэтому у нас самые низкие цены, которых нету ни в одном магазине.\n\n"
        "⌛️ <b>Дата основания:</b> январь 2022 год.\n"
        "За это время мы обрели клиентскую базу и базу поставщиков. "
        "Поддержка отвечает за 5 минут — этим славится наш магазин\n\n"
        "📤 <b>Оборот.</b>\n"
        "За 4 года работы было продано товаров свыше 200.000.000₽"
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

    if user_id in waiting_deposit:
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
    caption = (
        f"📸 <b>Скриншот оплаты от пользователя</b>\n"
        f"👤 ID: <code>{message.from_user.id}</code>\n"
        f"├ Юзернейм: @{message.from_user.username or '—'}\n"
        f"└ Имя: {message.from_user.first_name or '—'}"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, подтвердить", callback_data=f"admin_confirm_photo_{message.from_user.id}")
    builder.button(text="❌ Нет, отклонить", callback_data=f"admin_reject_photo_{message.from_user.id}")
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
            f"<b>{p['code']}</b> — {p['discount_percent']}% | "
            f"осталось: {left}/{p['max_activations']}"
        )
    await message.answer("\n".join(lines))


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
