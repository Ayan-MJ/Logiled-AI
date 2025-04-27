"""
Tests for the email alerting module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from logilead.alerter import (
    format_lead_for_email,
    format_leads_by_type,
    send_lead_digest,
    ALERT_RECIPIENTS
)
from logilead.db import Lead


@pytest.fixture
def mock_env_vars():
    """
    Fixture that sets up mock environment variables.
    """
    original_env = os.environ.copy()
    os.environ['LOGILEAD_SMTP_HOST'] = 'smtp.example.com'
    os.environ['LOGILEAD_SMTP_PORT'] = '587'
    os.environ['LOGILEAD_SMTP_USER'] = 'test@example.com'
    os.environ['LOGILEAD_SMTP_PASS'] = 'password'
    os.environ['LOGILEAD_ALERT_RECIPIENTS'] = 'recipient1@example.com,recipient2@example.com'
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_lead_objects():
    """
    Fixture that provides sample lead objects of different types.
    """
    # Create sample leads
    today = datetime.now()
    
    # Tender leads
    tender1 = Lead(
        id=1,
        source='GeM',
        title='Government IT Infrastructure Tender',
        issuer_or_company='Ministry of IT',
        location='New Delhi',
        deadline=today + timedelta(days=30),
        published_at=today - timedelta(days=2),
        url='https://example.com/tender1',
        url_hash='hash1',
        lead_type='tender',
        lead_score=3.0,
        fetched_at=today - timedelta(hours=12)
    )
    
    tender2 = Lead(
        id=2,
        source='GeM',
        title='Medical Supplies Tender',
        issuer_or_company='Ministry of Health',
        location='Mumbai',
        deadline=today + timedelta(days=15),
        published_at=today - timedelta(days=1),
        url='https://example.com/tender2',
        url_hash='hash2',
        lead_type='tender',
        lead_score=3.0,
        fetched_at=today - timedelta(hours=6)
    )
    
    # News leads
    news1 = Lead(
        id=3,
        source='Business Standard',
        title='Logistics Company Expanding Operations',
        issuer_or_company='Business Standard',
        location='Mumbai',
        published_at=today - timedelta(hours=8),
        url='https://example.com/news1',
        url_hash='hash3',
        lead_type='news',
        lead_score=2.3,
        fetched_at=today - timedelta(hours=4)
    )
    
    news2 = Lead(
        id=4,
        source='Economic Times',
        title='Warehouse Facility Opening in Pune',
        issuer_or_company='Economic Times',
        location='Pune',
        published_at=today - timedelta(hours=12),
        url='https://example.com/news2',
        url_hash='hash4',
        lead_type='news',
        lead_score=2.2,
        fetched_at=today - timedelta(hours=8)
    )
    
    # Job leads
    job1 = Lead(
        id=5,
        source='Naukri',
        title='Senior Logistics Manager',
        issuer_or_company='ABC Logistics Ltd',
        location='Bangalore',
        published_at=today - timedelta(days=3),
        url='https://example.com/job1',
        url_hash='hash5',
        lead_type='job',
        lead_score=1.15,
        fetched_at=today - timedelta(hours=10)
    )
    
    job2 = Lead(
        id=6,
        source='Naukri',
        title='Warehouse Supervisor',
        issuer_or_company='XYZ Warehousing',
        location='Chennai',
        published_at=today - timedelta(days=5),
        url='https://example.com/job2',
        url_hash='hash6',
        lead_type='job',
        lead_score=1.25,
        fetched_at=today - timedelta(hours=5)
    )
    
    return [tender1, tender2, news1, news2, job1, job2]


def test_format_lead_for_email(sample_lead_objects):
    """
    Test formatting individual leads for email.
    """
    # Test formatting a tender lead
    tender_lead = sample_lead_objects[0]
    tender_format = format_lead_for_email(tender_lead)
    assert "Government IT Infrastructure Tender" in tender_format
    assert "Ministry of IT" in tender_format
    assert "New Delhi" in tender_format
    assert "Score: 3.00" in tender_format
    assert tender_format.startswith("•")
    
    # Test formatting a news lead
    news_lead = sample_lead_objects[2]
    news_format = format_lead_for_email(news_lead)
    assert "Logistics Company Expanding Operations" in news_format
    assert "Business Standard" in news_format
    assert "Mumbai" in news_format
    assert "Score: 2.30" in news_format
    assert news_format.startswith("•")
    
    # Test formatting a job lead
    job_lead = sample_lead_objects[4]
    job_format = format_lead_for_email(job_lead)
    assert "Senior Logistics Manager" in job_format
    assert "ABC Logistics Ltd" in job_format
    assert "Bangalore" in job_format
    assert "Score: 1.15" in job_format
    assert job_format.startswith("•")


def test_format_leads_by_type(sample_lead_objects):
    """
    Test formatting groups of leads by type for email.
    """
    # Group leads by type
    leads_by_type = {
        'tender': [lead for lead in sample_lead_objects if lead.lead_type == 'tender'],
        'news': [lead for lead in sample_lead_objects if lead.lead_type == 'news'],
        'job': [lead for lead in sample_lead_objects if lead.lead_type == 'job']
    }
    
    # Format leads
    formatted = format_leads_by_type(leads_by_type)
    
    # Verify section headers
    assert "🔥 Top Tenders:" in formatted
    assert "📣 Top News Leads:" in formatted
    assert "💼 Top Job Leads:" in formatted
    
    # Verify content from each type of lead
    assert "Government IT Infrastructure Tender" in formatted
    assert "Logistics Company Expanding Operations" in formatted
    assert "Senior Logistics Manager" in formatted
    
    # Test with empty dictionary
    empty_format = format_leads_by_type({})
    assert "No new leads found" in empty_format
    
    # Test with some missing types
    partial_leads = {'tender': leads_by_type['tender']}
    partial_format = format_leads_by_type(partial_leads)
    assert "🔥 Top Tenders:" in partial_format
    assert "📣 Top News Leads:" not in partial_format
    assert "💼 Top Job Leads:" not in partial_format


def test_send_lead_digest_with_leads(mock_env_vars, sample_lead_objects):
    """
    Test sending lead digest when leads are available.
    """
    with patch('logilead.alerter.get_top_leads_by_type') as mock_get_leads:
        with patch('logilead.alerter.send_email') as mock_send_email:
            with patch('logilead.alerter.save_last_alert_time') as mock_save_time:
                # Setup mock to return our sample leads
                leads_by_type = {
                    'tender': [lead for lead in sample_lead_objects if lead.lead_type == 'tender'],
                    'news': [lead for lead in sample_lead_objects if lead.lead_type == 'news'],
                    'job': [lead for lead in sample_lead_objects if lead.lead_type == 'job']
                }
                mock_get_leads.return_value = leads_by_type
                
                # Configure send_email to succeed
                mock_send_email.return_value = True
                
                # Call the function
                result = send_lead_digest()
                
                # Verify the result
                assert result is True
                
                # Verify the mocks were called correctly
                mock_get_leads.assert_called_once()
                mock_send_email.assert_called_once()
                
                # Verify email arguments
                call_args = mock_send_email.call_args
                email_subject = call_args[0][0]
                email_body = call_args[0][1]
                email_recipients = call_args[0][2]
                
                # Check subject contains count of leads
                assert "6 New Leads" in email_subject
                
                # Check body contains all three section headers
                assert "🔥 Top Tenders:" in email_body
                assert "📣 Top News Leads:" in email_body
                assert "💼 Top Job Leads:" in email_body
                
                # Check recipients match environment variable
                assert email_recipients == ALERT_RECIPIENTS
                
                # Verify timestamp was saved
                mock_save_time.assert_called_once()


def test_send_lead_digest_no_leads(mock_env_vars):
    """
    Test sending lead digest when no leads are available.
    """
    with patch('logilead.alerter.get_top_leads_by_type') as mock_get_leads:
        with patch('logilead.alerter.send_email') as mock_send_email:
            # Setup mock to return empty dict
            mock_get_leads.return_value = {}
            
            # Call the function
            result = send_lead_digest()
            
            # Verify the result
            assert result is True
            
            # Verify send_email was not called (no email needed)
            mock_send_email.assert_not_called()


def test_send_lead_digest_email_failure(mock_env_vars, sample_lead_objects):
    """
    Test behavior when email sending fails.
    """
    with patch('logilead.alerter.get_top_leads_by_type') as mock_get_leads:
        with patch('logilead.alerter.send_email') as mock_send_email:
            with patch('logilead.alerter.save_last_alert_time') as mock_save_time:
                # Setup mock to return our sample leads
                leads_by_type = {
                    'tender': [lead for lead in sample_lead_objects if lead.lead_type == 'tender']
                }
                mock_get_leads.return_value = leads_by_type
                
                # Configure send_email to fail
                mock_send_email.return_value = False
                
                # Call the function
                result = send_lead_digest()
                
                # Verify the result
                assert result is False
                
                # Verify the timestamp was not saved
                mock_save_time.assert_not_called()
