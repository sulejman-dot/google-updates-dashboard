import os
import json
import time
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
STATE_FILE = "google_updates_state.json"
DASHBOARD_FILE = "dashboard/dashboard_data.json"
dashboard_alerts = []

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
        "seen_brand_mentions": [], "seen_hn_brand_mentions": [], "seen_hn_ugc": []
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
    
    if source_name == "Search Engine Roundtable":
        color = "#1E90FF" # Blue for community news
        icon = "📰"
        action_text = "📰 *New SEO Community Report*"
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
            
        # Discard posts older than 7 days
        if time.time() - created_utc > 7 * 86400:
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
        if time.time() - created_at_i > 7 * 86400:
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

def main():
    state = load_state()
    
    changes_a, state = check_official_google_updates(state)
    changes_b, state = check_seo_news_rss(state)
    changes_c, state = check_reddit_ugc(state)
    changes_d, state = check_brand_mentions(state)
    changes_e, state = check_hn_ugc(state)
    changes_f, state = check_hn_brand_mentions(state)
    
    if any([changes_a, changes_b, changes_c, changes_d, changes_e, changes_f]):
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
            
            # Prepend new alerts
            data = dashboard_alerts + data
            # Keep rolling history of max 500
            data = data[:500]
            
            with tempfile.NamedTemporaryFile('w', delete=False) as tf:
                json.dump(data, tf, indent=4)
                tmp_file = tf.name
            os.replace(tmp_file, DASHBOARD_FILE)
            print(f"📈 Added {len(dashboard_alerts)} new alerts to {DASHBOARD_FILE}.")
            
            # Attempt to auto-commit and push so Netlify auto-deploys
            print("📦 Attempting to sync dashboard data with GitHub...")
            subprocess.run(["git", "add", DASHBOARD_FILE], check=False)
            subprocess.run(["git", "commit", "-m", f"Dashboard datasync: {len(dashboard_alerts)} new automated alerts"], check=False)
            subprocess.run(["git", "push"], check=False)
        except Exception as e:
            print(f"❌ Failed to locally save or push dashboard data: {e}")

if __name__ == "__main__":
    main()
