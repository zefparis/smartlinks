#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de génération massive de données pour SmartLinks Analytics
Optimisé pour Windows avec gestion robuste des paths et encodage
"""

import sys
import os
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.soft.db import SessionLocal, engine
    from src.soft.models import Base, Offer, Segment, Creator, Click, Conversion
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Vérifiez que vous êtes dans le bon répertoire et que les dépendances sont installées")
    sys.exit(1)


def clean_database(db):
    """Nettoie complètement la base de données"""
    print("🧹 Nettoyage de la base de données...")
    try:
        # Ordre important pour respecter les contraintes de clés étrangères
        db.execute('DELETE FROM conversions')
        db.execute('DELETE FROM clicks')
        db.execute('DELETE FROM creators')
        db.execute('DELETE FROM segments')
        db.execute('DELETE FROM offers')
        db.commit()
        print("   ✅ Base nettoyée")
    except Exception as e:
        print(f"   ❌ Erreur lors du nettoyage: {e}")
        db.rollback()
        raise


def create_base_data(db):
    """Crée les données de base (offres, segments, créateurs)"""
    print("📊 Création des données de base...")
    
    # Créer les offres
    offers_data = [
        ('gaming_premium', 'Gaming App Premium'),
        ('finance_pro', 'Finance Trading Pro'),
        ('ecommerce_plus', 'E-commerce Platform Plus'),
        ('fitness_tracker', 'Fitness Tracker Pro'),
        ('crypto_exchange', 'Crypto Exchange Pro'),
    ]
    
    offers = []
    for offer_id, name in offers_data:
        offer = Offer(
            offer_id=offer_id,
            name=name,
            url=f'https://{offer_id}.example.com',
            incent_ok=1,
            cap_day=2000,
            geo_allow='ALL',
            status='on'
        )
        offers.append(offer)
        db.add(offer)
    
    db.commit()
    print(f"   ✅ {len(offers)} offres créées")
    
    # Créer les segments (geo + device)
    geos = ['US', 'UK', 'DE', 'FR', 'CA', 'AU', 'ES', 'IT', 'NL', 'SE']
    devices = ['mobile', 'desktop', 'tablet']
    
    segments = []
    for geo in geos:
        for device in devices:
            segment = Segment(
                segment_id=f'seg_{geo.lower()}_{device}',
                geo=geo,
                device=device
            )
            segments.append(segment)
            db.add(segment)
    
    db.commit()
    print(f"   ✅ {len(segments)} segments créés")
    
    # Créer les créateurs
    creators = []
    for i in range(15):
        creator = Creator(
            creator_id=f'creator_{i+1:03d}',
            q=random.uniform(0.7, 0.9),
            hard_cap_eur=random.uniform(50.0, 200.0),
            last_seen=int(time.time())
        )
        creators.append(creator)
        db.add(creator)
    
    db.commit()
    print(f"   ✅ {len(creators)} créateurs créés")
    
    return offers, segments, creators, geos, devices


def generate_massive_clicks(db, offers, segments, creators, geos, devices, days=30, volume='high'):
    """Génère des clics massifs sur la période spécifiée"""
    print(f"🚀 Génération de clics massifs ({days} jours, volume: {volume})...")
    
    # Définir le volume selon le paramètre
    if volume == 'low':
        base_daily_clicks = (800, 1500)
    elif volume == 'medium':
        base_daily_clicks = (1500, 3000)
    elif volume == 'high':
        base_daily_clicks = (3000, 6000)
    else:  # ultra
        base_daily_clicks = (5000, 10000)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    click_id = 1
    conv_id = 1
    total_clicks = 0
    total_conversions = 0
    total_revenue = 0
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        base_ts = int(current_date.timestamp())
        
        # Volume progressif (plus récent = plus d'activité)
        progress_factor = (day / days) * 0.5 + 0.75  # Entre 0.75 et 1.25
        daily_clicks = int(random.randint(*base_daily_clicks) * progress_factor)
        
        # Batch pour optimiser les insertions
        clicks_batch = []
        convs_batch = []
        
        for _ in range(daily_clicks):
            ts = base_ts + random.randint(0, 86400)
            geo = random.choice(geos)
            device = random.choice(devices)
            
            # Créer le clic
            click = Click(
                click_id=f'click_{click_id:08d}',
                ts=ts,
                creator_id=random.choice(creators).creator_id,
                slug=f'link_{random.randint(1, 2000)}',
                segment_id=f'seg_{geo.lower()}_{device}',
                geo=geo,
                device=device,
                fp=f'fp_{random.randint(1000000, 9999999)}',
                valid_final=1,
                risk=random.uniform(0.1, 0.3),
                offer_id=random.choice(offers).offer_id
            )
            clicks_batch.append(click)
            total_clicks += 1
            
            # 12-18% de conversions selon le geo
            conversion_rate = 0.15
            if geo in ['US', 'UK', 'CA']:
                conversion_rate = 0.18
            elif geo in ['DE', 'FR', 'NL']:
                conversion_rate = 0.16
            elif geo in ['ES', 'IT']:
                conversion_rate = 0.12
            
            if random.random() < conversion_rate:
                # Revenus variables selon geo et device
                base_revenue = random.uniform(5.0, 25.0)
                if geo in ['US', 'UK']:
                    base_revenue *= 1.5
                if device == 'desktop':
                    base_revenue *= 1.2
                elif device == 'tablet':
                    base_revenue *= 1.1
                
                conv = Conversion(
                    id=f'conv_{conv_id:08d}',
                    ts=ts + random.randint(300, 3600),  # Conversion entre 5min et 1h après
                    click_id=click.click_id,
                    offer_id=click.offer_id,
                    revenue=round(base_revenue, 2),
                    status='approved'
                )
                convs_batch.append(conv)
                total_conversions += 1
                total_revenue += base_revenue
                conv_id += 1
            
            click_id += 1
        
        # Insertion par batch pour optimiser les performances
        db.add_all(clicks_batch)
        db.add_all(convs_batch)
        db.commit()
        
        # Log du progrès
        if day % 5 == 0 or day == days - 1:
            print(f"   Jour {day+1:2d}: {daily_clicks:4d} clics, {len(convs_batch):3d} conversions")
    
    print(f"")
    print(f"🎉 GÉNÉRATION TERMINÉE!")
    print(f"📊 Statistiques finales:")
    print(f"   ├─ Clics totaux: {total_clicks:,}")
    print(f"   ├─ Conversions: {total_conversions:,}")
    print(f"   ├─ Revenus: €{total_revenue:,.2f}")
    print(f"   └─ Taux conversion: {(total_conversions/total_clicks*100):.1f}%")
    
    return total_clicks, total_conversions, total_revenue


def verify_data(db):
    """Vérifie que les données ont été correctement générées"""
    print("🔍 Vérification des données générées...")
    
    try:
        # Compter les données
        clicks_count = db.query(Click).count()
        conversions_count = db.query(Conversion).count()
        segments_count = db.query(Segment).count()
        offers_count = db.query(Offer).count()
        creators_count = db.query(Creator).count()
        
        print(f"📊 Données en base:")
        print(f"   ├─ Clics: {clicks_count:,}")
        print(f"   ├─ Conversions: {conversions_count:,}")
        print(f"   ├─ Segments: {segments_count}")
        print(f"   ├─ Offres: {offers_count}")
        print(f"   └─ Créateurs: {creators_count}")
        
        # Vérifier les segments avec données
        segment_stats = db.execute('''
            SELECT 
                s.segment_id,
                s.geo,
                s.device,
                COUNT(c.click_id) as clicks,
                COUNT(conv.id) as conversions
            FROM segments s
            LEFT JOIN clicks c ON s.segment_id = c.segment_id
            LEFT JOIN conversions conv ON c.click_id = conv.click_id AND conv.status = 'approved'
            GROUP BY s.segment_id, s.geo, s.device
            HAVING COUNT(c.click_id) > 0
            ORDER BY clicks DESC
            LIMIT 8
        ''').fetchall()
        
        print(f"")
        print(f"🌍 Top segments avec données:")
        for row in segment_stats:
            segment_id, geo, device, clicks, conversions = row
            conv_rate = (conversions / clicks * 100) if clicks > 0 else 0
            print(f"   - {segment_id}: {clicks:,} clics, {conversions} conv ({conv_rate:.1f}%)")
        
        print(f"")
        print(f"✅ Données prêtes pour le dashboard Analytics!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False


def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Génération massive de données pour SmartLinks')
    parser.add_argument('--days', type=int, default=30, help='Nombre de jours de données (défaut: 30)')
    parser.add_argument('--volume', choices=['low', 'medium', 'high', 'ultra'], default='high', 
                       help='Volume de données (défaut: high)')
    parser.add_argument('--clean', action='store_true', help='Nettoyer la base avant génération')
    parser.add_argument('--verify-only', action='store_true', help='Seulement vérifier les données existantes')
    
    args = parser.parse_args()
    
    print("🔧 GÉNÉRATION MASSIVE DE DONNÉES SMARTLINKS")
    print("=" * 60)
    print(f"Paramètres: {args.days} jours, volume {args.volume}")
    if args.clean:
        print("Mode: nettoyage + génération")
    elif args.verify_only:
        print("Mode: vérification seulement")
    else:
        print("Mode: génération (sans nettoyage)")
    print("")
    
    # Créer les tables si nécessaire
    Base.metadata.create_all(bind=engine)
    
    # Connexion à la base
    db = SessionLocal()
    
    try:
        if args.verify_only:
            # Seulement vérifier
            verify_data(db)
            return
        
        if args.clean:
            # Nettoyer la base
            clean_database(db)
        
        # Créer les données de base
        offers, segments, creators, geos, devices = create_base_data(db)
        
        # Générer les clics massifs
        generate_massive_clicks(db, offers, segments, creators, geos, devices, 
                              days=args.days, volume=args.volume)
        
        # Vérifier le résultat
        verify_data(db)
        
        print("")
        print("🔄 ÉTAPES SUIVANTES:")
        print("   1. Redémarrer le backend: python main.py")
        print("   2. Ouvrir le frontend: http://localhost:3000/analytics")
        print("   3. Vérifier que toutes les données s'affichent")
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
