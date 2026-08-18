"""Integração server-side com a API de Payments do Mercado Pago."""

from __future__ import annotations

import logging
import re
from decimal import Decimal

import requests
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .models import Order

logger = logging.getLogger(__name__)


class MercadoPagoConfigurationError(RuntimeError):
    pass


class MercadoPagoAPIError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


def _headers(*, idempotency_key: str | None = None) -> dict[str, str]:
    if not settings.MERCADOPAGO_ACCESS_TOKEN:
        raise MercadoPagoConfigurationError(
            "MERCADOPAGO_ACCESS_TOKEN não está configurado no ambiente."
        )
    headers = {
        "Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if idempotency_key:
        headers["X-Idempotency-Key"] = idempotency_key
    return headers


def notification_url() -> str | None:
    if settings.MERCADOPAGO_NOTIFICATION_URL:
        return settings.MERCADOPAGO_NOTIFICATION_URL
    if settings.SITE_URL and settings.SITE_URL.startswith("https://"):
        return f"{settings.SITE_URL}{reverse('store:mercadopago_webhook')}"
    return None


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if not parts:
        return "Cliente", "Pixelmon"
    if len(parts) == 1:
        return parts[0], "Pixelmon"
    return parts[0], " ".join(parts[1:])


def _clean_cpf(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def create_payment(order: Order, form_data: dict, *, cpf: str) -> dict:
    """Cria um pagamento usando apenas o total persistido no pedido local.

    Nunca usa o valor enviado pelo navegador como fonte de verdade.
    """
    payment_method_id = str(form_data.get("payment_method_id") or "").strip()
    if not payment_method_id:
        raise MercadoPagoAPIError("Meio de pagamento não informado.")

    first_name, last_name = _split_name(order.buyer_name)
    clean_cpf = _clean_cpf(cpf)

    payload: dict = {
        "transaction_amount": _money(order.total),
        "description": f"Pixelmon Adventures - Pedido {str(order.order_id)[:8]}",
        "external_reference": str(order.order_id),
        "payment_method_id": payment_method_id,
        "payer": {
            "email": order.buyer_email,
            "first_name": first_name,
            "last_name": last_name,
            "identification": {"type": "CPF", "number": clean_cpf},
        },
        "metadata": {
            "pixelmon_order_id": str(order.order_id),
            "nickname": order.nickname,
        },
        "additional_info": {
            "items": [
                {
                    "id": str(item.product_id or item.id),
                    "title": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": _money(item.unit_price),
                    "category_id": "digital_goods",
                }
                for item in order.items.all()
            ],
            "payer": {"first_name": first_name, "last_name": last_name},
        },
    }

    notify = notification_url()
    if notify:
        payload["notification_url"] = notify

    if payment_method_id != "pix":
        token = str(form_data.get("token") or "").strip()
        if not token:
            raise MercadoPagoAPIError("Token do cartão não informado.")
        try:
            installments = int(form_data.get("installments") or 1)
        except (TypeError, ValueError):
            installments = 1
        if installments < 1 or installments > settings.MERCADOPAGO_MAX_INSTALLMENTS:
            raise MercadoPagoAPIError(
                f"Número de parcelas inválido. Máximo: {settings.MERCADOPAGO_MAX_INSTALLMENTS}."
            )
        payload["token"] = token
        payload["installments"] = installments
        issuer_id = form_data.get("issuer_id")
        if issuer_id not in (None, ""):
            payload["issuer_id"] = str(issuer_id)

    url = f"{settings.MERCADOPAGO_API_BASE}/v1/payments"
    try:
        response = requests.post(
            url,
            json=payload,
            headers=_headers(idempotency_key=str(order.idempotency_key)),
            timeout=15,
        )
    except requests.RequestException as exc:
        raise MercadoPagoAPIError("Não foi possível conectar ao Mercado Pago.") from exc

    try:
        body = response.json()
    except ValueError:
        body = {"message": response.text[:500]}

    if response.status_code not in (200, 201):
        logger.warning("Mercado Pago create error %s: %s", response.status_code, body)
        message = body.get("message") or body.get("error") or "Pagamento não pôde ser criado."
        raise MercadoPagoAPIError(str(message), status_code=response.status_code, payload=body)
    return body


def get_payment(payment_id: str) -> dict:
    url = f"{settings.MERCADOPAGO_API_BASE}/v1/payments/{payment_id}"
    try:
        response = requests.get(url, headers=_headers(), timeout=12)
    except requests.RequestException as exc:
        raise MercadoPagoAPIError("Não foi possível consultar o Mercado Pago.") from exc
    try:
        body = response.json()
    except ValueError:
        body = {"message": response.text[:500]}
    if response.status_code != 200:
        raise MercadoPagoAPIError(
            str(body.get("message") or "Pagamento não encontrado."),
            status_code=response.status_code,
            payload=body,
        )
    return body


def map_status(mp_status: str, mp_status_detail: str = "") -> str:
    status = (mp_status or "").lower()
    detail = (mp_status_detail or "").lower()
    if status == "approved":
        return Order.Status.PAID
    if status == "refunded" or "refund" in detail:
        return Order.Status.REFUNDED
    if status in {"cancelled", "canceled"}:
        return Order.Status.CANCELLED
    if status == "rejected":
        return Order.Status.REJECTED
    if status in {"pending", "in_process", "authorized"}:
        return Order.Status.PENDING
    return Order.Status.PENDING


def apply_payment_to_order(order: Order, payment: dict) -> Order:
    """Atualiza o pedido somente após consultar/receber dados oficiais do MP."""
    external_reference = str(payment.get("external_reference") or "")
    if external_reference and external_reference != str(order.order_id):
        raise MercadoPagoAPIError("Referência do pagamento não corresponde ao pedido.")

    try:
        mp_amount = Decimal(str(payment.get("transaction_amount")))
    except Exception as exc:
        raise MercadoPagoAPIError("Mercado Pago retornou um valor inválido.") from exc
    if mp_amount.quantize(Decimal("0.01")) != order.total.quantize(Decimal("0.01")):
        raise MercadoPagoAPIError("Valor do pagamento não corresponde ao pedido.")

    mp_id = str(payment.get("id") or "")
    mp_status = str(payment.get("status") or "")
    mp_detail = str(payment.get("status_detail") or "")
    new_status = map_status(mp_status, mp_detail)

    if mp_id:
        order.mercadopago_payment_id = mp_id
    order.mercadopago_status = mp_status
    order.mercadopago_status_detail = mp_detail
    order.status = new_status

    payment_method_id = str(payment.get("payment_method_id") or "")
    payment_type_id = str(payment.get("payment_type_id") or "")
    order.payment_method = "pix" if payment_method_id == "pix" else (payment_type_id or payment_method_id)

    transaction_data = (
        (payment.get("point_of_interaction") or {}).get("transaction_data") or {}
    )
    if payment_method_id == "pix":
        order.pix_qr_code = str(transaction_data.get("qr_code") or order.pix_qr_code or "")
        order.pix_qr_code_base64 = str(
            transaction_data.get("qr_code_base64") or order.pix_qr_code_base64 or ""
        )
        order.pix_ticket_url = str(
            transaction_data.get("ticket_url") or order.pix_ticket_url or ""
        )

    if new_status == Order.Status.PAID and not order.paid_at:
        order.paid_at = timezone.now()

    order.save()
    return order


def sync_order(order: Order) -> Order:
    if not order.mercadopago_payment_id:
        return order
    payment = get_payment(order.mercadopago_payment_id)
    return apply_payment_to_order(order, payment)


def validate_webhook_signature(request, data_id: str) -> bool:
    """Valida x-signature quando a chave secreta estiver configurada.

    Mesmo sem secret, a view do webhook não confia no payload: consulta o
    pagamento novamente pela API autenticada e valida referência + valor.
    """
    secret = settings.MERCADOPAGO_WEBHOOK_SECRET
    if not secret:
        return True
    try:
        from mercadopago.webhook import (
            InvalidWebhookSignatureError,
            WebhookSignatureValidator,
        )
    except ImportError:
        logger.exception("SDK Mercado Pago sem validador de webhook.")
        return False

    try:
        WebhookSignatureValidator.validate(
            request.headers.get("x-signature"),
            request.headers.get("x-request-id"),
            data_id,
            secret,
        )
        return True
    except (InvalidWebhookSignatureError, ValueError, TypeError):
        return False
