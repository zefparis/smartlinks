"""
DG Autonome - Module de gouvernance digitale intelligente

Ce module implémente un directeur général numérique autonome qui orchestre
des algorithmes d'optimisation, de sécurité et de croissance pour SmartLinks.
"""
from .core.engine import DGEngine
from .api.router import router as dg_router

__version__ = "0.1.0"
__all__ = ['DGEngine', 'dg_router']
