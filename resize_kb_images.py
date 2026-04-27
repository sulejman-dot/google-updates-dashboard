#!/usr/bin/env python3
"""
Resize base64-encoded images in the KB markdown file to fit Google Docs page width.
- Max width: 750px
- Maintains aspect ratio
- Re-encodes as PNG/JPEG (preserves original format)
- Reports size reduction
"""

import re
import base64
import io
import os
import sys
from PIL import Image

KB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "guru_customer_success_knowledge_base.md")
MAX_WIDTH = 600

# Match base64 image patterns in markdown: ![...](data:image/...;base64,...)
IMG_PATTERN = re.compile(
    r'!\[([^\]]*)\]\((data:image/(png|jpeg|jpg|gif|webp);base64,)([A-Za-z0-9+/=\s]+)\)'
)


def resize_image(b64_data, img_format, max_width=MAX_WIDTH):
    """Decode, resize if needed, and re-encode a base64 image."""
    try:
        raw = base64.b64decode(b64_data)
        img = Image.open(io.BytesIO(raw))

        orig_w, orig_h = img.size

        if orig_w <= max_width:
            return None, orig_w, orig_h  # No resize needed

        # Calculate new dimensions
        ratio = max_width / orig_w
        new_h = int(orig_h * ratio)

        # Resize with high-quality downsampling
        img = img.resize((max_width, new_h), Image.LANCZOS)

        # Re-encode
        buf = io.BytesIO()
        save_format = 'PNG' if img_format.lower() == 'png' else 'JPEG'
        if save_format == 'JPEG' and img.mode == 'RGBA':
            img = img.convert('RGB')
        img.save(buf, format=save_format, quality=85, optimize=True)
        new_b64 = base64.b64encode(buf.getvalue()).decode('ascii')

        return new_b64, orig_w, orig_h

    except Exception as e:
        print(f"  ⚠️ Failed to process image: {e}")
        return None, 0, 0


def process_file(filepath):
    print(f"📖 Reading: {os.path.basename(filepath)}")
    with open(filepath, 'r') as f:
        content = f.read()

    original_size = len(content.encode('utf-8'))
    print(f"   Original size: {original_size / 1024 / 1024:.1f} MB")

    # Find all images
    matches = list(IMG_PATTERN.finditer(content))
    print(f"   Found {len(matches)} base64 images\n")

    resized = 0
    skipped = 0
    errors = 0

    for i, match in enumerate(matches, 1):
        alt_text = match.group(1)
        data_prefix = match.group(2)  # data:image/png;base64,
        img_format = match.group(3)   # png, jpeg, etc.
        b64_data = match.group(4).replace('\n', '').replace('\r', '').replace(' ', '')

        new_b64, orig_w, orig_h = resize_image(b64_data, img_format)

        if new_b64 is None and orig_w > 0:
            skipped += 1
            if i <= 20 or i % 50 == 0:
                print(f"  [{i}/{len(matches)}] ✓ Already fits ({orig_w}x{orig_h})")
        elif new_b64:
            new_w = MAX_WIDTH
            ratio = MAX_WIDTH / orig_w
            new_h = int(orig_h * ratio)
            old_len = len(b64_data)
            new_len = len(new_b64)
            reduction = (1 - new_len / old_len) * 100

            # Replace in content
            old_full = match.group(0)
            new_full = f"![{alt_text}]({data_prefix}{new_b64})"
            content = content.replace(old_full, new_full, 1)

            resized += 1
            if i <= 20 or i % 50 == 0:
                print(f"  [{i}/{len(matches)}] 🔧 Resized {orig_w}x{orig_h} → {new_w}x{new_h} (-{reduction:.0f}%)")
        else:
            errors += 1

        # Progress every 100
        if i % 100 == 0:
            print(f"  ... processed {i}/{len(matches)}")

    # Write back
    print(f"\n📝 Writing resized file...")
    with open(filepath, 'w') as f:
        f.write(content)

    new_size = len(content.encode('utf-8'))
    reduction = (1 - new_size / original_size) * 100

    print(f"\n{'='*50}")
    print(f"📊 Results:")
    print(f"   Images resized:  {resized}")
    print(f"   Already fit:     {skipped}")
    print(f"   Errors:          {errors}")
    print(f"   Original size:   {original_size / 1024 / 1024:.1f} MB")
    print(f"   New size:        {new_size / 1024 / 1024:.1f} MB")
    print(f"   Size reduction:  {reduction:.1f}%")


if __name__ == "__main__":
    if not os.path.exists(KB_FILE):
        print(f"❌ File not found: {KB_FILE}")
        sys.exit(1)
    process_file(KB_FILE)
