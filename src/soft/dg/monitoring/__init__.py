"""
Module de monitoring et d'observabilité pour le DG autonome.

Fournit des outils pour le logging structuré, les métriques et le suivi des décisions.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration du logger principal
logger = logging.getLogger("dg.monitoring")

# Logger spécifique pour les décisions
decision_logger = logging.getLogger("dg.decisions")

# Logger pour les événements système
event_logger = logging.getLogger("dg.events")

# Logger pour les métriques
metrics_logger = logging.getLogger("dg.metrics")

# Configuration des handlers (peut être surchargée)
def configure_logging(level=logging.INFO, log_file: Optional[str] = None):
    """Configure la journalisation pour le DG autonome.
    
    Args:
        level: Niveau de log (par défaut: INFO)
        log_file: Chemin vers le fichier de log (optionnel)
    """
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configuration des loggers
    for log in [logger, decision_logger, event_logger, metrics_logger]:
        log.setLevel(level)
        log.handlers = [console_handler]
    
    # Ajout du fichier de log si spécifié
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        for log in [logger, decision_logger, event_logger, metrics_logger]:
            log.addHandler(file_handler)

def get_dg_logger(name: str = None) -> logging.Logger:
    """Obtient un logger pour le module spécifié.
    
    Args:
        name: Nom du module (optionnel)
        
    Returns:
        logging.Logger: Instance de logger configurée
    """
    if name:
        return logging.getLogger(f"dg.{name}")
    return logger

__all__ = [
    'logger',
    'decision_logger',
    'event_logger',
    'metrics_logger',
    'configure_logging',
    'get_dg_logger'
]
