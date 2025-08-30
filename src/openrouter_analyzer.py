#!/usr/bin/env python3
"""
Analyseur OpenRouter dédié pour FLB News
Utilise GPT-5 pour générer des analyses et résumés intelligents
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import openai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class ArticleAnalysis:
    """Résultat d'analyse d'un article par GPT-5"""
    title_fr: str = ""
    smart_summary: str = ""  # Résumé intelligent en français
    flb_relevance: str = ""  # Explication de la pertinence pour FLB
    business_impact: str = ""  # Impact sur le business
    recommended_actions: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    category: str = ""
    confidence: float = 0.0

class OpenRouterAnalyzer:
    """Analyseur utilisant OpenRouter avec GPT-4o"""
    
    def __init__(self, api_key: str = None, model: str = "openai/o4"):
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.model = model
        self.client = None
        
        if self.api_key:
            self.client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key
            )
            logger.info(f"OpenRouter configuré avec le modèle: {self.model}")
        else:
            logger.error("Clé API OpenRouter non trouvée!")
    
    def analyze_article(self, title: str, content: str, source: str, url: str = "") -> ArticleAnalysis:
        """
        Analyser un article avec GPT-5 pour générer un résumé intelligent
        et une analyse stratégique pour FLB Solutions
        """
        
        if not self.client:
            return ArticleAnalysis(
                title_fr=title,
                smart_summary=content[:500] + "...",
                flb_relevance="Analyse non disponible"
            )
        
        # Prompt optimisé pour GPT-5
        prompt = f"""Tu es un analyste stratégique expert pour FLB Solutions, distributeur alimentaire B2B de Québec.
        
ARTICLE À ANALYSER:
Titre: {title}
Source: {source}
Contenu: {content[:2000]}

CONTEXTE FLB:
- Distributeur alimentaire B2B basé à Québec
- Clients: restaurants, hôtels, cafétérias, épiceries
- Produits: frais, surgelés, épicerie, viandes
- Zone: Capitale-Nationale et environs
- Défis: pénurie main-d'œuvre, inflation, chaîne d'approvisionnement

TÂCHE: Analyser cet article et générer un JSON structuré:

{{
    "title_fr": "Titre en français clair et accrocheur",
    "smart_summary": "Résumé de 2-3 phrases expliquant les points clés pour un distributeur alimentaire",
    "flb_relevance": "Explication directe de pourquoi FLB doit s'intéresser à cette nouvelle",
    "business_impact": "Impact concret sur FLB (coûts, opportunités, clients, etc.)",
    "category": "supply_chain|local|trends|regulatory|competitor|innovation|other",
    "relevance_score": 0-100,
    "opportunities": ["Opportunité business concrète"],
    "risks": ["Risque potentiel"],
    "recommended_actions": ["Action spécifique que FLB devrait prendre"],
    "confidence": 0.1-1.0
}}

