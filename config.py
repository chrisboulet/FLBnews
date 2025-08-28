import os
from dotenv import load_dotenv

load_dotenv()

# Configuration des sources de nouvelles par catégorie
NEWS_SOURCES = {
    # CATÉGORIE A - Publications commerciales et industrielles (Priorité maximale)
    'Canadian Grocer': {
        'type': 'rss',
        'url': 'https://canadiangrocer.com/feed',
        'category': 'A',
        'priority_multiplier': 1.5,
        'language': 'en',
        'description': 'Publication nationale de référence pour l\'industrie épicière'
    },
    'Grocery Business': {
        'type': 'rss',
        'url': 'https://www.grocerybusiness.ca/feed',
        'category': 'A',
        'priority_multiplier': 1.5,
        'language': 'en',
        'description': 'Magazine B2B pour détaillants et marketeurs'
    },
    'Western Grocer': {
        'type': 'rss',
        'url': 'https://westerngrocer.com/feed',
        'category': 'A',
        'priority_multiplier': 1.4,
        'language': 'en',
        'description': 'Publication spécialisée pour l\'Ouest canadien'
    },
    'Food in Canada': {
        'type': 'rss',
        'url': 'https://www.foodincanada.com/feed/',
        'category': 'A',
        'priority_multiplier': 1.5,
        'language': 'en',
        'description': 'Transformation alimentaire et boissons du Canada'
    },
    'Foodservice and Hospitality': {
        'type': 'rss',
        'url': 'https://www.foodserviceandhospitality.com/feed/',
        'category': 'A',
        'priority_multiplier': 1.4,
        'language': 'en',
        'description': 'Industrie canadienne de la restauration'
    },
    
    # CATÉGORIE B - Médias agricoles québécois (Priorité élevée pour FLB)
    'La Terre de Chez Nous': {
        'type': 'rss',
        'url': 'https://www.laterre.ca/feed',
        'category': 'B',
        'priority_multiplier': 1.4,
        'language': 'fr',
        'description': 'Hebdomadaire de l\'UPA Québec'
    },
    'Le Bulletin des Agriculteurs': {
        'type': 'rss',
        'url': 'https://www.lebulletin.com/feed',
        'category': 'B',
        'priority_multiplier': 1.3,
        'language': 'fr',
        'description': 'Plus de 100 ans d\'expertise agricole'
    },
    'Le Coopérateur': {
        'type': 'website',
        'url': 'https://cooperateur.coop/fr/',
        'article_selector': 'article',
        'title_selector': 'h2',
        'category': 'B',
        'priority_multiplier': 1.3,
        'language': 'fr',
        'description': 'Magazine de Sollio Groupe Coopératif'
    },
    'Journal Agricom': {
        'type': 'rss',
        'url': 'https://journalagricom.ca/feed',
        'category': 'B',
        'priority_multiplier': 1.2,
        'language': 'fr',
        'description': 'Perspective francophone sur les enjeux agricoles'
    },
    
    # CATÉGORIE C - Sources gouvernementales et organisationnelles
    'Agriculture et Agroalimentaire Canada': {
        'type': 'rss',
        'url': 'https://www.agr.gc.ca/fra/nouvelles-dagriculture-et-agroalimentaire-canada/?id=1399497793524&fluxrss',
        'category': 'C',
        'priority_multiplier': 1.2,
        'language': 'fr',
        'description': 'Publications officielles du gouvernement fédéral'
    },
    'MAPAQ': {
        'type': 'website',
        'url': 'https://www.mapaq.gouv.qc.ca/fr/Regions/Pages/NouvellesRegionales.aspx',
        'article_selector': '.news-item',
        'title_selector': 'h3',
        'category': 'C',
        'priority_multiplier': 1.3,
        'language': 'fr',
        'description': 'Ministère agriculture Québec'
    },
    'Agri-Réseau': {
        'type': 'rss',
        'url': 'https://www.agrireseau.net/rss/nouvelles',
        'category': 'C',
        'priority_multiplier': 1.2,
        'language': 'fr',
        'description': 'Plateforme collaborative agricole du Québec'
    },
    
    # CATÉGORIE D - Médias nationaux agricoles
    'The Western Producer': {
        'type': 'rss',
        'url': 'https://www.producer.com/feed/',
        'category': 'D',
        'priority_multiplier': 1.0,
        'language': 'en',
        'description': 'Nouvelles agricoles nationales'
    },
    'Real Agriculture': {
        'type': 'rss',
        'url': 'https://www.realagriculture.com/feed/',
        'category': 'D',
        'priority_multiplier': 1.0,
        'language': 'en',
        'description': 'Plateforme numérique agricole'
    },
    
    # CATÉGORIE E - Médias généralistes avec section alimentaire
    'Les Affaires': {
        'type': 'rss',
        'url': 'https://www.lesaffaires.com/rss/agriculture-et-agroalimentaire',
        'category': 'E',
        'priority_multiplier': 1.1,
        'language': 'fr',
        'description': 'Économie et agroalimentaire québécois'
    },
    'Radio-Canada Économie': {
        'type': 'website',
        'url': 'https://ici.radio-canada.ca/economie',
        'base_url': 'https://ici.radio-canada.ca',
        'article_selector': 'article',
        'title_selector': 'h3',
        'category': 'E',
        'priority_multiplier': 1.0,
        'language': 'fr',
        'description': 'Actualités économiques québécoises'
    },
    'Radio-Canada Nouvelles': {
        'type': 'rss',
        'url': 'https://ici.radio-canada.ca/rss/4159',
        'category': 'E',
        'priority_multiplier': 1.2,
        'language': 'fr',
        'description': 'Nouvelles générales Radio-Canada'
    },
    'La Presse Canadienne': {
        'type': 'rss',
        'url': 'https://www.lapresse.ca/actualites/rss',
        'category': 'E',
        'priority_multiplier': 1.2,
        'language': 'fr',
        'description': 'Agence de presse nationale'
    },
    'Journal de Montréal': {
        'type': 'rss',
        'url': 'https://www.journaldemontreal.com/rss.xml',
        'category': 'E',
        'priority_multiplier': 1.1,
        'language': 'fr',
        'description': 'Grand quotidien québécois'
    },
    'Journal de Québec': {
        'type': 'rss',
        'url': 'https://www.journaldequebec.com/rss.xml',
        'category': 'E',
        'priority_multiplier': 1.2,
        'language': 'fr',
        'description': 'Quotidien de la région de Québec'
    },
    'TVA Nouvelles': {
        'type': 'rss',
        'url': 'https://www.tvanouvelles.ca/rss.xml',
        'category': 'E',
        'priority_multiplier': 1.1,
        'language': 'fr',
        'description': 'Réseau TVA actualités'
    },
    'Global News': {
        'type': 'rss',
        'url': 'https://globalnews.ca/feed/',
        'category': 'E',
        'priority_multiplier': 1.0,
        'language': 'en',
        'description': 'Réseau anglophone national'
    },
    'CTV News': {
        'type': 'rss',
        'url': 'https://www.ctvnews.ca/rss/ctvnews-ca-top-stories-public-rss-1.822009',
        'category': 'E',
        'priority_multiplier': 1.0,
        'language': 'en',
        'description': 'Réseau CTV actualités'
    },
    'CBC News': {
        'type': 'rss',
        'url': 'https://www.cbc.ca/webfeed/rss/rss-topstories',
        'category': 'E',
        'priority_multiplier': 1.0,
        'language': 'en',
        'description': 'Société Radio-Canada anglophone'
    },
    'Le Devoir': {
        'type': 'rss',
        'url': 'https://www.ledevoir.com/rss/editoriaux.xml',
        'category': 'E',
        'priority_multiplier': 1.1,
        'language': 'fr',
        'description': 'Journal de référence québécois'
    },
    'The Globe and Mail': {
        'type': 'rss',
        'url': 'https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/',
        'category': 'E',
        'priority_multiplier': 1.0,
        'language': 'en',
        'description': 'Journal national canadien'
    },
    'National Post': {
        'type': 'rss',
        'url': 'https://nationalpost.com/feed',
        'category': 'E',
        'priority_multiplier': 1.0,
        'language': 'en',
        'description': 'Quotidien national canadien'
    }
}

