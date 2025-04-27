"""
Lead scoring module for LogiLead AI.

This module provides functions to score leads (tenders, news articles,
job postings) based on various criteria to help prioritize them.
"""

import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from dateutil import parser
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get key terms from environment variables
KEY_TERMS = os.getenv("KEY_TERMS", "logistics,warehouse,C&F").split(",")

# Normalize keywords (strip whitespace, convert to lowercase)
KEY_TERMS = [term.strip().lower() for term in KEY_TERMS if term.strip()]


def count_term_matches(text: str, terms: List[str]) -> int:
    """
    Count how many terms from the provided list appear in the text.
    
    Args:
        text: The text to check
        terms: List of terms to count
        
    Returns:
        int: Number of unique terms found in the text
    """
    if not text or not terms:
        return 0
        
    text_lower = text.lower()
    match_count = 0
    
    for term in terms:
        if term in text_lower:
            match_count += 1
            
    return match_count


def count_news_keywords(lead: Dict) -> int:
    """
    Count how many key terms appear in a news article's title and snippet.
    
    Args:
        lead: News lead dictionary with 'title' and 'snippet' keys
        
    Returns:
        int: Number of key term matches
    """
    title = lead.get('title', '')
    snippet = lead.get('snippet', '')
    
    # Count matches in title and snippet
    title_matches = count_term_matches(title, KEY_TERMS)
    snippet_matches = count_term_matches(snippet, KEY_TERMS)
    
    return title_matches + snippet_matches


def calculate_job_age_days(lead: Dict) -> int:
    """
    Calculate the age of a job posting in days.
    
    Args:
        lead: Job lead dictionary with 'published_at' key
        
    Returns:
        int: Age of the job posting in days
    """
    published_at_str = lead.get('published_at')
    
    if not published_at_str:
        logger.warning(f"Job lead missing published_at field: {lead}")
        return 0
        
    try:
        # Parse the date string
        published_at = parser.parse(published_at_str).date()
        
        # Calculate the difference in days
        today = datetime.now().date()
        days_diff = (today - published_at).days
        
        # Ensure non-negative value
        return max(0, days_diff)
        
    except Exception as e:
        logger.error(f"Error parsing date {published_at_str}: {e}")
        return 0


def score_lead(lead: Dict) -> float:
    """
    Score a lead based on its type and content.
    
    Scoring logic:
    - Tenders: Fixed score of 3.0
    - News: 2.0 + 0.1 * (number of KEY_TERMS matches in title + snippet)
    - Jobs: 1.0 + 0.05 * age_in_days
    
    Args:
        lead: Lead dictionary with 'lead_type' key
        
    Returns:
        float: Calculated score
    """
    lead_type = lead.get('lead_type', '')
    
    if not lead_type:
        logger.warning(f"Lead missing lead_type field: {lead}")
        return 0.0
        
    if lead_type == "tender":
        # Tenders get a fixed high score
        return 3.0
        
    elif lead_type == "news":
        # News score based on keyword matches
        keyword_matches = count_news_keywords(lead)
        return 2.0 + 0.1 * keyword_matches
        
    elif lead_type == "job":
        # Job score based on age in days
        age_days = calculate_job_age_days(lead)
        return 1.0 + 0.05 * age_days
        
    else:
        # Unknown lead type
        logger.warning(f"Unknown lead type: {lead_type}")
        return 0.0


def assign_scores(leads: List[Dict]) -> List[Dict]:
    """
    Assign scores to a list of leads.
    
    This function calculates a score for each lead and adds a 'lead_score'
    field to the lead dictionary with the computed value.
    
    Args:
        leads: List of lead dictionaries
        
    Returns:
        List[Dict]: The leads with added 'lead_score' field
    """
    if not leads:
        logger.info("No leads to score")
        return []
        
    scored_leads = []
    
    logger.info(f"Scoring {len(leads)} leads")
    
    for lead in leads:
        # Create a copy to avoid modifying the original
        scored_lead = lead.copy()
        
        # Calculate and assign the score
        score = score_lead(lead)
        scored_lead['lead_score'] = score
        
        scored_leads.append(scored_lead)
    
    logger.info(f"Scored {len(scored_leads)} leads")
    
    return scored_leads


if __name__ == "__main__":
    # Example usage
    test_leads = [
        {'lead_type': 'tender', 'title': 'Logistics Tender', 'issuer': 'Government'},
        {'lead_type': 'news', 'title': 'Logistics Company Expanding', 'snippet': 'New warehouse facility'},
        {'lead_type': 'job', 'job_title': 'Logistics Manager', 'published_at': '2025-04-20'}
    ]
    
    scored_leads = assign_scores(test_leads)
    
    print("Scored leads:")
    for lead in scored_leads:
        lead_type = lead.get('lead_type', 'Unknown')
        title = lead.get('title', lead.get('job_title', 'Untitled'))
        score = lead.get('lead_score', 0.0)
        print(f"- {lead_type}: {title} - Score: {score:.2f}")
