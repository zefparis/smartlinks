#!/usr/bin/env python3
"""
Script pour créer des données de test pour SmartLinks
"""
import random
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.soft.db import SessionLocal, engine
from src.soft.models import Base, Offer, Segment, Creator, Click, Conversion, PayoutRate

def create_sample_data():
    """Crée des données d'exemple pour tester le dashboard"""
    
    # Créer les tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Vérifier si des données existent déjà
        if db.query(Click).count() > 0:
            print("Des données existent déjà, suppression...")
            db.query(Conversion).delete()
            db.query(Click).delete()
            db.query(PayoutRate).delete()
            db.query(Creator).delete()
            db.query(Segment).delete()
            db.query(Offer).delete()
            db.commit()
        
        print("Création des offres...")
        offers = [
            Offer(offer_id="offer_1", name="Gaming App", url="https://example.com/gaming", incent_ok=1, cap_day=1000, geo_allow="US,CA,UK", status="on"),
            Offer(offer_id="offer_2", name="Finance App", url="https://example.com/finance", incent_ok=0, cap_day=500, geo_allow="US,DE,FR", status="on"),
            Offer(offer_id="offer_3", name="Shopping App", url="https://example.com/shop", incent_ok=1, cap_day=2000, geo_allow="ALL", status="on"),
            Offer(offer_id="offer_4", name="Health App", url="https://example.com/health", incent_ok=1, cap_day=800, geo_allow="US,UK,AU", status="on"),
            Offer(offer_id="offer_5", name="Travel App", url="https://example.com/travel", incent_ok=0, cap_day=300, geo_allow="EU", status="on"),
        ]
        
        for offer in offers:
            db.add(offer)
        db.commit()
        
        print("Création des segments...")
        segments = [
            Segment(segment_id="seg_us_mobile", geo="US", device="mobile"),
            Segment(segment_id="seg_us_desktop", geo="US", device="desktop"),
            Segment(segment_id="seg_uk_mobile", geo="UK", device="mobile"),
            Segment(segment_id="seg_de_mobile", geo="DE", device="mobile"),
            Segment(segment_id="seg_fr_desktop", geo="FR", device="desktop"),
            Segment(segment_id="seg_ca_mobile", geo="CA", device="mobile"),
        ]
        
        for segment in segments:
            db.add(segment)
        db.commit()
        
        print("Création des créateurs...")
        creators = [
            Creator(creator_id="creator_001", q=0.8, hard_cap_eur=100.0, last_seen=int(time.time())),
            Creator(creator_id="creator_002", q=0.6, hard_cap_eur=75.0, last_seen=int(time.time() - 3600)),
            Creator(creator_id="creator_003", q=0.9, hard_cap_eur=150.0, last_seen=int(time.time() - 7200)),
            Creator(creator_id="creator_004", q=0.7, hard_cap_eur=80.0, last_seen=int(time.time() - 1800)),
            Creator(creator_id="creator_005", q=0.5, hard_cap_eur=50.0, last_seen=int(time.time() - 10800)),
        ]
        
        for creator in creators:
            db.add(creator)
        db.commit()
        
        print("Création des taux de payout...")
        payout_rates = [
            PayoutRate(segment_id="seg_us_mobile", payout=2.50, updated_at=int(time.time())),
            PayoutRate(segment_id="seg_us_desktop", payout=3.00, updated_at=int(time.time())),
            PayoutRate(segment_id="seg_uk_mobile", payout=2.20, updated_at=int(time.time())),
            PayoutRate(segment_id="seg_de_mobile", payout=2.80, updated_at=int(time.time())),
            PayoutRate(segment_id="seg_fr_desktop", payout=2.60, updated_at=int(time.time())),
            PayoutRate(segment_id="seg_ca_mobile", payout=2.40, updated_at=int(time.time())),
        ]
        
        for rate in payout_rates:
            db.add(rate)
        db.commit()
        
        print("Génération des clics (30 derniers jours)...")
        
        # Générer des clics pour les 30 derniers jours
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        geos = ["US", "UK", "DE", "FR", "CA", "AU", "ES", "IT"]
        devices = ["mobile", "desktop", "tablet"]
        
        click_id_counter = 1
        conversion_id_counter = 1
        
        for day in range(30):
            current_date = start_date + timedelta(days=day)
            timestamp = int(current_date.timestamp())
            
            # Nombre de clics par jour (entre 50 et 200)
            daily_clicks = random.randint(50, 200)
            
            for _ in range(daily_clicks):
                geo = random.choice(geos)
                device = random.choice(devices)
                creator = random.choice(creators)
                offer = random.choice(offers)
                
                # Trouver un segment correspondant ou créer un générique
                segment = None
                for seg in segments:
                    if seg.geo == geo and seg.device == device:
                        segment = seg
                        break
                
                if not segment:
                    segment_id = f"seg_{geo.lower()}_{device}"
                    if not db.query(Segment).filter_by(segment_id=segment_id).first():
                        segment = Segment(segment_id=segment_id, geo=geo, device=device)
                        db.add(segment)
                        db.commit()
                    else:
                        segment = db.query(Segment).filter_by(segment_id=segment_id).first()
                
                # Créer le clic
                click = Click(
                    click_id=f"click_{click_id_counter:06d}",
                    ts=timestamp + random.randint(0, 86400),  # Répartir sur la journée
                    creator_id=creator.creator_id,
                    slug=f"link_{random.randint(1, 100)}",
                    segment_id=segment.segment_id,
                    geo=geo,
                    device=device,
                    fp=f"fp_{random.randint(100000, 999999)}",
                    valid_final=random.choice([0, 1]),
                    risk=random.uniform(0, 1),
                    offer_id=offer.offer_id
                )
                
                db.add(click)
                click_id_counter += 1
                
                # Générer des conversions (taux de conversion ~5-15%)
                if random.random() < 0.10:  # 10% de taux de conversion
                    conversion = Conversion(
                        id=f"conv_{conversion_id_counter:06d}",
                        ts=click.ts + random.randint(60, 3600),  # Conversion dans l'heure
                        click_id=click.click_id,
                        offer_id=offer.offer_id,
                        revenue=random.uniform(1.0, 10.0),
                        status=random.choice(["approved", "pending", "rejected"])
                    )
                    db.add(conversion)
                    conversion_id_counter += 1
        
        db.commit()
        
        # Statistiques
        total_clicks = db.query(Click).count()
        total_conversions = db.query(Conversion).count()
        total_revenue = db.query(Conversion).filter_by(status="approved").count() * 5.0  # Moyenne
        
        print(f"\n✅ Données créées avec succès!")
        print(f"📊 Statistiques:")
        print(f"   - Clics: {total_clicks}")
        print(f"   - Conversions: {total_conversions}")
        print(f"   - Taux de conversion: {(total_conversions/total_clicks*100):.1f}%")
        print(f"   - Revenus estimés: ${total_revenue:.2f}")
        print(f"   - Offres: {len(offers)}")
        print(f"   - Créateurs: {len(creators)}")
        print(f"   - Segments: {db.query(Segment).count()}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des données: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()
