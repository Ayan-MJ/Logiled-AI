"""
Tests for the API module.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from logilead.api import app, get_db
from logilead.db import Base, Lead


# Create in-memory SQLite database for testing
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the get_db dependency for testing
@pytest.fixture
def override_get_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# Create test client
@pytest.fixture
def client(override_get_db):
    def _get_test_db():
        try:
            yield override_get_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# Sample data fixture
@pytest.fixture
def sample_leads(override_get_db):
    today = datetime.now()
    
    # Create sample leads
    leads = [
        # Tender leads
        Lead(
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
        ),
        Lead(
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
        ),
        # News leads
        Lead(
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
        ),
        # Job leads
        Lead(
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
        ),
    ]
    
    # Add to database
    for lead in leads:
        override_get_db.add(lead)
    override_get_db.commit()
    
    # Refresh to get IDs
    for lead in leads:
        override_get_db.refresh(lead)
    
    return leads


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["data"]["status"] == "healthy"
    assert data["error"] is None


def test_get_leads_no_filter(client, sample_leads):
    """Test getting all leads without filtering."""
    response = client.get("/api/v1/leads")
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    assert data["data"]["total"] == 4
    assert len(data["data"]["items"]) == 4
    assert data["data"]["page"] == 1
    assert data["data"]["page_size"] == 25
    assert data["data"]["pages"] == 1
    
    # Verify leads are ordered by score descending
    leads = data["data"]["items"]
    scores = [lead["lead_score"] for lead in leads]
    assert scores == sorted(scores, reverse=True)


def test_get_leads_by_type(client, sample_leads):
    """Test filtering leads by type."""
    response = client.get("/api/v1/leads?type=tender")
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    assert data["data"]["total"] == 2
    assert len(data["data"]["items"]) == 2
    
    # Verify all returned leads are tenders
    for lead in data["data"]["items"]:
        assert lead["lead_type"] == "tender"


def test_get_leads_by_city(client, sample_leads):
    """Test filtering leads by city."""
    response = client.get("/api/v1/leads?city=Mumbai")
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    assert data["data"]["total"] == 2
    
    # Verify Mumbai is in the location of all returned leads
    for lead in data["data"]["items"]:
        assert "Mumbai" in lead["location"]


def test_get_leads_by_min_score(client, sample_leads):
    """Test filtering leads by minimum score."""
    response = client.get("/api/v1/leads?min_score=2.5")
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    
    # Verify all returned leads have score >= 2.5
    for lead in data["data"]["items"]:
        assert lead["lead_score"] >= 2.5


def test_get_leads_combined_filters(client, sample_leads):
    """Test combining multiple filters."""
    response = client.get("/api/v1/leads?type=tender&city=Mumbai&min_score=2.5")
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    
    # Verify results match all criteria
    for lead in data["data"]["items"]:
        assert lead["lead_type"] == "tender"
        assert "Mumbai" in lead["location"]
        assert lead["lead_score"] >= 2.5


def test_get_leads_pagination(client, sample_leads):
    """Test lead pagination."""
    # Request first page with 2 items per page
    response = client.get("/api/v1/leads?page=1&page_size=2")
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    assert data["data"]["total"] == 4
    assert len(data["data"]["items"]) == 2
    assert data["data"]["page"] == 1
    assert data["data"]["page_size"] == 2
    assert data["data"]["pages"] == 2
    
    # Get IDs from first page
    first_page_ids = [lead["id"] for lead in data["data"]["items"]]
    
    # Request second page
    response = client.get("/api/v1/leads?page=2&page_size=2")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["data"]["items"]) == 2
    assert data["data"]["page"] == 2
    
    # Get IDs from second page
    second_page_ids = [lead["id"] for lead in data["data"]["items"]]
    
    # Verify no overlap between pages
    assert not set(first_page_ids).intersection(set(second_page_ids))


def test_get_lead_by_id_exists(client, sample_leads):
    """Test getting a lead by ID when it exists."""
    # Get the ID of the first sample lead
    lead_id = sample_leads[0].id
    
    response = client.get(f"/api/v1/leads/{lead_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    assert data["data"]["id"] == lead_id
    assert data["data"]["title"] == sample_leads[0].title


def test_get_lead_by_id_not_found(client):
    """Test getting a lead by ID when it doesn't exist."""
    response = client.get("/api/v1/leads/999")
    assert response.status_code == 404
    
    data = response.json()
    assert data["data"] is None
    assert "not found" in data["error"].lower()


def test_error_handling(client, override_get_db):
    """Test error handling for database errors."""
    # Mock a database query to raise an exception
    with patch('sqlalchemy.orm.Session.query', side_effect=Exception("Test error")):
        response = client.get("/api/v1/leads")
        assert response.status_code == 500
        
        data = response.json()
        assert data["data"] is None
        assert "error" in data
        assert data["error"] is not None
