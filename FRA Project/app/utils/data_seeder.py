import datetime
import random
from sqlalchemy.orm import Session
from models import Company, Complaint, FinancialRecord, RiskScoreHistory, ScoringWeight
from risk_engine.complaints import calculate_complaints_metrics, calculate_complaints_risk_score, evaluate_complaint_ews_alerts
from risk_engine.financial import calculate_financial_ratios, calculate_financial_risk_score, calculate_composite_risk, evaluate_financial_ews_alerts

SAMPLE_COMPANIES = [
    {
        "tax_id": "TAX-EG-102938",
        "name": "EFG Hermes Holding",
        "sector": "Capital Markets",
        "financial_base": {"revenue": 450000000, "net_income": 85000000, "assets": 1200000000, "liabilities": 400000000, "curr_assets": 500000000, "curr_liab": 250000000, "equity": 800000000, "cash": 220000000},
        "complaint_base": {"total": 45, "neg": 8, "sev": 2, "open": 3, "fraud": 0, "growth": 0.05}
    },
    {
        "tax_id": "TAX-EG-204857",
        "name": "Valu Consumer Finance",
        "sector": "Consumer Finance",
        "financial_base": {"revenue": 320000000, "net_income": 42000000, "assets": 850000000, "liabilities": 520000000, "curr_assets": 350000000, "curr_liab": 280000000, "equity": 330000000, "cash": 95000000},
        "complaint_base": {"total": 310, "neg": 140, "sev": 45, "open": 50, "fraud": 12, "growth": 0.28}
    },
    {
        "tax_id": "TAX-EG-309182",
        "name": "Contact Financial Holding",
        "sector": "Leasing & Factoring",
        "financial_base": {"revenue": 280000000, "net_income": 39000000, "assets": 700000000, "liabilities": 310000000, "curr_assets": 290000000, "curr_liab": 140000000, "equity": 390000000, "cash": 110000000},
        "complaint_base": {"total": 85, "neg": 18, "sev": 5, "open": 8, "fraud": 1, "growth": -0.04}
    },
    {
        "tax_id": "TAX-EG-401928",
        "name": "Al Ahly Pharos Microfinance",
        "sector": "Microfinance",
        "financial_base": {"revenue": 140000000, "net_income": -18000000, "assets": 260000000, "liabilities": 210000000, "curr_assets": 85000000, "curr_liab": 120000000, "equity": 50000000, "cash": 15000000},
        "complaint_base": {"total": 420, "neg": 260, "sev": 110, "open": 180, "fraud": 48, "growth": 0.42}
    },
    {
        "tax_id": "TAX-EG-508273",
        "name": "Delta Insurance & Risk Services",
        "sector": "Insurance",
        "financial_base": {"revenue": 190000000, "net_income": -35000000, "assets": 310000000, "liabilities": 285000000, "curr_assets": 70000000, "curr_liab": 160000000, "equity": 25000000, "cash": 8000000},
        "complaint_base": {"total": 580, "neg": 390, "sev": 195, "open": 270, "fraud": 92, "growth": 0.65}
    },
    {
        "tax_id": "TAX-EG-603918",
        "name": "Tamweel Mortgage & Factoring",
        "sector": "Mortgage & Leasing",
        "financial_base": {"revenue": 110000000, "net_income": 5000000, "assets": 410000000, "liabilities": 320000000, "curr_assets": 120000000, "curr_liab": 110000000, "equity": 90000000, "cash": 24000000},
        "complaint_base": {"total": 210, "neg": 88, "sev": 28, "open": 42, "fraud": 8, "growth": 0.18}
    },
    {
        "tax_id": "TAX-EG-701923",
        "name": "Nile Capital Investments",
        "sector": "Capital Markets",
        "financial_base": {"revenue": 95000000, "net_income": 12000000, "assets": 340000000, "liabilities": 140000000, "curr_assets": 150000000, "curr_liab": 65000000, "equity": 200000000, "cash": 45000000},
        "complaint_base": {"total": 60, "neg": 14, "sev": 3, "open": 6, "fraud": 1, "growth": 0.02}
    },
    {
        "tax_id": "TAX-EG-802934",
        "name": "Aman Financial Services",
        "sector": "Consumer Finance",
        "financial_base": {"revenue": 260000000, "net_income": 31000000, "assets": 620000000, "liabilities": 380000000, "curr_assets": 280000000, "curr_liab": 170000000, "equity": 240000000, "cash": 80000000},
        "complaint_base": {"total": 140, "neg": 32, "sev": 9, "open": 14, "fraud": 2, "growth": 0.08}
    }
]

