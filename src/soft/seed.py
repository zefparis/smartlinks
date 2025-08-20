"""
Smart Data Seeder for SmartLinks Autopilot

Ce module fournit des fonctions pour peupler la base de données avec des données de test
de manière cohérente, en gérant automatiquement les dépendances entre les entités.

Usage:
    - En ligne de commande: `python -m src.soft.seed [--count=100] [--strict]`
    - En tant que module: `from src.soft.seed import seed_random_data`
"""
from __future__ import annotations

import random
import logging
import argparse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .db import SessionLocal, Base, engine
from .models import (
    Offer, Segment, Creator, Click, Conversion, PayoutRate
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Valeurs par défaut pour les entités
DEFAULT_OFFERS = [
    {"offer_id": "offer_a", "name": "Offer A", "url": "https://example.com/a"},
    {"offer_id": "offer_b", "name": "Offer B", "url": "https://example.com/b"},
    {"offer_id": "offer_c", "name": "Offer C", "url": "https://example.com/c"},
]

DEFAULT_CREATORS = [
    {"creator_id": "creator_1", "q": 0.7, "hard_cap_eur": 50.0},
    {"creator_id": "creator_2", "q": 0.5, "hard_cap_eur": 30.0},
    {"creator_id": "creator_3", "q": 0.8, "hard_cap_eur": 75.0},
]

DEFAULT_SEGMENTS = [
    {"segment_id": "FR:mobile", "geo": "FR", "device": "mobile"},
    {"segment_id": "FR:desktop", "geo": "FR", "device": "desktop"},
    {"segment_id": "US:mobile", "geo": "US", "device": "mobile"},
]

class DataSeeder:
    """Classe principale pour le peuplement des données avec gestion des dépendances"""
    
    def __init__(self, db: Session, strict_mode: bool = False):
        """
        Initialise le seeder avec une session de base de données.
        
        Args:
            db: Session SQLAlchemy
            strict_mode: Si True, lève une exception si une dépendance est manquante
        """
        self.db = db
        self.strict_mode = strict_mode
    
    def ensure_offer(self, offer_id: str, **kwargs) -> Offer:
        """
        Vérifie et crée une offre si elle n'existe pas.
        
        Args:
            offer_id: ID de l'offre
            **kwargs: Autres attributs de l'offre
            
        Returns:
            L'offre existante ou nouvellement créée
        """
        offer = self.db.query(Offer).filter(Offer.offer_id == offer_id).first()
        if offer:
            return offer
            
        # Valeurs par défaut
        defaults = {
            "name": f"Offer {offer_id}",
            "url": f"https://example.com/offer/{offer_id}",
            "incent_ok": 1,
            "cap_day": 10000,
            "geo_allow": "ALL",
            "status": "on"
        }
        defaults.update(kwargs)
        
        try:
            offer = Offer(offer_id=offer_id, **defaults)
            self.db.add(offer)
            self.db.commit()
            logger.info(f"✅ Created offer: {offer_id}")
            return offer
        except IntegrityError:
            self.db.rollback()
            return self.db.query(Offer).filter(Offer.offer_id == offer_id).first()
    
    def ensure_creator(self, creator_id: str, **kwargs) -> Creator:
        """
        Vérifie et crée un créateur s'il n'existe pas.
        
        Args:
            creator_id: ID du créateur
            **kwargs: Autres attributs du créateur
            
        Returns:
            Le créateur existant ou nouvellement créé
        """
        creator = self.db.query(Creator).filter(Creator.creator_id == creator_id).first()
        if creator:
            return creator
            
        # Valeurs par défaut
        defaults = {
            "q": round(random.uniform(0.3, 0.9), 2),  # Qualité aléatoire entre 0.3 et 0.9
            "hard_cap_eur": round(random.uniform(20, 100), 2),  # Cap aléatoire entre 20 et 100€
            "last_seen": int(datetime.now().timestamp())
        }
        defaults.update(kwargs)
        
        try:
            creator = Creator(creator_id=creator_id, **defaults)
            self.db.add(creator)
            self.db.commit()
            logger.info(f"✅ Created creator: {creator_id}")
            return creator
        except IntegrityError:
            self.db.rollback()
            return self.db.query(Creator).filter(Creator.creator_id == creator_id).first()
    
    def ensure_segment(self, segment_id: str, **kwargs) -> Segment:
        """
        Vérifie et crée un segment s'il n'existe pas.
        
        Args:
            segment_id: ID du segment (format "CODE_PAYS:device")
            **kwargs: Autres attributs du segment
            
        Returns:
            Le segment existant ou nouvellement créé
        """
        segment = self.db.query(Segment).filter(Segment.segment_id == segment_id).first()
        if segment:
            return segment
            
        # Extraction du code pays et du device depuis l'ID si possible
        if ":" in segment_id:
            geo, device = segment_id.split(":", 1)
        else:
            geo = kwargs.get("geo", "XX")
            device = kwargs.get("device", "desktop")
        
        # Valeurs par défaut
        defaults = {
            "geo": geo,
            "device": device
        }
        defaults.update(kwargs)
        
        try:
            segment = Segment(segment_id=segment_id, **defaults)
            self.db.add(segment)
            self.db.commit()
            logger.info(f"✅ Created segment: {segment_id} ({geo}, {device})")
            return segment
        except IntegrityError:
            self.db.rollback()
            return self.db.query(Segment).filter(Segment.segment_id == segment_id).first()
    
    def create_click(
        self, 
        creator_id: str, 
        segment_id: str,
        offer_id: str,
        **kwargs
    ) -> Click:
        """
        Crée un clic en s'assurant que toutes les dépendances existent.
        
        Args:
            creator_id: ID du créateur
            segment_id: ID du segment
            offer_id: ID de l'offre
            **kwargs: Autres attributs du clic
            
        Returns:
            Le clic créé
            
        Raises:
            ValueError: En mode strict, si une dépendance est manquante
        """
        # Vérification/création des dépendances
        creator = self.ensure_creator(creator_id)
        if not creator and self.strict_mode:
            raise ValueError(f"Creator {creator_id} does not exist")
            
        segment = self.ensure_segment(segment_id)
        if not segment and self.strict_mode:
            raise ValueError(f"Segment {segment_id} does not exist")
            
        offer = self.ensure_offer(offer_id)
        if not offer and self.strict_mode:
            raise ValueError(f"Offer {offer_id} does not exist")
        
        # Valeurs par défaut pour le clic
        now = int(datetime.now().timestamp())
        defaults = {
            "click_id": f"clk_{now}_{random.randint(1000, 9999)}",
            "ts": now - random.randint(0, 86400),  # Dernières 24h
            "slug": f"offer_{offer_id[-1].lower()}",
            "geo": segment.geo if segment else "XX",
            "device": segment.device if segment else "desktop",
            "fp": f"fp{random.randint(1000000000, 9999999999)}",
            "valid_final": 1,
            "risk": round(random.uniform(0, 0.5), 4)  # Risque bas par défaut
        }
        
        # Mise à jour avec les valeurs fournies
        click_data = {**defaults, **kwargs}
        
        # Création du clic
        click = Click(**click_data)
        self.db.add(click)
        
        try:
            self.db.commit()
            logger.debug(f"✅ Created click: {click.click_id}")
            return click
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating click: {e}")
            raise
    
    def create_conversion(
        self,
        click_id: str,
        offer_id: str,
        **kwargs
    ) -> Optional[Conversion]:
        """
        Crée une conversion pour un clic existant.
        
        Args:
            click_id: ID du clic
            offer_id: ID de l'offre
            **kwargs: Autres attributs de la conversion
            
        Returns:
            La conversion créée, ou None en cas d'erreur
        """
        # Vérification que le clic existe
        click = self.db.query(Click).filter(Click.click_id == click_id).first()
        if not click:
            if self.strict_mode:
                raise ValueError(f"Click {click_id} does not exist")
            logger.warning(f"⚠️ Click {click_id} not found, skipping conversion")
            return None
            
        # Vérification de l'offre
        offer = self.ensure_offer(offer_id)
        if not offer and self.strict_mode:
            raise ValueError(f"Offer {offer_id} does not exist")
        
        # Valeurs par défaut pour la conversion
        defaults = {
            "id": f"conv_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}",
            "ts": int(datetime.now().timestamp()),
            "revenue": round(random.uniform(1.0, 50.0), 2),
            "status": random.choice(["approved", "pending", "rejected"])
        }
        
        # Mise à jour avec les valeurs fournies
        conversion_data = {**defaults, **kwargs}
        
        # Création de la conversion
        conversion = Conversion(**conversion_data)
        self.db.add(conversion)
        
        try:
            self.db.commit()
            logger.debug(f"✅ Created conversion: {conversion.id}")
            return conversion
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating conversion: {e}")
            return None

def seed_default_data(db: Session, strict_mode: bool = False) -> Dict[str, int]:
    """
    Peuple la base avec des données par défaut (offres, créateurs, segments).
    
    Args:
        db: Session SQLAlchemy
        strict_mode: Si True, échoue si une entité existe déjà
        
    Returns:
        Dictionnaire avec le nombre d'entités créées par type
    """
    seeder = DataSeeder(db, strict_mode=strict_mode)
    counts = {"offers": 0, "creators": 0, "segments": 0}
    
    # Création des offres par défaut
    for offer_data in DEFAULT_OFFERS:
        try:
            seeder.ensure_offer(**offer_data)
            counts["offers"] += 1
        except IntegrityError:
            if strict_mode:
                raise
            
    # Création des créateurs par défaut
    for creator_data in DEFAULT_CREATORS:
        try:
            seeder.ensure_creator(**creator_data)
            counts["creators"] += 1
        except IntegrityError:
            if strict_mode:
                raise
    
    # Création des segments par défaut
    for segment_data in DEFAULT_SEGMENTS:
        try:
            seeder.ensure_segment(**segment_data)
            counts["segments"] += 1
        except IntegrityError:
            if strict_mode:
                raise
    
    return counts

def seed_random_data(
    db: Session,
    num_clicks: int = 100,
    conversion_rate: float = 0.1,
    strict_mode: bool = False
) -> Dict[str, int]:
    """
    Peuple la base avec des données aléatoires.
    
    Args:
        db: Session SQLAlchemy
        num_clicks: Nombre de clics à générer
        conversion_rate: Taux de conversion (entre 0 et 1)
        strict_mode: Si True, échoue si une dépendance est manquante
        
    Returns:
        Dictionnaire avec le nombre d'entités créées par type
    """
    # D'abord, on s'assure que les données de base sont présentes
    seed_default_data(db, strict_mode=strict_mode)
    
    seeder = DataSeeder(db, strict_mode=strict_mode)
    counts = {"clicks": 0, "conversions": 0}
    
    # Liste des IDs disponibles
    creators = [c.creator_id for c in db.query(Creator.creator_id).all()]
    segments = [s.segment_id for s in db.query(Segment.segment_id).all()]
    offers = [o.offer_id for o in db.query(Offer.offer_id).all()]
    
    if not creators or not segments or not offers:
        raise ValueError("Missing required data. Run seed_default_data() first.")
    
    # Génération des clics
    for _ in range(num_clicks):
        try:
            # Sélection aléatoire des dépendances
            creator_id = random.choice(creators)
            segment_id = random.choice(segments)
            offer_id = random.choice(offers)
            
            # Création du clic
            click = seeder.create_click(
                creator_id=creator_id,
                segment_id=segment_id,
                offer_id=offer_id
            )
            
            if click:
                counts["clicks"] += 1
                
                # Création d'une conversion aléatoire
                if random.random() < conversion_rate:
                    conversion = seeder.create_conversion(
                        click_id=click.click_id,
                        offer_id=offer_id
                    )
                    if conversion:
                        counts["conversions"] += 1
                        
        except Exception as e:
            if strict_mode:
                raise
            logger.warning(f"Skipping due to error: {e}")
    
    return counts

def main():
    """Point d'entrée en ligne de commande"""
    parser = argparse.ArgumentParser(description="SmartLinks Data Seeder")
    parser.add_argument(
        "--count", 
        type=int, 
        default=100,
        help="Number of clicks to generate (default: 100)"
    )
    parser.add_argument(
        "--conversion-rate",
        type=float,
        default=0.1,
        help="Conversion rate (0-1, default: 0.1)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode (fail on missing dependencies)"
    )
    parser.add_argument(
        "--only-defaults",
        action="store_true",
        help="Only seed default data (no random clicks)"
    )
    
    args = parser.parse_args()
    
    # Configuration du logging
    logging.basicConfig(level=logging.INFO)
    
    # Création des tables si elles n'existent pas
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Peuplement des données par défaut
        logger.info("🌱 Seeding default data...")
        default_counts = seed_default_data(db, strict_mode=args.strict)
        
        if not args.only_defaults:
            # Peuplement des données aléatoires
            logger.info(f"🎲 Generating {args.count} random clicks...")
            random_counts = seed_random_data(
                db,
                num_clicks=args.count,
                conversion_rate=args.conversion_rate,
                strict_mode=args.strict
            )
            
            # Affichage du résumé
            logger.info("\n✅ Seeding completed!")
            logger.info("\n📊 Summary:")
            logger.info(f"  - Default offers: {default_counts.get('offers', 0)}")
            logger.info(f"  - Default creators: {default_counts.get('creators', 0)}")
            logger.info(f"  - Default segments: {default_counts.get('segments', 0)}")
            logger.info(f"  - Random clicks: {random_counts.get('clicks', 0)}")
            logger.info(f"  - Random conversions: {random_counts.get('conversions', 0)}")
        else:
            logger.info("\n✅ Default data seeded successfully!")
            
    except Exception as e:
        logger.error(f"❌ Error during seeding: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
