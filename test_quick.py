#!/usr/bin/env python3

import sys
import os

# Ajouter le chemin src
sys.path.insert(0, 'src')

print("Test rapide de traduction DeepL\n")

# Définir la clé API directement
os.environ['DEEPL_API_KEY'] = 'fbf92def-0652-4c6d-87da-3e71f25a3fdd:fx'

try:
    import deepl
    translator = deepl.Translator(os.environ['DEEPL_API_KEY'])
    
    # Tester avec FR (pas FR-CA)
    result = translator.translate_text(
        "Food distribution supply chain challenges in Quebec",
        source_lang="EN",
        target_lang="FR",
        formality="less"
    )
    
    print("✅ DeepL fonctionne!")
    print(f"Texte original: Food distribution supply chain challenges in Quebec")
    print(f"Texte traduit:  {result.text}")
    
    usage = translator.get_usage()
    print(f"\nCaractères utilisés: {usage.character.count:,} / {usage.character.limit:,}")
    
except ImportError:
    print("❌ Module deepl non installé")
    print("Installez avec: pip install deepl")
    
except Exception as e:
    print(f"❌ Erreur: {e}")