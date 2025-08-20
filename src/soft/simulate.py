
from __future__ import annotations
import random, time, uuid
from .storage import record_click, record_conversion, set_payout_rate, init_db, upsert_segment
from .config import load_policy

POLICY = load_policy()

def gen(n=200, seg="FR:mobile"):
    now = int(time.time())
    for i in range(n):
        ts = now - random.randint(0, 60*60*2)  # last 2h
        click_id = str(uuid.uuid4())
        # fake metrics
        risk = random.random() * 0.6  # most below threshold
        record_click(click_id, ts, "creator_1", "slug", seg, "FR", "mobile", f"fp{i%50}", "offer_a", risk, 1)
        # 10% conv rate with revenue 1.0
        if random.random() < 0.1:
            record_conversion(ts+random.randint(0,600), click_id, "offer_a", 1.0, "approved")
    print(f"seeded {n} clicks on {seg}")

def ensure_creators():
    """Ensure default creators exist in the database"""
    from .storage import upsert_creator
    
    # Default creators for simulation
    default_creators = [
        ("creator_1", 0.7, 50.0),  # creator_id, q, hard_cap_eur
        ("creator_2", 0.5, 30.0),
        ("creator_3", 0.8, 75.0),
    ]
    
    for creator_id, q, hard_cap_eur in default_creators:
        try:
            upsert_creator(creator_id, q, hard_cap_eur)
            print(f"Ensured creator exists: {creator_id}")
        except Exception as e:
            print(f"Error ensuring creator {creator_id}: {e}")

def main():
    # Ensure DB is ready, default segments and creators exist
    try:
        init_db()
        upsert_segment("FR:mobile", "FR", "mobile")
        upsert_segment("FR:desktop", "FR", "desktop")
        ensure_creators()
    except Exception as e:
        print("[simulate] init error:", e)
        return
    
    # Generate clicks for different creators
    creators = ["creator_1", "creator_2", "creator_3"]
    
    # Generate mobile clicks
    for _ in range(100):  # 100 clicks per creator
        creator = random.choice(creators)
        ts = int(time.time()) - random.randint(0, 60*60*2)  # last 2h
        click_id = str(uuid.uuid4())
        risk = random.random() * 0.6  # most below threshold
        record_click(click_id, ts, creator, f"offer_{random.randint(1,5)}", 
                    "FR:mobile", "FR", "mobile", f"fp{random.randint(1,50)}", 
                    f"offer_{random.choice(['a','b','c'])}", risk, 1)
        
        # 10% conversion rate with random revenue
        if random.random() < 0.1:
            revenue = round(random.uniform(0.5, 5.0), 2)
            record_conversion(ts + random.randint(10, 600), click_id, 
                            f"offer_{random.choice(['a','b','c'])}", 
                            revenue, "approved")
    
    # Generate desktop clicks
    for _ in range(50):  # 50 clicks per creator
        creator = random.choice(creators)
        ts = int(time.time()) - random.randint(0, 60*60*2)  # last 2h
        click_id = str(uuid.uuid4())
        risk = random.random() * 0.6  # most below threshold
        record_click(click_id, ts, creator, f"offer_{random.randint(1,5)}", 
                    "FR:desktop", "FR", "desktop", f"fp{random.randint(1,50)}", 
                    f"offer_{random.choice(['a','b','c'])}", risk, 1)
        
        # 10% conversion rate with random revenue
        if random.random() < 0.1:
            revenue = round(random.uniform(0.5, 5.0), 2)
            record_conversion(ts + random.randint(10, 600), click_id, 
                            f"offer_{random.choice(['a','b','c'])}", 
                            revenue, "approved")
    
    print("Simulation completed successfully.")

if __name__ == "__main__":
    main()
