from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class PlayerGateMiddleware:
    """Exige nickname na loja, mas nunca bloqueia webhooks/infra."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        is_exempt = (
            path.startswith("/healthz/")
            or path.startswith("/admin")
            or path.startswith("/static")
            or path.startswith("/media")
            or path.startswith("/pagamentos/mercadopago/webhook/")
        )
        if not is_exempt:
            has_nickname = bool(request.session.get(settings.PLAYER_SESSION_KEY))
            landing_url = reverse("store:landing")
            if not has_nickname and path != landing_url:
                return redirect(f"{landing_url}?next={path}")
        return self.get_response(request)
