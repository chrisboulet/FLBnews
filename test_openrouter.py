#!/usr/bin/env python3
"""
Script de test pour l'intégration OpenRouter avec GPT-5
"""

import os
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le dossier src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from analyzer_engine import HybridAnalysisEngine, OpenRouterEnricher

def test_openrouter_direct():
    """Test direct de l'API OpenRouter"""
    print("Test direct de l'API OpenRouter avec GPT-5...")
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Clé API OpenRouter non trouvée dans .env")
        return False
    
    print(f"✅ Clé API trouvée: {api_key[:20]}...")
    
    # Créer l'enrichisseur
    enricher = OpenRouterEnricher(
        api_key=api_key,
        model="openai/gpt-5"
    )
    
    # Article de test
    test_article = {
        'title': "Pénurie de main-d'œuvre dans la distribution alimentaire au Québec",
        'summary': "Le secteur de la distribution alimentaire au Québec fait face à une pénurie critique de main-d'œuvre, avec plus de 5000 postes vacants. Les entreprises doivent augmenter les salaires et améliorer les conditions de travail pour attirer du personnel.",
        'source': "Le Journal de Québec"
    }
    
    # Créer une analyse de base
    from analyzer_engine import AnalysisResult
    basic_analysis = AnalysisResult(
        relevance_score=0.7,
        category="local",
        business_impact="Impact potentiel sur les opérations"
    )
    
    try:
        print("\n📡 Envoi de la requête à OpenRouter (GPT-5)...")
        enriched = enricher.enrich_analysis(
            title=test_article['title'],
            summary=test_article['summary'],
            initial_analysis=basic_analysis
        )
        
        print("\n✅ Analyse enrichie reçue:")
        print(f"  - Méthode: {enriched.analysis_method}")
        print(f"  - Score de pertinence: {enriched.relevance_score:.2%}")
        print(f"  - Catégorie: {enriched.category}")
        print(f"  - Impact business: {enriched.business_impact}")
        print(f"  - Insights stratégiques: {enriched.strategic_insights}")
        print(f"  - Actions recommandées: {enriched.recommended_actions}")
        print(f"  - Niveau de confiance: {enriched.confidence_level:.2%}")
        print(f"  - Temps de traitement: {enriched.processing_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'appel à OpenRouter: {e}")
        return False

def test_hybrid_engine():
    """Test du moteur hybride avec OpenRouter activé"""
    print("\n" + "="*60)
    print("Test du moteur hybride avec OpenRouter...")
    
    # Configuration avec OpenRouter activé
    config = {
        'enable_bm25': True,
        'enable_ollama': False,  # Désactivé pour ce test
        'enable_openrouter': True,  # Activé
        'mode': 'premium',  # Mode premium pour utiliser OpenRouter
        'openrouter_model': 'openai/gpt-5',
        'keywords': {
            'distributeur alimentaire': 10,
            'québec': 8,
            'supply chain': 7,
            'restauration': 6,
            'pénurie': 5,
            'main-d\'œuvre': 5
        },
        'max_ollama_articles': 20,  # Même si Ollama est désactivé
        'max_openrouter_articles': 2
    }
    
    # Créer le moteur
    engine = HybridAnalysisEngine(config)
    
    # Articles de test
    test_articles = [
        {
            'title': "Innovation majeure dans la chaîne d'approvisionnement alimentaire",
            'summary': "Une nouvelle technologie d'IA révolutionne la gestion des inventaires pour les distributeurs alimentaires, permettant de réduire le gaspillage de 30% et d'optimiser les livraisons.",
            'source': "Food Business News",
            'url': "https://example.com/1"
        },
        {
            'title': "Québec : Nouvelles réglementations pour les distributeurs",
            'summary': "Le gouvernement du Québec impose de nouvelles normes sanitaires strictes pour tous les distributeurs alimentaires de la province, entrée en vigueur en janvier 2025.",
            'source': "La Presse",
            'url': "https://example.com/2"
        },
        {
            'title': "Météo : Prévisions pour la semaine",
            'summary': "Temps ensoleillé prévu pour les prochains jours dans la région de Québec.",
            'source': "Météo Média",
            'url': "https://example.com/3"
        }
    ]
    
    try:
        print("\n🔄 Analyse des articles en cours...")
        results = engine.analyze_batch(test_articles)
        
        print(f"\n✅ {len(results)} articles analysés:")
        for article, analysis in results:
            print(f"\n📰 {article['title'][:60]}...")
            print(f"   Score: {analysis.relevance_score:.2%}")
            print(f"   Méthode: {analysis.analysis_method}")
            print(f"   Catégorie: {analysis.category}")
            if analysis.business_impact:
                print(f"   Impact: {analysis.business_impact[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'analyse hybride: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    print("🚀 Test de l'intégration OpenRouter avec GPT-5")
    print("="*60)
    
    # Test 1: API directe
    success_direct = test_openrouter_direct()
    
    # Test 2: Moteur hybride
    success_hybrid = test_hybrid_engine()
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS:")
    print(f"  - Test API directe: {'✅ Réussi' if success_direct else '❌ Échoué'}")
    print(f"  - Test moteur hybride: {'✅ Réussi' if success_hybrid else '❌ Échoué'}")
    
    if success_direct and success_hybrid:
        print("\n🎉 Tous les tests ont réussi! OpenRouter avec GPT-5 est opérationnel.")
    else:
        print("\n⚠️ Certains tests ont échoué. Vérifiez la configuration.")

if __name__ == "__main__":
    main()