#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')
import feedparser
import requests

# Test des nouveaux flux RSS
test_sources = {
    'Radio-Canada Nouvelles': 'https://ici.radio-canada.ca/rss/4159',
    'La Presse': 'https://www.lapresse.ca/actualites/rss', 
    'Journal de Montréal': 'https://www.journaldemontreal.com/rss.xml',
    'Journal de Québec': 'https://www.journaldequebec.com/rss.xml',
    'TVA Nouvelles': 'https://www.tvanouvelles.ca/rss.xml',
    'Global News': 'https://globalnews.ca/feed/',
    'CTV News': 'https://www.ctvnews.ca/rss/ctvnews-ca-top-stories-public-rss-1.822009',
    'CBC News': 'https://www.cbc.ca/webfeed/rss/rss-topstories',
    'Le Devoir': 'https://www.ledevoir.com/rss/editoriaux.xml',
    'Globe and Mail': 'https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/',
    'National Post': 'https://nationalpost.com/feed'
}

print("Test des nouveaux flux RSS des grands médias canadiens")
print("=" * 60)

for name, url in test_sources.items():
    try:
        print(f"\n{name}:")
        print("-" * 40)
        
        # Test de connexion
        response = requests.get(url, timeout=10, headers={'User-Agent': 'FLBNews/1.0'})
        response.raise_for_status()
        
        # Parse RSS
        feed = feedparser.parse(url)
        
        if feed.entries:
            print(f"✓ Flux RSS valide - {len(feed.entries)} articles trouvés")
            # Afficher le premier titre comme exemple
            first_entry = feed.entries[0]
            title = first_entry.get('title', 'Sans titre')[:80]
            print(f"  Premier article: {title}...")
        else:
            print(f"✗ Aucun article trouvé dans le flux")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Erreur de connexion: {str(e)[:60]}")
    except Exception as e:
        print(f"✗ Erreur: {str(e)[:60]}")