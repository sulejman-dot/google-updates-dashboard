"""
Guru Knowledge Base Extractor
Extracts all cards from the Customer Success collection and saves them as .md files with images.
"""

import urllib.request
import urllib.parse
import json
import os
import re
import time
from pathlib import Path
from html.parser import HTMLParser

# ── Config ─────────────────────────────────────────────────────────────────────
TOKEN = "Basic Y3VzdG9tZXIuc3VjY2Vzc0BzZW9tb25pdG9yLmNvbTo5ZjMwNjg5NC04NGJlLTQ1N2ItOWQ3MS0wNGQyODA4MTZjOTY="
COLLECTION_ID = "619483f2-3b39-43cc-bd20-c95a01e78405"  # Customer Success
OUTPUT_DIR = Path("/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace/guru_knowledge_base")
# ───────────────────────────────────────────────────────────────────────────────

def api_get(path):
    url = f"https://api.getguru.com{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", TOKEN)
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def download_image(url, dest_path):
    """Download an image from URL to dest_path."""
    try:
        req = urllib.request.Request(url)
        req.add_header("Authorization", TOKEN)
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=15) as resp:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(resp.read())
        return True
    except Exception as e:
        print(f"    ⚠ Could not download image: {url[:60]}... ({e})")
        return False

class HTMLToMarkdown(HTMLParser):
    """Simple HTML → Markdown converter that also extracts image URLs."""
    def __init__(self):
        super().__init__()
        self.md = []
        self.images = []  # list of (src, alt)
        self._in_tag = []
        self._skip = False
        self._href = None
        self._list_depth = 0
        self._ordered = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self._in_tag.append(tag)

        if tag in ("script", "style"):
            self._skip = True
        elif tag == "br":
            self.md.append("\n")
        elif tag == "hr":
            self.md.append("\n---\n")
        elif tag == "h1":
            self.md.append("\n# ")
        elif tag == "h2":
            self.md.append("\n## ")
        elif tag == "h3":
            self.md.append("\n### ")
        elif tag == "h4":
            self.md.append("\n#### ")
        elif tag == "h5":
            self.md.append("\n##### ")
        elif tag == "h6":
            self.md.append("\n###### ")
        elif tag == "p":
            self.md.append("\n")
        elif tag == "strong" or tag == "b":
            self.md.append("**")
        elif tag == "em" or tag == "i":
            self.md.append("_")
        elif tag == "code":
            self.md.append("`")
        elif tag == "pre":
            self.md.append("\n```\n")
        elif tag == "blockquote":
            self.md.append("\n> ")
        elif tag == "ul":
            self._list_depth += 1
            self._ordered.append(False)
        elif tag == "ol":
            self._list_depth += 1
            self._ordered.append(True)
        elif tag == "li":
            indent = "  " * (self._list_depth - 1)
            if self._ordered and self._ordered[-1]:
                self.md.append(f"\n{indent}1. ")
            else:
                self.md.append(f"\n{indent}- ")
        elif tag == "a":
            self._href = attrs.get("href", "")
            self.md.append("[")
        elif tag == "img":
            src = attrs.get("src", "")
            alt = attrs.get("alt", "image")
            if src:
                self.images.append((src, alt))
                # Placeholder — will be replaced with local path after download
                self.md.append(f"\n![{alt}](IMGPLACEHOLDER:{src})\n")
        elif tag == "table":
            self.md.append("\n")
        elif tag == "th":
            self.md.append("| **")
        elif tag == "td":
            self.md.append("| ")
        elif tag == "tr":
            self.md.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False
        elif tag in ("h1","h2","h3","h4","h5","h6"):
            self.md.append("\n")
        elif tag == "p":
            self.md.append("\n")
        elif tag in ("strong", "b"):
            self.md.append("**")
        elif tag in ("em", "i"):
            self.md.append("_")
        elif tag == "code":
            self.md.append("`")
        elif tag == "pre":
            self.md.append("\n```\n")
        elif tag in ("ul", "ol"):
            self._list_depth = max(0, self._list_depth - 1)
            if self._ordered:
                self._ordered.pop()
            self.md.append("\n")
        elif tag == "a":
            href = self._href or ""
            self.md.append(f"]({href})")
            self._href = None
        elif tag in ("th",):
            self.md.append(" **")
        elif tag in ("td",):
            self.md.append(" ")

        if self._in_tag and self._in_tag[-1] == tag:
            self._in_tag.pop()

    def handle_data(self, data):
        if not self._skip:
            # Skip if inside a/img already handled
            self.md.append(data)

    def get_markdown(self):
        return "".join(self.md)


