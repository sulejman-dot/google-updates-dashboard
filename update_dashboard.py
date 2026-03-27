#!/usr/bin/env python3
"""
Update Dashboard Data
======================
Exports guru_knowledge.db → guru-dashboard/data.json
and pushes to GitHub for auto-deploy on Netlify.

Usage:
    python3 update_dashboard.py         # Export only
    python3 update_dashboard.py --push  # Export + git push
"""

import os
import sys
import csv
import json
import re
import sqlite3
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "guru_knowledge.db")
DASHBOARD_DIR = os.path.join(SCRIPT_DIR, "guru-dashboard")
DATA_JSON = os.path.join(DASHBOARD_DIR, "data.json")
CSV_PATH = os.path.expanduser("~/Downloads/guru_card_export (1).csv")


def classify(title, content):
    """Classify a card into a topic category."""
    t = (title or '').lower()
    c = (content or '').lower()[:300]
    combined = t + ' ' + c
    if any(w in combined for w in ['ai search', 'ais ', 'ai overview', 'aio', 'ai writer', 'ai agent']): return 'AI Features'
    if any(w in combined for w in ['billing', 'invoice', 'payment', 'prepaid', 'credit', 'subscription', 'pricing', 'upgrade', 'downgrade']): return 'Billing & Plans'
    if any(w in combined for w in ['onboarding', 'wizard', 'setup', 'training', 'case study', 'sid:']): return 'Onboarding'
    if any(w in combined for w in ['competition', 'competitor', 'brand rule']): return 'Competition'
    if any(w in combined for w in ['forecast', 'seo forecast', 'objective', 'target']): return 'Forecast'
    if any(w in combined for w in ['api', 'integration', 'webhook', 'mcp', 'zapier']): return 'Integrations'
    if any(w in combined for w in ['ga4', 'google analytics', 'traffic', 'sessions', 'landing page']): return 'Analytics'
    if any(w in combined for w in ['content', 'writer', 'topic', 'daily digest']): return 'Content'
    if any(w in combined for w in ['report', 'export', 'download', 'pdf']): return 'Reports'
    if any(w in combined for w in ['rank track', 'ranking', 'serp', 'keyword', 'visibility', 'search volume']): return 'Rank Tracking'
    if any(w in combined for w in ['campaign', 'site ', 'account', 'admin']): return 'Campaigns'
    if any(w in combined for w in ['data', 'metric', 'score', 'ctr', 'click', 'impression']): return 'Data & Metrics'
    return 'General'


def html_to_text(html):
    if not html: return ''
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    return text.strip()


def clean_html(html):
    if not html: return ''
    html = re.sub(r'\s+data-[a-z-]+="[^"]*"', '', html)
    html = re.sub(r'\s+class="[^"]*"', '', html)
    html = re.sub(r'\s+id="[^"]*"', '', html)
    html = html.replace('<a ', '<a target="_blank" rel="noopener" ')
    return html.strip()


def export_data():
    """Export database + CSV data to data.json for the dashboard."""
    print("📦 Exporting dashboard data...")

    cards = []
    cats = {}

    # Load from CSV if available (has full HTML)
    if os.path.exists(CSV_PATH):
        print(f"   Using CSV: {os.path.basename(CSV_PATH)}")
        with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = row.get('Title', 'Untitled')
                content_html = row.get('Content', '')
                content_text = html_to_text(content_html)
                cat = classify(title, content_text)
                cats[cat] = cats.get(cat, 0) + 1
                cards.append({
                    'id': row.get('ID', ''),
                    'title': title,
                    'text': content_text[:200],
                    'html': clean_html(content_html),
                    'category': cat
                })
        cards.sort(key=lambda c: c['title'])
    else:
        # Fallback to SQLite (text only)
        print("   Using SQLite database (no CSV found)")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        for row in conn.execute('SELECT id, title, content FROM guru_cards ORDER BY title'):
            title = row['title']
            content = row['content'] or ''
            cat = classify(title, content)
            cats[cat] = cats.get(cat, 0) + 1
            cards.append({
                'id': row['id'], 'title': title,
                'text': content[:200], 'html': f'<p>{content}</p>',
                'category': cat
            })
        conn.close()

    # Add pending cards from DB
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    pending = []
    for row in conn.execute('SELECT id, title, question, answer, content_md, status, created_at, slack_permalink FROM pending_cards ORDER BY created_at DESC'):
        answer = row['answer'] or row['question'] or ''
        pending.append({
            'id': row['id'], 'title': row['title'],
            'text': (row['question'] or '')[:200],
            'html': f'<p>{answer}</p>',
            'status': row['status'] or '',
            'created_at': row['created_at'] or '',
            'slack_permalink': row['slack_permalink'] or '',
            'category': 'Pending'
        })
    conn.close()

    data = {
        'cards': cards,
        'pending': pending,
        'categories': dict(sorted(cats.items(), key=lambda x: -x[1]))
    }

    os.makedirs(DASHBOARD_DIR, exist_ok=True)
    with open(DATA_JSON, 'w') as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"   ✅ Exported {len(cards)} cards + {len(pending)} pending → data.json")
    print(f"   📊 Categories: {', '.join(cats.keys())}")
    return data


def git_push():
    """Commit and push to GitHub for Netlify auto-deploy."""
    print("\n🚀 Pushing to GitHub...")
    try:
        subprocess.run(['git', 'add', '-A'], cwd=DASHBOARD_DIR, check=True)
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=DASHBOARD_DIR, capture_output=True)
        if result.returncode == 0:
            print("   ℹ️  No changes to push")
            return
        subprocess.run(['git', 'commit', '-m', 'Update dashboard data'], cwd=DASHBOARD_DIR, check=True)
        subprocess.run(['git', 'push'], cwd=DASHBOARD_DIR, check=True)
        print("   ✅ Pushed to GitHub — Netlify will auto-deploy!")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Git error: {e}")


if __name__ == "__main__":
    export_data()
    if "--push" in sys.argv:
        git_push()
