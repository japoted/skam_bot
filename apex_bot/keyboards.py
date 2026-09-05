from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import config
from config import CATEGORIES, OFFER_URL


NEWS_URL = "https://t.me/+BqGzk8yKg7RkM2Vi"


def bottom_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📁 Каталог товаров")
    builder.button(text="👤 Профиль")
    builder.button(text="💰 Пополнить баланс")
    builder.button(text="🆘 Поддержка")
    builder.button(text="ℹ️ Информация")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Меню")


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 Новостной канал", url=NEWS_URL))
    builder.row(InlineKeyboardButton(text="📄 Оферта", url=OFFER_URL))
    return builder.as_markup()


def catalog_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    emojis = {"dns_tokens": "🌐", "proxies": "🛡️", "manuals": "📚", "certificates": "🏅", "dns_filter": "🔍", "dns_converter": "🔄", "dns_adapter": "🔌", "filter": "🧹"}
    for key, name in CATEGORIES.items():
        emoji = emojis.get(key, "📁")
        builder.button(text=f"{emoji} {name}", callback_data=f"cat_{key}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    return builder.as_markup()


def category_products(category_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pid, p in config.PRODUCTS.items():
        if p["category"] == category_key:
            stock = "✅" if p["in_stock"] else "❌"
            builder.row(
                InlineKeyboardButton(
                    text=f"{p['name']} | {p['price']}₽ {stock}",
                    callback_data=f"product_{pid}",
                )
            )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog"))
    return builder.as_markup()


def product_actions(product_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🛒 Приобрести", callback_data=f"qty_{product_id}")
    )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="catalog"))
    return builder.as_markup()


def quantity_selector(product_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for qty in [1, 2, 3, 5, 10, 15, 20]:
        builder.button(text=f"{qty} шт.", callback_data=f"sel_qty_{product_id}_{qty}")
    builder.adjust(4)
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="catalog"))
    return builder.as_markup()


def payment_methods(product_id: str, price: int | None = None, balance: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    p = config.PRODUCTS[product_id]
    final_price = price if price is not None else p["price"]
    builder.row(
        InlineKeyboardButton(text="💳 NicePay (СБП / Карта)", callback_data=f"pay_card_{product_id}_{final_price}"),
    )
    builder.row(
        InlineKeyboardButton(text="💎 Криптовалюта (кошелёк)", callback_data=f"pay_wallet_{product_id}_{final_price}"),
    )
    builder.row(
        InlineKeyboardButton(text="⭐ Звёзды Telegram", callback_data=f"pay_stars_{product_id}_{final_price}"),
    )
    if balance >= final_price and balance > 0:
        builder.row(
            InlineKeyboardButton(text=f"💰 Баланс ({balance}₽)", callback_data=f"pay_balance_{product_id}_{final_price}"),
        )
    builder.row(
        InlineKeyboardButton(text="🎟 Промокод", callback_data=f"promo_{product_id}"),
    )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="catalog"))
    return builder.as_markup()


def deposit_amounts() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    amounts = [250, 500, 1000, 2000, 3000, 4000, 5000, 10000, 15000, 20000]
    row = []
    for a in amounts:
        row.append(InlineKeyboardButton(text=f"{a:,}₽", callback_data=f"deposit_{a}"))
        if len(row) == 3:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)
    builder.row(InlineKeyboardButton(text="💳 Другая сумма →", callback_data="deposit_custom"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu"))
    return builder.as_markup()


def deposit_payment_methods(amount: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 NicePay (СБП / Карта)", callback_data=f"dep_pay_card_{amount}"))
    builder.row(InlineKeyboardButton(text="💎 Криптовалюта (кошелёк)", callback_data=f"dep_pay_wallet_{amount}"))
    builder.row(InlineKeyboardButton(text="⭐ Звёзды Telegram", callback_data=f"dep_pay_stars_{amount}"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="deposit"))
    return builder.as_markup()


def admin_panel() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Заявки на оплату", callback_data="admin_orders"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    return builder.as_markup()


def admin_order_actions(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_confirm_{order_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_{order_id}"),
    )
    return builder.as_markup()
