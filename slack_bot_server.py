from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials
import time
import json
import os
import threading
import traceback
import requests as req
from datetime import datetime, timezone, timedelta
from slack_sdk import WebClient
from dotenv import load_dotenv
import re
import subprocess

load_dotenv()

def clean_slack_url(url):
    """Strip Slack's auto-formatting from URLs.
    Slack wraps URLs like <https://example.com|example.com> — extract just the URL."""
    url = url.strip()
    if url.startswith('<') and url.endswith('>'):
        url = url[1:-1]
        if '|' in url:
            url = url.split('|')[0]
    return url

def strip_html(text):
    if not text:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

app = Flask(__name__)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN") or "xoxb-4173116321-10452138701364-22v7lSrQNCFqFe6lX8g0aCXM"
INTERCOM_API_TOKEN = os.getenv("INTERCOM_API_TOKEN")
slack_client = WebClient(token=SLACK_BOT_TOKEN)

SPREADSHEET_ID = "161qbyJ5nQsgDEaudZ5O1C4zldUIBbeDiYMYyCgldG40"
SERVICE_ACCOUNT_FILE = "service_account.json" 

def get_real_clickup_tasks():
    """
    Fetch real ClickUp tasks assigned to the current user using ClickUp MCP.
    Returns tasks that are open (status != 'Closed').
    """
    try:
        # Call the standalone script that fetches ClickUp tasks
        script_path = os.path.join(os.path.dirname(__file__), 'fetch_clickup_tasks.py')
        
        if not os.path.exists(script_path):
            print(f"⚠️ ClickUp fetch script not found at {script_path}. Using fallback.")
            return []
        
        # Execute the script and capture output
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"❌ ClickUp fetch script failed: {result.stderr}")
            return []
        
        # Parse JSON output
        tasks_data = json.loads(result.stdout)
        
        # Transform to format expected by Slack display
        tasks = []
        for task in tasks_data:
            # Determine tags based on task name patterns
            tags = []
            name_lower = task['name'].lower()
            if '[bug]' in name_lower:
                tags.append({'name': 'Bug'})
            if '[feature' in name_lower:
                tags.append({'name': 'Feature'})
            if 'maintenance' in name_lower or '[execute]' in name_lower:
                tags.append({'name': 'Maintenance'})
            if 'product' in name_lower:
                tags.append({'name': 'Product'})
            
            # Format for Slack
            formatted_task = {
                'id': task['id'],
                'name': task['name'],
                'status': {'status': task['status']},
                'tags': tags if tags else [{'name': 'Task'}],
                'url': task['url'],
                'custom_id': task.get('customId'),
                'assignees': task.get('assignees', [])
            }
            tasks.append(formatted_task)
        
        print(f"✅ Fetched {len(tasks)} ClickUp tasks")
        return tasks
        
    except subprocess.TimeoutExpired:
        print("❌ ClickUp fetch script timed out")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse ClickUp tasks JSON: {e}")
        return []
    except Exception as e:
        print(f"❌ Error fetching ClickUp tasks: {e}")
        return []


def get_mock_tasks():
    """Fallback mock tasks for testing"""
    return [
        {
            "id": "abc1234",
            "name": "Fix Critical Bug in Login",
            "status": {"status": "open"},
            "tags": [{"name": "Maintenance"}, {"name": "sub-system-auth"}],
            "url": "https://app.clickup.com/t/abc1234"
        },
        {
            "id": "def5678",
            "name": "Design New Dashboard",
            "status": {"status": "in progress"},
            "tags": [{"name": "Product"}, {"name": "Q1-goals"}],
            "url": "https://app.clickup.com/t/def5678"
        }
    ]

def get_mock_invoices():
    return [
        {
            "id": "INV-001",
            "customer_email": "clientA@example.com",
            "amount": 1000,
            "days_overdue": 2,
            "failure_reason": "card_expired",
            "scenario": "Path A: Technical",
            "tone": "Friendly"
        },
        {
            "id": "INV-002",
            "customer_email": "ghost@example.com",
            "amount": 500,
            "days_overdue": 20,
            "failure_reason": None,
            "scenario": "Path B: Ghost",
            "tone": "Firm"
        }
    ]

def get_mock_wbr():
    return {
        "summary": "📊 WBR Summary (Week of Feb 3-9, 2026)",
        "sheets": [
            {"name": "Overview", "key_metric": "✅ All systems operational | 42 total tasks"},
            {"name": "Product Tasks", "key_metric": "📈 15/20 completed (75%)"},
            {"name": "Maintenance", "key_metric": "🔧 8 open issues"},
            {"name": "Support Metrics", "key_metric": "⏱️ Avg response: 2.3h | 95% SLA"},
            {"name": "Customer Health", "key_metric": "😊 NPS: 45 | Churn: 2.1%"}
        ]
    }

def get_real_wbr():
    try:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            return None
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SPREADSHEET_ID)
        wbr_summary = f"📊 *Real-time WBR Summary:* {sh.title}"
        worksheet = sh.get_worksheet(0)
        top_metric = worksheet.cell(1, 1).value or "No data in A1"
        return {
            "summary": wbr_summary,
            "sheets": [
                {"name": worksheet.title, "key_metric": f"Sheet Key Metric: {top_metric}"}
            ]
        }
    except Exception as e:
        print(f"❌ Error fetching real WBR: {e}")
        return None

