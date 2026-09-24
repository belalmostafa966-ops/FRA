import html
import re
from sqlalchemy.orm import Session
from models import ActivityLog

def sanitize_input(input_str: str) -> str:
    """
    Sanitizes user input strings against XSS (Cross-Site Scripting) and script injection.
    Escapes HTML entities and trims unsafe script tags.
    """
    if not isinstance(input_str, str):
        return input_str
    # Strip script tags
    clean = re.sub(r'<script[^>]*>.*?</script>', '', input_str, flags=re.DOTALL | re.IGNORECASE)
    # HTML escape
    return html.escape(clean.strip())

def log_activity(db: Session, username: str, action: str, details: str = None, user_id: int = None):
    """
    Logs security and administrative activity for audit trail compliance.
    """
    try:
        log_entry = ActivityLog(
            user_id=user_id,
            username=sanitize_input(username),
            action=sanitize_input(action),
            details=sanitize_input(details) if details else None
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to record activity log: {e}")
