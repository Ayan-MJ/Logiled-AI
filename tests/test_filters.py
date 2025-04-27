"""
Tests for the lead filtering module.
"""

import os
import pytest
from unittest.mock import patch

from logilead.filters import (
    contains_any_term,
    filter_news_lead,
    filter_job_lead,
    tag_lead,
    filter_leads,
    KEY_TERMS,
    JOB_TITLES
)


@pytest.fixture
def sample_news_leads():
    """
    Fixture that provides sample news leads.
    """
    return [
        {
            'title': 'Logistics Company Expanding Operations',
            'snippet': 'A major logistics provider is expanding in Mumbai.',
            'url': 'https://example.com/news1',
            'source': 'Example News',
            'published_at': '2025-04-26'
        },
        {
            'title': 'New Warehouse Facility Opens',
            'snippet': 'A new state-of-the-art warehouse facility has opened.',
            'url': 'https://example.com/news2',
            'source': 'Example News',
            'published_at': '2025-04-25'
        },
        {
            'title': 'Regular News Without Keywords',
            'snippet': 'This is a news article without any relevant keywords.',
            'url': 'https://example.com/news3',
            'source': 'Example News',
            'published_at': '2025-04-24'
        },
        {
            'title': 'Tech News',
            'snippet': 'New technology developments in the logistics sector.',
            'url': 'https://example.com/news4',
            'source': 'Example News',
            'published_at': '2025-04-23'
        }
    ]


@pytest.fixture
def sample_job_leads():
    """
    Fixture that provides sample job leads.
    """
    return [
        {
            'job_title': 'Logistics Manager',
            'company_name': 'ABC Logistics',
            'location': 'Mumbai',
            'published_at': '2025-04-26',
            'url': 'https://example.com/job1'
        },
        {
            'job_title': 'Senior Warehouse Supervisor',
            'company_name': 'XYZ Warehousing',
            'location': 'Delhi',
            'published_at': '2025-04-25',
            'url': 'https://example.com/job2'
        },
        {
            'job_title': 'Software Developer',
            'company_name': 'Tech Company',
            'location': 'Bangalore',
            'published_at': '2025-04-24',
            'url': 'https://example.com/job3'
        },
        {
            'job_title': 'Assistant to the Logistics Manager',
            'company_name': 'DEF Shipping',
            'location': 'Pune',
            'published_at': '2025-04-23',
            'url': 'https://example.com/job4'
        }
    ]


@pytest.fixture
def mock_env_vars():
    """
    Fixture that sets up mock environment variables.
    """
    original_env = os.environ.copy()
    os.environ['KEY_TERMS'] = 'logistics,warehouse,C&F'
    os.environ['JOB_TITLES'] = 'Logistics Manager,Warehouse Supervisor'
    yield
    os.environ.clear()
    os.environ.update(original_env)


def test_contains_any_term():
    """
    Test the contains_any_term function for text matching.
    """
    # Test basic matching
    assert contains_any_term("This text contains logistics information", ["logistics"])
    assert contains_any_term("Warehouse operations", ["warehouse"])
    
    # Test case insensitivity
    assert contains_any_term("LOGISTICS center", ["logistics"])
    assert contains_any_term("WaReHoUsE facility", ["warehouse"])
    
    # Test partial word matching
    assert contains_any_term("Logistical operations", ["logistic"])
    
    # Test multiple terms
    assert contains_any_term("Supply chain management", ["supply", "chain"])
    
    # Test non-matching
    assert not contains_any_term("Regular text", ["logistics", "warehouse"])
    
    # Test edge cases
    assert not contains_any_term("", ["logistics"])
    assert not contains_any_term("Some text", [])
    assert not contains_any_term("", [])


def test_filter_news_lead(mock_env_vars):
    """
    Test the filter_news_lead function.
    """
    # Should match on title
    assert filter_news_lead({'title': 'Logistics News', 'snippet': 'General info'})
    
    # Should match on snippet
    assert filter_news_lead({'title': 'Business News', 'snippet': 'Updates on warehouse operations'})
    
    # Should match case-insensitive
    assert filter_news_lead({'title': 'LOGISTICS Update', 'snippet': 'General info'})
    
    # Should not match without keywords
    assert not filter_news_lead({'title': 'General News', 'snippet': 'Business updates'})
    
    # Should handle missing fields
    assert not filter_news_lead({'title': 'Logistics News'})
    assert not filter_news_lead({'snippet': 'Logistics updates'})
    assert not filter_news_lead({})