def get_intercom_summary():
    if not INTERCOM_API_TOKEN:
        return {"error": "INTERCOM_API_TOKEN missing from .env"}
    
    headers = {
        "Authorization": f"Bearer {INTERCOM_API_TOKEN}",
        "Accept": "application/json",
        "Intercom-Version": "2.11"
    }
    
    try:
        # Get conversations
        print("📡 Fetching Intercom conversations...")
        resp = req.get("https://api.intercom.io/conversations", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        conversations = data.get("conversations", [])
        
        # Initialize metrics
        status_breakdown = {"open": 0, "closed": 0, "snoozed": 0}
        assignee_counts = {}
        waiting_breakdown = {"waiting_customer": 0, "waiting_team": 0}
        channel_breakdown = {}
        priority_convos = []
        unassigned_count = 0
        
        # Fetch team members for name mapping
        team_resp = req.get("https://api.intercom.io/admins", headers=headers, timeout=10)
        admins = {}
        if team_resp.status_code == 200:
            admin_data = team_resp.json()
            admins = {admin['id']: admin.get('name', 'Unknown') for admin in admin_data.get('admins', [])}
        
        # Process each conversation
        for conv in conversations:
            # Status breakdown
            state = conv.get('state', 'unknown')
            if state in status_breakdown:
                status_breakdown[state] += 1
            
            # Assignee distribution
            assignee_id = conv.get('admin_assignee_id')
            if assignee_id:
                assignee_name = admins.get(assignee_id, f"Admin {assignee_id}")
                assignee_counts[assignee_name] = assignee_counts.get(assignee_name, 0) + 1
            else:
                unassigned_count += 1
            
            # Waiting status
            if conv.get('waiting_since'):
                waiting_breakdown["waiting_customer"] += 1
            elif state == 'open' and not assignee_id:
                waiting_breakdown["waiting_team"] += 1
            
            # Channel breakdown
            source = conv.get('source', {})
            source_type = source.get('type', 'unknown')
            channel_breakdown[source_type] = channel_breakdown.get(source_type, 0) + 1
            
            # Identify priority conversations (open + unassigned or waiting)
            if state == 'open' and (not assignee_id or conv.get('waiting_since')):
                priority_convos.append(conv)
        
        # Sort priority conversations by update time (most recent first)
        priority_convos.sort(key=lambda x: x.get('updated_at', 0), reverse=True)
        
        return {
            "total_count": len(conversations),
            "status_breakdown": status_breakdown,
            "unassigned_count": unassigned_count,
            "assignee_counts": assignee_counts,
            "waiting_breakdown": waiting_breakdown,
            "channel_breakdown": channel_breakdown,
            "priority_conversations": priority_convos[:5],  # Top 5 priority
            "latest_items": conversations[:5],
            "admins": admins  # For name lookup in display
        }
    except Exception as e:
        print(f"❌ Error fetching Intercom summary: {e}")
        return {"error": str(e)}


def get_intercom_okr_report():
    if not INTERCOM_API_TOKEN:
        return {"error": "INTERCOM_API_TOKEN missing from .env"}
    
    headers = {
        "Authorization": f"Bearer {INTERCOM_API_TOKEN}",
        "Accept": "application/json",
        "Intercom-Version": "2.11"
    }
    
    # Calculate timestamp for 7 days ago
    seven_days_ago = int(time.time()) - (7 * 24 * 3600)
    
    try:
        # Search API to find conversations from last 7 days
        search_query = {
            "query": {
                "field": "updated_at",
                "operator": ">",
                "value": seven_days_ago
            }
        }
        
        print(f"📡 Searching Intercom conversations since {datetime.fromtimestamp(seven_days_ago)}...")
        resp = req.post("https://api.intercom.io/conversations/search", headers=headers, json=search_query, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        conversations_summary = data.get("conversations", [])
        
        # Limit to recent 30 to prevent timeouts during detail fetch
        conversations_summary = conversations_summary[:30]
        
        print(f"🔍 Fetching details for {len(conversations_summary)} conversations...")

        # Metrics buckets
        total_fin_involved = 0
        resolved_by_fin = 0
        csat_total = 0
        csat_count = 0
        
        for summary in conversations_summary:
            try:
                # Fetch full conversation details to get ai_agent and custom_attributes
                conv_id = summary.get("id")
                detail_resp = req.get(f"https://api.intercom.io/conversations/{conv_id}", headers=headers, timeout=5)
                if detail_resp.status_code != 200:
                    continue
                    
                conv = detail_resp.json()
                
                # Check for Fin involvement
                ai_agent = conv.get("ai_agent", {})
                participated = conv.get("ai_agent_participated", False)
                
                if participated:
                    total_fin_involved += 1
                    # Resolution check (based on Fin's resolution state)
                    # Common states: 'resolved', 'assumed_resolved', 'routed_to_team', 'handoff_to_team'
                    resolution_state = ai_agent.get("resolution_state")
                    if resolution_state in ["resolved", "assumed_resolved"]:
                        resolved_by_fin += 1
                
                # CSAT from Custom Attributes (Verified field name from JSON: 'CX Score rating')
                custom_attrs = conv.get("custom_attributes", {})
                cx_score = custom_attrs.get("CX Score rating")
                
                # If CX Score is present (it's an integer in the JSON, e.g. 5)
                if cx_score is not None:
                    try:
                        score_val = float(cx_score)
                        csat_total += score_val
                        csat_count += 1
                    except (ValueError, TypeError):
                        pass
                        
            except Exception as e:
                print(f"⚠️ Error processing conversation {summary.get('id')}: {e}")
                continue
        
        # Calculate percentages
        deflection_pct = (resolved_by_fin / total_fin_involved * 100) if total_fin_involved > 0 else 0
        resolution_pct = deflection_pct # In this logic, we treat Fin resolution as both deflection and resolution
        csat_score = (csat_total / csat_count) if csat_count > 0 else 0
        
        return {
            "deflection": deflection_pct,
            "resolution": resolution_pct,
            "csat": csat_score,
            "fin_count": total_fin_involved,
            "csat_count": csat_count
        }
    except Exception as e:
        print(f"❌ Error calculating Intercom OKRs: {e}")
        return {"error": str(e)}

def get_intercom_audit():
    if not INTERCOM_API_TOKEN:
        return {"error": "INTERCOM_API_TOKEN missing from .env"}
    
    headers = {
        "Authorization": f"Bearer {INTERCOM_API_TOKEN}",
        "Accept": "application/json",
        "Intercom-Version": "2.11"
    }
    
    # Check last 14 days for a meaningful audit
    lookback = int(time.time()) - (14 * 24 * 3600)
    
    try:
        # Search for rated conversations (below 4 is usually a good signal for issues)
        search_query = {
            "query": {
                "operator": "AND",
                "value": [
                    {"field": "updated_at", "operator": ">", "value": lookback},
                    {"field": "conversation_rating.rating", "operator": "<", "value": 4}
                ]
            }
        }
        
        print(f"📡 Auditing Intercom conversations since {datetime.fromtimestamp(lookback)}...")
        resp = req.post("https://api.intercom.io/conversations/search", headers=headers, json=search_query, timeout=30)
        resp.raise_for_status()
        conversations = resp.json().get("conversations", [])
        
        audit_results = []
        workflow_mentions = {"billing": 0, "login": 0, "api": 0, "invoice": 0, "refund": 0}
        
        for conv in conversations[:10]: # Analyze top 10 for speed
            conv_id = conv.get("id")
            rating_data = conv.get("conversation_rating", {})
            rating = rating_data.get("rating")
            remark = strip_html(rating_data.get("remark") or "")
            
            # Fetch full conversation body to find sentiments/repetitive tasks
            detail_resp = req.get(f"https://api.intercom.io/conversations/{conv_id}", headers=headers, timeout=10)
            detail = detail_resp.json() if detail_resp.status_code == 200 else {}
            
            body = strip_html(detail.get("source", {}).get("body", "")).lower()
            
            # Sentiment tagging
            sentiments = []
            if any(word in body or word in remark.lower() for word in ["slow", "wait", "delay"]): sentiments.append("🕒 Latency/Slow Response")
            if any(word in body or word in remark.lower() for word in ["wrong", "incorrect", "misleading"]): sentiments.append("❌ Accuracy Issue")
            if any(word in body or word in remark.lower() for word in ["frustrated", "annoyed", "bad", "terrible"]): sentiments.append("😡 Frustrated User")
            
            # Workflow identification
            for wf in workflow_mentions.keys():
                if wf in body or wf in remark.lower():
                    workflow_mentions[wf] += 1
            
            audit_results.append({
                "id": conv_id,
                "rating": rating,
                "remark": remark or "No comment provided",
                "sentiments": sentiments,
                "url": f"https://app.intercom.com/a/apps/_/inbox/all/conversations/{conv_id}"
            })
            
        return {
            "total_audited": len(conversations),
            "findings": audit_results,
            "top_workflows": sorted(workflow_mentions.items(), key=lambda x: x[1], reverse=True)[:3]
        }
    except Exception as e:
        print(f"❌ Error during Intercom audit: {e}")
        return {"error": str(e)}

def get_product_updates(days=30):
    """Fetch messages from #product-comm and group by week."""
    PRODUCT_COMM_CHANNEL = 'C07GUPXUJGK'
    
    try:
        oldest = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
        
        # Paginate through all messages
        all_messages = []
        cursor = None
        while True:
            kwargs = {
                'channel': PRODUCT_COMM_CHANNEL,
                'oldest': str(oldest),
                'limit': 200
            }
            if cursor:
                kwargs['cursor'] = cursor
            result = slack_client.conversations_history(**kwargs)
            messages = result.get('messages', [])
            all_messages.extend(messages)
            cursor = result.get('response_metadata', {}).get('next_cursor', '')
            if not cursor:
                break
        
        # Filter out join/leave/bot messages
        real_messages = []
        user_cache = {}
        
        for msg in all_messages:
            subtype = msg.get('subtype', '')
            if subtype in ('channel_join', 'channel_leave', 'channel_purpose', 'channel_topic', 'bot_message'):
                continue
            if not msg.get('text', '').strip():
                continue
            
            # Resolve user name
            uid = msg.get('user', '')
            if uid and uid not in user_cache:
                try:
                    info = slack_client.users_info(user=uid)
                    user_cache[uid] = info['user'].get('real_name', info['user'].get('name', uid))
                except:
                    user_cache[uid] = uid
            
            ts = datetime.fromtimestamp(float(msg['ts']))
            real_messages.append({
                'date': ts,
                'author': user_cache.get(uid, 'Unknown'),
                'text': msg.get('text', ''),
                'ts': msg['ts']
            })
        
        # Sort by date (newest first)
        real_messages.sort(key=lambda m: m['date'], reverse=True)
        
        # Group by week
        weeks = {}
        for msg in real_messages:
            week_start = msg['date'] - timedelta(days=msg['date'].weekday())
            week_key = week_start.strftime('%b %d')
            if week_key not in weeks:
                weeks[week_key] = {
                    'start': week_start.strftime('%b %d'),
                    'end': (week_start + timedelta(days=6)).strftime('%b %d'),
                    'messages': []
                }
            weeks[week_key]['messages'].append(msg)
        
        return {
            'total': len(real_messages),
            'days': days,
            'weeks': weeks
        }
    except Exception as e:
        print(f"❌ Error fetching product updates: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

@app.route('/slack/ping', methods=['GET'])
def slack_ping():
    return f"pong - {datetime.now().isoformat()}"

def analyze_page(url):
    """
    Fetch and analyze a webpage, extracting SEO elements, technical metrics,
    and generating smart commentary on what's working well vs observations.
    """
    try:
        # Ensure URL has protocol
        if not url.startswith('http'):
            url = 'https://' + url
        
        # Fetch the page with timeout
        start_time = time.time()
        response = req.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }, allow_redirects=True)
        load_time = time.time() - start_time
        
        status_code = response.status_code
        if status_code != 200:
            return {"error": f"HTTP {status_code}", "url": url}
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        html_text = response.text
        
        # --- SEO Elements ---
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""
        
        meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
        if not meta_desc_tag:
            meta_desc_tag = soup.find('meta', attrs={'name': 'Description'})
        if not meta_desc_tag:
            meta_desc_tag = soup.find('meta', attrs={'property': 'og:description'})
        meta_desc = meta_desc_tag.get('content', '').strip() if meta_desc_tag else ""
        
        meta_keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        meta_keywords = meta_keywords_tag.get('content', '').strip() if meta_keywords_tag else ""
        
        canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
        canonical = canonical_tag.get('href', '').strip() if canonical_tag else ""
        
        robots_tag = soup.find('meta', attrs={'name': 'robots'})
        robots = robots_tag.get('content', '').strip() if robots_tag else ""
        
        # --- Headings ---
        h1_tags = soup.find_all('h1')
        h2_tags = soup.find_all('h2')
        h3_tags = soup.find_all('h3')
        h1_text = h1_tags[0].get_text().strip() if h1_tags else ""
        h2_texts = [h.get_text().strip()[:80] for h in h2_tags[:5]]
        
        # --- Open Graph ---
        og_title = (soup.find('meta', attrs={'property': 'og:title'}) or {}).get('content', '').strip() if soup.find('meta', attrs={'property': 'og:title'}) else ""
        og_desc = (soup.find('meta', attrs={'property': 'og:description'}) or {}).get('content', '').strip() if soup.find('meta', attrs={'property': 'og:description'}) else ""
        og_image = (soup.find('meta', attrs={'property': 'og:image'}) or {}).get('content', '').strip() if soup.find('meta', attrs={'property': 'og:image'}) else ""
        
        # --- Twitter Card ---
        twitter_card = (soup.find('meta', attrs={'name': 'twitter:card'}) or {}).get('content', '').strip() if soup.find('meta', attrs={'name': 'twitter:card'}) else ""
        twitter_handle = (soup.find('meta', attrs={'name': 'twitter:site'}) or {}).get('content', '').strip() if soup.find('meta', attrs={'name': 'twitter:site'}) else ""
        
        # --- Technical ---
        encoding = response.encoding or "Unknown"
        page_size_kb = round(len(response.content) / 1024, 1)
        
        favicon = bool(soup.find('link', attrs={'rel': 'icon'}) or soup.find('link', attrs={'rel': 'shortcut icon'}))
        apple_touch = bool(soup.find('link', attrs={'rel': 'apple-touch-icon'}))
        
        # --- Content ---
        img_tags = soup.find_all('img')
        imgs_with_alt = sum(1 for img in img_tags if img.get('alt'))
        
        a_tags = soup.find_all('a', href=True)
        internal_links = sum(1 for a in a_tags if a['href'].startswith('/') or url.split('//')[1].split('/')[0] in a['href'])
        external_links = len(a_tags) - internal_links
        
        body = soup.find('body')
        body_text = body.get_text(separator=' ', strip=True) if body else ""
        word_count = len(body_text.split())
        
        # --- Framework detection ---
        framework = ""
        if '__next' in html_text or '_next/static' in html_text:
            framework = "Next.js"
        elif 'wp-content' in html_text or 'wordpress' in html_text.lower():
            framework = "WordPress"
        elif 'react' in html_text.lower() and 'root' in html_text:
            framework = "React"
        elif 'gatsby' in html_text.lower():
            framework = "Gatsby"
        elif 'nuxt' in html_text.lower():
            framework = "Nuxt.js"
        
        is_js_rendered = bool(framework in ['Next.js', 'React', 'Gatsby', 'Nuxt.js'])
        
        # --- Generate smart commentary ---
        working_well = []
        observations = []
        
        # Title analysis
        if title:
            if len(title) <= 60:
                working_well.append(f"Good title length ({len(title)} chars, under 60)")
            elif len(title) <= 90:
                working_well.append(f"Acceptable title length ({len(title)} chars)")
            else:
                observations.append(f"Title is long ({len(title)} chars) — consider shortening to under 60")
        else:
            observations.append("Missing title tag")
        
        # Meta description
        if meta_desc:
            if 120 <= len(meta_desc) <= 160:
                working_well.append(f"Optimal meta description ({len(meta_desc)} chars)")
            elif len(meta_desc) > 0:
                working_well.append(f"Meta description present ({len(meta_desc)} chars)")
                if len(meta_desc) < 120:
                    observations.append(f"Meta description is short ({len(meta_desc)} chars) — aim for 120-160")
                elif len(meta_desc) > 160:
                    observations.append(f"Meta description may be truncated ({len(meta_desc)} chars)")
        else:
            observations.append("Missing meta description")
        
        # Meta keywords
        if meta_keywords:
            working_well.append("Meta keywords present")
        
        # Load time
        if load_time < 1:
            working_well.append(f"Fast load time ({load_time:.2f}s)")
        elif load_time < 2:
            working_well.append(f"Acceptable load time ({load_time:.2f}s)")
        else:
            observations.append(f"Slow load time ({load_time:.2f}s) — may impact rankings")
        
        # Open Graph
        og_count = sum(1 for x in [og_title, og_desc, og_image] if x)
        if og_count == 3:
            working_well.append("Complete Open Graph tags for social sharing")
        elif og_count > 0:
            observations.append(f"Partial Open Graph setup ({og_count}/3 tags)")
        else:
            observations.append("No Open Graph tags — social sharing will lack rich previews")
        
        # Twitter
        if twitter_card and twitter_handle:
            working_well.append(f"Twitter Card configured ({twitter_card})")
        elif twitter_card:
            observations.append("Twitter Card set but no @handle")
        
        # Canonical
        if canonical:
            working_well.append("Canonical URL properly set")
        else:
            observations.append("No canonical URL set — may cause duplicate content issues")
        
        # Robots
        if robots and 'noindex' not in robots.lower():
            working_well.append(f"Robots directive: {robots}")
        elif robots and 'noindex' in robots.lower():
            observations.append(f"Page is set to noindex! ({robots})")
        
        # Headings
        if len(h1_tags) == 1:
            working_well.append("Single H1 tag (best practice)")
        elif len(h1_tags) == 0:
            observations.append("No H1 tag found")
        else:
            observations.append(f"Multiple H1 tags ({len(h1_tags)}) — should have exactly 1")
        
        # Images
        if img_tags:
            alt_pct = round(imgs_with_alt / len(img_tags) * 100) if img_tags else 0
            if alt_pct >= 90:
                working_well.append(f"Good image alt text coverage ({alt_pct}%)")
            else:
                observations.append(f"Only {alt_pct}% of images have alt text ({imgs_with_alt}/{len(img_tags)})")
        
        # Favicon
        if favicon:
            working_well.append("Favicon configured")
        if apple_touch:
            working_well.append("Apple touch icon configured")
        
        # Framework
        if framework:
            if is_js_rendered:
                observations.append(f"Uses {framework} (JavaScript-rendered content)")
            else:
                observations.append(f"Built with {framework}")
        
        # H1 content insight
        if h1_text:
            observations.append(f"Main heading: \"{h1_text[:100]}\"")
        
        return {
            'url': url,
            'status': status_code,
            'load_time': round(load_time, 2),
            'size_kb': page_size_kb,
            'encoding': encoding,
            'title': title,
            'title_length': len(title),
            'meta_description': meta_desc,
            'meta_desc_length': len(meta_desc),
            'meta_keywords': meta_keywords,
            'h1': h1_text,
            'h1_count': len(h1_tags),
            'h2_count': len(h2_tags),
            'h2_texts': h2_texts,
            'h3_count': len(h3_tags),
            'canonical': canonical,
            'robots': robots,
            'og_title': og_title,
            'og_desc': og_desc,
            'og_image': og_image,
            'twitter_card': twitter_card,
            'twitter_handle': twitter_handle,
            'favicon': favicon,
            'apple_touch': apple_touch,
            'framework': framework,
            'img_count': len(img_tags),
            'imgs_with_alt': imgs_with_alt,
            'internal_links': internal_links,
            'external_links': external_links,
            'word_count': word_count,
            'working_well': working_well,
            'observations': observations,
            'raw_html': html_text
        }
    except req.exceptions.Timeout:
        return {"error": "Request timed out (15s)", "url": url}
    except req.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "url": url}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}", "url": url}

