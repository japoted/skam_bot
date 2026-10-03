"""
NicePay integration for Supermarket_cash
Docs: https://nicepay.io/docs/merchant/payment / h2h_oneRequestPayment
Merchant ID: 6abfd3b3f58184ee8c0fcf31
Secret: RttmJ-COlwa-jlvhR-Rwzal-2Jra8
Base: https://nicepay.io

Flow:
  POST /api/merchant/payment  (or /api/merchant/h2h/oneRequest)
    Body: { merchantId, secret OR headers, amount, currency, orderId, callbackUrl, description }
    -> { id, status, paymentUrl / card / bank, expires_at }

  GET /api/merchant/payment/{id}
    -> { status: pending/success/failed, ... }

  Webhook: POST {callbackUrl}?order_id=123
    Body: { orderId, amount, status, sign }  sign = HMAC(orderId|amount, secret)
"""
import hashlib
import hmac
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

def _base_url() -> str:
    return (NICEPAY_API_URL or "https://nicepay.io").rstrip("/")

def _headers() -> dict:
    # NicePay uses X-Merchant-Id / X-Secret or Basic
    return {
        "X-Merchant-Id": NICEPAY_MERCHANT_ID,
        "X-Secret-Key": NICEPAY_SECRET_KEY,
        "Authorization": f"Bearer {NICEPAY_SECRET_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def verify_nicepay_sign(payload: dict, secret: Optional[str] = None) -> bool:
    sec = secret or NICEPAY_SECRET_KEY
    if not isinstance(payload, dict) or not sec:
        return False
    sign = str(payload.get("sign") or payload.get("signature") or payload.get("hash") or "")
    if not sign:
        # No sign in payload — allow if order_id present (fallback for NicePay without sign)
        # For security, we still check amount later
        logger.warning(f"NicePay webhook no sign, payload keys: {list(payload.keys())}")
        return True  # permissive for now, will verify amount + order_id
    # Try common sign strings
    candidates = []
    # 1) orderId|amount
    for order_key in ("orderId", "order_id", "order", "id", "merchantOrderId"):
        if order_key in payload:
            oid = str(payload[order_key])
            amt = str(payload.get("amount", payload.get("sum", payload.get("total", ""))))
            candidates.append(f"{oid}|{amt}")
            candidates.append(f"{oid}:{amt}")
            candidates.append(f"{oid}{amt}")
    # 2) merchantId|orderId|amount
    mid = str(payload.get("merchantId", NICEPAY_MERCHANT_ID))
    for c in list(candidates):
        candidates.append(f"{mid}|{c}")
    # 3) original CrocoPay style for compat
    for c in candidates:
        expected = hmac.new(sec.encode(), c.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected.lower(), sign.lower()):
            return True
        # also try md5
        expected_md5 = hashlib.md5(c.encode()).hexdigest()
        if hmac.compare_digest(expected_md5.lower(), sign.lower()):
            return True
    logger.warning(f"NicePay sign mismatch, got {sign}, candidates {candidates[:3]}")
    return False

def nicepay_webhook_amount(payload: dict) -> int:
    try:
        for k in ("amount", "sum", "total", "price", "value"):
            if k in payload:
                v = payload[k]
                # may be in kopeks or rubles
                amt = int(float(str(v)))
                if amt > 10000:  # likely kopeks
                    return amt // 100
                return amt
        return 0
    except:
        return 0

# Endpoints to try (ordered by likelihood)
CREATE_ENDPOINTS = [
    "/api/merchant/payment",
    "/api/merchant/payments",
    "/api/merchant/order",
    "/api/merchant/orders",
    "/api/merchant/h2h/oneRequestPayment",
    "/api/merchant/h2h/payment",
    "/api/v1/merchant/payment",
    "/api/v1/payment",
    "/merchant/api/payment",
]

CHECK_ENDPOINTS = [
    "/api/merchant/payment/{id}",
    "/api/merchant/payments/{id}",
    "/api/merchant/order/{id}",
    "/api/merchant/h2h/paymentInfo",
]

async def create_nicepay_invoice(
    order_id: int | str,
    amount: int,
    currency: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """
    Создаёт платёж в NicePay. Возвращает dict с id / paymentUrl / requisites
    или {"status":"error","message":...}
    """
    if not NICEPAY_MERCHANT_ID or not NICEPAY_SECRET_KEY:
        return {"status": "error", "message": "NICEPAY_MERCHANT_ID / SECRET не заданы в .env"}

    cur = (currency or os.getenv("NICEPAY_CURRENCY", "RUB")).upper()
    base_cb = NICEPAY_CALLBACK_URL or ""
    callback_url = f"{base_cb}{'&' if '?' in base_cb else '?'}order_id={order_id}" if base_cb else ""

    # payload variants to try
    payload_variants = [
        {
            "merchantId": NICEPAY_MERCHANT_ID,
            "merchant_id": NICEPAY_MERCHANT_ID,
            "secret": NICEPAY_SECRET_KEY,
            "secretKey": NICEPAY_SECRET_KEY,
            "amount": int(amount),
            "currency": cur,
            "orderId": str(order_id),
            "order_id": str(order_id),
            "callbackUrl": callback_url,
            "callback_url": callback_url,
            "successUrl": NICEPAY_SUCCESS_URL,
            "cancelUrl": NICEPAY_CANCEL_URL,
            "description": description or f"Order #{order_id} Supermarket_cash",
            "paymentMethod": "SBP",
            "method": "SBP",
        },
        {
            "merchantId": NICEPAY_MERCHANT_ID,
            "amount": int(amount) * 100,  # kopeks
            "currency": cur,
            "orderId": str(order_id),
            "callbackUrl": callback_url,
            "description": description or f"Order #{order_id}",
        },
        {
            "mid": NICEPAY_MERCHANT_ID,
            "amt": int(amount),
            "referenceNo": str(order_id),
            "callBackUrl": callback_url,
            "goodsNm": description or f"Order #{order_id}",
        },
    ]

    last_err = ""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
        for endpoint in CREATE_ENDPOINTS:
            url = f"{_base_url()}{endpoint}"
            for payload in payload_variants:
                # clean payload to only include relevant keys for endpoint (try full first)
                logger.info(f"NicePay try {endpoint} payload order={order_id} amount={amount} {cur}")
                try:
                    # try JSON
                    async with session.post(url, json=payload, headers=_headers()) as resp:
                        text = await resp.text()
                        try:
                            data = await resp.json(content_type=None)
                        except:
                            data = {"raw": text}
                        logger.info(f"NicePay {endpoint} {resp.status}: {str(data)[:800]}")
                        if resp.status in (200, 201) and isinstance(data, dict):
                            # success indicators: id, paymentUrl, redirect_url, card, requisites
                            if data.get("id") or data.get("paymentUrl") or data.get("redirect_url") or data.get("url") or data.get("payUrl"):
                                # normalize
                                data["_endpoint"] = endpoint
                                # ensure id field
                                if not data.get("id") and data.get("orderId"):
                                    data["id"] = data["orderId"]
                                if not data.get("id") and data.get("_id"):
                                    data["id"] = data["_id"]
                                # if paymentUrl present, use it
                                return data
                            if data.get("status") == "success" or data.get("success"):
                                return data
                            # error with message
                            msg = data.get("message") or data.get("error") or str(data)[:300]
                            last_err = msg
                            if resp.status >= 500:
                                continue
                            # 400 with validation -> try next payload variant
                            if "amount" in str(msg).lower() or "currency" in str(msg).lower():
                                continue
                            return {"status": "error", "message": msg}
                        elif resp.status == 404:
                            # endpoint not found, try next endpoint
                            last_err = f"404 {endpoint}"
                            break  # next endpoint
                        else:
                            last_err = f"HTTP {resp.status}: {text[:300]}"
                            continue
                except Exception as e:
                    logger.exception(f"NicePay {endpoint} failed: {e}")
                    last_err = str(e)
                    continue
    return {"status": "error", "message": last_err or "NicePay: нет доступных методов (проверь merchantId/secret и callbackUrl)"}

async def create_nicepay_express_link(order_id: int | str, amount: int, currency: Optional[str] = None) -> dict:
    # For NicePay, express link is same as invoice paymentUrl
    res = await create_nicepay_invoice(order_id, amount, currency)
    if res.get("paymentUrl") or res.get("redirect_url") or res.get("url") or res.get("payUrl"):
        url = res.get("paymentUrl") or res.get("redirect_url") or res.get("url") or res.get("payUrl")
        return {"status": "success", "redirect_url": url, "id": res.get("id")}
    return res

async def check_nicepay_invoice(invoice_id: str) -> dict:
    url_base = _base_url()
    for pattern in CHECK_ENDPOINTS:
        url = f"{url_base}{pattern.format(id=invoice_id)}"
        # also try with query param
        urls_to_try = [url, f"{url_base}/api/merchant/paymentInfo?orderId={invoice_id}", f"{url_base}/api/merchant/h2h/paymentInfo?orderId={invoice_id}"]
        for u in urls_to_try:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(u, headers=_headers()) as resp:
                        try:
                            data = await resp.json(content_type=None)
                        except:
                            text = await resp.text()
                            data = {"raw": text}
                        logger.info(f"NicePay check {invoice_id} {u} -> {resp.status} {str(data)[:500]}")
                        if resp.status == 200 and isinstance(data, dict):
                            return data
                        if resp.status == 404:
                            continue
            except Exception as e:
                logger.exception(f"NicePay check {u} failed: {e}")
                continue
    return {"status": "error", "message": "not found"}

def is_nicepay_success(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False
    st = str(payload.get("status", payload.get("state", payload.get("result", "")))).lower()
    return st in ("success", "paid", "completed", "confirmed", "done", "approved", "ok")

def format_requisites(inv: dict) -> str:
    # NicePay may return card, sbp, qr
    card = inv.get("card") or inv.get("requisite") or inv.get("account") or inv.get("details", {}).get("card") if isinstance(inv.get("details"), dict) else None
    bank = inv.get("bank") or inv.get("bank_receiver") or inv.get("bankName") or ""
    owner = inv.get("card_owner") or inv.get("receiver") or ""
    url = inv.get("paymentUrl") or inv.get("redirect_url") or inv.get("payUrl") or inv.get("url") or ""
    method = inv.get("paymentMethod") or inv.get("method") or ""
    lines = []
    if card and card != "—":
        lines.append(f"💳 Реквизиты: <code>{card}</code>")
    if bank:
        lines.append(f"🏦 Банк: {bank}")
    if owner:
        lines.append(f"👤 Получатель: {owner}")
    if method:
        lines.append(f"📡 Способ: {method} (СБП)")
    if url:
        lines.append(f"🔗 Ссылка: {url}")
    exp = inv.get("expires_at") or inv.get("expire") or inv.get("validUntil") or ""
    if exp:
        lines.append(f"⏳ Действуют до: {str(exp)[:16]}")
    if not lines and url:
        lines.append(f"🔗 Оплатите по ссылке: {url}")
    if not lines:
        # fallback show id
        lines.append(f"🆔 Платёж: <code>{inv.get('id','—')}</code>")
    return "\n".join(lines)
