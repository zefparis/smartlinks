#!/usr/bin/env python3
"""
OpenAI API Health Check - Diagnostic complet de connectivité
"""
import os
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class OpenAIHealthCheck:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def validate_api_key(self):
        """Valide le format de la clé API"""
        if not self.api_key:
            return False, "Clé API manquante"
        
        if not self.api_key.startswith("sk-"):
            return False, "Format de clé invalide (doit commencer par sk-)"
            
        if len(self.api_key) < 50:
            return False, "Clé API trop courte"
            
        return True, "Format de clé valide"
    
    def test_models_endpoint(self):
        """Test de l'endpoint /v1/models"""
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=10
            )
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                models_data = response.json()
                available_models = [m["id"] for m in models_data.get("data", [])]
                gpt4_models = [m for m in available_models if "gpt-4" in m]
                
                return True, {
                    "status": "OK",
                    "latency_ms": round(latency, 2),
                    "total_models": len(available_models),
                    "gpt4_models": gpt4_models[:5],  # Top 5 GPT-4 models
                    "target_model_available": self.model in available_models
                }
            else:
                return False, {
                    "status": "ERROR",
                    "http_code": response.status_code,
                    "error": response.text,
                    "latency_ms": round(latency, 2)
                }
                
        except requests.exceptions.Timeout:
            return False, {"status": "TIMEOUT", "error": "Timeout après 10s"}
        except requests.exceptions.ConnectionError:
            return False, {"status": "CONNECTION_ERROR", "error": "Impossible de se connecter à OpenAI"}
        except Exception as e:
            return False, {"status": "EXCEPTION", "error": str(e)}
    
    def test_chat_completion(self):
        """Test d'une requête de chat completion"""
        try:
            start_time = time.time()
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Tu es un assistant de test. Réponds brièvement."},
                    {"role": "user", "content": "Dis juste 'Test OK' si tu reçois ce message."}
                ],
                "max_tokens": 10,
                "temperature": 0
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                
                return True, {
                    "status": "OK",
                    "model_used": data.get("model"),
                    "response": message.get("content", "").strip(),
                    "latency_ms": round(latency, 2),
                    "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                    "finish_reason": choice.get("finish_reason")
                }
            else:
                return False, {
                    "status": "ERROR",
                    "http_code": response.status_code,
                    "error": response.text,
                    "latency_ms": round(latency, 2)
                }
                
        except requests.exceptions.Timeout:
            return False, {"status": "TIMEOUT", "error": "Timeout après 30s"}
        except requests.exceptions.ConnectionError:
            return False, {"status": "CONNECTION_ERROR", "error": "Impossible de se connecter à OpenAI"}
        except Exception as e:
            return False, {"status": "EXCEPTION", "error": str(e)}
    
    def run_full_diagnostic(self):
        """Exécute le diagnostic complet"""
        print("🔍 OPENAI API HEALTH CHECK")
        print("=" * 50)
        
        timestamp = datetime.now().isoformat()
        print(f"Timestamp: {timestamp}")
        print(f"Modèle cible: {self.model}")
        print()
        
        # 1. Validation de la clé
        print("1. Validation de la clé API...")
        key_valid, key_msg = self.validate_api_key()
        print(f"   {key_msg}")
        
        if not key_valid:
            print("\n❌ HEALTHCHECK: FAILED - Clé API invalide")
            return
        
        # 2. Test de l'endpoint models
        print("\n2. Test de l'endpoint /v1/models...")
        models_ok, models_result = self.test_models_endpoint()
        
        if models_ok:
            print(f"   ✅ OK - {models_result['total_models']} modèles disponibles")
            print(f"   Latence: {models_result['latency_ms']}ms")
            print(f"   Modèle cible disponible: {'✅' if models_result['target_model_available'] else '❌'}")
            if models_result['gpt4_models']:
                print(f"   GPT-4 disponibles: {', '.join(models_result['gpt4_models'])}")
        else:
            print(f"   ❌ ERREUR: {models_result}")
            self._print_troubleshooting(models_result)
            return
        
        # 3. Test de chat completion
        print("\n3. Test de chat completion...")
        chat_ok, chat_result = self.test_chat_completion()
        
        if chat_ok:
            print(f"   ✅ OK - Réponse reçue")
            print(f"   Modèle utilisé: {chat_result['model_used']}")
            print(f"   Latence: {chat_result['latency_ms']}ms")
            print(f"   Tokens utilisés: {chat_result['tokens_used']}")
            print(f"   Réponse: '{chat_result['response']}'")
        else:
            print(f"   ❌ ERREUR: {chat_result}")
            self._print_troubleshooting(chat_result)
            return
        
        # Résumé final
        print("\n" + "=" * 50)
        print("✅ HEALTHCHECK: OK")
        print(f"Modèle: {chat_result.get('model_used', self.model)}")
        print(f"Latence moyenne: {round((models_result['latency_ms'] + chat_result['latency_ms']) / 2, 2)}ms")
        print(f"Timestamp: {timestamp}")
        print("Tous les tests sont passés avec succès!")
    
    def _print_troubleshooting(self, error_result):
        """Affiche les recommandations de troubleshooting"""
        print("\n🔧 TROUBLESHOOTING:")
        
        status = error_result.get("status", "")
        http_code = error_result.get("http_code")
        
        if status == "CONNECTION_ERROR":
            print("   • Vérifiez votre connexion internet")
            print("   • Vérifiez les paramètres proxy/firewall")
            print("   • Essayez: curl -I https://api.openai.com")
            
        elif status == "TIMEOUT":
            print("   • Connexion trop lente")
            print("   • Augmentez le timeout")
            print("   • Vérifiez la latence réseau")
            
        elif http_code == 401:
            print("   • Clé API invalide ou expirée")
            print("   • Vérifiez la clé dans votre compte OpenAI")
            print("   • Régénérez une nouvelle clé si nécessaire")
            
        elif http_code == 429:
            print("   • Quota dépassé ou rate limit")
            print("   • Attendez quelques minutes")
            print("   • Vérifiez votre usage sur platform.openai.com")
            
        elif http_code == 403:
            print("   • Accès refusé")
            print("   • Vérifiez les permissions de votre clé")
            print("   • Contactez le support OpenAI")
            
        else:
            print(f"   • Erreur HTTP {http_code}")
            print("   • Consultez la documentation OpenAI")
            print("   • Vérifiez les logs détaillés")

def main():
    checker = OpenAIHealthCheck()
    checker.run_full_diagnostic()

if __name__ == "__main__":
    main()
