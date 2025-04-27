"""
Database models and persistence for LogiLead AI.

This module defines SQLAlchemy models and database operations.
"""

import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL from environment variable
db_url = os.getenv("LOGILEAD_DB_URL")
if not db_url:
    logger.error("Database URL not found in environment variables")
    raise ValueError("LOGILEAD_DB_URL environment variable is required")

# Create SQLAlchemy engine
engine = create_engine(db_url)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Lead(Base):
    """
    SQLAlchemy model for lead data (tenders, news, jobs).
    """
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    issuer_or_company = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    deadline = Column(DateTime, nullable=True)  # Kept for backward compatibility with tenders
    published_at = Column(DateTime, nullable=True)
    url = Column(Text, nullable=False)
    url_hash = Column(String(64), nullable=False, unique=True, index=True)
    lead_type = Column(String(20), nullable=False, index=True)  # 'tender', 'news', 'job'
    lead_score = Column(Float, nullable=True)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation of the Lead object."""
        return f"<Lead(id={self.id}, type='{self.lead_type}', title='{self.title[:30]}...', score={self.lead_score})>"


def create_tables() -> None:
    """
    Create all tables in the database.
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def get_db_session() -> Session:
    """
    Get a database session.
    
    Returns:
        Session: A SQLAlchemy session object
    """
    return SessionLocal()


def save_leads(leads: List[Dict], lead_type: str = "tender") -> int:
    """
    Save a list of leads to the database.
    
    This function implements idempotency by checking if a lead with the same URL hash
    already exists in the database. If it does, the record is updated with the new
    fetched_at timestamp.
    
    Args:
        leads: List of lead dictionaries
        lead_type: Type of leads ('tender', 'news', 'job')
        
    Returns:
        int: Number of new leads saved
    """
    if not leads:
        logger.info(f"No {lead_type} leads to save")
        return 0
    
    session = get_db_session()
    new_count = 0
    
    try:
        logger.info(f"Saving {len(leads)} {lead_type} leads to database")
        
        for lead_dict in leads:
            try:
                # Set lead_type if not already present
                if 'lead_type' not in lead_dict:
                    lead_dict['lead_type'] = lead_type
                
                # Map fields based on lead type
                issuer_or_company = None
                if lead_type == "tender":
                    issuer_or_company = lead_dict.get('issuer')
                elif lead_type == "news":
                    issuer_or_company = lead_dict.get('source')
                elif lead_type == "job":
                    issuer_or_company = lead_dict.get('company_name')
                
                # Convert date strings to datetime objects if needed
                published_at = None
                if lead_type == "tender" and 'deadline' in lead_dict:
                    # For tenders, set both deadline and published_at
                    deadline = lead_dict.get('deadline')
                    if isinstance(deadline, str):
                        try:
                            lead_dict['deadline'] = datetime.fromisoformat(deadline)
                        except ValueError:
                            logger.warning(f"Invalid date format for tender: {lead_dict.get('title')}")
                            lead_dict['deadline'] = None
                    published_at = lead_dict.get('fetched_at')
                elif 'published_at' in lead_dict:
                    published_at = lead_dict.get('published_at')
                
                if isinstance(published_at, str):
                    try:
                        published_at = datetime.fromisoformat(published_at)
                    except ValueError:
                        logger.warning(f"Invalid published_at format: {published_at}")
                        published_at = datetime.utcnow()
                
                # Extract lead score if present
                lead_score = lead_dict.get('lead_score')
                
                # Prepare the insert statement with on_conflict_do_update
                stmt = insert(Lead).values(
                    source=lead_dict.get('source'),
                    title=lead_dict.get('title', lead_dict.get('job_title', 'Unknown')),
                    issuer_or_company=issuer_or_company,
                    location=lead_dict.get('location'),
                    deadline=lead_dict.get('deadline'),
                    published_at=published_at,
                    url=lead_dict.get('url'),
                    url_hash=lead_dict.get('url_hash'),
                    lead_type=lead_dict.get('lead_type'),
                    lead_score=lead_score,
                    fetched_at=datetime.fromisoformat(lead_dict.get('fetched_at')) 
                    if isinstance(lead_dict.get('fetched_at'), str) 
                    else datetime.utcnow()
                )
                
                # Handle conflict - update fetched_at timestamp but keep other data
                stmt = stmt.on_conflict_do_update(
                    index_elements=['url_hash'],
                    set_=dict(fetched_at=datetime.utcnow())
                )
                
                result = session.execute(stmt)
                
                # Check if a new record was inserted
                if result.rowcount > 0:
                    new_count += 1
                
            except Exception as e:
                logger.error(f"Error saving lead {lead_dict.get('title', lead_dict.get('job_title', 'Unknown'))}: {e}")
                continue
        
        # Commit the transaction
        session.commit()
        logger.info(f"Successfully saved {new_count} new {lead_type} leads to database")
        
    except Exception as e:
        logger.error(f"Error in save_leads: {e}")
        session.rollback()
        raise
    finally:
        session.close()
    
    return new_count


