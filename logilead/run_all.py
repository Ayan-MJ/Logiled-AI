"""
Integration script for LogiLead AI.

This module ties together all components of the LogiLead AI system for testing
and manual execution.
"""

import logging
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "..", "logilead.log"))
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def run_full_cycle():
    """
    Run a complete cycle of the LogiLead AI system:
    1. Scrape tenders
    2. Store in database
    3. Send email alerts
    """
    logger.info("=" * 50)
    logger.info("Starting LogiLead AI full cycle")
    logger.info("=" * 50)
    
    # Step 1: Ensure database is ready
    logger.info("-" * 50)
    logger.info("STEP 1: Preparing database")
    from logilead.db import create_tables
    
    try:
        create_tables()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Database preparation failed: {e}")
        return False
    
    # Step 2: Scrape tenders
    logger.info("-" * 50)
    logger.info("STEP 2: Scraping tenders")
    from logilead.scraper import fetch_new_gem_tenders
    
    try:
        start_time = time.time()
        tenders = fetch_new_gem_tenders()
        duration = time.time() - start_time
        
        logger.info(f"Scraped {len(tenders)} new tenders in {duration:.2f} seconds")
        
        if not tenders:
            logger.info("No new tenders found")
    except Exception as e:
        logger.error(f"Tender scraping failed: {e}")
        return False
    
    # Step 3: Store tenders in database
    logger.info("-" * 50)
    logger.info("STEP 3: Storing tenders in database")
    from logilead.db import save_tenders
    
    try:
        if tenders:
            start_time = time.time()
            new_count = save_tenders(tenders)
            duration = time.time() - start_time
            
            logger.info(f"Saved {new_count} new tenders to database in {duration:.2f} seconds")
        else:
            logger.info("No tenders to save")
    except Exception as e:
        logger.error(f"Tender storage failed: {e}")
        return False
    
    # Step 4: Send email alerts
    logger.info("-" * 50)
    logger.info("STEP 4: Sending email alerts")
    from logilead.alerter import send_tender_digest
    
    try:
        start_time = time.time()
        success = send_tender_digest()
        duration = time.time() - start_time
        
        if success:
            logger.info(f"Email alerts sent successfully in {duration:.2f} seconds")
        else:
            logger.warning("Email alerts were not sent")
    except Exception as e:
        logger.error(f"Email alerting failed: {e}")
        return False
    
    # All steps completed
    logger.info("=" * 50)
    logger.info("LogiLead AI full cycle completed successfully")
    logger.info("=" * 50)
    
    return True


def run_scheduler():
    """
    Start the background scheduler for automated runs.
    """
    logger.info("Starting LogiLead AI scheduler")
    
    from logilead.scheduler import start_scheduler
    
    # Start the scheduler
    scheduler = start_scheduler()
    
    logger.info("Scheduler started. Press Ctrl+C to exit.")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        from logilead.scheduler import stop_scheduler
        stop_scheduler()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LogiLead AI - Tender scraping and alerting system")
    parser.add_argument("--scheduler", action="store_true", help="Start the background scheduler")
    parser.add_argument("--cycle", action="store_true", help="Run a complete cycle once")
    
    args = parser.parse_args()
    
    if args.scheduler:
        run_scheduler()
    elif args.cycle:
        run_full_cycle()
    else:
        # Default to running a complete cycle
        run_full_cycle()
