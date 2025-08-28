#!/usr/bin/env python3
"""
Moteur d'analyse avancée pour FLB News
Architecture hybride: BM25 + LLM (Ollama/OpenRouter)
"""

import logging
import json
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

# Imports conditionnels pour supporter différents modes
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logging.warning("rank-bm25 not installed. BM25 scoring will be disabled.")

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Ollama not installed. Local LLM analysis will be disabled.")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not installed. Cloud enrichment will be disabled.")

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Résultat d'analyse d'un article"""
    relevance_score: float = 0.0
    category: str = ""
    business_impact: str = ""
    strategic_insights: str = ""
    recommended_actions: List[str] = field(default_factory=list)
    analysis_method: str = "basic"  # basic, bm25, ollama, openrouter
    processing_time: float = 0.0
    confidence_level: float = 0.0

class BM25Analyzer:
    """Analyseur rapide basé sur BM25 pour pré-filtrage"""
    
    def __init__(self, keywords_config: Dict[str, int]):
        self.keywords = keywords_config
        self.bm25_index = None
        self.documents = []
        
        if not BM25_AVAILABLE:
            logger.warning("BM25 not available, falling back to keyword scoring")
    
    def build_index(self, documents: List[str]):
        """Construire l'index BM25 à partir des documents"""
        if not BM25_AVAILABLE:
            return
            
        # Tokenisation simple (peut être amélioré avec NLTK/spaCy)
        tokenized_docs = [doc.lower().split() for doc in documents]
        self.bm25_index = BM25Okapi(tokenized_docs)
        self.documents = documents
        logger.info(f"BM25 index built with {len(documents)} documents")
    
    def score_document(self, document: str, query_context: str = None) -> float:
        """Calculer le score de pertinence d'un document"""
        
        # Si pas de BM25, utiliser le scoring par mots-clés
        if not BM25_AVAILABLE or self.bm25_index is None:
            return self._keyword_score(document)
        
        # Construire la requête à partir du contexte FLB
        if query_context is None:
            query_context = self._build_flb_query()
        
        query_tokens = query_context.lower().split()
        scores = self.bm25_index.get_scores(query_tokens)
        
        # Trouver l'index du document
        try:
            doc_index = self.documents.index(document)
            bm25_score = scores[doc_index]
        except (ValueError, IndexError):
            bm25_score = 0
        
        # Combiner avec le score de mots-clés pour un résultat hybride
        keyword_score = self._keyword_score(document)
        
        # Pondération: 70% BM25, 30% mots-clés
        return (bm25_score * 0.7) + (keyword_score * 0.3)
    
    def _keyword_score(self, document: str) -> float:
        """Scoring basique par mots-clés (fallback)"""
        doc_lower = document.lower()
        score = 0.0
        
        for keyword, weight in self.keywords.items():
            if keyword.lower() in doc_lower:
                # Compter les occurrences avec diminution logarithmique
                count = doc_lower.count(keyword.lower())
                score += weight * (1 + (count - 1) * 0.3)
        
        # Normaliser le score
        return min(score / 100, 1.0)
    
    def _build_flb_query(self) -> str:
        """Construire une requête représentant les intérêts de FLB"""
        return """
        distributeur alimentaire grossiste québec capitale-nationale
        supply chain approvisionnement logistique livraison
        restauration hôtellerie HORECA épicerie détaillant
        produits frais viande volaille produits laitiers surgelés
        tendances alimentaires innovation durabilité local
        """

