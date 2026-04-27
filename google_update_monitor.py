import os
import sys
import json
import time
import uuid
import tempfile
import requests as req
import feedparser
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
# We use the Slack Webhook to post messages
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
# If you want to create ClickUp tasks, add your CLICKUP_LIST_ID to your .env file
CLICKUP_LIST_ID = os.getenv("CLICKUP_LIST_ID") 
CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY")

GOOGLE_STATUS_URL = "https://status.search.google.com/incidents.json"
SER_RSS_URL = "https://www.seroundtable.com/index.xml"
SEJ_RSS_URL = "https://www.searchenginejournal.com/feed/"
SEL_RSS_URL = "https://searchengineland.com/feed"
GOOGLE_BLOG_RSS_URL = "https://blog.google/products/search/rss/"

# Competitor Blog RSS Feeds
# Only include feeds that are verified live and publish product/AI content
COMPETITOR_FEEDS = {
    "SEMrush": "https://www.semrush.com/blog/feed/",
    "Ahrefs": "https://ahrefs.com/blog/feed/",
    "SE Ranking": "https://seranking.com/blog/feed/",
    "Sistrix": "https://www.sistrix.com/feed/",
    "Moz": "https://moz.com/blog/feed",
    "Rank Ranger": "https://www.rankranger.com/feed",
    # Botify, Authoritas, Nightwatch do not expose public RSS feeds
}

# Full competitor list for Reddit/HN community searches
# Includes competitors pushing AI Search / AI Overview tracking
COMPETITOR_NAMES = [
    "semrush", "ahrefs", "se ranking", "seranking", "accuranker",
    "sistrix", "brightedge", "conductor seo", "moz pro",
    "advanced web ranking", "surfer seo", "surferseo",
    # AI Search / AIO tracking focused competitors
    "rank ranger", "rankranger", "nightwatch", "botify",
    "authoritas", "searchmetrics"
]

# AI/LLM keywords for special flagging
AI_LLM_KEYWORDS = [
    'ai ', 'llm', 'ai-', 'artificial intelligence', 'machine learning',
    'gpt', 'large language model', 'generative ai', 'ai overview',
    'aio', 'ai search', 'ai tracking', 'ai content', 'ai writing',
    'chatgpt', 'gemini', 'claude', 'perplexity', 'searchgpt',
    'ai visibility', 'llm monitoring', 'ai optimization',
    'ai-powered', 'genai', 'copilot', 'ai agent'
]

STATE_FILE = "google_updates_state.json"
DASHBOARD_FILE = "dashboard/dashboard_data.json"
VOLATILITY_FILE = "dashboard/volatility_data.json"
dashboard_alerts = []

