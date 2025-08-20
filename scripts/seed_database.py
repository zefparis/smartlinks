#!/usr/bin/env python3
"""
Script de génération massive de données pour SmartLinks Dashboard
Génère des données réalistes pour 30 jours d'activité avec volumes importants

Usage:
    python scripts/seed_database.py
    
Options:
    --days N        Nombre de jours de données à générer (défaut: 30)
    --volume high   Volume élevé de données (défaut: medium)
    --clean         Nettoyer les données existantes avant génération
"""

import sys
import os
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.soft.db import SessionLocal, engine
from src.soft.models import Base, Offer, Segment, Creator, Click, Conversion, PayoutRate
import random
import time
from datetime import datetime, timedelta

def generate_data(days=30, volume='medium', clean=True):
    """
    Génère des données de test pour le dashboard SmartLinks
    
    Args:
        days (int): Nombre de jours de données à générer
        volume (str): Volume de données ('low', 'medium', 'high')
        clean (bool): Nettoyer les données existantes
    """
    print('🔧 GÉNÉRATION MASSIVE DE DONNÉES SMARTLINKS')
    print('=' * 60)
    print(f'📅 Période: {days} jours')
    print(f'📊 Volume: {volume}')
    print(f'🧹 Nettoyage: {"Oui" if clean else "Non"}')
    print('')
    
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Nettoyer si demandé
        if clean:
            print('🧹 Nettoyage base de données...')
            for table in [Conversion, Click, PayoutRate, Creator, Segment, Offer]:
                db.query(table).delete()
            db.commit()
            print('   ✅ Base nettoyée')
        
        # Vérifier si des données existent déjà
        existing_clicks = db.query(Click).count()
        if existing_clicks > 0 and not clean:
            print(f'⚠️  {existing_clicks:,} clics existants détectés')
            response = input('Continuer quand même? (y/N): ')
            if response.lower() != 'y':
                print('❌ Génération annulée')
                return False
        
        # Créer offres
        print('🎯 Création des offres...')
        offers_data = [
            ('gaming_premium', 'Gaming App Premium', 'https://gaming.example.com', 1, 2000, 'US,UK,CA,AU'),
            ('finance_pro', 'Finance Trading Pro', 'https://finance.example.com', 0, 1000, 'US,DE,FR,UK'),
            ('ecommerce_plus', 'E-commerce Platform Plus', 'https://shop.example.com', 1, 3000, 'ALL'),
            ('fitness_tracker', 'Fitness Tracker Pro', 'https://fitness.example.com', 1, 1500, 'US,UK,AU,CA'),
            ('crypto_exchange', 'Crypto Exchange Pro', 'https://crypto.example.com', 0, 800, 'US,UK,DE,FR'),
            ('travel_booking', 'Travel Booking Pro', 'https://travel.example.com', 1, 1200, 'US,UK,DE,FR,ES'),
            ('food_delivery', 'Food Delivery Plus', 'https://food.example.com', 1, 2500, 'ALL'),
            ('streaming_service', 'Streaming Service Pro', 'https://streaming.example.com', 1, 1800, 'ALL'),
        ]
        
        offers = []
        for offer_id, name, url, incent, cap, geo in offers_data:
            # Vérifier si l'offre existe déjà
            existing_offer = db.query(Offer).filter_by(offer_id=offer_id).first()
            if not existing_offer:
                offer = Offer(offer_id=offer_id, name=name, url=url, incent_ok=incent, cap_day=cap, geo_allow=geo, status='on')
                offers.append(offer)
                db.add(offer)
            else:
                offers.append(existing_offer)
        db.commit()
        print(f'   ✅ {len(offers)} offres configurées')
        
        # Créer segments
        print('🌍 Création des segments...')
        geos = ['US', 'UK', 'DE', 'FR', 'CA', 'AU', 'ES', 'IT', 'NL', 'SE', 'NO', 'DK']
        devices = ['mobile', 'desktop', 'tablet']
        segments = []
        
        for geo in geos:
            for device in devices:
                segment_id = f'seg_{geo.lower()}_{device}'
                existing_segment = db.query(Segment).filter_by(segment_id=segment_id).first()
                if not existing_segment:
                    segment = Segment(segment_id=segment_id, geo=geo, device=device)
                    segments.append(segment)
                    db.add(segment)
                else:
                    segments.append(existing_segment)
        db.commit()
        print(f'   ✅ {len(segments)} segments configurés')
        
        # Créer créateurs
        print('👥 Création des créateurs...')
        creators = []
        num_creators = 20 if volume == 'high' else 15 if volume == 'medium' else 10
        
        for i in range(num_creators):
            creator_id = f'creator_{i+1:03d}'
            existing_creator = db.query(Creator).filter_by(creator_id=creator_id).first()
            if not existing_creator:
                creator = Creator(
                    creator_id=creator_id,
                    q=random.uniform(0.4, 0.95),
                    hard_cap_eur=random.uniform(50, 400),
                    last_seen=int(time.time() - random.randint(0, 172800))
                )
                creators.append(creator)
                db.add(creator)
            else:
                creators.append(existing_creator)
        db.commit()
        print(f'   ✅ {len(creators)} créateurs configurés')
        
        # Créer taux de payout
        print('💰 Création des taux de payout...')
        payout_count = 0
        for segment in segments:
            existing_payout = db.query(PayoutRate).filter_by(segment_id=segment.segment_id).first()
            if not existing_payout:
                base_payout = 2.5
                if segment.geo in ['US', 'UK', 'CA']:
                    base_payout = 4.0  # Tier 1
                elif segment.geo in ['DE', 'FR', 'AU']:
                    base_payout = 3.2  # Tier 2
                elif segment.geo in ['ES', 'IT', 'NL']:
                    base_payout = 2.8  # Tier 3
                
                if segment.device == 'mobile':
                    base_payout *= 1.1
                
                payout = PayoutRate(
                    segment_id=segment.segment_id,
                    payout=round(base_payout + random.uniform(-0.5, 0.8), 2),
                    updated_at=int(time.time())
                )
                db.add(payout)
                payout_count += 1
        db.commit()
        print(f'   ✅ {payout_count} taux de payout configurés')
        
        # Génération MASSIVE de clics et conversions
        print(f'🚀 GÉNÉRATION MASSIVE DE DONNÉES ({days} jours)...')
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Multiplicateurs de volume
        volume_multipliers = {
            'low': 0.5,
            'medium': 1.0,
            'high': 2.0
        }
        multiplier = volume_multipliers.get(volume, 1.0)
        
        click_id = db.query(Click).count() + 1  # Continuer la numérotation
        conv_id = db.query(Conversion).count() + 1
        total_revenue = 0
        total_clicks = 0
        total_conversions = 0
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            base_timestamp = int(current_date.timestamp())
            
            # Volume progressif - plus récent = plus d'activité
            if day > days * 0.8:  # 20% derniers jours
                base_daily_clicks = random.randint(1200, 2500)
            elif day > days * 0.6:  # 40% derniers jours
                base_daily_clicks = random.randint(800, 1800)
            elif day > days * 0.4:  # 60% derniers jours
                base_daily_clicks = random.randint(600, 1200)
            elif current_date.weekday() >= 5:  # Weekends
                base_daily_clicks = random.randint(400, 1000)
            else:
                base_daily_clicks = random.randint(300, 800)
            
            daily_clicks = int(base_daily_clicks * multiplier)
            day_revenue = 0
            day_conversions = 0
            
            for _ in range(daily_clicks):
                # Répartition horaire réaliste
                hour_weights = [1,1,1,1,2,3,5,8,12,15,18,20,22,20,18,16,14,12,10,8,6,4,3,2]
                hour = random.choices(range(24), weights=hour_weights, k=1)[0]
                timestamp = base_timestamp + (hour * 3600) + random.randint(0, 3599)
                
                # Distribution géographique pondérée
                geo = random.choices(geos, weights=[30,20,15,12,10,8,6,5,4,3,2,1], k=1)[0]
                device = random.choices(devices, weights=[70,25,5], k=1)[0]  # Mobile dominant
                
                click = Click(
                    click_id=f'click_{click_id:08d}',
                    ts=timestamp,
                    creator_id=random.choice(creators).creator_id,
                    slug=f'smartlink_{random.randint(1, 2000)}',
                    segment_id=f'seg_{geo.lower()}_{device}',
                    geo=geo,
                    device=device,
                    fp=f'fp_{random.randint(10000000, 99999999)}',
                    valid_final=random.choices([0, 1], weights=[8, 92], k=1)[0],  # 92% valid
                    risk=random.uniform(0, 0.7),
                    offer_id=random.choice(offers).offer_id
                )
                db.add(click)
                
                # Taux de conversion sophistiqué
                base_conv_rate = 0.10  # 10% de base
                
                # Bonus geo
                if geo in ['US', 'UK', 'CA']:
                    base_conv_rate = 0.16  # Tier 1: 16%
                elif geo in ['DE', 'FR', 'AU']:
                    base_conv_rate = 0.13  # Tier 2: 13%
                elif geo in ['ES', 'IT', 'NL']:
                    base_conv_rate = 0.11  # Tier 3: 11%
                
                # Bonus device
                if device == 'mobile':
                    base_conv_rate *= 1.25  # Mobile convertit mieux
                elif device == 'tablet':
                    base_conv_rate *= 1.15
                
                # Bonus temporel (plus récent = meilleur)
                if day > days * 0.8:
                    base_conv_rate *= 1.2
                elif day > days * 0.6:
                    base_conv_rate *= 1.1
                
                if random.random() < base_conv_rate:
                    # Revenue sophistiqué
                    base_revenue = random.uniform(4.0, 35.0)
                    
                    # Multiplicateurs geo
                    if geo in ['US', 'UK']:
                        base_revenue *= 1.8
                    elif geo in ['CA', 'AU']:
                        base_revenue *= 1.6
                    elif geo in ['DE', 'FR']:
                        base_revenue *= 1.4
                    elif geo in ['ES', 'IT', 'NL']:
                        base_revenue *= 1.2
                    
                    # Multiplicateur device
                    if device == 'desktop':
                        base_revenue *= 1.1
                    
                    revenue = round(base_revenue, 2)
                    
                    conversion = Conversion(
                        id=f'conv_{conv_id:08d}',
                        ts=timestamp + random.randint(30, 14400),  # 30s à 4h de délai
                        click_id=click.click_id,
                        offer_id=click.offer_id,
                        revenue=revenue,
                        status=random.choices(['approved', 'pending', 'rejected'], weights=[88, 10, 2], k=1)[0]
                    )
                    db.add(conversion)
                    
                    if conversion.status == 'approved':
                        day_revenue += revenue
                        total_revenue += revenue
                    
                    day_conversions += 1
                    total_conversions += 1
                    conv_id += 1
                
                click_id += 1
                total_clicks += 1
                
                # Commit par batch pour performance
                if click_id % 10000 == 0:
                    db.commit()
                    print(f'     {click_id:,} clics générés...')
            
            # Commit quotidien
            db.commit()
            conv_rate = (day_conversions / daily_clicks * 100) if daily_clicks > 0 else 0
            print(f'   📅 Jour {day+1:2d}/{days}: {daily_clicks:4d} clics, {day_conversions:3d} conv ({conv_rate:.1f}%), €{day_revenue:7.2f}')
        
        # Statistiques finales
        final_clicks = db.query(Click).count()
        final_conversions = db.query(Conversion).count()
        approved_conv = db.query(Conversion).filter_by(status='approved').count()
        
        print('')
        print('🎉 GÉNÉRATION TERMINÉE AVEC SUCCÈS!')
        print('=' * 60)
        print('📊 STATISTIQUES FINALES:')
        print(f'   ├─ Clics totaux:           {final_clicks:,}')
        print(f'   ├─ Conversions totales:    {final_conversions:,}')
        print(f'   ├─ Conversions approuvées: {approved_conv:,}')
        print(f'   ├─ Taux de conversion:     {(final_conversions/final_clicks*100):.2f}%')
        print(f'   ├─ Revenus totaux:         €{total_revenue:,.2f}')
        print(f'   ├─ Revenue par clic:       €{(total_revenue/final_clicks):.2f}')
        print(f'   ├─ Revenue par conversion: €{(total_revenue/final_conversions):.2f}')
        print(f'   ├─ Offres actives:         {len(offers)}')
        print(f'   ├─ Créateurs actifs:       {len(creators)}')
        print(f'   └─ Segments configurés:    {len(segments)}')
        print('')
        print('✅ DASHBOARD ANALYTICS: 100% OPÉRATIONNEL')
        print('✅ TRAFFIC PAR SEGMENT: 100% OPÉRATIONNEL')
        print('✅ SETTINGS: 100% OPÉRATIONNEL')
        print('')
        
        return True
        
    except Exception as e:
        print(f'❌ ERREUR CRITIQUE: {e}')
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description='Génération de données de test pour SmartLinks')
    parser.add_argument('--days', type=int, default=30, help='Nombre de jours de données (défaut: 30)')
    parser.add_argument('--volume', choices=['low', 'medium', 'high'], default='medium', 
                       help='Volume de données (défaut: medium)')
    parser.add_argument('--clean', action='store_true', help='Nettoyer les données existantes')
    parser.add_argument('--force', action='store_true', help='Forcer la génération sans confirmation')
    
    args = parser.parse_args()
    
    if not args.force:
        print(f'🚀 Génération de {args.days} jours de données (volume: {args.volume})')
        if args.clean:
            print('⚠️  ATTENTION: Les données existantes seront supprimées!')
        response = input('Continuer? (y/N): ')
        if response.lower() != 'y':
            print('❌ Génération annulée')
            return
    
    success = generate_data(days=args.days, volume=args.volume, clean=args.clean)
    
    if success:
        print('🎯 GÉNÉRATION RÉUSSIE - DASHBOARD PRÊT!')
    else:
        print('❌ ÉCHEC DE LA GÉNÉRATION')
        sys.exit(1)

if __name__ == '__main__':
    main()
