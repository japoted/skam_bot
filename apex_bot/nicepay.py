"""
NicePay integration for Supermarket_cash
Docs: https://nicepay.io/docs/merchant/payment (POST https://nicepay.io/public/api/payment)
      https://nicepay.io/docs/merchant/h2h_oneRequestPayment (POST .../h2hOneRequestPayment)
      https://nicepay.io/docs/merchant/handler (GET callback with hash)
Merchant ID: 6abfd3b3f58184ee8c0fcf31
"""
import hashlib
import logging
import os
from typing import Optional

import aiohttp

try:
    from config import (
        NICEPAY_MERCHANT_ID,
        NICEPAY_SECRET_KEY,
        NICEPAY_API_URL,
        NICEPAY_CALLBACK_URL,
        NICEPAY_SUCCESS_URL,
        NICEPAY_CANCEL_URL,
    )
except ImportError:
    NICEPAY_MERCHANT_ID = os.getenv("NICEPAY_MERCHANT_ID", "6abfd3b3f58184ee8c0fcf31")
    NICEPAY_SECRET_KEY = os.getenv("NICEPAY_SECRET_KEY", "RttmJ-COlwa-jlvhR-Rwzal-2Jra8")
    NICEPAY_API_URL = os.getenv("NICEPAY_API_URL", "https://nicepay.io")
    NICEPAY_CALLBACK_URL = os.getenv("NICEPAY_CALLBACK_URL", "")
    NICEPAY_SUCCESS_URL = os.getenv("NICEPAY_SUCCESS_URL", "https://t.me/")
    NICEPAY_CANCEL_URL = os.getenv("NICEPAY_CANCEL_URL", "https://t.me/")

logger = logging.getLogger(__name__)

CREATE_URL = "/public/api/payment"
H2H_CREATE_URL = "/public/api/h2hOneRequestPayment"
H2H_INFO_URL = "/public/api/h2hPaymentInfo"


def _base_url() -> str:
    return (NICEPAY_API_URL or "https://nicepay.io").rstrip("/")


def verify_nicepay_sign(payload: dict, secret: Optional[str] = None) -> bool:
    """Проверка hash из хендлера NicePay по доке (PHP пример).

    hash = sha256(implode('{np}', sorted_values + secret))
    sorted: ksort($params, SORT_STRING) без hash, затем array_push secret.
    """
    sec = secret or NICEPAY_SECRET_KEY
    if not isinstance(payload, dict) or not sec:
        return False
    sign = str(payload.get("hash", payload.get("sign", payload.get("signature", ""))))
    if not sign:
        logger.warning(f"NicePay webhook no hash, keys: {list(payload.keys())}")
        return False
    params = {k: str(v) for k, v in payload.items() if k != "hash" and v is not None}
    # ksort SORT_STRING = сортировка по ключам как строки
    sorted_keys = sorted(params.keys())
    values = [params[k] for k in sorted_keys]
    values.append(sec)
    raw = "{np}".join(values)
    expected = hashlib.sha256(raw.encode()).hexdigest()
    ok = expected.lower() == sign.lower()
    if not ok:
        logger.warning(f"NicePay hash mismatch: got {sign[:16]}... expected {expected[:16]}... raw_keys={sorted_keys}")
    return ok


def nicepay_webhook_amount(payload: dict) -> int:
    """Сумма из webhook в РУБЛЯХ. В хендлере amount уже в копейках."""
    try:
        for k in ("amount", "sum", "total", "price", "value", "amountNum"):
            if k in payload and payload[k] not in (None, ""):
                amt = int(float(str(payload[k]).replace(" ", "").replace("₽", "")))
                # в колбэке amount в копейках (5670 = 56.70)
                if amt >= 1000:
                    # эвристика: если есть amount_currency и значение большое — копейки
                    return amt // 100 if amt % 100 != 0 or amt > 10000 else amt
                return amt
        return 0
    except Exception:
        return 0


