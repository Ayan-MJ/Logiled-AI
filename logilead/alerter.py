"""
Email alerting module for LogiLead AI.

This module handles sending email notifications about new leads.
"""

import logging
import os
import smtplib
import textwrap
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional

from dotenv import load_dotenv

from logilead.db import get_db_session, Lead, get_top_leads_by_type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get SMTP configuration from environment variables
SMTP_HOST = os.getenv("LOGILEAD_SMTP_HOST")
SMTP_PORT = int(os.getenv("LOGILEAD_SMTP_PORT", "587"))
SMTP_USER = os.getenv("LOGILEAD_SMTP_USER")
SMTP_PASS = os.getenv("LOGILEAD_SMTP_PASS")
ALERT_RECIPIENTS = os.getenv("LOGILEAD_ALERT_RECIPIENTS", "").split(",")

# Last alert timestamp file
LAST_ALERT_FILE = os.path.join(os.path.dirname(__file__), "..", "last_alert.txt")


def send_email(subject: str, body: str, recipients: List[str]) -> bool:
    """
    Send an email using SMTP credentials from environment variables.
    
    Args:
        subject: Email subject
        body: Email body (plain text)
        recipients: List of email addresses to send to
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS]):
        logger.error("SMTP configuration is incomplete. Check environment variables.")
        return False
    
    if not recipients:
        logger.warning("No recipients specified for email alert")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        
        # Attach body with 72-char wrapping as per Windsurf rules
        wrapped_body = "\n".join(
            textwrap.fill(line, width=72) if not line.startswith("•") else line
            for line in body.split("\n")
        )
        msg.attach(MIMEText(wrapped_body, 'plain'))
        
        # Connect to SMTP server
        logger.info(f"Connecting to SMTP server {SMTP_HOST}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email alert sent successfully to {len(recipients)} recipients")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email alert: {e}")
        # Retry once
        try:
            logger.info("Retrying email send...")
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            server.quit()
            logger.info("Retry successful")
            return True
        except Exception as retry_e:
            logger.error(f"Retry failed: {retry_e}")
            return False


def get_last_alert_time() -> Optional[datetime]:
    """
    Get the timestamp of the last alert sent.
    
    Returns:
        Optional[datetime]: Timestamp of the last alert, or None if no previous alert
    """
    try:
        if os.path.exists(LAST_ALERT_FILE):
            with open(LAST_ALERT_FILE, 'r') as f:
                timestamp_str = f.read().strip()
                return datetime.fromisoformat(timestamp_str)
        return None
    except Exception as e:
        logger.error(f"Error reading last alert timestamp: {e}")
        return None


def save_last_alert_time(timestamp: datetime = None) -> None:
    """
    Save the timestamp of the current alert.
    
    Args:
        timestamp: Timestamp to save, defaults to current time
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    try:
        with open(LAST_ALERT_FILE, 'w') as f:
            f.write(timestamp.isoformat())
    except Exception as e:
        logger.error(f"Error saving last alert timestamp: {e}")


def get_new_leads_since(lead_type: Optional[str] = None, since: Optional[datetime] = None) -> List[Lead]:
    """
    Get leads that were added to the database since the specified time.
    
    Args:
        lead_type: Optional lead type filter
        since: Timestamp to filter leads by, defaults to 24 hours ago
        
    Returns:
        List[Lead]: List of new Lead objects
    """
    if since is None:
        # Default to 24 hours ago if no timestamp provided
        since = datetime.now() - timedelta(days=1)
    
    session = get_db_session()
    try:
        # Query leads created since the specified time
        query = session.query(Lead).filter(Lead.created_at >= since)
        
        # Add lead type filter if specified
        if lead_type:
            query = query.filter(Lead.lead_type == lead_type)
            
        # Order by lead_score descending
        query = query.order_by(Lead.lead_score.desc())
        
        return query.all()
    except Exception as e:
        logger.error(f"Error querying new leads: {e}")
        return []
    finally:
        session.close()


def format_lead_for_email(lead: Lead) -> str:
    """
    Format a lead for inclusion in an email digest.
    
    Args:
        lead: Lead object to format
        
    Returns:
        str: Formatted lead string
    """
    # Basic information common to all lead types
    title = lead.title
    company = lead.issuer_or_company or "Unknown"
    location = f"({lead.location})" if lead.location else ""
    score = f"Score: {lead.lead_score:.2f}" if lead.lead_score else ""
    
    # Format according to Windsurf rules:
    # "• {title} – {issuer_or_company} ({location}) – Score: {lead_score:.2f}"
    line = f"• {title} – {company} {location}"
    
    if score:
        line += f" – {score}"
        
    return line