def test_filter_job_lead(mock_env_vars):
    """
    Test the filter_job_lead function.
    """
    # Should match exact job title
    assert filter_job_lead({'job_title': 'Logistics Manager'})
    
    # Should match case-insensitive
    assert filter_job_lead({'job_title': 'LOGISTICS MANAGER'})
    
    # Should match title containing target job title
    assert filter_job_lead({'job_title': 'Senior Logistics Manager'})
    
    # Should not match without job title keywords
    assert not filter_job_lead({'job_title': 'Software Developer'})
    
    # Should handle missing fields
    assert not filter_job_lead({})
    assert not filter_job_lead({'company_name': 'Logistics Company'})


def test_tag_lead():
    """
    Test the tag_lead function.
    """
    lead = {'title': 'Test Lead', 'content': 'Test content'}
    
    # Test tagging with different types
    tagged_news = tag_lead(lead, 'news')
    assert tagged_news['lead_type'] == 'news'
    assert tagged_news['title'] == 'Test Lead'
    
    tagged_job = tag_lead(lead, 'job')
    assert tagged_job['lead_type'] == 'job'
    assert tagged_job['title'] == 'Test Lead'
    
    # Make sure original dict is not modified
    assert 'lead_type' not in lead


def test_filter_leads_news(sample_news_leads, mock_env_vars):
    """
    Test filtering news leads.
    """
    filtered = filter_leads(sample_news_leads, 'news')
    
    # We expect 3 of the 4 sample news leads to match
    assert len(filtered) == 3
    
    # Check that each matching lead has been tagged
    for lead in filtered:
        assert lead['lead_type'] == 'news'
    
    # Check that specific leads were filtered correctly
    titles = [lead['title'] for lead in filtered]
    assert 'Logistics Company Expanding Operations' in titles
    assert 'New Warehouse Facility Opens' in titles
    assert 'Tech News' in titles  # Contains "logistics" in snippet
    assert 'Regular News Without Keywords' not in titles


def test_filter_leads_jobs(sample_job_leads, mock_env_vars):
    """
    Test filtering job leads.
    """
    filtered = filter_leads(sample_job_leads, 'job')
    
    # We expect 3 of the 4 sample job leads to match
    assert len(filtered) == 3
    
    # Check that each matching lead has been tagged
    for lead in filtered:
        assert lead['lead_type'] == 'job'
    
    # Check that specific leads were filtered correctly
    titles = [lead['job_title'] for lead in filtered]
    assert 'Logistics Manager' in titles
    assert 'Senior Warehouse Supervisor' in titles
    assert 'Assistant to the Logistics Manager' in titles
    assert 'Software Developer' not in titles


def test_filter_leads_unknown_type(sample_news_leads):
    """
    Test filtering with an unknown lead type.
    """
    filtered = filter_leads(sample_news_leads, 'unknown')
    
    # Unknown lead type should return empty list
    assert filtered == []
    assert len(filtered) == 0


def test_filter_leads_empty_input():
    """
    Test filtering with empty input.
    """
    assert filter_leads([], 'news') == []
    assert filter_leads(None, 'job') == []


def test_key_terms_and_job_titles(mock_env_vars):
    """
    Test that KEY_TERMS and JOB_TITLES are correctly loaded.
    """
    # Re-import to refresh environment variables
    from logilead.filters import KEY_TERMS, JOB_TITLES
    
    # Check KEY_TERMS
    assert isinstance(KEY_TERMS, list)
    assert len(KEY_TERMS) == 3
    assert 'logistics' in KEY_TERMS
    assert 'warehouse' in KEY_TERMS
    assert 'c&f' in KEY_TERMS  # Should be lowercase
    
    # Check JOB_TITLES
    assert isinstance(JOB_TITLES, list)
    assert len(JOB_TITLES) == 2
    assert 'logistics manager' in JOB_TITLES  # Should be lowercase
    assert 'warehouse supervisor' in JOB_TITLES  # Should be lowercase