def save_tenders(tenders: List[Dict]) -> int:
    """
    Alias for save_leads with lead_type='tender' for backward compatibility.
    
    Args:
        tenders: List of tender dictionaries
        
    Returns:
        int: Number of new tenders saved
    """
    return save_leads(tenders, lead_type="tender")


def get_recent_leads(lead_type: Optional[str] = None, limit: int = 10) -> List[Lead]:
    """
    Get the most recent leads from the database.
    
    Args:
        lead_type: Optional filter for lead type
        limit: Maximum number of leads to return
        
    Returns:
        List[Lead]: List of Lead objects
    """
    session = get_db_session()
    try:
        query = session.query(Lead).order_by(Lead.fetched_at.desc())
        
        if lead_type:
            query = query.filter(Lead.lead_type == lead_type)
            
        return query.limit(limit).all()
    except Exception as e:
        logger.error(f"Error retrieving recent leads: {e}")
        return []
    finally:
        session.close()


def get_top_leads(hours: int = 24, limit: int = 10) -> List[Lead]:
    """
    Get the top leads from the database based on lead score.
    
    Args:
        hours: Number of hours to look back
        limit: Maximum number of leads to return
        
    Returns:
        List[Lead]: List of Lead objects
    """
    session = get_db_session()
    try:
        # Calculate the cutoff time
        cutoff = datetime.utcnow() - datetime.timedelta(hours=hours)
        
        return session.query(Lead)\
            .filter(Lead.fetched_at >= cutoff)\
            .order_by(Lead.lead_score.desc())\
            .limit(limit)\
            .all()
    except Exception as e:
        logger.error(f"Error retrieving top leads: {e}")
        return []
    finally:
        session.close()


def get_top_leads_by_type(hours: int = 24, limit_per_type: int = 5) -> Dict[str, List[Lead]]:
    """
    Get the top leads from the database grouped by lead type.
    
    Args:
        hours: Number of hours to look back
        limit_per_type: Maximum number of leads to return per type
        
    Returns:
        Dict[str, List[Lead]]: Dictionary with lead_type as key and list of leads as value
    """
    session = get_db_session()
    result = {}
    
    try:
        # Calculate the cutoff time
        cutoff = datetime.utcnow() - datetime.timedelta(hours=hours)
        
        # Get distinct lead types
        lead_types = [row[0] for row in session.query(Lead.lead_type).distinct().all()]
        
        # For each lead type, get the top leads
        for lead_type in lead_types:
            leads = session.query(Lead)\
                .filter(Lead.lead_type == lead_type)\
                .filter(Lead.fetched_at >= cutoff)\
                .order_by(Lead.lead_score.desc())\
                .limit(limit_per_type)\
                .all()
            
            result[lead_type] = leads
            
        return result
    except Exception as e:
        logger.error(f"Error retrieving top leads by type: {e}")
        return {}
    finally:
        session.close()


if __name__ == "__main__":
    # Example usage
    create_tables()
    
    # Example of creating and saving a lead
    lead = {
        'source': 'Example Source',
        'title': 'Example Lead',
        'issuer_or_company': 'Example Company',
        'location': 'Example Location',
        'url': 'https://example.com/lead',
        'url_hash': 'example_hash_123',
        'lead_type': 'tender',
        'lead_score': 3.0,
        'fetched_at': datetime.utcnow().isoformat()
    }
    
    save_leads([lead])
    
    # Retrieve and display recent leads
    recent_leads = get_recent_leads(limit=5)
    print("\nRecent leads:")
    for lead in recent_leads:
        print(f"- {lead.title[:50]}... ({lead.issuer_or_company}) - Score: {lead.lead_score}")