def seed_sample_data(db: Session, force: bool = False):
    """
    Seeds sample companies, quarterly financial data, complaints, and risk scores.
    """
    if not force and db.query(Company).count() > 0:
        return

    # Seed Default Scoring Weights if empty
    if db.query(ScoringWeight).count() == 0:
        weight_record = ScoringWeight(
            vol_w=0.20, neg_w=0.20, sev_w=0.20, open_w=0.15, fraud_w=0.10, growth_w=0.15
        )
        db.add(weight_record)
        db.commit()

    quarters = [
        ("Q1", 2025), ("Q2", 2025), ("Q3", 2025), ("Q4", 2025),
        ("Q1", 2026), ("Q2", 2026)
    ]

    for comp_info in SAMPLE_COMPANIES:
        company = db.query(Company).filter(Company.tax_id == comp_info["tax_id"]).first()
        if not company:
            company = Company(
                tax_id=comp_info["tax_id"],
                name=comp_info["name"],
                sector=comp_info["sector"],
                risk_level="Low"
            )
            db.add(company)
            db.flush()

        fb = comp_info["financial_base"]
        cb = comp_info["complaint_base"]

        last_composite = 0.0
        last_risk_level = "Low"

        # Generate multi-quarter trend
        for idx, (q, yr) in enumerate(quarters):
            trend_mult = 1.0 + (idx - 3) * 0.04
            if comp_info["name"] in ["Delta Insurance & Risk Services", "Al Ahly Pharos Microfinance"]:
                # Worsening trend for high risk entities
                trend_mult = 1.0 + (idx) * 0.12

            # Financial Record
            rev = round(fb["revenue"] * trend_mult, 2)
            net_inc = round(fb["net_income"] * (trend_mult if fb["net_income"] > 0 else 1.0 + idx * 0.15), 2)
            tot_ast = round(fb["assets"] * trend_mult, 2)
            tot_liab = round(fb["liabilities"] * trend_mult, 2)
            curr_ast = round(fb["curr_assets"] * trend_mult, 2)
            curr_liab = round(fb["curr_liab"] * trend_mult, 2)
            equity = round(fb["equity"] * (1.0 - idx * 0.03 if net_inc < 0 else 1.0 + idx * 0.02), 2)
            cash = round(fb["cash"] * max(0.2, (1.0 - idx * 0.08 if net_inc < 0 else 1.0 + idx * 0.01)), 2)

            fin_rec = FinancialRecord(
                company_id=company.id,
                quarter=q,
                year=yr,
                revenue=rev,
                net_income=net_inc,
                total_assets=tot_ast,
                total_liabilities=tot_liab,
                current_assets=curr_ast,
                current_liabilities=curr_liab,
                total_equity=equity,
                cash_and_equivalents=cash
            )
            db.add(fin_rec)

            # Complaint Record
            c_tot = int(cb["total"] * trend_mult)
            c_neg = int(cb["neg"] * trend_mult)
            c_sev = int(cb["sev"] * trend_mult)
            c_open = int(cb["open"] * trend_mult)
            c_fraud = int(cb["fraud"] * trend_mult)
            c_growth = round(cb["growth"] + (idx - 3) * 0.03, 3)

            comp_rec = Complaint(
                company_id=company.id,
                quarter=q,
                year=yr,
                total_complaints=c_tot,
                negative_count=c_neg,
                high_severity_count=c_sev,
                open_count=c_open,
                fraud_allegation_count=c_fraud,
                growth_rate=c_growth
            )
            db.add(comp_rec)

            # Risk Calculations for current quarter
            comp_metrics = calculate_complaints_metrics(
                total_complaints=c_tot,
                negative_count=c_neg,
                high_severity_count=c_sev,
                open_count=c_open,
                fraud_allegation_count=c_fraud,
                growth_rate=c_growth
            )
            comp_score = calculate_complaints_risk_score(comp_metrics)
            
            fin_ratios = calculate_financial_ratios(
                revenue=rev, net_income=net_inc, total_assets=tot_ast,
                total_liabilities=tot_liab, current_assets=curr_ast,
                current_liabilities=curr_liab, total_equity=equity,
                cash_and_equivalents=cash
            )
            fin_score = calculate_financial_risk_score(fin_ratios)

            composite, risk_lvl = calculate_composite_risk(comp_score, fin_score)

            c_alert, c_reasons = evaluate_complaint_ews_alerts(comp_metrics, comp_score)
            f_alert, f_reasons = evaluate_financial_ews_alerts(fin_ratios, fin_score)
            ews_flag = c_alert or f_alert
            all_reasons = c_reasons + f_reasons

            eval_date = datetime.datetime.utcnow() - datetime.timedelta(days=(len(quarters) - idx) * 90)

            risk_hist = RiskScoreHistory(
                company_id=company.id,
                evaluation_date=eval_date,
                complaint_score=comp_score,
                financial_score=fin_score,
                composite_score=composite,
                risk_level=risk_lvl,
                ews_alert_flag=ews_flag,
                ews_reasons=" | ".join(all_reasons) if all_reasons else None
            )
            db.add(risk_hist)

            last_composite = composite
            last_risk_level = risk_lvl

        # Update latest company risk level
        company.risk_level = last_risk_level

        # Seed initial history log
        db.add(CompanyHistory(
            company_id=company.id,
            modified_by="system",
            modified_role="System Admin",
            field_name="Initial Registration",
            old_value=None,
            new_value="Entity Onboarded to FRA System",
            audit_note="Automated baseline setup during database initialization",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=180)
        ))

        # Seed initial audit report
        db.add(CompanyReport(
            company_id=company.id,
            title=f"Q2 2026 Statutory Compliance & Financial Audit ({company.name})",
            filename=f"{company.tax_id}_Q2_2026_Audit_Report.pdf",
            file_type="PDF",
            file_size_kb=1420.5,
            uploaded_by="analyst@fra.gov.eg",
            notes="Comprehensive Q2 statutory compliance review and risk assessment summary.",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=15)
        ))

    db.commit()
