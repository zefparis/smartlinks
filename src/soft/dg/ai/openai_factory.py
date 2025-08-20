"""
Factory pour la création et gestion des clients OpenAI.

Implémente un pattern Singleton/Factory pour la gestion robuste des clients OpenAI
avec gestion d'erreurs, timeouts, et mode dégradé.
"""
import asyncio
import logging
import os
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
from enum import Enum

try:
    from openai import AsyncOpenAI
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None
    openai = None
    logging.warning("Module openai non installé. Fonctionnement en mode dégradé.")

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class OpenAIStatus(str, Enum):
    """Statut de la connexion OpenAI."""
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    ERROR = "error"

class OpenAIClientFactory:
    """
    Factory pour créer et gérer les clients OpenAI avec gestion d'erreurs robuste.
    
    Fonctionnalités:
    - Pattern Singleton pour éviter les multiples instances
    - Gestion des timeouts et retry automatique
    - Mode dégradé si OpenAI indisponible
    - Selfcheck de connectivité
    - Support O3 High Reasoning et GPT-4o
    """
    
    _instance: Optional['OpenAIClientFactory'] = None
    _client: Optional[AsyncOpenAI] = None
    _status: OpenAIStatus = OpenAIStatus.UNAVAILABLE
    _last_check: Optional[datetime] = None
    _error_message: Optional[str] = None
    
    def __new__(cls) -> 'OpenAIClientFactory':
        """Implémentation Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialise la factory (une seule fois grâce au Singleton)."""
        if hasattr(self, '_initialized'):
            return
        
        load_dotenv()
        self._initialized = True
        self._api_key = None
        self._model = None
        self._base_url = None
        self._timeout = 30.0
        self._max_retries = 3
        
        # Configuration depuis l'environnement
        self._load_config()
        
        # Initialisation différée - sera appelée lors du premier accès
        self._initialization_started = False
    
    def _load_config(self) -> None:
        """Charge la configuration depuis les variables d'environnement."""
        self._api_key = os.getenv("OPENAI_API_KEY")
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self._base_url = os.getenv("OPENAI_API_BASE")
        
        # Support O3 High Reasoning
        if self._model == "o3-high-reasoning":
            # O3 pas encore disponible, fallback sur GPT-4o
            logger.info("O3 High Reasoning demandé, fallback sur GPT-4o")
            self._model = "gpt-4o"
        
        logger.info(f"Configuration OpenAI: model={self._model}, base_url={self._base_url}")
    
    async def _initialize_client(self) -> None:
        """Initialise le client OpenAI de manière asynchrone."""
        try:
            if not OPENAI_AVAILABLE:
                self._status = OpenAIStatus.UNAVAILABLE
                self._error_message = "Module openai non installé. Installez avec: pip install openai>=1.40.0"
                logger.warning(self._error_message)
                return
                
            if not self._api_key:
                self._status = OpenAIStatus.UNAVAILABLE
                self._error_message = "Clé API OpenAI manquante dans .env"
                logger.warning(self._error_message)
                return
            
            # Création du client
            client_kwargs = {"api_key": self._api_key}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url.rstrip("/")
            
            self._client = AsyncOpenAI(**client_kwargs)
            
            # Test de connectivité
            await self._test_connectivity()
            
        except Exception as e:
            self._status = OpenAIStatus.ERROR
            self._error_message = f"Erreur initialisation OpenAI: {str(e)}"
            logger.error(self._error_message, exc_info=True)
    
    async def _test_connectivity(self) -> bool:
        """Teste la connectivité avec OpenAI."""
        try:
            if not self._client:
                return False
            
            # Test simple avec un prompt minimal
            response = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=1
                ),
                timeout=self._timeout
            )
            
            if response and response.choices:
                self._status = OpenAIStatus.READY
                self._error_message = None
                self._last_check = datetime.utcnow()
                logger.info("Test connectivité OpenAI: OK")
                return True
            
        except Exception as e:
            if OPENAI_AVAILABLE and hasattr(openai, 'AuthenticationError') and isinstance(e, openai.AuthenticationError):
                self._status = OpenAIStatus.ERROR
                self._error_message = "Clé API OpenAI invalide"
                logger.error(self._error_message)
            elif OPENAI_AVAILABLE and hasattr(openai, 'RateLimitError') and isinstance(e, openai.RateLimitError):
                self._status = OpenAIStatus.DEGRADED
                self._error_message = "Limite de taux OpenAI atteinte"
                logger.warning(self._error_message)
            elif isinstance(e, asyncio.TimeoutError):
                self._status = OpenAIStatus.DEGRADED
                self._error_message = "Timeout connexion OpenAI"
                logger.warning(self._error_message)
            else:
                self._status = OpenAIStatus.ERROR
                self._error_message = f"Erreur test connectivité: {str(e)}"
                logger.error(self._error_message, exc_info=True)
        
        return False
    
    async def get_client(self) -> Optional[AsyncOpenAI]:
        """
        Retourne le client OpenAI si disponible.
        
        Returns:
            Client OpenAI ou None si indisponible
        """
        # Initialisation différée si pas encore faite
        if not self._initialization_started:
            self._initialization_started = True
            await self._initialize_client()
        
        # Vérification périodique (toutes les 5 minutes)
        if (self._last_check is None or 
            datetime.utcnow() - self._last_check > timedelta(minutes=5)):
            await self._test_connectivity()
        
        if self._status in [OpenAIStatus.READY, OpenAIStatus.DEGRADED]:
            return self._client
        
        return None
    
    async def ask_with_retry(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Optional[str]:
        """
        Envoie une requête à OpenAI avec retry automatique.
        
        Args:
            messages: Messages à envoyer
            temperature: Température (0.0 à 1.0)
            max_tokens: Nombre max de tokens
            **kwargs: Arguments supplémentaires
            
        Returns:
            Réponse de l'IA ou None si échec
        """
        client = await self.get_client()
        if not client:
            logger.warning("Client OpenAI indisponible")
            return None
        
        for attempt in range(self._max_retries):
            try:
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=self._model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    ),
                    timeout=self._timeout
                )
                
                if response and response.choices:
                    return response.choices[0].message.content
                
            except Exception as e:
                if OPENAI_AVAILABLE and hasattr(openai, 'RateLimitError') and isinstance(e, openai.RateLimitError):
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limit atteint, attente {wait_time}s (tentative {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                elif isinstance(e, asyncio.TimeoutError):
                    logger.warning(f"Timeout tentative {attempt + 1}")
                    continue
                else:
                    logger.error(f"Erreur requête OpenAI (tentative {attempt + 1}): {e}")
                    if attempt == self._max_retries - 1:
                        self._status = OpenAIStatus.ERROR
                        self._error_message = str(e)
                    continue
        
        return None
    
    async def selfcheck(self) -> Dict[str, Any]:
        """
        Effectue un diagnostic complet de l'intégration OpenAI.
        
        Returns:
            Dictionnaire avec le statut et les détails du diagnostic
        """
        logger.info("Démarrage selfcheck OpenAI...")
        
        check_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": self._status.value,
            "model": self._model,
            "api_key_configured": bool(self._api_key),
            "base_url": self._base_url,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "error_message": self._error_message,
            "tests": {}
        }
        
        # Test 1: Configuration
        check_results["tests"]["config"] = {
            "passed": bool(self._api_key) and OPENAI_AVAILABLE,
            "message": "Clé API configurée" if self._api_key and OPENAI_AVAILABLE else 
                      "Module openai manquant" if not OPENAI_AVAILABLE else "Clé API manquante"
        }
        
        # Test 2: Connectivité
        connectivity_ok = await self._test_connectivity()
        check_results["tests"]["connectivity"] = {
            "passed": connectivity_ok,
            "message": "Connexion OK" if connectivity_ok else self._error_message
        }
        
        # Test 3: Requête simple
        if connectivity_ok:
            test_response = await self.ask_with_retry([
                {"role": "user", "content": "Réponds simplement 'OK' pour confirmer le fonctionnement."}
            ], max_tokens=10)
            
            check_results["tests"]["simple_request"] = {
                "passed": bool(test_response),
                "message": f"Réponse: {test_response}" if test_response else "Échec requête test"
            }
        else:
            check_results["tests"]["simple_request"] = {
                "passed": False,
                "message": "Non testé (connectivité échouée)"
            }
        
        # Mise à jour du statut global
        all_tests_passed = all(test["passed"] for test in check_results["tests"].values())
        if all_tests_passed:
            self._status = OpenAIStatus.READY
            check_results["status"] = OpenAIStatus.READY.value
        elif check_results["tests"]["config"]["passed"]:
            self._status = OpenAIStatus.DEGRADED
            check_results["status"] = OpenAIStatus.DEGRADED.value
        else:
            self._status = OpenAIStatus.UNAVAILABLE
            check_results["status"] = OpenAIStatus.UNAVAILABLE.value
        
        logger.info(f"Selfcheck terminé: {check_results['status']}")
        return check_results
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut actuel de l'intégration OpenAI."""
        return {
            "status": self._status.value,
            "model": self._model,
            "api_key_configured": bool(self._api_key),
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "error_message": self._error_message
        }
    
    def is_available(self) -> bool:
        """Vérifie si OpenAI est disponible."""
        return self._status in [OpenAIStatus.READY, OpenAIStatus.DEGRADED]

# Instance globale (Singleton)
openai_factory = OpenAIClientFactory()

async def get_openai_client() -> Optional[AsyncOpenAI]:
    """Helper pour récupérer le client OpenAI."""
    return await openai_factory.get_client()

def get_openai_status() -> Dict[str, Any]:
    """Helper pour récupérer le statut OpenAI."""
    return openai_factory.get_status()
