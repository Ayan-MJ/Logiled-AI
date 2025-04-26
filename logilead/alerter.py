"""
Email alerting module for LogiLead AI.

This module handles sending email notifications about new tenders.
"""

import logging
import os
import smtplib
import textwrap
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from dotenv import load_dotenv

from logilead.db import get_db_session, Tender

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
            textwrap.fill(line, width=72) if not line.startswith("• ") else line
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


def get_new_tenders_since(since: Optional[datetime] = None) -> List[Tender]:
    """
    Get tenders that were added to the database since the specified time.
    
    Args:
        since: Timestamp to filter tenders by, defaults to 24 hours ago
        
    Returns:
        List[Tender]: List of new Tender objects
    """
    if since is None:
        # Default to 24 hours ago if no timestamp provided
        since = datetime.now() - timedelta(days=1)
    
    session = get_db_session()
    try:
        # Query tenders created since the specified time
        return session.query(Tender).filter(Tender.created_at >= since).all()
    except Exception as e:
        logger.error(f"Error querying new tenders: {e}")
        return []
    finally:
        session.close()


def format_tender_summary(tenders: List[Tender]) -> str:
    """
    Format a list of tenders into a plain text summary.
    
    Args:
        tenders: List of Tender objects
        
    Returns:
        str: Formatted summary text
    """
    if not tenders:
        return "No new tenders found."
    
    lines = ["New C&F tenders:"]
    
    for tender in tenders:
        # Format deadline
        deadline_str = tender.deadline.strftime("%Y-%m-%d") if tender.deadline else "N/A"
        
        # Format line according to Windsurf rules:
        # "• Title – Issuer (City) – YYYY-MM-DD"
        line = f"• {tender.title} – {tender.issuer}"
        if tender.location:
            line += f" ({tender.location})"
        line += f" – Deadline: {deadline_str}"
        
        lines.append(line)
    
    return "\n".join(lines)


def send_tender_digest() -> bool:
    """
    Send a digest email of new tenders since the last alert.
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Get the timestamp of the last alert
    last_alert_time = get_last_alert_time()
    logger.info(f"Last alert time: {last_alert_time}")
    
    # Get new tenders since the last alert
    new_tenders = get_new_tenders_since(last_alert_time)
    logger.info(f"Found {len(new_tenders)} new tenders since last alert")
    
    # If no new tenders, don't send an email
    if not new_tenders:
        logger.info("No new tenders to report")
        return True
    
    # Format the tender summary
    summary = format_tender_summary(new_tenders)
    
    # Send the email
    subject = f"LogiLead AI: {len(new_tenders)} New C&F Tenders - {datetime.now().strftime('%Y-%m-%d')}"
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
    success = send_tender_digest()
    
    if success:
        print("Test digest email sent successfully")
    else:
        print("Failed to send test digest email")
