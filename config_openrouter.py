#!/usr/bin/env python3
"""
Configuration pour utiliser OpenRouter avec GPT-5 dans FLB News
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration du moteur d'analyse hybride avec OpenRouter
ANALYSIS_CONFIG = {
    # Activation des différents moteurs
    'enable_bm25': True,           # Scoring rapide par mots-clés
    'enable_ollama': False,         # LLM local (désactivé)
    'enable_openrouter': True,      # OpenRouter avec GPT-5 (activé)
    
    # Mode de fonctionnement
    'mode': 'premium',              # economique, standard, ou premium
    
    # Configuration OpenRouter
    'openrouter_api_key': os.getenv('OPENROUTER_API_KEY'),
    'openrouter_model': 'openai/o4',
    
    # Seuils et limites
    'bm25_threshold': 0.3,          # Score minimum pour analyse LLM
    'max_ollama_articles': 20,      # Limite pour Ollama (même si désactivé)
    'max_openrouter_articles': 7,   # Top 7 articles analysés avec O4
    
    # Mots-clés pour le scoring BM25
    'keywords': {
        # Mots-clés principaux
        'distributeur alimentaire': 10,
        'distribution alimentaire': 10,
        'grossiste alimentaire': 9,
        'FLB': 10,
        
        # Géographie
        'québec': 8,
        'capitale-nationale': 8,
        'ville de québec': 8,
        'canada': 5,
        
        # Secteur d'activité
        'supply chain': 7,
        'chaîne d\'approvisionnement': 7,
        'logistique': 7,
        'livraison': 6,
        'transport': 6,
        'entrepôt': 6,
        
        # Clients
        'restauration': 7,
        'restaurant': 7,
        'hôtellerie': 6,
        'HORECA': 7,
        'épicerie': 6,
        'détaillant': 6,
        'cafétéria': 5,
        'traiteur': 5,
        
        # Produits
        'produits frais': 6,
        'viande': 5,
        'volaille': 5,
        'fruits et légumes': 5,
        'produits laitiers': 5,
        'surgelés': 5,
        'épicerie fine': 4,
        
        # Tendances et enjeux
        'tendance alimentaire': 6,
        'innovation': 6,
        'durabilité': 5,
        'local': 6,
        'produit local': 7,
        'économie circulaire': 5,
        'gaspillage alimentaire': 6,
        
        # Enjeux sectoriels
        'pénurie': 7,
        'main-d\'œuvre': 6,
        'inflation': 6,
        'coût': 5,
        'prix': 5,
        'réglementation': 6,
        'norme sanitaire': 7,
        'HACCP': 6,
        'traçabilité': 6,
        
        # Technologie
        'technologie': 5,
        'automatisation': 6,
        'intelligence artificielle': 5,
        'IA': 5,
        'digitalisation': 5,
        'e-commerce': 5
    }
}

def get_analysis_config():
    """
    Retourner la configuration pour le moteur d'analyse
    """
    # Vérifier que la clé API est configurée
    if ANALYSIS_CONFIG['enable_openrouter'] and not ANALYSIS_CONFIG['openrouter_api_key']:
        print("⚠️ Clé API OpenRouter non configurée dans .env")
        print("   OpenRouter sera désactivé.")
        ANALYSIS_CONFIG['enable_openrouter'] = False
        ANALYSIS_CONFIG['mode'] = 'economique'
    
    return ANALYSIS_CONFIG

if __name__ == "__main__":
    # Test de la configuration
    config = get_analysis_config()
    
    print("Configuration du moteur d'analyse:")
    print(f"  - BM25: {'✅' if config['enable_bm25'] else '❌'}")
    print(f"  - Ollama: {'✅' if config['enable_ollama'] else '❌'}")
    print(f"  - OpenRouter: {'✅' if config['enable_openrouter'] else '❌'}")
    
    if config['enable_openrouter']:
        print(f"  - Modèle: {config['openrouter_model']}")
        print(f"  - Articles max: {config['max_openrouter_articles']}")
        print(f"  - Mode: {config['mode']}")
        print(f"  - Clé API: {config['openrouter_api_key'][:20]}...")