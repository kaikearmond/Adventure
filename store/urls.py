from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("healthz/", views.healthz, name="healthz"),
    path("entrar/", views.landing, name="landing"),
    path("trocar-jogador/", views.change_player, name="change_player"),
    path("", views.home, name="home"),
    path("equipe/", views.team, name="team"),
    path("outros/", views.misc_info, name="misc_info"),
    path("categoria/<slug:slug>/", views.category_detail, name="category"),
    path("produto/<slug:slug>/", views.product_detail, name="product_detail"),
    path("carrinho/", views.cart_view, name="cart"),
    path("carrinho/adicionar/<int:product_id>/", views.cart_add, name="cart_add"),
    path("carrinho/remover/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("carrinho/atualizar/<int:product_id>/", views.cart_update, name="cart_update"),
    path("checkout/", views.checkout, name="checkout"),
    path("pagamentos/mercadopago/processar/", views.process_payment, name="process_payment"),
    path("pagamentos/mercadopago/webhook/", views.mercadopago_webhook, name="mercadopago_webhook"),
    path("pedido/<uuid:order_id>/", views.order_success, name="order_success"),
    path("pedido/<uuid:order_id>/status/", views.order_status, name="order_status"),
]