async def create_nicepay_invoice(
    order_id: int | str,
    amount: int,
    currency: Optional[str] = None,
    description: Optional[str] = None,
    customer: Optional[str] = None,
    method: Optional[str] = None,
) -> dict:
    """Создание счёта NicePay: POST /public/api/payment -> ссылка на форму.

    amount в рублях, в API уходит в копейках (500 -> 50000).
    Возвращает {"id": payment_id, "paymentUrl": link, ...}.
    """
    if not NICEPAY_MERCHANT_ID or not NICEPAY_SECRET_KEY:
        return {"status": "error", "message": "NICEPAY_MERCHANT_ID / SECRET не заданы в .env"}
    cur = (currency or os.getenv("NICEPAY_CURRENCY", "RUB")).upper()
    amount_minor = int(amount) * 100
    cust = str(customer or f"tg_{order_id}")[:50]

    payload = {
        "merchant_id": NICEPAY_MERCHANT_ID,
        "secret": NICEPAY_SECRET_KEY,
        "order_id": str(order_id)[:50],
        "customer": cust,
        "amount": amount_minor,
        "currency": cur,
        "description": (description or f"Order #{order_id} Supermarket_cash")[:150],
    }
    if method:
        payload["method"] = method
    if NICEPAY_SUCCESS_URL:
        payload["success_url"] = NICEPAY_SUCCESS_URL
    if NICEPAY_CANCEL_URL:
        payload["fail_url"] = NICEPAY_CANCEL_URL
    try:
        logger.info(f"NicePay create order={order_id} amount={amount_minor} {cur} customer={cust}")
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.post(f"{_base_url()}{CREATE_URL}", json=payload) as resp:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    text = await resp.text()
                    return {"status": "error", "message": f"HTTP {resp.status}: {text[:200]}"}
                logger.info(f"NicePay create {resp.status}: {str(data)[:800]}")
                if isinstance(data, dict) and data.get("status") == "success":
                    d = data.get("data", {})
                    return {
                        "id": d.get("payment_id", str(order_id)),
                        "status": "success",
                        "paymentUrl": d.get("link", ""),
                        "redirect_url": d.get("link", ""),
                        "amount": amount,
                        "_raw": data,
                    }
                msg = ""
                if isinstance(data, dict):
                    d = data.get("data", {})
                    msg = (d.get("message") if isinstance(d, dict) else "") or data.get("message") or str(data)[:300]
                return {"status": "error", "message": msg or f"HTTP {resp.status}"}
    except Exception as e:
        logger.exception(f"NicePay create failed: {e}")
        return {"status": "error", "message": str(e)}


async def create_nicepay_express_link(order_id: int | str, amount: int, currency: Optional[str] = None) -> dict:
    res = await create_nicepay_invoice(order_id, amount, currency)
    url = res.get("paymentUrl") or res.get("redirect_url") or res.get("url") or res.get("payUrl")
    if url:
        return {"status": "success", "redirect_url": url, "id": res.get("id")}
    return res


async def check_nicepay_invoice(invoice_id: str) -> dict:
    """Проверка статуса.

    У мерчанта нет H2H-доступа (h2hPaymentInfo -> 'no access'),
    поэтому для обычных /public/api/payment счетов статуса через API нет —
    автовыдача идёт только через webhook-handler.
    Возвращаем not_supported, чтобы кнопка 'Проверить' честно говорила ждать webhook.
    """
    payload = {
        "merchant_id": NICEPAY_MERCHANT_ID,
        "secret": NICEPAY_SECRET_KEY,
        "payment": invoice_id,
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(f"{_base_url()}{H2H_INFO_URL}", json=payload) as resp:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    text = await resp.text()
                    return {"status": "error", "message": f"HTTP {resp.status}: {text[:200]}"}
                logger.info(f"NicePay check {invoice_id}: {resp.status} {str(data)[:500]}")
                if isinstance(data, dict):
                    d = data.get("data", {})
                    if isinstance(d, dict) and "H2H" in str(d.get("message", "")):
                        return {"status": "not_supported", "message": "polling недоступен, ждём webhook"}
                    return data
                return {"status": "error", "message": str(data)[:300]}
    except Exception as e:
        logger.exception(f"NicePay check failed: {e}")
        return {"status": "error", "message": str(e)}


def is_nicepay_success(payload: dict) -> bool:
    """Успех: handler result==success ИЛИ h2h status==5."""
    if not isinstance(payload, dict):
        return False
    # handler формат
    if str(payload.get("result", "")).lower() == "success":
        return True
    # h2h info формат: {status: success, data: {status: 5}}
    if payload.get("status") == "success":
        d = payload.get("data", {})
        if isinstance(d, dict) and int(d.get("status", 0) or 0) == 5:
            return True
        # simple payment info без data.status
        if not isinstance(d, dict):
            return True
    d = payload.get("data", {})
    if isinstance(d, dict) and int(d.get("status", 0) or 0) == 5:
        return True
    st = str(payload.get("status", "")).lower()
    return st in ("success", "paid", "completed", "confirmed", "done", "approved", "details_found")


def format_requisites(inv: dict) -> str:
    card = inv.get("card") or inv.get("wallet") or "—"
    bank = inv.get("bank_receiver") or inv.get("bank") or ""
    owner = inv.get("card_owner") or inv.get("comment") or ""
    opt = inv.get("payment_option") or inv.get("method") or ""
    exp = inv.get("expires_at") or inv.get("expire") or ""
    url = inv.get("paymentUrl") or inv.get("redirect_url") or ""
    lines = []
    if card and card != "—":
        # phone или card
        if str(card).replace("+", "").replace(" ", "").isdigit() and len(str(card)) <= 12:
            lines.append(f"📱 Номер (СБП): <code>{card}</code>")
        else:
            lines.append(f"💳 Реквизиты: <code>{card}</code>")
    if bank:
        lines.append(f"🏦 Банк: {bank}")
    if owner:
        lines.append(f"👤 Комментарий: {owner}")
    if opt:
        lines.append(f"📡 Способ: {opt}")
    if url:
        lines.append(f"🔗 Ссылка: {url}")
    if exp:
        lines.append(f"⏳ Действуют до: {str(exp)[:16]}")
    if not lines:
        lines.append(f"🆔 Платёж: <code>{inv.get('id', '—')}</code>")
    return "\n".join(lines)
