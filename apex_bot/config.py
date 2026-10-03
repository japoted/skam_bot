import os

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass


def _get_int_list(name: str) -> list[int]:
    raw = os.getenv(name, "")
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def _require(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        raise RuntimeError(f"Не задана переменная окружения {name} (см. .env.example)")
    return value


TOKEN = _require("BOT_TOKEN")
ADMIN_IDS = _get_int_list("ADMIN_IDS")
MAIN_ADMIN = 8791839180  # главный

PROXY = os.getenv("PROXY", "")  # например "http://user:pass@ip:port" или "socks5://ip:port"

OFFER_URL = os.getenv("OFFER_URL", "")

# ── NicePay (https://nicepay.io) — СБП/карты ──
NICEPAY_MERCHANT_ID = os.getenv("NICEPAY_MERCHANT_ID", "6abfd3b3f58184ee8c0fcf31")
NICEPAY_SECRET_KEY = os.getenv("NICEPAY_SECRET_KEY", "RttmJ-COlwa-jlvhR-Rwzal-2Jra8")
NICEPAY_API_URL = os.getenv("NICEPAY_API_URL", "https://nicepay.io")
NICEPAY_CURRENCY = os.getenv("NICEPAY_CURRENCY", "RUB")
# публичный URL куда NicePay будет слать webhook, например https://xxx.bothost.tech/nicepay/callback
# order_id дописывается автоматически: {NICEPAY_CALLBACK_URL}?order_id=123
NICEPAY_CALLBACK_URL = os.getenv("NICEPAY_CALLBACK_URL", "")
NICEPAY_SUCCESS_URL = os.getenv("NICEPAY_SUCCESS_URL", "https://t.me/")
NICEPAY_CANCEL_URL = os.getenv("NICEPAY_CANCEL_URL", "https://t.me/")
# порт для локального webhook-сервера (aiohttp, на BotHost обычно 80)
NICEPAY_WEBHOOK_PORT = int(os.getenv("NICEPAY_WEBHOOK_PORT", "80"))
NICEPAY_WEBHOOK_PATH = os.getenv("NICEPAY_WEBHOOK_PATH", "/nicepay/callback")

CRYPTO_WALLET = os.getenv("CRYPTO_WALLET", "")

REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "")  # например @supermarket_cash

CATEGORIES = {
    "cash_boxes": "ТУРБО-Боксы",
    "shelf_proxies": "Прокси-Полки",
    "market_certs": "Сертификаты Свежести",
    "cart_filter": "Фильтр Корзины ТУРБО",
    "market_converter": "Конвертер ТУРБО",
    "manuals": "Мануалы по Заработку",
    "accounts": "Аккаунты",
    "services": "Сервисы",
    "cards": "Карты и Дропы",
}