IMPORTANT: 
- Résumé COURT et PERTINENT pour FLB
- Actions CONCRÈTES et RÉALISABLES
- Répondre UNIQUEMENT avec le JSON, sans texte additionnel"""

        try:
            logger.info(f"Analyse O4 de: {title[:50]}...")
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Tu es un analyste expert en distribution alimentaire. Réponds UNIQUEMENT en JSON valide."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Plus déterministe
                max_tokens=800,  # Réduit pour économiser les tokens
                timeout=15,  # Timeout pour éviter les attentes infinies
                extra_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "FLB News Bulletin Generator"
                }
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Réponse reçue en {processing_time:.2f}s")
            
            # Parser la réponse
            response_text = response.choices[0].message.content
            
            # Nettoyer et parser le JSON
            try:
                # Extraire le JSON de la réponse
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    data = json.loads(response_text)
                
                # Créer l'objet d'analyse
                return ArticleAnalysis(
                    title_fr=data.get('title_fr', title),
                    smart_summary=data.get('smart_summary', content[:300] + "..."),
                    flb_relevance=data.get('flb_relevance', 'Pertinence à évaluer'),
                    business_impact=data.get('business_impact', ''),
                    recommended_actions=data.get('recommended_actions', [])[:3],
                    opportunities=data.get('opportunities', [])[:2],
                    risks=data.get('risks', [])[:2],
                    relevance_score=float(data.get('relevance_score', 50)) / 100,
                    category=data.get('category', 'other'),
                    confidence=float(data.get('confidence', 0.5))
                )
                
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Erreur parsing JSON: {e}")
                logger.debug(f"Réponse brute: {response_text[:500]}...")
                
                # Fallback avec analyse basique
                return ArticleAnalysis(
                    title_fr=title,
                    smart_summary=f"Article de {source} sur les développements récents du secteur alimentaire.",
                    flb_relevance="Article potentiellement pertinent pour FLB Solutions.",
                    relevance_score=0.5,
                    category="other",
                    confidence=0.3
                )
                
        except Exception as e:
            logger.error(f"Erreur OpenRouter: {e}")
            return ArticleAnalysis(
                title_fr=title,
                smart_summary=content[:300] + "...",
                flb_relevance="Analyse temporairement indisponible",
                relevance_score=0.3
            )
    
    def analyze_batch(self, articles: List[Dict], max_articles: int = 7) -> List[ArticleAnalysis]:
        """
        Analyser un lot d'articles avec O4 de manière optimisée
        Utilise un retry intelligent et évite les pauses fixes
        """
        results = []
        
        # Pré-trier les articles par score de pertinence si disponible
        # Buffer: analyser plus d'articles pour avoir des alternatives si certains échouent
        buffer_size = max_articles + 3  # 3 articles de buffer
        candidate_articles = articles[:max_articles * 2] if len(articles) > max_articles * 2 else articles
        
        sorted_articles = sorted(
            candidate_articles,
            key=lambda x: x.get('relevance_score', 0),
            reverse=True
        )[:buffer_size]
        
        logger.info(f"Buffer d'analyse: {len(sorted_articles)} articles candidats (cible: {max_articles})")
        
        for i, article in enumerate(sorted_articles):
            logger.info(f"Analyse O4 ({i+1}/{len(sorted_articles)}): {article.get('title', '')[:50]}...")
            
            # Analyser avec retry intelligent
            analysis = self._analyze_with_retry(
                title=article.get('title', ''),
                content=article.get('summary', '') + " " + article.get('full_text', '')[:1000],
                source=article.get('source', ''),
                url=article.get('url', ''),
                retry_count=3
            )
            
            results.append(analysis)
            
            # Arrêter si on a assez d'analyses réussies
            successful_analyses = [r for r in results if r.relevance_score > 0.1]  # Score minimum
            if len(successful_analyses) >= max_articles:
                logger.info(f"Objectif atteint: {len(successful_analyses)} analyses réussies")
                break
        
        logger.info(f"Analyse terminée: {len(results)} articles traités, {len([r for r in results if r.relevance_score > 0.1])} réussis")
        return results[:max_articles]  # Retourner seulement le nombre demandé
    
    def _analyze_with_retry(self, title: str, content: str, source: str, url: str = "", retry_count: int = 3) -> ArticleAnalysis:
        """
        Analyser avec retry intelligent et backoff exponentiel
        """
        last_error = None
        
        for attempt in range(retry_count):
            try:
                return self.analyze_article(title, content, source, url)
            except Exception as e:
                last_error = e
                if attempt < retry_count - 1:
                    # Backoff exponentiel: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    logger.warning(f"API error (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts failed for {title[:30]}...")
        
        # Fallback si tous les essais échouent
        logger.warning(f"Falling back to basic analysis for: {title[:50]}...")
        return ArticleAnalysis(
            title_fr=title,
            smart_summary=content[:300] + "...",
            flb_relevance="Analyse temporairement indisponible - article sélectionné par scoring automatique",
            relevance_score=0.6,  # Score conservateur
            category="other",
            confidence=0.3
        )

def test_analyzer():
    """Test de l'analyseur OpenRouter"""
    
    analyzer = OpenRouterAnalyzer()
    
    test_article = {
        'title': "Pénurie de camionneurs : Metro et Sobeys peinent à approvisionner le Québec",
        'summary': """Les grandes chaînes d'alimentation du Québec font face à des défis majeurs 
        d'approvisionnement. La pénurie de camionneurs affecte particulièrement la région de 
        la Capitale-Nationale. Les restaurants et hôtels peinent à obtenir des produits frais 
        régulièrement. Les coûts de transport ont augmenté de 35% en 6 mois.""",
        'source': "La Presse",
        'url': "https://example.com/test"
    }
    
    print("🧪 Test de l'analyseur OpenRouter O4")
    print("="*60)
    
    analysis = analyzer.analyze_article(
        title=test_article['title'],
        content=test_article['summary'],
        source=test_article['source'],
        url=test_article['url']
    )
    
    print(f"\n📰 Titre FR: {analysis.title_fr}")
    print(f"\n💡 Résumé intelligent:\n   {analysis.smart_summary}")
    print(f"\n🎯 Pertinence FLB:\n   {analysis.flb_relevance}")
    print(f"\n💼 Impact business:\n   {analysis.business_impact}")
    
    if analysis.opportunities:
        print(f"\n✅ Opportunités:")
        for opp in analysis.opportunities:
            print(f"   - {opp}")
    
    if analysis.risks:
        print(f"\n⚠️ Risques:")
        for risk in analysis.risks:
            print(f"   - {risk}")
    
    if analysis.recommended_actions:
        print(f"\n📋 Actions recommandées:")
        for action in analysis.recommended_actions:
            print(f"   - {action}")
    
    print(f"\n📊 Score: {analysis.relevance_score:.0%} | Catégorie: {analysis.category}")
    print(f"🔍 Confiance: {analysis.confidence:.0%}")

if __name__ == "__main__":
    test_analyzer()