from __future__ import annotations
import os
import yaml
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv

# Determine the project root and load the .env file explicitly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=dotenv_path)


# Localisation flexible de policy.yaml (racine ou sous-dossier src)
_POLICY_CANDIDATES = [
    os.path.join(BASE_DIR, "policy.yaml"),
    os.path.join(BASE_DIR, "src", "policy.yaml"),
]

@dataclass
class Policy:
    version: str
    fraud_threshold: float
    fraud_weights: dict
    bandit_algo: str
    epsilon: float
    min_volume_segment: int
    alpha: float
    buffer_eur: float
    min_eur: float
    max_eur: float
    k_sigma: float
    k_fraud: float
    max_payout_day_global_eur: float
    max_payout_day_creator_eur: float
    base_hold_days: int

def load_policy(path: str | None = None) -> Policy:
    # Determine path if not provided
    candidate = None
    if path:
        candidate = path
    else:
        for p in _POLICY_CANDIDATES:
            if os.path.exists(p):
                candidate = p
                break
    if not candidate:
        raise FileNotFoundError(
            f"Policy file not found. Tried: {', '.join(_POLICY_CANDIDATES)}"
        )
    with open(candidate, "r", encoding="utf-8") as f:
        y = yaml.safe_load(f)
    return Policy(
        version=str(y.get("version")),
        fraud_threshold=float(y["fraud"]["threshold"]),
        fraud_weights=dict(y["fraud"]["weights"]),
        bandit_algo=str(y["bandit"]["algo"]),
        epsilon=float(y["bandit"]["epsilon"]),
        min_volume_segment=int(y["bandit"]["min_volume_segment"]),
        alpha=float(y["payout"]["alpha"]),
        buffer_eur=float(y["payout"]["buffer_eur"]),
        min_eur=float(y["payout"]["min_eur"]),
        max_eur=float(y["payout"]["max_eur"]),
        k_sigma=float(y["risk"]["k_sigma"]),
        k_fraud=float(y["risk"]["k_fraud"]),
        max_payout_day_global_eur=float(y["budget"]["max_payout_day_global_eur"]),
        max_payout_day_creator_eur=float(y["budget"]["max_payout_day_creator_eur"]),
        base_hold_days=int(y["hold"]["base_days"]),
    )

# DB et serveur
DB_PATH = os.getenv("SMARTLINKS_DB", os.path.join(BASE_DIR, "smartlinks.db"))
HOST = os.getenv("SMARTLINKS_HOST", "127.0.0.1")
PORT = int(os.getenv("SMARTLINKS_PORT", "8000"))
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "")

# AI Supervisor Configuration
@dataclass
class AISupervisorConfig:
    """Configuration for the AI Supervisor."""
    # OpenAI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4-1106-preview")
    
    # Operation mode (auto, manual, sandbox)
    default_mode: str = os.getenv("AI_SUPERVISOR_MODE", "auto")
    
    # Algorithm paths to load
    algorithm_paths: List[str] = field(default_factory=lambda: [
        os.path.join(BASE_DIR, "src", "soft", "dg", "algorithms"),
        os.path.join(BASE_DIR, "src", "soft", "dg", "algorithms", "security"),
        os.path.join(BASE_DIR, "src", "soft", "dg", "algorithms", "optimization"),
        os.path.join(BASE_DIR, "src", "soft", "dg", "algorithms", "maintenance"),
        os.path.join(BASE_DIR, "src", "soft", "dg", "algorithms", "simulation"),
    ])
    
    # Logging and monitoring
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", os.path.join(BASE_DIR, "ai_supervisor.log"))
    max_log_size_mb: int = int(os.getenv("MAX_LOG_SIZE_MB", "10"))
    log_backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Alerting thresholds
    alert_cooldown_minutes: int = int(os.getenv("ALERT_COOLDOWN_MINUTES", "15"))
    max_concurrent_repairs: int = int(os.getenv("MAX_CONCURRENT_REPAIRS", "3"))
    
    # Sandbox mode settings
    sandbox_prefix: str = "[SANDBOX] "
    
    # API rate limiting
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    rate_limit_period: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # in seconds
    
    # Caching
    cache_ttl: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes
    
    def validate(self) -> None:
        """Validate the configuration."""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        if self.default_mode not in ["auto", "manual", "sandbox"]:
            raise ValueError(f"Invalid default_mode: {self.default_mode}. Must be one of: auto, manual, sandbox")
        
        # Ensure algorithm paths exist
        for path in self.algorithm_paths:
            if not os.path.exists(path):
                logger.warning(f"Algorithm path does not exist: {path}")

# Initialize AI Supervisor config
ai_supervisor_config = AISupervisorConfig()

# Configure logging
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure logging for the application."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, ai_supervisor_config.log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                ai_supervisor_config.log_file,
                maxBytes=ai_supervisor_config.max_log_size_mb * 1024 * 1024,
                backupCount=ai_supervisor_config.log_backup_count
            )
        ]
    )

# Initialize logging when this module is imported
setup_logging()
logger = logging.getLogger(__name__)

# Validate config on import
try:
    ai_supervisor_config.validate()
except Exception as e:
    logger.error(f"Invalid AI Supervisor configuration: {e}")
    raise
