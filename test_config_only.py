#!/usr/bin/env python3
"""
Test rapide pour v\u00e9rifier les changements de configuration
"""

print("="*60)
print("TEST DE CONFIGURATION - O4 et 7 Articles")
print("="*60)

# 1. V\u00e9rifier la configuration OpenRouter
print("\n1️⃣ V\u00e9rification de la configuration OpenRouter:")
from config_openrouter import get_analysis_config
config = get_analysis_config()

assert config['openrouter_model'] == 'openai/o4', f"❌ Mod\u00e8le incorrect: {config['openrouter_model']}"
print(f"   ✅ Mod\u00e8le: {config['openrouter_model']}")

assert config['max_openrouter_articles'] == 7, f"❌ Nombre d'articles incorrect: {config['max_openrouter_articles']}"
print(f"   ✅ Nombre max d'articles: {config['max_openrouter_articles']}")

# 2. V\u00e9rifier que NewsItem a le champ image_url
print("\n2️⃣ V\u00e9rification du support des images:")
from src.scraper import NewsItem
import inspect

fields = [field for field in dir(NewsItem) if not field.startswith('_')]
assert 'image_url' in fields, "❌ Le champ image_url n'est pas dans NewsItem"
print("   ✅ NewsItem.image_url pr\u00e9sent")

# 3. V\u00e9rifier EnhancedNewsItem
from src.enhanced_scraper import EnhancedNewsItem
fields = [field for field in dir(EnhancedNewsItem) if not field.startswith('_')]
assert 'image_url' in fields, "❌ Le champ image_url n'est pas dans EnhancedNewsItem"
print("   ✅ EnhancedNewsItem.image_url pr\u00e9sent")

# 4. V\u00e9rifier que le template a \u00e9t\u00e9 mis \u00e0 jour
print("\n3️⃣ V\u00e9rification du template:")
with open('templates/ground_news_style.html', 'r') as f:
    template_content = f.read()
    
assert 'item.image_url' in template_content, "❌ Le template ne r\u00e9f\u00e9rence pas item.image_url"
print("   ✅ Template mis \u00e0 jour pour afficher les images")

assert "background-image: url('{{ item.image_url }}')" in template_content, "❌ Le style d'image n'est pas correct"
print("   ✅ Style background-image correctement configur\u00e9")

# 5. V\u00e9rifier l'article vedette dans enhanced_scraper
print("\n4️⃣ V\u00e9rification de la logique article vedette:")
with open('src/enhanced_scraper.py', 'r') as f:
    scraper_content = f.read()
    
assert 'featured_article' in scraper_content, "❌ Pas de logique pour l'article vedette"
print("   ✅ Logique article vedette pr\u00e9sente")

assert 'final_selection.append(featured_article)' in scraper_content, "❌ L'article vedette n'est pas ajout\u00e9 \u00e0 la fin"
print("   ✅ Article vedette plac\u00e9 en position 7")

print("\n" + "="*60)
print("✅ TOUS LES TESTS DE CONFIGURATION SONT PASS\u00c9S!")
print("="*60)

print("\n📋 R\u00e9sum\u00e9 des changements impl\u00e9ment\u00e9s:")
print("   • Mod\u00e8le migr\u00e9 de GPT-5 vers O4")
print("   • Support de 7 articles (6 normaux + 1 vedette)")
print("   • Images extraites et affich\u00e9es pour chaque article")
print("   • Article vedette plac\u00e9 en derni\u00e8re position")
print("\nPour tester compl\u00e8tement, ex\u00e9cutez: python main.py")