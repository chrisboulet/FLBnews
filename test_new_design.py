#!/usr/bin/env python3
import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, 'src')

from scraper import NewsItem
from bulletin_generator import BulletinGenerator

# Créer quelques articles de test
test_news = [
    NewsItem(
        title="Les épiciers québécois s'adaptent à la nouvelle réalité économique",
        url="https://example.com/1",
        source="La Presse Canadienne",
        published_date=datetime.now() - timedelta(days=1),
        summary="Les détaillants alimentaires du Québec font face à de nouveaux défis économiques avec l'inflation persistante et les changements dans les habitudes de consommation. Les épiciers indépendants et les grandes chaînes adaptent leurs stratégies pour maintenir leur compétitivité. L'industrie observe une augmentation de la demande pour les produits locaux et biologiques, malgré les pressions sur les prix. Les distributeurs jouent un rôle crucial dans cette transformation en optimisant leurs chaînes d'approvisionnement et en développant de nouveaux partenariats avec les producteurs régionaux. Cette évolution représente une opportunité pour les entreprises de distribution alimentaire de se positionner comme des acteurs clés de la transition.",
        full_text="",
        tags=["distribution", "québec", "économie"],
        relevance_to_flb="Directement pertinent pour FLB en tant que distributeur alimentaire québécois"
    ),
    NewsItem(
        title="Innovation in Food Supply Chain Management Transforms Canadian Market",
        url="https://example.com/2",
        source="Canadian Grocer",
        published_date=datetime.now() - timedelta(days=2),
        summary="Major Canadian food distributors are implementing cutting-edge technology to streamline operations and reduce waste. Artificial intelligence and predictive analytics are revolutionizing inventory management, while blockchain technology ensures food traceability from farm to fork. These innovations are particularly beneficial for regional distributors serving the restaurant and hospitality sectors. The integration of these technologies is expected to reduce operational costs by 15-20% over the next three years while improving service quality and delivery times.",
        full_text="",
        tags=["innovation", "supply chain", "technology"],
        relevance_to_flb=""
    ),
    NewsItem(
        title="Pénurie de main-d'œuvre dans le secteur alimentaire: solutions innovantes",
        url="https://example.com/3",
        source="Journal de Québec",
        published_date=datetime.now() - timedelta(hours=12),
        summary="Le secteur de la distribution alimentaire au Québec fait face à une pénurie de main-d'œuvre sans précédent. Les entreprises du secteur développent des stratégies créatives pour attirer et retenir les talents, incluant des programmes de formation améliorés et des conditions de travail plus flexibles. Les distributeurs alimentaires de la région de Québec sont particulièrement touchés, avec des besoins criants en chauffeurs-livreurs et en personnel d'entrepôt. Cette situation pousse l'industrie à accélérer l'automatisation de certaines opérations tout en investissant davantage dans le capital humain.",
        full_text="",
        tags=["emploi", "québec", "logistique"],
        relevance_to_flb="Impact direct sur les opérations de FLB dans la région de Québec"
    ),
    NewsItem(
        title="Sustainable Packaging Trends Reshape Food Distribution Industry",
        url="https://example.com/4",
        source="Western Grocer",
        published_date=datetime.now() - timedelta(days=3),
        summary="Environmental concerns are driving major changes in packaging across the food distribution sector. Wholesalers and distributors are partnering with manufacturers to implement eco-friendly packaging solutions that reduce plastic waste by up to 40%. These initiatives are particularly important for businesses serving the foodservice industry, where single-use packaging has been prevalent. The shift towards sustainable materials is creating new opportunities for innovation while meeting increasing consumer demand for environmentally responsible practices.",
        full_text="",
        tags=["sustainability", "packaging", "environment"]
    ),
    NewsItem(
        title="Boom des produits locaux: une opportunité pour les distributeurs régionaux",
        url="https://example.com/5",
        source="Le Bulletin des Agriculteurs",
        published_date=datetime.now() - timedelta(days=4),
        summary="La demande pour les produits alimentaires locaux connaît une croissance exceptionnelle au Québec. Les distributeurs régionaux sont idéalement positionnés pour capitaliser sur cette tendance en développant des réseaux d'approvisionnement courts avec les producteurs locaux. Cette approche permet non seulement de réduire l'empreinte carbone mais aussi d'offrir des produits plus frais aux restaurants et aux détaillants. Les entreprises de distribution qui investissent dans ces partenariats locaux voient leurs ventes augmenter de 25% en moyenne. La région de la Capitale-Nationale est particulièrement dynamique avec plusieurs initiatives innovantes.",
        full_text="",
        tags=["local", "agriculture", "partenariats"],
        relevance_to_flb="Opportunité stratégique pour FLB de développer son réseau local"
    )
]

# Générer le bulletin avec le nouveau template
generator = BulletinGenerator()

output_path = os.path.join('bulletins', f'test_design_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
bulletin = generator.generate_bulletin(test_news, output_path)

print(f"✅ Bulletin de test généré avec succès!")
print(f"📁 Fichier: {output_path}")
print(f"📊 {len(test_news)} articles inclus")
print(f"\n🎨 Le nouveau design inspiré de Ground News inclut:")
print("   • Header moderne avec logo et date")
print("   • Hero section avec statistiques")  
print("   • Cartes d'articles style Ground News")
print("   • Badges de source et tags")
print("   • Design responsive et moderne")