import requests
from bs4 import BeautifulSoup
import feedparser
from newspaper import Article
from datetime import datetime, timedelta
import logging
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import hashlib
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
    is_translated: bool = False  # Flag pour éviter la double traduction
    content_hash: str = ""  # Hash pour déduplication

class FoodIndustryNewsScraper:
    def __init__(self, sources_config: Dict, keywords_config: Dict = None, analysis_config: Dict = None, bulletin_config: Dict = None):
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
        
        # Configuration du bulletin (pour limites d'articles)
        self.bulletin_config = bulletin_config or {'max_articles': 7}
        
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
        start_time = time.time()
        cutoff_date = datetime.now() - timedelta(days=days_back)
        logger.info(f"🚀 DÉBUT SCRAPING - Recherche des {days_back} derniers jours depuis {cutoff_date.strftime('%Y-%m-%d %H:%M')}")
        
        # Phase 1: Paralléliser le scraping des sources
        phase_start = time.time()
        logger.info(f"📡 Phase 1: Scraping de {len(self.sources)} sources en parallèle...")
        all_news = self._parallel_scrape_sources(cutoff_date)
        logger.info(f"✅ Phase 1 terminée en {time.time() - phase_start:.1f}s → {len(all_news)} articles récupérés")
        
        if not all_news:
            logger.warning("❌ Aucun article trouvé, arrêt du processus")
            return []
        
        # Phase 2: Pré-filtrage optimisé en cascade
        phase_start = time.time()
        pre_filtered = self._pre_filter_articles(all_news)
        logger.info(f"✅ Phase 2 terminée en {time.time() - phase_start:.1f}s → {len(pre_filtered)}/{len(all_news)} articles retenus ({100*len(pre_filtered)/len(all_news):.1f}%)")
        
        if not pre_filtered:
            logger.warning("❌ Aucun article pertinent après pré-filtrage")
            return []
        
        # Phase 3: Extraction parallèle du contenu complet pour articles pré-filtrés
        phase_start = time.time()
        logger.info(f"📄 Phase 3: Extraction contenu complet de {len(pre_filtered)} articles...")
        enhanced_news = self._parallel_extract_content(pre_filtered)
        logger.info(f"✅ Phase 3 terminée en {time.time() - phase_start:.1f}s → {len(enhanced_news)} articles avec contenu")
        
        # Phase 3.5: Déduplication après extraction de contenu
        phase_start = time.time()
        logger.info(f"🔄 Phase 3.5: Déduplication de {len(enhanced_news)} articles...")
        deduplicated_news = self._deduplicate_articles(enhanced_news)
        removed = len(enhanced_news) - len(deduplicated_news)
        logger.info(f"✅ Phase 3.5 terminée en {time.time() - phase_start:.1f}s → {removed} doublons supprimés")
        
        # Phase 4: Filtrage final et sélection
        phase_start = time.time()
        logger.info(f"🎯 Phase 4: Sélection finale parmi {len(deduplicated_news)} articles...")
        selected_news = self._filter_relevant_news(deduplicated_news)
        logger.info(f"✅ Phase 4 terminée en {time.time() - phase_start:.1f}s → {len(selected_news)} articles sélectionnés")
        
        # Phase 5: Traduire seulement les nouvelles sélectionnées
        if selected_news:
            phase_start = time.time()
            logger.info(f"🌐 Phase 5: Traduction de {len(selected_news)} articles sélectionnés...")
            self._translate_selected_news(selected_news)
            logger.info(f"✅ Phase 5 terminée en {time.time() - phase_start:.1f}s")
        
        total_time = time.time() - start_time
        logger.info(f"🏁 SCRAPING TERMINÉ en {total_time:.1f}s → {len(selected_news)} articles finaux")
        return selected_news
    
    def _parallel_scrape_sources(self, cutoff_date: datetime) -> List[NewsItem]:
        """Scraper toutes les sources en parallèle"""
        all_news = []
        total_sources = len(self.sources)
        completed_sources = 0
        
        logger.info(f"📡 Lancement du scraping de {total_sources} sources avec 5 workers...")
        
        executor = ThreadPoolExecutor(max_workers=5)
        try:
            future_to_source = {}
            
            # Soumettre tous les jobs
            for source_name, source_config in self.sources.items():
                logger.debug(f"   → Soumission: {source_name} ({source_config['type']})")
                if source_config['type'] == 'rss':
                    future = executor.submit(self._scrape_rss_basic, source_name, source_config, cutoff_date)
                elif source_config['type'] == 'website':
                    future = executor.submit(self._scrape_website_basic, source_name, source_config, cutoff_date)
                else:
                    logger.warning(f"   ⚠️ Type inconnu pour {source_name}: {source_config['type']}")
                    continue
                future_to_source[future] = source_name
            
            # Collecter les résultats avec timeout global de 60s
            try:
                for future in as_completed(future_to_source, timeout=60):
                    source_name = future_to_source[future]
                    completed_sources += 1
                    try:
                        start_time = time.time()
                        news_items = future.result(timeout=30)  # Timeout par source: 30s
                        process_time = time.time() - start_time
                        all_news.extend(news_items)
                        logger.info(f"✅ {source_name}: {len(news_items)} articles en {process_time:.1f}s ({completed_sources}/{total_sources})")
                    except Exception as e:
                        logger.error(f"❌ {source_name}: ERREUR - {str(e)} ({completed_sources}/{total_sources})")
            except Exception as e:
                logger.error(f"⏰ Timeout global atteint lors du scraping des sources: {str(e)}")
                logger.info("🔍 DÉBUT annulation futures...")
                # Annuler les futures restantes - copie pour éviter modification pendant itération
                remaining_sources = []
                logger.info(f"🔍 Dictionnaire futures: {len(future_to_source)} items")
                items_list = list(future_to_source.items())
                logger.info(f"🔍 Liste copiée: {len(items_list)} items")
                for i, (future, source_name) in enumerate(items_list):
                    logger.info(f"🔍 Traitement {i+1}/{len(items_list)}: {source_name}")
                    if not future.done():
                        try:
                            future.cancel()
                            remaining_sources.append(source_name)
                            completed_sources += 1
                            logger.info(f"🔍 Annulé: {source_name}")
                        except Exception as e:
                            logger.warning(f"Erreur cancel {source_name}: {e}")
                    else:
                        logger.info(f"🔍 Déjà terminé: {source_name}")
                logger.info("🔍 FIN boucle annulation")
                if remaining_sources:
                    logger.warning(f"⏰ Sources annulées (timeout): {', '.join(remaining_sources)}")
                logger.info("🔍 Sortie du except timeout")
            
        finally:
            # Force fermeture de tous les threads 
            logger.info("🔍 Fermeture forcée executor...")
            try:
                executor.shutdown(wait=False)  # Ne pas attendre - fermeture forcée
                logger.info("🔍 Executor fermé")
            except Exception as e:
                logger.warning(f"Erreur fermeture executor: {e}")
        
        logger.info("🔍 AVANT try final")
        try:
            logger.info("🔍 DANS try final")
            news_count = len(all_news) if all_news else 0
            logger.info(f"🔍 Debug avant fin: all_news={news_count}, completed_sources={completed_sources}")
            logger.info(f"📊 Scraping terminé: {news_count} articles de {completed_sources} sources")
        except Exception as e:
            logger.error(f"❌ Erreur lors du décompte final: {e}")
            logger.info(f"📊 Scraping terminé: ? articles de {completed_sources} sources")
        logger.info("🔍 AVANT return")
        return all_news
    
    def _pre_filter_articles(self, articles: List[NewsItem]) -> List[NewsItem]:
        """Pré-filtrage optimisé en cascade pour réduire la charge"""
        if not articles:
            return []
        
        logger.info(f"🔍 Phase 2: Filtrage en cascade de {len(articles)} articles...")
        
        # Étape 1: Filtrage rapide par mots-clés critiques
        rapid_filtered = self._rapid_keyword_filter(articles)
        logger.info(f"   → Filtre rapide: {len(rapid_filtered)}/{len(articles)} articles retenus")
        
        # Étape 2: Priorisation par source et fraîcheur
        priority_filtered = self._priority_filter(rapid_filtered)
        logger.info(f"   → Filtre priorité: {len(priority_filtered)}/{len(rapid_filtered)} articles retenus")
        
        # Étape 3: Scoring complet sur un nombre réduit d'articles
        scored_articles = []
        for item in priority_filtered:
            score = self._calculate_unified_score(item, include_full_text=False)
            if score > 0:
                item.relevance_score = score
                scored_articles.append(item)
        
        if not scored_articles:
            logger.warning("Aucun article n'a passé le pré-filtrage complet")
            return []
        
        # Tri par score
        scored_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Sélection finale avec buffer
        max_articles = self.bulletin_config.get('max_articles', 7)
        buffer_size = max(3, len(scored_articles) // 5)  # Buffer adaptatif
        final_count = min(max_articles + buffer_size, len(scored_articles))
        
        selected = scored_articles[:final_count]
        logger.info(f"Pré-filtrage cascade terminé: {len(selected)}/{len(articles)} articles retenus ({(len(selected)/len(articles)*100):.1f}%)")
        
        return selected
    
    def _rapid_keyword_filter(self, articles: List[NewsItem]) -> List[NewsItem]:
        """Filtrage ultra-rapide par mots-clés critiques FLB"""
        critical_keywords = [
            # Priorité 1: Importation et commerce international
            'importation', 'import', 'douane', 'international', 'tarif',
            # Priorité 2: Distribution et concurrence
            'distributeur', 'grossiste', 'distribution', 'wholesale', 'sysco',
            # Priorité 3: Restauration (clientèle principale)
            'restaurant', 'restauration', 'foodservice', 'service alimentaire', 'chef',
            # Priorité 4: Hôtellerie (clientèle importante)
            'hôtel', 'hôtellerie', 'horeca', 'tourisme', 'hébergement',
            # Priorité 5: Proximité géographique (région de Québec)
            'ville de québec', 'quebec city', 'capitale-nationale', 'beauport', 'lévis',
            'sainte-foy', 'charlesbourg', 'ancienne-lorette',
            # Priorité 6: Province de Québec élargie
            'québec', 'quebec', 'montréal', 'montreal', 'sherbrooke', 'gatineau',
            # Mots génériques importants
            'alimentaire', 'food', 'prix', 'coût'
        ]
        
        filtered = []
        for article in articles:
            text = (article.title + " " + article.summary).lower()
            
            # Au moins 1 mot-clé critique requis
            if any(keyword in text for keyword in critical_keywords):
                filtered.append(article)
        
        return filtered
    
    def _priority_filter(self, articles: List[NewsItem]) -> List[NewsItem]:
        """Filtrage par catégorie de source et fraîcheur"""
        # Mapper les sources par catégorie de priorité
        category_priority = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1}
        
        # Enrichir avec score de priorité
        for article in articles:
            source_config = self.sources.get(article.source, {})
            category = source_config.get('category', 'E')
            
            # Score de priorité = catégorie + fraîcheur
            category_score = category_priority.get(category, 1)
            
            # Bonus de fraîcheur (articles récents prioritaires)
            freshness_score = 0
            if article.published_date:
                days_old = (datetime.now() - article.published_date).days
                freshness_score = max(0, 3 - days_old)  # 3 points si aujourd'hui, 0 si > 3 jours
            
            article.priority_score = category_score + freshness_score
        
        # Trier par priorité et prendre le top 30% ou minimum 20 articles
        articles.sort(key=lambda x: getattr(x, 'priority_score', 0), reverse=True)
        
        target_count = max(20, len(articles) // 3)  # Au moins 20 articles ou 30% du total
        return articles[:target_count]
    
    def _parallel_extract_content(self, articles: List[NewsItem]) -> List[NewsItem]:
        """Extraire le contenu complet en parallèle pour articles pré-filtrés avec timeout global"""
        start_time = time.time()
        total_articles = len(articles)
        completed_articles = 0
        successful_extractions = 0
        
        logger.info(f"📄 Extraction parallèle de {total_articles} articles avec 8 workers (timeout: 120s)...")
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_article = {}
            
            # Soumettre tous les jobs d'extraction
            for i, article in enumerate(articles):
                logger.debug(f"   → Soumission extraction {i+1}/{total_articles}: {article.title[:50]}...")
                future = executor.submit(self._extract_and_enhance_article, article)
                future_to_article[future] = article
            
            enhanced = []
            # Timeout global pour éviter blocage indéfini
            timeout_seconds = 120  # 2 minutes maximum pour tous les articles
            
            try:
                for future in as_completed(future_to_article, timeout=timeout_seconds):
                    completed_articles += 1
                    elapsed = time.time() - start_time
                    try:
                        article_start = time.time()
                        enhanced_article = future.result(timeout=10)  # 10s par article max
                        article_time = time.time() - article_start
                        if enhanced_article:
                            enhanced.append(enhanced_article)
                            successful_extractions += 1
                            logger.info(f"✅ Extraction #{completed_articles}/{total_articles}: {enhanced_article.title[:30]}... ({article_time:.1f}s, {elapsed:.1f}s total)")
                    except Exception as e:
                        # Récupérer l'article original pour fallback
                        original_article = future_to_article[future]
                        logger.warning(f"❌ Extraction #{completed_articles}/{total_articles} échouée: {original_article.title[:30]}... - {str(e)}")
                        # Utiliser fallback avec résumé RSS
                        original_article.full_text = original_article.summary or ""
                        original_article.relevance_score = self._calculate_unified_score(original_article, include_full_text=False)
                        enhanced.append(original_article)
                        
            except TimeoutError:
                logger.error(f"Timeout global atteint ({timeout_seconds}s) pour extraction de contenu")
                # Annuler les futures en attente et utiliser fallback
                for future, article in future_to_article.items():
                    if not future.done():
                        future.cancel()
                        # Ajouter avec fallback
                        article.full_text = article.summary or ""
                        article.relevance_score = self._calculate_unified_score(article, include_full_text=False)
                        enhanced.append(article)
                        logger.warning(f"Fallback utilisé pour {article.url} (timeout)")
        
        total_time = time.time() - start_time
        logger.info(f"📊 Extraction terminée en {total_time:.1f}s: {successful_extractions} réussies, {len(enhanced) - successful_extractions} fallbacks sur {total_articles} articles")
        return enhanced
    
    def _extract_and_enhance_article(self, item: NewsItem) -> Optional[NewsItem]:
        """Extraire contenu complet et image pour un article avec fallback robuste"""
        try:
            # Extraire contenu complet
            full_content = self._extract_article_content(item.url)
            if full_content:
                item.full_text = full_content
                # Améliorer le résumé si nécessaire
                if len(item.summary) < 600:
                    item.summary = full_content[:1800]
                logger.debug(f"Contenu extrait avec succès pour {item.url}")
            else:
                # Fallback : garder le résumé RSS existant
                logger.warning(f"Extraction contenu échouée pour {item.url}, conservation résumé RSS")
                item.full_text = item.summary  # Utiliser le résumé comme contenu
            
            # Extraire image si pas déjà présente
            if not item.image_url:
                try:
                    item.image_url = self._extract_image_from_article(item.url)
                except Exception as img_e:
                    logger.debug(f"Extraction image échouée pour {item.url}: {img_e}")
                    # Pas critique, continuer sans image
            
            # Recalculer le score avec le contenu complet maintenant disponible
            item.relevance_score = self._calculate_unified_score(item, include_full_text=True)
            
            return item
            
        except Exception as e:
            logger.error(f"Erreur critique lors de l'amélioration de l'article {item.url}: {str(e)}")
            # Fallback ultime : retourner l'article avec résumé RSS seulement
            item.full_text = item.summary or ""
            item.relevance_score = self._calculate_unified_score(item, include_full_text=False)
            return item
    
    def _translate_selected_news(self, selected_news: List[NewsItem]):
        """Traduire les articles sélectionnés avec protection double traduction"""
        for item in selected_news:
            if not item.is_translated:  # Éviter double traduction
                original_title = item.title
                original_summary = item.summary
                original_relevance = item.relevance_to_flb
                
                item.title = self.translator.translate_if_needed(item.title, item.source)
                item.summary = self.translator.translate_if_needed(item.summary, item.source)
                
                # Traduire aussi l'explication de pertinence si nécessaire
                if item.relevance_to_flb:
                    item.relevance_to_flb = self.translator.translate_if_needed(item.relevance_to_flb, item.source)
                
                # Marquer comme traduit seulement si quelque chose a changé
                if (item.title != original_title or 
                    item.summary != original_summary or 
                    item.relevance_to_flb != original_relevance):
                    item.is_translated = True
                    logger.debug(f"Article traduit: {item.title[:50]}...")
                else:
                    logger.debug(f"Article déjà en français: {item.title[:50]}...")
    
    def _scrape_rss_basic(self, source_name: str, config: Dict, cutoff_date: datetime) -> List[NewsItem]:
        """Scraping RSS basique sans extraction de contenu complet"""
        news_items = []
        try:
            feed = feedparser.parse(config['url'])
            
            for entry in feed.entries[:20]:
                try:
                    published = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                    
                    if published < cutoff_date:
                        continue
                    
                    # Utiliser seulement le résumé RSS pour le pré-filtrage
                    summary = entry.get('summary', '')[:1800]
                    
                    # Extraire l'image depuis le flux RSS seulement
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
                    
                    # Calculer hash pour déduplication
                    content_hash = self._calculate_content_hash(entry.title, entry.link)
                    
                    news_item = NewsItem(
                        title=entry.title,
                        url=entry.link,
                        source=source_name,
                        published_date=published,
                        summary=summary,
                        full_text="",  # Sera rempli plus tard lors de l'extraction parallèle
                        image_url=image_url,
                        content_hash=content_hash
                    )
                    
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"Error processing entry from {source_name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error parsing RSS feed {config['url']}: {str(e)}")
            
        return news_items
    
    def _scrape_website_basic(self, source_name: str, config: Dict, cutoff_date: datetime) -> List[NewsItem]:
        """Scraping website basique sans extraction de contenu complet"""
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
                    
                    # Pas d'extraction de contenu pour le moment, juste le titre
                    summary = ""  # Sera rempli lors de l'extraction parallèle
                    
                    # Calculer hash pour déduplication
                    content_hash = self._calculate_content_hash(title, url)
                    
                    news_item = NewsItem(
                        title=title,
                        url=url,
                        source=source_name,
                        published_date=datetime.now(),
                        summary=summary,
                        full_text="",  # Sera rempli plus tard
                        content_hash=content_hash
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
        """Pipeline unifié de filtrage avec ou sans analyseur avancé"""
        
        # Phase 1: Calcul du score de base pour tous les articles
        scored_items = self._calculate_base_scores(news_items)
        
        # Phase 2: Analyse avancée si disponible
        if self.analyzer:
            logger.info("Using advanced analysis pipeline")
            return self._apply_advanced_analysis(scored_items)
        else:
            logger.info("Using basic scoring pipeline")
            return self._apply_basic_selection(scored_items)
    
    def _calculate_unified_score(self, item: NewsItem, include_full_text: bool = True) -> float:
        """Calcul unifié du score avec analyse contextuelle intelligente"""
        relevant_keywords = []
        
        # Construire le texte à analyser selon le contexte
        if include_full_text:
            text_to_check = (item.title + " " + item.summary + " " + item.full_text).lower()
        else:
            # Pour pré-filtrage : seulement titre et résumé RSS
            text_to_check = (item.title + " " + item.summary).lower()
        
        if not text_to_check.strip():
            return 0.0
        
        # Tokeniser pour analyse contextuelle
        sentences = text_to_check.split('.')
        title_words = item.title.lower().split()
        
        # Score par mots-clés avec analyse contextuelle
        score = 0.0
        for keyword, weight in self.keyword_weights.items():
            keyword_lower = keyword.lower()
            keyword_score = self._calculate_contextual_keyword_score(
                keyword_lower, text_to_check, sentences, title_words, weight
            )
            if keyword_score > 0:
                score += keyword_score
                relevant_keywords.append(keyword)
        
        # Détection de contexte négatif (réduit le score)
        negative_context_penalty = self._detect_negative_context(text_to_check, relevant_keywords)
        score *= (1 - negative_context_penalty)
        
        # Multiplicateur de source
        source_config = self.sources.get(item.source, {})
        priority_multiplier = source_config.get('priority_multiplier', 1.0)
        score *= priority_multiplier
        
        # Bonus géographique avec contexte
        geo_bonus = self._calculate_geographic_relevance(text_to_check)
        score += geo_bonus
        
        # Score de fraîcheur
        if item.published_date:
            days_old = (datetime.now() - item.published_date).days
            freshness_bonus = {0: 1.5, 1: 1.3, 2: 1.2, 3: 1.1, 4: 1.0}.get(days_old, 0.8)
            score *= freshness_bonus
        
        # Mettre à jour les métadonnées de l'item si nécessaire
        if score > 0 and include_full_text:
            item.tags = relevant_keywords
            item.relevance_to_flb = self._generate_relevance_explanation(item, relevant_keywords)
        
        return score
    
    def _calculate_contextual_keyword_score(self, keyword: str, text: str, sentences: List[str], title_words: List[str], base_weight: float) -> float:
        """Calcul du score contextuel pour un mot-clé"""
        if keyword not in text:
            return 0.0
        
        score = 0.0
        
        # Bonus titre (mots-clés dans le titre = plus important)
        if keyword in title_words or any(keyword in word for word in title_words):
            score += base_weight * 1.5
        
        # Comptage avec bonus de proximité
        for sentence in sentences:
            if keyword in sentence:
                # Score de base pour présence
                sentence_score = base_weight
                
                # Bonus si proche d'autres mots-clés importants
                proximity_keywords = ['distributeur', 'québec', 'alimentaire', 'supply chain']
                for prox_kw in proximity_keywords:
                    if prox_kw != keyword and prox_kw in sentence:
                        sentence_score *= 1.2  # 20% de bonus
                
                # Bonus selon la position dans la phrase
                words = sentence.strip().split()
                if words and keyword in ' '.join(words[:5]):  # Dans les 5 premiers mots
                    sentence_score *= 1.1
                
                score += sentence_score
        
        # Diminution logarithmique pour occurrences multiples
        import math
        occurrences = text.count(keyword)
        if occurrences > 1:
            log_bonus = 1 + math.log(occurrences) * 0.3
            score *= log_bonus
        
        return score
    
    def _detect_negative_context(self, text: str, keywords: List[str]) -> float:
        """Détecter le contexte négatif qui réduit la pertinence"""
        negative_indicators = [
            'pas de', 'aucun', 'éviter', 'rejeter', 'interdire', 'bannir',
            'no longer', 'avoid', 'prevent', 'ban', 'prohibit',
            'fermeture', 'closure', 'échec', 'failure'
        ]
        
        penalty = 0.0
        for sentence in text.split('.'):
            # Vérifier si une phrase contient à la fois un mot-clé et un indicateur négatif
            has_keyword = any(kw.lower() in sentence for kw in keywords)
            has_negative = any(neg in sentence for neg in negative_indicators)
            
            if has_keyword and has_negative:
                penalty += 0.1  # 10% de pénalité par contexte négatif
        
        return min(penalty, 0.5)  # Maximum 50% de pénalité
    
    def _calculate_geographic_relevance(self, text: str) -> float:
        """Calcul intelligent de la pertinence géographique"""
        quebec_terms = ['québec', 'quebec', 'capitale-nationale', 'beauport', 'lévis', 'sainte-foy', 'charlesbourg']
        canada_terms = ['canada', 'canadien', 'canadian']
        
        geo_score = 0.0
        
        # Bonus élevé pour mentions spécifiques de Québec
        for term in quebec_terms:
            occurrences = text.count(term)
            if occurrences > 0:
                geo_score += occurrences * 8  # Score élevé pour géo local
        
        # Bonus moyen pour mentions du Canada
        for term in canada_terms:
            occurrences = text.count(term)
            if occurrences > 0:
                geo_score += occurrences * 3
        
        return geo_score
    
    def _calculate_base_scores(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """Wrapper pour compatibilité - utilise le scoring unifié"""
        valid_items = []
        for item in news_items:
            score = self._calculate_unified_score(item, include_full_text=True)
            if score > 0:
                item.relevance_score = score
                valid_items.append(item)
        
        return valid_items
    
    def _apply_basic_selection(self, scored_items: List[NewsItem]) -> List[NewsItem]:
        """Sélection basique avec seuils adaptatifs"""
        if not scored_items:
            return []
        
        # Calculer seuils adaptatifs
        scores = [item.relevance_score for item in scored_items]
        adaptive_threshold = self._calculate_adaptive_threshold(scores)
        logger.info(f"Seuil adaptatif calculé: {adaptive_threshold:.2f}")
        
        # Filtrer par seuil minimal
        qualified_items = [item for item in scored_items if item.relevance_score >= adaptive_threshold]
        logger.info(f"Articles qualifiés (seuil {adaptive_threshold:.2f}): {len(qualified_items)}/{len(scored_items)}")
        
        # Trier par score
        qualified_items.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Si moins de 7 articles qualifiés, élargir progressivement
        max_articles = self.bulletin_config.get('max_articles', 7)
        if len(qualified_items) < max_articles:
            logger.warning(f"Seulement {len(qualified_items)} articles qualifiés, élargissement du seuil...")
            # Prendre au moins les 7 meilleurs (ou tous si moins de 7)
            scored_items.sort(key=lambda x: x.relevance_score, reverse=True)
            qualified_items = scored_items[:max_articles]
        
        # Sélection avec diversité des sources
        max_per_source = self.bulletin_config.get('max_per_source', 2)
        return self._select_with_source_diversity(qualified_items, max_articles=max_articles, max_per_source=max_per_source)
    
    def _calculate_adaptive_threshold(self, scores: List[float]) -> float:
        """Calculer le seuil adaptatif basé sur la distribution des scores"""
        if not scores:
            return 0.0
        
        # Trier les scores
        sorted_scores = sorted(scores, reverse=True)
        
        # Calculer le percentile 60 comme seuil de base
        import math
        percentile_60_index = max(0, int(len(sorted_scores) * 0.4) - 1)
        percentile_60 = sorted_scores[percentile_60_index] if sorted_scores else 0.0
        
        # Seuil minimum optimal pour FLB (équilibre qualité/quantité)
        min_threshold = 0.25  # Ajusté pour atteindre 7 articles pertinents
        
        # Seuil dynamique basé sur la médiane si scores très variables
        if len(sorted_scores) >= 5:
            median_score = sorted_scores[len(sorted_scores) // 2]
            dynamic_threshold = max(median_score * 0.8, percentile_60)
        else:
            dynamic_threshold = percentile_60
        
        # Retourner le maximum entre seuil minimum et seuil dynamique
        final_threshold = max(min_threshold, dynamic_threshold)
        
        logger.debug(f"Calcul seuils: P60={percentile_60:.2f}, Min={min_threshold:.2f}, Dynamic={dynamic_threshold:.2f}, Final={final_threshold:.2f}")
        return final_threshold
    
    def _apply_advanced_analysis(self, scored_items: List[NewsItem]) -> List[NewsItem]:
        """Pipeline d'analyse avancée avec le moteur hybride"""
        logger.info(f"Using advanced analysis for {len(scored_items)} pre-scored articles")
        
        # Préparer pour l'analyse avancée
        articles_dict = []
        for item in scored_items:
            articles_dict.append({
                'title': item.title,
                'summary': item.summary,
                'full_text': item.full_text,
                'source': item.source,
                'url': item.url,
                'published_date': item.published_date,
                'base_score': item.relevance_score  # Conserver le score de base
            })
        
        # Analyse avec le moteur hybride
        analysis_results = self.analyzer.analyze_batch(articles_dict)
        
        # Enrichir les NewsItems
        enhanced_items = []
        for article_dict, analysis in analysis_results:
            # Retrouver l'item original
            for item in scored_items:
                if item.url == article_dict['url']:
                    # Normaliser base_score vers 0-1 pour cohérence avec analysis.relevance_score
                    max_base_score = max((a.get('base_score', 0) for a in articles_dict), default=1)
                    normalized_base_score = article_dict['base_score'] / max(max_base_score, 1)
                    
                    # Combiner scores normalisés: 60% analyse LLM + 40% score traditionnel
                    combined_score = (analysis.relevance_score * 0.6) + (normalized_base_score * 0.4)
                    item.relevance_score = combined_score
                    
                    logger.info(f"Score combiné pour {item.title[:30]}: LLM={analysis.relevance_score:.3f} + Base={normalized_base_score:.3f} = {combined_score:.3f}")
                    item.tags = [analysis.category] if analysis.category else item.tags
                    
                    # Utiliser notre analyse FLB personnalisée au lieu de celle générique
                    if hasattr(item, 'tags') and item.tags:
                        item.relevance_to_flb = self._generate_relevance_explanation(item, item.tags)
                    else:
                        # Fallback si pas de tags disponibles
                        if analysis.strategic_insights and analysis.business_impact != "Analyse basique - Impact à évaluer":
                            item.relevance_to_flb = f"{analysis.business_impact} {analysis.strategic_insights}"
                        else:
                            # Générer analyse basée sur le titre et résumé
                            keywords_found = [kw for kw, weight in self.keyword_weights.items() 
                                            if kw.lower() in (item.title + " " + item.summary).lower()]
                            item.relevance_to_flb = self._generate_relevance_explanation(item, keywords_found)
                    
                    # Métadonnées additionnelles
                    if hasattr(item, '__dict__'):
                        item.__dict__.update({
                            'recommended_actions': analysis.recommended_actions,
                            'confidence_level': analysis.confidence_level,
                            'analysis_method': analysis.analysis_method
                        })
                    
                    enhanced_items.append(item)
                    break
        
        # Trier par score combiné et confiance
        enhanced_items.sort(
            key=lambda x: x.relevance_score * getattr(x, 'confidence_level', 1),
            reverse=True
        )
        
        max_articles = self.bulletin_config.get('max_articles', 7)
        max_per_source = self.bulletin_config.get('max_per_source', 2)
        return self._select_with_source_diversity(enhanced_items, max_articles=max_articles, max_per_source=max_per_source)
    
    def _select_with_source_diversity(self, items: List[NewsItem], max_articles: int, max_per_source: int) -> List[NewsItem]:
        """Sélection stratégique avec article vedette et diversité"""
        if not items:
            return []
        
        # Identifier l'article vedette (plus haut score × facteur confiance)
        featured_candidate = self._identify_featured_article(items)
        logger.info(f"🌟 Article vedette identifié: {featured_candidate.title[:50]}... (Score: {featured_candidate.relevance_score:.2f})")
        
        # Sélectionner les autres articles avec diversité
        regular_articles = self._select_diverse_articles(items, featured_candidate, max_articles - 1, max_per_source)
        
        # Construire la sélection finale : articles normaux + vedette
        final_selection = regular_articles + [featured_candidate]
        
        # Métriques de qualité
        self._log_selection_metrics(final_selection, items)
        
        return final_selection
    
    def _identify_featured_article(self, items: List[NewsItem]) -> NewsItem:
        """Identifier l'article vedette avec critères multiples"""
        if not items:
            return items[0] if items else None
        
        # Calculer score composé pour chaque article
        for item in items:
            # Score de base
            base_score = item.relevance_score
            
            # Facteur de source (catégorie A = premium)
            source_config = self.sources.get(item.source, {})
            source_factor = 1.0
            if source_config.get('category') == 'A':
                source_factor = 1.3
            elif source_config.get('category') == 'B':
                source_factor = 1.2
            
            # Facteur d'impact (mots-clés à fort impact)
            impact_keywords = ['distributeur', 'grossiste', 'supply chain', 'pénurie', 'inflation majeure']
            text = (item.title + " " + item.summary).lower()
            impact_factor = 1.0
            for keyword in impact_keywords:
                if keyword in text:
                    impact_factor = min(impact_factor + 0.2, 1.8)
            
            # Facteur géographique (local = plus vedette)
            geo_factor = 1.1 if any(term in text for term in ['québec', 'capitale-nationale']) else 1.0
            
            # Score vedette composé
            item.featured_score = base_score * source_factor * impact_factor * geo_factor
        
        # Retourner l'article avec le plus haut score vedette
        return max(items, key=lambda x: getattr(x, 'featured_score', x.relevance_score))
    
    def _select_diverse_articles(self, items: List[NewsItem], featured_article: NewsItem, target_count: int, max_per_source: int) -> List[NewsItem]:
        """Sélectionner des articles diversifiés (excluant l'article vedette)"""
        candidates = [item for item in items if item != featured_article]
        candidates.sort(key=lambda x: x.relevance_score, reverse=True)
        
        selected = []
        source_count = {featured_article.source: 1}  # Compter la source de l'article vedette
        category_count = {}
        
        # Obtenir la catégorie de l'article vedette
        featured_category = self.sources.get(featured_article.source, {}).get('category', 'E')
        category_count[featured_category] = 1
        
        for item in candidates:
            if len(selected) >= target_count:
                break
            
            source = item.source
            item_category = self.sources.get(source, {}).get('category', 'E')
            
            # Vérifier les contraintes de diversité
            source_ok = source_count.get(source, 0) < max_per_source
            category_ok = category_count.get(item_category, 0) < 4  # Max 4 par catégorie pour plus de flexibilité
            
            if source_ok and category_ok:
                selected.append(item)
                source_count[source] = source_count.get(source, 0) + 1
                category_count[item_category] = category_count.get(item_category, 0) + 1
                logger.info(f"Selected: {item.title[:50]}... (Score: {item.relevance_score:.2f}, Cat: {item_category})")
        
        return selected
    
    def _log_selection_metrics(self, final_selection: List[NewsItem], all_candidates: List[NewsItem]):
        """Logger les métriques de qualité de la sélection"""
        if not final_selection:
            return
        
        # Diversité des sources
        sources = [item.source for item in final_selection]
        unique_sources = len(set(sources))
        
        # Diversité des catégories
        categories = [self.sources.get(item.source, {}).get('category', 'E') for item in final_selection]
        unique_categories = len(set(categories))
        
        # Distribution des scores
        scores = [item.relevance_score for item in final_selection]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        # Taux de sélection par catégorie
        category_stats = {}
        for cat in ['A', 'B', 'C', 'D', 'E']:
            selected_in_cat = sum(1 for c in categories if c == cat)
            total_in_cat = sum(1 for item in all_candidates 
                             if self.sources.get(item.source, {}).get('category', 'E') == cat)
            if total_in_cat > 0:
                category_stats[cat] = f"{selected_in_cat}/{total_in_cat}"
        
        logger.info(f"📊 Métriques sélection: {unique_sources} sources, {unique_categories} catégories")
        logger.info(f"📈 Scores: avg={avg_score:.2f}, min={min_score:.2f}, max={max_score:.2f}")
        logger.info(f"📋 Par catégorie: {category_stats}")
    
    def _calculate_content_hash(self, title: str, url: str) -> str:
        """Calculer hash pour déduplication basé sur titre et URL"""
        # Normaliser le titre pour déduplication (enlever ponctuation, espaces multiples)
        normalized_title = ' '.join(title.lower().split())
        # Utiliser titre + domaine (pas URL complète car peut avoir paramètres)
        from urllib.parse import urlparse
        try:
            domain = urlparse(url).netloc
        except:
            domain = url
        
        content_key = f"{normalized_title}|{domain}"
        return hashlib.md5(content_key.encode('utf-8')).hexdigest()[:12]  # 12 chars suffisent
    
    def _deduplicate_articles(self, articles: List[NewsItem]) -> List[NewsItem]:
        """Supprimer articles dupliqués basé sur hash de contenu"""
        seen_hashes = set()
        deduplicated = []
        duplicates_removed = 0
        
        for article in articles:
            if not article.content_hash:
                # Recalculer si manquant
                article.content_hash = self._calculate_content_hash(article.title, article.url)
            
            if article.content_hash not in seen_hashes:
                seen_hashes.add(article.content_hash)
                deduplicated.append(article)
            else:
                duplicates_removed += 1
                logger.debug(f"Article dupliqué supprimé: {article.title[:50]}... (hash: {article.content_hash})")
        
        logger.info(f"Déduplication: {duplicates_removed} doublons supprimés, {len(deduplicated)} articles uniques")
        return deduplicated
    
    # Cette méthode est maintenant remplacée par le pipeline unifié _filter_relevant_news()
    # Conservée temporairement pour compatibilité
    
    def _generate_relevance_explanation(self, item: NewsItem, keywords: List[str]) -> str:
        """Génère une analyse de pertinence intelligente pour FLB basée sur le contenu réel"""
        
        # Analyser le contenu complet (titre + résumé + contenu) 
        full_text = f"{item.title} {item.summary} {item.full_text}".lower()
        title_lower = item.title.lower()
        
        # Détection prioritaire selon les intérêts stratégiques de FLB
        
        # 1. IMPORTATION - Priorité critique pour FLB
        if any(term in full_text for term in [
            'importation', 'import', 'douane', 'frontière', 'international', 'étranger', 
            'tarif douanier', 'commerce international', 'accord commercial', 'quotas'
        ]):
            return "Impact critique sur nos activités d'importation. Cette évolution pourrait affecter nos coûts, délais ou procédures d'importation de produits alimentaires internationaux."
        
        # 2. DISTRIBUTION/CONCURRENCE - Surveillance concurrentielle
        elif any(term in full_text for term in [
            'distributeur', 'grossiste', 'distribution', 'wholesale', 'sysco', 'gordon food',
            'approvisionnement', 'supply chain', 'chaîne', 'concurrence', 'concurrent'
        ]):
            return "Mouvement concurrentiel dans la distribution alimentaire. Analyse nécessaire de l'impact sur notre positionnement marché et opportunités stratégiques à saisir."
        
        # 3. RESTAURATION - Cœur de clientèle FLB  
        elif any(term in full_text for term in [
            'restaurant', 'restauration', 'chef', 'menu', 'service alimentaire', 'foodservice',
            'restaurateur', 'cuisine', 'repas', 'McDo', 'Tim Hortons', 'chaîne resto'
        ]):
            return "Évolution dans notre secteur client prioritaire (restauration). Impact direct sur la demande de nos services et opportunité d'adaptation de notre offre produits."
        
        # 4. HÔTELLERIE - Segment client important
        elif any(term in full_text for term in [
            'hôtel', 'hôtellerie', 'horeca', 'hébergement', 'tourisme', 'hospitalité',
            'hôtelier', 'réception', 'vacances', 'voyage'
        ]):
            return "Développement du secteur hôtelier, client stratégique de FLB. Évaluation des impacts sur nos volumes de vente et ajustements possibles de nos gammes produits."
        
        # 5. PROXIMITÉ GÉOGRAPHIQUE - Priorité élevée pour FLB
        elif any(term in full_text for term in [
            'ville de québec', 'quebec city', 'capitale-nationale', 'beauport', 'lévis', 
            'sainte-foy', 'charlesbourg', 'ancienne-lorette', 'saint-augustin'
        ]):
            return "Développement dans notre zone géographique immédiate (région de Québec). Impact direct sur nos opérations locales et opportunités commerciales de proximité à saisir."
        
        # 6. PROVINCE DE QUÉBEC - Marché élargi stratégique
        elif any(term in full_text for term in [
            'québec', 'quebec', 'montréal', 'montreal', 'sherbrooke', 'gatineau', 'trois-rivières',
            'saguenay', 'chicoutimi', 'rimouski', 'drummondville', 'granby', 'saint-jean'
        ]):
            return "Évolution dans notre marché provincial stratégique. Opportunité d'expansion géographique ou d'adaptation de nos services aux réalités québécoises."
        
        # 6. Économie/Prix/Inflation (impact coûts)
        elif any(term in full_text for term in [
            'prix', 'inflation', 'coût', 'pénurie', 'shortage', 'économique', 'financier', 'tarif'
        ]):
            return "Pression économique sur nos coûts d'exploitation. Révision possible de nos marges et stratégies de négociation avec fournisseurs et clients."
        
        # 6. Innovation/Tendances
        elif any(term in full_text for term in [
            'innovation', 'nouveau', 'nouvelle', 'technologie', 'digital', 'tendance', 'trend'
        ]):
            return "Innovation du secteur alimentaire à surveiller. Évaluation nécessaire de l'impact sur notre offre et opportunités de modernisation de nos services."
        
        # 7. Durabilité/Environnement  
        elif any(term in full_text for term in [
            'durable', 'sustainability', 'environnement', 'écologique', 'bio', 'local', 'responsable'
        ]):
            return "Enjeu de développement durable croissant. Alignement nécessaire avec nos engagements RSE et évolution des attentes de nos clients et partenaires."
        
        # 8. Réglementation/Gouvernement
        elif any(term in full_text for term in [
            'gouvernement', 'ministre', 'règlement', 'loi', 'norme', 'inspection', 'salubrité'
        ]):
            return "Évolution réglementaire du secteur alimentaire. Veille nécessaire pour assurer la conformité de nos opérations et anticiper les adaptations requises."
        
        # 9. Agriculture (matières premières)
        elif any(term in full_text for term in [
            'agricole', 'ferme', 'producteur', 'récolte', 'culture', 'élevage', 'production'
        ]):
            return "Développement chez nos fournisseurs agricoles. Impact potentiel sur la disponibilité, qualité et prix de nos approvisionnements en matières premières."
        
        # 10. Analyse contextuelle du titre pour cas spéciaux
        elif any(term in title_lower for term in ['fermeture', 'faillite', 'cessation']):
            return "Restructuration du marché alimentaire. Opportunité commerciale potentielle de récupérer clientèle ou d'ajuster notre positionnement concurrentiel."
        
        elif any(term in title_lower for term in ['ouverture', 'lancement', 'expansion']):
            return "Nouvelle concurrence ou partenaire potentiel. Évaluation de l'impact sur notre écosystème commercial et identification d'opportunités de collaboration."
        
        elif any(term in title_lower for term in ['acquisition', 'fusion', 'rachat']):
            return "Consolidation du marché alimentaire. Analyse de l'impact sur nos relations commerciales et identification de nouveaux interlocuteurs stratégiques."
        
        # Fallback intelligent basé sur la source
        else:
            source_config = getattr(self, 'sources', {}).get(item.source, {})
            category = source_config.get('category', 'E')
            
            if category == 'A':
                return "Article d'une source commerciale de référence. Information stratégique pour notre positionnement dans l'industrie alimentaire."
            elif category == 'B':
                return "Développement du secteur agricole québécois. Impact potentiel sur nos approvisionnements et relations avec les producteurs locaux."
            else:
                return "Actualité du marché alimentaire canadien. Veille concurrentielle et identification d'opportunités sectorielles pour FLB Solutions."