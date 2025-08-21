"""
Access Control & Security - Sécurisation et optimisation de l'accès à l'app
Auth, permissions, rate limiting, sécurité avancée
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import uuid
import hashlib
import secrets
from functools import wraps

from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, JSON, Float
from sqlalchemy.ext.declarative import declarative_base

from ...backend.database import Base
from ..models.notifications import NotificationService

logger = logging.getLogger(__name__)

# Lazy import for PyJWT to avoid module-level import failures during uvicorn reload on Windows
_jwt = None  # cached module

def _get_jwt():
    """Return the PyJWT module, importing and caching it on first use.
    Raises a clear error if PyJWT is not installed.
    """
    global _jwt
    if _jwt is not None:
        return _jwt
    try:
        import jwt as _mod  # type: ignore
    except Exception as e:  # pragma: no cover - clear error path
        raise ImportError(
            "PyJWT is required but not installed. Install with 'pip install PyJWT==2.8.0'."
        ) from e
    _jwt = _mod
    return _jwt

class UserRole(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    AFFILIATE = "affiliate"
    CLIENT = "client"
    VIEWER = "viewer"

class Permission(Enum):
    # Paiements
    PAYMENTS_VIEW = "payments.view"
    PAYMENTS_CREATE = "payments.create"
    PAYMENTS_REFUND = "payments.refund"
    PAYOUTS_VIEW = "payouts.view"
    PAYOUTS_EXECUTE = "payouts.execute"
    
    # Analytics
    ANALYTICS_VIEW = "analytics.view"
    ANALYTICS_EXPORT = "analytics.export"
    
    # Utilisateurs
    USERS_VIEW = "users.view"
    USERS_CREATE = "users.create"
    USERS_EDIT = "users.edit"
    USERS_DELETE = "users.delete"
    
    # Administration
    ADMIN_SETTINGS = "admin.settings"
    ADMIN_LOGS = "admin.logs"
    ADMIN_SYSTEM = "admin.system"

class User(Base):
    """Utilisateur avec rôles et permissions."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    
    # Profil
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    country = Column(String, nullable=True)
    
    # Sécurité
    role = Column(String, default=UserRole.AFFILIATE.value)
    permissions = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Authentification
    last_login = Column(DateTime, nullable=True)
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # 2FA
    two_fa_enabled = Column(Boolean, default=False)
    two_fa_secret = Column(String, nullable=True)
    backup_codes = Column(JSON, default=[])
    
    # Sessions
    active_sessions = Column(JSON, default=[])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserSession(Base):
    """Sessions utilisateur actives."""
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    session_token = Column(String, unique=True, nullable=False)
    
    # Métadonnées
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    device_fingerprint = Column(String, nullable=True)
    
    # Statut
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class RateLimitRule(Base):
    """Règles de limitation de taux."""
    __tablename__ = "rate_limit_rules"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint = Column(String, nullable=False)
    method = Column(String, default="*")  # GET, POST, *, etc.
    
    # Limites
    requests_per_minute = Column(Integer, default=60)
    requests_per_hour = Column(Integer, default=1000)
    requests_per_day = Column(Integer, default=10000)
    
    # Applicabilité
    applies_to_role = Column(String, nullable=True)  # Si None, s'applique à tous
    applies_to_ip = Column(String, nullable=True)
    
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SecurityEvent(Base):
    """Événements de sécurité."""
    __tablename__ = "security_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String, nullable=False)  # login_failed, suspicious_activity, etc.
    severity = Column(String, default="medium")  # low, medium, high, critical
    
    # Contexte
    user_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    endpoint = Column(String, nullable=True)
    
    # Détails
    description = Column(Text, nullable=False)
    details = Column(JSON, default={})
    
    # Actions
    action_taken = Column(String, nullable=True)  # blocked, flagged, ignored
    resolved = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class SecurityService:
    """Service de sécurité et contrôle d'accès."""
    
    def __init__(self, db: Session):
        self.db = db
        self.notifications = NotificationService(db)
        
        # Configuration
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.session_duration = int(os.getenv("SESSION_DURATION_HOURS", "24"))
        self.max_login_attempts = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.lockout_duration = int(os.getenv("LOCKOUT_DURATION_MINUTES", "30"))
        
        # Permissions par rôle
        self.role_permissions = {
            UserRole.ADMIN: [p.value for p in Permission],
            UserRole.MANAGER: [
                Permission.PAYMENTS_VIEW.value,
                Permission.PAYOUTS_VIEW.value,
                Permission.PAYOUTS_EXECUTE.value,
                Permission.ANALYTICS_VIEW.value,
                Permission.ANALYTICS_EXPORT.value,
                Permission.USERS_VIEW.value,
                Permission.USERS_EDIT.value
            ],
            UserRole.AFFILIATE: [
                Permission.PAYMENTS_VIEW.value,
                Permission.PAYOUTS_VIEW.value,
                Permission.ANALYTICS_VIEW.value
            ],
            UserRole.CLIENT: [
                Permission.PAYMENTS_VIEW.value,
                Permission.ANALYTICS_VIEW.value
            ],
            UserRole.VIEWER: [
                Permission.ANALYTICS_VIEW.value
            ]
        }
    
    async def create_user(self, email: str, password: str, role: UserRole = UserRole.AFFILIATE,
                         first_name: str = None, last_name: str = None) -> User:
        """Crée un nouvel utilisateur avec sécurité renforcée."""
        logger.info(f"🔐 Creating user: {email}")
        
        # Vérifier si l'utilisateur existe
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("User already exists")
        
        # Valider le mot de passe
        if not self._validate_password_strength(password):
            raise ValueError("Password does not meet security requirements")
        
        # Générer salt et hash
        salt = secrets.token_hex(32)
        password_hash = self._hash_password(password, salt)
        
        # Créer l'utilisateur
        user = User(
            email=email,
            password_hash=password_hash,
            salt=salt,
            role=role.value,
            permissions=self.role_permissions.get(role, []),
            first_name=first_name,
            last_name=last_name
        )
        
        self.db.add(user)
        self.db.commit()
        
        # Événement de sécurité
        await self._log_security_event(
            "user_created",
            "medium",
            f"New user created: {email}",
            user_id=user.id,
            metadata={"role": role.value}
        )
        
        logger.info(f"✅ User created: {user.id}")
        return user
    
    async def authenticate_user(self, email: str, password: str, ip_address: str = None,
                              user_agent: str = None, two_fa_code: str = None) -> Dict[str, Any]:
        """Authentifie un utilisateur avec sécurité avancée."""
        logger.info(f"🔑 Authenticating user: {email}")
        
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            await self._log_security_event(
                "login_failed",
                "medium",
                f"Login attempt with non-existent email: {email}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise ValueError("Invalid credentials")
        
        # Vérifier si le compte est verrouillé
        if user.locked_until and user.locked_until > datetime.utcnow():
            await self._log_security_event(
                "login_blocked",
                "high",
                f"Login attempt on locked account: {email}",
                user_id=user.id,
                ip_address=ip_address
            )
            raise ValueError("Account is temporarily locked")
        
        # Vérifier le mot de passe
        if not self._verify_password(password, user.password_hash, user.salt):
            user.login_attempts += 1
            
            if user.login_attempts >= self.max_login_attempts:
                user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration)
                await self._log_security_event(
                    "account_locked",
                    "high",
                    f"Account locked after {self.max_login_attempts} failed attempts: {email}",
                    user_id=user.id,
                    ip_address=ip_address
                )
            
            self.db.commit()
            raise ValueError("Invalid credentials")
        
        # Vérifier 2FA si activé
        if user.two_fa_enabled:
            if not two_fa_code:
                return {"requires_2fa": True, "user_id": user.id}
            
            if not self._verify_2fa_code(user.two_fa_secret, two_fa_code):
                await self._log_security_event(
                    "2fa_failed",
                    "high",
                    f"2FA verification failed: {email}",
                    user_id=user.id,
                    ip_address=ip_address
                )
                raise ValueError("Invalid 2FA code")
        
        # Réinitialiser les tentatives de connexion
        user.login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        
        # Créer une session
        session = await self._create_session(user.id, ip_address, user_agent)
        
        # Générer JWT
        token = self._generate_jwt_token(user.id, session.id)
        
        self.db.commit()
        
        await self._log_security_event(
            "login_success",
            "low",
            f"Successful login: {email}",
            user_id=user.id,
            ip_address=ip_address
        )
        
        logger.info(f"✅ User authenticated: {user.id}")
        
        return {
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "permissions": user.permissions
            },
            "session_id": session.id,
            "expires_at": session.expires_at
        }
    
    async def _create_session(self, user_id: str, ip_address: str = None, 
                            user_agent: str = None) -> UserSession:
        """Crée une nouvelle session utilisateur."""
        
        # Générer token de session sécurisé
        session_token = secrets.token_urlsafe(64)
        
        # Calculer l'empreinte du dispositif
        device_fingerprint = None
        if ip_address and user_agent:
            device_fingerprint = hashlib.sha256(
                f"{ip_address}:{user_agent}".encode()
            ).hexdigest()
        
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            expires_at=datetime.utcnow() + timedelta(hours=self.session_duration)
        )
        
        self.db.add(session)
        
        # Nettoyer les anciennes sessions
        await self._cleanup_expired_sessions(user_id)
        
        return session
    
    async def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Valide une session utilisateur."""
        try:
            # Décoder le JWT
            jwt_mod = _get_jwt()
            payload = jwt_mod.decode(token, self.jwt_secret, algorithms=["HS256"])
            user_id = payload.get("user_id")
            session_id = payload.get("session_id")
            
            if not user_id or not session_id:
                return None
            
            # Vérifier la session
            session = self.db.query(UserSession).filter(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if not session:
                return None
            
            # Vérifier l'utilisateur
            user = self.db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()
            
            if not user:
                return None
            
            # Mettre à jour l'activité
            session.last_activity = datetime.utcnow()
            self.db.commit()
            
            return {
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
                "permissions": user.permissions,
                "session_id": session.id
            }
            
        except Exception as e:
            # If PyJWT is present, map its InvalidTokenError to None; else propagate clear install error
            try:
                jwt_mod = _get_jwt()
                if isinstance(e, getattr(jwt_mod, "InvalidTokenError", Exception)):
                    return None
            except ImportError:
                raise
            return None
            return None
    
    def check_permission(self, user_permissions: List[str], required_permission: Permission) -> bool:
        """Vérifie si l'utilisateur a la permission requise."""
        return required_permission.value in user_permissions
    
    def require_permission(self, permission: Permission):
        """Décorateur pour vérifier les permissions."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Récupérer l'utilisateur du contexte (à adapter selon votre framework)
                user_permissions = kwargs.get("user_permissions", [])
                
                if not self.check_permission(user_permissions, permission):
                    raise PermissionError(f"Permission required: {permission.value}")
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    async def apply_rate_limiting(self, endpoint: str, method: str, user_role: str = None,
                                ip_address: str = None) -> bool:
        """Applique la limitation de taux."""
        
        # Trouver les règles applicables
        rules = self.db.query(RateLimitRule).filter(
            RateLimitRule.enabled == True,
            RateLimitRule.endpoint == endpoint
        ).all()
        
        applicable_rules = []
        for rule in rules:
            if rule.method != "*" and rule.method != method:
                continue
            if rule.applies_to_role and rule.applies_to_role != user_role:
                continue
            if rule.applies_to_ip and rule.applies_to_ip != ip_address:
                continue
            applicable_rules.append(rule)
        
        # Vérifier les limites
        for rule in applicable_rules:
            if not await self._check_rate_limit(rule, ip_address, user_role):
                await self._log_security_event(
                    "rate_limit_exceeded",
                    "medium",
                    f"Rate limit exceeded for {endpoint}",
                    ip_address=ip_address,
                    endpoint=endpoint,
                    metadata={"rule_id": rule.id, "user_role": user_role}
                )
                return False
        
        return True
    
    async def _check_rate_limit(self, rule: RateLimitRule, ip_address: str = None,
                              user_role: str = None) -> bool:
        """Vérifie une règle de limitation spécifique."""
        # Ici vous implémenteriez la logique de vérification avec Redis ou cache
        # Pour l'exemple, on simule une vérification basique
        
        cache_key = f"rate_limit:{rule.id}:{ip_address or 'global'}:{user_role or 'anonymous'}"
        
        # Dans un vrai système, vous utiliseriez Redis avec des compteurs
        # et des TTL pour implémenter la limitation de taux
        
        return True  # Placeholder
    
    def _validate_password_strength(self, password: str) -> bool:
        """Valide la force du mot de passe."""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash un mot de passe avec salt."""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def _verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Vérifie un mot de passe."""
        return self._hash_password(password, salt) == password_hash
    
    def _generate_jwt_token(self, user_id: str, session_id: str) -> str:
        """Génère un token JWT."""
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.session_duration)
        }
        
        jwt_mod = _get_jwt()
        return jwt_mod.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def _verify_2fa_code(self, secret: str, code: str) -> bool:
        """Vérifie un code 2FA TOTP."""
        import pyotp
        
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    
    async def _cleanup_expired_sessions(self, user_id: str):
        """Nettoie les sessions expirées."""
        expired_sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.expires_at <= datetime.utcnow()
        ).all()
        
        for session in expired_sessions:
            session.is_active = False
    
    async def _log_security_event(self, event_type: str, severity: str, description: str,
                                user_id: str = None, ip_address: str = None,
                                user_agent: str = None, endpoint: str = None,
                                metadata: Dict[str, Any] = None):
        """Enregistre un événement de sécurité."""
        
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            details=metadata or {}
        )
        
        self.db.add(event)
        
        # Alerter si critique
        if severity == "critical":
            await self.notifications.send_admin_alert(
                type="security_critical",
                message=f"Critical security event: {description}",
                severity="critical",
                metadata=metadata or {}
            )
    
    async def enable_2fa(self, user_id: str) -> Dict[str, Any]:
        """Active la 2FA pour un utilisateur."""
        import pyotp
        import qrcode
        from io import BytesIO
        import base64
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Générer un secret 2FA
        secret = pyotp.random_base32()
        
        # Générer des codes de sauvegarde
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        
        # Générer le QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="SmartLinks"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Sauvegarder (mais pas encore activer)
        user.two_fa_secret = secret
        user.backup_codes = backup_codes
        
        self.db.commit()
        
        return {
            "secret": secret,
            "qr_code": qr_code_base64,
            "backup_codes": backup_codes,
            "provisioning_uri": provisioning_uri
        }
    
    async def confirm_2fa(self, user_id: str, code: str) -> bool:
        """Confirme et active la 2FA."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.two_fa_secret:
            return False
        
        if self._verify_2fa_code(user.two_fa_secret, code):
            user.two_fa_enabled = True
            self.db.commit()
            
            await self._log_security_event(
                "2fa_enabled",
                "medium",
                f"2FA enabled for user: {user.email}",
                user_id=user.id
            )
            
            return True
        
        return False
    
    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Récupère le tableau de bord sécurité."""
        
        # Événements récents
        recent_events = self.db.query(SecurityEvent).filter(
            SecurityEvent.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(SecurityEvent.created_at.desc()).limit(50).all()
        
        # Statistiques
        total_users = self.db.query(User).count()
        active_sessions = self.db.query(UserSession).filter(
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).count()
        
        locked_accounts = self.db.query(User).filter(
            User.locked_until > datetime.utcnow()
        ).count()
        
        users_with_2fa = self.db.query(User).filter(
            User.two_fa_enabled == True
        ).count()
        
        # Événements par type
        event_counts = {}
        for event in recent_events:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "statistics": {
                "total_users": total_users,
                "active_sessions": active_sessions,
                "locked_accounts": locked_accounts,
                "users_with_2fa": users_with_2fa,
                "2fa_adoption_rate": (users_with_2fa / total_users * 100) if total_users > 0 else 0
            },
            "recent_events": [
                {
                    "id": event.id,
                    "type": event.event_type,
                    "severity": event.severity,
                    "description": event.description,
                    "user_id": event.user_id,
                    "ip_address": event.ip_address,
                    "created_at": event.created_at.isoformat(),
                    "metadata": event.details
                }
                for event in recent_events
            ],
            "event_counts": event_counts,
            "security_score": await self._calculate_security_score()
        }
    
    async def _calculate_security_score(self) -> int:
        """Calcule un score de sécurité global."""
        score = 0
        max_score = 100
        
        # 2FA adoption (30 points)
        total_users = self.db.query(User).count()
        users_with_2fa = self.db.query(User).filter(User.two_fa_enabled == True).count()
        if total_users > 0:
            score += int((users_with_2fa / total_users) * 30)
        
        # Comptes non verrouillés (20 points)
        locked_accounts = self.db.query(User).filter(User.locked_until > datetime.utcnow()).count()
        if locked_accounts == 0:
            score += 20
        
        # Événements de sécurité récents (30 points)
        recent_critical_events = self.db.query(SecurityEvent).filter(
            SecurityEvent.severity == "critical",
            SecurityEvent.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        if recent_critical_events == 0:
            score += 30
        elif recent_critical_events <= 2:
            score += 15
        
        # Sessions actives raisonnables (20 points)
        active_sessions = self.db.query(UserSession).filter(
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).count()
        
        if active_sessions <= total_users * 2:  # Max 2 sessions par utilisateur
            score += 20
        
        return min(score, max_score)

# Middleware de sécurité
class SecurityMiddleware:
    """Middleware pour appliquer les contrôles de sécurité."""
    
    def __init__(self, security_service: SecurityService):
        self.security_service = security_service
    
    async def __call__(self, request, call_next):
        """Traite une requête avec contrôles de sécurité."""
        
        # Extraire les informations de la requête
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent", "")
        endpoint = request.url.path
        method = request.method
        
        # Vérifier l'authentification
        auth_header = request.headers.get("authorization", "")
        user_context = None
        
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            user_context = await self.security_service.validate_session(token)
        
        # Appliquer la limitation de taux
        user_role = user_context.get("role") if user_context else None
        
        if not await self.security_service.apply_rate_limiting(
            endpoint, method, user_role, ip_address
        ):
            # Retourner erreur 429 Too Many Requests
            from fastapi import HTTPException
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Ajouter le contexte utilisateur à la requête
        if user_context:
            request.state.user = user_context
        
        # Continuer le traitement
        response = await call_next(request)
        
        return response

# Configuration par défaut
async def setup_default_security_rules(db: Session):
    """Configure les règles de sécurité par défaut."""
    
    default_rules = [
        {
            "endpoint": "/api/auth/login",
            "method": "POST",
            "requests_per_minute": 5,
            "requests_per_hour": 20
        },
        {
            "endpoint": "/api/payments",
            "method": "*",
            "requests_per_minute": 30,
            "requests_per_hour": 500,
            "applies_to_role": "affiliate"
        },
        {
            "endpoint": "/api/admin",
            "method": "*",
            "requests_per_minute": 100,
            "requests_per_hour": 1000,
            "applies_to_role": "admin"
        }
    ]
    
    for rule_data in default_rules:
        existing_rule = db.query(RateLimitRule).filter(
            RateLimitRule.endpoint == rule_data["endpoint"],
            RateLimitRule.method == rule_data["method"]
        ).first()
        
        if not existing_rule:
            rule = RateLimitRule(**rule_data)
            db.add(rule)
    
    db.commit()
    logger.info("✅ Default security rules configured")
