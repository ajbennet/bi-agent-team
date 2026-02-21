import sqlite3
import json

conn = sqlite3.connect('saas_metrics.db')
c = conn.cursor()

print('Tables:')
for row in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(' -', row[0])

print('\nRow counts:')
print(' users:', c.execute('SELECT COUNT(*) FROM users').fetchone()[0])
print(' subscriptions:', c.execute('SELECT COUNT(*) FROM subscriptions').fetchone()[0])
print(' events:', c.execute('SELECT COUNT(*) FROM app_events').fetchone()[0])

print('\nUser distribution by country:')
for row in c.execute('SELECT country, COUNT(*) FROM users GROUP BY country ORDER BY COUNT(*) DESC'):
    print(' ', row[0], row[1])

print('\nUser distribution by acquisition_channel:')
for row in c.execute('SELECT acquisition_channel, COUNT(*) FROM users GROUP BY acquisition_channel ORDER BY COUNT(*) DESC'):
    print(' ', row[0], row[1])

print('\nSubscriptions by plan (count, total_amount):')
for row in c.execute("SELECT plan_name, COUNT(*), ROUND(SUM(amount),2) FROM subscriptions GROUP BY plan_name ORDER BY COUNT(*) DESC"):
    print(' ', row[0], row[1], row[2])

print('\nSubscription status distribution:')
for row in c.execute("SELECT status, COUNT(*) FROM subscriptions GROUP BY status"):
    print(' ', row[0], row[1])

total_subs = c.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
churned = c.execute("SELECT COUNT(*) FROM subscriptions WHERE status='churned'").fetchone()[0]
print('\nChurn rate: {} / {} = {:.2%}'.format(churned, total_subs, churned/total_subs if total_subs else 0))

print('\nActive subscriptions:')
print(' ', c.execute("SELECT COUNT(*) FROM subscriptions WHERE status='active'").fetchone()[0])

print('\nSignup date range:')
print(' ', c.execute("SELECT MIN(signup_date), MAX(signup_date) FROM users").fetchone())

print('\nEvent timestamp range:')
print(' ', c.execute("SELECT MIN(timestamp), MAX(timestamp) FROM app_events").fetchone())

print('\nEvents per user (min, avg, max):')
row = c.execute('SELECT MIN(cnt), AVG(cnt), MAX(cnt) FROM (SELECT COUNT(*) cnt FROM app_events GROUP BY user_id)').fetchone()
print(' ', row)

print('\nTop 5 users by events:')
for row in c.execute('SELECT user_id, COUNT(*) as cnt FROM app_events GROUP BY user_id ORDER BY cnt DESC LIMIT 5'):
    print(' ', row[0], row[1])

print('\nSample users (5):')
for row in c.execute('SELECT * FROM users LIMIT 5'):
    print(' ', row)

print('\nSample subscriptions (5):')
for row in c.execute('SELECT * FROM subscriptions LIMIT 5'):
    print(' ', row)

print('\nSample events (5):')
for row in c.execute('SELECT event_id, user_id, event_type, timestamp, metadata_json FROM app_events LIMIT 5'):
    print(' ', row)

# Check metadata_json validity
invalid = 0
for row in c.execute('SELECT metadata_json FROM app_events'):
    try:
        json.loads(row[0])
    except Exception:
        invalid += 1
print('\nInvalid JSON metadata count:', invalid)

conn.close()
