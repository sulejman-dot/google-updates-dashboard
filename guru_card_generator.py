#!/usr/bin/env python3
"""
Guru Card Content Generator
============================
Scans #technical-questions in Slack to find threads that:
  1. Have a real, substantive answer
  2. Do NOT yet have a Guru card created (no guru link posted)

For those threads, it generates Guru-ready Q&A content as markdown files.

Threads are classified as:
  ✅ GURU CARD EXISTS  — a real Guru card link was posted (skipped)
  🚫 NO CARD NEEDED   — marked with the "no card needed" Guru link (skipped)
  📝 NEEDS GURU CARD  — has answer but no card yet → content generated
  ⏭️  NO ANSWER YET    — no substantive answer yet (skipped, checked again next run)

Usage:
    python3 guru_card_generator.py              # Process new threads (last 30 days)
    python3 guru_card_generator.py --days 90    # Look back 90 days
    python3 guru_card_generator.py --all        # Reprocess all threads (ignore tracking)
"""

import os
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from slack_sdk import WebClient
from dotenv import load_dotenv
from guru_db import GuruDB

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN") or "xoxb-4173116321-10452138701364-22v7lSrQNCFqFe6lX8g0aCXM"
TECHNICAL_QUESTIONS_CHANNEL = "CDZMHAPLK"
DAYS_LOOKBACK = 30

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "guru_cards")
TRACKER_FILE = os.path.join(SCRIPT_DIR, "guru_cards_tracker.json")

slack_client = WebClient(token=SLACK_BOT_TOKEN)

# ── Guru link patterns ─────────────────────────────────────────────────────
# Real Guru card link (any card except the "no card needed" one)
GURU_CARD_LINK_RE = re.compile(r'https?://app\.getguru\.com/card/\w+')
# The specific "no card needed" link
NO_CARD_NEEDED_RE = re.compile(r'Internal-request-details-to-Guru-card-not-needed|i6E86MET')

# Bot noise patterns
BOT_NOISE_PATTERNS = [
    r"did you forget to add the guru card",
    r"the answer was provided \d+ hours? ago",
    r"keep spreading the knowledge",
    r"thanks.*:nerd_face:",
]
BOT_NOISE_RE = re.compile('|'.join(BOT_NOISE_PATTERNS), re.IGNORECASE)

# Minimum length for a substantive answer
MIN_ANSWER_LENGTH = 50

# Non-answer patterns (just @mentions, short acks, link-only, etc.)
NOT_AN_ANSWER_PATTERNS = [
    r'^(<@U[A-Z0-9]+>\s*)+$',                              # Just @mentions
    r'^(<@U[A-Z0-9]+>\s*)+(can you|can one of you|please|maybe|help|could you)',  # Tagging for help
    r'^(<@U[A-Z0-9]+>\s*)+(bring it|check this|see above)',  # Delegation, not answers
    r'^(on it|confirm|confirmed|yes|no|ok|okay|thanks|thank you|ty|thx|noted|got it|will do)\.?\s*$',
    r'^cc:?\s*<@',                                          # cc-ing someone
    r'^\s*<https://app\.getguru\.com/',                     # Just a Guru link
    r'^\s*<https://app\.clickup\.com/',                     # Just a ClickUp link
    r'^(<@U[A-Z0-9]+>\s*)+\??\s*$',                        # @mentions with optional ?
]
NOT_AN_ANSWER_RE = re.compile('|'.join(NOT_AN_ANSWER_PATTERNS), re.IGNORECASE)


# ── Helpers ─────────────────────────────────────────────────────────────────

def clean_slack_text(text):
    """Clean Slack formatting for readable markdown."""
    if not text:
        return ""

    # Clean links: <https://example.com|label> → [label](url)
    def replace_link(match):
        url = match.group(1)
        label = match.group(2) if match.group(2) else url
        return f"[{label}]({url})"
    text = re.sub(r'<(https?://[^|>]+)\|?([^>]*)>', replace_link, text)

    # Clean channel refs: <#C12345|channel-name> → #channel-name
    text = re.sub(r'<#[A-Z0-9]+\|([^>]+)>', r'#\1', text)

    # Clean user mentions: <@U12345> → @U12345 (keep ID since we can't resolve)
    text = re.sub(r'<@(U[A-Z0-9]+)>', r'@\1', text)

    return text.strip()


