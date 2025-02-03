from flask import Flask, render_template, request, jsonify, send_file, Response
import requests
from bs4 import BeautifulSoup
import csv
import json
import logging
from io import StringIO, BytesIO
from urllib.parse import urljoin, urlparse
from datetime import datetime
from functools import wraps
import time
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import validators
import re  # Import regex for date patterns

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per minute"]
)

# Configure cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# In-memory storage
scraped_data = []

def validate_url(url):
    """Validate URL format and accessibility"""
    if not validators.url(url):
        return False, "Invalid URL format"
    try:
        response = requests.head(url, timeout=5)
        return True, None
    except:
        return False, "URL is not accessible"

def extract_date(soup, url):
    """
    Extract the publication date of an article from common meta tags and HTML structures.
    Returns the date in 'YYYY-MM-DD' format or 'Unknown' if no date is found.
    """
    # Common meta tags for publication dates
    meta_tags = [
        {"property": "article:published_time"},
        {"property": "article:modified_time"},
        {"name": "date"},
        {"name": "pubdate"},
        {"name": "lastmod"},
        {"itemprop": "datePublished"},
        {"itemprop": "dateModified"},
        {"name": "DC.date.issued"},
        {"name": "DC.date.created"},
        {"name": "sailthru.date"},
        {"name": "PublishDate"},
        {"name": "pub-date"},
        {"name": "publish-date"},
    ]

    # Check meta tags first
    for meta in meta_tags:
        date_meta = soup.find("meta", meta)
        if date_meta and date_meta.get("content"):
            date_str = date_meta["content"]
            try:
                # Handle ISO format (e.g., "2023-10-05T12:34:56Z")
                if 'T' in date_str:
                    date = datetime.fromisoformat(date_str.split('T')[0])
                else:
                    # Handle other formats (e.g., "2023-10-05")
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                return date.strftime("%Y-%m-%d")
            except ValueError:
                continue

    # Check <time> tags
    time_tag = soup.find('time')
    if time_tag and time_tag.get('datetime'):
        date_str = time_tag['datetime']
        try:
            if 'T' in date_str:
                date = datetime.fromisoformat(date_str.split('T')[0])
            else:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            return date.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Check JSON-LD structured data
    script_tags = soup.find_all('script', type='application/ld+json')
    for script in script_tags:
        try:
            json_data = json.loads(script.string)
            if isinstance(json_data, dict):
                date_published = json_data.get("datePublished") or json_data.get("dateCreated")
                if date_published:
                    if 'T' in date_published:
                        date = datetime.fromisoformat(date_published.split('T')[0])
                    else:
                        date = datetime.strptime(date_published, '%Y-%m-%d')
                    return date.strftime("%Y-%m-%d")
        except (json.JSONDecodeError, ValueError):
            continue

    # Check Open Graph tags
    og_date = soup.find("meta", property="og:published_time")
    if og_date and og_date.get("content"):
        date_str = og_date["content"]
        try:
            if 'T' in date_str:
                date = datetime.fromisoformat(date_str.split('T')[0])
            else:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            return date.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Fallback: Look for date-like strings in the article body
    date_patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
        r'\b\d{2}/\d{2}/\d{4}\b',  # MM/DD/YYYY
        r'\b\d{2}-\d{2}-\d{4}\b',  # DD-MM-YYYY
    ]

    for pattern in date_patterns:
        date_match = soup.find(string=re.compile(pattern))
        if date_match:
            date_str = date_match.strip()
            try:
                if '-' in date_str:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                elif '/' in date_str:
                    date = datetime.strptime(date_str, '%m/%d/%Y')
                return date.strftime("%Y-%m-%d")
            except ValueError:
                continue

    # If no date is found, return 'Unknown'
    return "Unknown"

