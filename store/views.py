import json
import re
import uuid

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import connection, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .cart import Cart
from .mercadopago import (
    MercadoPagoAPIError,
    MercadoPagoConfigurationError,
    apply_payment_to_order,
    create_payment,
    get_payment,
    sync_order,
    validate_webhook_signature,
)
from .models import Category, Order, OrderItem, Product

NICKNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")
STORE_CATEGORY_SLUGS = ("vips", "tags")


def healthz(request):
    """Readiness simples para validar banco e configuração no deploy."""
    database_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        database_ok = False

    payload = {
        "ok": database_ok,
        "database": database_ok,
        "mercadopago": bool(
            settings.MERCADOPAGO_PUBLIC_KEY and settings.MERCADOPAGO_ACCESS_TOKEN
        ),
        "webhook_signature": bool(settings.MERCADOPAGO_WEBHOOK_SECRET),
    }
    return JsonResponse(payload, status=200 if database_ok else 503)


def landing(request):
    next_url = request.GET.get("next") or request.POST.get("next") or reverse("store:home")
    error = None
    if request.method == "POST":
        nickname = request.POST.get("nickname", "").strip()
        if NICKNAME_RE.match(nickname):
            request.session[settings.PLAYER_SESSION_KEY] = nickname
            return redirect(next_url)
        error = "Nickname inválido. Use de 3 a 16 caracteres: letras, números e _."
    return render(request, "store/landing.html", {"error": error, "next": next_url})


def change_player(request):
    request.session.pop(settings.PLAYER_SESSION_KEY, None)
    return redirect("store:landing")


def home(request):
    categories = (
        Category.objects.filter(is_active=True, slug__in=STORE_CATEGORY_SLUGS)
        .prefetch_related("products")
    )
    return render(request, "store/home.html", {"categories": categories})


def team(request):
    members = [
        {
            "role": "Fundador",
            "name": "Athos Ramon",
            "bio": "Responsável pela visão geral do servidor e Game-Developer Interino.",
            "avatar_url": "https://mc-heads.net/body/athenor/120",
        },
        {
            "role": "Co-Fundador",
            "name": "kaikinhoxw",
            "bio": "Responsável pela progressão do servidor, WebDeveloper",
            "avatar_url": "https://mc-heads.net/body/kaikinhoxw/120",
        },
        {
            "role": "Administrador",
            "name": "Daniel",
            "bio": "Responsável pelas mídias e engajamento do servidor",
            "avatar_url": "https://mc-heads.net/body/dx_z/120",
        },
    ]
    return render(request, "store/team.html", {"members": members})


def misc_info(request):
    discord_url = "https://discord.gg/3PrpQB2Jkh"
    cards = [
        {
            "anchor": "regras",
            "icon": "📜",
            "title": "Regras do servidor",
            "summary": (
                "Respeite a comunidade, jogue de forma justa e utilize o chat com "
                "responsabilidade. Abra para consultar todas as regras e punições."
            ),
            "expand_label": "Ver regras completas",
            "list_items": [
                "Respeite jogadores e membros da equipe. Ofensas, perseguições, discriminação e assédio não são permitidos.",
                "É proibido utilizar cheats, hacks, macros abusivas, clientes modificados ou qualquer vantagem não autorizada.",
                "Não explore bugs, falhas, duplicações ou erros do servidor. Ao encontrar um problema, reporte-o imediatamente à equipe.",
                "Atitudes tóxicas, provocações excessivas, ameaças, golpes e tentativas de prejudicar outros jogadores são proibidas.",
                "Não divulgue outros servidores, comunidades, lojas ou serviços sem autorização prévia da administração.",
                "Use o chat de maneira adequada. Evite spam, flood, conteúdo impróprio e discussões que prejudiquem a convivência.",
                "O descumprimento das regras poderá resultar em advertência, mute, suspensão, remoção de benefícios ou banimento, conforme a gravidade e reincidência.",
            ],
        },
        {
            "anchor": "discord",
            "image_url": "https://cdnjs.cloudflare.com/ajax/libs/simple-icons/15.16.0/discord.svg",
            "title": "Discord da comunidade",
            "summary": "Entre no Discord oficial para acompanhar novidades, eventos e conversar com outros jogadores da comunidade.",
            "link": discord_url,
            "link_text": "Entrar no Discord",
        },
        {
            "anchor": "suporte",
            "icon": "🛟",
            "title": "Suporte",
            "summary": (
                "Todo suporte ao servidor é realizado através do Discord oficial. "
                "Entre em nosso servidor para receber atendimento da equipe, tirar dúvidas, "
                "reportar problemas e obter suporte especializado."
            ),
            "link": discord_url,
            "link_text": "Solicitar suporte",
        },
        {
            "anchor": "reembolso",
            "icon": "↩️",
            "title": "Política de reembolso",
            "summary": "As compras correspondem a produtos digitais. Abra para consultar as condições de entrega, análise de exceções, fraude e solicitações por engano.",
            "expand_label": "Ver política completa",
            "detail_paragraphs": [
                "As compras realizadas na loja correspondem a produtos e benefícios digitais vinculados à conta informada pelo jogador.",
                "Após a confirmação do pagamento e a entrega dos benefícios no servidor, normalmente não será possível solicitar reembolso, pois o produto digital já terá sido disponibilizado e utilizado ou estará disponível para uso.",
                "Situações excepcionais poderão ser analisadas individualmente pela administração, sem garantia de aprovação. Compras realizadas por engano devem ser comunicadas imediatamente, antes da entrega ou utilização do benefício.",
                "Casos de fraude, contestação indevida, uso de dados de terceiros ou tentativa de abuso poderão ser investigados e resultar na suspensão da conta, remoção dos benefícios e outras medidas cabíveis.",
                "Ao concluir uma compra, o usuário declara que revisou os produtos, valores e nickname informado, e concorda com esta política e com os demais termos da loja.",
            ],
        },
    ]
    return render(request, "store/misc_info.html", {"cards": cards})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True, slug__in=STORE_CATEGORY_SLUGS)
    sort = request.GET.get("ordenar", "destaque")
    products = category.products.filter(is_active=True)
    if sort == "menor-preco":
        products = products.order_by("price")
    elif sort == "maior-preco":
        products = products.order_by("-price")
    elif sort == "novidades":
        products = products.order_by("-created_at")
    else:
        sort = "destaque"
        products = products.order_by("order", "-is_featured", "name")
    return render(request, "store/category.html", {"category": category, "products": products, "sort": sort})


