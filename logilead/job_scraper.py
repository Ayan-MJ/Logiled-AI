"""
Job board scraping module for LogiLead AI.

This module contains functions to scrape job listings from job boards
like Naukri.com based on specified job titles and locations.
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import re

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

# Get job search parameters from environment variables
JOB_TITLES = os.getenv("JOB_TITLES", "Logistics Manager,Warehouse Supervisor").split(",")
TARGET_CITIES = os.getenv("TARGET_CITIES", "Mumbai,Bangalore,Delhi").split(",")

# Base URL for Naukri.com search
NAUKRI_SEARCH_URL = "https://www.naukri.com/jobapi/v3/search"


def construct_naukri_search_url(job_title: str, location: str) -> str:
    """
    Construct a search URL for Naukri.com based on job title and location.
    
    Args:
        job_title: The job title to search for
        location: The location/city to search in
        
    Returns:
        str: The constructed search URL
    """
    # URL encode the parameters
    import urllib.parse
    encoded_title = urllib.parse.quote(job_title)
    encoded_location = urllib.parse.quote(location)
    
    # Construct the URL
    # Note: This URL structure may need to be updated if Naukri changes their API
    return f"{NAUKRI_SEARCH_URL}?noOfResults=20&searchType=adv&keyword={encoded_title}&location={encoded_location}"


def parse_naukri_date(date_text: str) -> str:
    """
    Parse and normalize a date string from Naukri.com to ISO format.
    
    Args:
        date_text: Date text from Naukri.com (e.g., "2 days ago", "Just now", etc.)
        
    Returns:
        str: The date in ISO format (YYYY-MM-DD)
    """
    today = datetime.now().date()
    
    # Handle common date formats
    if not date_text or date_text.lower() == "just now" or date_text.lower() == "today":
        return today.isoformat()
    
    if "hour" in date_text.lower() or "minute" in date_text.lower():
        return today.isoformat()
    
    if "yesterday" in date_text.lower():
        yesterday = today - timedelta(days=1)
        return yesterday.isoformat()
    
    # Handle "X days ago"
    days_ago_match = re.search(r'(\d+)\s*days?\s*ago', date_text.lower())
    if days_ago_match:
        days = int(days_ago_match.group(1))
        past_date = today - timedelta(days=days)
        return past_date.isoformat()
    
    # Handle "X weeks ago"
    weeks_ago_match = re.search(r'(\d+)\s*weeks?\s*ago', date_text.lower())
    if weeks_ago_match:
        weeks = int(weeks_ago_match.group(1))
        past_date = today - timedelta(weeks=weeks)
        return past_date.isoformat()
    
    # Handle "X months ago"
    months_ago_match = re.search(r'(\d+)\s*months?\s*ago', date_text.lower())
    if months_ago_match:
        # Approximate month as 30 days
        months = int(months_ago_match.group(1))
        past_date = today - timedelta(days=30*months)
        return past_date.isoformat()
    
    # For any other format, try to parse it or return today's date
    try:
        # This will need adjustments based on actual formats encountered
        parsed_date = datetime.strptime(date_text, "%b %d, %Y").date()
        return parsed_date.isoformat()
    except ValueError:
        logger.warning(f"Could not parse date string: {date_text}, using today's date")
        return today.isoformat()


def scrape_naukri_jobs(job_title: str, city: str) -> List[Dict]:
    """
    Scrape job listings from Naukri.com for a specific job title and city.
    
    Args:
        job_title: The job title to search for
        city: The city/location to search in
        
    Returns:
        List[Dict]: A list of job posting dictionaries
    """
    url = construct_naukri_search_url(job_title, city)
    job_postings = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
    }
    
    try:
        logger.info(f"Scraping Naukri.com for '{job_title}' in '{city}'")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Naukri returns JSON
        job_data = response.json()
        
        # Extract job listings from the response
        if 'jobDetails' in job_data:
            jobs = job_data['jobDetails']
            logger.info(f"Found {len(jobs)} job postings for '{job_title}' in '{city}'")
            
            for job in jobs:
                try:
                    # Extract job details
                    job_url = job.get('jdURL', '')
                    
                    # Create URL hash for deduplication
                    url_hash = hashlib.sha256(job_url.encode()).hexdigest()
                    
                    posting = {
                        'job_title': job.get('title', 'Unknown Title'),
                        'company_name': job.get('companyName', 'Unknown Company'),
                        'location': job.get('placeholders', [{}])[0].get('location', city),
                        'published_at': parse_naukri_date(job.get('footerPlaceholderLabel', '')),
                        'url': job_url,
                        'url_hash': url_hash,
                        'source': 'Naukri',
                        'fetched_at': datetime.now().isoformat()
                    }
                    
                    job_postings.append(posting)
                    
                except Exception as e:
                    logger.error(f"Error processing job posting: {e}")
                    continue
                
        else:
            logger.warning(f"No job details found in response for '{job_title}' in '{city}'")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching job listings from Naukri.com: {e}")
        # Retry once
        try:
            logger.info("Retrying after 5 seconds...")
            time.sleep(5)
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Process the retry response
            job_data = response.json()
            if 'jobDetails' in job_data:
                jobs = job_data['jobDetails']
                logger.info(f"Retry successful. Found {len(jobs)} job postings")
                
                for job in jobs:
                    # Extract job details (same as above)
                    job_url = job.get('jdURL', '')
                    url_hash = hashlib.sha256(job_url.encode()).hexdigest()
                    
                    posting = {
                        'job_title': job.get('title', 'Unknown Title'),
                        'company_name': job.get('companyName', 'Unknown Company'),
                        'location': job.get('placeholders', [{}])[0].get('location', city),
                        'published_at': parse_naukri_date(job.get('footerPlaceholderLabel', '')),
                        'url': job_url,
                        'url_hash': url_hash,
                        'source': 'Naukri',
                        'fetched_at': datetime.now().isoformat()
                    }
                    
                    job_postings.append(posting)
                    
        except requests.exceptions.RequestException as retry_e:
            logger.error(f"Retry failed: {retry_e}")
    
    return job_postings


def fetch_job_postings() -> List[Dict]:
    """
    Fetch job postings from Naukri.com based on job titles and cities
    specified in environment variables.
    
    This function iterates through all combinations of job titles and target cities,
    scraping job listings for each combination.
    
    Returns:
        List[Dict]: A list of job posting dictionaries with keys:
            - job_title: The job title
            - company_name: The name of the hiring company
            - location: The job location
            - published_at: Publication date (ISO format)
            - url: URL to the job posting
            - url_hash: SHA-256 hash of the URL for deduplication
            - source: The source of the job posting (always 'Naukri')
            - fetched_at: Timestamp when fetched (ISO format)
    """
    all_job_postings = []
    
    for job_title in JOB_TITLES:
        job_title = job_title.strip()
        if not job_title:
            continue
            
        for city in TARGET_CITIES:
            city = city.strip()
            if not city:
                continue
                
            try:
                # Scrape jobs for this title and city
                job_postings = scrape_naukri_jobs(job_title, city)
                all_job_postings.extend(job_postings)
                
                # Be nice to the server
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scraping jobs for '{job_title}' in '{city}': {e}")
                continue
    
    logger.info(f"Fetched a total of {len(all_job_postings)} job postings")
    return all_job_postings


if __name__ == "__main__":
    # Test the job scraping
    jobs = fetch_job_postings()
    
    print(f"Found {len(jobs)} job postings:")
    for i, job in enumerate(jobs):
        print(f"{i+1}. {job['job_title']} - {job['company_name']}")
        print(f"   Location: {job['location']}")
        print(f"   Published: {job['published_at']}")
        print(f"   URL: {job['url']}")
        print("-" * 80)