def fetch_serp_volatility():
    """Fetch SERP volatility data from MozCast and store 30-day history."""
    print(f"[{datetime.now().isoformat()}] Fetching SERP volatility from MozCast...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        resp = req.get('https://mozcast.com/', headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        # Extract the embedded Vue data JSON array
        weather_match = re.search(r'weather:\s*(\[.*?\])\s*,\s*\n', html, re.S)
        if not weather_match:
            # Fallback: just grab today's temperature from the display
            temp_match = re.search(r'display-1[^>]*>(\d+\.?\d*)°', html)
            if temp_match:
                today_temp = float(temp_match.group(1))
                print(f"  📊 MozCast today: {today_temp}°")
                # Store minimal record
                record = {'date': datetime.now().strftime('%Y-%m-%d'), 'temp': today_temp, 'source': 'mozcast'}
                existing = []
                if os.path.exists(VOLATILITY_FILE):
                    with open(VOLATILITY_FILE) as f:
                        existing = json.load(f)
                # Upsert today
                existing = [e for e in existing if e.get('date') != record['date']]
                existing.insert(0, record)
                existing = existing[:60]  # keep 60 days
                with open(VOLATILITY_FILE, 'w') as f:
                    json.dump(existing, f, indent=2)
                return today_temp
            return None

        weather_data = json.loads(weather_match.group(1))
        print(f"  📊 MozCast: {len(weather_data)} days of data fetched")

        # Normalize to clean records
        records = []
        for entry in weather_data:
            try:
                records.append({
                    'date': entry['date'][:10],          # YYYY-MM-DD
                    'dateStr': entry.get('dateStr', ''), # "Apr 9"
                    'temp': float(entry.get('temp', 70)),
                    'source': 'mozcast'
                })
            except (KeyError, ValueError):
                continue

        if not records:
            print("  ⚠️ MozCast: no records parsed")
            return None

        today_temp = records[0]['temp'] if records else None
        level = 'HIGH' if today_temp and today_temp > 90 else ('MEDIUM' if today_temp and today_temp > 75 else 'LOW')
        print(f"  📊 MozCast today: {today_temp}° ({level})")

        with open(VOLATILITY_FILE, 'w') as f:
            json.dump(records[:60], f, indent=2)

        # Send Slack alert if volatility is very high (>110°) and this is new
        if today_temp and today_temp > 110 and SLACK_WEBHOOK_URL:
            today_str = records[0]['date']
            # Check if we already alerted today
            state_path = STATE_FILE
            try:
                with open(state_path) as sf:
                    state = json.load(sf)
                alerted_dates = state.get('volatility_alerted', [])
                if today_str not in alerted_dates:
                    volatility_payload = {
                        'text': f'🌡️ *High SERP Volatility Detected!* MozCast is at *{today_temp}°* today (baseline ~70°). Google rankings may be fluctuating significantly.',
                        'attachments': [{
                            'color': '#FF4500',
                            'title': f'MozCast Temperature: {today_temp}°',
                            'title_link': 'https://mozcast.com/',
                            'fields': [
                                {'title': 'Status', 'value': level, 'short': True},
                                {'title': 'Baseline', 'value': '~70° = normal', 'short': True},
                            ],
                            'footer': 'MozCast SERP Volatility Tracker'
                        }]
                    }
                    try:
                        req.post(SLACK_WEBHOOK_URL, json=volatility_payload, timeout=10)
                        print(f"  ✅ High volatility Slack alert sent: {today_temp}°")
                        alerted_dates.append(today_str)
                        state['volatility_alerted'] = alerted_dates[-30:]  # keep 30 days
                        with open(state_path, 'w') as sf:
                            json.dump(state, sf, indent=4)
                    except Exception as e:
                        print(f"  ⚠️ Volatility Slack alert failed: {e}")
            except Exception:
                pass

        return today_temp

    except Exception as e:
        print(f"❌ Failed to fetch MozCast volatility: {e}")
        return None

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ State file corrupted. Starting fresh.")
    
    # Support migration of older state files
    state = {
        "seen_updates": {}, "seen_articles": [], "seen_ugc": [], 
        "seen_brand_mentions": [], "seen_hn_brand_mentions": [], "seen_hn_ugc": [],
        "seen_sej_articles": [], "seen_sel_articles": [], "seen_google_blog": [],
        "seen_brand_comments": [],
        "seen_competitor_blog": [], "seen_competitor_reddit": [], "seen_competitor_hn": []
    }
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                loaded = json.load(f)
                state.update(loaded)
        except json.JSONDecodeError:
            pass
    return state 

def save_state(state):
    tmp_file = f"{STATE_FILE}.tmp"
    with open(tmp_file, "w") as f:
        json.dump(state, f, indent=4)
    os.replace(tmp_file, STATE_FILE)

def send_slack_alert(title, status, severity, full_url, latest_text, is_new, source_name="Google Status Dashboard"):
    """Sends a cleanly formatted Slack message about an update/article."""
    if not SLACK_WEBHOOK_URL:
        print(f"⚠️ SLACK_WEBHOOK_URL not found. Would send: {title}")
        return

    # Clean up any literal <http...> bracket syntax that makes formatting look weird
    if isinstance(latest_text, str):
        latest_text = re.sub(r'<(https?://[^>]+)>', r'\n🔗 \1', latest_text)
        
    # Standardize our alert structure before pushing to Slack
    alert_payload = {
        "id": str(uuid.uuid4() if 'uuid' in sys.modules else hash(title + str(datetime.now()))),
        "date": datetime.now().isoformat(),
        "title": title,
        "status": status,
        "severity": severity,
        "url": full_url,
        "text": latest_text,
        "source": source_name,
        "is_new": is_new
    }
    dashboard_alerts.append(alert_payload)

    # Visuals based on severity/status
    color = "#FFA500" # Orange default
    icon = "⚠️"
    
    if source_name in ("Search Engine Roundtable", "Search Engine Journal", "Search Engine Land"):
        color = "#1E90FF" # Blue for community news
        icon = "📰"
        action_text = f"📰 *New SEO Community Report ({source_name})*"
    elif source_name == "Google Search Blog":
        color = "#0F9D58" # Google green
        icon = "📢"
        action_text = "📢 *New Google Official Blog Post*"
    elif status == "UGC Discussion":
        color = "#FF4500" # Reddit orange
        icon = "🗣️"
        action_text = "🗣️ *New Google Update UGC Discussion*"
    elif status == "Brand Mention":
        if "Positive" in severity:
            color = "#36a64f"
            icon = "🎉"
            action_text = "🎉 *New Positive SEOmonitor Mention!*"
        elif "Negative" in severity:
            color = "#e01e5a"
            icon = "🚨"
            action_text = "🚨 *New Negative SEOmonitor Mention!*"
        else:
            color = "#FFA500"
            icon = "🗣️"
            action_text = "🗣️ *New SEOmonitor Mention*"
    elif status == "Competitor Update":
        if "🤖" in severity or "AI" in severity:
            color = "#9B59B6" # Purple for AI/LLM
            icon = "🤖"
            action_text = f"🤖 *Competitor AI/LLM Update: {source_name}*"
        else:
            color = "#E67E22" # Orange for regular competitor update
            icon = "🏢"
            action_text = f"🏢 *Competitor Update: {source_name}*"
    elif status == "SERP Feature Change":
        color = "#8A2BE2" # Purple
        icon = "✨"
        action_text = "✨ *New Google SERP Feature Discussion*"
    else:
        if "AVAILABLE" in status or "RESOLVED" in status.upper():
            color = "#36a64f" # Green
            icon = "✅"
        elif severity == "HIGH":
            color = "#e01e5a" # Red
            icon = "🚨"
        action_text = "🚨 *NEW Google Search Update Detected!*" if is_new else "🔄 *Google Search Update Escalated/Resolved*"

    payload = {
        "text": f"{icon} {action_text}",
        "attachments": [
            {
                "color": color,
                "title": title,
                "title_link": full_url,
                "fields": [
                    {"title": "Source", "value": source_name, "short": True},
                    {"title": "Status/Severity", "value": f"{status} / {severity}", "short": True},
                    {"title": "Details", "value": latest_text, "short": False}
                ],
                "footer": "Google & SEO Update Monitor",
                "ts": int(time.time())
            }
        ]
    }

    try:
        resp = req.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
        print(f"✅ Slack alert sent for: {title}")
        # Throttle slightly to ensure we don't hit Slack's 1-message-per-second webhook rate limits
        time.sleep(1.2)
    except Exception as e:
        print(f"❌ Failed to send Slack alert: {e}")

def create_clickup_task(title, full_url, latest_text):
    """Creates a ClickUp task for major updates if CLICKUP_LIST_ID is present."""
    # Temporarily disabled per user request
    print("ℹ️ Skipping ClickUp task creation (Disabled)")
    return

def check_official_google_updates(state):
    print(f"[{datetime.now().isoformat()}] Checking Google Status Dashboard (Official)...")
    changes_made = False
    
    try:
        resp = req.get(GOOGLE_STATUS_URL, timeout=15)
        resp.raise_for_status()
        incidents = resp.json()
    except Exception as e:
        print(f"❌ Failed to fetch Google incidents: {e}")
        return changes_made, state

    seen_updates = state.get("seen_updates", {})

    # Check top 5 most recent incidents
    for incident in incidents[:5]:
        inc_id = incident.get("id")
        current_status = incident.get("status_impact", "UNKNOWN")
        title = incident.get("external_desc", "Google Search Update")
        severity = incident.get("severity", "unknown").upper()
        uri = incident.get("uri", "")
        full_url = f"https://status.search.google.com/{uri}" if uri else "https://status.search.google.com"
        
        updates = incident.get("updates", [])
        latest_text = updates[0].get("text", "No detailed information provided.") if updates else "No detailed information provided."
        
        # Check if this is a new incident we haven't seen before
        if inc_id not in seen_updates:
            print(f"🌟 Found NEW update: {title}")
            send_slack_alert(title, current_status, severity, full_url, latest_text, True, "Google Status Dashboard")
            
            # create ClickUp tasks for ranking/core updates or high severity
            desc_lower = title.lower()
            if "core update" in desc_lower or "spam update" in desc_lower or severity == "HIGH":
                create_clickup_task(title, full_url, latest_text)
                
            seen_updates[inc_id] = current_status
            changes_made = True
            
        # Or if it's an existing incident that changed status
        elif seen_updates[inc_id] != current_status:
            print(f"🔄 Status changed for {title}: {seen_updates[inc_id]} -> {current_status}")
            send_slack_alert(title, current_status, severity, full_url, latest_text, False, "Google Status Dashboard")
            seen_updates[inc_id] = current_status
            changes_made = True

    state["seen_updates"] = seen_updates
    return changes_made, state

def check_seo_news_rss(state):
    print(f"[{datetime.now().isoformat()}] Checking Search Engine Roundtable RSS (Community)...")
    changes_made = False
    seen_articles = state.get("seen_articles", [])
    
    try:
        feed = feedparser.parse(SER_RSS_URL)
        if feed.bozo:
             print(f"⚠️ RSS parse warning: {feed.bozo_exception}")
    except Exception as e:
        print(f"❌ Failed to fetch/parse RSS: {e}")
        return changes_made, state
        
    keyword_triggers = [
        'algorithm', 'core update', 'spam update', 'volatility', 'ranking', 
        'unconfirmed update', 'glitch', 'algo update', 'traffic drop'
    ]
    
    # Process only the 10 most recent posts
    for entry in feed.entries[:10]:
        article_id = entry.get('id', entry.get('link'))
        title = entry.get('title', '')
        link = entry.get('link', '')
        summary = entry.get('summary', '')[:300] + "..." # Truncate long summaries
        
        # We only care about articles that look like Google algorithm/ranking news
        # SER covers other search engines and PPC too, so we filter.
        title_lower = title.lower()
        if 'google' not in title_lower:
            continue
            
        if not any(kw in title_lower for kw in keyword_triggers):
            continue
            
        if article_id not in seen_articles:
            print(f"📰 Found relevant SEO News: {title}")
            send_slack_alert(
                title=title, 
                status="Community Report", 
                severity="Info/Unconfirmed", 
                full_url=link, 
                latest_text=summary, 
                is_new=True, 
                source_name="Search Engine Roundtable"
            )
            seen_articles.append(article_id)
            changes_made = True
            
    # keep list from growing indefinitely
    if len(seen_articles) > 100:
        seen_articles = seen_articles[-50:]
        
    state["seen_articles"] = seen_articles
    return changes_made, state

def check_reddit_ugc(state):
    print(f"[{datetime.now().isoformat()}] Checking Reddit UGC (Community)...")
    changes_made = False
    seen_ugc = state.get("seen_ugc", [])
    
    headers = {"User-Agent": "mac:google_update_monitor:v1.0 (by /u/SEOMonitor)"}
    url = "https://www.reddit.com/r/SEO+TechSEO/new.json?limit=25"
    
    try:
        resp = req.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        posts = resp.json().get('data', {}).get('children', [])
    except Exception as e:
        print(f"❌ Failed to fetch Reddit UGC: {e}")
        return changes_made, state
        
    keyword_triggers = [
        'algorithm', 'core update', 'spam update', 'volatility', 'tanked', 
        'plummet', 'traffic drop', 'huge drop', 'ranking drop', 'algo update'
    ]
    feature_triggers = [
        'ai overview', 'sge', 'featured snippet', 'rich snippet', 'local pack',
        'knowledge graph', 'knowledge panel', 'people also ask', 'serp feature',
        'rich result', 'search generative experience', 'zero click', 'zero-click'
    ]
    
    for post in posts:
        data = post.get('data', {})
        post_id = data.get('id')
        created_utc = data.get('created_utc', 0)
        
        # Discard posts older than 7 days
        if time.time() - created_utc > 7 * 86400:
            continue
            
        title = data.get('title', '')
        link = f"https://www.reddit.com{data.get('permalink', '')}"
        
        selftext_raw = data.get('selftext', '')
        selftext = selftext_raw[:300] + "..." if selftext_raw else "No description provided."
        
        title_lower = title.lower()
        body_lower = selftext_raw.lower()
        
        # Require "google" to be mentioned
        if 'google' not in title_lower and 'google' not in body_lower:
            continue
            
        found_algo = any(kw in title_lower or kw in body_lower for kw in keyword_triggers)
        found_feat = any(kw in title_lower or kw in body_lower for kw in feature_triggers)
        
        if not found_algo and not found_feat:
            continue
            
        alert_status = "SERP Feature Change" if found_feat and not found_algo else "UGC Discussion"
            
        if post_id not in seen_ugc:
            print(f"🗣️ Found relevant UGC Discussion: {title}")
            send_slack_alert(
                title=title, 
                status=alert_status, 
                severity="Info/Unconfirmed", 
                full_url=link, 
                latest_text=selftext, 
                is_new=True, 
                source_name=f"Reddit (r/{data.get('subreddit', 'SEO')})"
            )
            seen_ugc.append(post_id)
            changes_made = True
            
    if len(seen_ugc) > 100:
        seen_ugc = seen_ugc[-50:]
        
    state["seen_ugc"] = seen_ugc
    return changes_made, state

def analyze_sentiment(text, target_keyword='seomonitor', window=15):
    import string
    # Remove punctuation for cleaner word splitting
    text_clean = text.lower().translate(str.maketrans('', '', string.punctuation))
    words = text_clean.split()
    
    positive_words = {'love', 'great', 'awesome', 'best', 'good', 'amazing', 'recommend', 'helpful', 'fantastic', 'excellent', 'solid', 'nice'}
    negative_words = {'bad', 'terrible', 'worst', 'hate', 'cancel', 'bug', 'issue', 'slow', 'expensive', 'useless', 'garbage', 'crashed', 'poor', 'trash', 'broken'}
    
    # Find all indices of the target keyword
    target_indices = [i for i, w in enumerate(words) if target_keyword in w]
    
    # If the exact keyword isn't perfectly isolated (e.g. typos), default to full text
    if not target_indices:
        start, end = 0, len(words)
        target_indices = [0]
        window = len(words)
        
    pos_score = 0
    neg_score = 0
    
    # We only score words that appear within `window` distance of the brand mention
    scored_words = set()
    for i in target_indices:
        start = max(0, i - window)
        end = min(len(words), i + window + 1)
        for j in range(start, end):
            if j not in scored_words:
                w = words[j]
                if w in positive_words:
                    pos_score += 1
                if w in negative_words:
                    neg_score += 1
                scored_words.add(j)
    
    if pos_score > neg_score:
        return 1, "Positive 😊"
    elif neg_score > pos_score:
        return -1, "Negative 😡"
    else:
        return 0, "Neutral 😐"

def check_brand_mentions(state):
    print(f"[{datetime.now().isoformat()}] Checking Reddit for SEOmonitor mentions...")
    changes_made = False
    seen_mentions = state.get("seen_brand_mentions", [])
    
    headers = {"User-Agent": "mac:brand_monitor:v1.0 (by /u/SEOMonitor)"}
    # Search reddit globally for 'seomonitor'
    url = "https://www.reddit.com/search.json?q=seomonitor&sort=new&limit=25"
    
    try:
        resp = req.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        posts = resp.json().get('data', {}).get('children', [])
    except Exception as e:
        print(f"❌ Failed to fetch Brand Mentions: {e}")
        return changes_made, state
        
    new_mentions = []
    
    for post in posts:
        data = post.get('data', {})
        post_id = data.get('id')
        created_utc = data.get('created_utc', 0)
        
        if not post_id or post_id in seen_mentions:
            continue
            
        # Discard posts older than 90 days (brand mentions are rare)
        if time.time() - created_utc > 90 * 86400:
            continue
            
        title = data.get('title', '')
        selftext_raw = data.get('selftext', '')
        link = f"https://www.reddit.com{data.get('permalink', '')}"
        
        # Ensure it actually mentions our brand
        if 'seomonitor' not in title.lower() and 'seomonitor' not in selftext_raw.lower():
            continue
            
        score, label = analyze_sentiment(title + " " + selftext_raw)
        
        new_mentions.append({
            'post_id': post_id,
            'title': title,
            'text': selftext_raw[:300] + "..." if selftext_raw else "No description provided.",
            'link': link,
            'score': score,
            'label': label,
            'subreddit': data.get('subreddit', 'Unknown')
        })

    # Sort by sentiment score (-1 Negative first, 0 Neutral, 1 Positive)
    new_mentions.sort(key=lambda x: x['score'])
    
    for mention in new_mentions:
        print(f"🗣️ Found Brand Mention ({mention['label']}): {mention['title']}")
        send_slack_alert(
            title=f"{mention['label']} Mention on r/{mention['subreddit']}", 
            status="Brand Mention", 
            severity=mention['label'], 
            full_url=mention['link'], 
            latest_text=f"*{mention['title']}*\n{mention['text']}", 
            is_new=True, 
            source_name=f"Reddit (r/{mention['subreddit']})"
        )
        seen_mentions.append(mention['post_id'])
        changes_made = True

    if len(seen_mentions) > 100:
        seen_mentions = seen_mentions[-50:]
        
    state["seen_brand_mentions"] = seen_mentions
    return changes_made, state

def check_hn_brand_mentions(state):
    print(f"[{datetime.now().isoformat()}] Checking Hacker News for SEOmonitor mentions...")
    changes_made = False
    seen_mentions = state.get("seen_hn_brand_mentions", [])
    
    url = "https://hn.algolia.com/api/v1/search_by_date?query=seomonitor"
    
    try:
        resp = req.get(url, timeout=15)
        resp.raise_for_status()
        posts = resp.json().get('hits', [])
    except Exception as e:
        print(f"❌ Failed to fetch HN Brand Mentions: {e}")
        return changes_made, state
        
    new_mentions = []
    
    for post in posts:
        post_id = str(post.get('objectID'))
        if not post_id or post_id in seen_mentions:
            continue
            
        created_at_i = post.get('created_at_i', 0)
        if time.time() - created_at_i > 90 * 86400:
            continue
            
        title = post.get('title') or post.get('story_title') or ""
        text = post.get('comment_text') or ""
        link = f"https://news.ycombinator.com/item?id={post_id}"
        
        if 'seomonitor' not in title.lower() and 'seomonitor' not in text.lower():
            continue
            
        score, label = analyze_sentiment(title + " " + text)
        clean_text = re.sub(r'<[^>]+>', '', text)[:300] + "..." if text else "No description provided."
        
        new_mentions.append({
            'post_id': post_id,
            'title': title,
            'text': clean_text,
            'link': link,
            'score': score,
            'label': label,
            'source': 'Hacker News'
        })

    new_mentions.sort(key=lambda x: x['score'])
    
    for mention in new_mentions:
        print(f"🗣️ Found HN Brand Mention ({mention['label']}): {mention['title']}")
        send_slack_alert(
            title=f"{mention['label']} Mention on HN", 
            status="Brand Mention", 
            severity=mention['label'], 
            full_url=mention['link'], 
            latest_text=f"*{mention['title']}*\n{mention['text']}", 
            is_new=True, 
            source_name=mention['source']
        )
        seen_mentions.append(mention['post_id'])
        changes_made = True

    if len(seen_mentions) > 100:
        seen_mentions = seen_mentions[-50:]
        
    state["seen_hn_brand_mentions"] = seen_mentions
    return changes_made, state

def check_hn_ugc(state):
    print(f"[{datetime.now().isoformat()}] Checking Hacker News UGC...")
    changes_made = False
    seen_ugc = state.get("seen_hn_ugc", [])
    
    url = "https://hn.algolia.com/api/v1/search_by_date?query=google update"
    
    try:
        resp = req.get(url, timeout=15)
        resp.raise_for_status()
        posts = resp.json().get('hits', [])
    except Exception as e:
        print(f"❌ Failed to fetch HN UGC: {e}")
        return changes_made, state
        
    keyword_triggers = [
        'algorithm', 'core update', 'spam update', 'volatility', 'tanked', 
        'plummet', 'traffic drop', 'huge drop', 'ranking drop', 'algo update'
    ]
    feature_triggers = [
        'ai overview', 'sge', 'featured snippet', 'rich snippet', 'local pack',
        'knowledge graph', 'knowledge panel', 'people also ask', 'serp feature',
        'rich result', 'search generative experience', 'zero click', 'zero-click'
    ]
    
    for post in posts:
        post_id = str(post.get('objectID'))
        if not post_id or post_id in seen_ugc:
            continue
            
        created_at_i = post.get('created_at_i', 0)
        if time.time() - created_at_i > 7 * 86400:
            continue
            
        title = post.get('title') or post.get('story_title') or ""
        text = post.get('comment_text') or ""
        link = f"https://news.ycombinator.com/item?id={post_id}"
        
        title_lower = title.lower()
        body_lower = text.lower()
        
        if 'google' not in title_lower and 'google' not in body_lower:
            continue
            
        found_algo = any(kw in title_lower or kw in body_lower for kw in keyword_triggers)
        found_feat = any(kw in title_lower or kw in body_lower for kw in feature_triggers)
        
        if not found_algo and not found_feat:
            continue
            
        alert_status = "SERP Feature Change" if found_feat and not found_algo else "UGC Discussion"
            
        clean_text = re.sub(r'<[^>]+>', '', text)[:300] + "..." if text else "No description provided."
        
        print(f"🗣️ Found relevant HN Discussion: {title}")
        send_slack_alert(
            title=title, 
            status=alert_status, 
            severity="Info/Unconfirmed", 
            full_url=link, 
            latest_text=clean_text, 
            is_new=True, 
            source_name="Hacker News"
        )
        seen_ugc.append(post_id)
        changes_made = True

    if len(seen_ugc) > 100:
        seen_ugc = seen_ugc[-50:]
        
    state["seen_hn_ugc"] = seen_ugc
    return changes_made, state

def check_sej_rss(state):
    """Check Search Engine Journal RSS for Google algo news."""
    print(f"[{datetime.now().isoformat()}] Checking Search Engine Journal RSS...")
    changes_made = False
    seen_articles = state.get("seen_sej_articles", [])
    
    try:
        feed = feedparser.parse(SEJ_RSS_URL)
        if feed.bozo:
            print(f"⚠️ SEJ RSS parse warning: {feed.bozo_exception}")
    except Exception as e:
        print(f"❌ Failed to fetch/parse SEJ RSS: {e}")
        return changes_made, state
        
    keyword_triggers = [
        'algorithm', 'core update', 'spam update', 'volatility', 'ranking',
        'unconfirmed update', 'glitch', 'algo update', 'traffic drop',
        'search update', 'indexing', 'crawling', 'penalty'
    ]
    
    for entry in feed.entries[:15]:
        article_id = entry.get('id', entry.get('link'))
        title = entry.get('title', '')
        link = entry.get('link', '')
        summary = entry.get('summary', '')[:300] + "..."
        
        title_lower = title.lower()
        if 'google' not in title_lower:
            continue
        if not any(kw in title_lower for kw in keyword_triggers):
            continue
            
        if article_id not in seen_articles:
            print(f"📰 Found SEJ article: {title}")
            send_slack_alert(
                title=title,
                status="Community Report",
                severity="Info/Unconfirmed",
                full_url=link,
                latest_text=summary,
                is_new=True,
                source_name="Search Engine Journal"
            )
            seen_articles.append(article_id)
            changes_made = True
            
    if len(seen_articles) > 100:
        seen_articles = seen_articles[-50:]
        
    state["seen_sej_articles"] = seen_articles
    return changes_made, state

def check_sel_rss(state):
    """Check Search Engine Land RSS for Google algo news."""
    print(f"[{datetime.now().isoformat()}] Checking Search Engine Land RSS...")
    changes_made = False
    seen_articles = state.get("seen_sel_articles", [])
    
    try:
        feed = feedparser.parse(SEL_RSS_URL)
        if feed.bozo:
            print(f"⚠️ SEL RSS parse warning: {feed.bozo_exception}")
    except Exception as e:
        print(f"❌ Failed to fetch/parse SEL RSS: {e}")
        return changes_made, state
        
    keyword_triggers = [
        'algorithm', 'core update', 'spam update', 'volatility', 'ranking update',
        'search update', 'indexing change', 'crawling change', 'penalty',
        'helpful content', 'link spam', 'manual action'
    ]
    
    for entry in feed.entries[:15]:
        article_id = entry.get('id', entry.get('link'))
        title = entry.get('title', '')
        link = entry.get('link', '')
        summary = entry.get('summary', '')[:300] + "..."
        
        title_lower = title.lower()
        if 'google' not in title_lower:
            continue
        if not any(kw in title_lower for kw in keyword_triggers):
            continue
            
        if article_id not in seen_articles:
            print(f"📰 Found SEL article: {title}")
            send_slack_alert(
                title=title,
                status="Community Report",
                severity="Info/Unconfirmed",
                full_url=link,
                latest_text=summary,
                is_new=True,
                source_name="Search Engine Land"
            )
            seen_articles.append(article_id)
            changes_made = True
            
    if len(seen_articles) > 100:
        seen_articles = seen_articles[-50:]
        
    state["seen_sel_articles"] = seen_articles
    return changes_made, state

def check_google_blog_rss(state):
    """Check Google Search Blog for official announcements."""
    print(f"[{datetime.now().isoformat()}] Checking Google Search Blog RSS...")
    changes_made = False
    seen_articles = state.get("seen_google_blog", [])
    
    try:
        feed = feedparser.parse(GOOGLE_BLOG_RSS_URL)
        if feed.bozo:
            print(f"⚠️ Google Blog RSS parse warning: {feed.bozo_exception}")
    except Exception as e:
        print(f"❌ Failed to fetch/parse Google Blog RSS: {e}")
        return changes_made, state
        
    keyword_triggers = [
        'search ranking', 'search update', 'core update', 'algorithm', 'indexing',
        'crawl', 'spam', 'search quality', 'helpful content', 'webmaster',
        'ai overview', 'search console', 'search generative', 'web search',
        'google search', 'structured data', 'rich result'
    ]
    
    for entry in feed.entries[:10]:
        article_id = entry.get('id', entry.get('link'))
        title = entry.get('title', '')
        link = entry.get('link', '')
        summary = entry.get('summary', '')[:300] + "..."
        
        title_lower = title.lower()
        if not any(kw in title_lower for kw in keyword_triggers):
            continue
            
        if article_id not in seen_articles:
            print(f"📢 Found Google Blog post: {title}")
            send_slack_alert(
                title=title,
                status="Official Announcement",
                severity="Official",
                full_url=link,
                latest_text=summary,
                is_new=True,
                source_name="Google Search Blog"
            )
            seen_articles.append(article_id)
            changes_made = True
            
    if len(seen_articles) > 100:
        seen_articles = seen_articles[-50:]
        
    state["seen_google_blog"] = seen_articles
    return changes_made, state

def check_reddit_brand_comments(state):
    """Check Reddit comments (not just posts) for SEOmonitor mentions."""
    print(f"[{datetime.now().isoformat()}] Checking Reddit Comments for SEOmonitor mentions...")
    changes_made = False
    seen_comments = state.get("seen_brand_comments", [])
    
    headers = {"User-Agent": "mac:brand_monitor:v1.0 (by /u/SEOMonitor)"}
    url = "https://www.reddit.com/search.json?q=seomonitor&type=comment&sort=new&limit=25"
    
    try:
        resp = req.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        comments = resp.json().get('data', {}).get('children', [])
    except Exception as e:
        print(f"❌ Failed to fetch Reddit comments: {e}")
        return changes_made, state
        
    new_mentions = []
    
    for comment in comments:
        data = comment.get('data', {})
        comment_id = data.get('id')
        created_utc = data.get('created_utc', 0)
        
        if not comment_id or comment_id in seen_comments:
            continue
            
        # Only comments from last 14 days
        if time.time() - created_utc > 30 * 86400:
            continue
            
        body = data.get('body', '')
        link_title = data.get('link_title', '')
        permalink = data.get('permalink', '')
        link = f"https://www.reddit.com{permalink}"
        subreddit = data.get('subreddit', 'Unknown')
        
        # Must actually mention seomonitor
        if 'seomonitor' not in body.lower():
            continue
            
        score, label = analyze_sentiment(body)
        
        new_mentions.append({
            'comment_id': comment_id,
            'title': link_title or f"Comment in r/{subreddit}",
            'text': body[:300] + "..." if len(body) > 300 else body,
            'link': link,
            'score': score,
            'label': label,
            'subreddit': subreddit
        })
    
    # Negative first
    new_mentions.sort(key=lambda x: x['score'])
    
    for mention in new_mentions:
        print(f"💬 Found Brand Comment ({mention['label']}): {mention['title'][:60]}")
        send_slack_alert(
            title=f"{mention['label']} Comment in r/{mention['subreddit']}",
            status="Brand Mention",
            severity=mention['label'],
            full_url=mention['link'],
            latest_text=f"*{mention['title']}*\n{mention['text']}",
            is_new=True,
            source_name=f"Reddit Comment (r/{mention['subreddit']})"
        )
        seen_comments.append(mention['comment_id'])
        changes_made = True
    
    if len(seen_comments) > 200:
        seen_comments = seen_comments[-100:]
        
    state["seen_brand_comments"] = seen_comments
    return changes_made, state

def is_ai_related(text):
    """Check if text contains AI/LLM related keywords."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in AI_LLM_KEYWORDS)

def check_competitor_blogs(state):
    """Check competitor blog RSS feeds for product updates."""
    print(f"[{datetime.now().isoformat()}] Checking Competitor Blog RSS feeds...")
    changes_made = False
    seen_articles = state.get("seen_competitor_blog", [])
    
    # Keywords that signal a genuine NEW feature launch only.
    # Intentionally excludes broad terms like 'product update', 'changelog',
    # 'update:', 'what\'s new' — these catch too many non-launch posts.
    feature_launch_keywords = [
        'new feature', 'launch', 'just launched', 'launching',
        'announcing', 'we are announcing', 'announcing our',
        'introducing', 'introducing our', 'introducing the',
        'now available', 'now live', 'beta release', 'beta launch',
        'new integration', 'new api', "we've added", "we're launching",
        'we just released', 'we just launched', 'early access',
        'rolling out', 'shipped', 'just shipped'
    ]
    
    for competitor_name, feed_url in COMPETITOR_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo and len(feed.entries) == 0:
                print(f"  ⚠️ {competitor_name} RSS parse error: {feed.bozo_exception}")
                continue
        except Exception as e:
            print(f"  ❌ Failed to fetch {competitor_name} RSS: {e}")
            continue
            
        for entry in feed.entries[:10]:
            article_id = entry.get('id', entry.get('link', ''))
            title = entry.get('title', '')
            link = entry.get('link', '')
            
            # Use content:encoded if available (full article in RSS), else fall back to summary.
            # This covers 3x more signal with zero extra HTTP requests.
            content_encoded = ''
            if hasattr(entry, 'content') and entry.content:
                content_encoded = entry.content[0].get('value', '')[:800]
            if not content_encoded:
                content_encoded = entry.get('summary', '')[:800]
            
            if article_id in seen_articles:
                continue
            
            combined_text = f"{title} {content_encoded}".lower()
            
            # Determine if AI/LLM related (always pass through)
            ai_flag = is_ai_related(combined_text)
            
            # Must be either: AI/LLM related OR a genuine new feature launch.
            # Broad editorial content (roundups, guides, research) is excluded.
            is_feature_launch = any(kw in combined_text for kw in feature_launch_keywords)
            if not ai_flag and not is_feature_launch:
                continue
            
            severity = "🤖 AI/LLM" if ai_flag else "🚀 Feature Launch"
            
            label = f"{'🤖 ' if ai_flag else ''}{competitor_name}"
            print(f"  🏢 Found {label} update: {title[:60]}")
            
            send_slack_alert(
                title=f"[{competitor_name}] {title}",
                status="Competitor Update",
                severity=severity,
                full_url=link,
                latest_text=content_encoded[:300] + "...",
                is_new=True,
                source_name=competitor_name
            )
            seen_articles.append(article_id)
            changes_made = True
    
    if len(seen_articles) > 300:
        seen_articles = seen_articles[-150:]
        
    state["seen_competitor_blog"] = seen_articles
    return changes_made, state

# Subreddits where people post about their own indie tools — not relevant for competitor monitoring
PROMO_SUBREDDITS = {
    'saas', 'entrepreneur', 'startups', 'indiehackers', 'sideproject',
    'buildinpublic', 'microsaas', 'alphaandbeta', 'producthunt',
    'forhire', 'sideprojects', 'shareprojects'
}

# Phrases that indicate someone is pitching their own tool (not discussing an established competitor)
SELF_PROMO_PATTERNS = [
    'i built', "i've built", 'i made', "i've made", 'we built', "we've built",
    'i created', 'we created', 'i launched', 'we launched', 'i just launched',
    'just launched my', 'just released my', 'introducing my', 'my new tool',
    'my tool does', 'beta tester', 'beta testers', 'looking for beta',
    'looking for testers', 'looking for users', 'seeking feedback',
    'would love feedback', 'give me feedback', 'free for a month',
    'first 100 users', 'show hn:', 'show hn -',
    'built an', 'built a tool', 'built this', 'made a tool',
    'side project', 'solo founder', 'indie hacker', "i'm building",
    "we're building", 'my startup', 'my saas', 'my product',
]

def check_competitor_reddit(state):
    """Check Reddit for competitor product updates and discussions.
    Only surfaces posts where an ESTABLISHED competitor is the main subject,
    not indie self-promo posts that merely mention a competitor in passing.
    """
    print(f"[{datetime.now().isoformat()}] Checking Reddit for Competitor Updates...")
    changes_made = False
    seen_posts = state.get("seen_competitor_reddit", [])
    
    headers = {"User-Agent": "mac:competitor_monitor:v1.0 (by /u/SEOMonitor)"}
    
    # Search for competitor product updates on Reddit
    search_terms = [
        "semrush new feature", "semrush update", "semrush ai",
        "ahrefs new feature", "ahrefs update", "ahrefs ai",
        "se ranking update", "accuranker update",
        "sistrix update", "brightedge ai",
        "moz pro update", "surfer seo ai"
    ]
    
    all_posts = []
    for term in search_terms:
        try:
            url = f"https://www.reddit.com/search.json?q={term}&sort=new&limit=10&t=month"
            resp = req.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            posts = resp.json().get('data', {}).get('children', [])
            all_posts.extend(posts)
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            continue
    
    # Deduplicate by post ID
    unique_posts = {}
    for post in all_posts:
        post_id = post.get('data', {}).get('id')
        if post_id and post_id not in unique_posts:
            unique_posts[post_id] = post
    
    new_items = []
    for post in unique_posts.values():
        data = post.get('data', {})
        post_id = data.get('id')
        created_utc = data.get('created_utc', 0)
        
        if not post_id or post_id in seen_posts:
            continue
            
        # Only last 30 days
        if time.time() - created_utc > 30 * 86400:
            continue
        
        title = data.get('title', '')
        selftext = data.get('selftext', '')[:300]
        link = f"https://www.reddit.com{data.get('permalink', '')}"
        subreddit = data.get('subreddit', '')
        
        combined_text = f"{title} {selftext}".lower()
        title_lower = title.lower()
        
        # --- FILTER 1: Skip indie/startup self-promo subreddits ---
        # These communities are for founders pitching their own tools, not competitor news.
        if subreddit.lower() in PROMO_SUBREDDITS:
            print(f"  ⏭️ Skipping r/{subreddit} (promo sub): {title[:55]}")
            seen_posts.append(post_id)  # Mark seen so we never re-check it
            continue
        
        # --- FILTER 2: Exclude self-promotional "I built X" posts ---
        # These are indie founders who mention an established competitor only as a
        # reference point (e.g. "tired of paying for Ahrefs so I built my own tool").
        if any(p in combined_text for p in SELF_PROMO_PATTERNS):
            print(f"  ⏭️ Skipping self-promo post: {title[:55]}")
            seen_posts.append(post_id)  # Mark seen
            continue
        
        # --- FILTER 3: Competitor must appear in the TITLE ---
        # If the competitor is only mentioned in the body (e.g. a passing price comparison),
        # the post is NOT genuinely about that competitor.
        matched_competitor = None
        for comp_name in COMPETITOR_NAMES:
            if comp_name in title_lower:
                matched_competitor = comp_name.title()
                break
        
        if not matched_competitor:
            continue
            
        # Determine if AI/LLM related
        ai_flag = is_ai_related(combined_text)
        severity = "🤖 AI/LLM" if ai_flag else "Product Discussion"
        
        new_items.append({
            'post_id': post_id,
            'title': title,
            'text': selftext,
            'link': link,
            'competitor': matched_competitor,
            'subreddit': subreddit,
            'severity': severity,
            'ai_flag': ai_flag,
            'created_utc': created_utc
        })
    
    # AI-related first, then by recency
    new_items.sort(key=lambda x: (not x['ai_flag'], -x['created_utc']))
    
    for item in new_items[:10]:  # Cap at 10 per run to avoid flooding
        label = f"{'🤖 ' if item['ai_flag'] else '🏢 '}{item['competitor']}"
        print(f"  {label} Reddit discussion: {item['title'][:60]}")
        
        send_slack_alert(
            title=f"[{item['competitor']}] {item['title']}",
            status="Competitor Update",
            severity=item['severity'],
            full_url=item['link'],
            latest_text=item['text'],
            is_new=True,
            source_name=f"Reddit (r/{item['subreddit']})"
        )
        seen_posts.append(item['post_id'])
        changes_made = True
    
    if len(seen_posts) > 300:
        seen_posts = seen_posts[-150:]
        
    state["seen_competitor_reddit"] = seen_posts
    return changes_made, state

def check_competitor_hn(state):
    """Check Hacker News for competitor product announcements."""
    print(f"[{datetime.now().isoformat()}] Checking Hacker News for Competitor Updates...")
    changes_made = False
    seen_posts = state.get("seen_competitor_hn", [])
    
    headers = {"User-Agent": "mac:competitor_monitor:v1.0"}
    
    search_terms = ["semrush", "ahrefs", "sistrix", "accuranker", "brightedge", "moz seo"]
    
    for term in search_terms:
        try:
            url = f"https://hn.algolia.com/api/v1/search_by_date?query={term}&tags=story&hitsPerPage=5"
            resp = req.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            hits = resp.json().get('hits', [])
        except Exception as e:
            continue
        
        for hit in hits:
            post_id = hit.get('objectID')
            created_at_i = hit.get('created_at_i', 0)
            
            if not post_id or post_id in seen_posts:
                continue
                
            # Only last 30 days
            if time.time() - created_at_i > 30 * 86400:
                continue
            
            title = hit.get('title', '')
            url_link = hit.get('url', '') or f"https://news.ycombinator.com/item?id={post_id}"
            hn_link = f"https://news.ycombinator.com/item?id={post_id}"
            points = hit.get('points', 0)
            
            # Only significant discussions (5+ points)
            if points < 5:
                continue
            
            # Identify competitor
            title_lower = title.lower()
            matched_competitor = None
            for comp_name in COMPETITOR_NAMES:
                if comp_name in title_lower:
                    matched_competitor = comp_name.title()
                    break
            
            if not matched_competitor:
                continue
            
            ai_flag = is_ai_related(title_lower)
            severity = "🤖 AI/LLM" if ai_flag else "Product Discussion"
            
            label = f"{'🤖 ' if ai_flag else '🏢 '}{matched_competitor}"
            print(f"  {label} HN post ({points}pts): {title[:60]}")
            
            send_slack_alert(
                title=f"[{matched_competitor}] {title}",
                status="Competitor Update",
                severity=severity,
                full_url=hn_link,
                latest_text=f"Discussion on Hacker News ({points} points)\n🔗 Original: {url_link}",
                is_new=True,
                source_name="Hacker News"
            )
            seen_posts.append(post_id)
            changes_made = True
    
    if len(seen_posts) > 200:
        seen_posts = seen_posts[-100:]
        
    state["seen_competitor_hn"] = seen_posts
    return changes_made, state

def main():
    state = load_state()
    
    all_changes = []
    
    # Official sources
    changes, state = check_official_google_updates(state)
    all_changes.append(changes)
    
    # Community news RSS
    changes, state = check_seo_news_rss(state)
    all_changes.append(changes)
    changes, state = check_sej_rss(state)
    all_changes.append(changes)
    changes, state = check_sel_rss(state)
    all_changes.append(changes)
    changes, state = check_google_blog_rss(state)
    all_changes.append(changes)
    
    # UGC discussions
    changes, state = check_reddit_ugc(state)
    all_changes.append(changes)
    changes, state = check_hn_ugc(state)
    all_changes.append(changes)
    
    # Brand mentions (posts + comments)
    changes, state = check_brand_mentions(state)
    all_changes.append(changes)
    changes, state = check_reddit_brand_comments(state)
    all_changes.append(changes)
    changes, state = check_hn_brand_mentions(state)
    all_changes.append(changes)
    
    # Competitor intelligence
    changes, state = check_competitor_blogs(state)
    all_changes.append(changes)
    changes, state = check_competitor_reddit(state)
    all_changes.append(changes)
    changes, state = check_competitor_hn(state)
    all_changes.append(changes)
    
    # SERP Volatility (always fetch — it's a daily snapshot, not alert-based)
    fetch_serp_volatility()
    
    if any(all_changes):
        save_state(state)
        print("💾 State updated across all sources.")
    else:
        print("✅ No new updates, news, or brand mentions detected.")
        
    if dashboard_alerts:
        import subprocess
        try:
            if os.path.exists(DASHBOARD_FILE):
                with open(DASHBOARD_FILE, "r") as f:
                    data = json.load(f)
            else:
                data = []
            
            # Deduplicate by URL before adding
            existing_urls = {item.get('url') for item in data}
            new_alerts = [a for a in dashboard_alerts if a.get('url') not in existing_urls]
            
            # Prepend new alerts
            data = new_alerts + data
            # Keep rolling history of max 500
            data = data[:500]
            
            with tempfile.NamedTemporaryFile('w', delete=False) as tf:
                json.dump(data, tf, indent=4)
                tmp_file = tf.name
            os.replace(tmp_file, DASHBOARD_FILE)
            print(f"📈 Added {len(new_alerts)} new alerts to {DASHBOARD_FILE} ({len(dashboard_alerts) - len(new_alerts)} duplicates skipped).")
            
            # Attempt to auto-commit and push so Netlify auto-deploys
            if new_alerts:
                print("📦 Attempting to sync dashboard data with GitHub...")
                subprocess.run(["git", "add", DASHBOARD_FILE], check=False)
                if os.path.exists(VOLATILITY_FILE):
                    subprocess.run(["git", "add", VOLATILITY_FILE], check=False)
                subprocess.run(["git", "commit", "-m", f"Dashboard datasync: {len(new_alerts)} new automated alerts"], check=False)
                subprocess.run(["git", "push"], check=False)
        except Exception as e:
            print(f"❌ Failed to locally save or push dashboard data: {e}")

if __name__ == "__main__":
    main()