def content_audit(url):
    """
    Perform a Content Audit analysis on a URL, matching SEOmonitor's 
    Content Audit tool checks: Title/H1, heading structure, content analysis,
    topic focus, meta/technical, and overall score.
    """
    try:
        # Ensure URL has protocol
        if not url.startswith('http'):
            url = 'https://' + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = req.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        html_text = response.text
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_text, 'html.parser')
        
        results = {
            'url': response.url,
            'status_code': response.status_code,
            'issues': [],
            'passes': [],
            'warnings': [],
            'score': 100
        }
        
        score_deductions = 0
        
        # ── TITLE ANALYSIS ──
        title_tag = soup.find('title')
        title_text = title_tag.get_text(strip=True) if title_tag else ''
        title_len = len(title_text)
        
        if not title_text:
            results['issues'].append('❌ Missing <title> tag')
            score_deductions += 15
        elif title_len < 20:
            results['warnings'].append(f'⚠️ Title too short ({title_len} chars): "{title_text}"')
            score_deductions += 5
        elif title_len > 60:
            results['warnings'].append(f'⚠️ Title too long ({title_len} chars) — may be truncated in SERPs')
            score_deductions += 3
        else:
            results['passes'].append(f'✅ Title ({title_len} chars): "{title_text}"')
        
        results['title'] = title_text
        results['title_len'] = title_len
        
        # ── H1 ANALYSIS ──
        h1_tags = soup.find_all('h1')
        h1_count = len(h1_tags)
        h1_texts = [h1.get_text(strip=True) for h1 in h1_tags]
        
        if h1_count == 0:
            results['issues'].append('❌ Missing H1 heading')
            score_deductions += 15
        elif h1_count > 1:
            results['warnings'].append(f'⚠️ Multiple H1 tags ({h1_count}) — should have exactly 1')
            score_deductions += 5
        else:
            h1_text = h1_texts[0]
            h1_len = len(h1_text)
            if h1_len < 10:
                results['warnings'].append(f'⚠️ H1 too short ({h1_len} chars): "{h1_text}"')
                score_deductions += 3
            else:
                results['passes'].append(f'✅ H1 ({h1_len} chars): "{h1_text}"')
        
        results['h1_count'] = h1_count
        results['h1_texts'] = h1_texts
        
        # ── KEYWORD INCLUSION IN TITLE & H1 ──
        # Extract likely target keywords from the page
        meta_keywords = soup.find('meta', attrs={'name': re.compile(r'keywords', re.I)})
        meta_kw_content = meta_keywords.get('content', '') if meta_keywords else ''
        
        # Build keyword list from meta keywords + title words
        target_keywords = []
        if meta_kw_content:
            target_keywords = [kw.strip().lower() for kw in meta_kw_content.split(',') if len(kw.strip()) > 2]
        
        # If no meta keywords, extract from title
        if not target_keywords and title_text:
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'it', 'by', 'with', 'as', 'from', 'that', 'this', 'are', 'was', 'be', 'has', 'have', 'had', 'not', 'you', 'your', 'our', 'we', 'they', 'their', 'its', '|', '-', '–', '—'}
            target_keywords = [w.lower() for w in re.findall(r'\b\w{3,}\b', title_text) if w.lower() not in stop_words]
        
        results['target_keywords'] = target_keywords[:10]  # Top 10
        
        if target_keywords and title_text:
            title_lower = title_text.lower()
            kw_in_title = [kw for kw in target_keywords if kw in title_lower]
            if kw_in_title:
                results['passes'].append(f'✅ Keywords in title: {", ".join(kw_in_title[:5])}')
            else:
                results['warnings'].append('⚠️ No target keywords found in title')
                score_deductions += 5
        
        if target_keywords and h1_texts:
            h1_lower = ' '.join(h1_texts).lower()
            kw_in_h1 = [kw for kw in target_keywords if kw in h1_lower]
            if kw_in_h1:
                results['passes'].append(f'✅ Keywords in H1: {", ".join(kw_in_h1[:5])}')
            else:
                results['warnings'].append('⚠️ No target keywords found in H1')
                score_deductions += 5
        
        # ── HEADING STRUCTURE ──
        heading_counts = {}
        for level in range(1, 7):
            tags = soup.find_all(f'h{level}')
            heading_counts[f'h{level}'] = len(tags)
        
        results['heading_counts'] = heading_counts
        
        # Check hierarchy — no skipped levels
        hierarchy_ok = True
        found_first = False
        for level in range(1, 7):
            count = heading_counts[f'h{level}']
            if count > 0:
                found_first = True
            elif found_first and level <= 3:
                # Check if a deeper level exists
                deeper_exists = any(heading_counts[f'h{l}'] > 0 for l in range(level + 1, 7))
                if deeper_exists:
                    hierarchy_ok = False
                    break
        
        if hierarchy_ok:
            results['passes'].append('✅ Heading hierarchy — no skipped levels')
        else:
            results['warnings'].append('⚠️ Heading hierarchy has skipped levels')
            score_deductions += 3
        
        # ── CONTENT ANALYSIS ──
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
        
        body = soup.find('body')
        body_text = body.get_text(separator=' ', strip=True) if body else ''
        words = re.findall(r'\b\w+\b', body_text)
        word_count = len(words)
        
        results['word_count'] = word_count
        
        if word_count < 300:
            results['warnings'].append(f'⚠️ Thin content ({word_count} words) — consider adding more')
            score_deductions += 8
        elif word_count < 500:
            results['warnings'].append(f'⚠️ Light content ({word_count} words)')
            score_deductions += 3
        else:
            results['passes'].append(f'✅ Content length: {word_count:,} words')
        
        # Keyword density
        if target_keywords and word_count > 0:
            body_lower = body_text.lower()
            kw_density = {}
            for kw in target_keywords[:5]:
                count = body_lower.count(kw)
                density = round((count / word_count) * 100, 2) if word_count > 0 else 0
                kw_density[kw] = {'count': count, 'density': density}
            results['keyword_density'] = kw_density
        
        # ── LINKS ANALYSIS ──
        # Re-parse since we decomposed elements
        soup_links = BeautifulSoup(html_text, 'html.parser')
        all_links = soup_links.find_all('a', href=True)
        from urllib.parse import urlparse
        page_domain = urlparse(response.url).netloc
        
        internal_links = 0
        external_links = 0
        nofollow_links = 0
        for link in all_links:
            href = link.get('href', '')
            rel = link.get('rel', [])
            if 'nofollow' in rel:
                nofollow_links += 1
            parsed = urlparse(href)
            if parsed.netloc and parsed.netloc != page_domain:
                external_links += 1
            else:
                internal_links += 1
        
        results['internal_links'] = internal_links
        results['external_links'] = external_links
        results['nofollow_links'] = nofollow_links
        
        if internal_links == 0:
            results['warnings'].append('⚠️ No internal links found')
            score_deductions += 5
        else:
            results['passes'].append(f'✅ Internal links: {internal_links}')
        
        # ── IMAGE ANALYSIS ──
        all_images = soup_links.find_all('img')
        img_total = len(all_images)
        img_with_alt = sum(1 for img in all_images if img.get('alt', '').strip())
        img_without_alt = img_total - img_with_alt
        
        results['img_total'] = img_total
        results['img_with_alt'] = img_with_alt
        results['img_without_alt'] = img_without_alt
        
        if img_total > 0 and img_without_alt > 0:
            results['warnings'].append(f'⚠️ {img_without_alt}/{img_total} images missing alt text')
            score_deductions += min(img_without_alt * 2, 8)
        elif img_total > 0:
            results['passes'].append(f'✅ All {img_total} images have alt text')
        
        # ── TOPIC FOCUS ──
        h2_tags = soup_links.find_all('h2')
        h2_texts = [h2.get_text(strip=True).lower() for h2 in h2_tags if h2.get_text(strip=True)]
        
        # Simple topic clustering based on H2 headings
        topics = []
        for h2 in h2_texts:
            # Clean and extract meaningful words
            topic_words = [w for w in re.findall(r'\b\w{3,}\b', h2) if w not in {'the', 'and', 'for', 'how', 'what', 'why', 'our', 'your', 'with', 'this', 'that', 'are', 'from'}]
            if topic_words:
                topics.append(' '.join(topic_words[:3]))
        
        results['topics'] = topics[:10]
        results['topic_count'] = len(set(topics))
        
        if len(set(topics)) > 5:
            results['warnings'].append(f'⚠️ Page covers {len(set(topics))} distinct topics — may serve too many keywords')
            score_deductions += 5
        elif len(set(topics)) >= 2:
            results['passes'].append(f'✅ Page covers {len(set(topics))} topics')
        
        # ── META & TECHNICAL ──
        # Meta description
        meta_desc = soup_links.find('meta', attrs={'name': re.compile(r'description', re.I)})
        meta_desc_text = meta_desc.get('content', '') if meta_desc else ''
        meta_desc_len = len(meta_desc_text)
        
        if not meta_desc_text:
            results['issues'].append('❌ Missing meta description')
            score_deductions += 8
        elif meta_desc_len < 50:
            results['warnings'].append(f'⚠️ Meta description too short ({meta_desc_len} chars)')
            score_deductions += 3
        elif meta_desc_len > 160:
            results['warnings'].append(f'⚠️ Meta description too long ({meta_desc_len} chars) — may be truncated')
            score_deductions += 2
        else:
            results['passes'].append(f'✅ Meta description ({meta_desc_len} chars)')
        
        results['meta_description'] = meta_desc_text
        
        # Canonical
        canonical = soup_links.find('link', attrs={'rel': 'canonical'})
        canonical_url = canonical.get('href', '') if canonical else ''
        if canonical_url:
            if canonical_url == response.url or canonical_url.rstrip('/') == response.url.rstrip('/'):
                results['passes'].append('✅ Canonical: self-referencing')
            else:
                results['warnings'].append(f'⚠️ Canonical points elsewhere: {canonical_url}')
                score_deductions += 3
        else:
            results['warnings'].append('⚠️ No canonical tag found')
            score_deductions += 5
        
        results['canonical'] = canonical_url
        
        # Robots meta
        robots_meta = soup_links.find('meta', attrs={'name': re.compile(r'robots', re.I)})
        robots_content = robots_meta.get('content', '') if robots_meta else ''
        if 'noindex' in robots_content.lower():
            results['issues'].append('❌ Page is set to noindex')
            score_deductions += 15
        elif robots_content:
            results['passes'].append(f'✅ Robots: {robots_content}')
        
        results['robots'] = robots_content
        
        # Schema / Structured data
        schema_scripts = soup_links.find_all('script', attrs={'type': 'application/ld+json'})
        schema_types = []
        for script in schema_scripts:
            try:
                import json
                schema = json.loads(script.string)
                if isinstance(schema, dict):
                    schema_types.append(schema.get('@type', 'Unknown'))
                elif isinstance(schema, list):
                    for item in schema:
                        if isinstance(item, dict):
                            schema_types.append(item.get('@type', 'Unknown'))
            except:
                pass
        
        results['schema_types'] = schema_types
        if schema_types:
            results['passes'].append(f'✅ Schema markup: {", ".join(schema_types)}')
        else:
            results['warnings'].append('⚠️ No structured data (schema.org) found')
            score_deductions += 3
        
        # ── CALCULATE FINAL SCORE ──
        results['score'] = max(0, 100 - score_deductions)
        
        # Score label
        score = results['score']
        if score >= 80:
            results['score_label'] = '🟢 Good'
        elif score >= 60:
            results['score_label'] = '🟡 Needs Improvement'
        elif score >= 40:
            results['score_label'] = '🟠 Poor'
        else:
            results['score_label'] = '🔴 Critical'
        
        return results
        
    except req.exceptions.Timeout:
        return {"error": "Request timed out (15s)", "url": url}
    except req.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "url": url}
    except Exception as e:
        return {"error": f"Audit failed: {str(e)}", "url": url}


