"""
Librairie d'algorithmes pour le DG autonome.

Ce package contient les différents algorithmes utilisés par le moteur de stratégie
pour prendre des décisions intelligentes.
"""
from .base import Algorithm, AlgorithmResult

# Import des catégories d'algorithmes
from . import debug
from . import optimization
from . import security
from . import reporting

__all__ = ['Algorithm', 'AlgorithmResult']
