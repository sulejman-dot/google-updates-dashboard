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
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
if not SLACK_BOT_TOKEN:
    raise RuntimeError("SLACK_BOT_TOKEN not set in environment — refusing to start")
TECHNICAL_QUESTIONS_CHANNEL = "CDZMHAPLK"
DAYS_LOOKBACK = 30

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "guru_cards")
PENDING_DIR = os.path.join(SCRIPT_DIR, "guru_cards", "pending_review")  # staging area
TRACKER_FILE = os.path.join(SCRIPT_DIR, "guru_cards_tracker.json")

# Slack channel to post review notifications (bot lacks im:write for DMs)
REVIEW_NOTIFY_CHANNEL = "C0AESD9DTC5"  # #test-channel

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
MIN_ANSWER_LENGTH = 100

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
    r'^(<@U[A-Z0-9]+>\s*).*(what|was|wondering|can you)',   # Delegating question to someone
    r'^(sorry to drag|sorry to bother)',                    # Apologetic delegation
    r'^also,?\s*maybe\s*<@',                               # "also maybe @someone"
    r'^hey\s*<@.*would you be able to',                    # Asking someone else for help
    r'^hey\s*<@.*can you',                                 # Asking someone else for help
    r'^I\'?ll provide.*answers',                            # Promise to answer later
]
NOT_AN_ANSWER_RE = re.compile('|'.join(NOT_AN_ANSWER_PATTERNS), re.IGNORECASE)

# ── Hedging / uncertainty patterns (disqualify the answer) ─────────────────
HEDGING_PATTERNS = [
    r"i don'?t have confirmation",
    r"i'?m not sure",
    r"not sure about",
    r"not certain",
    r"i don'?t know",
    r"need to (check|confirm|verify|ask|investigate)",
    r"i think maybe",
    r"i believe but",
    r"might not",
    r"haven'?t confirmed",
    r"can'?t confirm",
    r"still checking",
    r"waiting for.*confirmation",
    r"don'?t quote me",
    r"take this with a grain of salt",
]
HEDGING_RE = re.compile('|'.join(HEDGING_PATTERNS), re.IGNORECASE)

# Thread-ignore patterns
IGNORE_THREAD_RE = re.compile(r'~?ignore this thread~?|disregard this', re.IGNORECASE)


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
    stripped = text.strip()
    if NOT_AN_ANSWER_RE.match(stripped):
        return False
    # If it's mostly questions (3+ question marks), it's not an answer
    if stripped.count('?') >= 3 and len(stripped) < 500:
        return False
    return True


def has_hedging(text):
    """Check if an answer contains hedging/uncertainty language that disqualifies it."""
    if not text:
        return False
    return bool(HEDGING_RE.search(text))


def is_thread_ignored(replies):
    """Check if a thread has been explicitly marked to ignore."""
    for reply in replies:
        if IGNORE_THREAD_RE.search(reply.get('text', '')):
            return True
    return False


def classify_thread(replies):
    """
    Classify a thread based on its replies:
      'has_card'       — A real Guru card link was posted
      'no_card_needed' — The "no card needed" link was posted
      'ignored'        — Thread explicitly marked to ignore
      'needs_card'     — Has a definitive answer but no Guru card yet
      'needs_followup' — Has answers but they contain hedging/uncertainty
      'no_answer'      — No substantive answer yet
    """
    # Check for ignored threads first
    if is_thread_ignored(replies):
        return 'ignored'

    has_guru_link = False
    is_no_card_needed = False
    has_real_answer = False
    all_answers_hedge = True  # Track if ALL answers hedge

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
            if not has_hedging(text):
                all_answers_hedge = False

    if has_guru_link:
        return 'has_card'
    if is_no_card_needed:
        return 'no_card_needed'
    if has_real_answer and all_answers_hedge:
        return 'needs_followup'
    if has_real_answer:
        return 'needs_card'
    return 'no_answer'


def extract_real_answers(replies):
    """Extract only substantive, non-bot, non-hedging answers from a thread."""
    answers = []
    for reply in replies[1:]:
        if is_bot_message(reply):
            continue
        text = reply.get('text', '')
        if not is_substantive_answer(text):
            continue
        # Skip answers that contain hedging/uncertainty
        if has_hedging(text):
            continue

        user_id = reply.get('user', 'Unknown')
        date = datetime.fromtimestamp(float(reply['ts']))
        clean_text = clean_slack_text(text)
        answers.append((user_id, date, clean_text))
    return answers


