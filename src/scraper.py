import requests
from bs4 import BeautifulSoup
import feedparser
from newspaper import Article
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from src.translator import NewsTranslator

# Import du nouvel analyseur hybride
try:
    from src.analyzer_engine import HybridAnalysisEngine, AnalysisResult
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    logger.warning("Advanced analyzer not available. Using basic scoring.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    published_date: Optional[datetime]
    summary: str
    full_text: str = ""
    relevance_to_flb: str = ""
    tags: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    image_url: str = ""

class FoodIndustryNewsScraper:
    def __init__(self, sources_config: Dict, keywords_config: Dict = None, analysis_config: Dict = None):
        self.sources = sources_config
        self.translator = NewsTranslator()
        # Utiliser les mots-clés de config.py si fournis
        if keywords_config:
            self.keyword_weights = keywords_config
        else:
            # Fallback sur l'ancienne liste
            self.keyword_weights = {
                'distributeur alimentaire': 10, 'grossiste alimentaire': 10,
                'québec': 8, 'supply chain': 6, 'chaîne d\'approvisionnement': 6,
                'food distribution': 10, 'food wholesale': 10, 'alimentation': 2,
                'épicerie': 7, 'restauration': 8, 'hôtellerie': 8, 'HORECA': 9,
                'tendances alimentaires': 4, 'food trends': 4, 'durabilité': 4,
                'sustainability': 4, 'local': 5, 'régional': 5, 'innovation': 4
            }
        
        # Initialiser l'analyseur avancé si disponible
        self.analyzer = None
        if ANALYZER_AVAILABLE and analysis_config:
            try:
                # Ajouter les mots-clés à la config de l'analyseur
                if 'keywords' not in analysis_config:
                    analysis_config['keywords'] = self.keyword_weights
                self.analyzer = HybridAnalysisEngine(analysis_config)
                logger.info("Advanced analyzer initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize advanced analyzer: {e}")
        
    def scrape_all_sources(self, days_back: int = 7) -> List[NewsItem]:
        all_news = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for source_name, source_config in self.sources.items():
            try:
                if source_config['type'] == 'rss':
                    news_items = self._scrape_rss(source_name, source_config, cutoff_date)
                elif source_config['type'] == 'website':
                    news_items = self._scrape_website(source_name, source_config, cutoff_date)
                else:
                    continue
                    
                all_news.extend(news_items)
                logger.info(f"Scraped {len(news_items)} items from {source_name}")
                
            except Exception as e:
                logger.error(f"Error scraping {source_name}: {str(e)}")
        
        # Filtrer et sélectionner les 5 meilleures nouvelles
        selected_news = self._filter_relevant_news(all_news)
        
        # Traduire seulement les nouvelles sélectionnées
        for item in selected_news:
            item.title = self.translator.translate_if_needed(item.title, item.source)
            item.summary = self.translator.translate_if_needed(item.summary, item.source)
            # Ne pas traduire le texte complet pour économiser les caractères
            # item.full_text = self.translator.translate_if_needed(item.full_text, item.source)
        
        return selected_news
    
    def _scrape_rss(self, source_name: str, config: Dict, cutoff_date: datetime) -> List[NewsItem]:
        news_items = []
        try:
            feed = feedparser.parse(config['url'])
            
            for entry in feed.entries[:20]:
                try:
                    published = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                    
                    if published < cutoff_date:
                        continue
                    
                    article_text = self._extract_article_content(entry.link)
                    
                    # Ne pas traduire immédiatement - attendre la sélection finale
                    # Créer un résumé substantiel (100-300 mots = environ 600-1800 caractères)
                    raw_summary = entry.get('summary', '')
                    if len(raw_summary) < 600 and article_text:
                        # Si le résumé RSS est trop court, utiliser le début de l'article complet
                        summary = article_text[:1800]
                    else:
                        summary = raw_summary[:1800]
                    
                    # Extraire l'image depuis le flux RSS
                    image_url = ""
                    # Chercher dans les enclosures
                    if hasattr(entry, 'enclosures') and entry.enclosures:
                        for enclosure in entry.enclosures:
                            if 'image' in enclosure.get('type', ''):
                                image_url = enclosure.get('href', '')
                                break
                    # Chercher dans media:content ou media:thumbnail
                    if not image_url:
                        if hasattr(entry, 'media_content') and entry.media_content:
                            image_url = entry.media_content[0].get('url', '')
                        elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                            image_url = entry.media_thumbnail[0].get('url', '')
                    # Si toujours pas d'image, on essaiera plus tard avec l'article
                    if not image_url:
                        image_url = self._extract_image_from_article(entry.link)
                    
                    news_item = NewsItem(
                        title=entry.title,
                        url=entry.link,
                        source=source_name,
                        published_date=published,
                        summary=summary,
                        full_text=article_text,
                        image_url=image_url
                    )
                    
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"Error processing entry from {source_name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error parsing RSS feed {config['url']}: {str(e)}")
            
        return news_items
    
    def _scrape_website(self, source_name: str, config: Dict, cutoff_date: datetime) -> List[NewsItem]:
        news_items = []
        try:
            response = requests.get(config['url'], timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            
            articles = soup.select(config.get('article_selector', 'article'))[:20]
            
            for article in articles:
                try:
                    title_elem = article.select_one(config.get('title_selector', 'h2'))
                    link_elem = article.select_one('a[href]')
                    
                    if not title_elem or not link_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url = link_elem['href']
                    
                    if not url.startswith('http'):
                        url = config.get('base_url', config['url']) + url
                    
                    article_text = self._extract_article_content(url)
                    
                    # Créer un résumé substantiel (100-300 mots = environ 600-1800 caractères)
                    summary = article_text[:1800] if article_text else ""
                    
                    # Ne pas traduire immédiatement - attendre la sélection finale
                    news_item = NewsItem(
                        title=title,
                        url=url,
                        source=source_name,
                        published_date=datetime.now(),
                        summary=summary,
                        full_text=article_text
                    )
                    
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"Error processing article from {source_name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error scraping website {config['url']}: {str(e)}")
            
        return news_items
    
    def _extract_article_content(self, url: str) -> str:
        try:
            article = Article(url)
            article.download()
            article.parse()
            return article.text
        except:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'lxml')
                
                for script in soup(["script", "style"]):
                    script.decompose()
                    
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return text[:5000]  # Augmenter pour avoir plus de contenu
            except:
                return ""
    
    def _extract_image_from_article(self, url: str) -> str:
        """Extraire l'image principale d'un article"""
        try:
            # D'abord essayer avec newspaper3k
            article = Article(url)
            article.download()
            article.parse()
            if article.top_image:
                return article.top_image
        except:
            pass
        
        # Si \u00e7a ne marche pas, essayer avec BeautifulSoup
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Chercher Open Graph image
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                return og_image['content']
            
            # Chercher Twitter Card image
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                return twitter_image['content']
            
            # Chercher la premi\u00e8re grande image
            img = soup.find('img', src=True)
            if img:
                img_url = img['src']
                # Convertir en URL absolue si n\u00e9cessaire
                if not img_url.startswith('http'):
                    from urllib.parse import urljoin
                    img_url = urljoin(url, img_url)
                return img_url
        except:
            pass
        
        return ""
    
    def _filter_relevant_news(self, news_items: List[NewsItem]) -> List[NewsItem]:
        # Si l'analyseur avancé est disponible, l'utiliser
        if self.analyzer:
            return self._advanced_filter(news_items)
        
        # Sinon, utiliser l'ancienne méthode
        relevant_news = []
        source_count = {}  # Pour limiter à 2 nouvelles par source
        
        for item in news_items:
            score = 0
            relevant_keywords = []
            
            text_to_check = (item.title + " " + item.summary + " " + item.full_text).lower()
            
            # Calculer le score pondéré
            for keyword, weight in self.keyword_weights.items():
                if keyword.lower() in text_to_check:
                    score += weight
                    relevant_keywords.append(keyword)
            
            # Appliquer le multiplicateur de priorité de la source
            source_config = self.sources.get(item.source, {})
            priority_multiplier = source_config.get('priority_multiplier', 1.0)
            score *= priority_multiplier
            
            # Bonus de proximité géographique
            quebec_mentions = text_to_check.count('québec') + text_to_check.count('quebec')
            score += quebec_mentions * 5
            
            # Score de fraîcheur (nouvelles récentes valent plus)
            if item.published_date:
                days_old = (datetime.now() - item.published_date).days
                if days_old == 0:
                    score *= 1.5
                elif days_old <= 2:
                    score *= 1.2
                elif days_old <= 4:
                    score *= 1.0
                else:
                    score *= 0.8
            
            if score > 0:
                item.relevance_score = score
                item.tags = relevant_keywords
                item.relevance_to_flb = self._generate_relevance_explanation(item, relevant_keywords)
                relevant_news.append(item)
        
        # Trier par score de pertinence
        relevant_news.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limiter à 2 nouvelles maximum par source et 5 au total
        final_selection = []
        for item in relevant_news:
            if item.source not in source_count:
                source_count[item.source] = 0
            if source_count[item.source] < 2 and len(final_selection) < 5:
                source_count[item.source] += 1
                final_selection.append(item)
        
        return final_selection
    
    def _advanced_filter(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Filtrage avancé avec le moteur d'analyse hybride"""
        logger.info(f"Using advanced analysis for {len(news_items)} articles")
        
        # Préparer les articles pour l'analyse
        articles_dict = []
        for item in news_items:
            articles_dict.append({
                'title': item.title,
                'summary': item.summary,
                'full_text': item.full_text,
                'source': item.source,
                'url': item.url,
                'published_date': item.published_date
            })
        
        # Analyser avec le moteur hybride
        analysis_results = self.analyzer.analyze_batch(articles_dict)
        
        # Enrichir les NewsItems avec les résultats d'analyse
        enhanced_items = []
        for i, (article_dict, analysis) in enumerate(analysis_results):
            # Retrouver le NewsItem original
            for item in news_items:
                if item.url == article_dict['url']:
                    # Enrichir avec l'analyse
                    item.relevance_score = analysis.relevance_score * 100
                    item.tags = [analysis.category] if analysis.category else []
                    
                    # Créer une explication enrichie
                    if analysis.strategic_insights:
                        item.relevance_to_flb = f"{analysis.business_impact} | {analysis.strategic_insights}"
                    else:
                        item.relevance_to_flb = analysis.business_impact
                    
                    # Ajouter les actions recommandées comme métadonnées
                    if hasattr(item, '__dict__'):
                        item.__dict__['recommended_actions'] = analysis.recommended_actions
                        item.__dict__['confidence_level'] = analysis.confidence_level
                        item.__dict__['analysis_method'] = analysis.analysis_method
                    
                    enhanced_items.append(item)
                    break
        
        # Trier par score de pertinence et confidence
        enhanced_items.sort(
            key=lambda x: (x.relevance_score * getattr(x, 'confidence_level', 1)),
            reverse=True
        )
        
        # Sélection finale avec diversité des sources
        final_selection = []
        source_count = {}
        
        for item in enhanced_items[:20]:  # Considérer les top 20
            if item.source not in source_count:
                source_count[item.source] = 0
            if source_count[item.source] < 2 and len(final_selection) < 5:
                source_count[item.source] += 1
                final_selection.append(item)
                logger.info(f"Selected: {item.title[:50]}... (Score: {item.relevance_score:.1f})")
        
        # IMPORTANT: Traduire les articles sélectionnés des sources anglaises
        logger.info("Translating selected articles from English sources...")
        for item in final_selection:
            item.title = self.translator.translate_if_needed(item.title, item.source)
            item.summary = self.translator.translate_if_needed(item.summary, item.source)
            # Traduire aussi l'explication de pertinence si nécessaire
            if hasattr(item, 'relevance_to_flb'):
                item.relevance_to_flb = self.translator.translate_if_needed(item.relevance_to_flb, item.source)
        
        return final_selection
    
    def _generate_relevance_explanation(self, item: NewsItem, keywords: List[str]) -> str:
        explanation = "Cette nouvelle est pertinente pour FLB car elle concerne "
        
        if any(k in ['distributeur alimentaire', 'grossiste alimentaire', 'food distribution', 'food wholesale'] for k in keywords):
            explanation += "directement notre secteur de distribution alimentaire en gros"
        elif any(k in ['québec', 'local', 'régional'] for k in keywords):
            explanation += "notre marché local dans la région de Québec et de la Capitale-Nationale"
        elif any(k in ['supply chain', 'chaîne d\'approvisionnement'] for k in keywords):
            explanation += "la chaîne d'approvisionnement qui influence directement nos opérations"
        elif any(k in ['restauration', 'hôtellerie', 'HORECA', 'épicerie'] for k in keywords):
            explanation += "notre clientèle dans les secteurs de la restauration, de l'hôtellerie et du commerce de détail"
        elif any(k in ['tendances alimentaires', 'food trends', 'innovation'] for k in keywords):
            explanation += "les tendances émergentes et les innovations qui transforment notre industrie"
        elif any(k in ['durabilité', 'sustainability'] for k in keywords):
            explanation += "les enjeux de développement durable, prioritaires pour notre entreprise et nos partenaires"
        else:
            explanation += "des développements importants pour l'industrie alimentaire québécoise"
        
        return explanation + "."