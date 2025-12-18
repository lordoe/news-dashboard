import json
import os
import time
import feedparser
import google.generativeai as genai
import markdown
from flask import Flask, render_template, request, jsonify
from email.utils import parsedate_to_datetime
from datetime import datetime

app = Flask(__name__)

# --- KONFIGURATION ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNUNG: Kein GEMINI_API_KEY gesetzt. KI-Features werden nicht funktionieren.")
CONFIG_FILE = "config.json"
CACHE_FILE = "cache.json"

def load_config():
    """Lädt die Konfiguration aus der JSON-Datei."""
    if not os.path.exists(CONFIG_FILE):
        return {"topics": []}
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    """Speichert die Konfiguration in die JSON-Datei."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def load_cache():
    """Lädt den Cache aus der JSON-Datei."""
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_cache(cache):
    """Speichert den Cache in die JSON-Datei."""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=4, ensure_ascii=False)

# --- ARCHIV KONFIGURATION ---
# ... (rest of file)

def get_gemini_summary(topic_name, news_items, force_refresh=False):
    """Lässt Gemini eine Zusammenfassung der Schlagzeilen erstellen (mit Caching)."""
    # 1. Check Cache
    cache = load_cache()
    cached_data = cache.get(topic_name)
    current_time = time.time()
    
    # Cache valid for 12 hours (12 * 60 * 60 = 43200 seconds)
    if not force_refresh and cached_data and (current_time - cached_data.get('timestamp', 0)) < 43200:
        return cached_data.get('summary')

    # 2. Call API if no cache or expired
    try:
        headlines = "\n".join([f"- {item['title']}" for item in news_items])
        prompt = (
            f"Hier sind die aktuellen Schlagzeilen zum Thema '{topic_name}':\n{headlines}\n\n"
            f"Bitte schreibe eine kurze, prägnante Zusammenfassung (max. 3 Sätze) über die aktuelle Lage "
            f"in diesem Themenbereich auf Deutsch. Sei informativ und direkt."
        )
        response = model.generate_content(prompt)
        summary = markdown.markdown(response.text)
        
        # 3. Save to Cache
        cache[topic_name] = {
            "summary": summary,
            "timestamp": current_time
        }
        save_cache(cache)
        
        return summary
    except Exception as e:
        return f"KI-Zusammenfassung konnte nicht geladen werden. ({e})"
ARCHIVE_FILE = "archive.json"

def load_archive():
    """Lädt das Archiv aus der JSON-Datei."""
    if not os.path.exists(ARCHIVE_FILE):
        return []
    with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_archive(archive):
    """Speichert das Archiv in die JSON-Datei."""
    with open(ARCHIVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(archive, f, indent=4, ensure_ascii=False)

# Gemini konfigurieren
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_news_from_rss(query, count=5, period="1d", language="de", region="DE"):
    """Holt die neusten Schlagzeilen via Google News RSS (zuverlässig & schnell)."""
    # URL encoded query für Google News
    # Add 'when:...' to force recency
    encoded_query = query.replace(" ", "%20") + f"+when:{period}"
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={language}&gl={region}&ceid={region}:{language}"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    for entry in feed.entries[:count]:
        news_items.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published,
            "source": entry.source.title if 'source' in entry else "News"
        })
    return news_items


@app.route('/')
def home():
    """Rendert nur das Grundgerüst, Daten werden per AJAX nachgeladen."""
    config = load_config()
    archive = load_archive()
    # Wir übergeben nur die Topics-Metadaten und die IDs der gespeicherten Artikel für das UI
    saved_links = [item['link'] for item in archive]
    return render_template('index.html', config=config, saved_links=saved_links)

@app.route('/api/get_topic_data', methods=['POST'])
def api_get_topic_data():
    """Holt Nachrichten und KI-Zusammenfassung für ein einzelnes Thema."""
    data = request.json
    topic_name = data.get('name')
    query = data.get('query')
    try:
        count = int(data.get('count', 5))
    except (ValueError, TypeError):
        count = 5
    
    use_ai = data.get('ai', True)
    force_refresh = data.get('refresh', False)
    save_ai = data.get('save_ai', False)

    # Load config to get global settings
    config = load_config()
    settings = config.get('settings', {'scraping_period': '1d', 'language': 'de', 'region': 'DE'})
    period = settings.get('scraping_period', '1d')
    language = settings.get('language', 'de')
    region = settings.get('region', 'DE')

    # Update Config if requested
    if save_ai:
        # config is already loaded
        for topic in config['topics']:
            if topic['name'] == topic_name:
                topic['ai'] = True
                break
        save_config(config)
    
    if query:
        articles = get_news_from_rss(query, count, period, language, region)
    else:
        articles = []
    summary = ""
    if articles and use_ai:
        summary = get_gemini_summary(topic_name, articles, force_refresh=force_refresh)
        
    return jsonify({
        "articles": articles,
        "summary": summary
    })

@app.route('/archive')
def archive_page():
    archive = load_archive()
    
    # Helper to parse RSS date safely
    def parse_date(item):
        try:
            return parsedate_to_datetime(item.get('published', ''))
        except:
            return datetime.min

    # Sort by Date (Newest first) - Primary for within topic
    archive.sort(key=parse_date, reverse=True)
    
    # Sort by Topic (A-Z) - Primary overall (stable sort preserves date order)
    archive.sort(key=lambda x: x.get('topic', 'Z_Uncategorized').lower())
    
    # Generate deterministic colors for topics
    colors = ['bg-primary', 'bg-success', 'bg-danger', 'bg-warning text-dark', 'bg-info text-dark', 'bg-secondary']
    topic_colors = {}
    
    for item in archive:
        topic = item.get('topic', 'Unbekannt')
        if topic not in topic_colors:
            # Simple deterministic hash: sum of char codes modulo color count
            idx = sum(ord(c) for c in topic) % len(colors)
            topic_colors[topic] = colors[idx]
            
    return render_template('archive.html', archive=archive, topic_colors=topic_colors)

@app.route('/api/archive/add', methods=['POST'])
def api_archive_add():
    article = request.json
    archive = load_archive()
    
    # Check duplicate by link
    if not any(a['link'] == article['link'] for a in archive):
        archive.append(article)
        save_archive(archive)
        
    return jsonify({"status": "success", "message": "Artikel gespeichert."})

@app.route('/api/archive/remove', methods=['POST'])
def api_archive_remove():
    data = request.json
    link_to_remove = data.get('link')
    archive = load_archive()
    
    archive = [a for a in archive if a['link'] != link_to_remove]
    save_archive(archive)
    
    return jsonify({"status": "success", "message": "Artikel entfernt."})

@app.route('/api/save_config', methods=['POST'])
def api_save_config():
    try:
        new_config = request.json
        save_config(new_config)
        return jsonify({"status": "success", "message": "Konfiguration gespeichert."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



if __name__ == '__main__':
    # Host='0.0.0.0' macht die Seite im ganzen lokalen Netzwerk verfügbar
    app.run(debug=True, host='0.0.0.0', port=5000)