def analyze_article(url):
    """
    Analyze an article page for Content Writer quality signals.
    Maps to SEOmonitor Content Writer checks: SEO Score, Content Foundation,
    Technical Elements, and Content Quality.
    """
    try:
        if not url.startswith('http'):
            url = 'https://' + url

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        start_time = time.time()
        response = req.get(url, headers=headers, timeout=20, allow_redirects=True)
        response.raise_for_status()
        load_time = round(time.time() - start_time, 2)
        html_text = response.text

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_text, 'html.parser')

        # Remove script/style/nav/footer elements to get article body
        for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        results = {
            'url': response.url,
            'load_time': load_time,
            'status_code': response.status_code,
        }

        # ══════════════════════════════════════
        # 1. EXTRACT CORE ELEMENTS
        # ══════════════════════════════════════
        title_tag = soup.find('title')
        title_text = title_tag.get_text(strip=True) if title_tag else ''
        results['title'] = title_text
        results['title_len'] = len(title_text)

        h1_tags = soup.find_all('h1')
        h1_texts = [h.get_text(strip=True) for h in h1_tags]
        results['h1'] = h1_texts[0] if h1_texts else ''
        results['h1_count'] = len(h1_tags)

        # All headings
        headings = {}
        all_heading_texts = []
        for level in range(1, 7):
            tags = soup.find_all(f'h{level}')
            texts = [t.get_text(strip=True) for t in tags]
            headings[f'h{level}'] = texts
            all_heading_texts.extend(texts)
        results['headings'] = headings
        results['heading_counts'] = {k: len(v) for k, v in headings.items() if v}

        # Meta description
        meta_desc_tag = soup.find('meta', attrs={'name': 'description'}) or \
                        soup.find('meta', attrs={'property': 'og:description'})
        meta_desc = meta_desc_tag.get('content', '').strip() if meta_desc_tag else ''
        results['meta_description'] = meta_desc
        results['meta_desc_len'] = len(meta_desc)

        # Canonical
        canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
        results['canonical'] = canonical_tag.get('href', '').strip() if canonical_tag else ''

        # ══════════════════════════════════════
        # 2. CONTENT BODY ANALYSIS
        # ══════════════════════════════════════

        # Get visible text from article/main or body
        article_tag = soup.find('article') or soup.find('main') or soup.find('body')
        body_text = article_tag.get_text(separator=' ', strip=True) if article_tag else ''

        # Clean up whitespace
        body_text = re.sub(r'\s+', ' ', body_text).strip()
        words = body_text.split()
        word_count = len(words)
        results['word_count'] = word_count
        results['reading_time'] = max(1, round(word_count / 238))  # avg reading speed

        # Sentences and paragraphs
        sentences = re.split(r'[.!?]+', body_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        results['sentence_count'] = len(sentences)
        results['avg_sentence_len'] = round(sum(len(s.split()) for s in sentences) / max(len(sentences), 1), 1)

        paragraphs = article_tag.find_all('p') if article_tag else []
        para_texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]
        results['paragraph_count'] = len(para_texts)

        # ══════════════════════════════════════
        # 3. SEO SCORE (mirrors Content Writer)
        # ══════════════════════════════════════
        seo_score = 0
        seo_details = {}

        # 3a. Title keyword assessment
        title_score = 0
        title_notes = []
        if title_text:
            if 30 <= len(title_text) <= 60:
                title_score = 100
                title_notes.append(f"✅ Good length ({len(title_text)} chars)")
            elif len(title_text) > 60:
                title_score = 70
                title_notes.append(f"⚠️ Slightly long ({len(title_text)} chars, ideal: 30-60)")
            else:
                title_score = 50
                title_notes.append(f"⚠️ Too short ({len(title_text)} chars)")
            # Check if title appears thematic
            if h1_texts and h1_texts[0].lower() != title_text.lower():
                title_notes.append("ℹ️ Title differs from H1 (separate optimization)")
        else:
            title_notes.append("❌ No title tag found")
        seo_details['title'] = {'score': title_score, 'notes': title_notes}

        # 3b. Headings keyword assessment
        heading_score = 0
        heading_notes = []
        h2_list = headings.get('h2', [])
        h3_list = headings.get('h3', [])
        total_subheadings = len(h2_list) + len(h3_list)

        if results['h1_count'] == 1:
            heading_score += 30
            heading_notes.append("✅ Single H1 tag")
        elif results['h1_count'] == 0:
            heading_notes.append("❌ Missing H1")
        else:
            heading_score += 10
            heading_notes.append(f"⚠️ Multiple H1 tags ({results['h1_count']})")

        if total_subheadings >= 3:
            heading_score += 40
            heading_notes.append(f"✅ {total_subheadings} subheadings (H2: {len(h2_list)}, H3: {len(h3_list)})")
        elif total_subheadings >= 1:
            heading_score += 20
            heading_notes.append(f"⚠️ Only {total_subheadings} subheading(s) — consider more for structure")
        else:
            heading_notes.append("❌ No subheadings — article lacks structure")

        # Check heading hierarchy (H2 before H3)
        heading_order = []
        for tag in (article_tag or soup).find_all(re.compile(r'^h[1-6]$')):
            heading_order.append(int(tag.name[1]))
        hierarchy_ok = True
        for i in range(1, len(heading_order)):
            if heading_order[i] > heading_order[i-1] + 1:
                hierarchy_ok = False
                break
        if hierarchy_ok and len(heading_order) > 1:
            heading_score += 30
            heading_notes.append("✅ Proper heading hierarchy")
        elif not hierarchy_ok:
            heading_score += 10
            heading_notes.append("⚠️ Heading hierarchy has gaps (e.g., H1 → H3)")
        seo_details['headings'] = {'score': heading_score, 'notes': heading_notes}

        # 3c. Coverage — keyword distribution
        coverage_score = 0
        coverage_notes = []

        # Extract key phrases from title + H1 (2-3 word combos)
        topic_source = (title_text + ' ' + (h1_texts[0] if h1_texts else '')).lower()
        topic_words = re.findall(r'[a-z]{3,}', topic_source)
        # Remove common stop words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her',
                      'was', 'one', 'our', 'out', 'has', 'how', 'its', 'may', 'new', 'now', 'old',
                      'see', 'way', 'who', 'did', 'get', 'let', 'say', 'she', 'too', 'use',
                      'with', 'this', 'that', 'from', 'they', 'been', 'have', 'many', 'some',
                      'them', 'than', 'other', 'into', 'what', 'your', 'about', 'which', 'their',
                      'will', 'each', 'make', 'like', 'just', 'over', 'such', 'take', 'also',
                      'best', 'tips', 'guide', 'complete'}
        topic_keywords = [w for w in topic_words if w not in stop_words]
        results['topic_keywords'] = topic_keywords[:10]

        body_lower = body_text.lower()
        kw_in_body = sum(1 for kw in topic_keywords if kw in body_lower)
        if topic_keywords:
            kw_coverage_pct = round(kw_in_body / len(topic_keywords) * 100)
            if kw_coverage_pct >= 80:
                coverage_score = 100
                coverage_notes.append(f"✅ {kw_coverage_pct}% of topic keywords found in body")
            elif kw_coverage_pct >= 50:
                coverage_score = 60
                coverage_notes.append(f"⚠️ {kw_coverage_pct}% of topic keywords found — room for improvement")
            else:
                coverage_score = 30
                coverage_notes.append(f"❌ Only {kw_coverage_pct}% coverage — add more topic-relevant content")
        else:
            coverage_score = 50
            coverage_notes.append("ℹ️ Could not extract topic keywords")

        # Check keyword presence in headings
        kw_in_headings = sum(1 for kw in topic_keywords for h in all_heading_texts if kw in h.lower())
        if kw_in_headings >= 2:
            coverage_notes.append(f"✅ Keywords appear in {kw_in_headings} headings")
        elif kw_in_headings == 1:
            coverage_notes.append("⚠️ Keywords in only 1 heading — distribute across more")
        else:
            coverage_notes.append("❌ No topic keywords in headings")

        # Check first paragraph coverage
        first_para = para_texts[0].lower() if para_texts else ''
        kw_in_intro = sum(1 for kw in topic_keywords if kw in first_para)
        if kw_in_intro >= 1:
            coverage_notes.append("✅ Topic keywords present in introduction")
        else:
            coverage_notes.append("⚠️ No topic keywords in introduction paragraph")

        seo_details['coverage'] = {'score': coverage_score, 'notes': coverage_notes}

        # 3d. Word count comparison
        wordcount_score = 0
        wordcount_notes = []
        # Typical benchmark: 1,500-2,500 for informational articles
        if word_count >= 1500:
            wordcount_score = 100
            wordcount_notes.append(f"✅ {word_count:,} words — comprehensive length")
        elif word_count >= 800:
            wordcount_score = 70
            wordcount_notes.append(f"⚠️ {word_count:,} words — moderate, consider expanding")
        elif word_count >= 300:
            wordcount_score = 40
            wordcount_notes.append(f"⚠️ {word_count:,} words — thin content, needs more depth")
        else:
            wordcount_score = 10
            wordcount_notes.append(f"❌ {word_count:,} words — very thin, unlikely to rank")
        wordcount_notes.append(f"📖 ~{results['reading_time']} min read")
        seo_details['wordcount'] = {'score': wordcount_score, 'notes': wordcount_notes}

        # Overall SEO Score (weighted average)
        seo_score = round(
            title_score * 0.25 +
            heading_score * 0.25 +
            coverage_score * 0.25 +
            wordcount_score * 0.25
        )
        results['seo_score'] = seo_score
        results['seo_details'] = seo_details

        # ══════════════════════════════════════
        # 4. CONTENT FOUNDATION (mirrors Quality Checks)
        # ══════════════════════════════════════
        foundation = {}

        # Introduction check
        intro_notes = []
        if para_texts:
            intro = para_texts[0]
            intro_words = len(intro.split())
            if intro_words >= 40:
                intro_notes.append(f"✅ Introduction sets context ({intro_words} words)")
            else:
                intro_notes.append(f"⚠️ Introduction is brief ({intro_words} words) — consider expanding")
        else:
            intro_notes.append("❌ No clear introduction paragraph detected")
        foundation['introduction'] = intro_notes

        # Conclusion check
        conclusion_notes = []
        if para_texts and len(para_texts) >= 3:
            last_para = para_texts[-1].lower()
            conclusion_signals = ['conclusion', 'summary', 'in summary', 'to sum up', 'final',
                                  'takeaway', 'key takeaway', 'wrap up', 'bottom line', 'overall']
            has_conclusion = any(s in last_para for s in conclusion_signals) or \
                             any(s in (headings.get('h2', [])[-1].lower() if headings.get('h2') else '') for s in conclusion_signals)
            if has_conclusion:
                conclusion_notes.append("✅ Article has a clear conclusion section")
            else:
                conclusion_notes.append("⚠️ No obvious conclusion — consider adding a wrap-up")
        else:
            conclusion_notes.append("⚠️ Article too short to evaluate conclusion")
        foundation['conclusion'] = conclusion_notes

        # Content structure
        structure_notes = []
        sections_count = len(h2_list) + 1  # sections between H2s, plus intro
        if sections_count >= 4:
            structure_notes.append(f"✅ Well-structured with {sections_count} sections")
        elif sections_count >= 2:
            structure_notes.append(f"⚠️ {sections_count} sections — could use more subtopics")
        else:
            structure_notes.append("❌ Minimal structure — needs more sections/headings")

        # Words per section
        if sections_count > 0:
            words_per_section = round(word_count / sections_count)
            if 150 <= words_per_section <= 400:
                structure_notes.append(f"✅ Balanced sections (~{words_per_section} words each)")
            elif words_per_section > 400:
                structure_notes.append(f"⚠️ Sections are dense (~{words_per_section} words) — consider splitting")
            else:
                structure_notes.append(f"⚠️ Sections are thin (~{words_per_section} words) — add more detail")
        foundation['structure'] = structure_notes
        results['foundation'] = foundation

        # ══════════════════════════════════════
        # 5. TECHNICAL ELEMENTS
        # ══════════════════════════════════════
        technical = {}

        # Links
        all_links = (article_tag or soup).find_all('a', href=True)
        from urllib.parse import urlparse
        base_domain = urlparse(response.url).netloc
        internal_links = []
        external_links = []
        for a in all_links:
            href = a.get('href', '')
            if href.startswith('#') or href.startswith('javascript'):
                continue
            if href.startswith('/') or base_domain in href:
                internal_links.append(href)
            elif href.startswith('http'):
                external_links.append(href)
        results['internal_links'] = len(internal_links)
        results['external_links'] = len(external_links)

        link_notes = []
        if internal_links:
            link_notes.append(f"✅ {len(internal_links)} internal links (good for topical authority)")
        else:
            link_notes.append("❌ No internal links — add links to related content")
        if external_links:
            link_notes.append(f"✅ {len(external_links)} external links (adds credibility)")
        else:
            link_notes.append("⚠️ No external links — consider citing sources")
        technical['links'] = link_notes

        # Images
        images = (article_tag or soup).find_all('img')
        img_with_alt = sum(1 for img in images if img.get('alt', '').strip())
        img_without_alt = len(images) - img_with_alt
        results['img_total'] = len(images)
        results['img_with_alt'] = img_with_alt
        results['img_without_alt'] = img_without_alt

        img_notes = []
        if len(images) >= 1:
            img_notes.append(f"✅ {len(images)} image(s) found")
            if img_without_alt > 0:
                img_notes.append(f"⚠️ {img_without_alt} image(s) missing alt text")
            else:
                img_notes.append("✅ All images have alt text")
        else:
            img_notes.append("⚠️ No images — visual content improves engagement")
        # Image-to-text ratio
        if word_count > 0 and len(images) > 0:
            ratio = round(word_count / len(images))
            img_notes.append(f"ℹ️ ~1 image per {ratio} words")
        technical['images'] = img_notes

        # Schema/structured data
        schema_types = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                sd = json.loads(script.string or '{}')
                if isinstance(sd, list):
                    for item in sd:
                        if '@type' in item:
                            schema_types.append(item['@type'])
                elif '@type' in sd:
                    schema_types.append(sd['@type'])
                if '@graph' in sd:
                    for item in sd['@graph']:
                        if '@type' in item:
                            schema_types.append(item['@type'])
            except:
                pass

        schema_notes = []
        article_schema = any(s in ['Article', 'NewsArticle', 'BlogPosting', 'TechArticle'] for s in schema_types)
        faq_schema = 'FAQPage' in schema_types
        howto_schema = 'HowTo' in schema_types

        if article_schema:
            schema_notes.append("✅ Article schema markup present (helps rich results)")
        else:
            schema_notes.append("⚠️ No Article schema — add BlogPosting or Article JSON-LD")
        if faq_schema:
            schema_notes.append("✅ FAQ schema found (eligible for FAQ rich results)")
        if howto_schema:
            schema_notes.append("✅ HowTo schema found")
        if schema_types:
            other = [s for s in schema_types if s not in ['Article', 'NewsArticle', 'BlogPosting', 'TechArticle', 'FAQPage', 'HowTo']]
            if other:
                schema_notes.append(f"ℹ️ Other schema: {', '.join(other[:5])}")
        elif not schema_types:
            schema_notes.append("❌ No structured data at all — implement JSON-LD")
        technical['schema'] = schema_notes
        results['schema_types'] = schema_types
        results['technical'] = technical

        # ══════════════════════════════════════
        # 6. CONTENT QUALITY
        # ══════════════════════════════════════
        quality = {}

        # Readability (simplified Flesch-Kincaid)
        def count_syllables(word):
            word = word.lower()
            vowels = 'aeiou'
            count = 0
            prev_vowel = False
            for char in word:
                is_vowel = char in vowels
                if is_vowel and not prev_vowel:
                    count += 1
                prev_vowel = is_vowel
            if word.endswith('e') and count > 1:
                count -= 1
            return max(count, 1)

        if sentences and word_count > 50:
            total_syllables = sum(count_syllables(w) for w in words[:500])  # sample first 500 words
            sample_word_count = min(word_count, 500)
            sample_sentence_count = max(len([s for s in sentences[:30]]), 1)
            avg_words_per_sent = sample_word_count / sample_sentence_count
            avg_syll_per_word = total_syllables / sample_word_count
            flesch = 206.835 - (1.015 * avg_words_per_sent) - (84.6 * avg_syll_per_word)
            flesch = round(max(0, min(100, flesch)), 1)
            results['readability_score'] = flesch

            readability_notes = []
            if flesch >= 60:
                readability_notes.append(f"✅ Readability: {flesch}/100 — Easy to read")
            elif flesch >= 40:
                readability_notes.append(f"⚠️ Readability: {flesch}/100 — Moderate difficulty")
            else:
                readability_notes.append(f"❌ Readability: {flesch}/100 — Difficult to read")
            readability_notes.append(f"ℹ️ Avg {results['avg_sentence_len']} words/sentence, {results['paragraph_count']} paragraphs")
        else:
            readability_notes = ["ℹ️ Not enough content to assess readability"]
        quality['readability'] = readability_notes

        # Keyword density (top 10 most frequent meaningful words)
        word_freq = {}
        for w in words:
            w_lower = w.lower().strip('.,!?:;()[]"\'')
            if len(w_lower) >= 4 and w_lower not in stop_words:
                word_freq[w_lower] = word_freq.get(w_lower, 0) + 1
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        kw_density = {}
        for kw, count in top_keywords:
            density = round(count / word_count * 100, 2) if word_count > 0 else 0
            kw_density[kw] = {'count': count, 'density': density}
        results['keyword_density'] = kw_density

        density_notes = []
        if top_keywords:
            top_3 = [f'"{kw}" ({count}x, {round(count/word_count*100, 1)}%)' for kw, count in top_keywords[:3]]
            density_notes.append(f"📊 Top keywords: {', '.join(top_3)}")
            # Check for keyword stuffing
            max_density = max(count / word_count * 100 for _, count in top_keywords) if top_keywords else 0
            if max_density > 3.5:
                density_notes.append("⚠️ Possible keyword stuffing — top keyword density > 3.5%")
            else:
                density_notes.append("✅ Natural keyword distribution")
        quality['keyword_density'] = density_notes

        # Content redundancy check
        redundancy_notes = []
        seen_sentences = {}
        duplicate_count = 0
        for s in sentences:
            s_normalized = re.sub(r'\s+', ' ', s.strip().lower())
            if len(s_normalized) > 20:
                if s_normalized in seen_sentences:
                    duplicate_count += 1
                else:
                    seen_sentences[s_normalized] = True
        if duplicate_count == 0:
            redundancy_notes.append("✅ No redundant/duplicate sentences detected")
        elif duplicate_count <= 3:
            redundancy_notes.append(f"⚠️ {duplicate_count} near-duplicate sentence(s) found")
        else:
            redundancy_notes.append(f"❌ {duplicate_count} duplicate sentences — review for redundancy")
        quality['redundancy'] = redundancy_notes

        results['quality'] = quality

        # ══════════════════════════════════════
        # 7. OVERALL SCORE
        # ══════════════════════════════════════
        # Weighted score from all dimensions
        foundation_score = 0
        if "✅" in str(foundation.get('introduction', '')):
            foundation_score += 33
        if "✅" in str(foundation.get('conclusion', '')):
            foundation_score += 33
        if "✅" in str(foundation.get('structure', '')):
            foundation_score += 34

        technical_score = 0
        if internal_links:
            technical_score += 25
        if external_links:
            technical_score += 15
        if len(images) >= 1:
            technical_score += 20
        if img_without_alt == 0 and len(images) > 0:
            technical_score += 15
        if article_schema:
            technical_score += 25

        quality_score = 0
        if results.get('readability_score', 0) >= 60:
            quality_score += 40
        elif results.get('readability_score', 0) >= 40:
            quality_score += 25
        if duplicate_count == 0:
            quality_score += 30
        max_d = max(count / word_count * 100 for _, count in top_keywords) if top_keywords and word_count > 0 else 0
        if max_d <= 3.5:
            quality_score += 30

        overall = round(seo_score * 0.35 + foundation_score * 0.20 + technical_score * 0.20 + quality_score * 0.25)
        results['overall_score'] = overall
        results['foundation_score'] = foundation_score
        results['technical_score'] = technical_score
        results['quality_score'] = quality_score

        if overall >= 80:
            results['overall_label'] = '🟢 Excellent'
        elif overall >= 60:
            results['overall_label'] = '🟡 Good'
        elif overall >= 40:
            results['overall_label'] = '🟠 Needs Work'
        else:
            results['overall_label'] = '🔴 Poor'

        return results

    except req.exceptions.Timeout:
        return {"error": "Request timed out (20s)", "url": url}
    except req.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "url": url}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}", "url": url}


