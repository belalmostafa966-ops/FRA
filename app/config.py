import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "fra_risk_platform.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

SECRET_KEY = os.getenv("SECRET_KEY", "fra-secret-key-super-secure-regulatory-authority-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# Default Complaints Scoring Weights (Total = 1.0)
DEFAULT_COMPLAINT_WEIGHTS = {
    "vol_w": 0.20,      # Volume Weight
    "neg_w": 0.20,      # Negative Ratio Weight
    "sev_w": 0.20,      # High Severity Weight
    "open_w": 0.15,     # Open Complaints Ratio Weight
    "fraud_w": 0.10,    # Fraud Allegation Weight
    "growth_w": 0.15,   # Growth Rate Weight
}

# EWS Thresholds
EWS_THRESHOLDS = {
    "COMPLAINT_SCORE_CRITICAL": 75.0,
    "COMPLAINT_SCORE_HIGH": 60.0,
    "FINANCIAL_SCORE_CRITICAL": 75.0,
    "FINANCIAL_SCORE_HIGH": 60.0,
    "GROWTH_RATE_SPIKE": 0.35,  # 35% growth spike
    "FRAUD_RATIO_HIGH": 0.15,    # 15% of complaints involve fraud
}
