"""
Job scheduling module for LogiLead AI.

This module configures and manages scheduled jobs using APScheduler.
"""

import logging
import os
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from logilead.scraper import fetch_new_gem_tenders
from logilead.db import save_tenders, create_tables
from logilead.alerter import send_tender_digest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global scheduler instance
scheduler = None


def scrape_and_save_tenders() -> None:
    """
    Fetch new tenders and save them to the database.
    
    This function is designed to be run as a scheduled job.
    """
    logger.info("Starting scheduled tender scraping job")
    
    try:
        # Fetch new tenders
        tenders = fetch_new_gem_tenders()
        logger.info(f"Fetched {len(tenders)} new tenders")
        
        # Save tenders to database
        if tenders:
            new_count = save_tenders(tenders)
            logger.info(f"Saved {new_count} new tenders to database")
        else:
            logger.info("No new tenders to save")
            
        logger.info("Tender scraping job completed successfully")
    except Exception as e:
        logger.error(f"Error in scheduled tender scraping job: {e}")
        # Log the error but don't crash the scheduler


def send_tender_alerts() -> None:
    """
    Send email alerts for new tenders.
    
    This function is designed to be run as a scheduled job.
    """
    logger.info("Starting scheduled tender alert job")
    
    try:
        # Send digest email
        success = send_tender_digest()
        if success:
            logger.info("Tender alert email sent successfully")
        else:
            logger.warning("Failed to send tender alert email")
            
        logger.info("Tender alert job completed successfully")
    except Exception as e:
        logger.error(f"Error in scheduled tender alert job: {e}")
        # Log the error but don't crash the scheduler


def scrape_save_and_alert() -> None:
    """
    Combined job that scrapes, saves, and sends alerts for new tenders.
    
    This function is designed to be run as a scheduled job.
    """
    logger.info("Starting combined tender scraping and alert job")
    
    try:
        # First scrape and save
        scrape_and_save_tenders()
        
        # Then send alerts
        send_tender_alerts()
        
        logger.info("Combined tender job completed successfully")
    except Exception as e:
        logger.error(f"Error in combined tender job: {e}")
        # Log the error but don't crash the scheduler


def start_scheduler() -> BackgroundScheduler:
    """
    Start the background scheduler with configured jobs.
    
    Returns:
        BackgroundScheduler: The started scheduler instance
    """
    global scheduler
    
    if scheduler is not None and scheduler.running:
        logger.warning("Scheduler is already running")
        return scheduler
    
    logger.info("Initializing scheduler")
    
    # Create a new scheduler
    scheduler = BackgroundScheduler()
    
    # Add the combined tender scraping and alert job to run at 00:30 daily
    scheduler.add_job(
        scrape_save_and_alert,
        trigger=CronTrigger(hour=0, minute=30),
        id='tender_combined_job',
        name='Scrape, save, and send alerts for tenders',
        replace_existing=True
    )
    
    # Ensure database tables exist
    try:
        create_tables()
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started successfully")
    
    return scheduler


def stop_scheduler() -> None:
    """
    Stop the background scheduler if it's running.
    """
    global scheduler
    
    if scheduler is not None and scheduler.running:
        logger.info("Stopping scheduler")
        scheduler.shutdown()
        logger.info("Scheduler stopped successfully")
    else:
        logger.warning("Scheduler is not running")


if __name__ == "__main__":
    # Create database tables if they don't exist
    create_tables()
    
    # Start the scheduler
    scheduler = start_scheduler()
    
    # Run the job once immediately for testing
    scrape_save_and_alert()
    
    try:
        # Keep the script running
        print("Scheduler is running. Press Ctrl+C to exit.")
        
        # This is a simple way to keep the script running
        # In a production environment, you might want to use a proper daemon
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Stopping scheduler...")
        stop_scheduler()
        print("Scheduler stopped. Exiting.")