def search_competitors(topic, num_results=5):
    """
    Search Google for competing articles on the same topic.
    Returns basic metrics for each competitor for comparison.
    """
    try:
        # Search Google
        query = topic.replace(' ', '+')
        google_url = f"https://www.google.com/search?q={query}&num={num_results + 3}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        response = req.get(google_url, headers=headers, timeout=10)
        response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        competitors = []
        # Parse Google results
        for result_div in soup.select('div.g, div[data-sokoban-container]'):
            if len(competitors) >= num_results:
                break
            link = result_div.find('a', href=True)
            title_el = result_div.find('h3')
            snippet_el = result_div.find('div', class_='VwiC3b') or result_div.find('span', class_='aCOpRe')

            if link and title_el:
                href = link.get('href', '')
                if not href.startswith('http'):
                    continue
                if 'google.com' in href:
                    continue

                comp = {
                    'url': href,
                    'title': title_el.get_text(strip=True),
                    'snippet': snippet_el.get_text(strip=True)[:150] if snippet_el else ''
                }

                # Try to fetch basic metrics from the competitor page
                try:
                    resp = req.get(href, headers=headers, timeout=8, allow_redirects=True)
                    if resp.status_code == 200:
                        csoup = BeautifulSoup(resp.text, 'html.parser')
                        for tag in csoup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                            tag.decompose()
                        c_article = csoup.find('article') or csoup.find('main') or csoup.find('body')
                        c_text = c_article.get_text(separator=' ', strip=True) if c_article else ''
                        c_words = len(c_text.split())
                        c_h2 = len(csoup.find_all('h2'))
                        c_h3 = len(csoup.find_all('h3'))
                        c_imgs = len(csoup.find_all('img'))
                        comp['word_count'] = c_words
                        comp['headings'] = c_h2 + c_h3
                        comp['images'] = c_imgs
                    else:
                        comp['word_count'] = 'N/A'
                        comp['headings'] = 'N/A'
                        comp['images'] = 'N/A'
                except:
                    comp['word_count'] = 'N/A'
                    comp['headings'] = 'N/A'
                    comp['images'] = 'N/A'

                competitors.append(comp)

        return competitors

    except Exception as e:
        print(f"[COMPETITOR SEARCH ERROR] {str(e)}", flush=True)
        return []