def product_detail(request, slug):
    product = get_object_or_404(
        Product,
        slug=slug,
        is_active=True,
        category__slug__in=STORE_CATEGORY_SLUGS,
    )
    related = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    return render(request, "store/product_detail.html", {"product": product, "related": related})


def cart_view(request):
    return render(request, "store/cart.html", {"cart": Cart(request)})


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True,
        category__slug__in=STORE_CATEGORY_SLUGS,
    )
    cart = Cart(request)
    cart.add(product)
    message = f"{product.icon} {product.name} adicionado ao carrinho!"
    if _is_ajax(request):
        return JsonResponse({"cart_count": len(cart), "cart_total": f"{cart.total:.2f}", "message": message})
    messages.success(request, message)
    if request.POST.get("buy_now"):
        return redirect("store:checkout")
    return redirect(request.META.get("HTTP_REFERER", reverse("store:home")))


@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    if _is_ajax(request):
        return JsonResponse({"cart_count": len(cart), "cart_total": f"{cart.total:.2f}"})
    return redirect("store:cart")


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except ValueError:
        quantity = 1
    cart = Cart(request)
    cart.set_quantity(product, quantity)
    if _is_ajax(request):
        return JsonResponse({"cart_count": len(cart), "cart_total": f"{cart.total:.2f}"})
    return redirect("store:cart")


def _clean_cpf(value):
    return re.sub(r"\D", "", value or "")


def _valid_cpf_shape(value):
    cpf = _clean_cpf(value)
    return len(cpf) == 11 and len(set(cpf)) > 1


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect("store:cart")
    nickname = request.session.get(settings.PLAYER_SESSION_KEY, "")
    config = {
        "publicKey": settings.MERCADOPAGO_PUBLIC_KEY,
        "amount": f"{cart.total:.2f}",
        "maxInstallments": settings.MERCADOPAGO_MAX_INSTALLMENTS,
        "processUrl": reverse("store:process_payment"),
        "enabled": bool(settings.MERCADOPAGO_PUBLIC_KEY and settings.MERCADOPAGO_ACCESS_TOKEN),
    }
    return render(
        request,
        "store/checkout.html",
        {
            "cart": cart,
            "nickname": nickname,
            "checkout_config": config,
            "mercadopago_ready": config["enabled"],
        },
    )