def format_leads_by_type(leads_by_type: Dict[str, List[Lead]]) -> str:
    """
    Format a digest of leads grouped by type.
    
    Args:
        leads_by_type: Dictionary of lead lists keyed by lead_type
        
    Returns:
        str: Formatted digest text
    """
    if not leads_by_type:
        return "No new leads found."
    
    sections = []
    
    # Format tenders section
    if 'tender' in leads_by_type and leads_by_type['tender']:
        tender_leads = leads_by_type['tender']
        tender_section = ["🔥 Top Tenders:"]
        for lead in tender_leads:
            tender_section.append(format_lead_for_email(lead))
        sections.append("\n".join(tender_section))
    
    # Format news section
    if 'news' in leads_by_type and leads_by_type['news']:
        news_leads = leads_by_type['news']
        news_section = ["📣 Top News Leads:"]
        for lead in news_leads:
            news_section.append(format_lead_for_email(lead))
        sections.append("\n".join(news_section))
    
    # Format job section
    if 'job' in leads_by_type and leads_by_type['job']:
        job_leads = leads_by_type['job']
        job_section = ["💼 Top Job Leads:"]
        for lead in job_leads:
            job_section.append(format_lead_for_email(lead))
        sections.append("\n".join(job_section))
    
    # Join all sections with double newlines
    return "\n\n".join(sections)


def send_lead_digest() -> bool:
    """
    Send a digest email of new leads since the last alert.
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Get the timestamp of the last alert
    last_alert_time = get_last_alert_time()
    logger.info(f"Last alert time: {last_alert_time}")
    
    # Get top leads by type from the last 24 hours
    hours = 24
    leads_by_type = get_top_leads_by_type(hours=hours, limit_per_type=5)
    
    total_leads = sum(len(leads) for leads in leads_by_type.values())
    logger.info(f"Found {total_leads} leads to include in digest")
    
    # If no leads, don't send an email
    if total_leads == 0:
        logger.info("No leads to report")
        return True
    
    # Format the lead summary
    summary = format_leads_by_type(leads_by_type)
    
    # Send the email
    subject = f"LogiLead AI: {total_leads} New Leads - {datetime.now().strftime('%Y-%m-%d')}"
    recipients = ALERT_RECIPIENTS
    
    success = send_email(subject, summary, recipients)
    
    # If email was sent successfully, update the last alert timestamp
    if success:
        save_last_alert_time()
    
    return success


def send_tender_digest() -> bool:
    """
    Send a digest email of new tenders since the last alert.
    (Legacy function, use send_lead_digest instead)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Get the timestamp of the last alert
    last_alert_time = get_last_alert_time()
    
    # Get new tenders since the last alert
    new_leads = get_new_leads_since('tender', last_alert_time)
    logger.info(f"Found {len(new_leads)} new tenders since last alert")
    
    # If no new tenders, don't send an email
    if not new_leads:
        logger.info("No new tenders to report")
        return True
    
    # Format the tender summary
    lines = ["New C&F tenders:"]
    
    for lead in new_leads:
        # Format deadline
        deadline_str = lead.deadline.strftime("%Y-%m-%d") if lead.deadline else "N/A"
        
        # Format line according to Windsurf rules:
        # "• Title – Issuer (City) – YYYY-MM-DD"
        line = f"• {lead.title} – {lead.issuer_or_company}"
        if lead.location:
            line += f" ({lead.location})"
        line += f" – Deadline: {deadline_str}"
        
        lines.append(line)
    
    summary = "\n".join(lines)
    
    # Send the email
    subject = f"LogiLead AI: {len(new_leads)} New Tenders - {datetime.now().strftime('%Y-%m-%d')}"
    recipients = ALERT_RECIPIENTS
    
    success = send_email(subject, summary, recipients)
    
    # If email was sent successfully, update the last alert timestamp
    if success:
        save_last_alert_time()
    
    return success


if __name__ == "__main__":
    # Test the email functionality
    from logilead.db import create_tables
    
    # Ensure database tables exist
    create_tables()
    
    # Send a test digest
    success = send_lead_digest()
    
    if success:
        print("Test digest email sent successfully")
    else:
        print("Failed to send test digest email")