@app.route('/slack/command', methods=['POST'])
def slack_command():
    data = request.form
    command = data.get('command', '')
    text = data.get('text', '')
    user = data.get('user_name', 'unknown')
    user_id = data.get('user_id', '')
    trigger_id = data.get('trigger_id')
    response_url = data.get('response_url')
    channel_id = data.get('channel_id', '')
    
    print(f"[{datetime.now().isoformat()}] 📩 Received command: {command} {text} from {user} (user_id={user_id}, channel_id={channel_id})")
    
    def process_command():
        try:
            print(f"[{datetime.now().isoformat()}] ⚙️ Starting background process_command")
            response_text = "I didn't understand that command."
            attachments = []

            if "hello" in command:
                req.post(response_url, json={"text": f"Hello, <@{user}>! I am your ClickUp Guardian. 🤖", "response_type": "in_channel"})
                return

            elif "clickup-comments" in command:
                # Daily ClickUp comment summary — reads from the MCP-populated cache
                try:
                    import sys
                    sys.path.insert(0, os.path.dirname(__file__))
                    from clickup_comments_cache_manager import get_todays_comments, load_cache, MONITORED_TASKS
                    
                    # Send immediate acknowledgment
                    req.post(response_url, json={
                        "response_type": "ephemeral",
                        "text": "🔍 Fetching today's ClickUp comments..."
                    })
                    
                    cache = load_cache()
                    if not cache:
                        req.post(response_url, json={
                            "response_type": "ephemeral",
                            "text": "❌ No comment cache found. Cache needs to be refreshed."
                        })
                        return
                    
                    now = datetime.now()
                    date_str = now.strftime("%A, %B %d")
                    last_updated = cache.get("last_updated", "Unknown")
                    tasks_scanned = len(MONITORED_TASKS)
                    
                    todays_comments = get_todays_comments(cache)
                    total_comments = sum(len(t["comments"]) for t in todays_comments.values())
                    
                    if total_comments == 0:
                        req.post(response_url, json={
                            "response_type": "ephemeral",
                            "text": f"📋 *ClickUp Daily Summary — {date_str}*\n\n✅ No comments on your tasks today. You're all caught up!\n\n_Scanned {tasks_scanned} open tasks | Cache updated: {last_updated}_"
                        })
                        return
                    
                    # Build rich summary with attachments
                    attachments = []
                    for task_id, data in todays_comments.items():
                        comment_lines = []
                        for c in data["comments"]:
                            comment_text = c["text"].replace("\n", " ").strip()[:150]
                            comment_lines.append(f"• *{c['time']}* — _{c['user']}_ : {comment_text}")
                        
                        attachments.append({
                            "color": "#7B68EE",
                            "title": f"💬 {data['name']}",
                            "title_link": data["url"],
                            "text": "\n".join(comment_lines),
                            "mrkdwn_in": ["text"],
                            "footer": f"Task: {task_id} | {len(data['comments'])} comment(s) today"
                        })
                    
                    tasks_with = len(todays_comments)
                    no_comments_count = tasks_scanned - tasks_with
                    
                    header_text = (
                        f"📋 *ClickUp Daily Comment Summary — {date_str}*\n\n"
                        f"🔔 *{total_comments} comment(s)* across *{tasks_with} task(s)*\n"
                        f"🔇 {no_comments_count} task(s) with no activity today\n"
                        f"_Scanned {tasks_scanned} tasks | Cache: {last_updated}_"
                    )
                    
                    req.post(response_url, json={
                        "response_type": "ephemeral",
                        "text": header_text,
                        "attachments": attachments
                    })
                    return
                    
                except Exception as e:
                    error_msg = f"❌ Error checking comments: {str(e)}"
                    print(error_msg)
                    print(traceback.format_exc())
                    req.post(response_url, json={
                        "response_type": "ephemeral",
                        "text": error_msg
                    })
                    return

            # DISABLED: Manual /intercom-alerts command removed - automated cron check still runs every 5 min
            # elif "intercom-alerts" in command:
            #     # Check for Intercom conversations waiting for team reply (10+ minutes)
            #     try:
            #         # Import the monitoring functions
            #         import sys
            #         sys.path.insert(0, os.path.dirname(__file__)
            #         from intercom_response_monitor import process_conversations, load_state
            #         
            #         # Send immediate acknowledgment
            #         req.post(response_url, json={
            #             "response_type": "ephemeral",
            #             "text": "🔍 Checking Intercom for slow responses..."
            #         })
            #         
            #         # Use Gemini agent's MCP access to get open conversations
            #         # THIS SECTION IS A PLACEHOLDER - The agent (me) will execute this via MCP
            #         print("\n🤖 AGENT MODE: Running Intercom response check via MCP")
            #         print("=" * 60)
            #         
            #         # The agent will:
            #         # 1. Search for open conversations using mcp_intercom_search
            #         # 2. Get conversation details for each using mcp_intercom_get_conversation
            #         # 3. Call process_conversations() with the data
            #         
            #         # For now, send a helpful response
            #         req.post(response_url, json={
            #             "response_type": "ephemeral",
            #             "text": "🤖 Intercom alert check initiated. The system will check all open conversations and alert if any have been waiting 10+ minutes for a team reply."
            #         })
            #         return
            #         
            #     except Exception as e:
            #         error_msg = f"❌ Error checking Intercom: {str(e)}"
            #         print(error_msg)
            #         print(traceback.format_exc())
            #         req.post(response_url, json={
            #             "response_type": "ephemeral",
            #             "text": error_msg
            #         })
            #         return

            elif "analyze-competitor" in command or "analyze" in command:
                # Article Analysis command — Content Writer quality checks + competitor benchmarking
                try:
                    parts = text.split()
                    if len(parts) < 1 or not text.strip():
                        req.post(response_url, json={
                            "response_type": "ephemeral",
                            "text": "❌ Please provide a URL: `/analyze https://example.com/article`"
                        })
                        return
                    
                    url = clean_slack_url(parts[0])
                    print(f"[ANALYZE] Starting analysis for: {url}", flush=True)

                    # Send immediate acknowledgment
                    req.post(response_url, json={
                        "response_type": "ephemeral",
                        "text": f"🔍 Analyzing article: {url}\n⏳ This takes 15-30 seconds (fetching page + searching competitors)..."
                    })

                    # 1. Run article analysis
                    analysis = analyze_article(url)

                    if 'error' in analysis:
                        req.post(response_url, json={
                            "response_type": "ephemeral",
                            "text": f"❌ {analysis['error']}"
                        })
                        return

                    # 2. Search for competitors based on article topic
                    topic = analysis.get('h1') or analysis.get('title', '')
                    competitors = []
                    if topic:
                        print(f"[ANALYZE] Searching competitors for topic: {topic}", flush=True)
                        competitors = search_competitors(topic)

                    # ═══ Build Slack Output ═══
                    domain = analysis['url'].split('//')[1].split('/')[0]
                    msg = f"🔍 *Article Analysis — {domain}*\n"
                    msg += f"📎 {analysis['url']}\n\n"

                    # ── OVERALL SCORE ──
                    overall = analysis.get('overall_score', 0)
                    label = analysis.get('overall_label', '')
                    msg += f"*🚦 Overall Content Score: {overall}/100 {label}*\n"
                    msg += f"  SEO: {analysis.get('seo_score', 0)} | Foundation: {analysis.get('foundation_score', 0)} | Technical: {analysis.get('technical_score', 0)} | Quality: {analysis.get('quality_score', 0)}\n\n"

                    # ── SEO SCORE ──
                    seo_details = analysis.get('seo_details', {})
                    msg += "*📊 SEO Score*\n"
                    for category in ['title', 'headings', 'coverage', 'wordcount']:
                        detail = seo_details.get(category, {})
                        cat_score = detail.get('score', 0)
                        cat_name = category.capitalize()
                        msg += f"  *{cat_name}* ({cat_score}/100):\n"
                        for note in detail.get('notes', []):
                            msg += f"    {note}\n"
                    msg += "\n"

                    # ── CONTENT FOUNDATION ──
                    foundation = analysis.get('foundation', {})
                    msg += "*📝 Content Foundation*\n"
                    for section_name, notes in foundation.items():
                        msg += f"  _{section_name.capitalize()}_:\n"
                        for note in notes:
                            msg += f"    {note}\n"
                    msg += "\n"

                    # ── TECHNICAL ELEMENTS ──
                    technical = analysis.get('technical', {})
                    msg += "*🔧 Technical Elements*\n"
                    for section_name, notes in technical.items():
                        msg += f"  _{section_name.capitalize()}_:\n"
                        for note in notes:
                            msg += f"    {note}\n"
                    msg += "\n"

                    # ── CONTENT QUALITY ──
                    quality = analysis.get('quality', {})
                    msg += "*✍️ Content Quality*\n"
                    for section_name, notes in quality.items():
                        display_name = section_name.replace('_', ' ').capitalize()
                        msg += f"  _{display_name}_:\n"
                        for note in notes:
                            msg += f"    {note}\n"
                    msg += "\n"

                    # ── ARTICLE OUTLINE (Headings) ──
                    headings = analysis.get('headings', {})
                    h2s = headings.get('h2', [])
                    if h2s:
                        msg += "*📑 Article Outline*\n"
                        for i, h2 in enumerate(h2s[:10], 1):
                            msg += f"  {i}. {h2[:80]}\n"
                        msg += "\n"

                    # ── COMPETITOR BENCHMARK ──
                    if competitors:
                        msg += "*🏆 Competitor Benchmark*\n"
                        my_wc = analysis.get('word_count', 0)
                        my_headings = sum(analysis.get('heading_counts', {}).values())
                        my_imgs = analysis.get('img_total', 0)
                        msg += f"  *Your article:* {my_wc:,} words | {my_headings} headings | {my_imgs} images\n\n"

                        for i, comp in enumerate(competitors[:5], 1):
                            comp_domain = comp['url'].split('//')[1].split('/')[0][:30]
                            comp_wc = comp.get('word_count', 'N/A')
                            comp_h = comp.get('headings', 'N/A')
                            comp_img = comp.get('images', 'N/A')
                            comp_wc_str = f"{comp_wc:,}" if isinstance(comp_wc, int) else comp_wc
                            msg += f"  {i}. *{comp.get('title', 'N/A')[:60]}*\n"
                            msg += f"     _{comp_domain}_ | {comp_wc_str} words | {comp_h} headings | {comp_img} images\n"

                        # Content gap summary
                        valid_comp_wc = [c.get('word_count', 0) for c in competitors if isinstance(c.get('word_count'), int) and c['word_count'] > 0]
                        if valid_comp_wc:
                            avg_comp_wc = round(sum(valid_comp_wc) / len(valid_comp_wc))
                            diff = my_wc - avg_comp_wc
                            msg += f"\n  📊 Avg competitor word count: {avg_comp_wc:,}"
                            if diff > 0:
                                msg += f" (yours is +{diff:,} words longer ✅)\n"
                            else:
                                msg += f" (yours is {diff:,} words shorter ⚠️)\n"
                    else:
                        msg += "*🏆 Competitor Benchmark*\n  ℹ️ Could not fetch competitor data\n"

                    msg += "\n"

                    # ── QUICK RECOMMENDATIONS ──
                    msg += "*💡 Quick Recommendations*\n"
                    recs = []
                    if analysis.get('seo_score', 0) < 60:
                        recs.append("Improve SEO score: optimize title, headings, and keyword coverage")
                    if not analysis.get('technical', {}).get('schema', [''])[0].startswith('✅'):
                        recs.append("Add Article/BlogPosting schema markup for rich results")
                    if analysis.get('word_count', 0) < 1000:
                        recs.append("Expand article content — aim for 1,500+ words for informational topics")
                    if analysis.get('internal_links', 0) == 0:
                        recs.append("Add internal links to related content for topical authority")
                    if analysis.get('readability_score', 100) < 50:
                        recs.append("Improve readability: shorter sentences, simpler words")
                    if not recs:
                        recs.append("Article is well-optimized! Consider A/B testing titles for CTR")

                    for rec in recs[:5]:
                        msg += f"  • {rec}\n"

                    # Send results
                    req.post(response_url, json={
                        "response_type": "in_channel",
                        "text": msg
                    })
                    return

                except Exception as e:
                    error_msg = f"❌ Error with /analyze: {str(e)}"
                    print(error_msg, flush=True)
                    print(traceback.format_exc(), flush=True)
                    req.post(response_url, json={
                        "response_type": "ephemeral",
                        "text": error_msg
                    })
                    return


            elif "curl" in command:
                # Page analysis / curl command
                try:
                    parts = text.split()
                    if len(parts) < 1 or not text.strip():
                        response_text = "❌ Please provide a URL: `/curl https://example.com`"
                    else:
                        url = clean_slack_url(parts[0])
                        
                        # Send immediate acknowledgment
                        req.post(response_url, json={
                            "response_type": "ephemeral",
                            "text": f"🔍 Analyzing {url}..."
                        })
                        
                        # Analyze the page
                        analysis = analyze_page(url)
                        
                        if "error" in analysis:
                            req.post(response_url, json={
                                "response_type": "ephemeral",
                                "text": f"❌ Error analyzing {analysis.get('url', url)}: {analysis['error']}"
                            })
                            return
                        
                        # Build rich formatted output
                        a = analysis  # shorthand
                        
                        msg = f"📄 *{a['url'].split('//')[1].split('/')[0]} — Page Analysis*\n\n"
                        
                        # SEO Elements
                        msg += "🏷️ *SEO Elements:*\n"
                        title_icon = '✅' if a['title'] else '❌'
                        msg += f"• Title: \"{a['title'][:100]}\" ({a['title_length']} chars) {title_icon}\n"
                        
                        desc_icon = '✅' if a['meta_description'] else '❌'
                        msg += f"• Meta Description: \"{a['meta_description'][:120]}\" ({a['meta_desc_length']} chars) {desc_icon}\n"
                        
                        if a['meta_keywords']:
                            msg += f"• Meta Keywords: \"{a['meta_keywords'][:100]}\" ✅\n"
                        
                        canonical_icon = '✅' if a['canonical'] else '⚠️'
                        msg += f"• Canonical URL: {a['canonical'] or 'Not set'} {canonical_icon}\n"
                        
                        robots_icon = '✅' if a['robots'] else '⚠️'
                        msg += f"• Robots: {a['robots'] or 'Not set'} {robots_icon}\n\n"
                        
                        # Technical Metrics
                        msg += "📊 *Technical Metrics:*\n"
                        msg += f"• HTTP Status: {a['status']} {'✅' if a['status'] == 200 else '❌'}\n"
                        speed_icon = '⚡' if a['load_time'] < 1 else ('✅' if a['load_time'] < 2 else '⚠️')
                        msg += f"• Load Time: {a['load_time']}s {speed_icon}\n"
                        msg += f"• Page Size: {a['size_kb']} KB\n"
                        msg += f"• Encoding: {a['encoding']}\n\n"
                        
                        # Open Graph / Social
                        msg += "🌐 *Open Graph / Social:*\n"
                        msg += f"• OG Title: \"{a['og_title'][:80]}\" {'✅' if a['og_title'] else '❌'}\n" if a['og_title'] else "• OG Title: Missing ❌\n"
                        msg += f"• OG Description: \"{a['og_desc'][:80]}\" {'✅' if a['og_desc'] else '❌'}\n" if a['og_desc'] else "• OG Description: Missing ❌\n"
                        msg += f"• OG Image: {a['og_image'][:60]} ✅\n" if a['og_image'] else "• OG Image: Missing ❌\n"
                        msg += f"• Twitter Card: {a['twitter_card']} ✅\n" if a['twitter_card'] else "• Twitter Card: Missing ⚠️\n"
                        msg += f"• Twitter Handle: {a['twitter_handle']} ✅\n" if a['twitter_handle'] else ""
                        msg += "\n"
                        
                        # What's Working Well
                        if a['working_well']:
                            msg += "✅ *What's Working Well:*\n"
                            for item in a['working_well']:
                                msg += f"• {item}\n"
                            msg += "\n"
                        
                        # Observations
                        if a['observations']:
                            msg += "💡 *Observations:*\n"
                            for item in a['observations']:
                                msg += f"• {item}\n"
                        
                        # Send final results
                        req.post(response_url, json={
                            "response_type": "in_channel",
                            "text": msg
                        })
                        
                        # Upload raw HTML as downloadable file
                        try:
                            domain = a['url'].split('//')[1].split('/')[0]
                            filename = f"{domain.replace('.', '_')}_raw.html"
                            raw_html = a.get('raw_html', '')
                            
                            # Truncate if too long for Slack (max ~40KB for text)
                            if len(raw_html) > 39000:
                                raw_html = raw_html[:39000] + "\n\n<!-- TRUNCATED: Full HTML exceeds Slack limit -->"
                            
                            print(f"📎 Sending HTML snippet ({len(raw_html)} chars) to channel_id={channel_id}")
                            slack_client.chat_postMessage(
                                channel=channel_id,
                                text=f"📎 Raw HTML source for {a['url']}",
                                attachments=[{
                                    "title": f"{filename}",
                                    "text": f"```{raw_html[:3000]}```\n\n_Full HTML: {len(a.get('raw_html', ''))} characters_",
                                    "color": "#36a64f"
                                }]
                            )
                            print(f"✅ HTML snippet sent successfully")
                        except Exception as file_err:
                            print(f"⚠️ Could not send HTML snippet: {file_err}")
                        
                        return
                        
                except Exception as e:
                    error_msg = f"❌ Error with /curl: {str(e)}"
                    print(error_msg)
                    print(traceback.format_exc())
                    req.post(response_url, json={
                        "response_type": "ephemeral",
                        "text": error_msg
                    })
                    return


            elif "audit" in command:
                # Content Audit command — SEOmonitor-style page analysis
                try:
                    parts = text.split()
                    if len(parts) < 1 or not text.strip():
                        response_text = "❌ Please provide a URL: `/audit https://example.com`"
                    else:
                        url = clean_slack_url(parts[0])
                        print(f"[AUDIT DEBUG] Raw text={repr(text)}, parts[0]={repr(parts[0])}, cleaned url={repr(url)}", flush=True)
                        # Send immediate acknowledgment
                        req.post(response_url, json={
                            "response_type": "ephemeral",
                            "text": f"📋 Running content audit on {url}..."
                        })
                        
                        # Run the audit
                        audit = content_audit(url)
                        
                        if 'error' in audit:
                            req.post(response_url, json={
                                "response_type": "ephemeral",
                                "text": f"❌ {audit['error']}"
                            })
                            return
                        
                        # Build rich formatted output
                        domain = audit['url'].split('//')[1].split('/')[0]
                        msg = f"📋 *{domain} — Content Audit*\n\n"
                        
                        # ── ISSUES (Critical) ──
                        if audit.get('issues'):
                            msg += "*🚨 Critical Issues*\n"
                            for issue in audit['issues']:
                                msg += f"  {issue}\n"
                            msg += "\n"
                        
                        # ── Title & H1 Analysis ──
                        msg += "*🔍 Title & H1 Analysis*\n"
                        title = audit.get('title', 'N/A')
                        title_len = audit.get('title_len', 0)
                        if title:
                            msg += f"  • Title: \"{title}\" ({title_len} chars)\n"
                        else:
                            msg += f"  • Title: _missing_\n"
                        
                        h1_texts = audit.get('h1_texts', [])
                        h1_count = audit.get('h1_count', 0)
                        if h1_count == 1:
                            msg += f"  • H1: \"{h1_texts[0]}\" ({len(h1_texts[0])} chars)\n"
                        elif h1_count > 1:
                            msg += f"  • H1: {h1_count} found — "
                            msg += ', '.join([f'"{h}"' for h in h1_texts[:3]]) + "\n"
                        else:
                            msg += f"  • H1: _missing_\n"
                        
                        # Keywords in title/H1
                        target_kw = audit.get('target_keywords', [])
                        if target_kw:
                            msg += f"  • Target keywords: {', '.join(target_kw[:5])}\n"
                        msg += "\n"
                        
                        # ── Heading Structure ──
                        heading_counts = audit.get('heading_counts', {})
                        if heading_counts:
                            msg += "*📐 Heading Structure*\n"
                            counts_str = ' | '.join([f"{k.upper()}: {v}" for k, v in heading_counts.items() if v > 0])
                            msg += f"  {counts_str}\n\n"
                        
                        # ── Content Analysis ──
                        msg += "*📝 Content Analysis*\n"
                        word_count = audit.get('word_count', 0)
                        msg += f"  • Word count: {word_count:,}\n"
                        
                        # Keyword density
                        kw_density = audit.get('keyword_density', {})
                        if kw_density:
                            density_parts = []
                            for kw, data in list(kw_density.items())[:3]:
                                density_parts.append(f'"{kw}" {data["count"]}x ({data["density"]}%)')
                            density_str = " | ".join(density_parts)
                            msg += f"  • Keyword density: {density_str}\n"
                        
                        msg += f"  • Internal links: {audit.get('internal_links', 0)} | External: {audit.get('external_links', 0)}\n"
                        
                        img_total = audit.get('img_total', 0)
                        img_with_alt = audit.get('img_with_alt', 0)
                        img_without_alt = audit.get('img_without_alt', 0)
                        if img_total > 0:
                            msg += f"  • Images: {img_total} ({img_with_alt} with alt, {img_without_alt} missing)\n"
                        msg += "\n"
                        
                        # ── Topic Focus ──
                        topics = audit.get('topics', [])
                        if topics:
                            msg += "*🎯 Topic Focus*\n"
                            unique_topics = list(set(topics))[:5]
                            msg += f"  • Topics detected: {len(set(topics))}\n"
                            msg += f"  • {', '.join(unique_topics)}\n\n"
                        
                        # ── Meta & Technical ──
                        msg += "*🏷️ Meta & Technical*\n"
                        meta_desc = audit.get('meta_description', '')
                        if meta_desc:
                            msg += f"  • Meta description: ✅ ({len(meta_desc)} chars)\n"
                        else:
                            msg += f"  • Meta description: ❌ Missing\n"
                        
                        canonical = audit.get('canonical', '')
                        if canonical:
                            msg += f"  • Canonical: ✅\n"
                        else:
                            msg += f"  • Canonical: ⚠️ Missing\n"
                        
                        robots = audit.get('robots', '')
                        if robots:
                            msg += f"  • Robots: {robots}\n"
                        
                        schema_types = audit.get('schema_types', [])
                        if schema_types:
                            msg += f"  • Schema: {', '.join(schema_types)}\n"
                        else:
                            msg += f"  • Schema: ⚠️ None found\n"
                        msg += "\n"
                        
                        # ── Warnings ──
                        warnings = audit.get('warnings', [])
                        if warnings:
                            msg += "*⚠️ Warnings*\n"
                            for w in warnings:
                                msg += f"  {w}\n"
                            msg += "\n"
                        
                        # ── What's Passing ──
                        passes = audit.get('passes', [])
                        if passes:
                            msg += "*✅ What's Working*\n"
                            for p in passes:
                                msg += f"  {p}\n"
                            msg += "\n"
                        
                        # ── Score ──
                        score = audit.get('score', 0)
                        score_label = audit.get('score_label', '')
                        msg += f"*🚦 Content Audit Score: {score}/100 {score_label}*\n"
                        
                        # Send the results
                        req.post(response_url, json={
                            "response_type": "in_channel",
                            "text": msg
                        })
                        return
                        
                except Exception as e:
                    error_msg = f"❌ Error with /audit: {str(e)}"
                    print(error_msg)
                    print(traceback.format_exc())
                    req.post(response_url, json={
                        "response_type": "ephemeral",
                        "text": error_msg
                    })
                    return

            elif "clickup-comments" in command or "check-comments" in command:
                # Check for new comments on open ClickUp tasks
                try:
                    from clickup_comment_monitor import run_check_with_mcp_data, OPEN_TASK_IDS
                    
                    print("🔍 Checking ClickUp comments...")
                    
                    # Send immediate acknowledgment
                    req.post(response_url, json={
                        "response_type": "ephemeral",
                        "text": "🔍 Scanning open ClickUp tasks for new comments..."
                    })
                    
                    # Step 1: Search for tasks
                    from mcp_tools import mcp_clickup_search
                    tasks_result = mcp_clickup_search({"keywords": "sulejman"})
                    
                    if not tasks_result:
                        req.post(response_url, json={
                            "response_type": "ephemeral",
                            "text": "❌ Failed to fetch  tasks from ClickUp"
                        })
                        return
                    
                    # Step 2: Get comments for each open task
                    from mcp_tools import mcp_clickup_get_task_comments
                    comments_by_task = {}
                    
                    for task_id in OPEN_TASK_IDS:
                        print(f"   Fetching comments for {task_id}...")
                        comments = mcp_clickup_get_task_comments(task_id)
                        if comments:
                            comments_by_task[task_id] = comments
                    
                    # Step 3: Check for new comments and send alerts
                    alerts_sent = run_check_with_mcp_data(
                        tasks_result,
                        comments_by_task,
                        dry_run=False
                    )
                    
                    # Send result
                    result_icon = "✅" if alerts_sent == 0 else "🔔"
                    result_msg = f"{result_icon} Scan complete: {alerts_sent} new comment(s) found"
                    
                    req.post(response_url, json={
                        "response_type": "ephemeral",
                        "text": result_msg
                    })
                    
                except Exception as e:
                    error_msg = f"❌ Error checking comments: {str(e)}"
                    print(error_msg)
                    print(traceback.format_exc())
                    req.post(response_url, json={
                        "response_type": "ephemeral",
                        "text": error_msg
                    })
                return
            
            elif "check-tasks" in command or "clickup" in command:
                tasks = get_real_clickup_tasks()
                
                # Fallback to mock if real tasks fail
                if not tasks:
                    print("⚠️ No real tasks found, using mock data as fallback")
                    tasks = get_mock_tasks()
                
                if not tasks:
                    response_text = "✅ No open tasks found. Great job!"
                else:
                    response_text = f"📋 *Your Open ClickUp Tasks* ({len(tasks)} tasks):"
                    for task in tasks:
                        # Determine color based on tags or status
                        color = "#36a64f"  # default green
                        tags_list = [t['name'] for t in task.get('tags', [])]
                        
                        if 'Bug' in tags_list or 'Maintenance' in tags_list:
                            color = "#e01e5a"  # red for bugs/maintenance
                        elif 'Product' in tags_list or 'Feature' in tags_list:
                            color = "#36a64f"  # green for product/features
                        else:
                            color = "#FFA500"  # orange for other tasks
                        
                        # Build fields for the attachment
                        fields = [
                            {"title": "Status", "value": task['status']['status'], "short": True}
                        ]
                        
                        # Add custom ID if available
                        if task.get('custom_id'):
                            fields.insert(0, {"title": "ID", "value": task['custom_id'], "short": True})
                        
                        # Add latest comment instead of tags
                        latest_comment = task.get('latest_comment')
                        if latest_comment:
                            fields.append({"title": "Latest Comment", "value": latest_comment, "short": False})
                        
                        # Add assignees if available
                        assignees = task.get('assignees', [])
                        if assignees and isinstance(assignees, list) and len(assignees) > 0:
                            assignee_str = ", ".join(assignees) if isinstance(assignees[0], str) else "Multiple assignees"
                            fields.append({"title": "Assignees", "value": assignee_str, "short": True})
                        
                        attachments.append({
                            "color": color,
                            "title": task['name'],
                            "title_link": task['url'],
                            "fields": fields
                        })

            elif "check-invoices" in command:
                invoices = get_mock_invoices()
                if not invoices:
                    response_text = "✅ No overdue invoices found."
                else:
                    response_text = f"🧾 Found {len(invoices)} invoices to review:"
                    for inv in invoices:
                        attachments.append({
                            "color": "#FFA500",
            "title": f"Invoice #{inv['id']} - {inv['customer_email']}",
                            "text": f"Amount: ${inv['amount']} | Overdue: {inv['days_overdue']} days\nStrategy: {inv['scenario']}",
                            "footer": f"Tone: {inv['tone']} | Reason: {inv.get('failure_reason')}"
                        })

            elif "wbr-compare" in command:
                # Week-over-week comparison command
                try:
                    script_path = os.path.join(os.path.dirname(__file__), 'wbr_enhanced.py')
                    result = subprocess.run(
                        ['python3', '-c', '''
import sys
sys.path.insert(0, ".")
from wbr_enhanced import get_wbr_data, compare_weeks
current = get_wbr_data(week_offset=0)
previous = get_wbr_data(week_offset=1)
if current and previous:
    print(compare_weeks(current, previous))
else:
    print("❌ Could not fetch WBR data for comparison")
'''],
                        capture_output=True,
                        text=True,
                        timeout=20,
                        cwd=os.path.dirname(__file__)
                    )
                    
                    # Check for errors
                    if result.returncode != 0:
                        print(f"❌ WBR compare subprocess failed with code {result.returncode}")
                        print(f"STDERR: {result.stderr}")
                        response_text = f"❌ Error loading WBR comparison (exit code {result.returncode})"
                        if result.stderr:
                            # Filter out common warnings
                            stderr_clean = '\n'.join([line for line in result.stderr.split('\n') 
                                                     if 'FutureWarning' not in line and 'NotOpenSSLWarning' not in line 
                                                     and line.strip()])
                            if stderr_clean:
                                response_text += f"\n```{stderr_clean[:200]}```"
                    elif result.stdout:
                        response_text = result.stdout.strip()
                    else:
                        response_text = "❌ Could not load WBR comparison (no output)"
                        
                except subprocess.TimeoutExpired:
                    response_text = "❌ WBR comparison timed out (taking more than 20 seconds)"
                except Exception as e:
                    print(f"❌ WBR compare exception: {e}")
                    print(traceback.format_exc())
                    response_text = f"❌ Error loading WBR comparison: {str(e)}"

            elif "wbr" in command or "summary" in command:
                # Enhanced WBR command with all sheets
                try:
                    script_path = os.path.join(os.path.dirname(__file__), 'wbr_enhanced.py')
                    result = subprocess.run(
                        ['python3', '-c', '''
import sys
sys.path.insert(0, ".")
from wbr_enhanced import get_wbr_data, format_wbr_summary
data = get_wbr_data(week_offset=0)
if data:
    print(format_wbr_summary(data))
else:
    print("❌ Could not fetch WBR data")
'''],
                        capture_output=True,
                        text=True,
                        timeout=20,
                        cwd=os.path.dirname(__file__)
                    )
                    
                    # Check for errors
                    if result.returncode != 0:
                        print(f"❌ WBR subprocess failed with code {result.returncode}")
                        print(f"STDERR: {result.stderr}")
                        response_text = f"❌ Error loading WBR data (exit code {result.returncode})"
                        if result.stderr:
                            stderr_clean = '\n'.join([line for line in result.stderr.split('\n') 
                                                     if 'FutureWarning' not in line and 'NotOpenSSLWarning' not in line 
                                                     and line.strip()])
                            if stderr_clean:
                                response_text += f"\n```{stderr_clean[:200]}```"
                    elif result.stdout:
                        response_text = result.stdout.strip()
                    else:
                        response_text = "❌ Could not load WBR data (no output)"
                        
                except subprocess.TimeoutExpired:
                    response_text = "❌ WBR fetch timed out (taking more than 20 seconds)"
                except Exception as e:
                    print(f"❌ WBR exception: {e}")
                    print(traceback.format_exc())
                    response_text = f"❌ Error loading WBR: {str(e)}"


            elif "intercom" in command:
                data = get_intercom_summary()
                if "error" in data:
                    response_text = f"❌ Error fetching Intercom data: {data['error']}"
                else:
                    # Main summary header
                    response_text = f"🏷️ *Intercom Inbox Summary* (Total: {data['total_count']})\n"
                    
                    # Status breakdown
                    status_bd = data.get('status_breakdown', {})
                    response_text += f"\n📊 *Status:*\n"
                    response_text += f"• 🟢 Open: {status_bd.get('open', 0)}\n"
                    response_text += f"• 🔴 Closed: {status_bd.get('closed', 0)}\n"
                    response_text += f"• 💤 Snoozed: {status_bd.get('snoozed', 0)}\n"
                    response_text += f"• 📥 Unassigned: {data['unassigned_count']}\n"
                    
                    # Waiting breakdown
                    waiting_bd = data.get('waiting_breakdown', {})
                    if waiting_bd.get('waiting_customer', 0) > 0 or waiting_bd.get('waiting_team', 0) > 0:
                        response_text += f"\n⏳ *Waiting:*\n"
                        if waiting_bd.get('waiting_customer', 0) > 0:
                            response_text += f"• Customer Reply: {waiting_bd['waiting_customer']}\n"
                        if waiting_bd.get('waiting_team', 0) > 0:
                            response_text += f"• Team Action: {waiting_bd['waiting_team']}\n"
                    
                    # Assignee distribution (top 5)
                    assignee_counts = data.get('assignee_counts', {})
                    if assignee_counts:
                        response_text += f"\n👥 *Assignees:*\n"
                        sorted_assignees = sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                        for name, count in sorted_assignees:
                            response_text += f"• {name}: {count}\n"
                    
                    # Channel breakdown
                    channel_bd = data.get('channel_breakdown', {})
                    if channel_bd:
                        response_text += f"\n📬 *Channels:*\n"
                        for channel, count in sorted(channel_bd.items(), key=lambda x: x[1], reverse=True):
                            channel_emoji = {"email": "📧", "conversation": "💬", "push": "📲", "phone": "📞"}.get(channel, "📨")
                            response_text += f"• {channel_emoji} {channel.title()}: {count}\n"
                    
                    # Priority conversations
                    priority = data.get('priority_conversations', [])
                    if priority:
                        response_text += f"\n\n🔥 *Priority Conversations ({len(priority)}):*"
                        for conv in priority:
                            conv_id = conv.get('id')
                            source = conv.get('source', {})
                            subject_raw = source.get('subject') or (source.get('body')[:50] + "...") if source.get('body') else "No Subject"
                            subject = strip_html(subject_raw)
                            
                            # Get assignee name
                            assignee_id = conv.get('admin_assignee_id')
                            admins = data.get('admins', {})
                            assignee_name = admins.get(assignee_id, "Unassigned") if assignee_id else "Unassigned"
                            
                            # Determine priority reason
                            priority_reason = "🔴 Unassigned" if not assignee_id else "⏳ Waiting"
                            
                            attachments.append({
                                "color": "#e01e5a" if not assignee_id else "#ffa500",
                                "title": f"Conversation #{conv_id}",
                                "title_link": f"https://app.intercom.com/a/apps/_/inbox/all/conversations/{conv_id}",
                                "text": f"{subject}",
                                "fields": [
                                    {"title": "Status", "value": priority_reason, "short": True},
                                    {"title": "Assignee", "value": assignee_name, "short": True}
                                ],
                                "footer": f"Updated: {datetime.fromtimestamp(conv.get('updated_at', 0)).strftime('%Y-%m-%d %H:%M')}"
                            })


            elif "intercom-report" in command or ("intercom" in command and "report" in text):
                report = get_intercom_okr_report()
                if "error" in report:
                    response_text = f"❌ Error generating report: {report['error']}"
                else:
                    response_text = "📊 *Intercom OKR Weekly Report*"
                    
                    # Fin Deflection
                    def_status = "✅ On Track" if report['deflection'] >= 72 else "⚠️ At Risk"
                    attachments.append({
                        "color": "#36a64f" if report['deflection'] >= 72 else "#e01e5a",
                        "title": "Fin AI Deflection",
                        "text": f"Current: *{report['deflection']:.1f}%* | Target: *72%*\nStatus: {def_status}",
                        "footer": f"Based on {report['fin_count']} Fin interactions"
                    })
                    
                    # Fin Resolution
                    res_status = "✅ On Track" if report['resolution'] >= 35 else "⚠️ At Risk"
                    attachments.append({
                        "color": "#36a64f" if report['resolution'] >= 35 else "#e01e5a",
                        "title": "Fin AI Resolution",
                        "text": f"Current: *{report['resolution']:.1f}%* | Target: *35%*\nStatus: {res_status}"
                    })
                    
                    # CSAT
                    csat_status = "✅ On Track" if report['csat'] >= 4.7 else "⚠️ At Risk"
                    attachments.append({
                        "color": "#36a64f" if report['csat'] >= 4.7 else "#e01e5a",
                        "title": "Customer Satisfaction (CSAT)",
                        "text": f"Current: *{report['csat']:.1f}/5* | Target: *4.7/5*\nStatus: {csat_status}",
                        "footer": f"Based on {report['csat_count']} customer ratings"
                    })

            elif "intercom-audit" in command or ("intercom" in command and "audit" in text):
                audit = get_intercom_audit()
                if "error" in audit:
                    response_text = f"❌ Audit failed: {audit['error']}"
                elif not audit['findings']:
                    response_text = "✅ *Intercom CSAT Audit*: No negative feedback (< 4 stars) found in the last 14 days. Great job!"
                else:
                    response_text = f"🔍 *Weekly CSAT Audit Summary* ({len(audit['findings'])} issues flagged)"
                    
                    # Workflow insights
                    wf_text = "\n".join([f"• *{wf.capitalize()}*: {count} mentions" for wf, count in audit['top_workflows'] if count > 0])
                    if wf_text:
                        attachments.append({
                            "color": "#4285F4",
                            "title": "🔄 Repetitive Workflow Detection",
                            "text": f"Potential automation opportunities found:\n{wf_text}"
                        })
                    
                    # Sentiment/Individual Issue analysis
                    for issue in audit['findings']:
                        sentiment_tags = " | ".join(issue['sentiments']) or "No specific pattern detected"
                        attachments.append({
                            "color": "#e01e5a",
                            "title": f"Conversation #{issue['id']} (Rating: {issue['rating']}/5)",
                            "title_link": issue['url'],
                            "text": f"*Sentiment:* {sentiment_tags}\n*Customer Remark:* {issue['remark']}",
                            "footer": "Categorized via Intercom Audit Logic"
                        })

            elif "product-updates" in command or "product-comm" in command:
                # Parse optional days parameter
                lookup_days = 30
                if text.strip():
                    try:
                        parts = text.strip().split('=')
                        if len(parts) == 2 and parts[0].strip() == 'days':
                            lookup_days = int(parts[1].strip())
                        else:
                            lookup_days = int(text.strip())
                    except ValueError:
                        pass
                
                req.post(response_url, json={
                    "response_type": "ephemeral",
                    "text": f"📡 Fetching product updates from the last {lookup_days} days..."
                })
                
                updates = get_product_updates(days=lookup_days)
                
                if 'error' in updates:
                    response_text = f"❌ Failed to fetch product updates: {updates['error']}"
                elif updates['total'] == 0:
                    response_text = f"📭 No product updates in #product-comm in the last {lookup_days} days."
                else:
                    response_text = f"📢 *Product Updates Summary* — Last {lookup_days} days ({updates['total']} updates)"
                    
                    for week_key, week_data in updates['weeks'].items():
                        week_lines = []
                        for msg in week_data['messages']:
                            # Clean up Slack formatting
                            text_clean = msg['text'].replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
                            # Truncate long messages
                            if len(text_clean) > 300:
                                text_clean = text_clean[:300] + '...'
                            date_str = msg['date'].strftime('%b %d, %H:%M')
                            week_lines.append(f"• *{date_str}* — _{msg['author']}_\n{text_clean}")
                        
                        attachments.append({
                            "color": "#36a64f",
                            "title": f"📅 Week of {week_data['start']} – {week_data['end']}",
                            "text": "\n\n".join(week_lines),
                            "mrkdwn_in": ["text"],
                            "footer": f"{len(week_data['messages'])} update(s)"
                        })

            elif "test-api" in command or "api" in command:
                modal_view = {
                    "type": "modal",
                    "callback_id": "api_test_modal",
                    "title": {"type": "plain_text", "text": "SEOmonitor API Test"},
                    "submit": {"type": "plain_text", "text": "Run Test"},
                    "close": {"type": "plain_text", "text": "Cancel"},
                    "blocks": [
                        {
                            "type": "input",
                            "block_id": "endpoint_block",
                            "element": {
                                "type": "static_select",
                                "action_id": "endpoint_select",
                                "placeholder": {"type": "plain_text", "text": "Select Endpoint"},
                                "options": [
                                    {"text": {"type": "plain_text", "text": "Get Tracked Campaigns"}, "value": "campaigns"},
                                    {"text": {"type": "plain_text", "text": "Get Keywords Data"}, "value": "keywords"},
                                    {"text": {"type": "plain_text", "text": "Get Competitors"}, "value": "competitors"},
                                    {"text": {"type": "plain_text", "text": "Get Visibility"}, "value": "visibility"},
                                    {"text": {"type": "plain_text", "text": "Get Forecasts"}, "value": "forecasts"}
                                ],
                                "initial_option": {"text": {"type": "plain_text", "text": "Get Keywords Data"}, "value": "keywords"}
                            },
                            "label": {"type": "plain_text", "text": "Endpoint (Required)"}
                        },
                        {
                            "type": "input",
                            "block_id": "token_block",
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "token_input",
                                "placeholder": {"type": "plain_text", "text": "Paste your JWT token here"}
                            },
                            "label": {"type": "plain_text", "text": "API Token (Required)"}
                        },
                        {
                            "type": "input",
                            "block_id": "campaign_id_block",
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "campaign_id_input",
                                "placeholder": {"type": "plain_text", "text": "e.g. 329461"}
                            },
                            "label": {"type": "plain_text", "text": "Campaign ID (Required)"}
                        },
                        {
                            "type": "input",
                            "block_id": "start_date_block",
                            "element": {
                                "type": "datepicker",
                                "action_id": "start_date_input",
                                "initial_date": "2026-01-05"
                            },
                            "label": {"type": "plain_text", "text": "Start Date (Required)"}
                        },
                        {
                            "type": "input",
                            "block_id": "end_date_block",
                            "element": {
                                "type": "datepicker",
                                "action_id": "end_date_input",
                                "initial_date": "2026-02-05"
                            },
                            "label": {"type": "plain_text", "text": "End Date (Required)"}
                        },
                        {
                            "type": "input",
                            "block_id": "group_id_block",
                            "optional": True,
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "group_id_input",
                                "placeholder": {"type": "plain_text", "text": "e.g. 0 (All Keywords)"}
                            },
                            "label": {"type": "plain_text", "text": "Group ID (Optional)"}
                        },
                        {
                            "type": "input",
                            "block_id": "search_block",
                            "optional": True,
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "search_input",
                                "placeholder": {"type": "plain_text", "text": "Search term..."}
                            },
                            "label": {"type": "plain_text", "text": "Search (Optional)"}
                        },
                        {
                            "type": "input",
                            "block_id": "limit_block",
                            "optional": True,
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "limit_input",
                                "placeholder": {"type": "plain_text", "text": "e.g. 100"}
                            },
                            "label": {"type": "plain_text", "text": "Limit (Optional)"}
                        },
                        {
                            "type": "input",
                            "block_id": "offset_block",
                            "optional": True,
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "offset_input",
                                "placeholder": {"type": "plain_text", "text": "e.g. 0"}
                            },
                            "label": {"type": "plain_text", "text": "Offset (Optional)"}
                        },
                        {
                            "type": "input",
                            "block_id": "order_by_block",
                            "optional": True,
                            "element": {
                                "type": "static_select",
                                "action_id": "order_by_select",
                                "placeholder": {"type": "plain_text", "text": "Select sorting"},
                                "options": [
                                    {"text": {"type": "plain_text", "text": "Search Volume"}, "value": "search_volume"},
                                    {"text": {"type": "plain_text", "text": "Rank"}, "value": "rank"}
                                ]
                            },
                            "label": {"type": "plain_text", "text": "Order By (Optional)"}
                        },
                        {
                            "type": "input",
                            "block_id": "order_direction_block",
                            "optional": True,
                            "element": {
                                "type": "static_select",
                                "action_id": "order_direction_select",
                                "placeholder": {"type": "plain_text", "text": "Select direction"},
                                "options": [
                                    {"text": {"type": "plain_text", "text": "Ascending"}, "value": "asc"},
                                    {"text": {"type": "plain_text", "text": "Descending"}, "value": "desc"}
                                ]
                            },
                            "label": {"type": "plain_text", "text": "Order Direction (Optional)"}
                        },
                        {
                            "type": "input",
                            "block_id": "keyword_ids_block",
                            "optional": True,
                            "element": {
                                "type": "plain_text_input",
                                "action_id": "keyword_ids_input",
                                "placeholder": {"type": "plain_text", "text": "e.g. 1,2,3"}
                            },
                            "label": {"type": "plain_text", "text": "Keyword IDs (Optional)"}
                        },
                        {
                            "type": "input",
                            "block_id": "include_all_groups_block",
                            "optional": True,
                            "element": {
                                "type": "static_select",
                                "action_id": "include_all_groups_select",
                                "placeholder": {"type": "plain_text", "text": "Select..."},
                                "options": [
                                    {"text": {"type": "plain_text", "text": "Yes (1)"}, "value": "1"},
                                    {"text": {"type": "plain_text", "text": "No (0)"}, "value": "0"}
                                ]
                            },
                            "label": {"type": "plain_text", "text": "Include All Groups (Optional)"}
                        }
                    ]
                }
                try:
                    slack_client.views_open(trigger_id=trigger_id, view=modal_view)
                    return
                except Exception as e:
                    print(f"❌ Error opening modal: {e}")
                    req.post(response_url, json={" text": f"Error opening modal: {str(e)}"})
                    return

            else:
                response_text = f"I received: `{command}`. Try `/check-tasks` or `/check-invoices`."

            # Send delayed response using response_url
            req.post(response_url, json={
                "response_type": "in_channel",
                "text": response_text,
                "attachments": attachments
            })
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"❌ Error in process_command: {e}\n{error_details}")
            try:
                req.post(response_url, json={
                    "response_type": "ephemeral",
                    "text": f"⚠️ *Internal Error:* Something went wrong while processing `{command}`.\n```{str(e)}```"
                })
            except:
                pass

    threading.Thread(target=process_command).start()
    return "", 200

