"""
Tests for the job scraper module.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from logilead.job_scraper import (
    construct_naukri_search_url,
    parse_naukri_date,
    scrape_naukri_jobs,
    fetch_job_postings,
    JOB_TITLES,
    TARGET_CITIES
)


@pytest.fixture
def mock_job_response():
    """
    Fixture that returns a mock Naukri.com API response.
    """
    return {
        'jobDetails': [
            {
                'title': 'Logistics Manager',
                'companyName': 'ABC Logistics Ltd',
                'placeholders': [{'location': 'Mumbai, Maharashtra'}],
                'footerPlaceholderLabel': '2 days ago',
                'jdURL': 'https://www.naukri.com/job-listings-logistics-manager-abc-logistics-mumbai-12345',
                'jobId': '12345'
            },
            {
                'title': 'Senior Logistics Manager',
                'companyName': 'XYZ Shipping Company',
                'placeholders': [{'location': 'Mumbai, Maharashtra'}],
                'footerPlaceholderLabel': 'Today',
                'jdURL': 'https://www.naukri.com/job-listings-senior-logistics-manager-xyz-shipping-mumbai-67890',
                'jobId': '67890'
            },
            {
                'title': 'Warehouse Logistics Supervisor',
                'companyName': 'Global Supply Chain Solutions',
                'placeholders': [{'location': 'Thane, Mumbai'}],
                'footerPlaceholderLabel': '5 days ago',
                'jdURL': 'https://www.naukri.com/job-listings-warehouse-supervisor-global-supply-chain-mumbai-54321',
                'jobId': '54321'
            }
        ]
    }


@pytest.fixture
def mock_empty_response():
    """
    Fixture that returns an empty response.
    """
    return {'jobDetails': []}


@pytest.fixture
def mock_env_vars():
    """
    Fixture that sets up mock environment variables.
    """
    original_env = os.environ.copy()
    os.environ['JOB_TITLES'] = 'Logistics Manager,Warehouse Supervisor'
    os.environ['TARGET_CITIES'] = 'Mumbai,Bangalore,Delhi'
    yield
    os.environ.clear()
    os.environ.update(original_env)


def test_construct_naukri_search_url():
    """
    Test that the search URL is constructed correctly.
    """
    url = construct_naukri_search_url("Logistics Manager", "Mumbai")
    
    # Check that the URL contains the encoded job title and location
    assert "Logistics%20Manager" in url
    assert "Mumbai" in url
    assert url.startswith("https://www.naukri.com/jobapi/v3/search")
    assert "noOfResults=20" in url


def test_parse_naukri_date():
    """
    Test that various date formats are parsed correctly.
    """
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    five_days_ago = today - timedelta(days=5)
    two_weeks_ago = today - timedelta(weeks=2)
    
    # Test various date formats
    assert parse_naukri_date("Just now") == today.isoformat()
    assert parse_naukri_date("Today") == today.isoformat()
    assert parse_naukri_date("Yesterday") == yesterday.isoformat()
    assert parse_naukri_date("5 days ago") == five_days_ago.isoformat()
    assert parse_naukri_date("2 weeks ago") == two_weeks_ago.isoformat()
    assert parse_naukri_date("2 hours ago") == today.isoformat()
    
    # Test with empty or invalid input
    assert parse_naukri_date("") == today.isoformat()
    assert parse_naukri_date("Invalid date") == today.isoformat()


def test_scrape_naukri_jobs_success(mock_job_response):
    """
    Test successful scraping of Naukri.com jobs.
    """
    with patch('logilead.job_scraper.requests.get') as mock_get:
        # Configure the mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_job_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call the function
        jobs = scrape_naukri_jobs("Logistics Manager", "Mumbai")
        
        # Verify the results
        assert len(jobs) == 3
        
        # Check job details
        assert jobs[0]['job_title'] == 'Logistics Manager'
        assert jobs[0]['company_name'] == 'ABC Logistics Ltd'
        assert jobs[0]['location'] == 'Mumbai, Maharashtra'
        assert jobs[0]['source'] == 'Naukri'
        assert 'published_at' in jobs[0]
        assert 'url' in jobs[0]
        assert 'url_hash' in jobs[0]
        assert 'fetched_at' in jobs[0]
        
        # Check that URLs are preserved
        assert jobs[0]['url'] == 'https://www.naukri.com/job-listings-logistics-manager-abc-logistics-mumbai-12345'
        
        # Verify the API call
        mock_get.assert_called_once()


def test_scrape_naukri_jobs_empty_response(mock_empty_response):
    """
    Test behavior when no jobs are found.
    """
    with patch('logilead.job_scraper.requests.get') as mock_get:
        # Configure the mock response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_empty_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call the function
        jobs = scrape_naukri_jobs("Non-existent Job", "Remote")
        
        # Verify that an empty list is returned
        assert jobs == []
        assert len(jobs) == 0


def test_scrape_naukri_jobs_http_error():
    """
    Test behavior when HTTP request fails.
    """
    with patch('logilead.job_scraper.requests.get') as mock_get:
        # Configure the mock to raise an exception
        mock_get.side_effect = Exception("HTTP Error")
        
        # Call the function
        jobs = scrape_naukri_jobs("Logistics Manager", "Mumbai")
        
        # Verify that an empty list is returned
        assert jobs == []


def test_fetch_job_postings(mock_env_vars, mock_job_response):
    """
    Test the main fetch_job_postings function.
    """
    with patch('logilead.job_scraper.scrape_naukri_jobs') as mock_scrape:
        # Configure the mock to return a fixed set of jobs
        mock_scrape.return_value = [
            {
                'job_title': 'Logistics Manager', 
                'company_name': 'Test Company',
                'location': 'Mumbai', 
                'published_at': '2025-04-25',
                'url': 'https://example.com/job1',
                'url_hash': 'hash1',
                'source': 'Naukri',
                'fetched_at': '2025-04-27T00:00:00'
            }
        ]
        
        # Call the function
        jobs = fetch_job_postings()
        
        # We expect mock_scrape to be called for each title-city combination
        expected_calls = len(JOB_TITLES) * len(TARGET_CITIES)
        assert mock_scrape.call_count == expected_calls
        
        # Check that the job count matches what we expect
        assert len(jobs) == expected_calls
        
        # Verify that the jobs have the required fields
        for job in jobs:
            assert 'job_title' in job
            assert 'company_name' in job
            assert 'location' in job
            assert 'published_at' in job
            assert 'url' in job
            assert 'url_hash' in job
            assert 'source' in job
            assert 'fetched_at' in job


def test_job_titles_and_target_cities(mock_env_vars):
    """
    Test that JOB_TITLES and TARGET_CITIES are correctly populated from environment vars.
    """
    # Re-import to refresh environment variables
    from logilead.job_scraper import JOB_TITLES, TARGET_CITIES
    
    # Check JOB_TITLES
    assert isinstance(JOB_TITLES, list)
    assert len(JOB_TITLES) == 2
    assert 'Logistics Manager' in JOB_TITLES
    assert 'Warehouse Supervisor' in JOB_TITLES
    
    # Check TARGET_CITIES
    assert isinstance(TARGET_CITIES, list)
    assert len(TARGET_CITIES) == 3
    assert 'Mumbai' in TARGET_CITIES
    assert 'Bangalore' in TARGET_CITIES
    assert 'Delhi' in TARGET_CITIES
