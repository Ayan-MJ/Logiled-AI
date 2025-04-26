"""
Database models and persistence for LogiLead AI.

This module defines SQLAlchemy models and database operations.
"""

import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, func
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


class Tender(Base):
    """
    SQLAlchemy model for tender data.
    """
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    issuer = Column(String(200), nullable=False)
    location = Column(String(200), nullable=True)
    deadline = Column(DateTime, nullable=True)
    url = Column(Text, nullable=False, unique=True)
    url_hash = Column(String(64), nullable=False, unique=True, index=True)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation of the Tender object."""
        return f"<Tender(id={self.id}, source='{self.source}', title='{self.title[:30]}...', deadline={self.deadline})>"


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


def save_tenders(tenders: List[Dict]) -> int:
    """
    Save a list of tenders to the database.
    
    This function implements idempotency by checking if a tender with the same URL hash
    already exists in the database. If it does, the record is updated with the new
    fetched_at timestamp.
    
    Args:
        tenders: List of tender dictionaries
        
    Returns:
        int: Number of new tenders saved
    """
    if not tenders:
        logger.info("No tenders to save")
        return 0
    
    session = get_db_session()
    new_count = 0
    
    try:
        logger.info(f"Saving {len(tenders)} tenders to database")
        
        for tender_dict in tenders:
            try:
                # Convert ISO date string to datetime object if needed
                if isinstance(tender_dict.get('deadline'), str):
                    try:
                        tender_dict['deadline'] = datetime.fromisoformat(tender_dict['deadline'])
                    except ValueError:
                        logger.warning(f"Invalid date format for tender: {tender_dict.get('title')}")
                        tender_dict['deadline'] = None
                
                # Prepare the insert statement with on_conflict_do_update
                stmt = insert(Tender).values(
                    source=tender_dict.get('source'),
                    title=tender_dict.get('title'),
                    issuer=tender_dict.get('issuer'),
                    location=tender_dict.get('location'),
                    deadline=tender_dict.get('deadline'),
                    url=tender_dict.get('url'),
                    url_hash=tender_dict.get('url_hash'),
                    fetched_at=datetime.fromisoformat(tender_dict.get('fetched_at')) 
                    if isinstance(tender_dict.get('fetched_at'), str) 
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
                logger.error(f"Error saving tender {tender_dict.get('title')}: {e}")
                continue
        
        # Commit the transaction
        session.commit()
        logger.info(f"Successfully saved {new_count} new tenders to database")
        
    except Exception as e:
        logger.error(f"Error in save_tenders: {e}")
        session.rollback()
        raise
    finally:
        session.close()
    
    return new_count


def get_recent_tenders(limit: int = 10) -> List[Tender]:
    """
    Get the most recent tenders from the database.
    
    Args:
        limit: Maximum number of tenders to return
        
    Returns:
        List[Tender]: List of Tender objects
    """
    session = get_db_session()
    try:
        return session.query(Tender).order_by(Tender.fetched_at.desc()).limit(limit).all()
    except Exception as e:
        logger.error(f"Error retrieving recent tenders: {e}")
        return []
    finally:
        session.close()


if __name__ == "__main__":
    # Example usage
    from scraper import fetch_gem_tenders
    
    # Create tables if they don't exist
    create_tables()
    
    # Fetch tenders from GeM portal
    tenders = fetch_gem_tenders()
    
    # Save tenders to database
    new_count = save_tenders(tenders)
    
    print(f"Fetched {len(tenders)} tenders, {new_count} new")
    
    # Retrieve and display recent tenders
    recent_tenders = get_recent_tenders(5)
    print("\nRecent tenders:")
    for tender in recent_tenders:
        print(f"- {tender.title[:50]}... ({tender.issuer}) - {tender.deadline}")
