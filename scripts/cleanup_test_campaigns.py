#!/usr/bin/env python3
"""Clean up duplicate/test campaigns from the database.

Keeps one copy of each featured campaign and removes all others.
Run inside the backend container: docker compose exec backend python3 /app/scripts/cleanup_test_campaigns.py
"""
import sqlite3
import os
import sys

DB_PATH = os.environ.get("DB_PATH", "/app/dungeon_master.db")
if not os.path.exists(DB_PATH):
    # Try local dev path
    DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "dungeon_master.db")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Count before
cur.execute("SELECT COUNT(*) FROM campaigns")
total = cur.fetchone()[0]
print(f"Total campaigns before cleanup: {total}")

# Featured campaigns to keep (one of each)
FEATURED = [
    "Wrath of the Stormspire",
    "The Drowned Throne", 
    "Ember of the Last God",
    "Carnival of Stolen Faces",
    "Iron Oath of Karak-Dum",
]

keep_ids = []
for name in FEATURED:
    cur.execute("SELECT id FROM campaigns WHERE name = ? ORDER BY created_at ASC LIMIT 1", (name,))
    row = cur.fetchone()
    if row:
        keep_ids.append(row[0])
        print(f"  Keep: {name} ({row[0][:8]}...)")

if not keep_ids:
    print("No featured campaigns found. Aborting.")
    sys.exit(1)

placeholders = ",".join(["?"] * len(keep_ids))

# Delete related data first (foreign key constraints)
cur.execute(f"DELETE FROM game_sessions WHERE campaign_id NOT IN ({placeholders})", keep_ids)
print(f"  Deleted {cur.rowcount} game sessions")

cur.execute(f"DELETE FROM characters WHERE campaign_id NOT IN ({placeholders})", keep_ids)
print(f"  Deleted {cur.rowcount} characters")

cur.execute(f"DELETE FROM campaigns WHERE id NOT IN ({placeholders})", keep_ids)
print(f"  Deleted {cur.rowcount} campaigns")

conn.commit()

# Count after
cur.execute("SELECT COUNT(*) FROM campaigns")
remaining = cur.fetchone()[0]
print(f"\nRemaining campaigns: {remaining}")
cur.execute("SELECT name FROM campaigns ORDER BY name")
for row in cur.fetchall():
    print(f"  - {row[0]}")

conn.close()
print("\nCleanup complete!")
