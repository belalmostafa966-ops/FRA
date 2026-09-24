import os
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from models import Company, Complaint, FinancialRecord, RiskScoreHistory, CompanyReport, CompanyHistory
from utils.company_manager import REPORTS_DIR

import os
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from models import Company, Complaint, FinancialRecord, RiskScoreHistory, CompanyReport, CompanyHistory
from utils.company_manager import REPORTS_DIR

@st.dialog("Comprehensive Entity Supervisory Profile", width="large")
def render_company_details_dialog(db: Session, company_id: int):
    """
    Renders a comprehensive popup modal displaying full company metrics,
    risk calculations, complaints statistics, financial balance sheet,
    attached reports, and historical staff modification audit trail.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        st.error("Target company profile was not found in database.")
        return

    # Fetch latest records
    latest_risk = db.query(RiskScoreHistory).filter(
        RiskScoreHistory.company_id == company.id
    ).order_by(RiskScoreHistory.created_at.desc()).first()

    latest_comp = db.query(Complaint).filter(
        Complaint.company_id == company.id
    ).order_by(Complaint.year.desc(), Complaint.quarter.desc()).first()

    latest_fin = db.query(FinancialRecord).filter(
        FinancialRecord.company_id == company.id
    ).order_by(FinancialRecord.year.desc(), FinancialRecord.quarter.desc()).first()

    reports = db.query(CompanyReport).filter(
        CompanyReport.company_id == company.id
    ).order_by(CompanyReport.created_at.desc()).all()

    history_logs = db.query(CompanyHistory).filter(
        CompanyHistory.company_id == company.id
    ).order_by(CompanyHistory.created_at.desc()).all()

    # Header section
    badge_bg = (
        "#991B1B" if company.risk_level == "Critical"
        else "#D97706" if company.risk_level == "High"
        else "#F59E0B" if company.risk_level == "Medium"
        else "#10B981"
    )

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0F172A, #1E3A8A); color: white; padding: 1.25rem 1.5rem; border-radius: 12px; border: 1px solid #D97706; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <h2 style="margin: 0; color: #FFFFFF; font-size: 1.4rem; font-weight: 800;">{company.name}</h2>
                <div style="margin-top: 0.3rem; color: #CBD5E1; font-size: 0.9rem;">
                    Tax Identification ID: <b style="color: #F8FAFC;">{company.tax_id}</b> | Sector: <b style="color: #D97706;">{company.sector}</b>
                </div>
            </div>
            <div>
                <span style="background: {badge_bg}; color: white; padding: 0.45rem 1.1rem; border-radius: 20px; font-weight: 800; font-size: 0.9rem; letter-spacing: 0.03em;">
                    Risk Rating: {company.risk_level}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_risk, tab_comp, tab_fin, tab_rep, tab_hist = st.tabs([
        "Supervisory Risk Assessment",
        "Complaints & Anomalies",
        "Financial Balance Sheet",
        "Attached Audit Reports",
        "Staff Audit History Log"
    ])

    with tab_risk:
        st.markdown("#### System Composite Risk Score Breakdown")
        r1, r2, r3 = st.columns(3)
        r1.metric("Composite Risk Index", f"{latest_risk.composite_score:.1f} / 100" if latest_risk else "N/A")
        r2.metric("Complaints Risk Subscore", f"{latest_risk.complaint_score:.1f}" if latest_risk else "N/A")
        r3.metric("Financial Risk Subscore", f"{latest_risk.financial_score:.1f}" if latest_risk else "N/A")

        st.markdown("---")
        if latest_risk and latest_risk.ews_alert_flag:
            st.error(f"Early Warning Triggered: {latest_risk.ews_reasons or 'Anomaly detected in complaints or financial indicators'}")
        else:
            st.success("No active Early Warning triggers detected for this entity.")

    with tab_comp:
        st.markdown("#### Quarterly Complaints & Statutory Violations Statistics")
        if latest_comp:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Filed Complaints", latest_comp.total_complaints)
            c2.metric("Negative Resolution Count", latest_comp.negative_count)
            c3.metric("High Severity Violations", latest_comp.high_severity_count)

            st.markdown("<br>", unsafe_allow_html=True)
            c4, c5, c6 = st.columns(3)
            c4.metric("Unresolved Open Cases", latest_comp.open_count)
            c5.metric("Fraud & Corruption Allegations", latest_comp.fraud_allegation_count)
            c6.metric("Complaints QoQ Growth Rate", f"{latest_comp.growth_rate * 100:.1f}%")
        else:
            st.info("No complaint records logged for this entity.")

    with tab_fin:
        st.markdown("#### Financial Indicators & Capital Metrics")
        if latest_fin:
            f1, f2, f3 = st.columns(3)
            f1.metric("Quarterly Revenue", f"${latest_fin.revenue:,.2f}")
            f2.metric("Net Profit / Income", f"${latest_fin.net_income:,.2f}")
            f3.metric("Total Equity", f"${latest_fin.total_equity:,.2f}")

            st.markdown("<br>", unsafe_allow_html=True)
            f4, f5, f6 = st.columns(3)
            f4.metric("Total Assets", f"${latest_fin.total_assets:,.2f}")
            f5.metric("Total Liabilities", f"${latest_fin.total_liabilities:,.2f}")
            f6.metric("Cash & Cash Equivalents", f"${latest_fin.cash_and_equivalents:,.2f}")
        else:
            st.info("No financial balance sheet records logged for this entity.")

    with tab_rep:
        st.markdown("#### Statutory Audit & Regulatory Reports")
        if reports:
            for rep in reports:
                file_path = os.path.join(REPORTS_DIR, rep.filename)
                with st.container():
                    r_col1, r_col2 = st.columns([70, 30])
                    with r_col1:
                        st.markdown(f"**{rep.title}**<br><span style='color: #64748B; font-size: 0.82rem;'>File: {rep.filename} | Size: {rep.file_size_kb} KB | By: {rep.uploaded_by} | Date: {rep.created_at.strftime('%Y-%m-%d %H:%M')}</span>", unsafe_allow_html=True)
                        if rep.notes:
                            st.caption(f"Notes: {rep.notes}")
                    with r_col2:
                        if os.path.exists(file_path):
                            with open(file_path, "rb") as f:
                                file_bytes = f.read()
                            st.download_button(
                                label=f"Download ({rep.file_type})",
                                data=file_bytes,
                                file_name=rep.filename,
                                mime="application/octet-stream",
                                key=f"dl_modal_rep_{rep.id}",
                                use_container_width=True
                            )
                        else:
                            st.caption("File not found on disk")
                    st.markdown("<hr style='margin: 0.4rem 0; border: 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
        else:
            st.info("No audit reports attached to this entity.")

    with tab_hist:
        st.markdown("#### Staff Audit & Entity Data Modification Log")
        if history_logs:
            hist_list = []
            for h in history_logs:
                hist_list.append({
                    "Timestamp": h.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "Modified By Staff": f"{h.modified_by} ({h.modified_role})",
                    "Target Field": h.field_name,
                    "Previous Value": h.old_value or "-",
                    "New Value": h.new_value or "-",
                    "Audit Note / Reason": h.audit_note or "-"
                })
            st.dataframe(pd.DataFrame(hist_list), use_container_width=True)
        else:
            st.info("No prior data modification records logged for this entity.")

