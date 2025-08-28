#!/usr/bin/env python3

print("=== DÉBOGAGE DE LA TRADUCTION ===\n")

# 1. Vérifier l'installation
print("1. Vérification des modules:")
modules_ok = True

try:
    import deepl
    print("   ✓ deepl installé")
except ImportError:
    print("   ✗ deepl NON installé")
    print("   → Installez avec: pip install deepl")
    modules_ok = False

try:
    from dotenv import load_dotenv
    print("   ✓ python-dotenv installé")
except ImportError:
    print("   ✗ python-dotenv NON installé")
    print("   → Installez avec: pip install python-dotenv")
    modules_ok = False

if not modules_ok:
    print("\n⚠️  Installez d'abord les modules manquants:")
    print("    pip install -r requirements.txt")
    exit(1)

# 2. Vérifier la clé API
print("\n2. Vérification de la clé API DeepL:")
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('DEEPL_API_KEY')

if api_key:
    print(f"   ✓ Clé trouvée: {api_key[:20]}...")
    
    # Tester la clé
    try:
        translator = deepl.Translator(api_key)
        usage = translator.get_usage()
        print(f"   ✓ Connexion DeepL OK")
        print(f"   → {usage.character.count:,} / {usage.character.limit:,} caractères utilisés")
        
        # Test de traduction
        test = translator.translate_text("Hello", target_lang="FR")
        print(f"   ✓ Test de traduction: 'Hello' → '{test.text}'")
        
    except Exception as e:
        print(f"   ✗ Erreur DeepL: {e}")
        print("   → Vérifiez que votre clé API est valide")
else:
    print("   ✗ Clé API non trouvée")
    print("   → Vérifiez le fichier .env")

# 3. Tester le module de traduction
print("\n3. Test du module de traduction:")
import sys
sys.path.insert(0, 'src')

try:
    from translator import NewsTranslator
    translator = NewsTranslator()
    
    # Tester avec une source anglophone
    test_text = "Food distribution supply chain"
    sources_to_test = ["Canadian Grocer", "Food in Canada", "Grocery Business", "Les Affaires"]
    
    print(f"\n   Texte test: '{test_text}'")
    print("   Résultats par source:")
    
    for source in sources_to_test:
        result = translator.translate_if_needed(test_text, source)
        if result != test_text:
            print(f"   • {source:20} → '{result}' ✓")
        else:
            print(f"   • {source:20} → Pas traduit ✗")
            
except Exception as e:
    print(f"   ✗ Erreur: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("Pour installer les dépendances manquantes:")
print("  pip install -r requirements.txt")
print("\nPour tester l'application:")
print("  python main.py --run-now")