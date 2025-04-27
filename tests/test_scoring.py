"""
Tests for the lead scoring module.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from logilead.scoring import (
    count_term_matches,
    count_news_keywords,
    calculate_job_age_days,
    score_lead,
    assign_scores,
    KEY_TERMS
)


@pytest.fixture
def sample_leads():
    """
    Fixture that provides sample leads of different types.
    """
    today = datetime.now().date()
    yesterday = (today - timedelta(days=1)).isoformat()
    week_ago = (today - timedelta(days=7)).isoformat()
    month_ago = (today - timedelta(days=30)).isoformat()
    
    return [
        # Tender leads
        {
            'lead_type': 'tender',
            'title': 'Logistics Service Tender',
            'issuer': 'Government Agency',
            'deadline': '2025-05-15'
        },
        # News leads with varying keyword matches
        {
            'lead_type': 'news',
            'title': 'Logistics Company Expanding Operations',  # 1 match in title
            'snippet': 'New warehouse facility opening in Mumbai',  # 1 match in snippet
            'source': 'Business News'
        },
        {
            'lead_type': 'news',
            'title': 'Regular News Without Keywords',  # 0 matches in title
            'snippet': 'General business updates',  # 0 matches in snippet
            'source': 'General News'
        },
        {
            'lead_type': 'news',
            'title': 'Warehouse and Logistics Updates',  # 2 matches in title
            'snippet': 'C&F and freight developments',  # 1 match in snippet
            'source': 'Industry News'
        },
        # Job leads with different ages
        {
            'lead_type': 'job',
            'job_title': 'Logistics Manager',
            'company_name': 'ABC Logistics',
            'published_at': yesterday  # 1 day old
        },
        {
            'lead_type': 'job',
            'job_title': 'Warehouse Supervisor',
            'company_name': 'XYZ Warehousing',
            'published_at': week_ago  # 7 days old
        },
        {
            'lead_type': 'job',
            'job_title': 'Senior Logistics Manager',
            'company_name': 'Global Supply Chain',
            'published_at': month_ago  # 30 days old
        }
    ]


@pytest.fixture
def mock_env_vars():
    """
    Fixture that sets up mock environment variables.
    """
    original_env = os.environ.copy()
    os.environ['KEY_TERMS'] = 'logistics,warehouse,C&F'
    yield
    os.environ.clear()
    os.environ.update(original_env)


def test_count_term_matches():
    """
    Test counting term matches in text.
    """
    terms = ['apple', 'banana', 'orange']
    
    # Test basic matching
    assert count_term_matches("I like apples and bananas", terms) == 2
    
    # Test case insensitivity
    assert count_term_matches("I like APPLES and Bananas", terms) == 2
    
    # Test with no matches
    assert count_term_matches("I like grapes and pears", terms) == 0
    
    # Test with empty inputs
    assert count_term_matches("", terms) == 0
    assert count_term_matches("Some text", []) == 0
    assert count_term_matches("", []) == 0


def test_count_news_keywords(mock_env_vars):
    """
    Test counting keyword matches in news leads.
    """
    # Test with multiple matches
    news1 = {
        'title': 'Logistics Updates',  # 1 match
        'snippet': 'New warehouse facility opening'  # 1 match
    }
    assert count_news_keywords(news1) == 2
    
    # Test with no matches
    news2 = {
        'title': 'General News',
        'snippet': 'Business updates'
    }
    assert count_news_keywords(news2) == 0
    
    # Test with missing fields
    news3 = {
        'title': 'Logistics Updates'
    }
    assert count_news_keywords(news3) == 1
    
    news4 = {
        'snippet': 'Warehouse facility'
    }
    assert count_news_keywords(news4) == 1
    
    news5 = {}
    assert count_news_keywords(news5) == 0


def test_calculate_job_age_days():
    """
    Test calculating job posting age in days.
    """
    today = datetime.now().date()
    yesterday = (today - timedelta(days=1)).isoformat()
    week_ago = (today - timedelta(days=7)).isoformat()
    month_ago = (today - timedelta(days=30)).isoformat()
    
    # Test with various dates
    job1 = {'published_at': yesterday}
    assert calculate_job_age_days(job1) == 1
    
    job2 = {'published_at': week_ago}
    assert calculate_job_age_days(job2) == 7
    
    job3 = {'published_at': month_ago}
    assert calculate_job_age_days(job3) == 30
    
    # Test with today's date
    job4 = {'published_at': today.isoformat()}
    assert calculate_job_age_days(job4) == 0
    
    # Test with missing field
    job5 = {}
    assert calculate_job_age_days(job5) == 0
    
    # Test with invalid date
    job6 = {'published_at': 'invalid-date'}
    assert calculate_job_age_days(job6) == 0


def test_score_lead_tender():
    """
    Test scoring tender leads.
    """
    # Tenders should always get a fixed score of 3.0
    tender = {'lead_type': 'tender', 'title': 'Some Tender'}
    assert score_lead(tender) == 3.0
    
    # Even with extra fields, score should be the same
    tender_with_extra = {
        'lead_type': 'tender',
        'title': 'Complex Tender',
        'keywords': ['logistics', 'warehouse'],
        'date': '2025-04-27'
    }
    assert score_lead(tender_with_extra) == 3.0


def test_score_lead_news(mock_env_vars):
    """
    Test scoring news leads.
    """
    # News with no keyword matches: 2.0 + 0.1 * 0 = 2.0
    news1 = {
        'lead_type': 'news',
        'title': 'General News',
        'snippet': 'Business updates'
    }
    assert score_lead(news1) == 2.0
    
    # News with 1 keyword match: 2.0 + 0.1 * 1 = 2.1
    news2 = {
        'lead_type': 'news',
        'title': 'Logistics Updates',
        'snippet': 'Business news'
    }
    assert score_lead(news2) == 2.1
    
    # News with 3 keyword matches: 2.0 + 0.1 * 3 = 2.3
    news3 = {
        'lead_type': 'news',
        'title': 'Logistics and Warehouse News',
        'snippet': 'Updates on C&F operations'
    }
    assert score_lead(news3) == 2.3


def test_score_lead_job():
    """
    Test scoring job leads.
    """
    today = datetime.now().date()
    
    # Job posted today: 1.0 + 0.05 * 0 = 1.0
    job1 = {
        'lead_type': 'job',
        'job_title': 'Logistics Manager',
        'published_at': today.isoformat()
    }
    assert score_lead(job1) == 1.0
    
    # Job posted 10 days ago: 1.0 + 0.05 * 10 = 1.5
    job2 = {
        'lead_type': 'job',
        'job_title': 'Warehouse Supervisor',
        'published_at': (today - timedelta(days=10)).isoformat()
    }
    assert score_lead(job2) == 1.5
    
    # Job posted 30 days ago: 1.0 + 0.05 * 30 = 2.5
    job3 = {
        'lead_type': 'job',
        'job_title': 'Senior Logistics Manager',
        'published_at': (today - timedelta(days=30)).isoformat()
    }
    assert score_lead(job3) == 2.5
    
    # Job posted 60 days ago: 1.0 + 0.05 * 60 = 4.0
    job4 = {
        'lead_type': 'job',
        'job_title': 'Logistics Director',
        'published_at': (today - timedelta(days=60)).isoformat()
    }
    assert score_lead(job4) == 4.0


def test_score_lead_unknown_type():
    """
    Test scoring leads with unknown type.
    """
    unknown = {'lead_type': 'unknown', 'title': 'Some lead'}
    assert score_lead(unknown) == 0.0
    
    missing_type = {'title': 'Some lead without type'}
    assert score_lead(missing_type) == 0.0


def test_assign_scores(sample_leads, mock_env_vars):
    """
    Test assigning scores to a list of leads.
    """
    # Score the sample leads
    scored_leads = assign_scores(sample_leads)
    
    # Check that we still have the same number of leads
    assert len(scored_leads) == len(sample_leads)
    
    # Check that each lead has a lead_score field
    for lead in scored_leads:
        assert 'lead_score' in lead
        
    # Check specific lead types
    tender_leads = [lead for lead in scored_leads if lead['lead_type'] == 'tender']
    news_leads = [lead for lead in scored_leads if lead['lead_type'] == 'news']
    job_leads = [lead for lead in scored_leads if lead['lead_type'] == 'job']
    
    # Check tender scores
    for lead in tender_leads:
        assert lead['lead_score'] == 3.0
    
    # Check that news scores vary based on keywords
    news_scores = [lead['lead_score'] for lead in news_leads]
    assert 2.0 in news_scores  # News with no keywords
    assert 2.2 in news_scores  # News with 2 keywords
    assert 2.3 in news_scores  # News with 3 keywords
    
    # Check that job scores vary based on age
    # Note: These assertions might need adjustment based on exact test dates
    job_scores = [lead['lead_score'] for lead in job_leads]
    assert any(1.0 <= score <= 1.1 for score in job_scores)  # Recent job
    assert any(1.3 <= score <= 1.4 for score in job_scores)  # ~week old job
    assert any(2.4 <= score <= 2.6 for score in job_scores)  # ~month old job


def test_assign_scores_empty_input():
    """
    Test assigning scores with empty input.
    """
    assert assign_scores([]) == []
    assert assign_scores(None) == []


def test_key_terms(mock_env_vars):
    """
    Test that KEY_TERMS are correctly loaded from environment variables.
    """
    # Re-import to refresh environment variables
    from logilead.scoring import KEY_TERMS
    
    # Check KEY_TERMS
    assert isinstance(KEY_TERMS, list)
    assert len(KEY_TERMS) == 3
    assert 'logistics' in KEY_TERMS
    assert 'warehouse' in KEY_TERMS
    assert 'c&f' in KEY_TERMS  # Should be lowercase