def safe_filename(name):
    """Convert card title to a safe directory/file name."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name[:80]


def api_get_with_next(path):
    """GET request that also returns the next-page URL from Link header."""
    req = urllib.request.Request(f"https://api.getguru.com{path}"
                                 if path.startswith("/") else path)
    req.add_header("Authorization", TOKEN)
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req) as resp:
        link_header = resp.headers.get("Link", "")
        data = json.loads(resp.read())
        # Extract next-page URL from Link header
        next_url = None
        if 'rel="next-page"' in link_header:
            import re
            m = re.search(r'<([^>]+)>;\s*rel="next-page"', link_header)
            if m:
                next_url = m.group(1)
        return data, next_url


def fetch_collection_cards(collection_id):
    """Fetch all CS cards using cursor-based pagination (Link header tokens)."""
    matched = {}  # id -> card, for dedup
    url = f"/api/v1/cards?limit=50"
    page = 0

    print(f"📥 Fetching Customer Success cards (cursor pagination)...")
    while url:
        data, next_url = api_get_with_next(url)
        if not data:
            break
        before = len(matched)
        for c in data:
            if c.get("collection", {}).get("id") == collection_id:
                matched[c["id"]] = c
        found = len(matched) - before
        page += 1
        print(f"  Page {page}: +{found} CS cards (total unique CS: {len(matched)})")
        # Stop early if we've collected all 631
        if len(matched) >= 631:
            print(f"  ✅ Reached 631 CS cards, stopping early.")
            break
        url = next_url
        time.sleep(0.05)

    return list(matched.values())


def fetch_card_content(card_id):
    """Fetch full card content including HTML."""
    try:
        return api_get(f"/api/v1/facts/{card_id}")
    except Exception as e:
        print(f"    ⚠ Could not fetch card {card_id}: {e}")
        return None


def process_card(card, output_dir):
    """Process a single card: extract content, download images, write MD."""
    title = card.get("preferredPhrase", "Untitled")
    card_id = card.get("id", "unknown")
    
    # Fetch full content
    full = fetch_card_content(card_id)
    if not full:
        return False

    html_content = full.get("content", "")
    boards = full.get("boards", [])
    tags = [t.get("value", "") for t in full.get("tags", [])]
    last_modified = full.get("lastModified", "")

    # Create card directory
    safe_name = safe_filename(title)
    card_dir = output_dir / safe_name
    card_dir.mkdir(parents=True, exist_ok=True)
    images_dir = card_dir / "images"

    # Parse HTML → Markdown
    parser = HTMLToMarkdown()
    parser.feed(html_content)
    markdown = parser.get_markdown()
    image_pairs = parser.images  # list of (src, alt)

    # Download images and replace placeholders
    downloaded_images = {}
    for idx, (src, alt) in enumerate(image_pairs):
        ext = os.path.splitext(src.split("?")[0])[1] or ".png"
        img_filename = f"img_{idx+1:03d}{ext}"
        img_path = images_dir / img_filename
        if download_image(src, img_path):
            downloaded_images[src] = f"images/{img_filename}"
        else:
            downloaded_images[src] = src  # fallback to original URL

    # Replace placeholders in markdown
    for src, local_path in downloaded_images.items():
        markdown = markdown.replace(f"IMGPLACEHOLDER:{src}", local_path)

    # Build final MD file
    board_names = " > ".join([b.get("title", "") for b in boards]) if boards else ""
    tags_str = ", ".join(tags) if tags else ""

    md_output = f"""# {title}

> **Collection:** Customer Success{f'  |  **Board:** {board_names}' if board_names else ''}
> **Last Modified:** {last_modified[:10] if last_modified else 'N/A'}
{f'> **Tags:** {tags_str}' if tags_str else ''}

---

{markdown.strip()}
"""

    with open(card_dir / "index.md", "w", encoding="utf-8") as f:
        f.write(md_output)

    return True


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🚀 Guru Knowledge Base Extractor")
    print(f"📁 Output: {OUTPUT_DIR}\n")

    # Fetch all cards from Customer Success
    cards = fetch_collection_cards(COLLECTION_ID)
    print(f"\n✅ Found {len(cards)} cards\n")

    success = 0
    failed = 0

    for i, card in enumerate(cards, 1):
        title = card.get("preferredPhrase", "Untitled")
        print(f"[{i}/{len(cards)}] {title[:70]}")
        try:
            ok = process_card(card, OUTPUT_DIR)
            if ok:
                success += 1
            else:
                failed += 1
        except Exception as e:
            print(f"    ❌ Error: {e}")
            failed += 1
        time.sleep(0.05)  # rate limiting

    print(f"\n{'='*60}")
    print(f"✅ Done! {success} cards extracted, {failed} failed.")
    print(f"📁 Output saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
