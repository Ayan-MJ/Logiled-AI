"""
Tests for the news scraper module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from logilead.news_scraper import (
    fetch_news_from_api,
    filter_industry_news,
    fetch_industry_news,
    NEWS_KEYWORDS,
    EXPANSION_VERBS
)


@pytest.fixture
def mock_news_response():
    """
    Fixture that returns a mock news API response.
    """
    return {
        'status': 'ok',
        'totalResults': 3,
        'articles': [
            {
                'source': {'id': 'test-source-1', 'name': 'Test Source 1'},
                'author': 'Author 1',
                'title': 'Pharma Company Expanding Operations in Mumbai',
                'description': 'A leading pharmaceutical company is expanding its operations in Mumbai.',
                'url': 'https://example.com/article1',
                'urlToImage': 'https://example.com/image1.jpg',
                'publishedAt': '2025-04-26T10:00:00Z',
                'content': 'Full content of article 1'
            },
            {
                'source': {'id': 'test-source-2', 'name': 'Test Source 2'},
                'author': 'Author 2',
                'title': 'Tech Company Releases New Product',
                'description': 'A tech company has released a new product.',
                'url': 'https://example.com/article2',
                'urlToImage': 'https://example.com/image2.jpg',
                'publishedAt': '2025-04-26T11:00:00Z',
                'content': 'Full content of article 2'
            },
            {
                'source': {'id': 'test-source-3', 'name': 'Test Source 3'},
                'author': 'Author 3',
                'title': 'FMCG Company Launching New Brand',
                'description': 'An FMCG company is launching a new brand in the market.',
                'url': 'https://example.com/article3',
                'urlToImage': 'https://example.com/image3.jpg',
                'publishedAt': '2025-04-26T12:00:00Z',
                'content': 'Full content of article 3'
            }
        ]
    }


@pytest.fixture
def mock_env_vars():
    """
    Fixture that sets up mock environment variables.
    """
    original_env = os.environ.copy()
    os.environ['NEWS_API_KEY'] = 'test-api-key'
    os.environ['NEWS_KEYWORDS'] = 'FMCG,Pharma,Logistics'
    yield
    os.environ.clear()
    os.environ.update(original_env)


def test_fetch_news_from_api(mock_env_vars):
    """
    Test that fetch_news_from_api makes the correct API call and processes the response.
    """
    with patch('logilead.news_scraper.requests.get') as mock_get:
        # Configure the mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': 'ok',
            'totalResults': 2,
            'articles': [
                {'title': 'Article 1', 'source': {'name': 'Source 1'}},
                {'title': 'Article 2', 'source': {'name': 'Source 2'}}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call the function
        articles = fetch_news_from_api()
        
        # Verify the results
        assert len(articles) == 2
        assert articles[0]['title'] == 'Article 1'
        assert articles[1]['title'] == 'Article 2'
        
        # Verify the API call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == 'https://newsapi.org/v2/everything'
        assert 'apiKey' in kwargs['params']
        assert kwargs['params']['apiKey'] == 'test-api-key'
        assert 'q' in kwargs['params']
        assert all(keyword in kwargs['params']['q'] for keyword in ['FMCG', 'Pharma', 'Logistics'])


def test_filter_industry_news(mock_news_response):
    """
    Test that filter_industry_news correctly filters articles
    based on industry keywords and expansion verbs.
    """
    # Call the function with mock articles
    filtered = filter_industry_news(mock_news_response['articles'])
    
    # We expect 2 articles to match (the Pharma expansion and FMCG launch)
    assert len(filtered) == 2
    
    # Check that the correct articles were filtered
    titles = [article['title'] for article in filtered]
    assert 'Pharma Company Expanding Operations in Mumbai' in titles
    assert 'FMCG Company Launching New Brand' in titles
    assert 'Tech Company Releases New Product' not in titles
    
    # Check that the article data is normalized correctly
    assert 'source' in filtered[0]
    assert 'title' in filtered[0]
    assert 'url' in filtered[0]
    assert 'published_at' in filtered[0]
    assert 'snippet' in filtered[0]
    assert 'fetched_at' in filtered[0]


def test_fetch_industry_news():
    """
    Test that fetch_industry_news calls the API and filters the results.
    """
    with patch('logilead.news_scraper.fetch_news_from_api') as mock_fetch:
        with patch('logilead.news_scraper.filter_industry_news') as mock_filter:
            # Configure the mocks
            mock_fetch.return_value = [{'title': 'Test Article'}]
            mock_filter.return_value = [{'title': 'Filtered Article'}]
            
            # Call the function
            result = fetch_industry_news(days=2)
            
            # Verify the mocks were called correctly
            mock_fetch.assert_called_once_with(days=2)
            mock_filter.assert_called_once_with([{'title': 'Test Article'}])
            
            # Verify the result
            assert result == [{'title': 'Filtered Article'}]


def test_news_keywords_and_expansion_verbs():
    """
    Test that the predefined keywords and verbs are set up correctly.
    """
    # Check that NEWS_KEYWORDS contains expected values
    assert isinstance(NEWS_KEYWORDS, list)
    assert len(NEWS_KEYWORDS) > 0
    
    # Check that EXPANSION_VERBS contains expected values
    assert isinstance(EXPANSION_VERBS, list)
    assert len(EXPANSION_VERBS) > 0
    assert "expanding" in EXPANSION_VERBS
    assert "opening" in EXPANSION_VERBS
    assert "launching" in EXPANSION_VERBS
