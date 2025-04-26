"""
Tender scraping module for LogiLead AI.

This module contains functions to scrape tender information from various sources.
"""

import logging
import os
from typing import Dict, List, Optional, Set
from datetime import datetime
import hashlib
import time

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def fetch_gem_tenders(existing_url_hashes: Optional[Set[str]] = None) -> List[Dict]:
    """
    Scrape tender information from the GeM portal related to C&F.
    
    Args:
        existing_url_hashes: Optional set of URL hashes that already exist in the database.
                            If provided, tenders with matching URL hashes will be skipped.
    
    Returns:
        List[Dict]: A list of dictionaries containing tender information with keys:
            - title: The tender title
            - issuer: The organization issuing the tender
            - location: The location of the tender
            - deadline: The deadline for submission (ISO format)
            - url: The URL to the tender details
            - source: The source of the tender (always 'GeM')
            - fetched_at: Timestamp when the tender was fetched (ISO format)
            - url_hash: SHA-256 hash of the URL for deduplication
    """
    logger.info("Starting to fetch tenders from GeM portal")
    
    # Initialize empty set if not provided
    if existing_url_hashes is None:
        existing_url_hashes = set()
    
    # GeM portal URL - this would typically come from environment variables
    gem_url = os.getenv("LOGILEAD_GEM_URL", "https://gem.gov.in/active-bids")
    
    tenders = []
    new_tenders = []
    
    try:
        # Send HTTP request to the GeM portal
        logger.info(f"Sending HTTP request to {gem_url}")
        response = requests.get(gem_url, timeout=30)
        
        # Raise an exception for bad status codes
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all tender listings - this selector would need to be updated
        # based on the actual structure of the GeM website
        tender_listings = soup.select('div.tender-listing')
        
        logger.info(f"Found {len(tender_listings)} tender listings")
        
        # Current timestamp for the fetched_at field
        fetched_at = datetime.now().isoformat()
        
        for listing in tender_listings:
            # Check if the tender is C&F-related
            # This is a placeholder - you would need to implement actual logic
            # to determine if a tender is C&F-related
            title = listing.select_one('h3.tender-title').text.strip()
            if not _is_cf_related(title):
                continue
                
            # Extract tender details
            try:
                url = listing.select_one('a.tender-link')['href']
                # Make sure URL is absolute
                if not url.startswith('http'):
                    url = f"https://gem.gov.in{url}"
                
                # Create URL hash for deduplication
                url_hash = hashlib.sha256(url.encode()).hexdigest()
                
                # Skip if this tender has already been seen
                if url_hash in existing_url_hashes:
                    logger.debug(f"Skipping already seen tender: {title}")
                    continue
                
                issuer = listing.select_one('div.tender-issuer').text.strip()
                location = listing.select_one('div.tender-location').text.strip()
                deadline_raw = listing.select_one('div.tender-deadline').text.strip()
                
                # Parse and normalize the deadline
                deadline = _parse_gem_date(deadline_raw)
                
                # Add tender to the list
                tender_data = {
                    'title': title,
                    'issuer': issuer,
                    'location': location,
                    'deadline': deadline,
                    'url': url,
                    'source': 'GeM',
                    'fetched_at': fetched_at,
                    'url_hash': url_hash
                }
                
                tenders.append(tender_data)
                new_tenders.append(tender_data)
                
            except Exception as e:
                logger.error(f"Error parsing tender listing: {e}")
                continue
        
        logger.info(f"Successfully extracted {len(tenders)} C&F-related tenders, {len(new_tenders)} are new")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching GeM tenders: {e}")
        # Retry once after a short delay
        try:
            logger.info("Retrying after 5 seconds...")
            time.sleep(5)
            response = requests.get(gem_url, timeout=30)
            response.raise_for_status()
            # Process response (simplified for brevity)
            # In a real implementation, this would duplicate the processing code above
        except requests.exceptions.RequestException as retry_e:
            logger.error(f"Retry failed: {retry_e}")
    
    return new_tenders


def get_existing_url_hashes() -> Set[str]:
    """
    Get a set of URL hashes for tenders that already exist in the database.
    
    Returns:
        Set[str]: A set of URL hash strings
    """
    try:
        # Import here to avoid circular imports
        from logilead.db import get_db_session, Tender
        
        session = get_db_session()
        try:
            # Query all URL hashes from the database
            result = session.query(Tender.url_hash).all()
            return {row[0] for row in result}
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error retrieving existing URL hashes: {e}")
        return set()


def fetch_new_gem_tenders() -> List[Dict]:
    """
    Fetch only new tenders from the GeM portal that don't exist in the database.
    
    Returns:
        List[Dict]: A list of dictionaries containing new tender information
    """
    # Get existing URL hashes from the database
    existing_url_hashes = get_existing_url_hashes()
    logger.info(f"Found {len(existing_url_hashes)} existing tenders in the database")
    
    # Fetch tenders, skipping those that already exist
    return fetch_gem_tenders(existing_url_hashes)


def _parse_gem_date(date_string: str) -> str:
    """
    Parse and normalize a date string from the GeM portal to ISO format.
    
    Args:
        date_string: The date string to parse (e.g., "Last Date: 15-Apr-2025")
        
    Returns:
        str: The date in ISO format (YYYY-MM-DD)
    """
    try:
        # Remove any prefix text and extract just the date part
        date_part = date_string.split(':')[-1].strip()
        
        # Parse the date - format may vary, adjust as needed
        date_obj = datetime.strptime(date_part, '%d-%b-%Y')
        
        # Return in ISO format
        return date_obj.date().isoformat()
    except Exception as e:
        logger.error(f"Error parsing date '{date_string}': {e}")
        return None


def _is_cf_related(title: str) -> bool:
    """
    Check if a tender is related to Clearing & Forwarding (C&F).
    
    Args:
        title: The tender title to check
        
    Returns:
        bool: True if the tender is C&F-related, False otherwise
    """
    # List of keywords related to C&F
    cf_keywords = [
        'clearing', 'forwarding', 'c&f', 'c & f', 'freight', 'logistics',
        'shipping', 'transport', 'cargo', 'customs', 'export', 'import'
    ]
    
    # Convert title to lowercase for case-insensitive matching
    title_lower = title.lower()
    
    # Check if any keyword is in the title
    return any(keyword in title_lower for keyword in cf_keywords)
