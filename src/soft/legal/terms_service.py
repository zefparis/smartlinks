"""
Terms of Service Management - CGU/CGV/Mentions légales avec système de validation
Gère l'acceptation et le suivi des conditions légales
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ..models.base import Base
from ..models.notifications import NotificationService

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    COOKIE_POLICY = "cookie_policy"
    AFFILIATE_TERMS = "affiliate_terms"
    PAYMENT_TERMS = "payment_terms"

class LegalDocument(Base):
    """Documents légaux (CGU, CGV, etc.)"""
    __tablename__ = "legal_documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_type = Column(String, nullable=False)  # DocumentType enum
    version = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    content_html = Column(Text, nullable=True)
    effective_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    requires_acceptance = Column(Boolean, default=True)
    
    # Relations
    acceptances = relationship("UserLegalAcceptance", back_populates="document")

class UserLegalAcceptance(Base):
    """Acceptations des documents légaux par les utilisateurs"""
    __tablename__ = "user_legal_acceptances"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    document_id = Column(String, ForeignKey("legal_documents.id"), nullable=False)
    accepted_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    acceptance_method = Column(String, nullable=False)  # 'signup', 'update', 'forced'
    
    # Relations
    document = relationship("LegalDocument", back_populates="acceptances")

class LegalService:
    """Service de gestion des documents légaux et acceptations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.notifications = NotificationService(db)
        
    async def create_legal_document(self, document_type: DocumentType, title: str, 
                                  content: str, content_html: str = None,
                                  effective_date: datetime = None) -> LegalDocument:
        """Crée un nouveau document légal."""
        logger.info(f"📋 Creating legal document: {document_type.value}")
        
        if effective_date is None:
            effective_date = datetime.utcnow()
        
        # Générer la version basée sur la date
        version = effective_date.strftime("%Y.%m.%d")
        
        # Désactiver l'ancienne version si elle existe
        old_doc = self.db.query(LegalDocument).filter(
            LegalDocument.document_type == document_type.value,
            LegalDocument.is_active == True
        ).first()
        
        if old_doc:
            old_doc.is_active = False
            logger.info(f"Deactivated old version: {old_doc.version}")
        
        # Créer le nouveau document
        document = LegalDocument(
            document_type=document_type.value,
            version=version,
            title=title,
            content=content,
            content_html=content_html or self._convert_to_html(content),
            effective_date=effective_date,
            requires_acceptance=True
        )
        
        self.db.add(document)
        self.db.commit()
        
        # Notifier les admins
        await self._notify_document_update(document, old_doc)
        
        logger.info(f"✅ Legal document created: {document.id} v{document.version}")
        return document
    
    async def get_active_documents(self) -> List[LegalDocument]:
        """Récupère tous les documents légaux actifs."""
        return self.db.query(LegalDocument).filter(
            LegalDocument.is_active == True
        ).order_by(LegalDocument.document_type, LegalDocument.effective_date.desc()).all()
    
    async def get_document_by_type(self, document_type: DocumentType) -> Optional[LegalDocument]:
        """Récupère le document actif d'un type donné."""
        return self.db.query(LegalDocument).filter(
            LegalDocument.document_type == document_type.value,
            LegalDocument.is_active == True
        ).first()
    
    async def record_user_acceptance(self, user_id: str, document_id: str,
                                   ip_address: str = None, user_agent: str = None,
                                   method: str = "manual") -> UserLegalAcceptance:
        """Enregistre l'acceptation d'un document par un utilisateur."""
        logger.info(f"📝 Recording legal acceptance: user {user_id}, doc {document_id}")
        
        # Vérifier si déjà accepté
        existing = self.db.query(UserLegalAcceptance).filter(
            UserLegalAcceptance.user_id == user_id,
            UserLegalAcceptance.document_id == document_id
        ).first()
        
        if existing:
            logger.info(f"Document already accepted by user {user_id}")
            return existing
        
        acceptance = UserLegalAcceptance(
            user_id=user_id,
            document_id=document_id,
            ip_address=ip_address,
            user_agent=user_agent,
            acceptance_method=method
        )
        
        self.db.add(acceptance)
        self.db.commit()
        
        logger.info(f"✅ Legal acceptance recorded: {acceptance.id}")
        return acceptance
    
    async def check_user_compliance(self, user_id: str) -> Dict[str, Any]:
        """Vérifie la conformité légale d'un utilisateur."""
        logger.info(f"🔍 Checking legal compliance for user {user_id}")
        
        active_docs = await self.get_active_documents()
        required_docs = [doc for doc in active_docs if doc.requires_acceptance]
        
        user_acceptances = self.db.query(UserLegalAcceptance).filter(
            UserLegalAcceptance.user_id == user_id
        ).all()
        
        accepted_doc_ids = {acc.document_id for acc in user_acceptances}
        
        compliance_status = {
            "is_compliant": True,
            "missing_documents": [],
            "accepted_documents": [],
            "last_update_required": None
        }
        
        for doc in required_docs:
            if doc.id in accepted_doc_ids:
                compliance_status["accepted_documents"].append({
                    "document_type": doc.document_type,
                    "version": doc.version,
                    "accepted_at": next(
                        acc.accepted_at for acc in user_acceptances 
                        if acc.document_id == doc.id
                    )
                })
            else:
                compliance_status["is_compliant"] = False
                compliance_status["missing_documents"].append({
                    "document_type": doc.document_type,
                    "version": doc.version,
                    "title": doc.title,
                    "effective_date": doc.effective_date
                })
        
        # Vérifier si des mises à jour sont nécessaires
        if compliance_status["missing_documents"]:
            compliance_status["last_update_required"] = max(
                doc["effective_date"] for doc in compliance_status["missing_documents"]
            )
        
        logger.info(f"Compliance check result: {compliance_status['is_compliant']}")
        return compliance_status
    
    async def get_required_acceptances_for_user(self, user_id: str) -> List[LegalDocument]:
        """Récupère les documents que l'utilisateur doit encore accepter."""
        compliance = await self.check_user_compliance(user_id)
        
        if compliance["is_compliant"]:
            return []
        
        missing_doc_types = [doc["document_type"] for doc in compliance["missing_documents"]]
        
        return self.db.query(LegalDocument).filter(
            LegalDocument.document_type.in_(missing_doc_types),
            LegalDocument.is_active == True
        ).all()
    
    async def bulk_accept_for_user(self, user_id: str, document_ids: List[str],
                                 ip_address: str = None, user_agent: str = None) -> List[UserLegalAcceptance]:
        """Accepte plusieurs documents en une fois."""
        logger.info(f"📋 Bulk accepting {len(document_ids)} documents for user {user_id}")
        
        acceptances = []
        for doc_id in document_ids:
            acceptance = await self.record_user_acceptance(
                user_id, doc_id, ip_address, user_agent, "bulk"
            )
            acceptances.append(acceptance)
        
        return acceptances
    
    async def generate_compliance_report(self, start_date: datetime = None,
                                       end_date: datetime = None) -> Dict[str, Any]:
        """Génère un rapport de conformité légale."""
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.utcnow()
        
        logger.info(f"📊 Generating compliance report from {start_date} to {end_date}")
        
        # Statistiques générales
        total_users = self.db.execute("SELECT COUNT(DISTINCT user_id) FROM users").scalar()
        
        acceptances_in_period = self.db.query(UserLegalAcceptance).filter(
            UserLegalAcceptance.accepted_at >= start_date,
            UserLegalAcceptance.accepted_at <= end_date
        ).all()
        
        # Grouper par type de document
        doc_stats = {}
        for acceptance in acceptances_in_period:
            doc_type = acceptance.document.document_type
            if doc_type not in doc_stats:
                doc_stats[doc_type] = {
                    "total_acceptances": 0,
                    "unique_users": set(),
                    "methods": {}
                }
            
            doc_stats[doc_type]["total_acceptances"] += 1
            doc_stats[doc_type]["unique_users"].add(acceptance.user_id)
            
            method = acceptance.acceptance_method
            doc_stats[doc_type]["methods"][method] = doc_stats[doc_type]["methods"].get(method, 0) + 1
        
        # Convertir les sets en counts
        for doc_type in doc_stats:
            doc_stats[doc_type]["unique_users"] = len(doc_stats[doc_type]["unique_users"])
        
        report = {
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "summary": {
                "total_users": total_users,
                "total_acceptances": len(acceptances_in_period),
                "unique_accepting_users": len(set(acc.user_id for acc in acceptances_in_period))
            },
            "by_document_type": doc_stats,
            "active_documents": len(await self.get_active_documents())
        }
        
        logger.info(f"✅ Compliance report generated: {report['summary']}")
        return report
    
    def _convert_to_html(self, content: str) -> str:
        """Convertit le contenu texte en HTML basique."""
        # Conversion basique markdown-like vers HTML
        html_content = content.replace('\n\n', '</p><p>')
        html_content = f"<p>{html_content}</p>"
        html_content = html_content.replace('**', '<strong>').replace('**', '</strong>')
        html_content = html_content.replace('*', '<em>').replace('*', '</em>')
        return html_content
    
    async def _notify_document_update(self, new_doc: LegalDocument, old_doc: LegalDocument = None):
        """Notifie la mise à jour d'un document légal."""
        if old_doc:
            message = f"Legal document updated: {new_doc.document_type} v{old_doc.version} → v{new_doc.version}"
        else:
            message = f"New legal document created: {new_doc.document_type} v{new_doc.version}"
        
        await self.notifications.send_admin_alert(
            type="legal_document_update",
            message=message,
            severity="medium",
            metadata={
                "document_id": new_doc.id,
                "document_type": new_doc.document_type,
                "version": new_doc.version,
                "effective_date": new_doc.effective_date.isoformat()
            }
        )

