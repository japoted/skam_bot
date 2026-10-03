"""
CrocoPay H2H integration.
Docs: http://crocopay.tech/developer

  POST /api/v2/h2h/invoices  (headers Client-Id / Client-Secret)
    Body: { amount, currency, payment_option, callback_url }
    -> { id, status: Pending, card, bank_receiver, card_owner, expires_at }

  GET /api/v2/h2h/invoices/{id}
    -> { id, status: Pending|Success|Expired|Cancelled|Failed, ... }

  GET /api/v2/h2h/payment-method/available
    -> { methods: [{currency, payment_option, name}] }

  Webhook: POST {callback_url}?order_id=123
    Body: { timestamp, subtotal, percentage, charge_percentage,
            charge_fixed, total, sign }
    sign = HMAC_SHA256("ts|subtotal|pct|charge_pct|charge_fixed|total", Client-Secret)
    ВНИМАНИЕ: subtotal/total приходят в МИНОРНЫХ единицах (копейках):
      amount=5000 RUB -> total=500000
"""
import hashlib
import hmac
import logging
import os
from typing import Optional

import aiohttp

try:
    from config import (
        CROCOPAY_CLIENT_ID,
        CROCOPAY_CLIENT_SECRET,
        CROCOPAY_API_URL,
        CROCOPAY_CURRENCY,
        CROCOPAY_CALLBACK_URL,
        CROCOPAY_PAYMENT_OPTION,
        CROCOPAY_SUCCESS_URL,
        CROCOPAY_CANCEL_URL,
    )
except ImportError:
    CROCOPAY_CLIENT_ID = os.getenv("CROCOPAY_CLIENT_ID", "")
    CROCOPAY_CLIENT_SECRET = os.getenv("CROCOPAY_CLIENT_SECRET", "")
    CROCOPAY_API_URL = os.getenv("CROCOPAY_API_URL", "https://crocopay.tech")
    CROCOPAY_CURRENCY = os.getenv("CROCOPAY_CURRENCY", "RUB")
    CROCOPAY_PAYMENT_OPTION = os.getenv("CROCOPAY_PAYMENT_OPTION", "TO_CARD")
    CROCOPAY_CALLBACK_URL = os.getenv("CROCOPAY_CALLBACK_URL", "")
    CROCOPAY_SUCCESS_URL = os.getenv("CROCOPAY_SUCCESS_URL", "https://t.me/")
    CROCOPAY_CANCEL_URL = os.getenv("CROCOPAY_CANCEL_URL", "https://t.me/")

logger = logging.getLogger(__name__)

# порядок перебора если выбранный payment_option не включен у кассы
FALLBACK_OPTIONS = ["TO_CARD", "SBP", "SBP_ALFA", "SBP_TBANK", "QR_NSPK"]


def _headers(client_id: Optional[str] = None, secret: Optional[str] = None) -> dict:
    return {
        "Client-Id": client_id or CROCOPAY_CLIENT_ID,
        "Client-Secret": secret or CROCOPAY_CLIENT_SECRET,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _base_url() -> str:
    return (CROCOPAY_API_URL or "https://crocopay.tech").rstrip("/")


def verify_crocopay_sign(payload: dict, secret: Optional[str] = None) -> bool:
    """Проверка HMAC-подписи webhook по доке."""
    sec = secret or CROCOPAY_CLIENT_SECRET
    if not isinstance(payload, dict) or not sec:
        return False
    sign = str(payload.get("sign", ""))
    if not sign:
        return False
    raw = "|".join(
        str(payload.get(k, 0))
        for k in (
            "timestamp",
            "subtotal",
            "percentage",
            "charge_percentage",
            "charge_fixed",
            "total",
        )
    )
    expected = hmac.new(sec.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected.lower(), sign.lower())


def croco_webhook_amount(payload: dict) -> int:
    """Сумма из webhook в РУБЛЯХ (делим minor units на 100)."""
    try:
        total = int(payload.get("total", 0))
        return total // 100 if total >= 100 else total
    except Exception:
        return 0


async def get_available_methods() -> dict:
    url = f"{_base_url()}/api/v2/h2h/payment-method/available"
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15)
        ) as session:
            async with session.get(url, headers=_headers()) as resp:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    text = await resp.text()
                    return {"status": "error", "message": f"HTTP {resp.status}: {text[:200]}"}
                if resp.status != 200:
                    return {"status": "error", "message": str(data)[:300]}
                return {"status": "ok", "data": data}
    except Exception as e:
        logger.exception(f"CrocoPay available methods failed: {e}")
        return {"status": "error", "message": str(e)}


