from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import config
from config import CATEGORIES, OFFER_URL


NEWS_URL = "https://t.me/Cash_shop_channel"

# Premium animated — NewsEmoji https://t.me/addemoji/NewsEmoji
CATEGORY_PREMIUM = {
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
PRODUCT_PREMIUM = {
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



def bottom_menu() -> ReplyKeyboardMarkup:
    # Нижнее меню как на референсе: контурные иконки + чистый текст
    # Каталог — 5210997770567062009, Профиль — 5210935566555714476
    # Баланс — 5208509635882947404
    # Инфо — 5210889687715059785, Поддержка — 5208651176530185025
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="Каталог товаров", icon_custom_emoji_id="5210997770567062009"))
    builder.row(
        KeyboardButton(text="Профиль", icon_custom_emoji_id="5210935566555714476"),
        KeyboardButton(text="Пополнить баланс", icon_custom_emoji_id="5208509635882947404"),
    )
    builder.row(
        KeyboardButton(text="Информация о магазине", icon_custom_emoji_id="5210889687715059785"),
        KeyboardButton(text="Поддержка", icon_custom_emoji_id="5208651176530185025"),
    )
    builder.adjust(1, 2, 2)
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Меню")


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Новостной канал", icon_custom_emoji_id="5458603043203327669", url=NEWS_URL))
    builder.row(InlineKeyboardButton(text="Оферта", icon_custom_emoji_id="5211204787990730015", url=OFFER_URL))
    return builder.as_markup()


def catalog_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, name in CATEGORIES.items():
        icon = CATEGORY_PREMIUM.get(key)
        # name already clean without emoji (config), add icon via premium
        if icon:
            builder.row(InlineKeyboardButton(text=name, icon_custom_emoji_id=icon, callback_data=f"cat_{key}"))
        else:
            builder.button(text=name, callback_data=f"cat_{key}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    return builder.as_markup()


def category_products(category_key: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    import re
    for pid, p in config.PRODUCTS.items():
        if p["category"] == category_key and p["in_stock"]:
            clean = re.sub(r'^[^\w\u0400-\u04FF]+', '', p['name']).lstrip()
            icon = PRODUCT_PREMIUM.get(pid)
            txt = f"{clean} | {p['price']}₽"
            if icon:
                builder.row(InlineKeyboardButton(text=txt, icon_custom_emoji_id=icon, callback_data=f"product_{pid}"))
            else:
                builder.row(InlineKeyboardButton(text=f"{txt} ✅", callback_data=f"product_{pid}"))
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
        InlineKeyboardButton(text="🟢 Карта / СБП (авто)", callback_data=f"pay_card_{product_id}_{final_price}"),
    )
    builder.row(
        InlineKeyboardButton(text="🟡 Криптовалюта TRC20", callback_data=f"pay_wallet_{product_id}_{final_price}"),
    )
    builder.row(
        InlineKeyboardButton(text="🔵 Звёзды Telegram", callback_data=f"pay_stars_{product_id}_{final_price}"),
    )
    if balance >= final_price and balance > 0:
        builder.row(
            InlineKeyboardButton(text=f"🟣 Баланс ({balance}₽)", callback_data=f"pay_balance_{product_id}_{final_price}"),
        )
    builder.row(
        InlineKeyboardButton(text="🎁 Промокод", callback_data=f"promo_{product_id}"),
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
    builder.row(InlineKeyboardButton(text="🟢 Карта / СБП (авто)", callback_data=f"dep_pay_card_{amount}"))
    builder.row(InlineKeyboardButton(text="🟡 Криптовалюта TRC20", callback_data=f"dep_pay_wallet_{amount}"))
    builder.row(InlineKeyboardButton(text="🔵 Звёзды Telegram", callback_data=f"dep_pay_stars_{amount}"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="deposit"))
    return builder.as_markup()


def admin_panel() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🟠 Заявки на оплату", callback_data="admin_orders"),
    )
    builder.row(
        InlineKeyboardButton(text="🟢 Выдать баланс", callback_data="admin_give_balance"),
    )
    builder.row(
        InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
    )
    builder.row(
        InlineKeyboardButton(text="🔒 Обязательная подписка", callback_data="admin_set_channel"),
    )
    builder.row(
        InlineKeyboardButton(text="👑 Админы", callback_data="admin_list"),
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
