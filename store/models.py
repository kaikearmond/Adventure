import uuid

from django.db import models
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    """Uma categoria de produtos da loja."""

    name = models.CharField("Nome", max_length=60)
    slug = models.SlugField("Slug", unique=True)
    tagline = models.CharField(
        "Frase curta", max_length=120,
        help_text="Aparece embaixo do nome da categoria.",
    )
    description = models.TextField("Descrição", blank=True)
    icon = models.CharField(
        "Ícone (emoji)", max_length=8, default="📦",
        help_text="Um emoji usado como ícone pixelado da categoria.",
    )
    mascot = models.CharField(
        "Mascote (caminho estático)", max_length=120, blank=True,
        help_text="Ex.: img/creatures/creature-vips.svg — criatura pixel art usada como mascote da categoria.",
    )
    accent = models.CharField(
        "Cor de destaque (hex)", max_length=7, default="#7CD84A",
    )
    order = models.PositiveIntegerField("Ordem", default=0)
    is_active = models.BooleanField("Ativa", default=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("store:category", kwargs={"slug": self.slug})

    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    class Rarity(models.TextChoices):
        COMMON = "COMMON", "Comum"
        UNCOMMON = "UNCOMMON", "Incomum"
        RARE = "RARE", "Raro"
        EPIC = "EPIC", "Épico"
        LEGENDARY = "LEGENDARY", "Lendário"

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products",
        verbose_name="Categoria",
    )
    name = models.CharField("Nome", max_length=80)
    slug = models.SlugField("Slug", unique=True)
    short_description = models.CharField("Descrição curta", max_length=140)
    description = models.TextField(
        "Descrição completa", blank=True,
        help_text="Uma linha por parágrafo.",
    )
    perks = models.TextField(
        "Benefícios (um por linha)", blank=True,
        help_text="Cada linha vira um item da lista de vantagens no card.",
    )
    icon = models.CharField("Ícone (emoji)", max_length=8, default="🎁")
    rarity = models.CharField(
        "Raridade", max_length=10, choices=Rarity.choices,
        default=Rarity.COMMON,
    )
    duration_label = models.CharField(
        "Duração", max_length=40, blank=True,
        help_text="Ex.: 30 dias, Permanente, Uso único.",
    )
    price = models.DecimalField("Preço (R$)", max_digits=8, decimal_places=2)
    original_price = models.DecimalField(
        "Preço original (R$)", max_digits=8, decimal_places=2,
        null=True, blank=True,
        help_text="Preenchido apenas quando o item está em promoção.",
    )
    badge_text = models.CharField(
        "Selo personalizado", max_length=20, blank=True,
        help_text="Ex.: MAIS VENDIDO, NOVO. Deixe em branco para automático.",
    )
    is_featured = models.BooleanField("Destaque na home", default=False)
    is_promotion = models.BooleanField("Em promoção", default=False)
    promotion_ends_at = models.DateTimeField(
        "Promoção termina em", null=True, blank=True,
    )
    stock_label = models.CharField(
        "Rótulo de disponibilidade", max_length=40,
        default="Entrega automática",
    )
    order = models.PositiveIntegerField("Ordem", default=0)
    is_active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["order", "-is_featured", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("store:product_detail", kwargs={"slug": self.slug})

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return round((1 - (self.price / self.original_price)) * 100)
        return 0

    @property
    def perks_list(self):
        return [line.strip() for line in self.perks.splitlines() if line.strip()]

    @property
    def description_paragraphs(self):
        return [line.strip() for line in self.description.splitlines() if line.strip()]

    @property
    def is_promotion_active(self):
        if not self.is_promotion:
            return False
        if self.promotion_ends_at:
            return self.promotion_ends_at > timezone.now()
        return True

    @property
    def display_badge(self):
        if self.badge_text:
            return self.badge_text
        if self.is_promotion_active:
            return f"-{self.discount_percent}%"
        if self.is_featured:
            return "DESTAQUE"
        return ""


class PromoBanner(models.Model):
    """Banner rotativo em destaque na home."""

    eyebrow = models.CharField("Selo pequeno", max_length=40, default="OFERTA POR TEMPO LIMITADO")
    title = models.CharField("Título", max_length=90)
    subtitle = models.CharField("Subtítulo", max_length=160)
    cta_text = models.CharField("Texto do botão", max_length=30, default="Ver oferta")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="banners",
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="banners",
    )
    theme = models.CharField(
        "Tema visual", max_length=20,
        choices=[
            ("forest", "Floresta / Grass"),
            ("void", "Vazio / Espacial"),
            ("ember", "Fogo / Energia"),
            ("aether", "Místico / Épico"),
        ],
        default="void",
    )
    ends_at = models.DateTimeField("Termina em", null=True, blank=True)
    order = models.PositiveIntegerField("Ordem", default=0)
    is_active = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Banner de promoção"
        verbose_name_plural = "Banners de promoção"
        ordering = ["order"]

    def __str__(self):
        return self.title

    def get_link(self):
        if self.product:
            return self.product.get_absolute_url()
        if self.category:
            return self.category.get_absolute_url()
        return reverse("store:home")


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Aguardando pagamento"
        PAID = "PAID", "Pago"
        REJECTED = "REJECTED", "Recusado"
        CANCELLED = "CANCELLED", "Cancelado"
        REFUNDED = "REFUNDED", "Reembolsado"
        ERROR = "ERROR", "Erro no pagamento"

    class DeliveryStatus(models.TextChoices):
        PENDING = "PENDING", "Aguardando entrega manual"
        DELIVERED = "DELIVERED", "Entregue"

    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    idempotency_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    nickname = models.CharField("Nickname", max_length=16)
    buyer_name = models.CharField("Nome do comprador", max_length=120, blank=True)
    buyer_email = models.EmailField("E-mail", blank=True)
    buyer_cpf_last4 = models.CharField("CPF (últimos 4)", max_length=4, blank=True)
    payment_method = models.CharField("Forma de pagamento", max_length=30, blank=True)
    total = models.DecimalField("Total (R$)", max_digits=9, decimal_places=2)
    status = models.CharField(
        "Status", max_length=12, choices=Status.choices, default=Status.PENDING,
    )
    delivery_status = models.CharField(
        "Entrega", max_length=12, choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
    )
    mercadopago_payment_id = models.CharField(
        "ID Mercado Pago", max_length=40, blank=True, null=True, unique=True,
    )
    mercadopago_status = models.CharField("Status Mercado Pago", max_length=40, blank=True)
    mercadopago_status_detail = models.CharField(
        "Detalhe do status Mercado Pago", max_length=120, blank=True,
    )
    pix_qr_code = models.TextField("Pix copia e cola", blank=True)
    pix_qr_code_base64 = models.TextField("QR Code Pix (base64)", blank=True)
    pix_ticket_url = models.TextField("URL do comprovante Pix", blank=True)
    paid_at = models.DateTimeField("Pago em", null=True, blank=True)
    delivered_at = models.DateTimeField("Entregue em", null=True, blank=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Pedido #{str(self.order_id)[:8]} — {self.nickname}"

    @property
    def is_paid(self):
        return self.status == self.Status.PAID

    def mark_delivered(self):
        if not self.is_paid:
            return False
        self.delivery_status = self.DeliveryStatus.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=["delivery_status", "delivered_at", "updated_at"])
        return True


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=80)
    product_icon = models.CharField(max_length=8, default="🎁")
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
