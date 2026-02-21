import sqlite3
import random
from datetime import datetime, timedelta
import json

# Connect to database
conn = sqlite3.connect('saas_metrics.db')
c = conn.cursor()

# 1. Create Tables (Complex Schema)
c.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        signup_date DATE,
        country TEXT,
        acquisition_channel TEXT
    );

    CREATE TABLE IF NOT EXISTS subscriptions (
        sub_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        plan_name TEXT, -- 'Basic', 'Pro', 'Enterprise'
        amount REAL,
        start_date DATE,
        end_date DATE, -- NULL means active
        status TEXT -- 'active', 'cancelled', 'churned'
    );

    CREATE TABLE IF NOT EXISTS app_events (
        event_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        event_type TEXT, -- 'login', 'export_report', 'invite_user'
        timestamp DATETIME,
        metadata_json TEXT -- JSON string e.g., {"browser": "Chrome", "latency_ms": 200}
    );
''')

# 2. Generate 1,000 Users and messy data
countries = ['US', 'UK', 'DE', 'FR', 'JP']
channels = ['Ads', 'Organic', 'Referral']
plans = {'Basic': 10, 'Pro': 50, 'Enterprise': 200}

users = []
subs = []
events = []

start_date = datetime(2025, 1, 1)

print("Generating complex data...")
for i in range(1, 1001):
    # User
    join_date = start_date + timedelta(days=random.randint(0, 365))
    country = random.choice(countries)
    users.append((i, join_date.strftime('%Y-%m-%d'), country, random.choice(channels)))

    # Subscription (Logic: Some churn, some upgrade)
    plan = random.choice(list(plans.keys()))
    is_churned = random.random() < 0.3 # 30% churn rate
    
    sub_start = join_date
    sub_end = None
    status = 'active'
    
    if is_churned:
        status = 'churned'
        sub_end = sub_start + timedelta(days=random.randint(30, 180))
    
    subs.append((i, plan, plans[plan], sub_start.strftime('%Y-%m-%d'), 
                 sub_end.strftime('%Y-%m-%d') if sub_end else None, status))

    # Events (JSON data requires parsing)
    for _ in range(random.randint(5, 50)):
        event_time = join_date + timedelta(hours=random.randint(1, 2000))
        meta = json.dumps({"browser": random.choice(["Chrome", "Safari"]), "latency": random.randint(50, 500)})
        events.append((i, random.choice(['login', 'export_report']), event_time.strftime('%Y-%m-%d %H:%M:%S'), meta))

# Bulk Insert
c.executemany('INSERT INTO users VALUES (?,?,?,?)', users)
c.executemany('INSERT INTO subscriptions (user_id, plan_name, amount, start_date, end_date, status) VALUES (?,?,?,?,?,?)', subs)
c.executemany('INSERT INTO app_events (user_id, event_type, timestamp, metadata_json) VALUES (?,?,?,?)', events)

conn.commit()
print("Database 'saas_metrics.db' created with 1000 users, subscriptions, and ~25k events.")
conn.close()