def generate_title(text):
    """
    Generate a clean TOPIC title from question text.
    Titles should be topic-based (e.g., 'ChatGPT tracking') not question-based.
    """
    first_line = text.split('\n')[0].strip()
    title = re.sub(r'[*_`]', '', first_line)
    # Strip greetings
    title = re.sub(r'^(hey\s*(team|everyone|guys|all|there)?[!,.\s]*)', '', title, flags=re.IGNORECASE).strip()
    title = re.sub(r'^(hi\s*(team|everyone|guys|all|there)?[!,.\s]*)', '', title, flags=re.IGNORECASE).strip()
    title = re.sub(r'^(i have (the following |a )?question[:\s]*)', '', title, flags=re.IGNORECASE).strip()
    title = re.sub(r'^(quick question[:\s]*)', '', title, flags=re.IGNORECASE).strip()
    # Convert question form to topic form
    title = re.sub(r'^(do we|does|can we|is there|are there|what is|what are|how do we|how does)\s+', '', title, flags=re.IGNORECASE).strip()
    # Remove trailing question marks
    title = title.rstrip('?').strip()
    # If too short, try next lines
    if len(title) < 15:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines:
            clean = re.sub(r'[*_`]', '', line)
            clean = re.sub(r'^(hey\s*(team|everyone|all)?[!,.\s]*)', '', clean, flags=re.IGNORECASE).strip()
            if len(clean) >= 15:
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


def notify_slack_review(title, filename, permalink, card_content, filepath):
    """
    Send a Slack notification with:
    - Prominent thread link
    - Interactive Approve/Reject/Follow-up buttons
    - Uploaded .md file as a snippet for inline viewing/editing
    """
    try:
        # ── 1. Post Block Kit message with interactive buttons ──
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📋 New KB Card Ready for Review"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Title:*\n{title}"},
                    {"type": "mrkdwn", "text": f"*File:*\n`{filename}`"}
                ]
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"🔗 *<{permalink}|View original Slack thread>*" if permalink else "_Thread link not available_"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "✏️ _Open the attached file in Google Docs to review/edit, then click Approve below._"}
            },
            {"type": "divider"},
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve"},
                        "style": "primary",
                        "action_id": "kb_approve",
                        "value": filename
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject"},
                        "style": "danger",
                        "action_id": "kb_reject",
                        "value": filename
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "⚠️ Follow-up"},
                        "action_id": "kb_followup",
                        "value": filename
                    }
                ]
            }
        ]

        slack_client.chat_postMessage(
            channel=REVIEW_NOTIFY_CHANNEL,
            text=f"📋 New KB Card for Review: {title}",  # fallback
            blocks=blocks
        )

        # ── 2. Upload the .md file as a snippet for inline viewing/editing ──
        try:
            slack_client.files_upload_v2(
                channel=REVIEW_NOTIFY_CHANNEL,
                file=filepath,
                filename=filename,
                title=f"📄 {title} — Review & Edit",
                initial_comment="⬇️ *Open with Google Docs to review/edit before approving:*",
            )
            print(f"   📬 Slack notification + file uploaded for review: {filename}")
        except Exception as upload_err:
            preview = card_content[:2500] if len(card_content) > 2500 else card_content
            if len(card_content) > 2500:
                preview += "\n\n_...content truncated..._"
            slack_client.chat_postMessage(
                channel=REVIEW_NOTIFY_CHANNEL,
                text=f"📄 *Card content (file upload failed):*\n```\n{preview}\n```"
            )
            print(f"   ⚠️ File upload failed ({upload_err}), posted content inline")

    except Exception as e:
        print(f"   ⚠️ Could not send Slack notification: {e}")


