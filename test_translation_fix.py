#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')

from translator import NewsTranslator

translator = NewsTranslator()

# Test avec les différentes sources
test_text = "Food distribution companies are facing new challenges in supply chain management"

sources_to_test = [
    'Canadian Grocer',
    'Western Grocer',
    'Le Bulletin des Agriculteurs',
    'La Terre de Chez Nous'
]

for source in sources_to_test:
    print(f"\n{source}:")
    print("-" * 50)
    translated = translator.translate_if_needed(test_text, source)
    if translated != test_text:
        print(f"✓ Traduit: {translated}")
    else:
        print(f"✗ Non traduit: {test_text}")