# Configuration du bulletin
BULLETIN_CONFIG = {
    'output_directory': os.path.join(os.path.dirname(__file__), 'bulletins'),
    'days_to_scrape': 7,
    'max_articles': 5,  # Limite à 5 nouvelles les plus pertinentes
    'max_per_source': 2,  # Maximum 2 nouvelles par source
    'template_path': os.path.join(os.path.dirname(__file__), 'templates', 'ground_news_style.html'),
    'cache_duration_hours': 48  # Cache pour éviter les doublons
}

# Configuration email
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
    'sender_email': os.getenv('SENDER_EMAIL', ''),
    'sender_password': os.getenv('SENDER_PASSWORD', ''),
    'recipient_emails': os.getenv('RECIPIENT_EMAILS', '').split(',') if os.getenv('RECIPIENT_EMAILS') else []
}

# Configuration SharePoint
SHAREPOINT_CONFIG = {
    'site_url': os.getenv('SHAREPOINT_SITE_URL', ''),
    'document_library': os.getenv('SHAREPOINT_DOC_LIBRARY', 'Documents'),
    'username': os.getenv('SHAREPOINT_USERNAME', ''),
    'password': os.getenv('SHAREPOINT_PASSWORD', '')
}

# Configuration de la planification
SCHEDULE_CONFIG = {
    'enabled': os.getenv('SCHEDULE_ENABLED', 'False').lower() == 'true',
    'time': os.getenv('SCHEDULE_TIME', '08:00'),
    'days': os.getenv('SCHEDULE_DAYS', 'monday,wednesday,friday').split(',')
}