def notify_slack_followup(thread_preview, permalink):
    """
    Notify that a thread needs a proper answer before it can become a KB card.
    """
    try:
        msg = (
            f"⚠️ *Thread Needs Follow-Up*\n\n"
            f"A question in #technical-questions has answers that contain "
            f"uncertainty/hedging language and can't be turned into a KB card yet.\n\n"
            f"*Thread:* {thread_preview[:100]}...\n"
            f"*Link:* {permalink or '_not available_'}\n\n"
            f"Please provide a definitive answer in the thread so it can be "
            f"reviewed as a KB card."
        )
        slack_client.chat_postMessage(channel=REVIEW_NOTIFY_CHANNEL, text=msg)
        print(f"   📬 Follow-up notification sent for thread")
    except Exception as e:
        print(f"   ⚠️ Could not send follow-up notification: {e}")


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
    Pick the best answer from the thread.
    Strategy: prefer the longest, most definitive answer (usually the final resolution).
    If there are multiple substantial answers, use the longest one.
    Only add additional context from other replies if they are also substantial.
    """
    if len(real_answers) == 1:
        _, _, text = real_answers[0]
        return text.strip()

    # Find the longest/most substantive answer
    sorted_answers = sorted(real_answers, key=lambda a: len(a[2]), reverse=True)
    best = sorted_answers[0][2].strip()

    # Only add additional context if it's substantially different, substantial,
    # and itself is an answer (not more questions)
    additional = []
    for _, _, text in sorted_answers[1:]:
        cleaned = text.strip()
        # Must be long, not a subset of best, and not mostly questions
        if len(cleaned) >= 300 and cleaned[:50] not in best and cleaned.count('?') < 3:
            additional.append(cleaned)

    if additional:
        parts = [best]
        for add_text in additional[:2]:  # Max 2 additional context blocks
            parts.append(f"\n\n**Additional context:**\n\n{add_text}")
        return "\n".join(parts)

    return best


def auto_generate_tags(question_text, answer_text):
    """Generate relevant tags from the question and answer content."""
    combined = (question_text + ' ' + answer_text).lower()
    # Common product/feature keywords to check
    tag_keywords = [
        'chatgpt', 'ais', 'ai search', 'rank tracker', 'content writer',
        'forecast', 'traffic', 'api', 'gsc', 'google search console',
        'keywords', 'billing', 'pricing', 'campaigns', 'visibility',
        'search volume', 'serp', 'organic', 'carbon', 'emissions',
        'writer-only', 'pro', 'onboarding', 'churn', 'integration',
        'localization', 'tracking', 'scraping', 'data', 'export',
    ]
    tags = []
    for kw in tag_keywords:
        if kw in combined:
            tags.append(kw)
    return ', '.join(tags[:5]) if tags else 'technical'


def format_guru_card(parent_msg, real_answers):
    """
    Generate Guru card content matching the existing KB format:
    - Topic-based title (not a question)
    - Metadata header (Collection, Last Modified, Tags)
    - Factual, declarative content (not Q&A format)
    """
    raw_question = clean_slack_text(parent_msg.get('text', ''))
    question_text = summarize_question(raw_question)
    question_date = datetime.fromtimestamp(float(parent_msg['ts']))
    today = datetime.now().strftime('%Y-%m-%d')
    title = generate_title(question_text)
    permalink = slack_permalink(TECHNICAL_QUESTIONS_CHANNEL, parent_msg['ts'])
    answer_text = summarize_answer(real_answers)
    tags = auto_generate_tags(question_text, answer_text)

    # KB-matching format: metadata header + factual content
    card = f"""# {title}

> **Collection:** Customer Success
> **Last Modified:** {today}
> **Tags:** {tags}

---

{answer_text}

---

*Source: #technical-questions — {question_date.strftime('%B %d, %Y')}*
"""
    if permalink:
        card += f"*Slack thread: {permalink}*\n"

    return title, card


def run(days_lookback=DAYS_LOOKBACK, process_all=False):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PENDING_DIR, exist_ok=True)
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

    stats = {'has_card': 0, 'no_card_needed': 0, 'needs_card': 0, 'no_answer': 0, 'ignored': 0, 'needs_followup': 0}
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

        elif classification == 'ignored':
            print(f"  [{i}] 🚫 Ignored thread: \"{preview}...\"")
            db.upsert_slack_thread(
                thread_ts=ts, channel=TECHNICAL_QUESTIONS_CHANNEL,
                classification='ignored', question_preview=preview,
                has_answer=0, has_guru_card=0
            )

        elif classification == 'needs_card':
            real_answers = extract_real_answers(replies)
            if not real_answers:
                # All answers were hedging — reclassify
                print(f"  [{i}] ⚠️  All answers hedge: \"{preview}...\"")
                permalink = slack_permalink(TECHNICAL_QUESTIONS_CHANNEL, ts)
                notify_slack_followup(preview, permalink)
                continue

            question_text = clean_slack_text(thread.get('text', ''))
            title, card_content = format_guru_card(thread, real_answers)
            answer_text = '\n\n'.join(a[2] for a in real_answers)
            permalink = slack_permalink(TECHNICAL_QUESTIONS_CHANNEL, ts)

            # Save to pending_review/ folder (staging area — not yet in KB)
            date_prefix = datetime.fromtimestamp(float(ts)).strftime('%Y%m%d')
            filename = f"{date_prefix}_{sanitize_filename(title)}.md"
            filepath = os.path.join(PENDING_DIR, filename)
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

            print(f"  [{i}] 📝 NEEDS CARD → Staged for review: {filename}")

            # Notify reviewer via Slack with full card preview
            notify_slack_review(title, filename, permalink, card_content, filepath)
            cards_created += 1

        elif classification == 'needs_followup':
            print(f"  [{i}] ⚠️  Needs follow-up (hedging detected): \"{preview}...\"")
            permalink = slack_permalink(TECHNICAL_QUESTIONS_CHANNEL, ts)
            notify_slack_followup(preview, permalink)
            db.upsert_slack_thread(
                thread_ts=ts, channel=TECHNICAL_QUESTIONS_CHANNEL,
                classification='needs_followup', question_preview=preview,
                has_answer=1, has_guru_card=0
            )
            # Don't add to processed — re-check next run

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
    print(f"   🚫 Ignored threads:                   {stats['ignored']}")
    print(f"   ⚠️  Needs follow-up:                   {stats['needs_followup']}")
    print(f"   ⏭️  No answer yet:                     {stats['no_answer']}")
    print(f"\n   📂 Pending: {PENDING_DIR}")
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