def is_bot_message(msg):
    """Check if a message is from a bot."""
    return msg.get('subtype') == 'bot_message' or not msg.get('user')


def is_substantive_answer(text):
    """Check if text qualifies as a real answer (not just acks/mentions/links)."""
    if not text or len(text.strip()) < MIN_ANSWER_LENGTH:
        return False
    if NOT_AN_ANSWER_RE.match(text.strip()):
        return False
    return True


def classify_thread(replies):
    """
    Classify a thread based on its replies:
      'has_card'    — A real Guru card link was posted
      'no_card_needed' — The "no card needed" link was posted
      'needs_card'  — Has a real answer but no Guru card yet
      'no_answer'   — No substantive answer yet
    """
    has_guru_link = False
    is_no_card_needed = False
    has_real_answer = False

    for reply in replies[1:]:  # Skip parent message
        text = reply.get('text', '')

        # Check for Guru card links
        if GURU_CARD_LINK_RE.search(text):
            if NO_CARD_NEEDED_RE.search(text):
                is_no_card_needed = True
            else:
                has_guru_link = True

        # Check for substantive answers (skip bot messages)
        if not is_bot_message(reply) and is_substantive_answer(text):
            has_real_answer = True

    if has_guru_link:
        return 'has_card'
    if is_no_card_needed:
        return 'no_card_needed'
    if has_real_answer:
        return 'needs_card'
    return 'no_answer'


def extract_real_answers(replies):
    """Extract only substantive, non-bot answers from a thread."""
    answers = []
    for reply in replies[1:]:
        if is_bot_message(reply):
            continue
        text = reply.get('text', '')
        if not is_substantive_answer(text):
            continue

        user_id = reply.get('user', 'Unknown')
        date = datetime.fromtimestamp(float(reply['ts']))
        clean_text = clean_slack_text(text)
        answers.append((user_id, date, clean_text))
    return answers


def generate_title(text):
    """Generate a clean title from question text."""
    first_line = text.split('\n')[0].strip()
    title = re.sub(r'[*_`]', '', first_line)
    # Strip greetings
    title = re.sub(r'^(hey\s*(team|everyone|all)?[!,.\s]*)', '', title, flags=re.IGNORECASE).strip()
    title = re.sub(r'^(i have the following question[:\s]*)', '', title, flags=re.IGNORECASE).strip()
    # If too short, try next lines
    if len(title) < 20:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines:
            clean = re.sub(r'[*_`]', '', line)
            clean = re.sub(r'^(hey\s*(team|everyone|all)?[!,.\s]*)', '', clean, flags=re.IGNORECASE).strip()
            if len(clean) >= 20:
                title = clean
                break
    if len(title) > 120:
        title = title[:117] + "..."
    if title:
        title = title[0].upper() + title[1:]
    return title


def slack_permalink(channel_id, thread_ts):
    """Get Slack permalink for a thread."""
    try:
        result = slack_client.chat_getPermalink(channel=channel_id, message_ts=thread_ts)
        return result.get("permalink", "")
    except Exception:
        return ""


def load_tracker():
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r') as f:
            return json.load(f)
    return {"processed_threads": [], "last_updated": None}