PRODUCTS = {
    "turbo_lite": {
        "category": "cash_boxes",
        "name": "🛍 ТУРБО-ЛАЙТ Бокс",
        "price": 1499,
        "desc": "Лайт-корзина Supermarket_cash — входной ТУРБО.\nЧистый кэш-след, быстрая касса, лёгкая привязка. Для теста полки и первого чека. Бери и кати к кассе!",
        "in_stock": True,
    },
    "turbo": {
        "category": "cash_boxes",
        "name": "⚡️ ТУРБО Бокс",
        "price": 2499,
        "desc": "Хит продаж — классический ТУРБО.\nУсиленный чек, совместим с Binance/Bybit/OKX, держит фрод. Баланс: цена/качество = как тележка, набитая кэшем.",
        "in_stock": True,
    },
    "x_turbo": {
        "category": "cash_boxes",
        "name": "🔥 ИКС-ТУРБО Бокс",
        "price": 3990,
        "desc": "ИКС-ТУРБО — полка премиум.\nПул резервных кошельков, маршрутизация по 15 кассам, выкупается с надбавкой 40%. Для тех, кто берёт по-крупному в Supermarket_cash.",
        "in_stock": True,
    },
    "giga_turbo": {
        "category": "cash_boxes",
        "name": "💎 ГИГА-ТУРБО Бокс",
        "price": 5990,
        "desc": "ГИГА-ТУРБО — фура кэша.\nМакс. доверие, антифрод-броня, ликвид на любой кассе. Выкупается с надбавкой до 60%. Когда нужен весь супермаркет.",
        "in_stock": True,
    },
    "cash_eco": {
        "category": "cash_boxes",
        "name": "🛒 ТУРБО-ЛАЙТ Бокс",
        "price": 1499,
        "desc": "Алиас turbo_lite",
        "in_stock": False,
    },
    "cash_pro": {
        "category": "cash_boxes",
        "name": "⚡ ТУРБО Бокс",
        "price": 2499,
        "desc": "Алиас turbo",
        "in_stock": False,
    },
    "cash_vip": {
        "category": "cash_boxes",
        "name": "🔥 ИКС-ТУРБО Бокс",
        "price": 3990,
        "desc": "Алиас x_turbo",
        "in_stock": False,
    },
    "dns_eco": {
        "category": "cash_boxes",
        "name": "КЭШ-БОКС ECO",
        "price": 1799,
        "desc": "Алиас",
        "in_stock": False,
    },
    "dns_pro": {
        "category": "cash_boxes",
        "name": "КЭШ-БОКС PRO",
        "price": 2990,
        "desc": "Алиас",
        "in_stock": False,
    },
    "dns_vip": {
        "category": "cash_boxes",
        "name": "КЭШ-БОКС VIP",
        "price": 4990,
        "desc": "Алиас",
        "in_stock": False,
    },
    "proxy_ipv4": {
        "category": "shelf_proxies",
        "name": "🛡 Полка IPv4 ТУРБО",
        "price": 890,
        "desc": "Статика для ТУРБО-боксов. Чистый IP как ценник без брака. Держит привязку неделями.",
        "in_stock": True,
    },
    "proxy_ipv6": {
        "category": "shelf_proxies",
        "name": "🌐 Полка IPv6 ОПТ",
        "price": 590,
        "desc": "Оптом дешевле — бери 5-10 ТУРБО на одну полку. Для мульти-корзин.",
        "in_stock": True,
    },
    "proxy_mobile": {
        "category": "shelf_proxies",
        "name": "🟢 Мобильная Полка PREMIUM",
        "price": 1990,
        "desc": "Живые мобильные IP — кассиры Supermarket_cash любят как свежий товар. Для ГИГА-чеков.",
        "in_stock": True,
    },
    "manual_p2p_start": {
        "category": "manuals",
        "name": "📊 Мануал: P2P Старт 2026",
        "price": 500,
        "desc": "База P2P от Supermarket_cash. С нуля до первой сделки за день: биржи, кассы, лимиты, прогрев, вывод по СБП. По шагам, скрины, связки. Авторская переработка открытых схем.",
        "in_stock": True,
    },
    "manual_p2p_pro": {
        "category": "manuals",
        "name": "📈 Мануал: P2P PRO Связки",
        "price": 500,
        "desc": "15 рабочих связок 2026: Binance ↔ Bybit ↔ OKX ↔ HTX. Спред 3-7%, обход фрода, лимиты. Всё адаптировано под ТУРБО-боксы Supermarket_cash.",
        "in_stock": True,
    },
    "manual_airdrop": {
        "category": "manuals",
        "name": "⭐ Мануал: Фарм Airdrop",
        "price": 500,
        "desc": "Как фармить дропы на 20+ кошельков: софт, прокси-полки, антидетект, чек-лист. 30 проектов на 2026. Переписано и дополнено Supermarket_cash.",
        "in_stock": True,
    },
    "manual_tiktok": {
        "category": "manuals",
        "name": "🔔 Мануал: TikTok Трафик",
        "price": 500,
        "desc": "Льём с TikTok на P2P/крипту: крео, акки, прогрев, клоакинг. 0 → 100к показов. Кейсы Supermarket_cash, бюджет от 500₽.",
        "in_stock": True,
    },
    "manual_cards": {
        "category": "manuals",
        "name": "💸 Мануал: Карты и Дропы",
        "price": 500,
        "desc": "Виртуалки, дроповоды, оформление, лимиты ЦБ. Как не словить блок. Схемы переписаны, добавлены свежие BINы 2026.",
        "in_stock": True,
    },
    "manual_anon": {
        "category": "manuals",
        "name": "🔒 Мануал: Анонимность PRO",
        "price": 500,
        "desc": "Антидетект, отпечатки, прокси-полки, дедики. Полная анонимизация под Supermarket_cash. Чек-лист настройки за 20 мин.",
        "in_stock": True,
    },
    "manual_binance_guide": {
        "category": "manuals",
        "name": "💵 Мануал: Binance от А до Я",
        "price": 500,
        "desc": "Верификация, P2P-раздел, лимиты, обход холда. 100% рабочая методичка 2026, переписана под ТУРБО-кассы.",
        "in_stock": True,
    },
    "manual_bybit_guide": {
        "category": "manuals",
        "name": "💱 Мануал: Bybit Арбитраж",
        "price": 500,
        "desc": "Bybit P2P фишки, быстрая верификация, вывод без холда. Связки Bybit ↔ СБП.",
        "in_stock": True,
    },
    "manual_traffic_fb": {
        "category": "manuals",
        "name": "💡 Мануал: FB Ads под P2P",
        "price": 500,
        "desc": "Льём с FB на крипту: фарм, БМы, крео, клоака. Бюджет 1000₽ → первая прибыль. Авторская адаптация Supermarket_cash.",
        "in_stock": True,
    },
    "manual_combo_lite": {
        "category": "manuals",
        "name": "🎉 Мануал: COMBO Лайт",
        "price": 500,
        "desc": "Сборник: P2P + трафик + анонимность в одной корзине. 3 в 1, экономия. Бери и кати!",
        "in_stock": True,
    },
    "manual_1": {
        "category": "manuals",
        "name": "📚 Мануал: Мультиакк в Supermarket_cash",
        "price": 500,
        "desc": "Алиас COMBO Лайт (старый)",
        "in_stock": False,
    },
    "manual_cash": {
        "category": "manuals",
        "name": "📚 Мануал: Кэш-аут через СБП",
        "price": 500,
        "desc": "Алиас P2P Старт",
        "in_stock": False,
    },
    "manual_p2p": {
        "category": "manuals",
        "name": "📚 Мануал: P2P-турбо",
        "price": 500,
        "desc": "Алиас P2P PRO",
        "in_stock": False,
    },
    "manual_combo": {
        "category": "manuals",
        "name": "📚 Мануал COMBO PRO",
        "price": 500,
        "desc": "Алиас COMBO Лайт",
        "in_stock": False,
    },
    "acc_binance": {
        "category": "accounts",
        "name": "✔️ Аккаунт Binance (верифик)",
        "price": 1485,
        "desc": "Готовый верифик Binance: почта + KYC + P2P открыт. Подвязка под ТУРБО-бокс за 5 мин.",
        "in_stock": True,
    },
    "acc_bybit": {
        "category": "accounts",
        "name": "📌 Аккаунт Bybit (верифик)",
        "price": 1485,
        "desc": "Bybit верифик, лимиты сняты, P2P доступен. Чистый, ручной рег.",
        "in_stock": True,
    },
    "acc_okx": {
        "category": "accounts",
        "name": "🆒 Аккаунт OKX (верифик)",
        "price": 1485,
        "desc": "OKX с KYC, готов к СБП-выводу. Под ТУРБО/ИКС-ТУРБО.",
        "in_stock": True,
    },
    "sim_rf": {
        "category": "services",
        "name": "💬 SIM РФ + SMS",
        "price": 520,
        "desc": "Живая SIM РФ, приём SMS для верификации. Подходит для Binance/Bybit. 15 мин аренда.",
        "in_stock": True,
    },
    "dedik_usa": {
        "category": "services",
        "name": "🖥 Дедик USA (RDP)",
        "price": 990,
        "desc": "Чистый дедик США, Windows, 30 дней. Под антидетект и ТУРБО-ферму.",
        "in_stock": True,
    },
    "antidetect": {
        "category": "services",
        "name": "🔗 Антидетект AdsPower 30д",
        "price": 990,
        "desc": "Подписка + профили под Supermarket_cash. Прокладка для мультиакков.",
        "in_stock": True,
    },
    "vpn_premium": {
        "category": "services",
        "name": "ℹ️ VPN Premium 1мес",
        "price": 550,
        "desc": "Премиум VPN, без логов, под P2P. Скорость 1Gbps.",
        "in_stock": True,
    },
    "card_virtual": {
        "category": "cards",
        "name": "💸 Виртуалка 3% кэш",
        "price": 590,
        "desc": "Виртуальная карта под пополнение, BIN US/EU, 3D-S, пополнение криптой.",
        "in_stock": True,
    },
    "selfreg_fb": {
        "category": "accounts",
        "name": "✨ Саморег FB/Binance",
        "price": 1335,
        "desc": "Саморег с куками, фарм 7 дней, готов к заливу.",
        "in_stock": True,
    },
    "wallet_clean": {
        "category": "services",
        "name": "💸 Кошелёк Tron чистый",
        "price": 790,
        "desc": "Чистый TRC20 кошелёк с историей, под вывод с ТУРБО.",
        "in_stock": True,
    },
    "cert_clean": {
        "category": "market_certs",
        "name": "🛍 Сертификат CLEAN (свежесть)",
        "price": 2490,
        "desc": "Чек чистоты ТУРБО-бокса: 30 антифрод-систем. Без грязи — кассир берёт с первого раза.",
        "in_stock": True,
    },
    "cert_express": {
        "category": "market_certs",
        "name": "🔍 Сертификат EXPRESS (вне очереди)",
        "price": 3490,
        "desc": "Экспресс-касса: выкуп за 15 мин вместо 3 часов. Как проход без очереди в час-пик.",
        "in_stock": True,
    },
    "cert_guarantee": {
        "category": "market_certs",
        "name": "🔄 Сертификат GUARANTEE 30д",
        "price": 5490,
        "desc": "Страховка: если бокс не приняли — заменим до 5 раз. Для любого ТУРБО/ИКС-ТУРБО.",
        "in_stock": True,
    },
    "cert_trb": {
        "category": "market_certs",
        "name": "Сертификат GUARANTEE",
        "price": 5490,
        "desc": "Алиас",
        "in_stock": False,
    },
    "cart_filter": {
        "category": "cart_filter",
        "name": "‼️ Фильтр Корзины ТУРБО PWP",
        "price": 899,
        "desc": "Прогоняет ТУРБО через 15 касc до оплаты. Чистит метки, правит совместимость. Без него 70% отказ, с ним 97% приём.",
        "in_stock": True,
    },
    "dns_filter": {
        "category": "cart_filter",
        "name": "Фильтр PWP",
        "price": 899,
        "desc": "Алиас",
        "in_stock": False,
    },
    "cash_converter": {
        "category": "market_converter",
        "name": "❌ Конвертер ТУРБО → ИКС",
        "price": 3990,
        "desc": "Меняет Лайт/ТУРБО на ИКС-ТУРБО под другую кассу (Binance→Bybit/OKX). Апгрейдит историю и доверие. Спасает просрочку.",
        "in_stock": True,
    },
    "dns_swap": {
        "category": "market_converter",
        "name": "Конвертер SWAP",
        "price": 3990,
        "desc": "Алиас",
        "in_stock": False,
    },
}
