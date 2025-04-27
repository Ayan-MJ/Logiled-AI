"""
News scraping module for LogiLead AI.

This module contains functions to scrape industry news from various sources
using the NewsAPI.org service.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get NewsAPI key from environment variable
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
if not NEWS_API_KEY:
    logger.warning("NEWS_API_KEY not found in environment variables")

# Get industry keywords from environment variable
NEWS_KEYWORDS = os.getenv("NEWS_KEYWORDS", "FMCG,Pharma,Logistics").split(",")
if not NEWS_KEYWORDS:
    logger.warning("No NEWS_KEYWORDS found, using defaults")

# Expansion verbs that indicate business growth
EXPANSION_VERBS = [
    "expanding", "opening", "launching", "investment", "growth", 
    "acquisition", "merger", "partnership", "contract", "tender", 
    "development", "building", "constructing", "scaling"
]


def fetch_news_from_api(days: int = 1, 
                        max_results: int = 100) -> List[Dict]:
    """
    Fetch news articles from NewsAPI.org for the specified time period.

    Args:
        days: Number of days in the past to fetch news for (default: 1)
        max_results: Maximum number of results to fetch (default: 100)

    Returns:
        List[Dict]: A list of dictionaries containing news articles
    """
    if not NEWS_API_KEY:
        logger.error("Cannot fetch news: NEWS_API_KEY is not set")
        return []

    # Calculate the date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Format dates for the API
    from_date = start_date.strftime('%Y-%m-%d')
    to_date = end_date.strftime('%Y-%m-%d')
    
    # NewsAPI endpoint
    url = "https://newsapi.org/v2/everything"
    
    # Build a query for industry keywords
    # Join keywords with OR operator for the API
    query = " OR ".join(NEWS_KEYWORDS)
    
    # Set up parameters
    params = {
        'q': query,
        'from': from_date,
        'to': to_date,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': min(max_results, 100),  # API limits to 100 per page
        'apiKey': NEWS_API_KEY
    }
    
    articles = []
    
    try:
        logger.info(f"Fetching news articles from {from_date} to {to_date}")
        response = requests.get(url, params=params, timeout=30)
        
        # Check response
        response.raise_for_status()
        data = response.json()
        
        # Extract articles
        if 'articles' in data:
            articles = data['articles']
            logger.info(f"Fetched {len(articles)} news articles")
        else:
            logger.warning("No 'articles' field in NewsAPI response")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching news from NewsAPI: {e}")
        # Retry once
        try:
            logger.info("Retrying after 5 seconds...")
            import time
            time.sleep(5)
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if 'articles' in data:
                articles = data['articles']
                logger.info(f"Retry successful, fetched {len(articles)} news articles")
        except requests.exceptions.RequestException as retry_e:
            logger.error(f"Retry failed: {retry_e}")
    
    return articles


def filter_industry_news(articles: List[Dict]) -> List[Dict]:
    """
    Filter articles to find those related to industry expansion.
    
    This function looks for articles whose title or description contains
    both an industry keyword and an expansion verb.
    
    Args:
        articles: List of article dictionaries from NewsAPI
        
    Returns:
        List[Dict]: Filtered and normalized article dictionaries
    """
    filtered_articles = []
    
    logger.info(f"Filtering {len(articles)} articles for industry expansion news")
    
    for article in articles:
        # Get title and description, defaulting to empty string if not present
        title = article.get('title', '').lower()
        description = article.get('description', '').lower() if article.get('description') else ''
        
        # Check if the article contains any industry keyword
        has_industry_keyword = any(keyword.lower() in title or keyword.lower() in description 
                                   for keyword in NEWS_KEYWORDS)
        
        # Check if the article contains any expansion verb
        has_expansion_verb = any(verb.lower() in title or verb.lower() in description 
                                 for verb in EXPANSION_VERBS)
        
        # Only include articles with both an industry keyword and an expansion verb
        if has_industry_keyword and has_expansion_verb:
            # Normalize the article data
            filtered_article = {
                'source': article.get('source', {}).get('name', 'Unknown'),
                'title': article.get('title', 'No Title'),
                'url': article.get('url', ''),
                'published_at': article.get('publishedAt', ''),
                'snippet': article.get('description', 'No description available'),
                'fetched_at': datetime.now().isoformat()
            }
            
            filtered_articles.append(filtered_article)
    
    logger.info(f"Found {len(filtered_articles)} relevant industry expansion news articles")
    
    return filtered_articles


def fetch_industry_news(days: int = 1) -> List[Dict]:
    """
    Fetch and filter industry news about expansion, openings, and launches.
    
    Args:
        days: Number of days in the past to fetch news for (default: 1)
        
    Returns:
        List[Dict]: A list of dictionaries containing filtered news articles with keys:
            - source: The name of the news source
            - title: The article title
            - url: The URL to the article
            - published_at: When the article was published
            - snippet: A short description or excerpt
            - fetched_at: Timestamp when the article was fetched (ISO format)
    """
    # Fetch raw articles from NewsAPI
    articles = fetch_news_from_api(days=days)
    
    # Filter articles for industry expansion news
    filtered_articles = filter_industry_news(articles)
    
    return filtered_articles


if __name__ == "__main__":
    # Test the news scraping
    news = fetch_industry_news()
    
    print(f"Found {len(news)} industry expansion news articles:")
    for i, article in enumerate(news):
        print(f"{i+1}. {article['title']} - {article['source']}")
        print(f"   {article['snippet']}")
        print(f"   Published: {article['published_at']}")
        print(f"   URL: {article['url']}")
        print("-" * 80)
