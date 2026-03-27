#!/usr/bin/env python3
"""
Import Guru Export into SQLite
================================
Imports Guru card data from a Guru export file (ZIP or CSV)
into the local SQLite knowledge base.

Supported formats:
  - ZIP export: Contains cards/ folder with YAML metadata + MD/HTML content
  - CSV export: Contains card data with HTML content in columns

Usage:
    python3 import_guru_export.py /path/to/export.zip
    python3 import_guru_export.py /path/to/export.csv
"""

import os
import sys
import csv
import json
import zipfile
import re
from datetime import datetime, timezone
from guru_db import GuruDB

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def html_to_text(html):
    """Convert HTML content to plain text."""
    if not html:
        return ""
    if HAS_BS4:
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator='\n', strip=True)
    # Fallback: basic regex stripping
    text = re.sub(r'<[^>]+>', '', html)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    return text.strip()


def import_csv(filepath, db):
    """Import cards from a Guru CSV export."""
    print(f"📄 Importing from CSV: {os.path.basename(filepath)}")

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        print(f"   Columns: {columns}")

        count = 0
        for row in reader:
            # Map CSV columns to DB fields (handles multiple naming variants)
            card_id = row.get('ID', row.get('Card ID', row.get('card_id', f"csv_{count}")))
            title = row.get('Title', row.get('title', 'Untitled'))
            content_html = row.get('Content', row.get('content', ''))
            content = html_to_text(content_html)
            collection = row.get('Collection', row.get('Collection Name', row.get('collection', '')))
            folder = row.get('Folders', row.get('folders', ''))
            tags = row.get('Tags', row.get('tags', ''))
            trust_state = row.get('Trust State', row.get('trust_state', ''))
            verified = 1 if trust_state and trust_state.lower() == 'trusted' else 0
            verifier = row.get('Verifier', row.get('verifier', ''))
            verification_interval = row.get('Verification Interval', '')
            created_at = row.get('Date Created', row.get('date_created', ''))
            created_by = row.get('Created By', row.get('created_by', ''))
            updated_at = row.get('Last Modified', row.get('last_modified', ''))
            updated_by = row.get('Last Modified By', row.get('last_modified_by', ''))
            last_verified_at = row.get('Last Verified', row.get('last_verified', ''))
            last_verified_by = row.get('Last Verified By', row.get('last_verified_by', ''))
            times_viewed = int(row.get('Views', row.get('Times Viewed', row.get('times_viewed', 0))) or 0)
            times_favorited = int(row.get('Favorites', row.get('Times Favorited', row.get('times_favorited', 0))) or 0)
            guru_url = row.get('Link', row.get('Card Link', row.get('card_link', '')))

            db.upsert_guru_card(
                id=card_id,
                title=title,
                content=content,
                content_html=content_html,
                collection=collection,
                folder=folder,
                tags=tags,
                verified=verified,
                verifier=verifier,
                verification_interval=verification_interval,
                created_at=created_at,
                created_by=created_by,
                updated_at=updated_at,
                updated_by=updated_by,
                last_verified_at=last_verified_at,
                last_verified_by=last_verified_by,
                times_viewed=times_viewed,
                times_favorited=times_favorited,
                guru_url=guru_url
            )
            count += 1

            if count % 50 == 0:
                print(f"   Imported {count} cards...")

    db.log_import('csv', os.path.basename(filepath), count)
    print(f"\n✅ Imported {count} cards from CSV")
    return count


def import_zip(filepath, db):
    """Import cards from a Guru ZIP export."""
    print(f"📦 Importing from ZIP: {os.path.basename(filepath)}")

    if not HAS_YAML:
        print("⚠️  PyYAML not installed. Installing...")
        os.system(f"{sys.executable} -m pip install pyyaml")
        import yaml

    with zipfile.ZipFile(filepath, 'r') as zf:
        file_list = zf.namelist()
        print(f"   ZIP contains {len(file_list)} files")

        # Find card files
        card_files = {}
        for f in file_list:
            if '/cards/' in f or f.startswith('cards/'):
                # Group by card ID (basename without extension)
                basename = os.path.splitext(os.path.basename(f))[0]
                if basename not in card_files:
                    card_files[basename] = {}
                ext = os.path.splitext(f)[1].lower()
                card_files[basename][ext] = f

        print(f"   Found {len(card_files)} cards in archive")

        # Parse collection.yaml if present
        collection_name = ''
        for f in file_list:
            if f.endswith('collection.yaml'):
                try:
                    data = yaml.safe_load(zf.read(f))
                    collection_name = data.get('Name', data.get('name', ''))
                    print(f"   Collection: {collection_name}")
                except Exception:
                    pass

        count = 0
        for card_id, files in card_files.items():
            title = card_id
            content = ''
            content_html = ''
            tags = ''
            folder = ''

            # Read YAML metadata
            if '.yaml' in files or '.yml' in files:
                yaml_file = files.get('.yaml', files.get('.yml', ''))
                try:
                    meta = yaml.safe_load(zf.read(yaml_file))
                    title = meta.get('Title', meta.get('title', card_id))
                    tags = ', '.join(meta.get('Tags', meta.get('tags', [])) or [])
                    folder = meta.get('Folder', meta.get('folder', ''))
                except Exception:
                    pass

            # Read content (prefer MD over HTML)
            if '.md' in files:
                content = zf.read(files['.md']).decode('utf-8', errors='replace')
            if '.html' in files:
                content_html = zf.read(files['.html']).decode('utf-8', errors='replace')
                if not content:
                    content = html_to_text(content_html)

            db.upsert_guru_card(
                id=card_id,
                title=title,
                content=content,
                content_html=content_html,
                collection=collection_name,
                folder=folder,
                tags=tags
            )
            count += 1

            if count % 50 == 0:
                print(f"   Imported {count} cards...")

        db.log_import('zip', os.path.basename(filepath), count)
        print(f"\n✅ Imported {count} cards from ZIP")
        return count


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 import_guru_export.py <export_file.zip|.csv>")
        print("\nSupported formats:")
        print("  - ZIP export (from Guru collection export)")
        print("  - CSV export (from Guru Card Manager export)")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    db = GuruDB()

    if filepath.lower().endswith('.csv'):
        count = import_csv(filepath, db)
    elif filepath.lower().endswith('.zip'):
        count = import_zip(filepath, db)
    else:
        print(f"❌ Unsupported format. Use .csv or .zip")
        sys.exit(1)

    # Show stats
    stats = db.get_stats()
    print(f"\n📊 Database now contains:")
    print(f"   📚 Guru cards:    {stats['guru_cards']} ({stats['verified_cards']} verified)")
    print(f"   📝 Pending cards: {stats['pending_cards']}")
    print(f"   💬 Slack threads: {stats['slack_threads']}")

    db.close()


if __name__ == "__main__":
    main()
