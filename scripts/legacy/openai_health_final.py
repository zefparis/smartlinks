#!/usr/bin/env python3
"""
OpenAI API Health Check - Diagnostic complet de connectivité
Compatible Windows avec gestion d'erreurs avancée
"""
import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def openai_health_check():
    """Diagnostic complet OpenAI API"""
    
    api_key = os.getenv('OPENAI_API_KEY')
    model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo')
    
    print('🔍 OPENAI API HEALTH CHECK')
    print('=' * 50)
    
    timestamp = datetime.now().isoformat()
    print(f'Timestamp: {timestamp}')
    print(f'Modèle cible: {model}')
    print()
    
    # 1. Validation de la clé API
    print('1. Validation de la clé API...')
    if not api_key:
        print('   ❌ Clé API manquante dans .env')
        print('   🔧 TROUBLESHOOTING: Ajoutez OPENAI_API_KEY=sk-... dans .env')
        return False
        
    if not api_key.startswith('sk-'):
        print('   ❌ Format de clé invalide (doit commencer par sk-)')
        print('   🔧 TROUBLESHOOTING: Vérifiez le format sur platform.openai.com')
        return False
        
    if len(api_key) < 50:
        print('   ❌ Clé API trop courte')
        print('   🔧 TROUBLESHOOTING: Clé probablement tronquée')
        return False
        
    print('   ✅ Format de clé valide')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'SmartLinks-Autopilot/1.0'
    }
    
    # 2. Test de l'endpoint /v1/models
    print()
    print('2. Test de l\'endpoint /v1/models...')
    try:
        start_time = time.time()
        response = requests.get(
            'https://api.openai.com/v1/models', 
            headers=headers, 
            timeout=15
        )
        latency_models = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            models_data = response.json()
            available_models = [m['id'] for m in models_data.get('data', [])]
            gpt4_models = [m for m in available_models if 'gpt-4' in m]
            
            print(f'   ✅ OK - {len(available_models)} modèles disponibles')
            print(f'   Latence: {round(latency_models, 2)}ms')
            print(f'   Modèle cible disponible: {"✅" if model in available_models else "❌"}')
            
            if gpt4_models:
                print(f'   GPT-4 disponibles: {", ".join(gpt4_models[:5])}')
            else:
                print('   ⚠️ Aucun modèle GPT-4 trouvé')
                
        elif response.status_code == 401:
            print('   ❌ ERREUR 401: Clé API invalide ou expirée')
            print('   🔧 TROUBLESHOOTING:')
            print('     • Vérifiez la clé sur platform.openai.com')
            print('     • Régénérez une nouvelle clé si nécessaire')
            print('     • Vérifiez que le compte a des crédits')
            return False
            
        elif response.status_code == 429:
            print('   ❌ ERREUR 429: Rate limit ou quota dépassé')
            print('   🔧 TROUBLESHOOTING:')
            print('     • Attendez quelques minutes')
            print('     • Vérifiez votre usage sur platform.openai.com')
            print('     • Augmentez vos limites si nécessaire')
            return False
            
        else:
            print(f'   ❌ ERREUR HTTP {response.status_code}')
            print(f'   Réponse: {response.text[:200]}')
            return False
            
    except requests.exceptions.Timeout:
        print('   ❌ TIMEOUT après 15s')
        print('   🔧 TROUBLESHOOTING:')
        print('     • Vérifiez votre connexion internet')
        print('     • Testez: ping api.openai.com')
        print('     • Vérifiez proxy/firewall')
        return False
        
    except requests.exceptions.ConnectionError:
        print('   ❌ ERREUR DE CONNEXION')
        print('   🔧 TROUBLESHOOTING:')
        print('     • Vérifiez votre connexion internet')
        print('     • Vérifiez les paramètres proxy Windows')
        print('     • Testez: curl -I https://api.openai.com')
        print('     • Désactivez temporairement antivirus/firewall')
        return False
        
    except Exception as e:
        print(f'   ❌ ERREUR INATTENDUE: {e}')
        return False
    
    # 3. Test de chat completion
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
            timeout=45
        )
        
        latency_chat = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            choice = data.get('choices', [{}])[0]
            message = choice.get('message', {})
            usage = data.get('usage', {})
            
            print(f'   ✅ OK - Réponse reçue')
            print(f'   Modèle utilisé: {data.get("model")}')
            print(f'   Latence: {round(latency_chat, 2)}ms')
            print(f'   Tokens utilisés: {usage.get("total_tokens", 0)}')
            print(f'   Réponse: "{message.get("content", "").strip()}"')
            print(f'   Finish reason: {choice.get("finish_reason")}')
            
            # Résumé final de succès
            print()
            print('=' * 50)
            print('✅ HEALTHCHECK: OK')
            print(f'Modèle: {data.get("model")}')
            print(f'Latence moyenne: {round((latency_models + latency_chat) / 2, 2)}ms')
            print(f'Timestamp: {timestamp}')
            print('Tous les tests sont passés avec succès!')
            print('OpenAI API est opérationnelle et prête à l\'usage.')
            return True
            
        elif response.status_code == 400:
            print('   ❌ ERREUR 400: Requête malformée')
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            print(f'   Détail: {error_data.get("error", {}).get("message", response.text[:100])}')
            return False
            
        elif response.status_code == 404:
            print(f'   ❌ ERREUR 404: Modèle "{model}" non trouvé')
            print('   🔧 TROUBLESHOOTING:')
            print('     • Utilisez un modèle disponible (gpt-4, gpt-4-turbo, gpt-3.5-turbo)')
            print('     • Vérifiez l\'orthographe du nom du modèle')
            return False
            
        else:
            print(f'   ❌ ERREUR HTTP {response.status_code}')
            print(f'   Réponse: {response.text[:200]}')
            return False
            
    except requests.exceptions.Timeout:
        print('   ❌ TIMEOUT après 45s')
        print('   🔧 TROUBLESHOOTING: Requête trop lente, vérifiez la connexion')
        return False
        
    except Exception as e:
        print(f'   ❌ ERREUR Chat: {e}')
        return False

if __name__ == '__main__':
    success = openai_health_check()
    
    if not success:
        print()
        print('🔧 RECOMMANDATIONS AVANCÉES WINDOWS:')
        print('1. Redémarrez votre terminal en tant qu\'administrateur')
        print('2. Vérifiez les variables d\'environnement: echo %OPENAI_API_KEY%')
        print('3. Testez la connectivité: nslookup api.openai.com')
        print('4. Vérifiez les paramètres proxy: netsh winhttp show proxy')
        print('5. Désactivez temporairement Windows Defender')
        print('6. Essayez avec un VPN si blocage géographique')
        
    input('\nAppuyez sur Entrée pour quitter...')
