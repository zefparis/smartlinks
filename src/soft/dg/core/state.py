"""
Gestion de l'état système du DG autonome.
Ce module est utilisé par DGEngine pour tracker le state en mémoire.
"""

class SystemState:
    def __init__(self):
        # État courant du système, tu peux adapter selon tes besoins
        self.current_state = {}

    def update(self, context):
        # Logique de mise à jour, ici on fusionne le context dans l'état courant
        self.current_state.update(context)
