"""SMTP email sender for digest delivery"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()


def send_digest_email(
    to_email: str,
    html_body: str,
    subject: str = "Your Daily Digest"
) -> bool:
    """
    Send digest HTML via SMTP.
    
    Args:
        to_email: Recipient email address
        html_body: HTML content of the digest
        subject: Email subject line
    
    Returns:
        True if sent successfully, False otherwise
    """
    server = os.getenv("SMTP_SERVER")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    
    if not all([server, username, password]):
        return False
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = username
    msg["To"] = to_email
    
    html_part = MIMEText(html_body, "html")
    msg.attach(html_part)
    
    try:
        with smtplib.SMTP(server, port) as smtp:
            smtp.starttls()
            smtp.login(username, password)
            smtp.sendmail(username, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email send failed: {e}", flush=True)
        return False
