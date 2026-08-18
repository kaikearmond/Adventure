from decimal import Decimal

from django.conf import settings

from .models import Product


class Cart:
    """Carrinho simples guardado na sessão do jogador."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_KEY)
        if cart is None:
            cart = self.session[settings.CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, product, quantity=1):
        product_id = str(product.id)
        if product_id in self.cart:
            self.cart[product_id]["quantity"] += quantity
        else:
            self.cart[product_id] = {"quantity": quantity}
        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def set_quantity(self, product, quantity):
        product_id = str(product.id)
        if product_id in self.cart:
            if quantity <= 0:
                del self.cart[product_id]
            else:
                self.cart[product_id]["quantity"] = quantity
            self.save()

    def clear(self):
        self.session[settings.CART_SESSION_KEY] = {}
        self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        products_map = {str(p.id): p for p in products}
        for product_id, item in self.cart.items():
            product = products_map.get(product_id)
            if not product:
                continue
            yield {
                "product": product,
                "quantity": item["quantity"],
                "subtotal": product.price * item["quantity"],
            }

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    @property
    def total(self):
        return sum(entry["subtotal"] for entry in self)
