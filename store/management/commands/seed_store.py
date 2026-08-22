from django.core.management.base import BaseCommand
from django.utils.text import slugify

from store.models import Category, Product


class Command(BaseCommand):
    help = "Popula a loja Pixelmon Adventures com os planos VIP oficiais."

    def handle(self, *args, **options):
        # Categorias removidas não devem voltar ao executar o seed.
        Category.objects.filter(
            slug__in=("tags", "itens-especiais", "cosmeticos", "outros")
        ).delete()

        category_data = dict(
            name="VIPs", slug="vips", icon="👑", accent="#E63946", order=1,
            mascot="",
            tagline="Assinaturas com vantagens no servidor",
            description="Escolha entre o Adventure mensal e o Beta permanente para ampliar sua experiência no servidor.",
        )
        vip_category, _ = Category.objects.update_or_create(
            slug="vips", defaults=category_data
        )

        products = [
            dict(
                name="Adventure",
                short="Benefícios mensais para evoluir sua jornada.",
                desc="Um plano mensal para jogadores ativos que querem mais conforto e vantagens recorrentes durante a aventura.",
                perks="Kit periódico de apoio\n3 homes (/home)\nTag [Adventure] no chat\nAcesso a uma área VIP",
                icon="🥾", rarity="COMMON", price="24.99",
                duration="Mensal", featured=False, badge="MAIS POPULAR", order=0,
            ),
            dict(
                name="Beta",
                short="Vantagens permanentes para quem quer ir além.",
                desc="Um plano de pagamento único com benefícios permanentes e mais recursos para explorar o servidor com liberdade.",
                perks="Kit periódico aprimorado\n/fly em áreas liberadas\n6 homes (/home)\nPrioridade em filas\nTag [Beta] no chat\nAcesso a áreas VIP",
                icon="🧭", rarity="UNCOMMON", price="49.99",
                duration="Permanente", featured=False, order=1,
            ),
        ]

        expected_slugs = set()
        for product_data in products:
            slug = slugify(product_data["name"])
            expected_slugs.add(slug)
            defaults = {
                "category": vip_category,
                "name": product_data["name"],
                "short_description": product_data["short"],
                "description": product_data["desc"],
                "perks": product_data["perks"],
                "icon": product_data.get("icon", "🎁"),
                "rarity": product_data.get("rarity", "COMMON"),
                "duration_label": product_data.get("duration", ""),
                "price": product_data["price"],
                "original_price": None,
                "badge_text": product_data.get("badge", ""),
                "is_featured": product_data.get("featured", False),
                "is_promotion": False,
                "promotion_ends_at": None,
                "stock_label": product_data.get("stock_label", "Entrega manual"),
                "order": product_data["order"],
                "is_active": True,
            }
            Product.objects.update_or_create(slug=slug, defaults=defaults)

        Product.objects.filter(category=vip_category).exclude(
            slug__in=expected_slugs
        ).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"1 categoria e {len(products)} produtos criados/atualizados."
            )
        )
