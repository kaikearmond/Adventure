import uuid

import django.utils.timezone
from django.db import migrations, models


def populate_idempotency(apps, schema_editor):
    Order = apps.get_model("store", "Order")
    for order in Order.objects.filter(idempotency_key__isnull=True):
        order.idempotency_key = uuid.uuid4()
        order.save(update_fields=["idempotency_key"])


class Migration(migrations.Migration):
    dependencies = [("store", "0002_category_mascot")]

    operations = [
        migrations.AddField(
            model_name="order",
            name="idempotency_key",
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.RunPython(populate_idempotency, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="order",
            name="idempotency_key",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(model_name="order", name="buyer_name", field=models.CharField(blank=True, max_length=120, verbose_name="Nome do comprador")),
        migrations.AddField(model_name="order", name="buyer_email", field=models.EmailField(blank=True, max_length=254, verbose_name="E-mail")),
        migrations.AddField(model_name="order", name="buyer_cpf_last4", field=models.CharField(blank=True, max_length=4, verbose_name="CPF (últimos 4)")),
        migrations.AlterField(model_name="order", name="payment_method", field=models.CharField(blank=True, max_length=30, verbose_name="Forma de pagamento")),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Aguardando pagamento"),
                    ("PAID", "Pago"),
                    ("REJECTED", "Recusado"),
                    ("CANCELLED", "Cancelado"),
                    ("REFUNDED", "Reembolsado"),
                    ("ERROR", "Erro no pagamento"),
                ],
                default="PENDING",
                max_length=12,
                verbose_name="Status",
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="delivery_status",
            field=models.CharField(
                choices=[("PENDING", "Aguardando entrega manual"), ("DELIVERED", "Entregue")],
                default="PENDING",
                max_length=12,
                verbose_name="Entrega",
            ),
        ),
        migrations.AddField(model_name="order", name="mercadopago_payment_id", field=models.CharField(blank=True, max_length=40, null=True, unique=True, verbose_name="ID Mercado Pago")),
        migrations.AddField(model_name="order", name="mercadopago_status", field=models.CharField(blank=True, max_length=40, verbose_name="Status Mercado Pago")),
        migrations.AddField(model_name="order", name="mercadopago_status_detail", field=models.CharField(blank=True, max_length=120, verbose_name="Detalhe do status Mercado Pago")),
        migrations.AddField(model_name="order", name="pix_qr_code", field=models.TextField(blank=True, verbose_name="Pix copia e cola")),
        migrations.AddField(model_name="order", name="pix_qr_code_base64", field=models.TextField(blank=True, verbose_name="QR Code Pix (base64)")),
        migrations.AddField(model_name="order", name="pix_ticket_url", field=models.TextField(blank=True, verbose_name="URL do comprovante Pix")),
        migrations.AddField(model_name="order", name="paid_at", field=models.DateTimeField(blank=True, null=True, verbose_name="Pago em")),
        migrations.AddField(model_name="order", name="delivered_at", field=models.DateTimeField(blank=True, null=True, verbose_name="Entregue em")),
        migrations.AddField(model_name="order", name="updated_at", field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now, verbose_name="Atualizado em"), preserve_default=False),
    ]
