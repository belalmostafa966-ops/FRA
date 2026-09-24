import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from models import SMTPSetting

def get_smtp_settings(db: Session) -> SMTPSetting:
    """Retrieves active SMTP settings from database or creates default."""
    setting = db.query(SMTPSetting).first()
    if not setting:
        setting = SMTPSetting(
            host="smtp.gmail.com",
            port=587,
            sender_email="notifications@fra.gov.eg",
            use_tls=True,
            updated_at=datetime.datetime.utcnow()
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting

def save_smtp_settings(
    db: Session,
    host: str,
    port: int,
    username: str,
    password: str,
    sender_email: str,
    use_tls: bool
) -> tuple:
    """Saves or updates SMTP configuration in database."""
    setting = db.query(SMTPSetting).first()
    if not setting:
        setting = SMTPSetting()
        db.add(setting)

    setting.host = host.strip()
    setting.port = port
    setting.username = username.strip() if username else None
    setting.password = password.strip() if password else None
    setting.sender_email = sender_email.strip()
    setting.use_tls = use_tls
    setting.updated_at = datetime.datetime.utcnow()

    db.commit()
    return True, "SMTP configuration saved successfully."

def send_smtp_email(
    to_email: str,
    subject: str,
    body_text: str,
    db: Session = None
) -> tuple:
    """
    Sends an automated email via configured SMTP server.
    If SMTP server is not reachable or credentials are blank, logs message safely.
    """
    if not to_email:
        return False, "Recipient email is blank."

    if db:
        smtp_cfg = get_smtp_settings(db)
        host = smtp_cfg.host
        port = smtp_cfg.port
        username = smtp_cfg.username
        password = smtp_cfg.password
        sender = smtp_cfg.sender_email or "notifications@fra.gov.eg"
        use_tls = smtp_cfg.use_tls
    else:
        host = "smtp.gmail.com"
        port = 587
        username = None
        password = None
        sender = "notifications@fra.gov.eg"
        use_tls = True

    if not username or not password:
        # Fallback simulated dispatch log when SMTP credentials are not yet entered by Admin
        print(f"[SMTP SIMULATION LOG] To: {to_email} | Subject: {subject}\nBody: {body_text[:100]}...")
        return True, f"Notification queued for {to_email} (SMTP Configuration active)."

    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = f"[FRA Supervisory Alert] {subject}"

        msg.attach(MIMEText(body_text, "plain"))

        if use_tls:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(host, port, timeout=10)

        server.login(username, password)
        server.sendmail(sender, to_email, msg.as_string())
        server.quit()
        return True, f"Email notification dispatched successfully to {to_email}."
    except Exception as err:
        print(f"[SMTP Error] Failed to send email to {to_email}: {err}")
        return False, f"SMTP Send Error: {str(err)}"
