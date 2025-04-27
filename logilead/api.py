"""
API module for LogiLead AI.

This module provides a FastAPI-based REST API for accessing lead data.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from logilead.db import Lead, get_db_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LogiLead API",
    description="API for accessing leads from tenders, news, and job postings",
    version="1.0.0"
)

# Add CORS middleware
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class LeadBase(BaseModel):
    """Base Pydantic model for Lead data."""
    model_config = ConfigDict(from_attributes=True)
    
    title: str
    source: str
    issuer_or_company: Optional[str] = None
    location: Optional[str] = None
    url: str
    lead_type: str
    lead_score: Optional[float] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime


class LeadResponse(LeadBase):
    """Pydantic model for Lead response including ID."""
    id: int


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    data: Any = None
    error: Optional[str] = None


class PaginatedLeadsResponse(BaseModel):
    """Paginated response for leads endpoint."""
    items: List[LeadResponse]
    total: int
    page: int
    page_size: int
    pages: int


# Database dependency
def get_db():
    """
    FastAPI dependency that provides a database session.
    
    The session is closed after the request is processed.
    """
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standard response format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": None, "error": exc.detail},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy exceptions with standard response format."""
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"data": None, "error": "Database error occurred"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with standard response format."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"data": None, "error": "An unexpected error occurred"},
    )


# API routes
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return APIResponse(data={"status": "healthy"})


@app.get("/api/v1/leads", response_model=APIResponse)
async def get_leads(
    db: Session = Depends(get_db),
    type: Optional[str] = Query(None, description="Filter by lead type (tender, news, job)"),
    city: Optional[str] = Query(None, description="Filter by city/location"),
    min_score: float = Query(0.0, description="Minimum lead score"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page")
):
    """
    Get a paginated list of leads with optional filtering.
    
    Args:
        db: Database session
        type: Optional lead type filter
        city: Optional city/location filter
        min_score: Minimum lead score filter
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Paginated list of leads
    """
    # Build the query with filters
    query = db.query(Lead)
    
    if type:
        query = query.filter(Lead.lead_type == type)
    
    if city:
        query = query.filter(Lead.location.ilike(f"%{city}%"))
    
    if min_score > 0:
        query = query.filter(Lead.lead_score >= min_score)
    
    # Get total count for pagination
    total = query.count()
    
    # Calculate pagination
    offset = (page - 1) * page_size
    total_pages = (total + page_size - 1) // page_size  # Ceiling division
    
    # Get paginated results
    leads = query.order_by(Lead.lead_score.desc())\
                .offset(offset)\
                .limit(page_size)\
                .all()
    
    # Create response
    response = PaginatedLeadsResponse(
        items=[LeadResponse.model_validate(lead) for lead in leads],
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages
    )
    
    return APIResponse(data=response)


@app.get("/api/v1/leads/{lead_id}", response_model=APIResponse)
async def get_lead_by_id(lead_id: int, db: Session = Depends(get_db)):
    """
    Get a single lead by ID.
    
    Args:
        lead_id: The ID of the lead to retrieve
        db: Database session
        
    Returns:
        The lead with the specified ID
        
    Raises:
        HTTPException: If the lead is not found
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    
    return APIResponse(data=LeadResponse.model_validate(lead))


if __name__ == "__main__":
    # This block allows running the API directly for development
    import uvicorn
    uvicorn.run("logilead.api:app", host="0.0.0.0", port=8000, reload=True)