class OllamaAnalyzer:
    """Analyseur basé sur LLM local via Ollama"""
    
    def __init__(self, model_name: str = "phi2", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.client = None
        
        if OLLAMA_AVAILABLE:
            try:
                self.client = ollama.Client(host=base_url)
                # Vérifier si le modèle est disponible
                models = self.client.list()
                if not any(model_name in m['name'] for m in models.get('models', [])):
                    logger.warning(f"Model {model_name} not found in Ollama. Please pull it first.")
                    self.client = None
            except Exception as e:
                logger.warning(f"Cannot connect to Ollama: {e}")
                self.client = None
    
    def analyze_article(self, title: str, summary: str, source: str) -> AnalysisResult:
        """Analyser un article avec le LLM local"""
        
        if not OLLAMA_AVAILABLE or self.client is None:
            return AnalysisResult(analysis_method="fallback")
        
        prompt = f"""
        Analyser cet article pour FLB Solutions, un distributeur alimentaire de Québec.
        
        ARTICLE:
        Titre: {title}
        Source: {source}
        Résumé: {summary[:1000]}
        
        Répondre en JSON avec cette structure exacte:
        {{
            "relevance_score": 0-100,
            "category": "supply_chain|local|trends|regulatory|competitor|other",
            "business_impact": "Description courte de l'impact sur FLB",
            "strategic_insights": "Opportunités ou risques identifiés",
            "recommended_actions": ["action1", "action2"],
            "confidence_level": 0-1
        }}
        """
        
        try:
            import time
            start_time = time.time()
            
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": 0.3,  # Plus déterministe
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            )
            
            processing_time = time.time() - start_time
            
            # Parser la réponse JSON
            response_text = response.get('response', '{}')
            try:
                # Extraire le JSON de la réponse
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = {}
            except json.JSONDecodeError:
                logger.warning("Failed to parse Ollama response as JSON")
                data = {}
            
            return AnalysisResult(
                relevance_score=data.get('relevance_score', 50) / 100,
                category=data.get('category', 'other'),
                business_impact=data.get('business_impact', ''),
                strategic_insights=data.get('strategic_insights', ''),
                recommended_actions=data.get('recommended_actions', []),
                confidence_level=data.get('confidence_level', 0.5),
                analysis_method='ollama',
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            return AnalysisResult(analysis_method="error")

class OpenRouterEnricher:
    """Enrichisseur basé sur OpenRouter pour analyse approfondie"""
    
    def __init__(self, api_key: str = None, model: str = "openai/o4"):
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            self.client = openai.OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        else:
            logger.warning("OpenRouter not configured. Cloud enrichment disabled.")
    
    def enrich_analysis(self, title: str, summary: str, initial_analysis: AnalysisResult) -> AnalysisResult:
        """Enrichir l'analyse avec un LLM cloud plus puissant"""
        
        if not self.client:
            return initial_analysis
        
        prompt = f"""
        En tant qu'expert en distribution alimentaire, analyser cet article pour FLB Solutions (distributeur alimentaire B2B à Québec).
        
        ARTICLE:
        Titre: {title}
        Résumé: {summary}
        
        ANALYSE INITIALE:
        Catégorie: {initial_analysis.category}
        Score de pertinence: {initial_analysis.relevance_score * 100:.0f}%
        
        Fournir une analyse stratégique approfondie en répondant UNIQUEMENT avec un objet JSON valide contenant:
        {{
            "business_impact": "Impact concret sur les opérations de FLB",
            "strategic_insights": "Opportunités et risques identifiés",
            "recommended_actions": ["action1", "action2", "action3"]
        }}
        
        Répondre SEULEMENT avec le JSON, sans texte supplémentaire.
        """
        
        try:
            import time
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Vous êtes un analyste stratégique spécialisé en distribution alimentaire B2B. Répondez UNIQUEMENT en JSON valide, sans aucun texte supplémentaire."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=800,
                extra_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "FLB News Bulletin Generator"
                }
            )
            
            processing_time = time.time() - start_time
            
            # Parser la réponse
            response_text = response.choices[0].message.content
            
            # Essayer de parser le JSON
            try:
                # Nettoyer la réponse si nécessaire
                import re
                # Essayer de trouver un objet JSON dans la réponse
                json_match = re.search(r'\{[^}]*\}', response_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    # Essayer de parser directement
                    data = json.loads(response_text)
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Failed to parse OpenRouter response as JSON: {e}")
                logger.debug(f"Response was: {response_text[:200]}...")
                # Utiliser des valeurs par défaut
                data = {
                    "business_impact": "Analyse en cours...",
                    "strategic_insights": "Données non disponibles",
                    "recommended_actions": []
                }
            
            # Enrichir l'analyse existante
            initial_analysis.strategic_insights = data.get('strategic_insights', initial_analysis.strategic_insights)
            initial_analysis.recommended_actions = data.get('recommended_actions', initial_analysis.recommended_actions)
            initial_analysis.business_impact = data.get('business_impact', initial_analysis.business_impact)
            initial_analysis.analysis_method = 'openrouter_enriched'
            initial_analysis.processing_time += processing_time
            initial_analysis.confidence_level = min(initial_analysis.confidence_level + 0.2, 1.0)
            
            return initial_analysis
            
        except Exception as e:
            logger.error(f"OpenRouter enrichment failed: {e}")
            return initial_analysis

class HybridAnalysisEngine:
    """Moteur d'analyse hybride orchestrant les différentes méthodes"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        
        # Initialiser les analyseurs selon la configuration
        self.bm25 = None
        self.ollama = None
        self.openrouter = None
        
        if self.config['enable_bm25']:
            keywords = self.config.get('keywords', {})
            self.bm25 = BM25Analyzer(keywords)
        
        if self.config['enable_ollama']:
            self.ollama = OllamaAnalyzer(
                model_name=self.config.get('ollama_model', 'phi2')
            )
        
        if self.config['enable_openrouter']:
            self.openrouter = OpenRouterEnricher(
                api_key=self.config.get('openrouter_api_key'),
                model=self.config.get('openrouter_model', 'openai/gpt-5')
            )
        
        self.cache_dir = os.path.join(os.path.dirname(__file__), '..', '.analysis_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _default_config(self) -> Dict:
        """Configuration par défaut"""
        return {
            'enable_bm25': True,
            'enable_ollama': False,  # Désactivé par défaut (nécessite Ollama installé)
            'enable_openrouter': False,  # Désactivé par défaut (nécessite API key)
            'mode': 'economique',  # economique, standard, premium
            'bm25_threshold': 0.3,  # Score minimum pour passer à l'analyse LLM
            'max_ollama_articles': 20,
            'max_openrouter_articles': 5
        }
    
    def analyze_batch(self, articles: List[Dict]) -> List[Tuple[Dict, AnalysisResult]]:
        """Analyser un lot d'articles avec la pipeline hybride"""
        
        results = []
        
        # Phase 1: BM25 scoring si disponible
        if self.bm25:
            # Construire l'index avec tous les articles
            documents = [
                f"{a.get('title', '')} {a.get('summary', '')} {a.get('full_text', '')}"
                for a in articles
            ]
            self.bm25.build_index(documents)
            
            # Scorer chaque article
            for i, article in enumerate(articles):
                score = self.bm25.score_document(documents[i])
                article['bm25_score'] = score
        else:
            # Fallback: tous les articles ont un score de 0.5
            for article in articles:
                article['bm25_score'] = 0.5
        
        # Trier par score BM25
        articles.sort(key=lambda x: x.get('bm25_score', 0), reverse=True)
        
        # Phase 2: Analyse Ollama pour les top articles
        ollama_candidates = articles[:self.config['max_ollama_articles']]
        
        for article in ollama_candidates:
            # Vérifier le cache
            cache_key = self._get_cache_key(article)
            cached_result = self._load_from_cache(cache_key)
            
            if cached_result:
                results.append((article, cached_result))
                continue
            
            # Analyse avec Ollama si disponible
            if self.ollama and article.get('bm25_score', 0) >= self.config['bm25_threshold']:
                analysis = self.ollama.analyze_article(
                    title=article.get('title', ''),
                    summary=article.get('summary', ''),
                    source=article.get('source', '')
                )
            else:
                # Analyse basique
                analysis = self._basic_analysis(article)
            
            # Sauvegarder en cache
            self._save_to_cache(cache_key, analysis)
            results.append((article, analysis))
        
        # Phase 3: Enrichissement OpenRouter pour les meilleurs
        if self.openrouter and self.config['mode'] in ['standard', 'premium']:
            # Trier par score de pertinence
            results.sort(key=lambda x: x[1].relevance_score, reverse=True)
            
            # Enrichir les top articles
            for i in range(min(self.config['max_openrouter_articles'], len(results))):
                article, analysis = results[i]
                
                # Enrichir seulement si le score est suffisant
                if analysis.relevance_score >= 0.5:
                    enriched = self.openrouter.enrich_analysis(
                        title=article.get('title', ''),
                        summary=article.get('summary', ''),
                        initial_analysis=analysis
                    )
                    results[i] = (article, enriched)
        
        return results
    
    def _basic_analysis(self, article: Dict) -> AnalysisResult:
        """Analyse basique sans LLM"""
        # Utiliser le score BM25 s'il existe
        score = article.get('bm25_score', 0.5)
        
        # Catégorisation simple basée sur mots-clés
        text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
        
        category = "other"
        if any(word in text for word in ['chaîne', 'supply', 'logistique', 'transport']):
            category = "supply_chain"
        elif any(word in text for word in ['québec', 'local', 'régional']):
            category = "local"
        elif any(word in text for word in ['tendance', 'trend', 'innovation']):
            category = "trends"
        elif any(word in text for word in ['règlement', 'loi', 'norme']):
            category = "regulatory"
        
        return AnalysisResult(
            relevance_score=score,
            category=category,
            business_impact="Analyse basique - Impact à évaluer",
            analysis_method="basic",
            confidence_level=0.3
        )
    
    def _get_cache_key(self, article: Dict) -> str:
        """Générer une clé de cache pour un article"""
        content = f"{article.get('title', '')}{article.get('url', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _load_from_cache(self, key: str) -> Optional[AnalysisResult]:
        """Charger une analyse depuis le cache"""
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_file):
            # Vérifier l'âge du cache (24h)
            if (datetime.now().timestamp() - os.path.getmtime(cache_file)) < 86400:
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        return AnalysisResult(**data)
                except Exception as e:
                    logger.warning(f"Failed to load cache {key}: {e}")
        return None
    
    def _save_to_cache(self, key: str, result: AnalysisResult):
        """Sauvegarder une analyse dans le cache"""
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump(result.__dict__, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache {key}: {e}")

# Point d'entrée pour les tests
if __name__ == "__main__":
    # Configuration de test
    config = {
        'enable_bm25': True,
        'enable_ollama': False,  # Mettre à True si Ollama est installé
        'enable_openrouter': False,  # Mettre à True avec une API key
        'mode': 'economique',
        'keywords': {
            'distributeur alimentaire': 10,
            'québec': 8,
            'supply chain': 7,
            'restauration': 6
        }
    }
    
    # Créer le moteur
    engine = HybridAnalysisEngine(config)
    
    # Articles de test
    test_articles = [
        {
            'title': "Nouvelle réglementation sur la distribution alimentaire au Québec",
            'summary': "Le gouvernement du Québec annonce de nouvelles normes pour les distributeurs alimentaires...",
            'source': "La Presse",
            'url': "https://example.com/1"
        },
        {
            'title': "Innovation in Food Supply Chain Management",
            'summary': "Major advances in AI and blockchain are transforming food distribution...",
            'source': "Food Business News",
            'url': "https://example.com/2"
        }
    ]
    
    # Analyser
    results = engine.analyze_batch(test_articles)
    
    # Afficher les résultats
    for article, analysis in results:
        print(f"\n{'='*60}")
        print(f"Titre: {article['title']}")
        print(f"Score: {analysis.relevance_score:.2%}")
        print(f"Catégorie: {analysis.category}")
        print(f"Méthode: {analysis.analysis_method}")
        print(f"Impact: {analysis.business_impact}")