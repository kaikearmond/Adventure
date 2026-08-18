from django.db import migrations
from django.utils.text import slugify


def seed_catalog(apps, schema_editor):
    Category = apps.get_model("store", "Category")
    Product = apps.get_model("store", "Product")

    Category.objects.filter(slug__in=("itens-especiais", "cosmeticos", "outros")).delete()

    categories = [
        {
            "name": "VIPs", "slug": "vips", "icon": "👑", "accent": "#FFC845", "order": 1,
            "mascot": "", "tagline": "Assinaturas com vantagens no servidor",
            "description": "Planos de VIP com benefícios que evoluem junto com você: mais homes, kits, acesso a áreas exclusivas e muito mais.",
            "is_active": True,
        },
        {
            "name": "Tags", "slug": "tags", "icon": "🏷️", "accent": "#3FD0D4", "order": 2,
            "mascot": "", "tagline": "Tags sazonais e de eventos para o seu chat",
            "description": "Tags temáticas de datas comemorativas e eventos especiais, para exibir no chat durante a temporada.",
            "is_active": True,
        },
    ]
    cat_objs = {}
    for data in categories:
        obj, _ = Category.objects.update_or_create(slug=data["slug"], defaults=data)
        cat_objs[data["slug"]] = obj

    products = [
        {"cat":"vips","name":"Beta","short":"Mais liberdade para desbravar o mundo Pixelmon.","desc":"Para quem já pegou gosto pela exploração e quer ir além.\nInclui vantagens de mobilidade e mais liberdade no servidor.","perks":"Kit diário de itens\n/fly em áreas liberadas\n4 homes (/home)\n+1 slot de loja pessoal","icon":"🧭","rarity":"UNCOMMON","price":"50.00","duration":"Permanente","badge":"","order":0},
        {"cat":"vips","name":"Adventure","short":"Primeiros passos com benefícios diários.","desc":"Ideal para quem está começando a jornada.\nInclui vantagens básicas para explorar o mapa com mais conforto.","perks":"Kit diário de itens básicos\n2 homes (/home)\nTag [Adventure] no chat\nAcesso ao lobby VIP","icon":"🥾","rarity":"COMMON","price":"49.90","duration":"Permanente","badge":"MAIS POPULAR","order":1},
        {"cat":"vips","name":"VIP","short":"Para treinadores que querem dominar o servidor.","desc":"Um plano completo para jogadores ativos.\nDesbloqueia kits e benefícios exclusivos para sua jornada.","perks":"Benefícios exclusivos de VIP\nKit semanal\n6 homes (/home)\nAcesso a áreas exclusivas","icon":"🛡️","rarity":"RARE","price":"34.99","duration":"Permanente","badge":"","order":2},
        {"cat":"tags","name":"Férias","short":"Uma tag descontraída para curtir o recesso.","desc":"Tag temática para o período de férias,\nideal para mostrar que você está de folga mas não parou de jogar.","perks":"Tag [Férias] no chat\nCor exclusiva por tempo limitado\nCompatível com qualquer VIP","icon":"🏖️","rarity":"COMMON","price":"29.99","duration":"Temporada","badge":"","order":0},
        {"cat":"tags","name":"Páscoa","short":"Comemore a Páscoa com uma tag exclusiva.","desc":"Tag sazonal de Páscoa, disponível apenas\ndurante o período do evento no servidor.","perks":"Tag [Páscoa] colorida no chat\nEfeito visual leve ao coletar itens\nEdição sazonal","icon":"🐰","rarity":"UNCOMMON","price":"29.99","duration":"Temporada","badge":"","order":1},
        {"cat":"tags","name":"Halloween","short":"Uma tag sombria para a época mais assustadora do ano.","desc":"Tag temática de Halloween, com um visual\nespecial disponível somente durante o evento.","perks":"Tag [Halloween] com efeito animado\nParticipação prioritária em eventos temáticos\nEdição sazonal","icon":"🎃","rarity":"RARE","price":"29.99","duration":"Temporada","badge":"","order":2},
        {"cat":"tags","name":"Natal","short":"A tag mais festiva do servidor.","desc":"Tag temática de Natal, com efeito de neve\ne cores exclusivas durante o período natalino.","perks":"Tag [Natal] animada no chat\nEfeito de neve ao caminhar durante o evento\nEdição sazonal limitada","icon":"🎄","rarity":"EPIC","price":"29.99","duration":"Temporada","badge":"EDIÇÃO SAZONAL","order":3},
    ]

    expected = []
    for p in products:
        slug = slugify(p["name"])
        expected.append(slug)
        Product.objects.update_or_create(
            slug=slug,
            defaults={
                "category": cat_objs[p["cat"]], "name": p["name"],
                "short_description": p["short"], "description": p["desc"], "perks": p["perks"],
                "icon": p["icon"], "rarity": p["rarity"], "duration_label": p["duration"],
                "price": p["price"], "original_price": None, "badge_text": p["badge"],
                "is_featured": False, "is_promotion": False, "promotion_ends_at": None,
                "stock_label": "Entrega manual", "order": p["order"], "is_active": True,
            },
        )
    Product.objects.filter(category__slug__in=("vips", "tags")).exclude(slug__in=expected).delete()


class Migration(migrations.Migration):
    dependencies = [("store", "0003_order_mercadopago")]
    operations = [migrations.RunPython(seed_catalog, migrations.RunPython.noop)]