# Contenu par défaut des documents légaux
DEFAULT_TERMS_OF_SERVICE = """
# CONDITIONS GÉNÉRALES D'UTILISATION - SmartLinks

**Dernière mise à jour : {date}**

## 1. OBJET

Les présentes Conditions Générales d'Utilisation (CGU) régissent l'utilisation de la plateforme SmartLinks, service de gestion de liens d'affiliation exploité par SmartLinks SAS.

## 2. ACCEPTATION DES CONDITIONS

En utilisant nos services, vous acceptez pleinement et sans réserve les présentes CGU. Si vous n'acceptez pas ces conditions, vous ne devez pas utiliser nos services.

## 3. DESCRIPTION DU SERVICE

SmartLinks propose une plateforme de gestion de liens d'affiliation permettant aux utilisateurs de :
- Créer et gérer des liens d'affiliation
- Suivre les performances de leurs campagnes
- Recevoir des commissions sur les ventes générées

## 4. INSCRIPTION ET COMPTE UTILISATEUR

4.1. L'inscription est gratuite et ouverte à toute personne physique ou morale.
4.2. Vous vous engagez à fournir des informations exactes et à jour.
4.3. Vous êtes responsable de la confidentialité de vos identifiants.

## 5. OBLIGATIONS DE L'UTILISATEUR

5.1. Respecter les lois et règlements en vigueur
5.2. Ne pas utiliser le service à des fins illégales ou frauduleuses
5.3. Ne pas porter atteinte aux droits de tiers
5.4. Respecter les conditions des annonceurs partenaires

## 6. COMMISSIONS ET PAIEMENTS

6.1. Les commissions sont calculées selon les barèmes en vigueur
6.2. Les paiements sont effectués mensuellement pour les montants supérieurs à 50€
6.3. Les commissions frauduleuses seront annulées

## 7. RESPONSABILITÉ

7.1. SmartLinks ne peut être tenu responsable des dommages indirects
7.2. Notre responsabilité est limitée au montant des commissions dues

## 8. DONNÉES PERSONNELLES

Le traitement de vos données personnelles est régi par notre Politique de Confidentialité.

## 9. MODIFICATION DES CGU

Nous nous réservons le droit de modifier ces CGU à tout moment. Les utilisateurs seront informés des modifications.

## 10. DROIT APPLICABLE

Les présentes CGU sont régies par le droit français.

## CONTACT

Pour toute question : legal@smartlinks.com
"""

