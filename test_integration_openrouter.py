#!/usr/bin/env python3
"""
Test d'intégration complète avec OpenRouter GPT-5
"""

import os
import sys
from datetime import datetime

# Configuration de l'environnement
os.environ['PYTHONPATH'] = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import FLBNewsApp
from config_openrouter import get_analysis_config

def test_bulletin_with_openrouter():
    """Test de génération de bulletin avec OpenRouter"""
    print("🚀 Test de génération de bulletin avec OpenRouter GPT-5")
    print("="*60)
    
    # Vérifier la configuration
    config = get_analysis_config()
    
    if not config.get('enable_openrouter'):
        print("❌ OpenRouter n'est pas activé. Vérifiez votre configuration.")
        return False
    
    print(f"✅ OpenRouter activé avec le modèle: {config['openrouter_model']}")
    print(f"   Mode: {config['mode']}")
    print(f"   Articles max avec GPT-5: {config['max_openrouter_articles']}")
    
    try:
        # Créer l'application
        print("\n📱 Initialisation de l'application FLB News...")
        app = FLBNewsApp()
        
        # Générer un bulletin
        print("\n📰 Génération du bulletin en cours...")
        print("   (Cela peut prendre quelques minutes avec l'analyse GPT-5)")
        
        bulletin_path = app.run_bulletin_generation()
        
        if bulletin_path:
            print(f"\n✅ Bulletin généré avec succès!")
            print(f"   Fichier: {bulletin_path}")
            
            # Afficher un aperçu du contenu
            with open(bulletin_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'GPT-5' in content or 'openrouter' in content.lower():
                    print("   ✅ Traces d'analyse OpenRouter détectées dans le bulletin")
                
            return True
        else:
            print("\n⚠️ Aucun bulletin généré (peut-être aucune nouvelle pertinente)")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la génération: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quick_analysis():
    """Test rapide de l'analyse avec un article exemple"""
    print("\n" + "="*60)
    print("⚡ Test rapide d'analyse avec OpenRouter")
    
    from analyzer_engine import HybridAnalysisEngine
    from config_openrouter import get_analysis_config
    
    config = get_analysis_config()
    engine = HybridAnalysisEngine(config)
    
    # Article test très pertinent pour FLB
    test_article = {
        'title': "Metro et Sobeys annoncent une pénurie de produits frais au Québec",
        'summary': """Les grands distributeurs alimentaires du Québec font face à des défis 
        d'approvisionnement majeurs. La chaîne du froid est perturbée et les coûts de 
        transport ont augmenté de 25%. Les restaurateurs de la région de Québec peinent 
        à s'approvisionner en produits frais locaux. FLB Solutions pourrait bénéficier 
        de cette situation en offrant des alternatives d'approvisionnement.""",
        'source': "La Presse Affaires",
        'url': "https://example.com/test"
    }
    
    print(f"\n📄 Article test: {test_article['title']}")
    
    try:
        print("\n🔄 Analyse en cours avec GPT-5...")
        results = engine.analyze_batch([test_article])
        
        if results:
            article, analysis = results[0]
            print(f"\n✅ Résultats de l'analyse:")
            print(f"   - Score de pertinence: {analysis.relevance_score:.2%}")
            print(f"   - Catégorie: {analysis.category}")
            print(f"   - Méthode d'analyse: {analysis.analysis_method}")
            print(f"   - Niveau de confiance: {analysis.confidence_level:.2%}")
            
            if analysis.business_impact:
                print(f"\n   💼 Impact business:")
                print(f"      {analysis.business_impact}")
            
            if analysis.strategic_insights:
                print(f"\n   🎯 Insights stratégiques:")
                print(f"      {analysis.strategic_insights}")
            
            if analysis.recommended_actions:
                print(f"\n   ✅ Actions recommandées:")
                for action in analysis.recommended_actions[:3]:
                    print(f"      - {action}")
            
            return True
        else:
            print("❌ Aucun résultat d'analyse")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔧 TEST D'INTÉGRATION OPENROUTER GPT-5 AVEC FLB NEWS")
    print("="*60)
    
    # Test 1: Analyse rapide
    success_analysis = test_quick_analysis()
    
    # Test 2: Génération de bulletin (optionnel car plus long)
    print("\n" + "="*60)
    response = input("\n💭 Voulez-vous tester la génération complète du bulletin? (o/n): ")
    
    success_bulletin = False
    if response.lower() in ['o', 'oui', 'y', 'yes']:
        success_bulletin = test_bulletin_with_openrouter()
    else:
        print("   Test de génération ignoré")
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS:")
    print(f"   - Analyse rapide: {'✅ Réussi' if success_analysis else '❌ Échoué'}")
    if response.lower() in ['o', 'oui', 'y', 'yes']:
        print(f"   - Génération bulletin: {'✅ Réussi' if success_bulletin else '❌ Échoué'}")
    
    if success_analysis:
        print("\n🎉 OpenRouter GPT-5 est correctement intégré à FLB News!")
        print("\n📝 Pour utiliser OpenRouter dans vos bulletins:")
        print("   1. Assurez-vous que la clé API est dans .env")
        print("   2. Lancez: python main.py")
        print("   3. Le bulletin utilisera automatiquement GPT-5 pour l'analyse")

if __name__ == "__main__":
    main()