import sys
import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from database import Base
from config import DATABASE_URL
from models import User, Company, Complaint, FinancialRecord, RiskScoreHistory, ScoringWeight, ActivityLog, InspectionTask, Notification, CompanyReport, CompanyHistory
from auth import hash_password

MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DB = "fra_risk_db"

def setup_database():
    """
    Automated SQL Database Initialization Script.
    Connects to MySQL server (XAMPP), creates 'fra_risk_db' if missing,
    instantiates all SQLAlchemy tables, and seeds default records.
    Falls back to SQLite if MySQL service is unreachable.
    """
    print("=" * 60)
    print("[+] AUTOMATED SQL DATABASE SETUP - FRA RISK PLATFORM")
    print("=" * 60)

    db_url = None
    engine = None

    # Step 1: Try connecting to local MySQL server
    try:
        import pymysql
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            autocommit=True
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.close()

        db_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        print(f"[SUCCESS] MySQL Database '{MYSQL_DB}' created/verified at {MYSQL_HOST}:{MYSQL_PORT}")
    except Exception as err:
        print(f"[INFO] Could not connect to MySQL server ({err}). Using fallback database.")
        db_url = DATABASE_URL
        engine = create_engine(db_url, connect_args={"check_same_thread": False})

    # Step 2: Create all database tables
    print("[+] Instantiating database tables...")
    Base.metadata.create_all(bind=engine)
    print("  -> Tables created: users, companies, complaints, financial_records, risk_scores_history, scoring_weights, activity_logs.")

    # Step 3: Seed initial data
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    try:
        print("[+] Seeding default initial records...")

        # 3a. Seed Users
        if db.query(User).count() == 0:
            default_users = [
                User(username="admin", email="admin@fra.gov.eg", hashed_password=hash_password("Admin@123"), role="Admin", is_active=True),
                User(username="analyst", email="analyst@fra.gov.eg", hashed_password=hash_password("Analyst@123"), role="Risk Analyst", is_active=True),
                User(username="executive", email="executive@fra.gov.eg", hashed_password=hash_password("Exec@123"), role="Executive", is_active=True),
            ]
            db.add_all(default_users)
            db.commit()
            print("  -> Seeded 3 default users (admin, analyst, executive)")

        # 3b. Seed Scoring Weights
        if db.query(ScoringWeight).count() == 0:
            default_weight = ScoringWeight(
                vol_w=0.20, neg_w=0.20, sev_w=0.20, open_w=0.15, fraud_w=0.10, growth_w=0.15,
                updated_at=datetime.datetime.utcnow()
            )
            db.add(default_weight)
            db.commit()
            print("  -> Seeded default scoring weights (20/20/20/15/10/15)")

        # 3c. Seed Monitored Companies
        if db.query(Company).count() == 0:
            companies_data = [
                {"name": "EFG Hermes Holding", "tax_id": "TAX-EG-102938", "sector": "Capital Markets", "risk_level": "Low"},
                {"name": "Fawry Microfinance", "tax_id": "TAX-EG-493021", "sector": "Microfinance", "risk_level": "Medium"},
                {"name": "CI Capital Financial", "tax_id": "TAX-EG-884920", "sector": "Capital Markets", "risk_level": "Low"},
                {"name": "Valu Consumer Finance", "tax_id": "TAX-EG-304912", "sector": "Consumer Finance", "risk_level": "High"},
                {"name": "GIG Insurance Egypt", "tax_id": "TAX-EG-993810", "sector": "Insurance", "risk_level": "Low"},
                {"name": "Al Ahly Pharos Microfinance", "tax_id": "TAX-EG-558291", "sector": "Microfinance", "risk_level": "Critical"},
                {"name": "Corplot Leasing", "tax_id": "TAX-EG-774019", "sector": "Leasing", "risk_level": "Medium"},
                {"name": "Delta Insurance & Risk Services", "tax_id": "TAX-EG-661029", "sector": "Insurance", "risk_level": "Critical"},
            ]

            sample_complaints = {
                "EFG Hermes Holding": {"total": 24, "neg": 4, "sev": 1, "open": 2, "fraud": 0, "growth": 0.02},
                "Fawry Microfinance": {"total": 85, "neg": 32, "sev": 8, "open": 14, "fraud": 1, "growth": 0.18},
                "CI Capital Financial": {"total": 18, "neg": 3, "sev": 0, "open": 1, "fraud": 0, "growth": -0.05},
                "Valu Consumer Finance": {"total": 142, "neg": 68, "sev": 22, "open": 31, "fraud": 4, "growth": 0.35},
                "GIG Insurance Egypt": {"total": 30, "neg": 6, "sev": 2, "open": 3, "fraud": 0, "growth": 0.04},
                "Al Ahly Pharos Microfinance": {"total": 198, "neg": 110, "sev": 45, "open": 58, "fraud": 9, "growth": 0.62},
                "Corplot Leasing": {"total": 48, "neg": 15, "sev": 4, "open": 7, "fraud": 1, "growth": 0.12},
                "Delta Insurance & Risk Services": {"total": 215, "neg": 135, "sev": 52, "open": 64, "fraud": 12, "growth": 0.75},
            }

            sample_financials = {
                "EFG Hermes Holding": {"rev": 450000000.0, "net": 95000000.0, "assets": 1200000000.0, "liab": 400000000.0, "c_asset": 350000000.0, "c_liab": 150000000.0, "eq": 800000000.0, "cash": 180000000.0},
                "Fawry Microfinance": {"rev": 180000000.0, "net": 22000000.0, "assets": 420000000.0, "liab": 250000000.0, "c_asset": 120000000.0, "c_liab": 90000000.0, "eq": 170000000.0, "cash": 45000000.0},
                "CI Capital Financial": {"rev": 320000000.0, "net": 70000000.0, "assets": 850000000.0, "liab": 300000000.0, "c_asset": 280000000.0, "c_liab": 110000000.0, "eq": 550000000.0, "cash": 140000000.0},
                "Valu Consumer Finance": {"rev": 290000000.0, "net": -15000000.0, "assets": 600000000.0, "liab": 480000000.0, "c_asset": 150000000.0, "c_liab": 210000000.0, "eq": 120000000.0, "cash": 25000000.0},
                "GIG Insurance Egypt": {"rev": 510000000.0, "net": 82000000.0, "assets": 1100000000.0, "liab": 450000000.0, "c_asset": 380000000.0, "c_liab": 160000000.0, "eq": 650000000.0, "cash": 190000000.0},
                "Al Ahly Pharos Microfinance": {"rev": 95000000.0, "net": -38000000.0, "assets": 280000000.0, "liab": 240000000.0, "c_asset": 60000000.0, "c_liab": 140000000.0, "eq": 40000000.0, "cash": 8000000.0},
                "Corplot Leasing": {"rev": 210000000.0, "net": 28000000.0, "assets": 550000000.0, "liab": 360000000.0, "c_asset": 180000000.0, "c_liab": 120000000.0, "eq": 190000000.0, "cash": 35000000.0},
                "Delta Insurance & Risk Services": {"rev": 140000000.0, "net": -45000000.0, "assets": 320000000.0, "liab": 290000000.0, "c_asset": 70000000.0, "c_liab": 160000000.0, "eq": 30000000.0, "cash": 6000000.0},
            }

            sample_scores = {
                "EFG Hermes Holding": (12.5, 18.0, 15.2, "Low", False, None),
                "Fawry Microfinance": (42.0, 38.5, 40.2, "Medium", False, None),
                "CI Capital Financial": (10.0, 14.2, 12.1, "Low", False, None),
                "Valu Consumer Finance": (68.5, 72.0, 70.2, "High", True, "High Complaint Growth Surge | Operating Losses"),
                "GIG Insurance Egypt": (14.0, 16.5, 15.2, "Low", False, None),
                "Al Ahly Pharos Microfinance": (84.0, 81.5, 82.7, "Critical", True, "Excessive Open Complaints | Fraud Allegations | Negative Net Income"),
                "Corplot Leasing": (38.0, 34.0, 36.0, "Medium", False, None),
                "Delta Insurance & Risk Services": (91.0, 88.0, 89.5, "Critical", True, "High Fraud Allegations | Severely Impaired Equity"),
            }

            for c_info in companies_data:
                comp = Company(tax_id=c_info["tax_id"], name=c_info["name"], sector=c_info["sector"], risk_level=c_info["risk_level"])
                db.add(comp)
                db.flush()

                c_data = sample_complaints[comp.name]
                complaint = Complaint(
                    company_id=comp.id, quarter="Q1", year=2026,
                    total_complaints=c_data["total"], negative_count=c_data["neg"],
                    high_severity_count=c_data["sev"], open_count=c_data["open"],
                    fraud_allegation_count=c_data["fraud"], growth_rate=c_data["growth"]
                )
                db.add(complaint)

                f_data = sample_financials[comp.name]
                fin = FinancialRecord(
                    company_id=comp.id, quarter="Q1", year=2026,
                    revenue=f_data["rev"], net_income=f_data["net"],
                    total_assets=f_data["assets"], total_liabilities=f_data["liab"],
                    current_assets=f_data["c_asset"], current_liabilities=f_data["c_liab"],
                    total_equity=f_data["eq"], cash_and_equivalents=f_data["cash"]
                )
                db.add(fin)

                c_sc, f_sc, comp_sc, r_lvl, ews_flag, ews_reasons = sample_scores[comp.name]
                hist = RiskScoreHistory(
                    company_id=comp.id,
                    evaluation_date=datetime.datetime.utcnow(),
                    complaint_score=c_sc,
                    financial_score=f_sc,
                    composite_score=comp_sc,
                    risk_level=r_lvl,
                    ews_alert_flag=ews_flag,
                    ews_reasons=ews_reasons
                )
                db.add(hist)

            db.commit()
            print("  -> Seeded 8 monitored entities with full financial, complaint, and risk score histories.")

        # 3d. Seed Activity Logs
        if db.query(ActivityLog).count() == 0:
            logs = [
                ActivityLog(username="system", action="DATABASE_INIT", details="Automated SQL Database setup completed successfully."),
                ActivityLog(username="admin", action="SYSTEM_BOOT", details="FRA Risk Platform booted with default regulatory weights."),
                ActivityLog(username="analyst", action="DATA_SYNC", details="Synchronized Q1 2026 financial statements and complaints dataset."),
                ActivityLog(username="admin", action="WEIGHTS_UPDATE", details="Verified statutory default weights (20/20/20/15/10/15).")
            ]
            db.add_all(logs)
            db.commit()
            print("  -> Seeded initial system activity audit logs.")

        # 3e. Seed Inspection Tasks
        if db.query(InspectionTask).count() == 0:
            comp_ahly = db.query(Company).filter(Company.name == "Al Ahly Pharos Microfinance").first()
            comp_valu = db.query(Company).filter(Company.name == "Valu Consumer Finance").first()
            analyst_u = db.query(User).filter(User.username == "analyst").first()

            if comp_ahly and analyst_u:
                tasks_data = [
                    InspectionTask(
                        company_id=comp_ahly.id,
                        assigned_to_user_id=analyst_u.id,
                        inspector_username="analyst",
                        title="Urgent On-Site Audit - Fraud Allegation & Solvency Audit",
                        urgency="Critical",
                        status="In Progress",
                        scheduled_date=datetime.datetime.utcnow(),
                        findings_notes="Review of NPL provisions, loan books, and liquidity ratios following EWS fraud alerts.",
                        created_at=datetime.datetime.utcnow()
                    ),
                    InspectionTask(
                        company_id=comp_valu.id if comp_valu else comp_ahly.id,
                        assigned_to_user_id=analyst_u.id,
                        inspector_username="analyst",
                        title="Complaint Surge & Capital Adequacy Review",
                        urgency="High",
                        status="Scheduled",
                        scheduled_date=datetime.datetime.utcnow() + datetime.timedelta(days=3),
                        findings_notes="Follow up on 35% quarter-on-quarter complaint surge and evaluate minimum capital buffer.",
                        created_at=datetime.datetime.utcnow()
                    )
                ]
                db.add_all(tasks_data)
                db.commit()
                print("  -> Seeded 2 default inspection tasks.")

        # 3f. Seed System Notifications
        if db.query(Notification).count() == 0:
            notifs = [
                Notification(
                    title="Early Warning System (EWS) Alert Triggered",
                    message="Critical risk indicators flagged for Al Ahly Pharos Microfinance (High Fraud Allegations & Negative Equity).",
                    type="critical",
                    is_read=False,
                    created_at=datetime.datetime.utcnow()
                ),
                Notification(
                    title="Field Inspection Task Assigned",
                    message="Lead Risk Analyst assigned to conduct on-site audit for Valu Consumer Finance.",
                    type="warning",
                    is_read=False,
                    created_at=datetime.datetime.utcnow()
                )
            ]
            db.add_all(notifs)
            db.commit()
            print("  -> Seeded initial system notifications.")

        print("=" * 60)
        print("[SUCCESS] DATABASE INITIALIZATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error during database seeding: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    setup_database()
