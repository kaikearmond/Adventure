from django.conf import settings

from .cart import Cart
from .models import Category


def player_context(request):
    nickname = request.session.get(settings.PLAYER_SESSION_KEY, "")
    cart = Cart(request)
    return {
        "player_nickname": nickname,
        "nav_categories": Category.objects.filter(
            is_active=True, slug__in=("vips", "tags")
        ),
        "cart_count": len(cart),
        "cart_total": cart.total,
    }