def save_tracker(data):
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(TRACKER_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def sanitize_filename(title):
    safe = re.sub(r'[^\w\s-]', '', title.lower())
    safe = re.sub(r'[\s]+', '_', safe.strip())
    return safe[:80]


# ── Core ────────────────────────────────────────────────────────────────────

def fetch_threads(days_lookback=DAYS_LOOKBACK):
    """Fetch all threaded messages from #technical-questions."""
    oldest = int((datetime.now(timezone.utc) - timedelta(days=days_lookback)).timestamp())
    print(f"📡 Fetching from #technical-questions (last {days_lookback} days)...")

    all_msgs = []
    cursor = None
    while True:
        kwargs = {'channel': TECHNICAL_QUESTIONS_CHANNEL, 'oldest': str(oldest), 'limit': 200}
        if cursor:
            kwargs['cursor'] = cursor
        try:
            result = slack_client.conversations_history(**kwargs)
        except Exception as e:
            if 'not_in_channel' in str(e):
                print("\n❌ Bot not in #technical-questions! Add it with /invite @BotName")
                sys.exit(1)
            raise
        all_msgs.extend(result.get('messages', []))
        cursor = result.get('response_metadata', {}).get('next_cursor', '')
        if not cursor:
            break

    threads = [m for m in all_msgs if m.get('reply_count', 0) > 0]
    print(f"   Found {len(all_msgs)} messages, {len(threads)} with threads")
    return threads


def fetch_replies(thread_ts):
    try:
        result = slack_client.conversations_replies(
            channel=TECHNICAL_QUESTIONS_CHANNEL, ts=thread_ts, limit=200
        )
        return result.get('messages', [])
    except Exception as e:
        print(f"   ⚠️ Failed to fetch replies for {thread_ts}: {e}")
        return []


def summarize_question(text):
    """Clean up a question: strip greetings, preamble, and noise."""
    # Remove common greetings and preamble
    preamble = re.compile(
        r'^(hey\s*(team|everyone|guys|all|there)[!,.]?\s*|'
        r'hi\s*(team|everyone|guys|all|there)[!,.]?\s*|'
        r'hello\s*(team|everyone|guys|all|there)[!,.]?\s*|'
        r'good\s*(morning|afternoon|evening)[!,.]?\s*|'
        r'I\s+have\s+a\s+question[:\s]*|'
        r'quick\s+question[:\s]*|'
        r'just\s+wanted\s+to\s+(ask|check|know|confirm)[:\s]*)',
        re.IGNORECASE
    )
    text = preamble.sub('', text).strip()
    # Capitalize first letter
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def summarize_answer(real_answers):
    """
    Consolidate multiple thread replies into a single clean answer.
    If there's one answer, return it clean.
    If multiple, combine them with clear attribution.
    """
    if len(real_answers) == 1:
        _, _, text = real_answers[0]
        return text.strip()

    # Multiple answers — combine into one coherent response
    parts = []
    for i, (uid, date, text) in enumerate(real_answers):
        cleaned = text.strip()
        if i == 0:
            parts.append(cleaned)
        else:
            # Add separator for additional context
            parts.append(f"\n\n**Additional context:**\n\n{cleaned}")
    return "\n".join(parts)


def format_guru_card(parent_msg, real_answers):
    """Generate Guru card content from a Q&A thread — clean, summarized."""
    raw_question = clean_slack_text(parent_msg.get('text', ''))
    question_text = summarize_question(raw_question)
    question_date = datetime.fromtimestamp(float(parent_msg['ts']))
    title = generate_title(question_text)
    permalink = slack_permalink(TECHNICAL_QUESTIONS_CHANNEL, parent_msg['ts'])
    answer_text = summarize_answer(real_answers)

    # Markdown card
    card = f"""# {title}

## Question

{question_text}

---

## Answer

{answer_text}

---

*Source: #technical-questions — {question_date.strftime('%B %d, %Y')}*
"""
    if permalink:
        card += f"*Slack thread: {permalink}*\n"

    return title, card


def run(days_lookback=DAYS_LOOKBACK, process_all=False):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    db = GuruDB()

    # Use DB for tracking instead of JSON file
    if process_all:
        processed_set = set()
        print("🔄 Processing ALL threads (ignoring tracker)")
    else:
        processed_set = db.get_processed_threads()
        # Also merge in legacy JSON tracker if present
        legacy = load_tracker()
        processed_set |= set(legacy.get("processed_threads", []))
        print(f"📋 Tracker: {len(processed_set)} previously processed threads")

    threads = fetch_threads(days_lookback)
    new_threads = [t for t in threads if t['ts'] not in processed_set]

    if not new_threads:
        print("✅ No new threads to process!")
        db.close()
        return

    print(f"\n🔍 Analyzing {len(new_threads)} threads...\n")

    stats = {'has_card': 0, 'no_card_needed': 0, 'needs_card': 0, 'no_answer': 0}
    cards_created = 0

    for i, thread in enumerate(new_threads, 1):
        ts = thread['ts']
        preview = thread.get('text', '')[:60].replace('\n', ' ')
        replies = fetch_replies(ts)
        if not replies:
            continue

        classification = classify_thread(replies)
        stats[classification] += 1

        # Find guru card URL if one exists in the thread
        guru_url = ''
        for r in replies:
            match = GURU_CARD_LINK_RE.search(r.get('text', ''))
            if match and not NO_CARD_NEEDED_RE.search(r.get('text', '')):
                guru_url = match.group(0)

        if classification == 'has_card':
            print(f"  [{i}] ✅ Already has Guru card: \"{preview}...\"")
            db.upsert_slack_thread(
                thread_ts=ts, channel=TECHNICAL_QUESTIONS_CHANNEL,
                classification='has_card', question_preview=preview,
                has_answer=1, has_guru_card=1, guru_card_url=guru_url
            )

        elif classification == 'no_card_needed':
            print(f"  [{i}] 🚫 No card needed: \"{preview}...\"")
            db.upsert_slack_thread(
                thread_ts=ts, channel=TECHNICAL_QUESTIONS_CHANNEL,
                classification='no_card_needed', question_preview=preview,
                has_answer=1, has_guru_card=0
            )

        elif classification == 'needs_card':
            real_answers = extract_real_answers(replies)
            question_text = clean_slack_text(thread.get('text', ''))
            title, card_content = format_guru_card(thread, real_answers)
            answer_text = '\n\n'.join(a[2] for a in real_answers)
            permalink = slack_permalink(TECHNICAL_QUESTIONS_CHANNEL, ts)

            # Save markdown file
            date_prefix = datetime.fromtimestamp(float(ts)).strftime('%Y%m%d')
            filename = f"{date_prefix}_{sanitize_filename(title)}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, 'w') as f:
                f.write(card_content)

            # Save to database
            db.insert_pending_card(
                title=title, question=question_text, answer=answer_text,
                content_md=card_content, slack_thread_ts=ts,
                slack_channel=TECHNICAL_QUESTIONS_CHANNEL,
                slack_permalink=permalink, classification='needs_card'
            )
            db.upsert_slack_thread(
                thread_ts=ts, channel=TECHNICAL_QUESTIONS_CHANNEL,
                classification='needs_card', question_preview=preview,
                has_answer=1, has_guru_card=0
            )

            print(f"  [{i}] 📝 NEEDS CARD → Created: {filename}")
            cards_created += 1

        elif classification == 'no_answer':
            print(f"  [{i}] ⏭️  No answer yet: \"{preview}...\"")
            # Don't track — check again next run

    # Also save to legacy JSON tracker for backward compat
    all_processed = db.get_processed_threads()
    save_tracker({"processed_threads": list(all_processed)})

    # Show stats
    db_stats = db.get_stats()
    db.close()

    print(f"\n{'='*60}")
    print(f"📊 Summary:")
    print(f"   📝 Needs Guru card (content created): {stats['needs_card']}")
    print(f"   ✅ Already has Guru card:             {stats['has_card']}")
    print(f"   🚫 No card needed:                    {stats['no_card_needed']}")
    print(f"   ⏭️  No answer yet:                     {stats['no_answer']}")
    print(f"\n   📂 Markdown: {OUTPUT_DIR}")
    print(f"   🗄️  Database: {db_stats['guru_cards']} guru cards, {db_stats['pending_cards']} pending")


if __name__ == "__main__":
    days = DAYS_LOOKBACK
    process_all = False

    if "--all" in sys.argv:
        process_all = True
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            days = int(sys.argv[idx + 1])

    run(days_lookback=days, process_all=process_all)
