import os
from dotenv import load_dotenv

load_dotenv()

# Charger la configuration des sources depuis le fichier externe
def load_news_sources():
    """Charger la configuration des sources depuis sources_config.json"""
    import json
    import logging
    
    config_file = os.path.join(os.path.dirname(__file__), 'sources_config.json')
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Filtrer seulement les sources activées
        news_sources = {}
        for source_name, source_config in config['news_sources'].items():
            if source_config.get('enabled', True):
                # Créer une copie de la config sans les champs de contrôle
                clean_config = {k: v for k, v in source_config.items() 
                              if k not in ['enabled', 'disabled_reason']}
                news_sources[source_name] = clean_config
            else:
                reason = source_config.get('disabled_reason', 'Non spécifié')
                logging.info(f"Source désactivée: {source_name} - {reason}")
                
        logging.info(f"Configuration chargée: {len(news_sources)} sources actives sur {len(config['news_sources'])} totales")
        return news_sources
        
    except FileNotFoundError:
        logging.error(f"Fichier de configuration introuvable: {config_file}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Erreur JSON dans {config_file}: {e}")
        return {}
    except Exception as e:
        logging.error(f"Erreur lors du chargement de la configuration: {e}")
        return {}

# Configuration des sources chargée dynamiquement
NEWS_SOURCES = load_news_sources()

# Configuration du bulletin
BULLETIN_CONFIG = {
    'output_directory': os.path.join(os.path.dirname(__file__), 'bulletins'),
    'days_to_scrape': 7,
    'max_articles': 7,  # Limite à 7 nouvelles les plus pertinentes
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
    # PRIORITÉ CRITIQUE: Importation et commerce international
    'importation': 15,
    'import': 15, 
    'douane': 12,
    'tarif douanier': 12,
    'commerce international': 12,
    'international': 10,
    'accord commercial': 11,
    'frontière': 10,
    
    # Distribution et concurrence (surveillance)
    'distributeur alimentaire': 12,
    'grossiste alimentaire': 12,
    'distribution alimentaire': 12,
    'food distribution': 12,
    'food wholesale': 12,
    'sysco': 13,
    'gordon food': 13,
    'concurrence': 11,
    'concurrent': 11,
    'wholesale': 10,
    'grossiste': 10,
    
    # CLIENTÈLE PRIORITAIRE: Restauration
    'restauration': 12,
    'restaurant': 12,
    'foodservice': 12,
    'service alimentaire': 12,
    'chef': 9,
    'menu': 8,
    'restaurateur': 10,
    'chaîne resto': 10,
    
    # CLIENTÈLE IMPORTANTE: Hôtellerie
    'hôtellerie': 11,
    'hôtel': 11,
    'HORECA': 12,
    'hébergement': 9,
    'tourisme': 8,
    'hospitalité': 9,
    
    # PROXIMITÉ GÉOGRAPHIQUE - Zone d'opération immédiate (priorité très élevée)
    'ville de québec': 14,
    'quebec city': 14,
    'capitale-nationale': 13,
    'beauport': 12,
    'lévis': 12,
    'sainte-foy': 12,
    'charlesbourg': 12,
    'ancienne-lorette': 11,
    'saint-augustin': 11,
    
    # PROVINCE DE QUÉBEC - Marché élargi stratégique
    'québec': 10,
    'quebec': 10,
    'montréal': 9,
    'montreal': 9,
    'sherbrooke': 8,
    'gatineau': 8,
    'trois-rivières': 8,
    'saguenay': 8,
    'chicoutimi': 8,
    'rimouski': 7,
    'drummondville': 7,
    'granby': 7,
    'saint-jean': 7,
    
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