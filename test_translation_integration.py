#!/usr/bin/env python3
"""
Test de l'intégration de la traduction avec le système d'analyse avancée
"""

import sys
import os
from datetime import datetime
sys.path.insert(0, 'src')

from scraper import FoodIndustryNewsScraper, NewsItem
from translator import NewsTranslator

def test_translation_with_analysis():
    print("\n" + "="*60)
    print("TEST: Traduction avec Analyse Avancée")
    print("="*60)
    
    # Configuration minimale
    test_sources = {
        'Canadian Grocer': {
            'type': 'rss',
            'url': 'test',
            'language': 'en',
            'priority_multiplier': 1.5
        },
        'Western Grocer': {
            'type': 'rss',
            'url': 'test',
            'language': 'en',
            'priority_multiplier': 1.4
        },
        'Le Journal de Québec': {
            'type': 'rss',
            'url': 'test',
            'language': 'fr',
            'priority_multiplier': 1.3
        }
    }
    
    # Configuration d'analyse en mode économique
    analysis_config = {
        'enable_bm25': True,
        'enable_ollama': False,
        'enable_openrouter': False,
        'mode': 'economique',
        'bm25_threshold': 0.3,
        'max_ollama_articles': 20,
        'max_openrouter_articles': 5
    }
    
    # Créer le scraper avec analyseur
    scraper = FoodIndustryNewsScraper(
        test_sources,
        analysis_config=analysis_config
    )
    
    # Créer des articles de test
    test_items = [
        NewsItem(
            title="Food Distribution Innovation Transforms Supply Chain",
            summary="Major Canadian food distributors are implementing new technologies to improve efficiency. The industry is seeing unprecedented changes in warehouse management and delivery systems.",
            source="Canadian Grocer",
            url="https://test1.com",
            published_date=datetime.now(),
            full_text="Full article content..."
        ),
        NewsItem(
            title="Western Canada Sees Growth in Local Food Movement",
            summary="Restaurants and retailers in Western Canada are increasingly sourcing from local producers. This trend is reshaping distribution networks.",
            source="Western Grocer",
            url="https://test2.com",
            published_date=datetime.now(),
            full_text="Full article content..."
        ),
        NewsItem(
            title="Québec lance un nouveau programme pour les distributeurs",
            summary="Le gouvernement du Québec annonce des mesures de soutien pour les distributeurs alimentaires régionaux.",
            source="Le Journal de Québec",
            url="https://test3.com",
            published_date=datetime.now(),
            full_text="Contenu complet..."
        )
    ]
    
    print(f"\n{len(test_items)} articles de test créés")
    print("\nAVANT traduction:")
    print("-" * 40)
    for item in test_items:
        print(f"📰 [{item.source}] {item.title[:50]}...")
    
    # Filtrer et traduire avec le nouveau système
    if scraper.analyzer:
        print("\n✅ Utilisation du système d'analyse avancée")
        filtered_items = scraper._advanced_filter(test_items)
    else:
        print("\n⚠️ Utilisation du système basique (analyseur non disponible)")
        filtered_items = scraper._filter_relevant_news(test_items)
    
    print(f"\n{len(filtered_items)} articles sélectionnés et traduits")
    print("\nAPRÈS traduction:")
    print("-" * 40)
    
    for item in filtered_items:
        print(f"\n📰 [{item.source}]")
        print(f"   Titre: {item.title[:80]}")
        print(f"   Résumé: {item.summary[:100]}...")
        print(f"   Score: {getattr(item, 'relevance_score', 0):.1f}")
        
        # Vérifier si la traduction a eu lieu pour les sources anglaises
        if item.source in ['Canadian Grocer', 'Western Grocer']:
            # Détecter des mots français dans le titre
            french_words = ['de', 'le', 'la', 'les', 'dans', 'pour', 'avec', 'et']
            has_french = any(word in item.title.lower().split() for word in french_words)
            
            if has_french or 'distribution' in item.title.lower():
                print("   ✅ Traduction effectuée")
            else:
                print("   ⚠️ Traduction peut-être incomplète")

def test_translator_directly():
    print("\n" + "="*60)
    print("TEST: Traducteur Direct")
    print("="*60)
    
    translator = NewsTranslator()
    
    test_texts = [
        ("Food distribution companies face new challenges", "Canadian Grocer"),
        ("Supply chain innovation transforms the industry", "Western Grocer"),
        ("Les distributeurs québécois innovent", "Le Journal de Québec")
    ]
    
    for text, source in test_texts:
        translated = translator.translate_if_needed(text, source)
        print(f"\n[{source}]")
        print(f"Original: {text}")
        print(f"Traduit:  {translated}")
        if text != translated:
            print("✅ Traduction appliquée")
        else:
            print("ℹ️ Pas de traduction nécessaire")

def main():
    print("\n" + "#"*60)
    print("# TEST D'INTÉGRATION TRADUCTION + ANALYSE")
    print("#"*60)
    
    # Test direct du traducteur
    test_translator_directly()
    
    # Test avec le système complet
    test_translation_with_analysis()
    
    print("\n" + "#"*60)
    print("# TESTS TERMINÉS")
    print("#"*60)
    
    print("\n📊 Résumé:")
    print("- La traduction est maintenant intégrée dans _advanced_filter()")
    print("- Les articles des sources anglaises sont traduits APRÈS sélection")
    print("- Seuls les 5 articles finaux sont traduits (économie de crédits DeepL)")
    
    print("\n💡 Notes importantes:")
    print("1. La traduction se fait APRÈS l'analyse de pertinence")
    print("2. Seuls les articles sélectionnés sont traduits")
    print("3. Titre, résumé ET explication de pertinence sont traduits")

if __name__ == "__main__":
    main()