#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import deepl

load_dotenv()

api_key = os.getenv('DEEPL_API_KEY')
print(f"API Key trouvée: {bool(api_key)}")

if api_key:
    try:
        translator = deepl.Translator(api_key)
        
        # Test de connexion
        usage = translator.get_usage()
        print(f"Connexion DeepL réussie")
        print(f"Caractères utilisés: {usage.character.count}/{usage.character.limit}")
        
        # Test de traduction simple
        test_text = "Food distribution companies are facing new challenges"
        result = translator.translate_text(
            test_text,
            source_lang="EN",
            target_lang="FR"
        )
        print(f"\nTest de traduction:")
        print(f"Anglais: {test_text}")
        print(f"Français: {result.text}")
        
    except Exception as e:
        print(f"Erreur DeepL: {e}")
        print(f"Type d'erreur: {type(e).__name__}")
else:
    print("Clé API non trouvée dans .env")