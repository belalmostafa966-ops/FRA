import streamlit as st
import pandas as pd
import datetime
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Company, Complaint, FinancialRecord, RiskScoreHistory, ScoringWeight, CompanyHistory, CompanyReport
from risk_engine.complaints import calculate_complaints_metrics, calculate_complaints_risk_score, evaluate_complaint_ews_alerts
from risk_engine.financial import calculate_financial_ratios, calculate_financial_risk_score, calculate_composite_risk, evaluate_financial_ews_alerts
from utils.report_generator import generate_risk_summary_csv
from config import DEFAULT_COMPLAINT_WEIGHTS
from utils.company_manager import update_company_data, create_company_manual, upload_company_report, delete_company_entity
from utils.company_modal import render_company_details_dialog

def render_analyst_hub_view():
    """
    Renders Risk Analyst Hub: Direct entity data editing, report uploads, change history logs,
    CSV batch importer, risk engine triggers, and compliance summary exports.
    """
    if "edit_success_msg" in st.session_state:
        st.success(st.session_state.pop("edit_success_msg"))
        st.toast("Action executed successfully!", icon="✅")

    st.title("Risk Analyst Data Hub & Calculation Engine")
    st.markdown("Edit entity metrics inline, upload regulatory audit reports, import CSV datasets, trigger batch risk models, and review staff modification logs.")

    db: Session = SessionLocal()
    user = st.session_state.get("user", {})

    try:
        tab_editor, tab_calc, tab_upload, tab_history, tab_export = st.tabs([
            "Direct Entity Data Editor & Reports",
            "Batch Risk Model Execution",
            "CSV Batch Importer",
            "Company Change History Audit Trail",
            "Export Compliance Summaries"
        ])

        # -------------------------------------------------------------
        # Tab 1: Direct Entity Data Editor & Reports Upload
        # -------------------------------------------------------------
        with tab_editor:
            st.subheader("Direct Inline Entity Data Editor")
            st.info("Modify company statistics, complaint metrics, and financial records directly in the database without uploading a new Excel/CSV file.")

            companies = db.query(Company).order_by(Company.name.asc()).all()
            if not companies:
                st.warning("No companies found in database.")
            else:
                comp_map = {f"{c.name} ({c.tax_id}) — Sector: {c.sector}": c.id for c in companies}
                selected_str = st.selectbox("Select Monitored Entity to Edit", list(comp_map.keys()), key="analyst_edit_comp_select")
                selected_id = comp_map[selected_str]

                if st.button("View Full Entity Details (Modal Popup)", use_container_width=True, key="analyst_view_modal_btn"):
                    render_company_details_dialog(db, selected_id)

                target_comp = db.query(Company).filter(Company.id == selected_id).first()
                target_comp_rec = db.query(Complaint).filter(Complaint.company_id == selected_id).order_by(Complaint.year.desc(), Complaint.quarter.desc()).first()
                target_fin_rec = db.query(FinancialRecord).filter(FinancialRecord.company_id == selected_id).order_by(FinancialRecord.year.desc(), FinancialRecord.quarter.desc()).first()

                subtab_edit, subtab_delete, subtab_create, subtab_rep = st.tabs([
                    "Edit Existing Entity",
                    "Delete Monitored Entity",
                    "Register New Entity",
                    "Upload Audit Reports"
                ])

                with subtab_edit:
                    with st.form("analyst_inline_edit_form"):
                        st.markdown("#### Company Profile")
                        ec1, ec2, ec3 = st.columns(3)
                        with ec1:
                            new_name = st.text_input("Company Name", value=target_comp.name)
                        with ec2:
                            new_tax = st.text_input("Tax ID", value=target_comp.tax_id)
                        with ec3:
                            new_sector = st.selectbox("Sector", ["Capital Markets", "Insurance", "Microfinance", "Consumer Finance", "Leasing"], index=["Capital Markets", "Insurance", "Microfinance", "Consumer Finance", "Leasing"].index(target_comp.sector) if target_comp.sector in ["Capital Markets", "Insurance", "Microfinance", "Consumer Finance", "Leasing"] else 0)

                        st.markdown("---")
                        st.markdown("#### Complaints & Supervisory Risk Metrics")
                        cc1, cc2, cc3 = st.columns(3)
                        with cc1:
                            new_tot_comp = st.number_input("Total Complaints Volume", min_value=0, value=int(target_comp_rec.total_complaints) if target_comp_rec else 0)
                            new_neg_comp = st.number_input("Negative Sentiment Complaints", min_value=0, value=int(target_comp_rec.negative_count) if target_comp_rec else 0)
                        with cc2:
                            new_sev_comp = st.number_input("High Severity Violation Complaints", min_value=0, value=int(target_comp_rec.high_severity_count) if target_comp_rec else 0)
                            new_open_comp = st.number_input("Unresolved Open Complaints", min_value=0, value=int(target_comp_rec.open_count) if target_comp_rec else 0)
                        with cc3:
                            new_fraud_comp = st.number_input("Fraud & Financial Misconduct Allegations", min_value=0, value=int(target_comp_rec.fraud_allegation_count) if target_comp_rec else 0)
                            new_growth_comp = st.number_input("QoQ Complaint Growth Rate (%)", min_value=-100.0, max_value=500.0, value=float(target_comp_rec.growth_rate * 100.0) if target_comp_rec else 0.0, step=0.5)

                        st.markdown("---")
                        st.markdown("#### Financial Indicators ($ USD / EGP)")
                        fc1, fc2, fc3 = st.columns(3)
                        with fc1:
                            new_rev = st.number_input("Quarterly Revenue", min_value=0.0, value=float(target_fin_rec.revenue) if target_fin_rec else 0.0, step=100000.0)
                            new_net_inc = st.number_input("Net Income / Profit", value=float(target_fin_rec.net_income) if target_fin_rec else 0.0, step=50000.0)
                            new_equity = st.number_input("Shareholders' Equity", value=float(target_fin_rec.total_equity) if target_fin_rec else 0.0, step=100000.0)
                        with fc2:
                            new_tot_assets = st.number_input("Total Assets", min_value=0.0, value=float(target_fin_rec.total_assets) if target_fin_rec else 0.0, step=500000.0)
                            new_tot_liab = st.number_input("Total Liabilities", min_value=0.0, value=float(target_fin_rec.total_liabilities) if target_fin_rec else 0.0, step=500000.0)
                        with fc3:
                            new_curr_assets = st.number_input("Current Assets", min_value=0.0, value=float(target_fin_rec.current_assets) if target_fin_rec else 0.0, step=100000.0)
                            new_curr_liab = st.number_input("Current Liabilities", min_value=0.0, value=float(target_fin_rec.current_liabilities) if target_fin_rec else 0.0, step=100000.0)
                            new_cash = st.number_input("Cash & Cash Equivalents", min_value=0.0, value=float(target_fin_rec.cash_and_equivalents) if target_fin_rec else 0.0, step=50000.0)

                        st.markdown("---")
                        audit_note = st.text_area("Audit Log Reason / Note (Required for Staff Log)", placeholder="e.g. Adjusted Q3 revenue following audit statement verification...")

                        save_btn = st.form_submit_button("Save Changes & Recalculate Risk Score", type="primary", use_container_width=True)

                        if save_btn:
                            if not audit_note.strip():
                                st.error("Please provide an Audit Log Note explaining the modification.")
                            else:
                                c_up = {"name": new_name.strip(), "tax_id": new_tax.strip(), "sector": new_sector}
                                comp_up = {
                                    "total_complaints": new_tot_comp, "negative_count": new_neg_comp,
                                    "high_severity_count": new_sev_comp, "open_count": new_open_comp,
                                    "fraud_allegation_count": new_fraud_comp, "growth_rate": new_growth_comp / 100.0
                                }
                                fin_up = {
                                    "revenue": new_rev, "net_income": new_net_inc, "total_assets": new_tot_assets,
                                    "total_liabilities": new_tot_liab, "current_assets": new_curr_assets,
                                    "current_liabilities": new_curr_liab, "total_equity": new_equity,
                                    "cash_and_equivalents": new_cash
                                }
                                ok, updated_comp, changes, new_sc = update_company_data(
                                    db, target_comp.id, user, c_up, comp_up, fin_up, audit_note.strip()
                                )
                                if ok:
                                    st.session_state["edit_success_msg"] = f"Successfully updated '{updated_comp.name}'! Modified {len(changes)} fields. Recalculated Risk Score: {new_sc:.1f} ({updated_comp.risk_level.upper()})."
                                    st.rerun()

                with subtab_delete:
                    st.markdown("#### Permanent Monitored Entity Deletion")
                    st.error(f"⚠️ DANGER ZONE: You are about to delete entity '{target_comp.name}' (Tax ID: {target_comp.tax_id}).")
                    st.markdown("Deleting this entity will permanently purge all associated complaints, financials, risk score histories, inspection tasks, and attached regulatory reports.")

                    confirm_del_analyst = st.checkbox(f"I confirm I want to PERMANENTLY DELETE '{target_comp.name}' from the FRA platform", key=f"confirm_del_tab_analyst_{target_comp.id}")
                    if st.button("Permanently Delete Entity", type="primary", disabled=not confirm_del_analyst, key=f"btn_del_tab_analyst_{target_comp.id}", use_container_width=True):
                        success_del, msg_del = delete_company_entity(db, target_comp.id, user)
                        if success_del:
                            st.session_state["edit_success_msg"] = msg_del
                            st.rerun()
                        else:
                            st.error(msg_del)

                with subtab_create:
                    with st.form("analyst_manual_create_form"):
                        m1, m2, m3 = st.columns(3)
                        m_tax = m1.text_input("Tax ID", placeholder="TAX-EG-123456")
                        m_name = m2.text_input("Entity Name", placeholder="e.g. Delta Finance")
                        m_sec = m3.selectbox("Sector", ["Capital Markets", "Insurance", "Microfinance", "Consumer Finance", "Leasing"])

                        st.markdown("#### Financials ($ USD / EGP)")
                        mf1, mf2, mf3 = st.columns(3)
                        m_rev = mf1.number_input("Revenue", min_value=0.0, value=1000000.0)
                        m_net = mf1.number_input("Net Income", value=150000.0)
                        m_assets = mf2.number_input("Total Assets", min_value=0.0, value=5000000.0)
                        m_liab = mf2.number_input("Total Liabilities", min_value=0.0, value=2000000.0)
                        m_eq = mf3.number_input("Equity", min_value=0.0, value=3000000.0)
                        m_cash = mf3.number_input("Cash", min_value=0.0, value=500000.0)

                        st.markdown("#### Complaints")
                        mc1, mc2 = st.columns(2)
                        m_tot_c = mc1.number_input("Total Complaints", min_value=0, value=5)
                        m_neg_c = mc1.number_input("Negative Complaints", min_value=0, value=1)
                        m_open_c = mc2.number_input("Open Complaints", min_value=0, value=1)
                        m_fraud_c = mc2.number_input("Fraud Allegations", min_value=0, value=0)

                        c_submit = st.form_submit_button("Register New Entity", type="primary", use_container_width=True)

                        if c_submit:
                            if not m_tax.strip() or not m_name.strip():
                                st.error("Tax ID and Entity Name are required.")
                            else:
                                c_d = {"total_complaints": m_tot_c, "negative_count": m_neg_c, "high_severity_count": 0, "open_count": m_open_c, "fraud_allegation_count": m_fraud_c, "growth_rate": 0.0}
                                f_d = {"revenue": m_rev, "net_income": m_net, "total_assets": m_assets, "total_liabilities": m_liab, "current_assets": m_assets * 0.4, "current_liabilities": m_liab * 0.5, "total_equity": m_eq, "cash_and_equivalents": m_cash}
                                ok, new_c, err = create_company_manual(db, user, m_tax, m_name, m_sec, c_d, f_d)
                                if ok:
                                    st.success(f"Registered entity '{new_c.name}' successfully!")
                                    st.rerun()
                                else:
                                    st.error(err)

                with subtab_rep:
                    with st.form("analyst_upload_rep_form"):
                        r_title = st.text_input("Report Title", placeholder="Q3 Supervisory Audit Summary")
                        r_file = st.file_uploader("Upload Audit Document (.pdf, .docx, .xlsx, .png)", type=["pdf", "docx", "xlsx", "png", "jpg", "txt"])
                        r_notes = st.text_area("Audit Notes", placeholder="Key findings and compliance observations...")
                        r_btn = st.form_submit_button("Attach Report to Entity", type="primary", use_container_width=True)

                        if r_btn:
                            if not r_file:
                                st.error("Please choose a file.")
                            else:
                                ok, msg = upload_company_report(db, target_comp.id, r_file, r_title, user, r_notes)
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

        # -------------------------------------------------------------
        # Tab 2: Batch Risk Model Execution
        # -------------------------------------------------------------
        with tab_calc:
            st.subheader("Execute Regulatory Risk Engine")
            st.markdown("Triggers model calculations for all monitored entities using active scoring weights stored in the database.")

            active_weights_obj = db.query(ScoringWeight).order_by(ScoringWeight.updated_at.desc()).first()
            if active_weights_obj:
                weights = {
                    "vol_w": active_weights_obj.vol_w, "neg_w": active_weights_obj.neg_w,
                    "sev_w": active_weights_obj.sev_w, "open_w": active_weights_obj.open_w,
                    "fraud_w": active_weights_obj.fraud_w, "growth_w": active_weights_obj.growth_w,
                }
            else:
                weights = DEFAULT_COMPLAINT_WEIGHTS

            st.info(f"**Current Scoring Weights:** Volume={weights['vol_w']*100:.0f}% | Negative={weights['neg_w']*100:.0f}% | Severity={weights['sev_w']*100:.0f}% | Open={weights['open_w']*100:.0f}% | Fraud={weights['fraud_w']*100:.0f}% | Growth={weights['growth_w']*100:.0f}%")

            if st.button("Run Full System Risk Evaluation Now", type="primary", use_container_width=True):
                companies = db.query(Company).all()
                updated_count = 0
                ews_alert_count = 0

                for company in companies:
                    latest_comp = db.query(Complaint).filter(Complaint.company_id == company.id).order_by(Complaint.year.desc(), Complaint.quarter.desc()).first()
                    latest_fin = db.query(FinancialRecord).filter(FinancialRecord.company_id == company.id).order_by(FinancialRecord.year.desc(), FinancialRecord.quarter.desc()).first()

                    if latest_comp and latest_fin:
                        comp_metrics = calculate_complaints_metrics(
                            total_complaints=latest_comp.total_complaints, negative_count=latest_comp.negative_count,
                            high_severity_count=latest_comp.high_severity_count, open_count=latest_comp.open_count,
                            fraud_allegation_count=latest_comp.fraud_allegation_count, growth_rate=latest_comp.growth_rate
                        )
                        comp_score = calculate_complaints_risk_score(comp_metrics, weights=weights)

                        fin_ratios = calculate_financial_ratios(
                            revenue=latest_fin.revenue, net_income=latest_fin.net_income,
                            total_assets=latest_fin.total_assets, total_liabilities=latest_fin.total_liabilities,
                            current_assets=latest_fin.current_assets, current_liabilities=latest_fin.current_liabilities,
                            total_equity=latest_fin.total_equity, cash_and_equivalents=latest_fin.cash_and_equivalents
                        )
                        fin_score = calculate_financial_risk_score(fin_ratios)

                        composite_score, risk_lvl = calculate_composite_risk(comp_score, fin_score)

                        c_alert, c_reasons = evaluate_complaint_ews_alerts(comp_metrics, comp_score)
                        f_alert, f_reasons = evaluate_financial_ews_alerts(fin_ratios, fin_score)
                        ews_flag = c_alert or f_alert
                        all_reasons = c_reasons + f_reasons

                        if ews_flag:
                            ews_alert_count += 1

                        new_hist = RiskScoreHistory(
                            company_id=company.id, evaluation_date=datetime.datetime.utcnow(),
                            complaint_score=comp_score, financial_score=fin_score,
                            composite_score=composite_score, risk_level=risk_lvl,
                            ews_alert_flag=ews_flag, ews_reasons=" | ".join(all_reasons) if all_reasons else None
                        )
                        db.add(new_hist)
                        company.risk_level = risk_lvl
                        updated_count += 1

                db.commit()
                st.success(f"Risk Evaluation Completed! Evaluated {updated_count} entities. Detected {ews_alert_count} Active EWS Alerts.")

        # -------------------------------------------------------------
        # Tab 3: CSV Data Batch Importer
        # -------------------------------------------------------------
        with tab_upload:
            st.subheader("Upload Quarterly Financials & Complaints Data (CSV)")
            st.markdown("Upload CSV files to batch import company financial statements or complaints datasets directly.")

            st.write("#### 1. Import Complaints Data (CSV)")
            comp_csv = st.file_uploader("Choose Complaints CSV File", type=["csv"], key="comp_csv_up")
            if comp_csv is not None:
                try:
                    df_c = pd.read_csv(comp_csv)
                    st.dataframe(df_c.head())
                    if st.button("Confirm Import Complaints CSV"):
                        imported = 0
                        for _, row in df_c.iterrows():
                            comp_obj = db.query(Company).filter(
                                (Company.tax_id == str(row["tax_id"])) | (Company.name == str(row["company_name"]))
                            ).first()
                            if comp_obj:
                                rec = Complaint(
                                    company_id=comp_obj.id, quarter=str(row.get("quarter", "Q1")),
                                    year=int(row.get("year", 2026)), total_complaints=int(row.get("total_complaints", 0)),
                                    negative_count=int(row.get("negative_count", 0)), high_severity_count=int(row.get("high_severity_count", 0)),
                                    open_count=int(row.get("open_count", 0)), fraud_allegation_count=int(row.get("fraud_allegation_count", 0)),
                                    growth_rate=float(row.get("growth_rate", 0.0))
                                )
                                db.add(rec)
                                imported += 1
                        db.commit()
                        st.success(f"Successfully imported {imported} complaint records!")
                except Exception as e:
                    st.error(f"Error parsing Complaints CSV: {e}")

            st.write("#### 2. Import Financial Statements Data (CSV)")
            fin_csv = st.file_uploader("Choose Financial Statements CSV File", type=["csv"], key="fin_csv_up")
            if fin_csv is not None:
                try:
                    df_f = pd.read_csv(fin_csv)
                    st.dataframe(df_f.head())
                    if st.button("Confirm Import Financial Statements CSV"):
                        imported = 0
                        for _, row in df_f.iterrows():
                            comp_obj = db.query(Company).filter(
                                (Company.tax_id == str(row["tax_id"])) | (Company.name == str(row["company_name"]))
                            ).first()
                            if comp_obj:
                                rec = FinancialRecord(
                                    company_id=comp_obj.id, quarter=str(row.get("quarter", "Q1")),
                                    year=int(row.get("year", 2026)), revenue=float(row.get("revenue", 0.0)),
                                    net_income=float(row.get("net_income", 0.0)), total_assets=float(row.get("total_assets", 0.0)),
                                    total_liabilities=float(row.get("total_liabilities", 0.0)), current_assets=float(row.get("current_assets", 0.0)),
                                    current_liabilities=float(row.get("current_liabilities", 0.0)), total_equity=float(row.get("total_equity", 0.0)),
                                    cash_and_equivalents=float(row.get("cash_and_equivalents", 0.0))
                                )
                                db.add(rec)
                                imported += 1
                        db.commit()
                        st.success(f"Successfully imported {imported} financial statement records!")
                except Exception as e:
                    st.error(f"Error parsing Financial Statements CSV: {e}")

            st.markdown("---")
            st.subheader("Download CSV Templates")
            sample_comp_df = pd.DataFrame([{
                "tax_id": "TAX-EG-102938", "company_name": "EFG Hermes Holding", "quarter": "Q1", "year": 2026,
                "total_complaints": 50, "negative_count": 10, "high_severity_count": 3, "open_count": 5,
                "fraud_allegation_count": 0, "growth_rate": 0.05
            }])
            st.download_button(
                "Download Complaints CSV Template",
                data=sample_comp_df.to_csv(index=False),
                file_name="complaints_template.csv",
                mime="text/csv"
            )

        # -------------------------------------------------------------
        # Tab 4: Company Change History Audit Trail
        # -------------------------------------------------------------
        with tab_history:
            st.subheader("Company Change History Audit Trail")
            st.markdown("Review all manual entity modifications, updated financial figures, and audit reasons logged by staff.")

            hist_logs = db.query(CompanyHistory, Company).join(Company, CompanyHistory.company_id == Company.id).order_by(CompanyHistory.created_at.desc()).all()

            if not hist_logs:
                st.info("No company history logs recorded yet.")
            else:
                hist_data = []
                for h, c in hist_logs:
                    hist_data.append({
                        "Timestamp": h.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "Company Name": c.name,
                        "Modified By": f"{h.modified_by} ({h.modified_role})",
                        "Field Modified": h.field_name,
                        "Old Value": h.old_value or "-",
                        "New Value": h.new_value or "-",
                        "Audit Reason / Note": h.audit_note or "-"
                    })

                df_h = pd.DataFrame(hist_data)
                search_q = st.text_input("Filter History Log", "", key="analyst_hist_search")
                if search_q.strip():
                    q = search_q.strip().lower()
                    df_h = df_h[
                        df_h["Company Name"].str.lower().str.contains(q) |
                        df_h["Modified By"].str.lower().str.contains(q) |
                        df_h["Field Modified"].str.lower().str.contains(q) |
                        df_h["Audit Reason / Note"].str.lower().str.contains(q)
                    ]

                st.dataframe(df_h, use_container_width=True)

        # -------------------------------------------------------------
        # Tab 5: Export Compliance Summaries
        # -------------------------------------------------------------
        with tab_export:
            st.subheader("Export System Risk Summary")
            st.markdown("Generate and download full supervisory audit spreadsheets for all monitored entities.")

            csv_data = generate_risk_summary_csv(db)
            st.download_button(
                label="Download Full System Risk Summary (.CSV)",
                data=csv_data,
                file_name=f"FRA_Risk_Summary_{datetime.date.today()}.csv",
                mime="text/csv",
                use_container_width=True
            )

    finally:
        db.close()
