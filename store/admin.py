from django.contrib import admin, messages

from .models import Category, Order, OrderItem, PromoBanner, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "accent", "product_count", "order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_active", "order")
    list_filter = ("category", "is_active")
    search_fields = ("name", "short_description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order",)


@admin.register(PromoBanner)
class PromoBannerAdmin(admin.ModelAdmin):
    list_display = ("title", "theme", "is_active", "order")
    ordering = ("order",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "product_icon", "unit_price", "quantity")


@admin.action(description="Marcar pedidos pagos como entregues")
def mark_orders_delivered(modeladmin, request, queryset):
    count = 0
    skipped = 0
    for order in queryset:
        if order.mark_delivered():
            count += 1
        else:
            skipped += 1
    if count:
        modeladmin.message_user(request, f"{count} pedido(s) marcado(s) como entregue(s).", messages.SUCCESS)
    if skipped:
        modeladmin.message_user(request, f"{skipped} pedido(s) ignorado(s) porque ainda não estão pagos.", messages.WARNING)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "short_id", "nickname", "buyer_name", "total", "payment_method",
        "status", "delivery_status", "mercadopago_payment_id", "created_at",
    )
    list_filter = ("status", "delivery_status", "payment_method")
    search_fields = ("nickname", "buyer_name", "buyer_email", "mercadopago_payment_id", "order_id")
    readonly_fields = (
        "order_id", "idempotency_key", "total", "mercadopago_payment_id",
        "mercadopago_status", "mercadopago_status_detail", "paid_at",
        "created_at", "updated_at", "buyer_cpf_last4",
    )
    inlines = [OrderItemInline]
    actions = [mark_orders_delivered]

    @admin.display(description="Pedido")
    def short_id(self, obj):
        return f"#{str(obj.order_id)[:8]}"
