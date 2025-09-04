#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, 'src')

# Test 1: Vérifier les modules
print("=== TEST 1: Vérification des modules ===")
try:
    from dotenv import load_dotenv
    print("✓ python-dotenv installé")
except ImportError:
    print("✗ python-dotenv NON installé - Installez avec: pip install python-dotenv")

try:
    import deepl
    print("✓ deepl installé")
except ImportError:
    print("✗ deepl NON installé - Installez avec: pip install deepl")

# Test 2: Vérifier la clé API
print("\n=== TEST 2: Vérification de la clé API ===")
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('DEEPL_API_KEY')
if api_key:
    print(f"✓ Clé API trouvée: {api_key[:15]}...")
else:
    print("✗ Clé API non trouvée dans .env")

# Test 3: Tester la traduction
print("\n=== TEST 3: Test de traduction ===")
try:
    from translator import NewsTranslator
    translator = NewsTranslator()
    
    # Test avec un texte anglais
    test_text = "Food distribution companies face supply chain challenges"
    result = translator.translate_if_needed(test_text, "Canadian Grocer")
    
    print(f"Texte original: {test_text}")
    print(f"Texte traduit:  {result}")
    
    if result != test_text:
        print("✓ Traduction fonctionnelle!")
    else:
        print("✗ La traduction n'a pas fonctionné")
        
except Exception as e:
    print(f"✗ Erreur lors du test: {e}")

# Test 4: Vérifier le cache
print("\n=== TEST 4: Vérification du cache ===")
import os
cache_dir = ".translation_cache"
if os.path.exists(cache_dir):
    files = os.listdir(cache_dir)
    print(f"✓ Dossier cache existe avec {len(files)} fichiers")
    if files:
        print("  Fichiers en cache:", files[:5])
else:
    print("✗ Dossier cache n'existe pas")