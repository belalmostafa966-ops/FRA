import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="Executive")  # Admin, Risk Analyst, Executive
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    inspection_tasks = relationship("InspectionTask", back_populates="assigned_user", foreign_keys="InspectionTask.assigned_to_user_id")
    notifications = relationship("Notification", back_populates="user")

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    tax_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    sector = Column(String(80), nullable=False)  # e.g., Insurance, Microfinance, Consumer Finance, Leasing, Capital Markets
    risk_level = Column(String(20), default="Low")  # Low, Medium, High, Critical
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    complaints = relationship("Complaint", back_populates="company", cascade="all, delete-orphan")
    financial_records = relationship("FinancialRecord", back_populates="company", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScoreHistory", back_populates="company", cascade="all, delete-orphan")
    inspection_tasks = relationship("InspectionTask", back_populates="company", cascade="all, delete-orphan")
    reports = relationship("CompanyReport", back_populates="company", cascade="all, delete-orphan")
    history_logs = relationship("CompanyHistory", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company {self.name} ({self.sector})>"

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    quarter = Column(String(10), nullable=False)  # Q1, Q2, Q3, Q4
    year = Column(Integer, nullable=False)
    total_complaints = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    high_severity_count = Column(Integer, default=0)
    open_count = Column(Integer, default=0)
    fraud_allegation_count = Column(Integer, default=0)
    growth_rate = Column(Float, default=0.0)  # Complaint growth rate vs previous quarter
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="complaints")

    def __repr__(self):
        return f"<Complaint Company={self.company_id} {self.quarter} {self.year}>"

class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    quarter = Column(String(10), nullable=False)  # Q1, Q2, Q3, Q4
    year = Column(Integer, nullable=False)
    revenue = Column(Float, default=0.0)
    net_income = Column(Float, default=0.0)
    total_assets = Column(Float, default=0.0)
    total_liabilities = Column(Float, default=0.0)
    current_assets = Column(Float, default=0.0)
    current_liabilities = Column(Float, default=0.0)
    total_equity = Column(Float, default=0.0)
    cash_and_equivalents = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="financial_records")

    def __repr__(self):
        return f"<FinancialRecord Company={self.company_id} {self.quarter} {self.year}>"

class RiskScoreHistory(Base):
    __tablename__ = "risk_scores_history"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    evaluation_date = Column(DateTime, default=datetime.datetime.utcnow)
    complaint_score = Column(Float, default=0.0)
    financial_score = Column(Float, default=0.0)
    composite_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="Low")  # Low, Medium, High, Critical
    ews_alert_flag = Column(Boolean, default=False)
    ews_reasons = Column(Text, nullable=True)  # JSON or comma separated alert reasons
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="risk_scores")

    def __repr__(self):
        return f"<RiskScoreHistory Company={self.company_id} Composite={self.composite_score:.1f}>"

class ScoringWeight(Base):
    __tablename__ = "scoring_weights"

    id = Column(Integer, primary_key=True, index=True)
    vol_w = Column(Float, default=0.20)
    neg_w = Column(Float, default=0.20)
    sev_w = Column(Float, default=0.20)
    open_w = Column(Float, default=0.15)
    fraud_w = Column(Float, default=0.10)
    growth_w = Column(Float, default=0.15)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<ScoringWeight vol={self.vol_w} neg={self.neg_w} sev={self.sev_w}>"

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True)
    action = Column(String(150), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<ActivityLog {self.username}: {self.action}>"

class InspectionTask(Base):
    __tablename__ = "inspection_tasks"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    inspector_username = Column(String(50), nullable=True)
    title = Column(String(200), nullable=False)
    urgency = Column(String(20), default="Medium")  # Critical, High, Medium, Routine
    scheduled_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(20), default="Scheduled")  # Scheduled, In Progress, Completed, Cancelled
    findings_notes = Column(Text, nullable=True)
    inspector_notes = Column(Text, nullable=True)
    manager_comments = Column(Text, nullable=True)
    evidence_filename = Column(String(255), nullable=True)
    approval_status = Column(String(30), default="Pending Review")  # Pending Review, Approved, Requires Action, Escalated
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="inspection_tasks")
    assigned_user = relationship("User", back_populates="inspection_tasks", foreign_keys=[assigned_to_user_id])

    def __repr__(self):
        return f"<InspectionTask {self.title} Status={self.status}>"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for broadcast notifications
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(30), default="SYSTEM")  # EWS_ALERT, INSPECTION_ASSIGNED, WEIGHTS_UPDATED, SYSTEM
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.title} Type={self.type} Read={self.is_read}>"

class SMTPSetting(Base):
    __tablename__ = "smtp_settings"

    id = Column(Integer, primary_key=True, index=True)
    host = Column(String(150), default="smtp.gmail.com")
    port = Column(Integer, default=587)
    username = Column(String(150), nullable=True)
    password = Column(String(150), nullable=True)
    sender_email = Column(String(150), default="notifications@fra.gov.eg")
    use_tls = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<SMTPSetting {self.host}:{self.port}>"

class CompanyReport(Base):
    __tablename__ = "company_reports"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String(200), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), default="PDF")
    file_size_kb = Column(Float, default=0.0)
    uploaded_by = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="reports")

    def __repr__(self):
        return f"<CompanyReport {self.title} Company={self.company_id}>"

class CompanyHistory(Base):
    __tablename__ = "company_histories"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    modified_by = Column(String(100), nullable=False)
    modified_role = Column(String(50), default="Staff")
    field_name = Column(String(100), nullable=False)  # e.g., Net Income, Complaints, Risk Level
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    audit_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="history_logs")

    def __repr__(self):
        return f"<CompanyHistory Company={self.company_id} Field={self.field_name}>"