def find_articles(soup, base_url):
    """Find articles using multiple selectors and patterns"""
    articles = []
    seen_urls = set()  # Track seen URLs to avoid duplicates
    
    # Common article containers
    article_selectors = [
        'article',
        '.article',
        '.post',
        '.entry',
        'div[class*="article"]',
        'div[class*="post"]',
        '.story',
        '.news-item'
    ]
    
    # Try each selector
    for selector in article_selectors:
        items = soup.select(selector)
        if items:
            for item in items:
                article = extract_article_info(item, base_url)
                if article and article['url'] not in seen_urls:
                    articles.append(article)
                    seen_urls.add(article['url'])
            if articles:
                break
    
    # Fallback to headings if no articles found
    if not articles:
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            article = extract_article_info(heading, base_url)
            if article and article['url'] not in seen_urls:
                articles.append(article)
                seen_urls.add(article['url'])
    
    return articles

def extract_article_info(element, base_url):
    """Extract title and URL from an article element"""
    # Find title
    title_element = element.find(['h1', 'h2', 'h3', 'h4']) or element
    if not title_element:
        return None
    
    title = title_element.get_text(strip=True)
    if not title:
        return None
    
    # Find URL
    link = (
        element.find('a') or 
        title_element.find('a') or 
        title_element.find_parent('a')
    )
    
    url = None
    if link and link.get('href'):
        url = urljoin(base_url, link['href'])
    
    if not url:
        return None
    
    return {
        'title': title,
        'url': url
    }

@app.route('/')
def index():
    return render_template('index.html', data=scraped_data)

@app.route('/get-data')
def get_data():
    return jsonify(scraped_data)

@app.route('/scrape', methods=['POST'])
@limiter.limit("10 per minute")
def scrape():
    url = request.form.get('url', '').strip()
    
    # Validate URL
    is_valid, error_message = validate_url(url)
    if not is_valid:
        return jsonify({"error": error_message}), 400
    
    try:
        # Check cache first
        cached_data = cache.get(url)
        if cached_data:
            return jsonify(cached_data)
        
        # Make request with timeout
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract articles
        articles = find_articles(soup, url)
        
        if not articles:
            return jsonify({"error": "No articles found on this page. The link may not be an article or the website structure is not supported."}), 404
        
        # Add publication date to each article
        for article in articles:
            article['date'] = extract_date(soup, url)
        
        # Update global scraped_data atomically
        global scraped_data
        scraped_data = articles
        
        # Cache the results
        cache.set(url, articles, timeout=300)  # Cache for 5 minutes
        
        return jsonify(articles)
        
    except requests.Timeout:
        logger.error(f"Request timed out for URL: {url}")
        return jsonify({"error": "Request timed out. Please try again later."}), 408
    except requests.RequestException as e:
        logger.error(f"Scraping error for URL {url}: {str(e)}")
        return jsonify({"error": "Failed to fetch the webpage. Please ensure the URL is correct and accessible."}), 500
    except Exception as e:
        logger.error(f"Unexpected error for URL {url}: {str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

@app.route('/delete/<int:index>', methods=['POST'])
def delete(index):
    try:
        global scraped_data
        if 0 <= index < len(scraped_data):
            del scraped_data[index]
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Item not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting item: {str(e)}")
        return jsonify({"error": "Failed to delete item"}), 500

@app.route('/refresh', methods=['POST'])
def refresh():
    global scraped_data
    scraped_data = []
    cache.clear()  # Clear cache to ensure consistency
    return jsonify({"success": True})

@app.route('/export/<format>')
def export(format):
    if not scraped_data:
        return jsonify({"error": "No data to export"}), 400
        
    try:
        if format == 'csv':
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=["title", "url", "date"])
            writer.writeheader()
            writer.writerows(scraped_data)
            output.seek(0)
            
            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={
                    "Content-Disposition": f"attachment;filename=scraped_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )

        elif format == 'json':
            output = BytesIO()
            formatted_json = json.dumps(
                scraped_data,
                indent=2,
                ensure_ascii=False
            ).encode('utf-8')
            output.write(formatted_json)
            output.seek(0)
            
            return send_file(
                output,
                mimetype="application/json",
                as_attachment=True,
                download_name=f"scraped_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

        return jsonify({"error": "Invalid format"}), 400
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({"error": "Export failed"}), 500

if __name__ == '__main__':
    app.run(debug=True)