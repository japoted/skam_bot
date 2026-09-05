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
    from config import NICEPAY_MERCHANT_ID, NICEPAY_SECRET, NICEPAY_API_URL, NICEPAY_CURRENCY
except ImportError:
    NICEPAY_MERCHANT_ID = os.getenv("NICEPAY_MERCHANT_ID", "")
    NICEPAY_SECRET = os.getenv("NICEPAY_SECRET", "")
    NICEPAY_API_URL = os.getenv("NICEPAY_API_URL", "https://nicepay.io/public/api/payment")
    NICEPAY_CURRENCY = os.getenv("NICEPAY_CURRENCY", "RUB")

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

    logger.info(f"NicePay create payment: order_id={order_id} amount={amount} {cur} -> {nicepay_amount} minor units customer={customer}")

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
