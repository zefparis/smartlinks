import sys, os
sys.path.insert(0, os.getcwd())

from src.soft.db import SessionLocal, engine
from src.soft.models import Base, Offer, Segment, Creator, Click, Conversion, PayoutRate
import random, time
from datetime import datetime, timedelta

print("🚀 GÉNÉRATION MASSIVE DE DONNÉES")
print("=" * 40)

Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    # Nettoyer
    for table in [Conversion, Click, PayoutRate, Creator, Segment, Offer]:
        db.query(table).delete()
    db.commit()
    print("✅ Base nettoyée")
    
    # Offres
    offers_data = [
        ("gaming_premium", "Gaming App Premium"),
        ("finance_pro", "Finance Trading Pro"),
        ("ecommerce_plus", "E-commerce Platform Plus"),
        ("fitness_tracker", "Fitness Tracker Pro"),
        ("crypto_exchange", "Crypto Exchange Pro"),
    ]
    
    offers = []
    for oid, name in offers_data:
        offer = Offer(offer_id=oid, name=name, url=f"https://{oid}.example.com", incent_ok=1, cap_day=2000, geo_allow="ALL", status="on")
        offers.append(offer)
        db.add(offer)
    db.commit()
    print(f"✅ {len(offers)} offres")
    
    # Segments
    geos = ["US", "UK", "DE", "FR", "CA", "AU", "ES", "IT"]
    devices = ["mobile", "desktop", "tablet"]
    
    for geo in geos:
        for device in devices:
            segment = Segment(segment_id=f"seg_{geo.lower()}_{device}", geo=geo, device=device)
            db.add(segment)
    db.commit()
    print(f"✅ {len(geos)*len(devices)} segments")
    
    # Créateurs
    creators = []
    for i in range(10):
        creator = Creator(creator_id=f"creator_{i+1:03d}", q=0.8, hard_cap_eur=100.0, last_seen=int(time.time()))
        creators.append(creator)
        db.add(creator)
    db.commit()
    print(f"✅ {len(creators)} créateurs")
    
    # Clics massifs
    print("🚀 Génération clics (30 jours)...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    click_id = 1
    conv_id = 1
    total_revenue = 0
    
    for day in range(30):
        current_date = start_date + timedelta(days=day)
        base_ts = int(current_date.timestamp())
        
        if day > 25:
            daily_clicks = random.randint(2000, 4000)
        elif day > 20:
            daily_clicks = random.randint(1500, 3000)
        else:
            daily_clicks = random.randint(1000, 2000)
        
        day_revenue = 0
        day_conversions = 0
        
        for _ in range(daily_clicks):
            ts = base_ts + random.randint(0, 86400)
            geo = random.choice(geos)
            device = random.choice(devices)
            
            click = Click(
                click_id=f"click_{click_id:08d}",
                ts=ts,
                creator_id=random.choice(creators).creator_id,
                slug=f"link_{random.randint(1,1000)}",
                segment_id=f"seg_{geo.lower()}_{device}",
                geo=geo,
                device=device,
                fp=f"fp_{random.randint(1000000,9999999)}",
                valid_final=1,
                risk=0.2,
                offer_id=random.choice(offers).offer_id
            )
            db.add(click)
            
            # 15% conversions
            if random.random() < 0.15:
                revenue = random.uniform(5.0, 25.0)
                if geo in ["US", "UK"]:
                    revenue *= 1.5
                
                conv = Conversion(
                    id=f"conv_{conv_id:08d}",
                    ts=ts + 1800,
                    click_id=click.click_id,
                    offer_id=click.offer_id,
                    revenue=round(revenue, 2),
                    status="approved"
                )
                db.add(conv)
                day_revenue += revenue
                total_revenue += revenue
                day_conversions += 1
                conv_id += 1
            
            click_id += 1
            
            if click_id % 20000 == 0:
                db.commit()
                print(f"  {click_id:,} clics...")
        
        db.commit()
        if day % 3 == 0:
            print(f"  Jour {day+1}: {daily_clicks} clics, {day_conversions} conv, €{day_revenue:.2f}")
    
    final_clicks = db.query(Click).count()
    final_conversions = db.query(Conversion).count()
    
    print(f"")
    print(f"🎉 GÉNÉRATION TERMINÉE!")
    print(f"📊 {final_clicks:,} clics, {final_conversions:,} conversions")
    print(f"💰 €{total_revenue:,.2f} revenus")
    print(f"✅ DASHBOARD PRÊT!")
    
except Exception as e:
    print(f"❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