async def create_crocopay_invoice(
    order_id: int | str,
    amount: int,
    payment_option: Optional[str] = None,
    currency: Optional[str] = None,
    client_id: Optional[str] = None,
    secret: Optional[str] = None,
) -> dict:
    """
    Создаёт счёт H2H. Возвращает dict CrocoPay либо
    {"status":"error","message":...} при ошибке.
    Успех: {"id": uuid, "status":"Pending", "card":..., ...}
    """
    mid = client_id or CROCOPAY_CLIENT_ID
    sec = secret or CROCOPAY_CLIENT_SECRET
    if not mid or not sec:
        return {"status": "error", "message": "CROCOPAY_CLIENT_ID / SECRET не заданы в .env"}

    cur = (currency or CROCOPAY_CURRENCY or "RUB").upper()
    first = (payment_option or CROCOPAY_PAYMENT_OPTION or "TO_CARD").upper()

    # Сначала спрашиваем какие методы реально включены у кассы —
    # иначе вслепую перебираем 5 вариантов (~18 сек) и всё равно получаем 422.
    options = [first] + [o for o in FALLBACK_OPTIONS if o != first]
    try:
        avail = await get_available_methods()
        if avail.get("status") == "ok":
            raw_methods = (avail.get("data") or {}).get("methods") or []
            enabled = [m.get("payment_option") for m in raw_methods if isinstance(m, dict) and str(m.get("currency", "")).upper() == cur and m.get("payment_option")]
            if enabled:
                # выбранный метод первым, дальше остальные включённые
                options = [first] + [o for o in enabled if o != first]
                logger.info(f"CrocoPay available {cur}: {enabled}")
            else:
                return {"status": "error", "message": f"NO_METHODS: для валюты {cur} у кассы нет включённых методов. Обратитесь к менеджеру CrocoPay."}
    except Exception as e:
        logger.warning(f"CrocoPay available precheck failed, fallback to blind retry: {e}")

    base_cb = CROCOPAY_CALLBACK_URL or ""
    last_err = ""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
        for opt in options:
            payload = {
                "amount": int(amount),  # целые рубли, НЕ копейки
                "currency": cur,
                "payment_option": opt,
            }
            if base_cb:
                sep = "&" if "?" in base_cb else "?"
                payload["callback_url"] = f"{base_cb}{sep}order_id={order_id}"
            logger.info(f"CrocoPay create invoice: order={order_id} amount={amount} {cur} opt={opt}")
            try:
                async with session.post(
                    f"{_base_url()}/api/v2/h2h/invoices",
                    json=payload,
                    headers=_headers(mid, sec),
                ) as resp:
                    try:
                        data = await resp.json(content_type=None)
                    except Exception:
                        text = await resp.text()
                        logger.error(f"CrocoPay non-JSON {resp.status}: {text[:500]}")
                        last_err = f"HTTP {resp.status}: {text[:200]}"
                        # 422 = метод не включен -> пробуем следующий option
                        if resp.status == 422:
                            continue
                        return {"status": "error", "message": last_err}
                    logger.info(f"CrocoPay response {resp.status}: {data}")
                    if resp.status == 200 and isinstance(data, dict) and data.get("id"):
                        data["_payment_option"] = opt
                        return data
                    # ошибка вида {"status":"error","message":...} или 422
                    last_err = (
                        data.get("message")
                        if isinstance(data, dict)
                        else str(data)[:300]
                    ) or f"HTTP {resp.status}"
                    # если ругается на payment_option — пробуем следующий
                    if "payment_option" in str(last_err) or resp.status == 422:
                        continue
                    return {"status": "error", "message": last_err}
            except Exception as e:
                logger.exception(f"CrocoPay request failed opt={opt}: {e}")
                last_err = str(e)
                continue
    return {"status": "error", "message": last_err or "CrocoPay: нет доступных методов"}


