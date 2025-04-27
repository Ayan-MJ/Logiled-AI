"""
Migration script to convert the existing tenders table to the new leads table.

This script performs a raw SQL migration to:
1. Rename the 'tenders' table to 'leads'
2. Add new columns: lead_type, lead_score, published_at, issuer_or_company
3. Populate those columns with default values for existing records
"""

import os
import logging
from datetime import datetime

from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Float, DateTime
from sqlalchemy.exc import SQLAlchemyError
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


def check_table_exists(engine, table_name):
    """Check if a table exists in the database."""
    metadata = MetaData()
    metadata.reflect(bind=engine)
    return table_name in metadata.tables


def migrate_tenders_to_leads():
    """
    Main migration function to convert tenders table to leads table.
    """
    engine = create_engine(db_url)
    conn = engine.connect()
    
    try:
        # Start transaction
        trans = conn.begin()
        logger.info("Starting migration from tenders to leads")
        
        # Check if tenders table exists
        if not check_table_exists(engine, 'tenders'):
            logger.info("Tenders table doesn't exist. Migration not needed.")
            return False
        
        # Check if leads table already exists
        if check_table_exists(engine, 'leads'):
            logger.info("Leads table already exists. Migration already completed.")
            return False
        
        # 1. Rename tenders table to leads
        logger.info("Renaming 'tenders' table to 'leads'")
        conn.execute(text("ALTER TABLE tenders RENAME TO leads;"))
        
        # 2. Add new columns
        logger.info("Adding new columns to 'leads' table")
        conn.execute(text("ALTER TABLE leads ADD COLUMN lead_type VARCHAR(20);"))
        conn.execute(text("ALTER TABLE leads ADD COLUMN lead_score FLOAT;"))
        conn.execute(text("ALTER TABLE leads ADD COLUMN published_at TIMESTAMP;"))
        conn.execute(text("ALTER TABLE leads ADD COLUMN issuer_or_company VARCHAR(200);"))
        
        # 3. Populate new columns with default values
        logger.info("Populating new columns with default values")
        conn.execute(text("UPDATE leads SET lead_type = 'tender';"))
        conn.execute(text("UPDATE leads SET lead_score = 3.0;"))
        conn.execute(text("UPDATE leads SET published_at = fetched_at;"))
        conn.execute(text("UPDATE leads SET issuer_or_company = issuer;"))
        
        # 4. Create indices for new columns
        logger.info("Creating indices for new columns")
        conn.execute(text("CREATE INDEX idx_leads_lead_type ON leads (lead_type);"))
        conn.execute(text("CREATE INDEX idx_leads_lead_score ON leads (lead_score);"))
        
        # 5. Make lead_type column NOT NULL
        logger.info("Setting lead_type column to NOT NULL")
        conn.execute(text("ALTER TABLE leads ALTER COLUMN lead_type SET NOT NULL;"))
        
        # Commit the transaction
        trans.commit()
        logger.info("Migration completed successfully")
        return True
        
    except SQLAlchemyError as e:
        # Rollback on error
        trans.rollback()
        logger.error(f"Migration failed: {e}")
        return False
        
    finally:
        # Close connection
        conn.close()


if __name__ == "__main__":
    # Run the migration
    if migrate_tenders_to_leads():
        print("Migration completed successfully")
    else:
        print("Migration failed or was not necessary")
