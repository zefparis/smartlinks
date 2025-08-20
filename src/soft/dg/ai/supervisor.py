"""
AI Supervisor for SmartLinks DG.

This module provides the core IASupervisor class that orchestrates various
autonomous DG algorithms and provides intelligent decision-making capabilities.
"""

import asyncio
import importlib
import inspect
import json
import logging
import os
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, Union, Callable, Coroutine, TypeVar, Generic
from dataclasses import dataclass, field, asdict
from typing_extensions import Self

from pydantic import BaseModel, Field, validator

from ..models.decision import DecisionContext, Action, ActionStatus
from .openai_factory import openai_factory, OpenAIStatus
from ...config import BASE_DIR

# Type variable for algorithm classes
T = TypeVar('T')

logger = logging.getLogger(__name__)

class OperationMode(str, Enum):
    """Operation modes for the AI Supervisor."""
    AUTO = "auto"      # Autonomous mode - takes actions automatically
    MANUAL = "manual"  # Manual mode - requires human approval for actions
    SANDBOX = "sandbox" # Sandbox mode - simulates actions without executing them

class SupervisorState(BaseModel):
    """Current state of the AI Supervisor."""
    mode: OperationMode = Field(default=OperationMode.AUTO)
    last_analysis_time: Optional[datetime] = None
    last_action_time: Optional[datetime] = None
    active_actions: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

class AlgorithmRegistry:
    """Manages registration and discovery of DG algorithms."""
    
    def __init__(self, base_project_dir: str):
        self._algorithms: Dict[str, Type] = {}
        self._instances: Dict[str, Any] = {}
        self._base_dir = Path(base_project_dir)
    
    def register(self, algorithm_class: Type) -> None:
        """Register an algorithm class."""
        if not hasattr(algorithm_class, 'get_name'):
            raise ValueError("Algorithm class must implement get_name() class method")
        
        name = algorithm_class.get_name()
        self._algorithms[name] = algorithm_class
        logger.info(f"Registered algorithm: {name}")
    
    def get_algorithm(self, name: str) -> Any:
        """Get an instance of the specified algorithm (creates if not exists)."""
        if name not in self._algorithms:
            raise ValueError(f"Algorithm not found: {name}")
        
        if name not in self._instances:
            self._instances[name] = self._algorithms[name]()
            
        return self._instances[name]
    
    def get_available_algorithms(self) -> List[str]:
        """Get a list of all registered algorithm names."""
        return list(self._algorithms.keys())
    
    def load_algorithms_from_path(self, path: str) -> None:
        """Dynamically load algorithms from a directory."""
        algo_dir = Path(path)
        if not algo_dir.exists() or not algo_dir.is_dir():
            logger.warning(f"Algorithm directory not found: {path}")
            return

        # Walk through all Python files in the directory
        for py_file in algo_dir.rglob("*.py"):
            # Skip __init__.py and files starting with _
            if py_file.name.startswith('_') or py_file.name == '__init__.py':
                continue

            # Convert file path to a module path relative to the project's base directory
            try:
                # self._base_dir is the project root, e.g., c:\smartlinks-autopilot
                # py_file is the full path to the algorithm file
                rel_path = py_file.relative_to(self._base_dir)
                module_path = str(rel_path.with_suffix('')).replace(os.sep, '.')
            except ValueError:
                logger.error(f"Could not determine module path for {py_file} relative to {self._base_dir}")
                continue

            try:
                logger.debug(f"Attempting to load module: {module_path}")
                module = importlib.import_module(module_path)

                # Find all classes that look like algorithms
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        obj.__module__ == module_path and  # Ensure class is defined in this module
                        hasattr(obj, 'get_name') and hasattr(obj, 'execute') and
                        inspect.iscoroutinefunction(obj.execute)
                    ):
                        # Register the algorithm
                        self.register(obj)
                        logger.debug(f"Discovered algorithm: {obj.get_name()} from {module_path}.{name}")

            except ImportError as e:
                logger.error(f"Failed to import module {module_path}: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error processing module {module_path}: {e}", exc_info=True)

