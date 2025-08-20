"""
Automated Onboarding System - Industrialisation de l'onboarding automatique
Gère l'inscription, validation, activation et parcours client complet
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid
import json

from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, JSON, Float
from sqlalchemy.ext.declarative import declarative_base

from ..models.base import Base
from ..models.notifications import NotificationService
from ..legal.terms_service import LegalService, DocumentType

logger = logging.getLogger(__name__)

class OnboardingStatus(Enum):
    STARTED = "started"
    EMAIL_VERIFICATION = "email_verification"
    PROFILE_COMPLETION = "profile_completion"
    LEGAL_ACCEPTANCE = "legal_acceptance"
    PAYMENT_SETUP = "payment_setup"
    VERIFICATION_PENDING = "verification_pending"
    APPROVED = "approved"
    ACTIVE = "active"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class OnboardingStep(Base):
    """Étapes du processus d'onboarding."""
    __tablename__ = "onboarding_steps"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    step_name = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, completed, skipped, failed
    data = Column(JSON, default={})
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class OnboardingSession(Base):
    """Session d'onboarding utilisateur."""
    __tablename__ = "onboarding_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, unique=True)
    current_status = Column(String, default=OnboardingStatus.STARTED.value)
    current_step = Column(String, nullable=True)
    progress_percentage = Column(Float, default=0.0)
    
    # Données collectées
    profile_data = Column(JSON, default={})
    verification_data = Column(JSON, default={})
    preferences = Column(JSON, default={})
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Métadonnées
    source = Column(String, nullable=True)  # organic, referral, campaign
    referrer_id = Column(String, nullable=True)
    utm_data = Column(JSON, default={})