@require_POST
def process_payment(request):
    if not settings.MERCADOPAGO_PUBLIC_KEY or not settings.MERCADOPAGO_ACCESS_TOKEN:
        return JsonResponse({"ok": False, "error": "Mercado Pago ainda não está configurado."}, status=503)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Dados de pagamento inválidos."}, status=400)

    buyer = payload.get("buyer") or {}
    form_data = payload.get("formData") or {}
    buyer_name = str(buyer.get("name") or "").strip()
    buyer_email = str(buyer.get("email") or "").strip().lower()
    cpf = _clean_cpf(str(buyer.get("cpf") or ""))

    if len(buyer_name) < 3:
        return JsonResponse({"ok": False, "error": "Informe o nome completo do comprador."}, status=400)
    try:
        validate_email(buyer_email)
    except ValidationError:
        return JsonResponse({"ok": False, "error": "Informe um e-mail válido."}, status=400)
    if not _valid_cpf_shape(cpf):
        return JsonResponse({"ok": False, "error": "Informe um CPF válido com 11 dígitos."}, status=400)

    try:
        attempt_id = uuid.UUID(str(payload.get("attemptId") or ""))
    except (ValueError, TypeError, AttributeError):
        return JsonResponse({"ok": False, "error": "Identificador da compra inválido. Recarregue a página."}, status=400)

    cart = Cart(request)
    nickname = request.session.get(settings.PLAYER_SESSION_KEY, "")
    if len(cart) == 0:
        return JsonResponse({"ok": False, "error": "Seu carrinho está vazio."}, status=400)

    with transaction.atomic():
        order = Order.objects.select_for_update().filter(idempotency_key=attempt_id).first()
        if order is None:
            order = Order.objects.create(
                idempotency_key=attempt_id,
                nickname=nickname,
                buyer_name=buyer_name,
                buyer_email=buyer_email,
                buyer_cpf_last4=cpf[-4:],
                total=cart.total,
                status=Order.Status.PENDING,
            )
            for entry in cart:
                OrderItem.objects.create(
                    order=order,
                    product=entry["product"],
                    product_name=entry["product"].name,
                    product_icon=entry["product"].icon,
                    unit_price=entry["product"].price,
                    quantity=entry["quantity"],
                )
        elif order.nickname != nickname:
            return JsonResponse({"ok": False, "error": "Pedido não pertence a este jogador."}, status=409)

    if order.mercadopago_payment_id:
        cart.clear()
        return JsonResponse({"ok": True, "orderUrl": reverse("store:order_success", kwargs={"order_id": order.order_id})})

    try:
        payment = create_payment(order, form_data, cpf=cpf)
        apply_payment_to_order(order, payment)
    except MercadoPagoConfigurationError as exc:
        order.status = Order.Status.ERROR
        order.save(update_fields=["status", "updated_at"])
        return JsonResponse({"ok": False, "error": str(exc)}, status=503)
    except MercadoPagoAPIError as exc:
        order.status = Order.Status.ERROR
        order.save(update_fields=["status", "updated_at"])
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    cart.clear()
    return JsonResponse(
        {
            "ok": True,
            "status": order.status,
            "orderUrl": reverse("store:order_success", kwargs={"order_id": order.order_id}),
        }
    )


def _player_order(request, order_id):
    nickname = request.session.get(settings.PLAYER_SESSION_KEY, "")
    return get_object_or_404(Order.objects.prefetch_related("items"), order_id=order_id, nickname=nickname)


def order_success(request, order_id):
    order = _player_order(request, order_id)
    if order.status == Order.Status.PENDING and order.mercadopago_payment_id:
        try:
            order = sync_order(order)
        except MercadoPagoAPIError:
            pass
    return render(request, "store/order_success.html", {"order": order})


def order_status(request, order_id):
    order = _player_order(request, order_id)
    if order.status == Order.Status.PENDING and order.mercadopago_payment_id:
        try:
            order = sync_order(order)
        except MercadoPagoAPIError:
            pass
    return JsonResponse(
        {
            "status": order.status,
            "statusLabel": order.get_status_display(),
            "paid": order.is_paid,
            "deliveryStatus": order.delivery_status,
        }
    )


@csrf_exempt
@require_POST
def mercadopago_webhook(request):
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except (ValueError, UnicodeDecodeError):
        payload = {}

    data_id = str(
        request.GET.get("data.id")
        or request.GET.get("data_id")
        or (payload.get("data") or {}).get("id")
        or ""
    )
    notification_type = str(payload.get("type") or request.GET.get("type") or "")
    if not data_id or (notification_type and notification_type != "payment"):
        return HttpResponse(status=200)

    if not validate_webhook_signature(request, data_id):
        return HttpResponse(status=401)

    try:
        payment = get_payment(data_id)
    except (MercadoPagoAPIError, MercadoPagoConfigurationError):
        return HttpResponse(status=200)

    external_reference = str(payment.get("external_reference") or "")
    try:
        order_uuid = uuid.UUID(external_reference)
    except (ValueError, TypeError):
        return HttpResponse(status=200)

    order = Order.objects.filter(order_id=order_uuid).first()
    if not order:
        return HttpResponse(status=200)

    try:
        apply_payment_to_order(order, payment)
    except MercadoPagoAPIError:
        return HttpResponse(status=200)
    return HttpResponse(status=200)
