import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Company, RiskScoreHistory, Complaint, FinancialRecord, CompanyHistory, CompanyReport
from risk_engine.financial import calculate_financial_ratios
from risk_engine.complaints import calculate_complaints_metrics
from utils.report_generator import generate_company_compliance_report

def render_company_deepdive_view():
    """
    Renders deep-dive view for a specific regulated company showing quarterly financials,
    complaint breakdowns, change history audit trail, and attached audit reports.
    """
    st.title("Company Risk Deep-Dive")
    st.markdown("Detailed quarterly trajectory analysis, complaint severity breakdowns, change history audit trail, and attached audit reports.")

    db: Session = SessionLocal()
    try:
        companies = db.query(Company).order_by(Company.name).all()
        if not companies:
            st.warning("No companies found in database.")
            return

        company_map = {f"{c.name} ({c.sector})": c.id for c in companies}
        selected_label = st.selectbox("Select Regulated Entity to Inspect", list(company_map.keys()))
        selected_company_id = company_map[selected_label]

        company = db.query(Company).filter(Company.id == selected_company_id).first()

        fin_records = (
            db.query(FinancialRecord)
            .filter(FinancialRecord.company_id == company.id)
            .order_by(FinancialRecord.year.asc(), FinancialRecord.quarter.asc())
            .all()
        )

        comp_records = (
            db.query(Complaint)
            .filter(Complaint.company_id == company.id)
            .order_by(Complaint.year.asc(), Complaint.quarter.asc())
            .all()
        )

        risk_history = (
            db.query(RiskScoreHistory)
            .filter(RiskScoreHistory.company_id == company.id)
            .order_by(RiskScoreHistory.evaluation_date.desc())
            .all()
        )

        latest_risk = risk_history[0] if risk_history else None

        # -------------------------------------------------------------
        # 1. Official FRA Regulatory Header Cards
        # -------------------------------------------------------------
        st.markdown("---")
        b1, b2, b3, b4 = st.columns(4)

        with b1:
            st.markdown(f"""
            <div class="fra-card-navy">
                <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #D97706; letter-spacing: 0.05em;">ENTITY NAME</div>
                <div style="font-size: 1.35rem; font-weight: 800; margin-top: 0.2rem; color: #FFFFFF;">{company.name}</div>
                <div style="font-size: 0.8rem; margin-top: 0.4rem; color: #CBD5E1;">Tax ID: {company.tax_id}</div>
            </div>
            """, unsafe_allow_html=True)

        with b2:
            score_val = f"{latest_risk.composite_score:.1f}" if latest_risk else "N/A"
            st.markdown(f"""
            <div class="fra-card-navy">
                <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #D97706; letter-spacing: 0.05em;">COMPOSITE RISK SCORE</div>
                <div style="font-size: 2rem; font-weight: 800; margin-top: 0.1rem; color: #FFFFFF;">{score_val} <span style="font-size: 1rem; color: #CBD5E1;">/ 100</span></div>
                <div style="font-size: 0.8rem; margin-top: 0.2rem; color: #CBD5E1;">Sector: {company.sector}</div>
            </div>
            """, unsafe_allow_html=True)

        with b3:
            card_bg = "background: linear-gradient(135deg, #78350F 0%, #D97706 100%);" if company.risk_level in ["High", "Critical"] else "background: linear-gradient(135deg, #065F46 0%, #10B981 100%);"
            st.markdown(f"""
            <div class="fra-card-gold" style="{card_bg}">
                <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #FEF3C7; letter-spacing: 0.05em;">RISK CLASSIFICATION</div>
                <div style="font-size: 1.6rem; font-weight: 800; margin-top: 0.2rem; color: #FFFFFF;">{company.risk_level.upper()}</div>
                <div style="font-size: 0.8rem; margin-top: 0.3rem; color: #FEF3C7;">Supervisory Priority</div>
            </div>
            """, unsafe_allow_html=True)

        with b4:
            ews_flag = latest_risk and latest_risk.ews_alert_flag
            ews_bg = "background: linear-gradient(135deg, #7F1D1D 0%, #EF4444 100%);" if ews_flag else "background: linear-gradient(135deg, #0F172A 0%, #334155 100%);"
            st.markdown(f"""
            <div style="{ews_bg} border-radius: 18px; padding: 1.5rem; color: #FFFFFF; box-shadow: 0 10px 25px rgba(0,0,0,0.15);">
                <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #FCA5A5; letter-spacing: 0.05em;">EWS ALERT STATUS</div>
                <div style="font-size: 1.5rem; font-weight: 800; margin-top: 0.2rem; color: #FFFFFF;">{"ACTIVE TRIGGER" if ews_flag else "NORMAL"}</div>
                <div style="font-size: 0.8rem; margin-top: 0.3rem; color: #F3F4F6;">Early Warning System</div>
            </div>
            """, unsafe_allow_html=True)

        if latest_risk and latest_risk.ews_reasons:
            st.error(f"**EWS Active Triggers:** {latest_risk.ews_reasons}")

        st.markdown("<br>", unsafe_allow_html=True)
        # Download Official Compliance Report CTA Button
        report_text = generate_company_compliance_report(db, company.id)
        st.download_button(
            label="Download Official Compliance & Risk Report (.txt)",
            data=report_text,
            file_name=f"FRA_Risk_Report_{company.tax_id}.txt",
            mime="text/plain",
            type="primary",
            use_container_width=True
        )

        st.markdown("---")

        # Tabs Setup
        tab_fin, tab_comp, tab_reports, tab_hist = st.tabs([
            "Financial & Ratio Analytics",
            "Complaints & Consumer Protection",
            "Attached Audit Reports",
            "Company Change History & Audit Log"
        ])

        # -------------------------------------------------------------
        # Tab 1: Financial & Ratio Analytics
        # -------------------------------------------------------------
        with tab_fin:
            st.subheader("Quarterly Financial Trajectory & Ratio Health")

            if fin_records:
                fin_data = []
                for f in fin_records:
                    ratios = calculate_financial_ratios(
                        revenue=f.revenue, net_income=f.net_income, total_assets=f.total_assets,
                        total_liabilities=f.total_liabilities, current_assets=f.current_assets,
                        current_liabilities=f.current_liabilities, total_equity=f.total_equity,
                        cash_and_equivalents=f.cash_and_equivalents
                    )
                    period_str = f"{f.year} {f.quarter}"
                    fin_data.append({
                        "Period": period_str,
                        "Revenue (EGP)": f.revenue,
                        "Net Income (EGP)": f.net_income,
                        "Profit Margin (%)": ratios["profit_margin"] * 100,
                        "Debt Ratio (%)": ratios["debt_ratio"] * 100,
                        "Current Ratio": ratios["current_ratio"],
                        "Cash Ratio": ratios["cash_ratio"],
                        "Debt to Equity": ratios["debt_to_equity"],
                    })

                df_fin = pd.DataFrame(fin_data)

                f_chart_col1, f_chart_col2 = st.columns(2)

                with f_chart_col1:
                    fig_rev = px.bar(
                        df_fin,
                        x="Period",
                        y=["Revenue (EGP)", "Net Income (EGP)"],
                        barmode="group",
                        title="Revenue & Net Income Trend (EGP)",
                        color_discrete_sequence=["#2563EB", "#10B981"],
                        height=350
                    )
                    fig_rev.update_layout(
                        template="plotly_white",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Plus Jakarta Sans, sans-serif", color="#1E293B"),
                    )
                    st.plotly_chart(fig_rev, use_container_width=True)

                with f_chart_col2:
                    fig_ratios = px.line(
                        df_fin,
                        x="Period",
                        y=["Profit Margin (%)", "Debt Ratio (%)"],
                        title="Profit Margin & Debt Ratio Trend (%)",
                        color_discrete_sequence=["#7C3AED", "#D97706"],
                        markers=True,
                        height=350
                    )
                    fig_ratios.update_layout(
                        template="plotly_white",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Plus Jakarta Sans, sans-serif", color="#1E293B"),
                    )
                    st.plotly_chart(fig_ratios, use_container_width=True)

                st.markdown("#### Solvency & Liquidity Ratios (Latest Quarter)")
                latest_fin = df_fin.iloc[-1]
                l_col1, l_col2, l_col3, l_col4 = st.columns(4)
                l_col1.metric("Profit Margin", f"{latest_fin['Profit Margin (%)']:.1f}%")
                l_col2.metric("Debt Ratio", f"{latest_fin['Debt Ratio (%)']:.1f}%")
                l_col3.metric("Current Ratio", f"{latest_fin['Current Ratio']:.2f}")
                l_col4.metric("Cash Ratio", f"{latest_fin['Cash Ratio']:.2f}")

            else:
                st.info("No financial records uploaded for this company.")

        # -------------------------------------------------------------
        # Tab 2: Complaints & Consumer Protection
        # -------------------------------------------------------------
        with tab_comp:
            st.subheader("Consumer Complaints & Severity Metrics")

            if comp_records:
                comp_data = []
                for c in comp_records:
                    period_str = f"{c.year} {c.quarter}"
                    comp_data.append({
                        "Period": period_str,
                        "Total Complaints": c.total_complaints,
                        "Negative Complaints": c.negative_count,
                        "High Severity": c.high_severity_count,
                        "Open Complaints": c.open_count,
                        "Fraud Allegations": c.fraud_allegation_count,
                        "Growth Rate (%)": c.growth_rate * 100
                    })

                df_comp = pd.DataFrame(comp_data)

                c_chart_col1, c_chart_col2 = st.columns(2)

                with c_chart_col1:
                    fig_comp_vol = px.line(
                        df_comp,
                        x="Period",
                        y=["Total Complaints", "Negative Complaints", "Open Complaints"],
                        title="Quarterly Complaints Volume & Status",
                        color_discrete_sequence=["#2563EB", "#D97706", "#EF4444"],
                        markers=True,
                        height=350
                    )
                    fig_comp_vol.update_layout(
                        template="plotly_white",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Plus Jakarta Sans, sans-serif", color="#1E293B"),
                    )
                    st.plotly_chart(fig_comp_vol, use_container_width=True)

                with c_chart_col2:
                    latest_comp = df_comp.iloc[-1]
                    pie_data = pd.DataFrame({
                        "Category": ["High Severity", "Fraud Allegation", "Other Complaints"],
                        "Count": [
                            latest_comp["High Severity"],
                            latest_comp["Fraud Allegations"],
                            max(0, latest_comp["Total Complaints"] - latest_comp["High Severity"] - latest_comp["Fraud Allegations"])
                        ]
                    })
                    fig_pie = px.pie(
                        pie_data,
                        values="Count",
                        names="Category",
                        title="Latest Quarter Complaints Composition",
                        color_discrete_sequence=["#EF4444", "#991B1B", "#3B82F6"],
                        height=350
                    )
                    fig_pie.update_layout(
                        template="plotly_white",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="Plus Jakarta Sans, sans-serif", color="#1E293B"),
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)

            else:
                st.info("No complaint records found for this company.")

        # -------------------------------------------------------------
        # Tab 3: Attached Audit Reports
        # -------------------------------------------------------------
        with tab_reports:
            st.subheader(f"Attached Regulatory Audit Reports for {company.name}")
            reports = db.query(CompanyReport).filter(CompanyReport.company_id == company.id).order_by(CompanyReport.created_at.desc()).all()

            if not reports:
                st.info("No audit reports attached to this company yet. Staff can upload reports via the Admin Panel or Analyst Hub.")
            else:
                rep_data = []
                for r in reports:
                    rep_data.append({
                        "Report Title": r.title,
                        "Filename": r.filename,
                        "Format": r.file_type,
                        "Size (KB)": r.file_size_kb,
                        "Uploaded By": r.uploaded_by,
                        "Upload Date": r.created_at.strftime("%Y-%m-%d %H:%M"),
                        "Notes": r.notes or "-"
                    })
                st.dataframe(pd.DataFrame(rep_data), use_container_width=True)

        # -------------------------------------------------------------
        # Tab 4: Company Change History & Staff Audit Log
        # -------------------------------------------------------------
        with tab_hist:
            st.subheader(f"Modification & Change History Audit Trail ({company.name})")
            st.markdown("Chronological record of all manual edits, value updates, and audit notes entered by supervisory staff.")

            company_logs = db.query(CompanyHistory).filter(CompanyHistory.company_id == company.id).order_by(CompanyHistory.created_at.desc()).all()

            if not company_logs:
                st.info("No manual edits recorded for this company yet.")
            else:
                h_rows = []
                for h in company_logs:
                    h_rows.append({
                        "Timestamp": h.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "Modified By Staff": f"{h.modified_by} ({h.modified_role})",
                        "Field Modified": h.field_name,
                        "Previous Value": h.old_value or "-",
                        "Updated Value": h.new_value or "-",
                        "Audit Reason / Note": h.audit_note or "-"
                    })
                st.dataframe(pd.DataFrame(h_rows), use_container_width=True)

            st.markdown("---")
            st.subheader("Historical Risk Scoring Audit Log")
            if risk_history:
                hist_rows = []
                for rh in risk_history:
                    hist_rows.append({
                        "Evaluation Date": rh.evaluation_date.strftime("%Y-%m-%d %H:%M"),
                        "Composite Score": rh.composite_score,
                        "Complaints Score": rh.complaint_score,
                        "Financial Score": rh.financial_score,
                        "Risk Level": rh.risk_level,
                        "EWS Alert": "YES" if rh.ews_alert_flag else "NO",
                        "EWS Reasons": rh.ews_reasons or "-"
                    })
                st.dataframe(pd.DataFrame(hist_rows), use_container_width=True)

    finally:
        db.close()
