#!/usr/bin/env python3
"""
Scraper amélioré avec intégration OpenRouter GPT-4o
Génère des bulletins avec résumés intelligents et images
"""

import requests
from bs4 import BeautifulSoup
import feedparser
from newspaper import Article
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from src.translator import NewsTranslator
from src.openrouter_analyzer import OpenRouterAnalyzer, ArticleAnalysis
import os
import hashlib
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass 
class EnhancedNewsItem:
    """Article enrichi avec analyse GPT-4o et métadonnées"""
    # Données de base
    title: str
    url: str
    source: str
    published_date: Optional[datetime]
    
    # Contenu enrichi par GPT-4o
    smart_summary: str = ""  # Résumé intelligent
    flb_relevance: str = ""  # Pertinence pour FLB
    business_impact: str = ""
    opportunities: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    
    # Métadonnées
    category: str = ""
    relevance_score: float = 0.0
    confidence: float = 0.0
    image_url: str = ""  # URL de l'image de l'article
    
    # Texte original (pour référence)
    original_summary: str = ""
    full_text: str = ""

class EnhancedFoodNewsScraper:
    """Scraper amélioré avec analyse GPT-4o"""
    
    def __init__(self, sources_config: Dict, use_openrouter: bool = True):
        self.sources = sources_config
        self.translator = NewsTranslator()
        self.use_openrouter = use_openrouter
        
        # Initialiser l'analyseur OpenRouter si activé
        self.analyzer = None
        if use_openrouter:
            api_key = os.getenv('OPENROUTER_API_KEY')
            if api_key:
                self.analyzer = OpenRouterAnalyzer(api_key=api_key, model="openai/gpt-4o")
                logger.info("OpenRouter GPT-4o activé pour l'analyse")
            else:
                logger.warning("Clé API OpenRouter non trouvée")
                self.use_openrouter = False
    
    def extract_image_from_article(self, url: str) -> str:
        """Extraire l'image principale d'un article"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            # Retourner l'image principale si trouvée
            if article.top_image:
                return article.top_image
            
            # Sinon, essayer de trouver une image dans le HTML
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Chercher les balises meta pour l'image
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                return og_image['content']
            
            # Chercher la première grande image
            img = soup.find('img', src=True)
            if img:
                img_url = img['src']
                if not img_url.startswith('http'):
                    parsed = urlparse(url)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"
                    img_url = base_url + img_url
                return img_url
                
        except Exception as e:
            logger.debug(f"Impossible d'extraire l'image de {url}: {e}")
        
        return ""
    
    def scrape_all_sources(self, days_back: int = 7, num_articles: int = 7) -> List[EnhancedNewsItem]:
        """
        Scraper toutes les sources et analyser avec GPT-4o
        Retourne 7 articles avec le plus important en dernier (position vedette)
        """
        all_news = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Phase 1: Collecte des articles
        logger.info("Phase 1: Collecte des articles...")
        for source_name, source_config in self.sources.items():
            try:
                if source_config['type'] == 'rss':
                    news_items = self._scrape_rss(source_name, source_config, cutoff_date)
                elif source_config['type'] == 'website':
                    news_items = self._scrape_website(source_name, source_config, cutoff_date)
                else:
                    continue
                    
                all_news.extend(news_items)
                logger.info(f"Collecté {len(news_items)} articles de {source_name}")
                
            except Exception as e:
                logger.error(f"Erreur scraping {source_name}: {str(e)}")
        
        # Phase 2: Pré-filtrage basique
        logger.info("Phase 2: Pré-filtrage...")
        filtered_news = self._basic_filter(all_news)
        logger.info(f"{len(filtered_news)} articles retenus après filtrage")
        
        # Phase 3: Analyse avec GPT-4o (analyser plus d'articles pour avoir le choix)
        if self.use_openrouter and self.analyzer and len(filtered_news) > 0:
            logger.info("Phase 3: Analyse avec OpenRouter GPT-4o...")
            # Analyser jusqu'à 12 articles pour avoir une bonne sélection
            enhanced_news = self._analyze_with_openrouter(filtered_news[:12])
        else:
            logger.info("Phase 3: Enrichissement basique (OpenRouter non disponible)")
            enhanced_news = self._basic_enrichment(filtered_news[:num_articles])
        
        # Phase 4: Sélection stratégique des 7 articles
        logger.info("Phase 4: Sélection des 7 articles avec article vedette...")
        final_selection = self._select_strategic_articles(enhanced_news, num_articles)
        
        # Phase 5: Extraction des images
        logger.info("Phase 5: Extraction des images...")
        for item in final_selection:
            if not item.image_url:
                item.image_url = self.extract_image_from_article(item.url)
        
        return final_selection
    
    def _scrape_rss(self, source_name: str, config: Dict, cutoff_date: datetime) -> List[EnhancedNewsItem]:
        """Scraper un flux RSS"""
        news_items = []
        try:
            feed = feedparser.parse(config['url'])
            
            for entry in feed.entries[:20]:
                # Parser la date
                published_date = None
                if hasattr(entry, 'published_parsed'):
                    published_date = datetime(*entry.published_parsed[:6])
                    if published_date < cutoff_date:
                        continue
                
                # Créer l'item
                item = EnhancedNewsItem(
                    title=entry.get('title', 'Sans titre'),
                    url=entry.get('link', ''),
                    source=source_name,
                    published_date=published_date,
                    original_summary=entry.get('summary', '')[:500]
                )
                
                news_items.append(item)
                
        except Exception as e:
            logger.error(f"Erreur RSS {source_name}: {e}")
            
        return news_items
    
    def _scrape_website(self, source_name: str, config: Dict, cutoff_date: datetime) -> List[EnhancedNewsItem]:
        """Scraper un site web (placeholder)"""
        # Implémentation simplifiée
        return []
    
    def _basic_filter(self, news_items: List[EnhancedNewsItem]) -> List[EnhancedNewsItem]:
        """Filtrage basique par mots-clés"""
        keywords = [
            'alimentaire', 'distributeur', 'québec', 'supply chain',
            'restauration', 'grossiste', 'approvisionnement', 'inflation',
            'pénurie', 'local', 'durabilité', 'innovation', 'horeca'
        ]
        
        filtered = []
        for item in news_items:
            text = f"{item.title} {item.original_summary}".lower()
            score = sum(1 for kw in keywords if kw in text)
            
            if score >= 2:  # Au moins 2 mots-clés
                item.relevance_score = min(score / 10, 1.0)
                filtered.append(item)
        
        # Trier par score
        filtered.sort(key=lambda x: x.relevance_score, reverse=True)
        return filtered
    
    def _analyze_with_openrouter(self, news_items: List[EnhancedNewsItem]) -> List[EnhancedNewsItem]:
        """Analyser les articles avec GPT-4o"""
        enhanced = []
        
        for item in news_items:
            logger.info(f"Analyse GPT-4o: {item.title[:50]}...")
            
            # Préparer le contenu pour l'analyse
            content = item.original_summary
            if item.full_text:
                content += " " + item.full_text[:1000]
            
            # Analyser avec GPT-4o
            analysis = self.analyzer.analyze_article(
                title=item.title,
                content=content,
                source=item.source,
                url=item.url
            )
            
            # Enrichir l'item avec l'analyse
            item.title = analysis.title_fr  # Titre amélioré
            item.smart_summary = analysis.smart_summary
            item.flb_relevance = analysis.flb_relevance
            item.business_impact = analysis.business_impact
            item.opportunities = analysis.opportunities
            item.risks = analysis.risks
            item.recommended_actions = analysis.recommended_actions
            item.category = analysis.category
            item.relevance_score = analysis.relevance_score
            item.confidence = analysis.confidence
            
            enhanced.append(item)
        
        # Trier par score et confiance
        enhanced.sort(
            key=lambda x: x.relevance_score * x.confidence,
            reverse=True
        )
        
        return enhanced
    
    def _select_strategic_articles(self, news_items: List[EnhancedNewsItem], num_articles: int = 7) -> List[EnhancedNewsItem]:
        """
        Sélectionner stratégiquement 7 articles:
        - 6 articles variés et pertinents
        - Le 7e (dernière position) = article VEDETTE (le plus important)
        """
        if len(news_items) == 0:
            return []
        
        # Identifier l'article vedette (plus haut score * confiance)
        sorted_items = sorted(news_items, key=lambda x: x.relevance_score * x.confidence, reverse=True)
        featured_article = sorted_items[0] if sorted_items else None
        
        # Sélectionner les autres articles avec diversité
        other_articles = []
        categories_used = set()
        sources_count = {}
        
        for item in sorted_items[1:]:  # Exclure l'article vedette
            # Éviter trop d'articles de la même source
            if sources_count.get(item.source, 0) >= 2:
                continue
            
            # Favoriser la diversité des catégories
            if item.category in categories_used and len(other_articles) >= 3:
                if len([a for a in other_articles if a.category == item.category]) >= 2:
                    continue
            
            other_articles.append(item)
            sources_count[item.source] = sources_count.get(item.source, 0) + 1
            categories_used.add(item.category)
            
            if len(other_articles) >= num_articles - 1:  # 6 articles normaux
                break
        
        # Construire la liste finale: 6 articles normaux + 1 vedette
        final_selection = other_articles[:num_articles-1] if other_articles else []
        
        # Ajouter l'article vedette à la fin (position 7)
        if featured_article:
            final_selection.append(featured_article)
            logger.info(f"🌟 Article vedette sélectionné: {featured_article.title[:50]}... (Score: {featured_article.relevance_score:.0%})")
        
        return final_selection
    
    def _basic_enrichment(self, news_items: List[EnhancedNewsItem]) -> List[EnhancedNewsItem]:
        """Enrichissement basique sans GPT-4o"""
        for item in news_items:
            # Traduire si nécessaire
            item.title = self.translator.translate_if_needed(item.title, item.source)
            item.smart_summary = self.translator.translate_if_needed(
                item.original_summary[:300],
                item.source
            )
            
            # Analyse basique
            item.flb_relevance = "Article pertinent pour le secteur de la distribution alimentaire"
            item.business_impact = "Impact potentiel sur les opérations"
            item.category = "other"
            
        return news_items

def test_enhanced_scraper():
    """Test du scraper amélioré"""
    from config import NEWS_SOURCES
    
    print("🚀 Test du scraper amélioré avec OpenRouter GPT-4o")
    print("="*60)
    
    scraper = EnhancedFoodNewsScraper(NEWS_SOURCES, use_openrouter=True)
    
    print("\n📰 Collecte et analyse des nouvelles...")
    news = scraper.scrape_all_sources(days_back=3)
    
    print(f"\n✅ {len(news)} articles analysés et enrichis")
    
    # Afficher les 6 premiers articles normaux
    print("\n📄 Articles standards:")
    for i, item in enumerate(news[:6], 1):
        print(f"\n{'='*60}")
        print(f"Article {i}: {item.title}")
        print(f"Source: {item.source} | Score: {item.relevance_score:.0%}")
        print(f"\n💡 Résumé intelligent:")
        print(f"   {item.smart_summary}")
        print(f"\n🎯 Pertinence FLB:")
        print(f"   {item.flb_relevance}")
        
        if item.opportunities:
            print(f"\n✅ Opportunités:")
            for opp in item.opportunities[:2]:
                print(f"   - {opp}")
        
        if item.image_url:
            print(f"\n🖼️ Image: {item.image_url[:50]}...")
    
    # Afficher l'article vedette
    if len(news) >= 7:
        print(f"\n{'='*60}")
        print("🌟 ARTICLE VEDETTE (le plus important):")
        featured = news[6]
        print(f"Titre: {featured.title}")
        print(f"Score: {featured.relevance_score:.0%} | Confiance: {featured.confidence:.0%}")
        print(f"\n💡 Résumé intelligent:")
        print(f"   {featured.smart_summary}")
        print(f"\n🎯 Pertinence FLB:")
        print(f"   {featured.flb_relevance}")
        if featured.recommended_actions:
            print(f"\n📝 Actions recommandées:")
            for action in featured.recommended_actions:
                print(f"   • {action}")

if __name__ == "__main__":
    test_enhanced_scraper()