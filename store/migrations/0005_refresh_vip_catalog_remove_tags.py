from django.db import migrations
from django.utils.text import slugify


def refresh_catalog(apps, schema_editor):
    Category = apps.get_model("store", "Category")
    Product = apps.get_model("store", "Product")

    # Remove definitivamente as categorias que não fazem mais parte da loja.
    Category.objects.filter(
        slug__in=("tags", "itens-especiais", "cosmeticos", "outros")
    ).delete()

    vip_category, _ = Category.objects.update_or_create(
        slug="vips",
        defaults={
            "name": "VIPs",
            "icon": "👑",
            "accent": "#E63946",
            "order": 1,
            "mascot": "",
            "tagline": "Assinaturas com vantagens no servidor",
            "description": "Escolha entre o Adventure mensal e o Beta permanente para ampliar sua experiência no servidor.",
            "is_active": True,
        },
    )

    products = [
        {
            "name": "Adventure",
            "short": "Benefícios mensais para evoluir sua jornada.",
            "desc": "Um plano mensal para jogadores ativos que querem mais conforto e vantagens recorrentes durante a aventura.",
            "perks": "Kit periódico de apoio\n3 homes (/home)\nTag [Adventure] no chat\nAcesso a uma área VIP",
            "icon": "🥾",
            "rarity": "COMMON",
            "price": "24.99",
            "duration": "Mensal",
            "badge": "MAIS POPULAR",
            "order": 0,
        },
        {
            "name": "Beta",
            "short": "Vantagens permanentes para quem quer ir além.",
            "desc": "Um plano de pagamento único com benefícios permanentes e mais recursos para explorar o servidor com liberdade.",
            "perks": "Kit periódico aprimorado\n/fly em áreas liberadas\n6 homes (/home)\nPrioridade em filas\nTag [Beta] no chat\nAcesso a áreas VIP",
            "icon": "🧭",
            "rarity": "UNCOMMON",
            "price": "49.99",
            "duration": "Permanente",
            "badge": "",
            "order": 1,
        },
    ]

    expected_slugs = []
    for data in products:
        slug = slugify(data["name"])
        expected_slugs.append(slug)
        Product.objects.update_or_create(
            slug=slug,
            defaults={
                "category": vip_category,
                "name": data["name"],
                "short_description": data["short"],
                "description": data["desc"],
                "perks": data["perks"],
                "icon": data["icon"],
                "rarity": data["rarity"],
                "duration_label": data["duration"],
                "price": data["price"],
                "original_price": None,
                "badge_text": data["badge"],
                "is_featured": False,
                "is_promotion": False,
                "promotion_ends_at": None,
                "stock_label": "Entrega manual",
                "order": data["order"],
                "is_active": True,
            },
        )

    Product.objects.filter(category=vip_category).exclude(
        slug__in=expected_slugs
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("store", "0004_seed_store_catalog")]

    operations = [
        migrations.RunPython(refresh_catalog, migrations.RunPython.noop),
    ]