class AutomatedOnboardingService:
    """Service d'onboarding automatisé avec parcours personnalisé."""
    
    def __init__(self, db: Session):
        self.db = db
        self.notifications = NotificationService(db)
        self.legal_service = LegalService(db)
        
        # Configuration du parcours
        self.onboarding_steps = [
            "email_verification",
            "profile_completion", 
            "legal_acceptance",
            "payment_setup",
            "verification_submission",
            "approval_waiting",
            "welcome_activation"
        ]
        
        # Seuils et limites
        self.auto_approval_threshold = float(os.getenv("AUTO_APPROVAL_THRESHOLD", "0.8"))
        self.manual_review_required = ["high_risk_country", "large_volume_expected"]
        
    async def start_onboarding(self, user_id: str, source: str = "organic", 
                             referrer_id: str = None, utm_data: Dict = None) -> OnboardingSession:
        """Démarre le processus d'onboarding pour un utilisateur."""
        logger.info(f"🚀 Starting onboarding for user {user_id}")
        
        # Vérifier si onboarding existe déjà
        existing_session = self.db.query(OnboardingSession).filter(
            OnboardingSession.user_id == user_id
        ).first()
        
        if existing_session:
            logger.info(f"Resuming existing onboarding session for user {user_id}")
            return existing_session
        
        # Créer nouvelle session
        session = OnboardingSession(
            user_id=user_id,
            source=source,
            referrer_id=referrer_id,
            utm_data=utm_data or {}
        )
        
        self.db.add(session)
        self.db.commit()
        
        # Créer les étapes
        for step_name in self.onboarding_steps:
            step = OnboardingStep(
                user_id=user_id,
                step_name=step_name
            )
            self.db.add(step)
        
        self.db.commit()
        
        # Envoyer email de bienvenue
        await self._send_welcome_email(user_id, session)
        
        # Démarrer la première étape
        await self._advance_to_next_step(session)
        
        logger.info(f"✅ Onboarding started for user {user_id}")
        return session
    
    async def complete_step(self, user_id: str, step_name: str, 
                          step_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Marque une étape comme complétée et avance dans le processus."""
        logger.info(f"📝 Completing step {step_name} for user {user_id}")
        
        session = self.db.query(OnboardingSession).filter(
            OnboardingSession.user_id == user_id
        ).first()
        
        if not session:
            raise ValueError(f"No onboarding session found for user {user_id}")
        
        step = self.db.query(OnboardingStep).filter(
            OnboardingStep.user_id == user_id,
            OnboardingStep.step_name == step_name
        ).first()
        
        if not step:
            raise ValueError(f"Step {step_name} not found for user {user_id}")
        
        # Valider les données de l'étape
        validation_result = await self._validate_step_data(step_name, step_data or {})
        
        if not validation_result["valid"]:
            return {
                "success": False,
                "errors": validation_result["errors"],
                "next_step": step_name  # Rester sur la même étape
            }
        
        # Marquer l'étape comme complétée
        step.status = "completed"
        step.data = step_data or {}
        step.completed_at = datetime.utcnow()
        
        # Mettre à jour la session
        if step_name == "profile_completion":
            session.profile_data.update(step_data or {})
        elif step_name == "verification_submission":
            session.verification_data.update(step_data or {})
        
        session.last_activity = datetime.utcnow()
        
        # Calculer le progrès
        completed_steps = self.db.query(OnboardingStep).filter(
            OnboardingStep.user_id == user_id,
            OnboardingStep.status == "completed"
        ).count()
        
        session.progress_percentage = (completed_steps / len(self.onboarding_steps)) * 100
        
        self.db.commit()
        
        # Avancer à l'étape suivante
        next_step_result = await self._advance_to_next_step(session)
        
        logger.info(f"✅ Step {step_name} completed for user {user_id}")
        
        return {
            "success": True,
            "completed_step": step_name,
            "next_step": next_step_result["next_step"],
            "progress_percentage": session.progress_percentage,
            "status": session.current_status
        }
    
    async def _validate_step_data(self, step_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valide les données d'une étape."""
        errors = []
        
        if step_name == "email_verification":
            if not data.get("email_verified"):
                errors.append("Email verification required")
        
        elif step_name == "profile_completion":
            required_fields = ["first_name", "last_name", "country", "phone"]
            for field in required_fields:
                if not data.get(field):
                    errors.append(f"Field '{field}' is required")
            
            # Validation spécifique
            if data.get("country") in ["XX", "YY"]:  # Pays à haut risque
                errors.append("Country not supported for automatic approval")
        
        elif step_name == "legal_acceptance":
            if not data.get("terms_accepted") or not data.get("privacy_accepted"):
                errors.append("Legal documents must be accepted")
        
        elif step_name == "payment_setup":
            if not data.get("payout_method"):
                errors.append("Payout method must be configured")
            
            if data.get("payout_method") == "bank_transfer":
                if not data.get("iban") or not data.get("bic"):
                    errors.append("IBAN and BIC required for bank transfer")
        
        elif step_name == "verification_submission":
            required_docs = ["identity_document", "address_proof"]
            for doc in required_docs:
                if not data.get(doc):
                    errors.append(f"Document '{doc}' is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _advance_to_next_step(self, session: OnboardingSession) -> Dict[str, Any]:
        """Avance à l'étape suivante du processus."""
        current_step_index = None
        
        if session.current_step:
            try:
                current_step_index = self.onboarding_steps.index(session.current_step)
            except ValueError:
                pass
        
        # Déterminer la prochaine étape
        if current_step_index is None:
            next_step = self.onboarding_steps[0]
        elif current_step_index < len(self.onboarding_steps) - 1:
            next_step = self.onboarding_steps[current_step_index + 1]
        else:
            # Processus terminé
            return await self._finalize_onboarding(session)
        
        # Mettre à jour la session
        session.current_step = next_step
        session.current_status = self._get_status_for_step(next_step)
        
        self.db.commit()
        
        # Envoyer notifications/instructions pour la prochaine étape
        await self._send_step_instructions(session.user_id, next_step)
        
        return {
            "next_step": next_step,
            "status": session.current_status,
            "instructions": await self._get_step_instructions(next_step)
        }
    
    def _get_status_for_step(self, step_name: str) -> str:
        """Retourne le statut correspondant à une étape."""
        status_mapping = {
            "email_verification": OnboardingStatus.EMAIL_VERIFICATION.value,
            "profile_completion": OnboardingStatus.PROFILE_COMPLETION.value,
            "legal_acceptance": OnboardingStatus.LEGAL_ACCEPTANCE.value,
            "payment_setup": OnboardingStatus.PAYMENT_SETUP.value,
            "verification_submission": OnboardingStatus.VERIFICATION_PENDING.value,
            "approval_waiting": OnboardingStatus.VERIFICATION_PENDING.value,
            "welcome_activation": OnboardingStatus.APPROVED.value
        }
        return status_mapping.get(step_name, OnboardingStatus.STARTED.value)
    
    async def _finalize_onboarding(self, session: OnboardingSession) -> Dict[str, Any]:
        """Finalise le processus d'onboarding."""
        logger.info(f"🎉 Finalizing onboarding for user {session.user_id}")
        
        # Évaluation automatique pour approbation
        approval_result = await self._evaluate_for_approval(session)
        
        if approval_result["auto_approve"]:
            session.current_status = OnboardingStatus.ACTIVE.value
            session.completed_at = datetime.utcnow()
            
            # Activer le compte
            await self._activate_user_account(session.user_id)
            
            # Email de bienvenue final
            await self._send_activation_email(session.user_id)
            
            logger.info(f"✅ User {session.user_id} automatically approved and activated")
            
        else:
            session.current_status = OnboardingStatus.VERIFICATION_PENDING.value
            
            # Envoyer pour révision manuelle
            await self._submit_for_manual_review(session, approval_result["reasons"])
            
            # Email d'attente
            await self._send_pending_review_email(session.user_id)
            
            logger.info(f"📋 User {session.user_id} submitted for manual review")
        
        self.db.commit()
        
        return {
            "next_step": None,
            "status": session.current_status,
            "auto_approved": approval_result["auto_approve"],
            "completion_date": session.completed_at
        }
    
    async def _evaluate_for_approval(self, session: OnboardingSession) -> Dict[str, Any]:
        """Évalue si un utilisateur peut être approuvé automatiquement."""
        score = 0.0
        max_score = 1.0
        reasons = []
        
        # Critères d'évaluation
        profile_data = session.profile_data
        
        # 1. Pays (30% du score)
        high_risk_countries = ["XX", "YY", "ZZ"]  # À configurer
        if profile_data.get("country") not in high_risk_countries:
            score += 0.3
        else:
            reasons.append("High-risk country")
        
        # 2. Complétude du profil (20% du score)
        required_fields = ["first_name", "last_name", "phone", "address"]
        completed_fields = sum(1 for field in required_fields if profile_data.get(field))
        profile_completeness = completed_fields / len(required_fields)
        score += 0.2 * profile_completeness
        
        if profile_completeness < 1.0:
            reasons.append("Incomplete profile")
        
        # 3. Documents fournis (30% du score)
        verification_data = session.verification_data
        required_docs = ["identity_document", "address_proof"]
        provided_docs = sum(1 for doc in required_docs if verification_data.get(doc))
        doc_completeness = provided_docs / len(required_docs)
        score += 0.3 * doc_completeness
        
        if doc_completeness < 1.0:
            reasons.append("Missing documents")
        
        # 4. Rapidité du processus (10% du score)
        process_duration = (datetime.utcnow() - session.started_at).total_seconds() / 3600
        if process_duration <= 24:  # Moins de 24h
            score += 0.1
        
        # 5. Source de trafic (10% du score)
        if session.source in ["referral", "organic"]:
            score += 0.1
        elif session.source in ["suspicious_campaign"]:
            reasons.append("Suspicious traffic source")
        
        auto_approve = score >= self.auto_approval_threshold and len(reasons) == 0
        
        return {
            "auto_approve": auto_approve,
            "score": score,
            "threshold": self.auto_approval_threshold,
            "reasons": reasons
        }
    
    async def _send_welcome_email(self, user_id: str, session: OnboardingSession):
        """Envoie l'email de bienvenue."""
        await self.notifications.send_email(
            to=f"user_{user_id}@example.com",  # À adapter
            subject="🎉 Bienvenue chez SmartLinks !",
            template="onboarding_welcome",
            data={
                "user_id": user_id,
                "onboarding_url": f"https://smartlinks.com/onboarding/{session.id}",
                "estimated_duration": "10 minutes"
            }
        )
    
    async def _send_step_instructions(self, user_id: str, step_name: str):
        """Envoie les instructions pour une étape."""
        instructions = await self._get_step_instructions(step_name)
        
        await self.notifications.send_email(
            to=f"user_{user_id}@example.com",
            subject=f"📋 Prochaine étape: {instructions['title']}",
            template="onboarding_step",
            data={
                "step_name": step_name,
                "step_title": instructions["title"],
                "step_description": instructions["description"],
                "action_url": instructions["action_url"]
            }
        )
    
    async def _get_step_instructions(self, step_name: str) -> Dict[str, str]:
        """Retourne les instructions pour une étape."""
        instructions = {
            "email_verification": {
                "title": "Vérifiez votre email",
                "description": "Cliquez sur le lien dans l'email que nous vous avons envoyé.",
                "action_url": "https://smartlinks.com/verify-email"
            },
            "profile_completion": {
                "title": "Complétez votre profil",
                "description": "Renseignez vos informations personnelles et professionnelles.",
                "action_url": "https://smartlinks.com/onboarding/profile"
            },
            "legal_acceptance": {
                "title": "Acceptez les conditions",
                "description": "Lisez et acceptez nos conditions d'utilisation et politique de confidentialité.",
                "action_url": "https://smartlinks.com/onboarding/legal"
            },
            "payment_setup": {
                "title": "Configurez vos paiements",
                "description": "Ajoutez votre méthode de paiement pour recevoir vos commissions.",
                "action_url": "https://smartlinks.com/onboarding/payment"
            },
            "verification_submission": {
                "title": "Vérification d'identité",
                "description": "Téléchargez vos documents d'identité pour la vérification.",
                "action_url": "https://smartlinks.com/onboarding/verification"
            }
        }
        
        return instructions.get(step_name, {
            "title": "Étape suivante",
            "description": "Continuez votre processus d'inscription.",
            "action_url": "https://smartlinks.com/onboarding"
        })
    
    async def _activate_user_account(self, user_id: str):
        """Active le compte utilisateur."""
        # Ici vous activeriez le compte dans votre système
        logger.info(f"🔓 Activating account for user {user_id}")
        
        # Créer les liens d'affiliation par défaut
        # Configurer les paramètres par défaut
        # Envoyer les accès API si nécessaire
    
    async def _send_activation_email(self, user_id: str):
        """Envoie l'email d'activation."""
        await self.notifications.send_email(
            to=f"user_{user_id}@example.com",
            subject="🎉 Votre compte SmartLinks est activé !",
            template="account_activated",
            data={
                "user_id": user_id,
                "dashboard_url": "https://smartlinks.com/dashboard",
                "affiliate_link": f"https://smartlinks.com/ref/{user_id}",
                "support_url": "https://smartlinks.com/support"
            }
        )
    
    async def _submit_for_manual_review(self, session: OnboardingSession, reasons: List[str]):
        """Soumet pour révision manuelle."""
        # Créer une tâche de révision pour les admins
        await self.notifications.send_admin_alert(
            type="manual_review_required",
            message=f"User {session.user_id} requires manual review",
            severity="medium",
            metadata={
                "user_id": session.user_id,
                "reasons": reasons,
                "profile_data": session.profile_data,
                "verification_data": session.verification_data
            }
        )
    
    async def _send_pending_review_email(self, user_id: str):
        """Envoie l'email d'attente de révision."""
        await self.notifications.send_email(
            to=f"user_{user_id}@example.com",
            subject="📋 Votre demande est en cours de révision",
            template="pending_review",
            data={
                "user_id": user_id,
                "estimated_review_time": "24-48 heures",
                "support_url": "https://smartlinks.com/support"
            }
        )
    
    async def get_onboarding_status(self, user_id: str) -> Dict[str, Any]:
        """Récupère le statut d'onboarding d'un utilisateur."""
        session = self.db.query(OnboardingSession).filter(
            OnboardingSession.user_id == user_id
        ).first()
        
        if not session:
            return {"status": "not_started"}
        
        steps = self.db.query(OnboardingStep).filter(
            OnboardingStep.user_id == user_id
        ).all()
        
        return {
            "status": session.current_status,
            "current_step": session.current_step,
            "progress_percentage": session.progress_percentage,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "steps": [
                {
                    "name": step.step_name,
                    "status": step.status,
                    "completed_at": step.completed_at
                }
                for step in steps
            ]
        }

# Tâches automatiques
async def process_pending_onboardings():
    """Traite les onboardings en attente."""
    from ..db import get_db
    
    db = next(get_db())
    try:
        service = AutomatedOnboardingService(db)
        
        # Relancer les utilisateurs inactifs
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        inactive_sessions = db.query(OnboardingSession).filter(
            OnboardingSession.current_status.in_([
                OnboardingStatus.STARTED.value,
                OnboardingStatus.EMAIL_VERIFICATION.value,
                OnboardingStatus.PROFILE_COMPLETION.value
            ]),
            OnboardingSession.last_activity <= cutoff_time
        ).all()
        
        for session in inactive_sessions:
            await service._send_step_instructions(session.user_id, session.current_step)
        
        logger.info(f"Processed {len(inactive_sessions)} inactive onboarding sessions")
        
    finally:
        db.close()
