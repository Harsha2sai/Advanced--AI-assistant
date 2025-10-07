# main/skills/web_services.py

import requests
import json
import logging
from bs4 import BeautifulSoup
import re
from datetime import datetime
import urllib.parse

logger = logging.getLogger(__name__)

class WebServices:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def _make_request(self, url, params=None, timeout=10):
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
# Global web service instance
web_service = WebServices()

def search_web(query: str) -> str:
    """Search the web using DuckDuckGo (no API key needed)"""
    try:
        # Method 1: Try DuckDuckGo instant answers
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_redirect': '1',
            'no_html': '1'
        }
        response = web_service._make_request(url, params)
        if response:
            data = response.json()
            
            # Check for instant answer
            if data.get('Answer'):
                return f"🔍 {query}:\n{data['Answer']}"
            elif data.get('AbstractText'):
                return f"🔍 {query}:\n{data['AbstractText'][:300]}..."
            elif data.get('Definition'):
                return f"🔍 {query}:\n{data['Definition'][:300]}..."
    
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
    
    # Method 2: Simple web search via scraping (fallback)
    try:
        search_url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        response = web_service._make_request(search_url)
        
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('a', class_='result__url')[:3]
            
            if results:
                search_results = []
                for result in results:
                    title = result.get_text(strip=True)
                    if title:
                        search_results.append(f"• {title}")
                
                if search_results:
                    return f"🔍 Search results for '{query}':\n" + "\n".join(search_results)
    
    except Exception as e:
        logger.error(f"Web search scraping failed: {e}")
    
    return f"🔍 Sorry, couldn't search for '{query}' right now. Please try again later."

def get_weather(location: str = "New York") -> str:
    """Get weather using free wttr.in service (no API key needed)"""
    try:
        if not location:
            location = "New York"
        
        # wttr.in provides weather in plain text format
        url = f"http://wttr.in/{location}?format=%l:+%C+%t+(feels+like+%f)+%h+humidity+%w+wind"
        
        response = web_service._make_request(url)
        if response and response.status_code == 200:
            weather_text = response.text.strip()
            if weather_text and "Unknown location" not in weather_text:
                return f"🌤️ Weather: {weather_text}"
    
    except Exception as e:
        logger.error(f"Weather request failed: {e}")
    
    return f"❌ Unable to get weather for {location}. Please try another location."

def get_news(query: str = "latest") -> str:
    """Get news from BBC RSS (free, no API key needed)"""
    try:
        # BBC World News RSS
        rss_url = "https://feeds.bbci.co.uk/news/world/rss.xml"
        
        response = web_service._make_request(rss_url)
        if response:
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:5]
            
            news_items = []
            for item in items:
                title = item.title.text if item.title else "No title"
                description = item.description.text if item.description else ""
                pub_date = item.pubDate.text if item.pubDate else "Recent"
                
                # Clean up HTML tags from description
                description = re.sub(r'<[^>]+>', '', description)
                if len(description) > 100:
                    description = description[:97] + "..."
                
                news_items.append(f"📰 {title}\n   BBC News | {pub_date[:16]}\n   {description}")
            
            if news_items:
                return f"📈 Latest News Headlines:\n\n" + "\n\n".join(news_items)
    
    except Exception as e:
        logger.error(f"News fetch failed: {e}")
    
    return "❌ Unable to fetch news right now. Please try again later."

def get_forex_news() -> str:
    """Get Forex Factory news (web scraping)"""
    try:
        url = "https://www.forexfactory.com/"
        
        response = web_service._make_request(url, timeout=15)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for news headlines
            news_elements = soup.find_all(['div', 'span', 'a'], class_=re.compile(r'news|headline|title'))
            
            forex_news = []
            for element in news_elements[:5]:
                text = element.get_text(strip=True)
                if text and len(text) > 20 and len(text) < 200:
                    # Filter out navigation and UI elements
                    if not any(skip in text.lower() for skip in ['login', 'register', 'menu', 'search', 'copyright']):
                        forex_news.append(f"📊 {text}")
            
            if forex_news:
                return f"💱 Forex Factory Updates:\n\n" + "\n\n".join(forex_news[:3])
    
    except Exception as e:
        logger.error(f"Forex Factory scraping failed: {e}")
    
    return "❌ Unable to fetch Forex Factory news. Please try again later."

def search_wikipedia(topic: str) -> str:
    """Search Wikipedia"""
    try:
        # Wikipedia API
        url = "https://en.wikipedia.org/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": topic,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "exsectionformat": "plain"
        }
        
        response = web_service._make_request(url, params)
        if response:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            
            for page_id, page in pages.items():
                if page_id != "-1":  # Page exists
                    title = page.get("title", topic)
                    extract = page.get("extract", "")
                    
                    if extract:
                        if len(extract) > 500:
                            extract = extract[:497] + "..."
                        
                        wiki_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                        return f"📖 Wikipedia - {title}:\n\n{extract}\n\nRead more: {wiki_url}"
    
    except Exception as e:
        logger.error(f"Wikipedia search failed: {e}")
    
    return f"❌ Unable to find Wikipedia article about '{topic}'."

def get_crypto_prices(symbols: str = "bitcoin") -> str:
    """Get crypto prices from CoinGecko (free API)"""
    try:
        if not symbols:
            symbols = "bitcoin"
        
        # CoinGecko free API
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": symbols.lower().replace(" ", ","),
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        
        response = web_service._make_request(url, params)
        if response:
            data = response.json()
            
            prices = []
            for crypto, price_data in data.items():
                price = price_data.get("usd", 0)
                change_24h = price_data.get("usd_24h_change", 0)
                
                change_emoji = "🔺" if change_24h > 0 else "🔻" if change_24h < 0 else "▶️"
                change_text = f"{change_24h:+.2f}%" if change_24h else "0.00%"
                
                crypto_name = crypto.replace("-", " ").title()
                prices.append(f"₿ {crypto_name}: ${price:,.2f} {change_emoji} {change_text}")
            
            if prices:
                return f"💰 Cryptocurrency Prices:\n\n" + "\n".join(prices)
    
    except Exception as e:
        logger.error(f"Crypto price fetch failed: {e}")
    
    return f"❌ Unable to fetch crypto prices for {symbols}."

# Placeholder functions for other services
def get_twitter_posts(query: str) -> str:
    # If not configured, return a graceful message
    return "🐦 Twitter integration requires API setup. Please configure Twitter Bearer Token."

def get_reddit_posts(subreddit: str) -> str:
    return f"🔴 Reddit integration requires API setup. Please configure Reddit credentials to browse r/{subreddit}."

def get_github_trending(language: str = "") -> str:
    return "🚀 GitHub trending requires API setup for full functionality."
