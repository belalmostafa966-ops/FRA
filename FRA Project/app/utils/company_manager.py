import os
import datetime
import json
from sqlalchemy.orm import Session
from models import Company, Complaint, FinancialRecord, RiskScoreHistory, ScoringWeight, CompanyHistory, CompanyReport, ActivityLog
from risk_engine.financial import calculate_financial_ratios, calculate_financial_risk_score, calculate_composite_risk, evaluate_financial_ews_alerts
from risk_engine.complaints import calculate_complaints_metrics, calculate_complaints_risk_score, evaluate_complaint_ews_alerts
from config import DEFAULT_COMPLAINT_WEIGHTS

REPORTS_DIR = os.path.join("uploads", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def update_company_data(
    db: Session,
    company_id: int,
    user_dict: dict,
    comp_updates: dict,
    complaint_updates: dict,
    financial_updates: dict,
    audit_note: str = ""
) -> tuple:
    """
    Updates company, complaint, and financial records inline.
    Calculates new composite risk scores, logs all field changes in CompanyHistory,
    and returns (success, company, changes_made, new_score).
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return False, None, [], 0.0

    username = user_dict.get("username", "Staff")
    role = user_dict.get("role", "Staff")
    changes_made = []

    # 1. Update Company Basic Info
    for field, new_val in comp_updates.items():
        if hasattr(company, field):
            old_val = getattr(company, field)
            if str(old_val) != str(new_val):
                setattr(company, field, new_val)
                changes_made.append((field, str(old_val), str(new_val)))
                history_rec = CompanyHistory(
                    company_id=company.id,
                    modified_by=username,
                    modified_role=role,
                    field_name=f"Company {field.replace('_', ' ').title()}",
                    old_value=str(old_val),
                    new_value=str(new_val),
                    audit_note=audit_note,
                    created_at=datetime.datetime.utcnow()
                )
                db.add(history_rec)

    # 2. Update Complaint Record
    comp_rec = db.query(Complaint).filter(Complaint.company_id == company_id).order_by(Complaint.year.desc(), Complaint.quarter.desc()).first()
    if comp_rec:
        for field, new_val in complaint_updates.items():
            if hasattr(comp_rec, field):
                old_val = getattr(comp_rec, field)
                if str(old_val) != str(new_val):
                    setattr(comp_rec, field, new_val)
                    changes_made.append((f"Complaint.{field}", str(old_val), str(new_val)))
                    history_rec = CompanyHistory(
                        company_id=company.id,
                        modified_by=username,
                        modified_role=role,
                        field_name=f"Complaint {field.replace('_', ' ').title()}",
                        old_value=str(old_val),
                        new_value=str(new_val),
                        audit_note=audit_note,
                        created_at=datetime.datetime.utcnow()
                    )
                    db.add(history_rec)

    # 3. Update Financial Record
    fin_rec = db.query(FinancialRecord).filter(FinancialRecord.company_id == company_id).order_by(FinancialRecord.year.desc(), FinancialRecord.quarter.desc()).first()
    if fin_rec:
        for field, new_val in financial_updates.items():
            if hasattr(fin_rec, field):
                old_val = getattr(fin_rec, field)
                if str(old_val) != str(new_val):
                    setattr(fin_rec, field, new_val)
                    changes_made.append((f"Financial.{field}", str(old_val), str(new_val)))
                    history_rec = CompanyHistory(
                        company_id=company.id,
                        modified_by=username,
                        modified_role=role,
                        field_name=f"Financial {field.replace('_', ' ').title()}",
                        old_value=str(old_val),
                        new_value=str(new_val),
                        audit_note=audit_note,
                        created_at=datetime.datetime.utcnow()
                    )
                    db.add(history_rec)

    db.commit()
    db.refresh(company)

    # 4. Re-evaluate Risk Engine
    weights_rec = db.query(ScoringWeight).order_by(ScoringWeight.updated_at.desc()).first()
    if weights_rec:
        weights = {
            "vol_w": weights_rec.vol_w, "neg_w": weights_rec.neg_w, "sev_w": weights_rec.sev_w,
            "open_w": weights_rec.open_w, "fraud_w": weights_rec.fraud_w, "growth_w": weights_rec.growth_w
        }
    else:
        weights = DEFAULT_COMPLAINT_WEIGHTS

    # Calculate Complaint Score
    comp_metrics = calculate_complaints_metrics(
        total_complaints=comp_rec.total_complaints if comp_rec else 0,
        negative_count=comp_rec.negative_count if comp_rec else 0,
        high_severity_count=comp_rec.high_severity_count if comp_rec else 0,
        open_count=comp_rec.open_count if comp_rec else 0,
        fraud_allegation_count=comp_rec.fraud_allegation_count if comp_rec else 0,
        growth_rate=comp_rec.growth_rate if comp_rec else 0.0,
        benchmark_max_volume=50
    )
    complaint_score = calculate_complaints_risk_score(comp_metrics, weights)

    # Calculate Financial Score
    ratios = calculate_financial_ratios(
        revenue=fin_rec.revenue if fin_rec else 0.0,
        net_income=fin_rec.net_income if fin_rec else 0.0,
        total_assets=fin_rec.total_assets if fin_rec else 0.0,
        total_liabilities=fin_rec.total_liabilities if fin_rec else 0.0,
        current_assets=fin_rec.current_assets if fin_rec else 0.0,
        current_liabilities=fin_rec.current_liabilities if fin_rec else 0.0,
        total_equity=fin_rec.total_equity if fin_rec else 0.0,
        cash_and_equivalents=fin_rec.cash_and_equivalents if fin_rec else 0.0
    )
    financial_score = calculate_financial_risk_score(ratios)

    # Calculate Composite Score
    composite_score, risk_level = calculate_composite_risk(complaint_score, financial_score)

    # EWS Triggers
    c_ews, c_reasons = evaluate_complaint_ews_alerts(comp_metrics, complaint_score)
    f_ews, f_reasons = evaluate_financial_ews_alerts(ratios, financial_score)

    has_ews = c_ews or f_ews
    all_reasons = c_reasons + f_reasons

    # Log Risk Score History
    new_risk_rec = RiskScoreHistory(
        company_id=company.id,
        evaluation_date=datetime.datetime.utcnow(),
        complaint_score=complaint_score,
        financial_score=financial_score,
        composite_score=composite_score,
        risk_level=risk_level,
        ews_alert_flag=has_ews,
        ews_reasons="; ".join(all_reasons) if all_reasons else None
    )
    db.add(new_risk_rec)

    old_risk_level = company.risk_level
    company.risk_level = risk_level

    if old_risk_level != risk_level:
        history_rec = CompanyHistory(
            company_id=company.id,
            modified_by=username,
            modified_role=role,
            field_name="Risk Level Classification",
            old_value=old_risk_level,
            new_value=risk_level,
            audit_note="Auto Risk Engine Recalculation",
            created_at=datetime.datetime.utcnow()
        )
        db.add(history_rec)

    db.add(ActivityLog(
        username=username,
        action=f"Edited Company Statistics for '{company.name}'",
        details=f"Updated {len(changes_made)} fields. New composite risk score: {composite_score:.1f} ({risk_level}). Note: {audit_note}"
    ))

    db.commit()
    return True, company, changes_made, composite_score

def create_company_manual(
    db: Session,
    user_dict: dict,
    tax_id: str,
    name: str,
    sector: str,
    complaint_data: dict,
    financial_data: dict
) -> tuple:
    """Creates a new monitored company record manually."""
    existing = db.query(Company).filter(Company.tax_id == tax_id.strip()).first()
    if existing:
        return False, None, f"Company with Tax ID '{tax_id}' already exists."

    username = user_dict.get("username", "Staff")
    role = user_dict.get("role", "Staff")

    # 1. Create Company
    new_company = Company(
        tax_id=tax_id.strip(),
        name=name.strip(),
        sector=sector,
        risk_level="Low"
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    # 2. Add Complaint Record
    new_comp = Complaint(
        company_id=new_company.id,
        quarter="Q3",
        year=2026,
        total_complaints=complaint_data.get("total_complaints", 0),
        negative_count=complaint_data.get("negative_count", 0),
        high_severity_count=complaint_data.get("high_severity_count", 0),
        open_count=complaint_data.get("open_count", 0),
        fraud_allegation_count=complaint_data.get("fraud_allegation_count", 0),
        growth_rate=complaint_data.get("growth_rate", 0.0)
    )
    db.add(new_comp)

    # 3. Add Financial Record
    new_fin = FinancialRecord(
        company_id=new_company.id,
        quarter="Q3",
        year=2026,
        revenue=financial_data.get("revenue", 0.0),
        net_income=financial_data.get("net_income", 0.0),
        total_assets=financial_data.get("total_assets", 0.0),
        total_liabilities=financial_data.get("total_liabilities", 0.0),
        current_assets=financial_data.get("current_assets", 0.0),
        current_liabilities=financial_data.get("current_liabilities", 0.0),
        total_equity=financial_data.get("total_equity", 0.0),
        cash_and_equivalents=financial_data.get("cash_and_equivalents", 0.0)
    )
    db.add(new_fin)

    # 4. History Log
    history_rec = CompanyHistory(
        company_id=new_company.id,
        modified_by=username,
        modified_role=role,
        field_name="Entity Creation",
        old_value=None,
        new_value="Registered in FRA System",
        audit_note="Manual Entity Registration",
        created_at=datetime.datetime.utcnow()
    )
    db.add(history_rec)

    db.add(ActivityLog(
        username=username,
        action=f"Manually Created Monitored Entity '{name}'",
        details=f"Tax ID: {tax_id}, Sector: {sector}"
    ))

    db.commit()

    # Re-evaluate Risk
    update_company_data(db, new_company.id, user_dict, {}, {}, {}, "Initial Risk Evaluation")

    return True, new_company, "Entity created successfully."

def upload_company_report(
    db: Session,
    company_id: int,
    uploaded_file,
    title: str,
    user_dict: dict,
    notes: str = ""
) -> tuple:
    """Saves uploaded report file and registers record in CompanyReport table."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return False, "Company not found."

    username = user_dict.get("username", "Staff")

    filename = f"{company.tax_id}_{int(datetime.datetime.utcnow().timestamp())}_{uploaded_file.name}"
    file_path = os.path.join(REPORTS_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    size_kb = round(len(uploaded_file.getbuffer()) / 1024.0, 2)
    ext = uploaded_file.name.split(".")[-1].upper() if "." in uploaded_file.name else "FILE"

    report_rec = CompanyReport(
        company_id=company.id,
        title=title.strip() if title else uploaded_file.name,
        filename=filename,
        file_type=ext,
        file_size_kb=size_kb,
        uploaded_by=username,
        notes=notes,
        created_at=datetime.datetime.utcnow()
    )
    db.add(report_rec)

    # History entry
    history_rec = CompanyHistory(
        company_id=company.id,
        modified_by=username,
        modified_role=user_dict.get("role", "Staff"),
        field_name="Audit Report Attachment",
        old_value=None,
        new_value=title.strip() if title else uploaded_file.name,
        audit_note=f"Uploaded report file ({size_kb} KB)",
        created_at=datetime.datetime.utcnow()
    )
    db.add(history_rec)

    db.add(ActivityLog(
        username=username,
        action=f"Uploaded Report '{title}' for Company '{company.name}'",
        details=f"File: {filename}, Size: {size_kb} KB"
    ))

    db.commit()
    return True, "Report uploaded and attached successfully."

def delete_company_entity(db: Session, company_id: int, user_dict: dict) -> tuple:
    """
    Deletes a company entity and all associated records from the database.
    Logs deletion activity in ActivityLog.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return False, "Company entity not found."

    comp_name = company.name
    tax_id = company.tax_id
    username = user_dict.get("username", "Admin")

    # Cascade delete is configured in models.py, but explicit cleanup ensures database consistency
    db.query(Complaint).filter(Complaint.company_id == company_id).delete()
    db.query(FinancialRecord).filter(FinancialRecord.company_id == company_id).delete()
    db.query(RiskScoreHistory).filter(RiskScoreHistory.company_id == company_id).delete()
    db.query(CompanyReport).filter(CompanyReport.company_id == company_id).delete()
    db.query(CompanyHistory).filter(CompanyHistory.company_id == company_id).delete()
    
    db.delete(company)
    
    db.add(ActivityLog(
        username=username,
        action=f"Deleted Monitored Entity '{comp_name}'",
        details=f"Tax ID: {tax_id}"
    ))
    db.commit()
    return True, f"Monitored Entity '{comp_name}' (Tax ID: {tax_id}) has been permanently deleted from the system."
