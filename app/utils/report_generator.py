import io
import datetime
import pandas as pd
from sqlalchemy.orm import Session
from models import Company, RiskScoreHistory, Complaint, FinancialRecord

def generate_risk_summary_csv(db: Session) -> str:
    """
    Generates a CSV string containing all company risk profiles and scores.
    """
    companies = db.query(Company).all()
    rows = []
    
    for c in companies:
        latest_risk = (
            db.query(RiskScoreHistory)
            .filter(RiskScoreHistory.company_id == c.id)
            .order_by(RiskScoreHistory.evaluation_date.desc())
            .first()
        )
        
        latest_complaint = (
            db.query(Complaint)
            .filter(Complaint.company_id == c.id)
            .order_by(Complaint.year.desc(), Complaint.quarter.desc())
            .first()
        )

        rows.append({
            "Company ID": c.id,
            "Tax ID": c.tax_id,
            "Company Name": c.name,
            "Sector": c.sector,
            "Risk Level": c.risk_level,
            "Composite Risk Score": latest_risk.composite_score if latest_risk else 0.0,
            "Complaints Risk Score": latest_risk.complaint_score if latest_risk else 0.0,
            "Financial Risk Score": latest_risk.financial_score if latest_risk else 0.0,
            "EWS Alert Active": "YES" if (latest_risk and latest_risk.ews_alert_flag) else "NO",
            "EWS Trigger Reasons": latest_risk.ews_reasons if latest_risk else "",
            "Total Complaints": latest_complaint.total_complaints if latest_complaint else 0,
            "Negative Complaints": latest_complaint.negative_count if latest_complaint else 0,
            "High Severity Complaints": latest_complaint.high_severity_count if latest_complaint else 0,
            "Fraud Allegations": latest_complaint.fraud_allegation_count if latest_complaint else 0,
            "Last Evaluation Date": latest_risk.evaluation_date.strftime("%Y-%m-%d %H:%M") if latest_risk else "N/A"
        })

    df = pd.DataFrame(rows)
    return df.to_csv(index=False)

def generate_company_compliance_report(db: Session, company_id: int) -> str:
    """
    Generates a formatted markdown text report for a specific company.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return "Company Not Found"

    risk_history = (
        db.query(RiskScoreHistory)
        .filter(RiskScoreHistory.company_id == company.id)
        .order_by(RiskScoreHistory.evaluation_date.desc())
        .all()
    )

    latest_risk = risk_history[0] if risk_history else None

    report = []
    report.append("================================================================================")
    report.append("          FINANCIAL REGULATORY AUTHORITY (FRA) - COMPLIANCE & RISK REPORT       ")
    report.append("================================================================================")
    report.append(f"Entity Name     : {company.name}")
    report.append(f"Tax Identifier  : {company.tax_id}")
    report.append(f"Regulated Sector: {company.sector}")
    report.append(f"Current Status  : RISK LEVEL [{company.risk_level.upper()}]")
    report.append(f"Report Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report.append("--------------------------------------------------------------------------------\n")

    if latest_risk:
        report.append("--- EXECUTIVE RISK SUMMARY ---")
        report.append(f"Composite Risk Score (0-100) : {latest_risk.composite_score:.1f}")
        report.append(f"Complaints Risk Score (0-100): {latest_risk.complaint_score:.1f}")
        report.append(f"Financial Risk Score (0-100) : {latest_risk.financial_score:.1f}")
        report.append(f"Early Warning System Trigger : {'[ACTIVE ALERT]' if latest_risk.ews_alert_flag else '[NORMAL]'}")
        if latest_risk.ews_reasons:
            report.append(f"EWS Trigger Details          : {latest_risk.ews_reasons}")
        report.append("\n")

    report.append("--- HISTORICAL EVALUATION LOGS ---")
    report.append(f"{'Date':<20} | {'Composite':<10} | {'Complaints':<10} | {'Financial':<10} | {'Risk Level':<10} | {'EWS Alert':<10}")
    report.append("-" * 80)
    for rh in risk_history[:10]:
        dt_str = rh.evaluation_date.strftime("%Y-%m-%d %H:%M")
        report.append(f"{dt_str:<20} | {rh.composite_score:<10.1f} | {rh.complaint_score:<10.1f} | {rh.financial_score:<10.1f} | {rh.risk_level:<10} | {'YES' if rh.ews_alert_flag else 'NO':<10}")

    report.append("\n================================================================================")
    report.append(" END OF OFFICIAL FRA RISK INTELLIGENCE REPORT - CONFIDENTIAL & PROPRIETARY     ")
    report.append("================================================================================")

    return "\n".join(report)