# Configuration de l'analyseur avancé
ANALYSIS_CONFIG = {
    # Modes: 'economique', 'standard', 'premium'
    'mode': 'economique',  # Commencer en mode économique (BM25 seulement)
    
    # Activer/désactiver les composants
    'enable_bm25': True,  # Toujours actif pour le pré-filtrage
    'enable_ollama': False,  # Mettre à True si Ollama est installé
    'enable_openrouter': False,  # Mettre à True avec une API key
    
    # Configuration Ollama (si activé)
    'ollama_model': 'phi2',  # Options: phi2, mistral, llama2, etc.
    'ollama_base_url': 'http://localhost:11434',
    
    # Configuration OpenRouter (si activé)
    'openrouter_api_key': os.getenv('OPENROUTER_API_KEY'),
    'openrouter_model': 'anthropic/claude-3-haiku',  # Économique et performant
    
    # Seuils et limites
    'bm25_threshold': 0.3,  # Score minimum pour analyse LLM
    'max_ollama_articles': 20,  # Nombre max d'articles à analyser avec Ollama
    'max_openrouter_articles': 5,  # Nombre max pour enrichissement cloud
    
    # Paramètres de cache
    'cache_enabled': True,
    'cache_duration_hours': 24
}

# Mots-clés et scoring pour FLB Solutions alimentaires
RELEVANCE_KEYWORDS = {
    # Cœur de métier (score élevé)
    'distributeur alimentaire': 10,
    'grossiste alimentaire': 10,
    'distribution alimentaire': 10,
    'food distribution': 10,
    'food wholesale': 10,
    'wholesale': 8,
    'grossiste': 8,
    
    # Marché géographique prioritaire
    'québec': 9,
    'ville de québec': 10,
    'capitale-nationale': 10,
    'beauport': 8,
    'lévis': 8,
    'sainte-foy': 8,
    'charlesbourg': 8,
    
    # Clientèle cible
    'restauration': 8,
    'restaurant': 8,
    'hôtellerie': 8,
    'HORECA': 9,
    'épicerie': 7,
    'détaillant': 7,
    'food service': 8,
    'service alimentaire': 8,
    'institutionnel': 7,
    
    # Opérations et logistique
    'chaîne d\'approvisionnement': 7,
    'supply chain': 7,
    'logistique': 6,
    'logistics': 6,
    'transport': 5,
    'entreposage': 5,
    'warehouse': 5,
    'livraison': 6,
    'delivery': 6,
    
    # Produits et catégories
    'produits frais': 5,
    'produce': 5,
    'viande': 5,
    'meat': 5,
    'poultry': 5,
    'volaille': 5,
    'produits laitiers': 5,
    'dairy': 5,
    'surgelés': 4,
    'frozen': 4,
    'épices': 4,
    'condiments': 4,
    
    # Tendances et innovation
    'tendances alimentaires': 4,
    'food trends': 4,
    'innovation': 4,
    'durabilité': 4,
    'sustainability': 4,
    'local': 5,
    'régional': 5,
    'biologique': 3,
    'organic': 3,
    
    # Économie et marché
    'inflation': 3,
    'prix': 3,
    'price': 3,
    'pénurie': 4,
    'shortage': 4,
    'demande': 3,
    'demand': 3
}