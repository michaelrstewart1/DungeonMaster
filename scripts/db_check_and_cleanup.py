#!/usr/bin/env python3
"""Check DB state and clean up test data.
Run: docker compose exec backend python3 /app/scripts/db_check_and_cleanup.py
"""
import sqlite3
import sys

DB = "/app/dungeon_master.db"
try:
    conn = sqlite3.connect(DB)
except:
    DB = "dungeon_master.db"
    conn = sqlite3.connect(DB)

cur = conn.cursor()

# Count everything
cur.execute("SELECT COUNT(*) FROM campaigns")
print(f"Campaigns: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM characters")
print(f"Characters: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM game_sessions")
print(f"Game sessions: {cur.fetchone()[0]}")

# Check for echo in stored messages
cur.execute("SELECT id FROM game_sessions WHERE extra_data LIKE '%You I check%' LIMIT 5")
echoed = cur.fetchall()
print(f"Sessions with echo bug in stored data: {len(echoed)}")

# --- CLEANUP ---
# Featured campaigns to keep (oldest instance of each)
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
        print(f"  Keep: {name} ({row[0][:12]}...)")

if not keep_ids:
    print("No featured campaigns found, aborting cleanup")
    conn.close()
    sys.exit(1)

placeholders = ",".join(["?"] * len(keep_ids))

# Delete game sessions for doomed campaigns
cur.execute(f"DELETE FROM game_sessions WHERE campaign_id NOT IN ({placeholders})", keep_ids)
print(f"Deleted {cur.rowcount} game sessions")

# Delete characters for doomed campaigns
cur.execute(f"DELETE FROM characters WHERE campaign_id NOT IN ({placeholders})", keep_ids)
print(f"Deleted {cur.rowcount} characters")

# Delete campaigns
cur.execute(f"DELETE FROM campaigns WHERE id NOT IN ({placeholders})", keep_ids)
print(f"Deleted {cur.rowcount} campaigns")

# Also clean stale game sessions for kept campaigns (reset for fresh testing)
cur.execute(f"DELETE FROM game_sessions WHERE campaign_id IN ({placeholders})", keep_ids)
print(f"Deleted {cur.rowcount} stale game sessions from kept campaigns")

conn.commit()

# Final counts
cur.execute("SELECT COUNT(*) FROM campaigns")
print(f"\nFinal campaigns: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM characters")
print(f"Final characters: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM game_sessions")
print(f"Final game sessions: {cur.fetchone()[0]}")

cur.execute("SELECT name FROM campaigns ORDER BY name")
for row in cur.fetchall():
    print(f"  - {row[0]}")

conn.close()
print("\nCleanup complete!")
