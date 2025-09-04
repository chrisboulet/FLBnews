#!/usr/bin/env python3
"""
Test rapide pour générer un bulletin avec seulement quelques sources
pour vérifier que la traduction fonctionne
"""

import sys
import os
sys.path.insert(0, 'src')

import config
from main import FLBNewsApp
import logging

# Configurer les logs
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Réduire temporairement les sources pour un test rapide
config.NEWS_SOURCES = {
    'Canadian Grocer': config.NEWS_SOURCES['Canadian Grocer'],
    'Western Grocer': config.NEWS_SOURCES['Western Grocer'],
    'Le Bulletin des Agriculteurs': config.NEWS_SOURCES['Le Bulletin des Agriculteurs']
}

# S'assurer que l'analyse est activée
config.ANALYSIS_CONFIG['enable_bm25'] = True
config.ANALYSIS_CONFIG['mode'] = 'economique'

# Réduire le nombre de jours pour aller plus vite
config.BULLETIN_CONFIG['days_to_scrape'] = 3

print("🚀 Test rapide de génération de bulletin avec traduction")
print("="*60)
print("Sources testées:")
for source in config.NEWS_SOURCES.keys():
    print(f"  - {source}")
print("="*60)

app = FLBNewsApp()
result = app.run_bulletin_generation()

if result:
    print(f"\n✅ Bulletin généré avec succès!")
    print(f"📄 Fichier: {result['path']}")
    print(f"📊 Articles: {len(result['news_items'])}")
    
    print("\n📰 Articles sélectionnés:")
    print("-"*40)
    for item in result['news_items']:
        print(f"\n[{item.source}]")
        print(f"Titre: {item.title[:80]}")
        
        # Vérifier si c'est traduit pour les sources anglaises
        if item.source in ['Canadian Grocer', 'Western Grocer']:
            if any(word in item.title.lower() for word in ['le', 'la', 'les', 'de', 'du', 'des']):
                print("✅ Traduit en français")
            else:
                print("⚠️ Peut-être non traduit")
else:
    print("❌ Erreur lors de la génération")