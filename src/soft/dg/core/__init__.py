"""
Module principal du moteur DG (Directeur Général) autonome.

Ce module contient les composants essentiels pour le fonctionnement
du DG autonome, y compris le moteur principal, la gestion des stratégies
et l'état du système.
"""
from .engine import DGEngine
from .strategy import StrategyEngine
from .state import SystemState

__all__ = ['DGEngine', 'StrategyEngine', 'SystemState']
