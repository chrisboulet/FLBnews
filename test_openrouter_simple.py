#!/usr/bin/env python3
"""Test simple de l'API OpenRouter"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_openrouter_api():
    """Test direct de l'API OpenRouter avec requests"""
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Clé API non trouvée")
        return
    
    print(f"✅ Clé API trouvée: {api_key[:20]}...")
    
    # Test simple
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "FLB News Test",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "openai/gpt-4o",  # Utiliser GPT-4o au lieu de GPT-5
        "messages": [
            {
                "role": "user",
                "content": "Réponds uniquement avec un JSON simple: {\"status\": \"ok\", \"message\": \"test réussi\"}"
            }
        ],
        "temperature": 0.1,
        "max_tokens": 100
    }
    
    print("\n📡 Envoi de la requête à OpenRouter...")
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"\n✅ Réponse reçue:\n{content}")
            else:
                print(f"\n⚠️ Structure inattendue:\n{json.dumps(result, indent=2)}")
        else:
            print(f"\n❌ Erreur {response.status_code}:")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")

if __name__ == "__main__":
    test_openrouter_api()