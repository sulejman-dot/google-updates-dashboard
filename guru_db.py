#!/usr/bin/env python3
"""
Guru Knowledge Base — SQLite Database
=======================================
Simple database storing Guru card titles + content,
plus pending cards generated from Slack threads.

Usage:
    from guru_db import GuruDB
    db = GuruDB()
    db.upsert_guru_card(id="abc", title="...", content="...")
    db.insert_pending_card(title="...", question="...", answer="...")
    db.get_stats()
"""

import os
import re
import sqlite3
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "guru_knowledge.db")


class GuruDB:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS guru_cards (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT
            );

            CREATE TABLE IF NOT EXISTS pending_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                question TEXT,
                answer TEXT,
                content_md TEXT,
                slack_thread_ts TEXT UNIQUE,
                slack_channel TEXT,
                slack_permalink TEXT,
                classification TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS slack_threads (
                thread_ts TEXT PRIMARY KEY,
                channel TEXT,
                classification TEXT,
                question_preview TEXT,
                has_answer INTEGER DEFAULT 0,
                has_guru_card INTEGER DEFAULT 0,
                guru_card_url TEXT,
                processed_at TEXT
            );
        """)
        self.conn.commit()

    # ── Guru Cards ──────────────────────────────────────────────────────

    def upsert_guru_card(self, **kwargs):
        kwargs.setdefault('id', f"card_{datetime.now().timestamp()}")
        self.conn.execute(
            "INSERT OR REPLACE INTO guru_cards (id, title, content) VALUES (?, ?, ?)",
            (kwargs['id'], kwargs.get('title', ''), kwargs.get('content', ''))
        )
        self.conn.commit()

    def search_guru_cards(self, query):
        return self.conn.execute(
            "SELECT * FROM guru_cards WHERE title LIKE ? OR content LIKE ? ORDER BY title",
            (f'%{query}%', f'%{query}%')
        ).fetchall()

    def get_all_guru_cards(self):
        return self.conn.execute("SELECT * FROM guru_cards ORDER BY title").fetchall()

    # ── Pending Cards ───────────────────────────────────────────────────

    def insert_pending_card(self, **kwargs):
        kwargs.setdefault('created_at', datetime.now(timezone.utc).isoformat())
        kwargs.setdefault('status', 'pending')
        cols = ', '.join(kwargs.keys())
        placeholders = ', '.join(['?'] * len(kwargs))
        try:
            self.conn.execute(f"INSERT INTO pending_cards ({cols}) VALUES ({placeholders})",
                              list(kwargs.values()))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_pending_cards(self, status='pending'):
        return self.conn.execute(
            "SELECT * FROM pending_cards WHERE status = ? ORDER BY created_at DESC",
            (status,)
        ).fetchall()

    # ── Slack Threads ───────────────────────────────────────────────────

    def upsert_slack_thread(self, **kwargs):
        kwargs.setdefault('processed_at', datetime.now(timezone.utc).isoformat())
        cols = ', '.join(kwargs.keys())
        placeholders = ', '.join(['?'] * len(kwargs))
        updates = ', '.join(f'{k}=excluded.{k}' for k in kwargs.keys() if k != 'thread_ts')
        self.conn.execute(f"""
            INSERT INTO slack_threads ({cols}) VALUES ({placeholders})
            ON CONFLICT(thread_ts) DO UPDATE SET {updates}
        """, list(kwargs.values()))
        self.conn.commit()

    def get_processed_threads(self):
        rows = self.conn.execute("SELECT thread_ts FROM slack_threads").fetchall()
        return set(row['thread_ts'] for row in rows)

    # ── Stats ───────────────────────────────────────────────────────────

    def get_stats(self):
        return {
            'guru_cards': self.conn.execute("SELECT COUNT(*) FROM guru_cards").fetchone()[0],
            'pending_cards': self.conn.execute("SELECT COUNT(*) FROM pending_cards WHERE status='pending'").fetchone()[0],
            'slack_threads': self.conn.execute("SELECT COUNT(*) FROM slack_threads").fetchone()[0],
        }

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    db = GuruDB()
    stats = db.get_stats()
    print(f"📊 Guru Knowledge Base:")
    print(f"   📚 Guru cards:    {stats['guru_cards']}")
    print(f"   📝 Pending cards: {stats['pending_cards']}")
    print(f"   💬 Slack threads: {stats['slack_threads']}")
    db.close()