DEFAULT_PRIVACY_POLICY = """
# POLITIQUE DE CONFIDENTIALITÉ - SmartLinks

**Dernière mise à jour : {date}**

## 1. COLLECTE DES DONNÉES

Nous collectons les données suivantes :
- Informations d'identification (nom, email)
- Données de navigation et d'utilisation
- Informations de paiement
- Données de performance des campagnes

## 2. UTILISATION DES DONNÉES

Vos données sont utilisées pour :
- Fournir et améliorer nos services
- Calculer et verser les commissions
- Communiquer avec vous
- Respecter nos obligations légales

## 3. PARTAGE DES DONNÉES

Nous ne partageons vos données qu'avec :
- Nos partenaires techniques (hébergement, paiement)
- Les autorités légales si requis par la loi

## 4. CONSERVATION DES DONNÉES

Vos données sont conservées pendant la durée nécessaire à la fourniture du service et conformément aux obligations légales.

## 5. VOS DROITS

Vous disposez des droits suivants :
- Accès à vos données
- Rectification des données inexactes
- Suppression des données
- Portabilité des données
- Opposition au traitement

## 6. SÉCURITÉ

Nous mettons en œuvre des mesures techniques et organisationnelles appropriées pour protéger vos données.

## 7. COOKIES

Notre site utilise des cookies pour améliorer votre expérience. Consultez notre Politique de Cookies pour plus d'informations.

## CONTACT

Pour exercer vos droits : privacy@smartlinks.com
"""

async def initialize_default_legal_documents(db: Session):
    """Initialise les documents légaux par défaut."""
    legal_service = LegalService(db)
    
    current_date = datetime.utcnow().strftime("%d/%m/%Y")
    
    # CGU
    await legal_service.create_legal_document(
        DocumentType.TERMS_OF_SERVICE,
        "Conditions Générales d'Utilisation",
        DEFAULT_TERMS_OF_SERVICE.format(date=current_date)
    )
    
    # Politique de confidentialité
    await legal_service.create_legal_document(
        DocumentType.PRIVACY_POLICY,
        "Politique de Confidentialité",
        DEFAULT_PRIVACY_POLICY.format(date=current_date)
    )
    
    logger.info("✅ Default legal documents initialized")
