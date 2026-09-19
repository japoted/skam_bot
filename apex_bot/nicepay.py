"""
NicePay.io integration.
Docs (reverse-engineered from production example):
  POST https://nicepay.io/public/api/payment
  Body: { merchant_id, secret, order_id, customer, amount, currency }

Response:
  { "status": "success", "data": { "link": "https://nicepay.io/payment/..." } }
  { "status": "error", "data": { "message": "..." } }

Webhook (handler) is expected to POST JSON to NICEPAY_CALLBACK_URL with at least order_id.
Exact signature is not documented publicly, so we accept flexible payload and verify order_id+amount.
"""
import logging
from typing import Optional

import aiohttp

import os
# Совместимость со старым config.py на хосте
try:
    from config import NICEPAY_MERCHANT_ID, NICEPAY_SECRET, NICEPAY_API_URL, NICEPAY_CURRENCY, NICEPAY_CALLBACK_URL
except ImportError:
    NICEPAY_MERCHANT_ID = os.getenv("NICEPAY_MERCHANT_ID", "")
    NICEPAY_SECRET = os.getenv("NICEPAY_SECRET", "")
    NICEPAY_API_URL = os.getenv("NICEPAY_API_URL", "https://nicepay.io/public/api/payment")
    NICEPAY_CURRENCY = os.getenv("NICEPAY_CURRENCY", "RUB")
    NICEPAY_CALLBACK_URL = os.getenv("NICEPAY_CALLBACK_URL", "")

logger = logging.getLogger(__name__)


async def create_nicepay_payment(
    order_id: int | str,
    amount: int,
    customer: int | str,
    currency: Optional[str] = None,
    merchant_id: Optional[str] = None,
    secret: Optional[str] = None,
) -> dict:
    """
    Создает платеж в NicePay и возвращает распарсенный JSON.
    :param order_id: уникальный ID заказа (используем id из БД)
    :param amount: сумма в рублях (целое число, например 1799)
    :param customer: telegram user_id
    :return: dict с ключами status/data, либо {"status":"error","data":{"message":...}}
    """
    mid = merchant_id or NICEPAY_MERCHANT_ID
    sec = secret or NICEPAY_SECRET
    cur = currency or NICEPAY_CURRENCY

    if not mid or not sec:
        return {"status": "error", "data": {"message": "NICEPAY_MERCHANT_ID / NICEPAY_SECRET не заданы в .env"}}

    # NicePay ожидает сумму в копейках (minor units). 250 RUB = 25000
    # Для RUB умножаем на 100, для других валют отправляем как есть
    nicepay_amount = int(amount) * 100 if cur.upper() == "RUB" else int(amount)

    payload = {
        "merchant_id": mid,
        "secret": sec,
        "order_id": str(order_id),
        "customer": str(customer),
        "amount": str(nicepay_amount),
        "currency": cur,
    }

    if NICEPAY_CALLBACK_URL:
        payload["callback_url"] = NICEPAY_CALLBACK_URL

    logger.info(f"NicePay create payment: order_id={order_id} amount={amount} {cur} -> {nicepay_amount} minor units customer={customer} callback_url={NICEPAY_CALLBACK_URL}")

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.post(
                NICEPAY_API_URL,
                json=payload,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
            ) as resp:
                # NicePay всегда отдает JSON даже при 4xx
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    text = await resp.text()
                    logger.error(f"NicePay non-JSON response {resp.status}: {text[:500]}")
                    return {"status": "error", "data": {"message": f"HTTP {resp.status}: {text[:200]}"}}
                logger.info(f"NicePay response {resp.status}: {data}")
                return data
    except Exception as e:
        logger.exception(f"NicePay request failed: {e}")
        return {"status": "error", "data": {"message": str(e)}}


async def check_nicepay_payment(order_id: int | str) -> dict:
    """
    Проверяет статус платежа в NicePay через API.
    NicePay.io может поддерживать GET /public/api/payment/{order_id} или аналогичный эндпоинт.
    """
    api_base = NICEPAY_API_URL.rsplit("/", 1)[0] if "/" in NICEPAY_API_URL else NICEPAY_API_URL
    check_url = f"{api_base}/{order_id}"

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(
                check_url,
                params={"merchant_id": NICEPAY_MERCHANT_ID, "secret": NICEPAY_SECRET},
                headers={"Accept": "application/json"},
            ) as resp:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    text = await resp.text()
                    logger.warning(f"NicePay check status non-JSON {resp.status}: {text[:300]}")
                    return {"status": "error", "data": {"message": f"HTTP {resp.status}"}}
                logger.info(f"NicePay check status {resp.status}: {data}")
                return data
    except Exception as e:
        logger.exception(f"NicePay check status failed: {e}")
        return {"status": "error", "data": {"message": str(e)}}


def extract_nicepay_order_id(payload: dict) -> Optional[str]:
    """
    Пытается вытащить order_id из webhook payload разными вариантами.
    NicePay может прислать order_id / orderId / payment.order_id / data.order_id
    """
    if not isinstance(payload, dict):
        return None
    for key in ("order_id", "orderId", "order", "payment_id", "paymentId", "id"):
        if key in payload:
            v = payload[key]
            if isinstance(v, (str, int)):
                return str(v)
            if isinstance(v, dict) and "order_id" in v:
                return str(v["order_id"])
    # вложенные объекты
    for nested_key in ("data", "payment", "result", "payload"):
        if nested_key in payload and isinstance(payload[nested_key], dict):
            inner = extract_nicepay_order_id(payload[nested_key])
            if inner:
                return inner
    return None


def is_nicepay_success(payload: dict) -> bool:
    """
    Определяет успешную оплату по payload. Эвристика, т.к. точный формат не документирован.
    Считаем success если status == success/paid/completed/confirmed
    """
    if not isinstance(payload, dict):
        return False
    # прямые поля
    for key in ("status", "payment_status", "state"):
        if key in payload:
            val = str(payload[key]).lower()
            if val in ("success", "paid", "completed", "confirmed", "done", "succeeded", "approved"):
                return True
            if val in ("error", "failed", "canceled", "cancelled", "rejected"):
                return False
    # вложенные
    for nested_key in ("data", "payment", "result"):
        if nested_key in payload and isinstance(payload[nested_key], dict):
            if is_nicepay_success(payload[nested_key]):
                return True
    # если есть link но нет статуса — считаем pending
    return False