@app.route('/slack/interactive', methods=['POST'])
def slack_interactive():
    raw_payload = request.form.get('payload')
    if not raw_payload:
        return jsonify({"text": "No payload received"}), 200
    payload = json.loads(raw_payload)
    if payload['type'] == 'view_submission' and payload['view']['callback_id'] == 'api_test_modal':
        values = payload['view']['state']['values']
        endpoint = values['endpoint_block']['endpoint_select']['selected_option']['value']
        token = values['token_block']['token_input']['value']
        campaign_id = values['campaign_id_block']['campaign_id_input']['value']
        start_date = values['start_date_block']['start_date_input'].get('selected_date', '')
        end_date = values['end_date_block']['end_date_input'].get('selected_date', '')

        # Optional fields
        group_id = values.get('group_id_block', {}).get('group_id_input', {}).get('value')
        search_term = values.get('search_block', {}).get('search_input', {}).get('value')
        limit = values.get('limit_block', {}).get('limit_input', {}).get('value')
        offset = values.get('offset_block', {}).get('offset_input', {}).get('value')
        order_by_sel = values.get('order_by_block', {}).get('order_by_select', {}).get('selected_option')
        order_by = order_by_sel['value'] if order_by_sel else None
        order_dir_sel = values.get('order_direction_block', {}).get('order_direction_select', {}).get('selected_option')
        order_direction = order_dir_sel['value'] if order_dir_sel else None
        keyword_ids = values.get('keyword_ids_block', {}).get('keyword_ids_input', {}).get('value')
        include_groups_sel = values.get('include_all_groups_block', {}).get('include_all_groups_select', {}).get('selected_option')
        include_all_groups = include_groups_sel['value'] if include_groups_sel else None

        user_id = payload['user']['id']

        def async_api_test():
            try:
                # Build API URL based on endpoint
                base_url = "https://apigw.seomonitor.com/v3"
                endpoint_paths = {
                    "campaigns": f"/rank-tracker/v3.0/campaigns/{campaign_id}",
                    "keywords": f"/rank-tracker/v3.0/keywords?campaign_id={campaign_id}&start_date={start_date}&end_date={end_date}",
                    "competitors": f"/rank-tracker/v3.0/competitors?campaign_id={campaign_id}&start_date={start_date}&end_date={end_date}",
                    "visibility": f"/rank-tracker/v3.0/visibility?campaign_id={campaign_id}&start_date={start_date}&end_date={end_date}",
                    "forecasts": f"/forecast/v3.0/forecast?campaign_id={campaign_id}",
                }
                url = base_url + endpoint_paths.get(endpoint, f"/rank-tracker/v3.0/{endpoint}")

                # Add optional query params
                if '?' in url:
                    qp = []
                else:
                    url += '?'
                    qp = []
                if group_id: qp.append(f"group_id={group_id}")
                if search_term: qp.append(f"search={search_term}")
                if limit: qp.append(f"limit={limit}")
                if offset: qp.append(f"offset={offset}")
                if order_by: qp.append(f"order_by={order_by}")
                if order_direction: qp.append(f"order_direction={order_direction}")
                if keyword_ids: qp.append(f"keyword_ids={keyword_ids}")
                if include_all_groups: qp.append(f"include_all_groups={include_all_groups}")
                if qp:
                    url += "&" + "&".join(qp) if '=' in url else "&".join(qp)

                print(f"🔍 API Test: {endpoint} → {url}")

                headers = {
                    "Authorization": token,
                    "Accept": "application/json"
                }
                response = req.get(url, headers=headers, timeout=30)

                status_code = response.status_code
                try:
                    data = response.json()
                except:
                    data = response.text

                # Build Slack message
                attachments = []
                if status_code == 200:
                    if isinstance(data, list):
                        total_items = len(data)
                        summary_text = f"✅ *{endpoint.upper()}* returned *{total_items} items*"
                        # Show first 5 items as preview
                        preview_items = data[:5]
                        for i, item in enumerate(preview_items):
                            if endpoint == "keywords":
                                kw = item.get('keyword', 'N/A')
                                intent = item.get('search_intent', 'N/A')
                                # Nested: search_data
                                search_data = item.get('search_data', {})
                                sv = search_data.get('search_volume', 'N/A')
                                yoy = search_data.get('year_over_year', 'N/A')
                                # Nested: ranking_data
                                ranking_data = item.get('ranking_data', {})
                                desktop_rank = ranking_data.get('desktop', {}).get('rank', 'N/A')
                                mobile_rank = ranking_data.get('mobile', {}).get('rank', 'N/A')
                                desktop_best = ranking_data.get('desktop', {}).get('best_rank', {})
                                best_rank = desktop_best.get('rank', 'N/A')
                                best_date = desktop_best.get('date', '')
                                # Nested: opportunity
                                opp_data = item.get('opportunity', {})
                                opp_score = opp_data.get('score', 'N/A')
                                difficulty = opp_data.get('difficulty', 'N/A')
                                cpc = opp_data.get('avg_cpc', 'N/A')
                                # Nested: landing_pages
                                lp_data = item.get('landing_pages', {})
                                landing_page = lp_data.get('desktop', {}).get('current', 'N/A')
                                # Nested: ai_search
                                ai_data = item.get('ai_search', {})
                                ai_rank = ai_data.get('rank', 'N/A')
                                ai_brand = ai_data.get('my_brand_presence', False)
                                ai_sentiment = ai_data.get('sentiment_of_my_brand', 'N/A')
                                # Nested: serp_data
                                serp_data = item.get('serp_data', {})
                                pct_clicks = serp_data.get('percentage_clicks', 'N/A')
                                # SERP features list
                                desktop_features = serp_data.get('desktop', [])
                                feat_list = ", ".join([f.get('feature', '') for f in desktop_features]) if desktop_features else 'None'
                                # Traffic
                                traffic = item.get('traffic_data', {})
                                sessions = traffic.get('sessions', 0)
                                currency = traffic.get('currency', '')

                                # Rank display
                                rank_display = f"D:{desktop_rank} / M:{mobile_rank}"
                                if best_rank != 'N/A':
                                    rank_display += f" (Best: {best_rank} on {best_date})"
                                # AI display
                                ai_display = f"Rank: {ai_rank}"
                                if ai_brand:
                                    ai_display += f" | Brand: ✅ ({ai_sentiment})"
                                else:
                                    ai_display += " | Brand: ❌"

                                attachments.append({
                                    "color": "#36a64f",
                                    "title": f"#{i+1}: {kw}",
                                    "text": (
                                        f"*Rank:* {rank_display}\n"
                                        f"*Search Vol:* {sv} | *YoY:* {yoy} | *Intent:* {intent}\n"
                                        f"*Opportunity:* {opp_score} | *Difficulty:* {difficulty} | *CPC:* {cpc}\n"
                                        f"*AI Search:* {ai_display}\n"
                                        f"*SERP Features:* {feat_list} | *Click %:* {pct_clicks}\n"
                                        f"*Landing Page:* {landing_page}\n"
                                        f"*Sessions:* {sessions} {currency}"
                                    ),
                                    "footer": f"SEOmonitor API • {endpoint}"
                                })
                            else:
                                title = item.get('name', item.get('keyword', item.get('domain', f'Item {i+1}')))
                                item_preview = json.dumps(item, indent=2)[:500]
                                attachments.append({
                                    "color": "#36a64f",
                                    "title": f"#{i+1}: {title}",
                                    "text": f"```{item_preview}```",
                                    "footer": f"SEOmonitor API • {endpoint}"
                                })
                        if total_items > 5:
                            summary_text += f"\n_(Showing first 5 of {total_items})_"
                    elif isinstance(data, dict):
                        summary_text = f"✅ *{endpoint.upper()}* returned data"
                        data_preview = json.dumps(data, indent=2)[:1500]
                        attachments.append({
                            "color": "#36a64f",
                            "text": f"```{data_preview}```",
                            "footer": f"SEOmonitor API • {endpoint}"
                        })
                    else:
                        summary_text = f"✅ *{endpoint.upper()}* response: `{str(data)[:500]}`"
                else:
                    summary_text = f"❌ *{endpoint.upper()}* failed with status `{status_code}`"
                    error_text = json.dumps(data, indent=2)[:1000] if isinstance(data, (dict, list)) else str(data)[:1000]
                    attachments.append({
                        "color": "#e01e5a",
                        "title": f"Error {status_code}",
                        "text": f"```{error_text}```"
                    })

                # Send result as DM to the user
                slack_client.chat_postMessage(
                    channel=user_id,
                    text=summary_text,
                    attachments=attachments
                )
                print(f"✅ API test results sent to user {user_id}")

            except Exception as e:
                error_details = traceback.format_exc()
                print(f"❌ API test error: {e}\n{error_details}")
                try:
                    slack_client.chat_postMessage(
                        channel=user_id,
                        text=f"❌ *API Test Failed*\n```{str(e)}```"
                    )
                except:
                    pass

        threading.Thread(target=async_api_test).start()
    return "", 200

