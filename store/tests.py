from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

from .mercadopago import apply_payment_to_order, create_payment, map_status
from .models import Category, Order, OrderItem, Product


class MercadoPagoIntegrationTests(TestCase):
    def setUp(self):
        category = Category.objects.create(
            name="VIPs", slug="vips", tagline="VIP", icon="", accent="#ffffff"
        )
        self.product = Product.objects.create(
            category=category,
            name="Adventure",
            slug="adventure-test",
            short_description="Plano de teste",
            price=Decimal("49.90"),
            order=0,
        )
        self.order = Order.objects.create(
            nickname="Tester",
            buyer_name="Jogador Teste",
            buyer_email="test@example.com",
            buyer_cpf_last4="9100",
            total=Decimal("49.90"),
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name=self.product.name,
            product_icon="🧭",
            unit_price=self.product.price,
            quantity=1,
        )

    def test_status_mapping(self):
        self.assertEqual(map_status("approved"), Order.Status.PAID)
        self.assertEqual(map_status("pending"), Order.Status.PENDING)
        self.assertEqual(map_status("rejected"), Order.Status.REJECTED)
        self.assertEqual(map_status("refunded"), Order.Status.REFUNDED)

    def test_pix_response_persists_qr_code(self):
        payment = {
            "id": 123456,
            "external_reference": str(self.order.order_id),
            "transaction_amount": 49.90,
            "status": "pending",
            "status_detail": "pending_waiting_transfer",
            "payment_method_id": "pix",
            "payment_type_id": "bank_transfer",
            "point_of_interaction": {
                "transaction_data": {
                    "qr_code": "000201PIXTEST",
                    "qr_code_base64": "BASE64TEST",
                    "ticket_url": "https://example.invalid/pix",
                }
            },
        }
        apply_payment_to_order(self.order, payment)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_method, "pix")
        self.assertEqual(self.order.pix_qr_code, "000201PIXTEST")
        self.assertEqual(self.order.pix_qr_code_base64, "BASE64TEST")
        self.assertEqual(self.order.status, Order.Status.PENDING)

    @override_settings(
        MERCADOPAGO_ACCESS_TOKEN="TEST-ACCESS-TOKEN",
        MERCADOPAGO_API_BASE="https://api.mercadopago.com",
        MERCADOPAGO_NOTIFICATION_URL="",
        SITE_URL="",
    )
    @patch("store.mercadopago.requests.post")
    def test_pix_uses_backend_order_total_and_idempotency(self, post):
        response = Mock()
        response.status_code = 201
        response.json.return_value = {
            "id": 987,
            "external_reference": str(self.order.order_id),
            "transaction_amount": 49.90,
            "status": "pending",
            "payment_method_id": "pix",
        }
        post.return_value = response

        # Um valor adulterado no navegador não deve alterar o valor enviado.
        create_payment(
            self.order,
            {"payment_method_id": "pix", "transaction_amount": 0.01},
            cpf="19119119100",
        )
        _, kwargs = post.call_args
        self.assertEqual(kwargs["json"]["transaction_amount"], 49.90)
        self.assertEqual(
            kwargs["headers"]["X-Idempotency-Key"], str(self.order.idempotency_key)
        )
        self.assertEqual(kwargs["json"]["external_reference"], str(self.order.order_id))

    def test_health_endpoint_bypasses_nickname_gate(self):
        response = self.client.get(reverse("store:healthz"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["database"])


class PaymentIntegrityTests(TestCase):
    def test_rejects_payment_with_wrong_amount(self):
        order = Order.objects.create(
            nickname="Tester",
            buyer_email="test@example.com",
            total=Decimal("50.00"),
        )
        payment = {
            "id": 999,
            "external_reference": str(order.order_id),
            "transaction_amount": 1.00,
            "status": "approved",
            "payment_method_id": "pix",
        }
        with self.assertRaisesMessage(RuntimeError, "Valor do pagamento não corresponde"):
            apply_payment_to_order(order, payment)