async def create_crocopay_express_link(
    order_id: int | str,
    amount: int,
    currency: Optional[str] = None,
    client_id: Optional[str] = None,
    secret: Optional[str] = None,
) -> dict:
    """
    Запасной вариант: Express-форма CrocoPay (когда в H2H нет реквизитов).
    POST /api/v2/initiate-payment form-urlencoded
      -> {"status":"success","redirect_url":"https://crocopay.tech/restapi/payment?..."}
    Webhook у Express тот же самый (HMAC), автовыдача работает без изменений.
    """
    mid = client_id or CROCOPAY_CLIENT_ID
    sec = secret or CROCOPAY_CLIENT_SECRET
    if not mid or not sec:
        return {"status": "error", "message": "CROCOPAY_CLIENT_ID / SECRET не заданы в .env"}
    cur = (currency or CROCOPAY_CURRENCY or "RUB").upper()
    base_cb = CROCOPAY_CALLBACK_URL or ""
    sep = "&" if "?" in base_cb else "?"
    callback_url = f"{base_cb}{sep}order_id={order_id}" if base_cb else ""
    try:
        from config import CROCOPAY_SUCCESS_URL, CROCOPAY_CANCEL_URL
    except ImportError:
        CROCOPAY_SUCCESS_URL = os.getenv("CROCOPAY_SUCCESS_URL", "https://t.me/")
        CROCOPAY_CANCEL_URL = os.getenv("CROCOPAY_CANCEL_URL", "https://t.me/")
    form = {
        "client_id": mid,
        "client_secret": sec,
        "amount": str(int(amount)),  # целые рубли
        "currency": cur,
        "successUrl": CROCOPAY_SUCCESS_URL or "https://t.me/",
        "cancelUrl": CROCOPAY_CANCEL_URL or "https://t.me/",
        "callbackUrl": callback_url,
    }
    logger.info(f"CrocoPay express link: order={order_id} amount={amount} {cur}")
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(
                f"{_base_url()}/api/v2/initiate-payment",
                data=form,
                headers={"Accept": "application/json"},
            ) as resp:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    text = await resp.text()
                    return {"status": "error", "message": f"HTTP {resp.status}: {text[:200]}"}
                logger.info(f"CrocoPay express response {resp.status}: {data}")
                return data if isinstance(data, dict) else {"status": "error", "message": str(data)[:300]}
    except Exception as e:
        logger.exception(f"CrocoPay express failed: {e}")
        return {"status": "error", "message": str(e)}


async def check_crocopay_invoice(invoice_id: str) -> dict:
    """GET /api/v2/h2h/invoices/{id} — статус счёта."""
    url = f"{_base_url()}/api/v2/h2h/invoices/{invoice_id}"
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        ) as session:
            async with session.get(url, headers=_headers()) as resp:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    text = await resp.text()
                    return {"status": "error", "message": f"HTTP {resp.status}: {text[:200]}"}
                logger.info(f"CrocoPay check {invoice_id}: {resp.status} {data}")
                return data if isinstance(data, dict) else {"status": "error", "message": str(data)[:300]}
    except Exception as e:
        logger.exception(f"CrocoPay check failed: {e}")
        return {"status": "error", "message": str(e)}


def is_crocopay_success(payload: dict) -> bool:
    """Success только при status == Success (Polling GET)."""
    if not isinstance(payload, dict):
        return False
    return str(payload.get("status", "")).lower() == "success"


def format_requisites(inv: dict) -> str:
    """Человекочитаемые реквизиты для сообщения в боте."""
    card = inv.get("card", "—")
    bank = inv.get("bank_receiver", "")
    owner = inv.get("card_owner", "")
    exp = inv.get("expires_at", "")
    opt = inv.get("payment_option") or inv.get("_payment_option", "")
    lines = [f"💳 Реквизиты: <code>{card}</code>"]
    if bank:
        lines.append(f"🏦 Банк: {bank}")
    if owner:
        lines.append(f"👤 Получатель: {owner}")
    if opt:
        lines.append(f"📡 Способ: {opt}")
    if exp:
        lines.append(f"⏳ Действуют до: {exp[:16].replace('T', ' ')}")
    return "\n".join(lines)
