#!/usr/bin/env python3
"""
Content Analyzer - Extract SEO insights from competitor articles

Analyzes webpage content to provide insights for SEOmonitor Content Writer users:
- Word count, reading time, content structure
- Heading hierarchy (H1, H2, H3)
- Keyword density and usage
- Meta tags and SEO elements
- Link analysis (internal/external)
- Image count and alt text usage
"""

import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
from urllib.parse import urlparse, urljoin
import json


def fetch_page(url):
    """Fetch webpage content."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        raise Exception(f"Failed to fetch {url}: {str(e)}")


def extract_text_content(soup):
    """Extract clean text content from page."""
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "header", "footer"]):
        script.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text


def count_words(text):
    """Count words in text."""
    words = re.findall(r'\b\w+\b', text.lower())
    return len(words)


def estimate_reading_time(word_count):
    """Estimate reading time (average 200 words/min)."""
    minutes = word_count / 200
    return round(minutes)


def extract_headings(soup):
    """Extract all headings with hierarchy."""
    headings = {
        'h1': [],
        'h2': [],
        'h3': [],
        'h4': []
    }
    
    for level in ['h1', 'h2', 'h3', 'h4']:
        for heading in soup.find_all(level):
            text = heading.get_text().strip()
            if text:
                headings[level].append(text)
    
    return headings


def extract_keywords(text, top_n=20):
    """Extract most common keywords from text."""
    # Common stop words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'as', 'is', 'was', 'are', 'been', 'be', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might',
        'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
        'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
        'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
        'very', 'just', 'with', 'from', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'up', 'down', 'out', 'off', 'over',
        'under', 'again', 'further', 'then', 'once'
    }
    
    # Extract words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out stop words and short words
    meaningful_words = [w for w in words if w not in stop_words and len(w) > 3]
    
    # Count occurrences
    word_counts = Counter(meaningful_words)
    
    return word_counts.most_common(top_n)


def extract_meta_tags(soup):
    """Extract important meta tags."""
    meta = {}
    
    # Title
    title_tag = soup.find('title')
    meta['title'] = title_tag.get_text() if title_tag else None
    meta['title_length'] = len(meta['title']) if meta['title'] else 0
    
    # Meta description
    desc_tag = soup.find('meta', attrs={'name': 'description'})
    if desc_tag:
        meta['description'] = desc_tag.get('content', '')
        meta['description_length'] = len(meta['description'])
    else:
        meta['description'] = None
        meta['description_length'] = 0
    
    # Open Graph tags
    og_title = soup.find('meta', property='og:title')
    meta['og_title'] = og_title.get('content') if og_title else None
    
    # Canonical URL
    canonical = soup.find('link', rel='canonical')
    meta['canonical'] = canonical.get('href') if canonical else None
    
    return meta


def analyze_links(soup, base_url):
    """Analyze internal and external links."""
    links = {'internal': 0, 'external': 0}
    base_domain = urlparse(base_url).netloc
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        
        # Make absolute URL
        absolute_url = urljoin(base_url, href)
        link_domain = urlparse(absolute_url).netloc
        
        if link_domain == base_domain or not link_domain:
            links['internal'] += 1
        else:
            links['external'] += 1
    
    return links


def analyze_images(soup):
    """Analyze images and alt text usage."""
    images = soup.find_all('img')
    total_images = len(images)
    images_with_alt = sum(1 for img in images if img.get('alt'))
    
    return {
        'total': total_images,
        'with_alt': images_with_alt,
        'alt_coverage': round((images_with_alt / total_images * 100) if total_images > 0 else 0)
    }


def detect_schema(soup):
    """Detect structured data/schema markup."""
    schemas = []
    
    # JSON-LD
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and '@type' in data:
                schemas.append(data['@type'])
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and '@type' in item:
                        schemas.append(item['@type'])
        except:
            pass
    
    return schemas


def analyze_content(url):
    """Main function to analyze webpage content."""
    
    print(f"\n🔍 Analyzing: {url}\n")
    
    # Fetch page
    html = fetch_page(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract content
    text_content = extract_text_content(soup)
    word_count = count_words(text_content)
    
    # Analysis
    results = {
        'url': url,
        'word_count': word_count,
        'reading_time': estimate_reading_time(word_count),
        'headings': extract_headings(soup),
        'keywords': extract_keywords(text_content),
        'meta': extract_meta_tags(soup),
        'links': analyze_links(soup, url),
        'images': analyze_images(soup),
        'schema': detect_schema(soup)
    }
    
    return results


def format_results_for_slack(results):
    """Format analysis results for Slack message."""
    
    meta = results['meta']
    headings = results['headings']
    images = results['images']
    links = results['links']
    
    # Title validation
    title_status = "✅" if 30 <= meta['title_length'] <= 60 else "⚠️"
    desc_status = "✅" if 120 <= meta['description_length'] <= 160 else "⚠️"
    
    message = f"""🎯 **Competitor Analysis: {results['url']}**

📊 **Content Metrics:**
• Word Count: {results['word_count']:,} words
• Reading Time: ~{results['reading_time']} min
• H1 Count: {len(headings['h1'])}
• H2 Count: {len(headings['h2'])}
• H3 Count: {len(headings['h3'])}
• Images: {images['total']} ({images['with_alt']} with alt text - {images['alt_coverage']}%)
• Internal Links: {links['internal']}
• External Links: {links['external']}

🏗️ **Content Structure:**"""
    
    # Show H1
    if headings['h1']:
        message += f"\nH1: \"{headings['h1'][0]}\""
    
    # Show first 5 H2s
    if headings['h2']:
        message += "\n\nKey H2 Headings:"
        for i, h2 in enumerate(headings['h2'][:5], 1):
            message += f"\n  {i}. {h2}"
        if len(headings['h2']) > 5:
            message += f"\n  ... and {len(headings['h2']) - 5} more"
    
    # Top keywords
    message += "\n\n🔑 **Top Keywords:**"
    for word, count in results['keywords'][:10]:
        message += f"\n• \"{word}\" ({count} times)"
    
    # SEO Elements
    message += f"\n\n📝 **SEO Elements:**"
    message += f"\n• Title: \"{meta['title']}\" ({meta['title_length']} chars) {title_status}"
    if meta['description']:
        message += f"\n• Meta Desc: \"{meta['description'][:80]}...\" ({meta['description_length']} chars) {desc_status}"
    else:
        message += f"\n• Meta Desc: ❌ Missing"
    
    if results['schema']:
        message += f"\n• Schema: {', '.join(results['schema'])} ✅"
    else:
        message += f"\n• Schema: ❌ None detected"
    
    return message


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 content_analyzer.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    try:
        results = analyze_content(url)
        print(format_results_for_slack(results))
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