class IASupervisor:
    """AI Supervisor that orchestrates autonomous DG algorithms."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4-1106-preview",
        algorithm_paths: Optional[List[str]] = None,
        initial_mode: OperationMode = OperationMode.AUTO
    ):
        """Initialize the AI Supervisor.
        
        Args:
            openai_api_key: OpenAI API key. If not provided, will try to load from environment.
            openai_model: The OpenAI model to use.
            algorithm_paths: List of paths to search for algorithms.
            initial_mode: Initial operation mode.
        """
        # Initialize state
        self.state = SupervisorState(mode=initial_mode)
        
        # Initialize OpenAI integration via factory
        self.openai_factory = openai_factory
        self._degraded_mode = False
        
        # Initialize algorithm registry
        self.registry = AlgorithmRegistry(base_project_dir=BASE_DIR)
        
        # Default algorithm paths if none provided
        if algorithm_paths is None:
            base_dir = Path(__file__).parent.parent
            algorithm_paths = [
                str(base_dir / "algorithms"),
                str(base_dir / "algorithms" / "security"),
                str(base_dir / "algorithms" / "optimization"),
                str(base_dir / "algorithms" / "maintenance"),
                str(base_dir / "algorithms" / "simulation"),
            ]
        
        # Load algorithms from specified paths
        for path in algorithm_paths:
            self.registry.load_algorithms_from_path(path)
        
        logger.info(f"Initialized AI Supervisor with {len(self.registry.get_available_algorithms())} algorithms")
    
    async def analyze_system(self, context: Optional[DecisionContext] = None) -> Dict[str, Any]:
        """Perform a comprehensive system analysis.
        
        Args:
            context: Optional decision context. If not provided, a new one will be created.
            
        Returns:
            Dictionary containing analysis results.
        """
        if context is None:
            context = DecisionContext()
        
        logger.info("Starting system analysis...")
        
        # Run all registered algorithms
        results = {}
        for algo_name in self.registry.get_available_algorithms():
            try:
                algo = self.registry.get_algorithm(algo_name)
                result = await algo.execute(context, {})
                results[algo_name] = result.dict()
                logger.debug(f"Executed algorithm {algo_name}: {result.summary}")
            except Exception as e:
                logger.error(f"Error executing algorithm {algo_name}: {e}", exc_info=True)
                results[algo_name] = {"error": str(e)}
        
        # Update state
        self.state.last_analysis_time = datetime.utcnow()
        
        # Get AI-powered analysis of results
        ai_analysis = await self._get_ai_analysis({
            "timestamp": datetime.utcnow().isoformat(),
            "algorithm_results": results,
            "system_state": self.state.dict()
        }, "anomaly")
        
        # Update state with analysis results
        self.state.metrics.update({
            "last_analysis": {
                "timestamp": self.state.last_analysis_time.isoformat(),
                "algorithms_executed": len(results),
                "ai_analysis": ai_analysis
            }
        })
        
        logger.info("System analysis completed")
        
        return {
            "timestamp": self.state.last_analysis_time.isoformat(),
            "algorithms_executed": list(results.keys()),
            "results": results,
            "ai_analysis": ai_analysis,
            "recommended_actions": self._extract_recommended_actions(results)
        }
    
    async def fix_detected_issues(self, context: Optional[DecisionContext] = None) -> Dict[str, Any]:
        """Fix all detected issues based on the current system state.
        
        Args:
            context: Optional decision context. If not provided, a new one will be created.
            
        Returns:
            Dictionary containing fix results.
        """
        if context is None:
            context = DecisionContext()
        
        if self.state.mode == OperationMode.MANUAL:
            logger.warning("Cannot fix issues in manual mode. Switch to auto or sandbox mode.")
            return {"status": "error", "message": "Cannot fix issues in manual mode"}
        
        logger.info("Starting to fix detected issues...")
        
        # First, analyze the system to detect issues
        analysis = await self.analyze_system(context)
        
        # Extract recommended actions
        actions = self._extract_recommended_actions(analysis["results"])
        
        # Execute actions based on mode
        results = []
        for action in actions:
            try:
                if self.state.mode == OperationMode.SANDBOX:
                    logger.info(f"[SANDBOX] Would execute action: {action}")
                    result = {"status": "simulated", "action": action}
                else:
                    logger.info(f"Executing action: {action}")
                    # In a real implementation, this would execute the action
                    result = await self._execute_action(action, context)
                    
                    # Update state
                    self.state.last_action_time = datetime.utcnow()
                    self.state.active_actions.append({
                        "action": action,
                        "timestamp": self.state.last_action_time.isoformat(),
                        "status": "completed"
                    })
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error executing action {action}: {e}", exc_info=True)
                results.append({
                    "status": "error",
                    "action": action,
                    "error": str(e)
                })
        
        logger.info(f"Completed fixing issues. {len(results)} actions executed.")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "actions_executed": len(results),
            "results": results
        }
    
    async def ask(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Ask the AI Supervisor a question and get a response.
        
        Args:
            question: The question to ask
            context: Optional context information
            
        Returns:
            The AI's response
        """
        logger.info(f"Processing question: {question}")
        
        # Force initialization of OpenAI factory
        await self.openai_factory.get_client()
        
        # Build context for the AI
        full_context = {
            "question": question,
            "system_state": asdict(self.state),
            "available_algorithms": [alg.get_name() if alg else None for alg in self.algorithms.get_all()],
            "current_time": datetime.utcnow().isoformat()
        }
        
        if context:
            full_context.update(context)
        
        # Create a comprehensive system prompt
        system_prompt = f"""You are the SmartLinks AI Supervisor, an intelligent system that manages autonomous algorithms for digital marketing optimization.

Current System State:
- Mode: {self.state.mode.value}
- Available Algorithms: {len(self.algorithms.get_all())} algorithms loaded
- Last Analysis: {self.state.last_analysis_time or 'Never'}
- Active Actions: {len(self.state.active_actions)} running

Your role is to:
1. Answer questions about the system status and performance
2. Recommend actions based on data analysis
3. Coordinate algorithm execution
4. Provide insights and explanations

Be helpful, concise, and technical when appropriate. If asked about specific algorithms or actions, provide detailed information."""
        
        # Get AI response
        response = await self._ask_ai(
            prompt=question,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Log the interaction
        self._log_interaction("question", question, response, full_context)
        
        return response
    
    def set_mode(self, mode: Union[OperationMode, str]) -> None:
        """Set the operation mode of the supervisor.
        
        Args:
            mode: The operation mode to set (auto, manual, or sandbox).
        """
        if isinstance(mode, str):
            mode = OperationMode(mode.lower())
        
        logger.info(f"Changing operation mode from {self.state.mode} to {mode}")
        self.state.mode = mode
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the supervisor."""
        try:
            algos = getattr(self, "registry", None)
            if algos and hasattr(algos, "get_available_algorithms"):
                available = algos.get_available_algorithms()
                available = sorted([str(k) for k in available]) if isinstance(available, list) else []
            else:
                available = []
        except Exception:
            available = []

        try:
            raw_log = self.state.metrics.get("interaction_log", []) if hasattr(self.state, "metrics") else []
            interaction_log = []
            for e in raw_log[-200:]:
                if isinstance(e, dict):
                    interaction_log.append(e)
                else:
                    interaction_log.append({"ts": datetime.utcnow().isoformat(), "event": str(e)})
        except Exception:
            interaction_log = []

        try:
            metrics = self.state.metrics if hasattr(self.state, "metrics") and self.state.metrics else {}
            metrics["interaction_log"] = interaction_log
        except Exception:
            metrics = {"interaction_log": interaction_log}

        return {
            "mode": getattr(self.state, "mode", OperationMode.MANUAL).value if hasattr(self.state, "mode") else "manual",
            "last_analysis_time": self.state.last_analysis_time.isoformat() if hasattr(self.state, "last_analysis_time") and self.state.last_analysis_time else None,
            "last_action_time": self.state.last_action_time.isoformat() if hasattr(self.state, "last_action_time") and self.state.last_action_time else None,
            "active_actions": len(getattr(self.state, "active_actions", [])),
            "available_algorithms": available,
            "metrics": metrics
        }
    
    def _extract_recommended_actions(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract recommended actions from algorithm results."""
        actions = []
        
        for algo_name, result in results.items():
            if isinstance(result, dict) and "recommended_actions" in result:
                for action in result["recommended_actions"]:
                    if isinstance(action, dict):
                        action["source_algorithm"] = algo_name
                        actions.append(action)
                    elif hasattr(action, "dict"):
                        action_dict = action.dict()
                        action_dict["source_algorithm"] = algo_name
                        actions.append(action_dict)
        
        return actions
    
    async def _execute_action(self, action: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """Execute a recommended action.
        
        In a real implementation, this would map action types to specific functions
        that know how to execute them.
        """
        # This is a simplified implementation
        action_type = action.get("action_type", "")
        
        # Simulate action execution
        await asyncio.sleep(0.1)  # Simulate work
        
        return {
            "status": "success",
            "action": action,
            "result": f"Successfully executed {action_type}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _log_interaction(self, type: str, content: str, response: str, context: Dict[str, Any]) -> None:
        """Log an interaction with the supervisor."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": type,
            "content": content,
            "response": response,
            "context": context
        }
        
        # In a real implementation, this would save to a database or log file
        logger.info(f"Interaction logged: {json.dumps(log_entry, default=str)}")
        
        # Keep a limited history in memory
        if len(self.state.metrics.get("interaction_log", [])) > 100:  # Keep last 100 interactions
            self.state.metrics["interaction_log"] = self.state.metrics["interaction_log"][-99:]
        
        if "interaction_log" not in self.state.metrics:
            self.state.metrics["interaction_log"] = []
            
        self.state.metrics["interaction_log"].append(log_entry)
    
    async def _ask_ai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """
        Demande une réponse à l'IA avec gestion du mode dégradé.
        
        Args:
            prompt: Question ou instruction
            system_prompt: Prompt système optionnel
            temperature: Température (0.0 à 1.0)
            max_tokens: Nombre max de tokens
            **kwargs: Arguments supplémentaires
            
        Returns:
            Réponse de l'IA ou message de mode dégradé
        """
        try:
            # Force initialization and check availability
            client = await self.openai_factory.get_client()
            if not client:
                self._degraded_mode = True
                logger.warning("OpenAI client unavailable, activating degraded mode")
                return "IA temporairement indisponible. Veuillez réessayer dans quelques instants."
            
            if not self.openai_factory.is_available():
                self._degraded_mode = True
                logger.warning("OpenAI indisponible, mode dégradé activé")
                return "IA temporairement indisponible. Veuillez réessayer dans quelques instants."
            
            # Préparation des messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Appel à OpenAI via la factory avec timeout
            response = await asyncio.wait_for(
                self.openai_factory.ask_with_retry(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                ),
                timeout=30.0  # 30 seconds timeout
            )
            
            self._degraded_mode = False
            return response
            
        except asyncio.TimeoutError:
            self._degraded_mode = True
            logger.error("OpenAI request timed out after 30 seconds")
            return "Désolé, la requête a pris trop de temps. Veuillez réessayer avec une question plus simple."
            
        except Exception as e:
            self._degraded_mode = True
            logger.error(f"Erreur lors de l'appel OpenAI: {e}", exc_info=True)
            return f"Erreur IA: {str(e)[:100]}... Veuillez réessayer."
    
    async def _get_ai_analysis(
        self,
        context: Dict[str, Any],
        analysis_type: str = "generic"
    ) -> Dict[str, Any]:
        """
        Obtient une analyse IA du contexte avec gestion du mode dégradé.
        
        Args:
            context: Contexte à analyser
            analysis_type: Type d'analyse (anomaly, optimization, etc.)
            
        Returns:
            Dictionnaire avec l'analyse ou réponse dégradée
        """
        if not self.openai_factory.is_available():
            self._degraded_mode = True
            return {
                "summary": "Analyse IA indisponible",
                "key_findings": ["OpenAI non configuré ou inaccessible"],
                "recommendations": ["Configurer la clé API OpenAI"],
                "confidence_score": 0.0,
                "immediate_actions": [],
                "long_term_actions": ["Vérifier la configuration OpenAI"]
            }
        
        # Prompts système selon le type d'analyse
        system_prompts = {
            "anomaly": (
                "Tu es un assistant IA spécialisé dans la détection d'anomalies. "
                "Analyse les métriques système et logs fournis pour identifier des anomalies, "
                "leur impact potentiel, et recommander des actions. Réponds en français."
            ),
            "optimization": (
                "Tu es un assistant IA spécialisé dans l'optimisation de performance. "
                "Analyse les métriques système et configuration pour identifier des "
                "opportunités d'optimisation et recommander des actions spécifiques. Réponds en français."
            ),
            "reporting": (
                "Tu es un assistant IA spécialisé dans la génération de rapports clairs et concis. "
                "Résume les points clés et fournis des recommandations basées sur les données. "
                "Réponds en français."
            ),
            "generic": (
                "Tu es un assistant IA utile. Analyse les informations fournies et "
                "donne une réponse claire et concise en français."
            )
        }
        
        system_prompt = system_prompts.get(analysis_type, system_prompts["generic"])
        
        # Conversion du contexte en texte formaté
        import json
        context_str = json.dumps(context, indent=2, default=str, ensure_ascii=False)
        
        prompt = (
            f"Analyse le contexte {analysis_type} suivant et fournis des insights:\n\n"
            f"{context_str}\n\n"
            "Fournis ton analyse au format JSON suivant:\n"
            "{\n"
            "  \"summary\": \"Résumé bref de l'analyse\",\n"
            "  \"key_findings\": [\"liste\", \"des\", \"découvertes\", \"clés\"],\n"
            "  \"recommendations\": [\"liste\", \"des\", \"recommandations\"],\n"
            "  \"confidence_score\": 0.0,\n"
            "  \"immediate_actions\": [\"actions\", \"immédiates\"],\n"
            "  \"long_term_actions\": [\"actions\", \"long\", \"terme\"]\n"
            "}"
        )
        
        response = await self._ask_ai(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format={"type": "json_object"}
        )
        
        # Parsing de la réponse JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Échec parsing JSON de l'analyse IA")
            return {
                "summary": "Analyse IA partiellement disponible",
                "key_findings": ["Erreur de format dans la réponse IA"],
                "recommendations": ["Réessayer l'analyse"],
                "confidence_score": 0.5,
                "immediate_actions": [],
                "long_term_actions": [],
                "raw_response": response
            }
    
    async def selfcheck(self) -> Dict[str, Any]:
        """
        Effectue un diagnostic complet de l'IA Supervisor.
        
        Returns:
            Dictionnaire avec le statut et diagnostic détaillé
        """
        logger.info("Démarrage selfcheck IA Supervisor...")
        
        selfcheck_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "supervisor_status": {
                "mode": self.state.mode.value,
                "degraded_mode": self._degraded_mode,
                "algorithms_count": len(self.registry.get_available_algorithms()),
                "last_analysis": self.state.last_analysis_time.isoformat() if self.state.last_analysis_time else None
            },
            "openai_status": {},
            "tests": {}
        }
        
        # Test OpenAI
        openai_check = await self.openai_factory.selfcheck()
        selfcheck_results["openai_status"] = openai_check
        
        # Test algorithmes
        algorithms = self.registry.get_available_algorithms()
        selfcheck_results["tests"]["algorithms"] = {
            "count": len(algorithms),
            "list": algorithms,
            "passed": len(algorithms) > 0,
            "message": f"{len(algorithms)} algorithmes chargés" if algorithms else "Aucun algorithme trouvé"
        }
        
        # Test analyse simple
        try:
            test_context = {"test": "selfcheck", "timestamp": datetime.utcnow().isoformat()}
            test_analysis = await self._get_ai_analysis(test_context, "generic")
            
            selfcheck_results["tests"]["analysis"] = {
                "passed": bool(test_analysis.get("summary")),
                "message": "Analyse IA fonctionnelle" if test_analysis.get("summary") else "Analyse IA échouée"
            }
        except Exception as e:
            selfcheck_results["tests"]["analysis"] = {
                "passed": False,
                "message": f"Erreur test analyse: {str(e)}"
            }
        
        # Test question simple
        try:
            test_response = await self._ask_ai("Test de fonctionnement, réponds simplement 'OK'.")
            selfcheck_results["tests"]["question"] = {
                "passed": bool(test_response and "indisponible" not in test_response.lower()),
                "message": f"Réponse: {test_response[:50]}..." if test_response else "Pas de réponse"
            }
        except Exception as e:
            selfcheck_results["tests"]["question"] = {
                "passed": False,
                "message": f"Erreur test question: {str(e)}"
            }
        
        # Statut global
        all_tests_passed = all(
            test.get("passed", False) for test in selfcheck_results["tests"].values()
        )
        openai_ready = openai_check.get("status") == "ready"
        
        if all_tests_passed and openai_ready:
            selfcheck_results["global_status"] = "ready"
        elif openai_check.get("status") in ["ready", "degraded"]:
            selfcheck_results["global_status"] = "degraded"
        else:
            selfcheck_results["global_status"] = "unavailable"
        
        logger.info(f"Selfcheck terminé: {selfcheck_results['global_status']}")
        return selfcheck_results
    
    def is_ready(self) -> bool:
        """Vérifie si l'IA Supervisor est prêt à fonctionner."""
        return self.openai_factory.is_available() and not self._degraded_mode
