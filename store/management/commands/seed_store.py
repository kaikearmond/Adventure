from django.core.management.base import BaseCommand
from django.utils.text import slugify

from store.models import Category, Product


class Command(BaseCommand):
    help = "Popula a loja Pixelmon Adventures com VIPs e Tags."

    def handle(self, *args, **options):
        # Categorias removidas não devem voltar ao executar o seed.
        Category.objects.filter(
            slug__in=("itens-especiais", "cosmeticos", "outros")
        ).delete()

        categories = [
            dict(
                name="VIPs", slug="vips", icon="👑", accent="#FFC845", order=1,
                mascot="",
                tagline="Assinaturas com vantagens no servidor",
                description="Planos de VIP com benefícios que evoluem junto com você: mais homes, kits, acesso a áreas exclusivas e muito mais.",
            ),
            dict(
                name="Tags", slug="tags", icon="🏷️", accent="#3FD0D4", order=2,
                mascot="",
                tagline="Tags sazonais e de eventos para o seu chat",
                description="Tags temáticas de datas comemorativas e eventos especiais, para exibir no chat durante a temporada.",
            ),
        ]

        cat_objs = {}
        for category_data in categories:
            obj, _ = Category.objects.update_or_create(
                slug=category_data["slug"], defaults=category_data
            )
            cat_objs[category_data["slug"]] = obj

        products = [
            dict(
                cat="vips", name="Beta",
                short="Mais liberdade para desbravar o mundo Pixelmon.",
                desc="Para quem já pegou gosto pela exploração e quer ir além.\nInclui vantagens de mobilidade e mais liberdade no servidor.",
                perks="Kit diário de itens\n/fly em áreas liberadas\n4 homes (/home)\n+1 slot de loja pessoal",
                icon="🧭", rarity="UNCOMMON", price="50.00",
                duration="Permanente", featured=False, order=0,
            ),
            dict(
                cat="vips", name="Adventure",
                short="Primeiros passos com benefícios diários.",
                desc="Ideal para quem está começando a jornada.\nInclui vantagens básicas para explorar o mapa com mais conforto.",
                perks="Kit diário de itens básicos\n2 homes (/home)\nTag [Adventure] no chat\nAcesso ao lobby VIP",
                icon="🥾", rarity="COMMON", price="49.90",
                duration="Permanente", featured=False, badge="MAIS POPULAR", order=1,
            ),
            dict(
                cat="vips", name="VIP",
                short="Para treinadores que querem dominar o servidor.",
                desc="Um plano completo para jogadores ativos.\nDesbloqueia kits e benefícios exclusivos para sua jornada.",
                perks="Benefícios exclusivos de VIP\nKit semanal\n6 homes (/home)\nAcesso a áreas exclusivas",
                icon="🛡️", rarity="RARE", price="34.99",
                duration="Permanente", featured=False, order=2,
            ),
            dict(
                cat="tags", name="Férias",
                short="Uma tag descontraída para curtir o recesso.",
                desc="Tag temática para o período de férias,\nideal para mostrar que você está de folga mas não parou de jogar.",
                perks="Tag [Férias] no chat\nCor exclusiva por tempo limitado\nCompatível com qualquer VIP",
                icon="🏖️", rarity="COMMON", price="29.99", duration="Temporada", order=0,
            ),
            dict(
                cat="tags", name="Páscoa",
                short="Comemore a Páscoa com uma tag exclusiva.",
                desc="Tag sazonal de Páscoa, disponível apenas\ndurante o período do evento no servidor.",
                perks="Tag [Páscoa] colorida no chat\nEfeito visual leve ao coletar itens\nEdição sazonal",
                icon="🐰", rarity="UNCOMMON", price="29.99", duration="Temporada", order=1,
            ),
            dict(
                cat="tags", name="Halloween",
                short="Uma tag sombria para a época mais assustadora do ano.",
                desc="Tag temática de Halloween, com um visual\nespecial disponível somente durante o evento.",
                perks="Tag [Halloween] com efeito animado\nParticipação prioritária em eventos temáticos\nEdição sazonal",
                icon="🎃", rarity="RARE", price="29.99", duration="Temporada", order=2,
            ),
            dict(
                cat="tags", name="Natal",
                short="A tag mais festiva do servidor.",
                desc="Tag temática de Natal, com efeito de neve\ne cores exclusivas durante o período natalino.",
                perks="Tag [Natal] animada no chat\nEfeito de neve ao caminhar durante o evento\nEdição sazonal limitada",
                icon="🎄", rarity="EPIC", price="29.99", duration="Temporada",
                badge="EDIÇÃO SAZONAL", order=3,
            ),
        ]

        expected_slugs = set()
        for product_data in products:
            slug = slugify(product_data["name"])
            expected_slugs.add(slug)
            defaults = {
                "category": cat_objs[product_data["cat"]],
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

        Product.objects.filter(category__slug__in=("vips", "tags")).exclude(
            slug__in=expected_slugs
        ).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"{len(categories)} categorias e {len(products)} produtos criados/atualizados."
            )
        )
