"""
Lead filtering and tagging module for LogiLead AI.

This module provides functions to filter and tag leads (news articles,
job postings, etc.) based on configurable criteria.
"""

import logging
import os
import re
from typing import Dict, List, Optional, Set

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get key terms and job titles from environment variables
KEY_TERMS = os.getenv("KEY_TERMS", "logistics,warehouse,C&F").split(",")
JOB_TITLES = os.getenv("JOB_TITLES", "Logistics Manager,Warehouse Supervisor").split(",")

# Normalize keywords (strip whitespace, convert to lowercase)
KEY_TERMS = [term.strip().lower() for term in KEY_TERMS if term.strip()]
JOB_TITLES = [title.strip().lower() for title in JOB_TITLES if title.strip()]


def contains_any_term(text: str, terms: List[str]) -> bool:
    """
    Check if text contains any of the specified terms.
    
    The check is case-insensitive and matches whole or partial words.
    
    Args:
        text: The text to check
        terms: List of terms to look for
        
    Returns:
        bool: True if any term is found in the text, False otherwise
    """
    if not text or not terms:
        return False
        
    text_lower = text.lower()
    
    for term in terms:
        if term in text_lower:
            return True
            
    return False


def filter_news_lead(lead: Dict) -> bool:
    """
    Check if a news lead contains key terms of interest.
    
    Args:
        lead: News lead dictionary with 'title' and 'snippet' keys
        
    Returns:
        bool: True if the lead contains key terms, False otherwise
    """
    # Check if required keys exist
    if 'title' not in lead or 'snippet' not in lead:
        logger.warning(f"News lead missing required fields: {lead}")
        return False
        
    title = lead.get('title', '')
    snippet = lead.get('snippet', '')
    
    # Check if title or snippet contains any key term
    return contains_any_term(title, KEY_TERMS) or contains_any_term(snippet, KEY_TERMS)


def filter_job_lead(lead: Dict) -> bool:
    """
    Check if a job lead matches job titles of interest.
    
    Args:
        lead: Job lead dictionary with 'job_title' key
        
    Returns:
        bool: True if the lead matches job titles, False otherwise
    """
    # Check if required key exists
    if 'job_title' not in lead:
        logger.warning(f"Job lead missing required field: {lead}")
        return False
        
    job_title = lead.get('job_title', '')
    
    # Check if job title contains any target job title term
    return contains_any_term(job_title, JOB_TITLES)


def tag_lead(lead: Dict, lead_type: str) -> Dict:
    """
    Tag a lead with its type.
    
    Args:
        lead: Lead dictionary
        lead_type: Type of lead ('news', 'job', etc.)
        
    Returns:
        Dict: Lead dictionary with 'lead_type' field added
    """
    # Create a copy to avoid modifying the original
    tagged_lead = lead.copy()
    
    # Add lead_type tag
    tagged_lead['lead_type'] = lead_type
    
    return tagged_lead


def filter_leads(leads: List[Dict], lead_type: str) -> List[Dict]:
    """
    Filter leads based on their type and content.
    
    This function filters a list of leads based on the specified lead type:
    - For "news" leads: Checks if title or snippet contains key terms.
    - For "job" leads: Checks if job title matches target job titles.
    
    Each passing lead is tagged with a 'lead_type' field.
    
    Args:
        leads: List of lead dictionaries
        lead_type: Type of leads ('news' or 'job')
        
    Returns:
        List[Dict]: Filtered and tagged leads
    """
    if not leads:
        logger.info(f"No {lead_type} leads to filter")
        return []
        
    filtered_leads = []
    
    logger.info(f"Filtering {len(leads)} {lead_type} leads")
    
    for lead in leads:
        # Apply appropriate filter based on lead type
        if lead_type == "news":
            matches = filter_news_lead(lead)
        elif lead_type == "job":
            matches = filter_job_lead(lead)
        else:
            logger.warning(f"Unknown lead type: {lead_type}")
            matches = False
            
        if matches:
            # Tag and add matching lead
            tagged_lead = tag_lead(lead, lead_type)
            filtered_leads.append(tagged_lead)
    
    logger.info(f"Found {len(filtered_leads)} matching {lead_type} leads out of {len(leads)}")
    
    return filtered_leads


if __name__ == "__main__":
    # Example usage
    test_news = [
        {"title": "Logistics company expands operations", "snippet": "A major logistics provider is expanding..."},
        {"title": "New restaurant opens", "snippet": "Downtown sees a new food option..."}
    ]
    
    test_jobs = [
        {"job_title": "Logistics Manager", "company_name": "ABC Corp"},
        {"job_title": "Software Developer", "company_name": "XYZ Inc"}
    ]
    
    # Filter news leads
    filtered_news = filter_leads(test_news, "news")
    print(f"Filtered {len(filtered_news)} news leads:")
    for news in filtered_news:
        print(f"- {news['title']} (Type: {news['lead_type']})")
        
    # Filter job leads
    filtered_jobs = filter_leads(test_jobs, "job")
    print(f"Filtered {len(filtered_jobs)} job leads:")
    for job in filtered_jobs:
        print(f"- {job['job_title']} (Type: {job['lead_type']})")