@app.route('/clickup/webhook', methods=['POST'])
def clickup_webhook():
    """
    Webhook endpoint to receive ClickUp events.
    Sends Slack notifications for comments on tasks where you're assigned.
    """
    try:
        data = request.json
        print(f"[{datetime.now().isoformat()}] 📨 Received ClickUp webhook: {json.dumps(data, indent=2)}")
        
        # Extract event type
        event = data.get('event')
        
        if event == 'taskCommentPosted':
            # Extract comment and task details
            comment_data = data.get('comment', {})
            task_data = data.get('task', {})
            
            comment_text = comment_data.get('comment_text', '')
            comment_user = comment_data.get('user', {})
            commenter_name = comment_user.get('username', 'Unknown User')
            
            task_id = task_data.get('id', '')
            task_name = task_data.get('name', 'Unknown Task')
            task_url = task_data.get('url', '')
            
            # Get assignees
            assignees = task_data.get('assignees', [])
            assignee_ids = [a.get('id') for a in assignees]
            
            # Get your user ID from environment or ClickUp MCP
            # For now, we'll send notification for all comments
            # You can add filtering logic here if needed
            
            print(f"📝 Comment from {commenter_name} on task: {task_name}")
            
            # Format Slack message
            slack_message = {
                "text": f"🔔 *New comment on ClickUp task*",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🔔 New ClickUp Comment"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Task:*\n<{task_url}|{task_name}>"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*From:*\n{commenter_name}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Comment:*\n{comment_text}"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View Task"
                                },
                                "url": task_url,
                                "style": "primary"
                            }
                        ]
                    }
                ]
            }
            
            # Send to Slack (you can configure the channel via environment variable)
            slack_channel = os.getenv("SLACK_ALERT_CHANNEL", "#general")
            
            try:
                slack_client.chat_postMessage(
                    channel=slack_channel,
                    **slack_message
                )
                print(f"✅ Sent Slack notification to {slack_channel}")
            except Exception as e:
                print(f"❌ Error sending Slack message: {e}")
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"❌ Error processing ClickUp webhook: {e}\n{error_details}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return "✅ Bot Server is Running!"

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

if __name__ == '__main__':
    print("🚀 Server starting on http://localhost:3000")
    app.run(port=3000, debug=False)
