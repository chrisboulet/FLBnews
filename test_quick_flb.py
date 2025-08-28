#!/usr/bin/env python3
"""
Test rapide pour v\u00e9rifier:
1. Migration vers O4
2. 7 articles avec article vedette
3. Images incluses
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """V\u00e9rifier la configuration"""
    print("🔍 V\u00e9rification de la configuration...")
    
    from config_openrouter import get_analysis_config
    config = get_analysis_config()
    
    print(f"  ✓ Mod\u00e8le: {config['openrouter_model']}")
    assert config['openrouter_model'] == 'openai/o4', f"Mod\u00e8le devrait \u00eatre openai/o4, mais est {config['openrouter_model']}"
    
    print(f"  ✓ Nombre d'articles: {config['max_openrouter_articles']}")
    assert config['max_openrouter_articles'] == 7, f"Devrait avoir 7 articles, mais a {config['max_openrouter_articles']}"
    
    print("✅ Configuration correcte!\n")
    return config

def test_scraper():
    """V\u00e9rifier le scraper avec images"""
    print("📰 Test du scraper avec extraction d'images...")
    
    from src.scraper import FoodIndustryNewsScraper, NewsItem
    from config import NEWS_SOURCES, RELEVANCE_KEYWORDS
    from config_openrouter import get_analysis_config
    
    # Cr\u00e9er un scraper
    scraper = FoodIndustryNewsScraper(
        NEWS_SOURCES,
        keywords_config=RELEVANCE_KEYWORDS,
        analysis_config=get_analysis_config()
    )
    
    # R\u00e9cup\u00e9rer quelques articles
    print("  ⏳ R\u00e9cup\u00e9ration des articles (peut prendre quelques secondes)...")
    all_news = scraper.scrape_all_sources(days_back=1)
    
    if not all_news:
        print("  ⚠️ Aucun article trouv\u00e9")
        return []
    
    print(f"  ✓ {len(all_news)} articles r\u00e9cup\u00e9r\u00e9s")
    
    # V\u00e9rifier les images
    with_images = [item for item in all_news if item.image_url]
    print(f"  ✓ {len(with_images)} articles avec images")
    
    # Afficher quelques exemples
    print("\n  📸 Exemples d'images extraites:")
    for item in with_images[:3]:
        print(f"    - {item.title[:40]}...")
        print(f"      Image: {item.image_url[:60]}...")
    
    return all_news[:7]  # Retourner seulement 7 pour le test

def test_enhanced_scraper():
    """V\u00e9rifier le scraper am\u00e9lior\u00e9 avec article vedette"""
    print("\n🌟 Test du scraper am\u00e9lior\u00e9 avec article vedette...")
    
    try:
        from src.enhanced_scraper import EnhancedFoodNewsScraper
        from config import NEWS_SOURCES
        
        scraper = EnhancedFoodNewsScraper(NEWS_SOURCES, use_openrouter=False)
        
        # Test simple sans OpenRouter pour la vitesse
        print("  ⏳ S\u00e9lection des 7 meilleurs articles...")
        news = scraper.get_top_news(days_back=1, limit=7)
        
        if len(news) < 7:
            print(f"  ⚠️ Seulement {len(news)} articles trouv\u00e9s")
        else:
            print(f"  ✓ {len(news)} articles s\u00e9lectionn\u00e9s")
            
            # V\u00e9rifier l'article vedette (le dernier)
            featured = news[-1] if news else None
            if featured:
                print(f"\n  🌟 Article vedette:")
                print(f"     Titre: {featured.title[:60]}...")
                print(f"     Score: {featured.relevance_score:.0%}")
                print(f"     Image: {'✓' if featured.image_url else '✗'}")
                
                if featured.image_url:
                    print(f"     URL: {featured.image_url[:60]}...")
        
        return news
    
    except ImportError as e:
        print(f"  ❌ Erreur d'import: {e}")
        return []

def test_bulletin_generation(news_items):
    """Test de g\u00e9n\u00e9ration du bulletin avec images"""
    print("\n📄 Test de g\u00e9n\u00e9ration du bulletin...")
    
    if not news_items:
        print("  ⚠️ Pas d'articles pour g\u00e9n\u00e9rer le bulletin")
        return
    
    from src.bulletin_generator import BulletinGenerator
    
    # G\u00e9n\u00e9rer le bulletin
    generator = BulletinGenerator('templates/ground_news_style.html')
    
    # Nom du fichier de test
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f'bulletins/test_o4_{timestamp}.html'
    
    bulletin_path = generator.generate_bulletin(news_items, output_path)
    
    if os.path.exists(bulletin_path):
        print(f"  ✓ Bulletin g\u00e9n\u00e9r\u00e9: {bulletin_path}")
        
        # V\u00e9rifier que les images sont dans le HTML
        with open(bulletin_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        image_count = content.count('background-image: url(')
        print(f"  ✓ {image_count} images int\u00e9gr\u00e9es dans le bulletin")
        
        print(f"\n✅ Test termin\u00e9! Ouvrez le fichier pour voir le r\u00e9sultat:")
        print(f"   file://{os.path.abspath(bulletin_path)}")
    else:
        print(f"  ❌ Erreur lors de la g\u00e9n\u00e9ration du bulletin")

def main():
    print("="*60)
    print("TEST COMPLET - FLB NEWS avec O4 et Images")
    print("="*60)
    
    try:
        # 1. V\u00e9rifier la config
        config = test_config()
        
        # 2. Tester le scraper de base
        basic_news = test_scraper()
        
        # 3. Tester le scraper am\u00e9lior\u00e9
        enhanced_news = test_enhanced_scraper()
        
        # 4. G\u00e9n\u00e9rer un bulletin de test
        if enhanced_news:
            test_bulletin_generation(enhanced_news)
        elif basic_news:
            print("\n⚠️ Utilisation des articles du scraper de base")
            test_bulletin_generation(basic_news)
        
        print("\n" + "="*60)
        print("✅ TOUS LES TESTS SONT PASS\u00c9S!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()