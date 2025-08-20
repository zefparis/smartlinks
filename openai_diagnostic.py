#!/usr/bin/env python3
import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo')

print('🔍 OPENAI API HEALTH CHECK')
print('=' * 50)

timestamp = datetime.now().isoformat()
print(f'Timestamp: {timestamp}')
print(f'Modèle cible: {model}')
print()

# 1. Validation clé
print('1. Validation de la clé API...')
if not api_key or not api_key.startswith('sk-') or len(api_key) < 50:
    print('   ❌ Clé API invalide')
    exit(1)
print('   ✅ Format de clé valide')

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# 2. Test endpoint models
print()
print('2. Test de l\'endpoint /v1/models...')
try:
    start_time = time.time()
    response = requests.get('https://api.openai.com/v1/models', headers=headers, timeout=10)
    latency_models = (time.time() - start_time) * 1000
    
    if response.status_code == 200:
        models_data = response.json()
        available_models = [m['id'] for m in models_data.get('data', [])]
        gpt4_models = [m for m in available_models if 'gpt-4' in m]
        
        print(f'   ✅ OK - {len(available_models)} modèles disponibles')
        print(f'   Latence: {round(latency_models, 2)}ms')
        print(f'   Modèle cible disponible: {"✅" if model in available_models else "❌"}')
        print(f'   GPT-4 disponibles: {", ".join(gpt4_models[:3])}...')
    else:
        print(f'   ❌ ERREUR HTTP {response.status_code}: {response.text[:100]}')
        exit(1)
        
except Exception as e:
    print(f'   ❌ ERREUR: {e}')
    exit(1)

# 3. Test chat completion
print()
print('3. Test de chat completion...')
try:
    start_time = time.time()
    
    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': 'Tu es un assistant de test. Réponds brièvement.'},
            {'role': 'user', 'content': 'Dis juste "Test OK" si tu reçois ce message.'}
        ],
        'max_tokens': 10,
        'temperature': 0
    }
    
    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers=headers,
        json=payload,
        timeout=30
    )
    
    latency_chat = (time.time() - start_time) * 1000
    
    if response.status_code == 200:
        data = response.json()
        choice = data.get('choices', [{}])[0]
        message = choice.get('message', {})
        
        print(f'   ✅ OK - Réponse reçue')
        print(f'   Modèle utilisé: {data.get("model")}')
        print(f'   Latence: {round(latency_chat, 2)}ms')
        print(f'   Tokens utilisés: {data.get("usage", {}).get("total_tokens", 0)}')
        print(f'   Réponse: "{message.get("content", "").strip()}"')
        
        # Résumé final
        print()
        print('=' * 50)
        print('✅ HEALTHCHECK: OK')
        print(f'Modèle: {data.get("model")}')
        print(f'Latence moyenne: {round((latency_models + latency_chat) / 2, 2)}ms')
        print(f'Timestamp: {timestamp}')
        print('Tous les tests sont passés avec succès!')
        
    else:
        print(f'   ❌ ERREUR HTTP {response.status_code}: {response.text[:100]}')
        exit(1)
        
except Exception as e:
    print(f'   ❌ ERREUR: {e}')
    exit(1)
