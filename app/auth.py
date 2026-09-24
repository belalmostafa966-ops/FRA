import hashlib
import hmac
import datetime
import jwt
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from models import User

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

def hash_password(password: str) -> str:
    """Hash password securely using bcrypt or SHA-256 fallback."""
    if HAS_BCRYPT:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    else:
        # Fallback secure hash
        key = SECRET_KEY.encode("utf-8")
        return hmac.new(key, password.encode("utf-8"), hashlib.sha256).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    if HAS_BCRYPT and hashed_password.startswith("$2"):
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False
    # Fallback verification
    key = SECRET_KEY.encode("utf-8")
    expected = hmac.new(key, plain_password.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Create signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None

def authenticate_user(db: Session, email_or_username: str, password: str) -> Optional[User]:
    """Authenticate user by email or username."""
    user = db.query(User).filter(
        (User.email == email_or_username) | (User.username == email_or_username)
    ).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def seed_default_users(db: Session):
    """Seed system default accounts for all 4 roles if missing."""
    default_users = [
        {
            "username": "admin",
            "email": "admin@fra.gov.eg",
            "password": "Admin@123",
            "role": "Admin",
        },
        {
            "username": "analyst",
            "email": "analyst@fra.gov.eg",
            "password": "Analyst@123",
            "role": "Risk Analyst",
        },
        {
            "username": "executive",
            "email": "executive@fra.gov.eg",
            "password": "Exec@123",
            "role": "Executive",
        },
        {
            "username": "inspector",
            "email": "inspector@fra.gov.eg",
            "password": "Inspector@123",
            "role": "Inspector",
        },
    ]

    for u in default_users:
        existing = db.query(User).filter(User.username == u["username"]).first()
        if not existing:
            user_obj = User(
                username=u["username"],
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                role=u["role"],
                is_active=True
            )
            db.add(user_obj)
    db.commit()
