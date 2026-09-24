import streamlit as st
import datetime
import os
import pandas as pd
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User, Company, Complaint, FinancialRecord, ScoringWeight, CompanyHistory, CompanyReport, ActivityLog
from auth import hash_password
from config import DEFAULT_COMPLAINT_WEIGHTS
from utils.company_manager import update_company_data, create_company_manual, upload_company_report, delete_company_entity, REPORTS_DIR
from utils.email_service import get_smtp_settings, save_smtp_settings
from utils.company_modal import render_company_details_dialog

def render_admin_panel_view():
    """
    Renders Admin Panel: Data editing, manual entity creation, report upload,
    change history audit trail, weight tuning, SMTP email settings, and user RBAC controls.
    """
    if "edit_success_msg" in st.session_state:
        st.success(st.session_state.pop("edit_success_msg"))
        st.toast("Action executed successfully!", icon="✅")

    st.title("Admin System Control & Entity Management")
    st.markdown("Directly edit entity statistics, upload regulatory audit reports, inspect staff modification histories, configure SMTP email server, tune risk model weights, and manage RBAC access.")

    db: Session = SessionLocal()
    user = st.session_state.get("user", {})

    try:
        tab_editor, tab_create, tab_reports, tab_history, tab_weights, tab_smtp, tab_users = st.tabs([
            "Edit Entity Data Inline",
            "Manual Company Registration",
            "Upload Audit Reports",
            "Company Change History Log",
            "Risk Model Weight Tuning",
            "SMTP Email Configuration",
            "User Management & RBAC"
        ])

        # -------------------------------------------------------------
        # Tab 1: Direct Entity Data Editor (No CSV Re-upload Required)
        # -------------------------------------------------------------
        with tab_editor:
            st.subheader("Direct Inline Entity Data Editor")
            st.info("Select a monitored entity to modify its complaints, financials, or risk metrics directly in the database without uploading a new Excel/CSV file.")

            companies = db.query(Company).order_by(Company.name.asc()).all()
            if not companies:
                st.warning("No companies found in database.")
            else:
                company_map = {f"{c.name} ({c.tax_id}) — Sector: {c.sector}": c.id for c in companies}
                selected_company_str = st.selectbox("Select Monitored Entity to Edit", list(company_map.keys()), key="admin_edit_comp_select")
                selected_id = company_map[selected_company_str]

                if st.button("View Full Entity Details (Modal Popup)", use_container_width=True, key="admin_view_modal_btn"):
                    render_company_details_dialog(db, selected_id)

                target_company = db.query(Company).filter(Company.id == selected_id).first()
                target_comp_rec = db.query(Complaint).filter(Complaint.company_id == selected_id).order_by(Complaint.year.desc(), Complaint.quarter.desc()).first()
                target_fin_rec = db.query(FinancialRecord).filter(FinancialRecord.company_id == selected_id).order_by(FinancialRecord.year.desc(), FinancialRecord.quarter.desc()).first()

                with st.form("inline_edit_company_form"):
                    st.markdown("#### Basic Company Information")
                    ecol1, ecol2, ecol3 = st.columns(3)
                    with ecol1:
                        new_name = st.text_input("Company Name", value=target_company.name)
                    with ecol2:
                        new_tax = st.text_input("Tax ID", value=target_company.tax_id)
                    with ecol3:
                        new_sector = st.selectbox("Sector", ["Capital Markets", "Insurance", "Microfinance", "Consumer Finance", "Leasing"], index=["Capital Markets", "Insurance", "Microfinance", "Consumer Finance", "Leasing"].index(target_company.sector) if target_company.sector in ["Capital Markets", "Insurance", "Microfinance", "Consumer Finance", "Leasing"] else 0)

                    st.markdown("---")
                    st.markdown("#### Complaints & Supervisory Risk Metrics")
                    ccol1, ccol2, ccol3 = st.columns(3)
                    with ccol1:
                        new_tot_comp = st.number_input("Total Complaints Volume", min_value=0, value=int(target_comp_rec.total_complaints) if target_comp_rec else 0)
                        new_neg_comp = st.number_input("Negative Sentiment Complaints", min_value=0, value=int(target_comp_rec.negative_count) if target_comp_rec else 0)
                    with ccol2:
                        new_sev_comp = st.number_input("High Severity Violation Complaints", min_value=0, value=int(target_comp_rec.high_severity_count) if target_comp_rec else 0)
                        new_open_comp = st.number_input("Unresolved Open Complaints", min_value=0, value=int(target_comp_rec.open_count) if target_comp_rec else 0)
                    with ccol3:
                        new_fraud_comp = st.number_input("Fraud & Financial Misconduct Allegations", min_value=0, value=int(target_comp_rec.fraud_allegation_count) if target_comp_rec else 0)
                        new_growth_comp = st.number_input("QoQ Complaint Growth Rate (%)", min_value=-100.0, max_value=500.0, value=float(target_comp_rec.growth_rate * 100.0) if target_comp_rec else 0.0, step=0.5)

                    st.markdown("---")
                    st.markdown("#### Financial Records & Balance Sheet Ratios ($ USD / EGP)")
                    fcol1, fcol2, fcol3 = st.columns(3)
                    with fcol1:
                        new_rev = st.number_input("Quarterly Revenue", min_value=0.0, value=float(target_fin_rec.revenue) if target_fin_rec else 0.0, step=100000.0)
                        new_net_inc = st.number_input("Net Income / Profit", value=float(target_fin_rec.net_income) if target_fin_rec else 0.0, step=50000.0)
                        new_equity = st.number_input("Total Shareholders' Equity", value=float(target_fin_rec.total_equity) if target_fin_rec else 0.0, step=100000.0)
                    with fcol2:
                        new_tot_assets = st.number_input("Total Assets", min_value=0.0, value=float(target_fin_rec.total_assets) if target_fin_rec else 0.0, step=500000.0)
                        new_tot_liab = st.number_input("Total Liabilities", min_value=0.0, value=float(target_fin_rec.total_liabilities) if target_fin_rec else 0.0, step=500000.0)
                    with fcol3:
                        new_curr_assets = st.number_input("Current Assets", min_value=0.0, value=float(target_fin_rec.current_assets) if target_fin_rec else 0.0, step=100000.0)
                        new_curr_liab = st.number_input("Current Liabilities", min_value=0.0, value=float(target_fin_rec.current_liabilities) if target_fin_rec else 0.0, step=100000.0)
                        new_cash = st.number_input("Cash & Cash Equivalents", min_value=0.0, value=float(target_fin_rec.cash_and_equivalents) if target_fin_rec else 0.0, step=50000.0)

                    st.markdown("---")
                    audit_note = st.text_area("Audit Log Note / Reason for Change (Required for System Log)", placeholder="e.g. Updated Q3 audited financial figures following field inspection notes...")

                    save_edit_btn = st.form_submit_button("Save Changes & Recalculate Risk Live", type="primary", use_container_width=True)

                    if save_edit_btn:
                        if not audit_note.strip():
                            st.error("Please enter an Audit Log Note explaining the modification before saving.")
                        else:
                            comp_updates = {
                                "name": new_name.strip(),
                                "tax_id": new_tax.strip(),
                                "sector": new_sector
                            }
                            complaint_updates = {
                                "total_complaints": new_tot_comp,
                                "negative_count": new_neg_comp,
                                "high_severity_count": new_sev_comp,
                                "open_count": new_open_comp,
                                "fraud_allegation_count": new_fraud_comp,
                                "growth_rate": new_growth_comp / 100.0
                            }
                            financial_updates = {
                                "revenue": new_rev,
                                "net_income": new_net_inc,
                                "total_assets": new_tot_assets,
                                "total_liabilities": new_tot_liab,
                                "current_assets": new_curr_assets,
                                "current_liabilities": new_curr_liab,
                                "total_equity": new_equity,
                                "cash_and_equivalents": new_cash
                            }

                            success, updated_comp, changes_made, new_score = update_company_data(
                                db, target_company.id, user, comp_updates, complaint_updates, financial_updates, audit_note.strip()
                            )

                            if success:
                                st.session_state["edit_success_msg"] = f"Successfully updated '{updated_comp.name}'! Updated {len(changes_made)} fields. Recalculated Risk Score: {new_score:.1f} ({updated_comp.risk_level.upper()})."
                                st.rerun()

                st.markdown("---")
                with st.expander("Delete Monitored Entity", expanded=False):
                    st.warning(f"Warning: Deleting '{target_company.name}' (Tax ID: {target_company.tax_id}) will permanently remove all associated complaints, financials, risk histories, and attached audit reports.")
                    confirm_del_admin = st.checkbox(f"I confirm I want to permanently delete '{target_company.name}'", key=f"confirm_del_admin_{target_company.id}")
                    if st.button("Delete Entity Permanently", type="primary", disabled=not confirm_del_admin, key=f"btn_del_admin_{target_company.id}"):
                        success_del, msg_del = delete_company_entity(db, target_company.id, user)
                        if success_del:
                            st.session_state["edit_success_msg"] = msg_del
                            st.rerun()
                        else:
                            st.error(msg_del)

        # -------------------------------------------------------------
        # Tab 2: Manual Company Registration
        # -------------------------------------------------------------
        with tab_create:
            st.subheader("Manual Monitored Entity Registration")
            st.markdown("Register a new non-banking financial institution manually without uploading external files.")

            with st.form("manual_create_company_form"):
                mc1, mc2, mc3 = st.columns(3)
                with mc1:
                    m_tax_id = st.text_input("Tax ID (e.g. TAX-EG-998877)", placeholder="TAX-EG-123456")
                with mc2:
                    m_name = st.text_input("Entity Legal Name", placeholder="e.g. Al Ahly Financial Solutions")
                with mc3:
                    m_sector = st.selectbox("Supervisory Sector", ["Capital Markets", "Insurance", "Microfinance", "Consumer Finance", "Leasing"])

                st.markdown("---")
                st.markdown("#### Initial Financial Indicators ($ USD / EGP)")
                mf1, mf2, mf3 = st.columns(3)
                with mf1:
                    m_rev = st.number_input("Initial Revenue", min_value=0.0, value=1000000.0, step=100000.0)
                    m_net_inc = st.number_input("Initial Net Income", value=150000.0, step=50000.0)
                with mf2:
                    m_tot_assets = st.number_input("Initial Total Assets", min_value=0.0, value=5000000.0, step=500000.0)
                    m_tot_liab = st.number_input("Initial Total Liabilities", min_value=0.0, value=2000000.0, step=200000.0)
                with mf3:
                    m_equity = st.number_input("Shareholders' Equity", min_value=0.0, value=3000000.0, step=300000.0)
                    m_cash = st.number_input("Cash & Cash Equivalents", min_value=0.0, value=500000.0, step=50000.0)

                st.markdown("---")
                st.markdown("#### Initial Complaints Stats")
                mcp1, mcp2 = st.columns(2)
                with mcp1:
                    m_tot_comp = st.number_input("Initial Total Complaints", min_value=0, value=5)
                    m_neg_comp = st.number_input("Negative Sentiment Complaints", min_value=0, value=1)
                with mcp2:
                    m_open_comp = st.number_input("Open Complaints", min_value=0, value=1)
                    m_fraud_comp = st.number_input("Fraud Allegations", min_value=0, value=0)

                create_btn = st.form_submit_button("Register Monitored Entity", type="primary", use_container_width=True)

                if create_btn:
                    if not m_tax_id.strip() or not m_name.strip():
                        st.error("Please fill in both Tax ID and Entity Name.")
                    else:
                        complaint_data = {
                            "total_complaints": m_tot_comp,
                            "negative_count": m_neg_comp,
                            "high_severity_count": 0,
                            "open_count": m_open_comp,
                            "fraud_allegation_count": m_fraud_comp,
                            "growth_rate": 0.0
                        }
                        financial_data = {
                            "revenue": m_rev,
                            "net_income": m_net_inc,
                            "total_assets": m_tot_assets,
                            "total_liabilities": m_tot_liab,
                            "current_assets": m_tot_assets * 0.4,
                            "current_liabilities": m_tot_liab * 0.5,
                            "total_equity": m_equity,
                            "cash_and_equivalents": m_cash
                        }
                        success, new_comp, msg = create_company_manual(
                            db, user, m_tax_id, m_name, m_sector, complaint_data, financial_data
                        )
                        if success:
                            st.success(f"Entity '{new_comp.name}' successfully registered in FRA system!")
                            st.rerun()
                        else:
                            st.error(msg)

        # -------------------------------------------------------------
        # Tab 3: Upload Audit Reports & Document Attachments
        # -------------------------------------------------------------
        with tab_reports:
            st.subheader("Regulatory Audit Reports & Document Upload")
            st.markdown("Upload official audit notes, inspection reports, or compliance documents attached to monitored entities.")

            companies = db.query(Company).order_by(Company.name.asc()).all()
            if companies:
                comp_report_map = {f"{c.name} ({c.tax_id})": c.id for c in companies}
                rep_comp_str = st.selectbox("Select Target Entity for Report Upload", list(comp_report_map.keys()))
                rep_comp_id = comp_report_map[rep_comp_str]

                with st.form("upload_report_form"):
                    rep_title = st.text_input("Report Title / Subject", placeholder="e.g. Q3 On-Site Inspection Summary Report")
                    uploaded_file = st.file_uploader("Choose Audit File (.pdf, .docx, .xlsx, .jpg, .png)", type=["pdf", "docx", "xlsx", "jpg", "png", "txt"])
                    rep_notes = st.text_area("Supervisory Notes & Key Findings", placeholder="Summary of compliance findings and recommendations...")

                    upload_btn = st.form_submit_button("Upload & Attach Report to Entity", type="primary", use_container_width=True)

                    if upload_btn:
                        if not uploaded_file:
                            st.error("Please select a file to upload.")
                        else:
                            success, msg = upload_company_report(
                                db, rep_comp_id, uploaded_file, rep_title, user, rep_notes
                            )
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

                st.markdown("---")
                st.subheader("Attached Regulatory Reports Directory & File Download")
                reports = db.query(CompanyReport).filter(CompanyReport.company_id == rep_comp_id).order_by(CompanyReport.created_at.desc()).all()
                if not reports:
                    st.info("No reports attached to this entity yet.")
                else:
                    for r in reports:
                        file_path = os.path.join(REPORTS_DIR, r.filename)
                        with st.container():
                            rc1, rc2 = st.columns([70, 30])
                            with rc1:
                                st.markdown(f"**{r.title}**<br><span style='color: #64748B; font-size: 0.82rem;'>File: {r.filename} | Format: {r.file_type} | Size: {r.file_size_kb} KB | By: {r.uploaded_by} | Date: {r.created_at.strftime('%Y-%m-%d %H:%M')}</span>", unsafe_allow_html=True)
                                if r.notes:
                                    st.caption(f"Supervisory Notes: {r.notes}")
                            with rc2:
                                if os.path.exists(file_path):
                                    with open(file_path, "rb") as f:
                                        f_bytes = f.read()
                                    st.download_button(
                                        label=f"Download Report ({r.file_type})",
                                        data=f_bytes,
                                        file_name=r.filename,
                                        mime="application/octet-stream",
                                        key=f"dl_admin_rep_{r.id}",
                                        use_container_width=True
                                    )
                                else:
                                    st.caption("File unavailable on disk")
                            st.markdown("<hr style='margin: 0.4rem 0; border: 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # Tab 4: Company Change History & Audit Trail Log
        # -------------------------------------------------------------
        with tab_history:
            st.subheader("System Activity & Company Modification Audit Trail")
            st.markdown("Track all staff modifications, value changes, audit notes, and entity updates across the platform.")

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

                df_hist = pd.DataFrame(hist_data)

                # Search filter
                search_q = st.text_input("Filter History Log (Company Name, User, Field, or Reason)", "")
                if search_q.strip():
                    q = search_q.strip().lower()
                    df_hist = df_hist[
                        df_hist["Company Name"].str.lower().str.contains(q) |
                        df_hist["Modified By"].str.lower().str.contains(q) |
                        df_hist["Field Modified"].str.lower().str.contains(q) |
                        df_hist["Audit Reason / Note"].str.lower().str.contains(q)
                    ]

                st.dataframe(df_hist, use_container_width=True)

        # -------------------------------------------------------------
        # Tab 5: Dynamic Risk Scoring Weight Tuning
        # -------------------------------------------------------------
        with tab_weights:
            st.subheader("Complaints Risk Engine Model Weights")
            st.markdown("Adjust relative weight factors for Complaints Risk Scoring Engine.")

            active_weights = db.query(ScoringWeight).order_by(ScoringWeight.updated_at.desc()).first()
            if active_weights:
                curr_vol, curr_neg, curr_sev = active_weights.vol_w, active_weights.neg_w, active_weights.sev_w
                curr_open, curr_fraud, curr_growth = active_weights.open_w, active_weights.fraud_w, active_weights.growth_w
            else:
                curr_vol = DEFAULT_COMPLAINT_WEIGHTS["vol_w"]
                curr_neg = DEFAULT_COMPLAINT_WEIGHTS["neg_w"]
                curr_sev = DEFAULT_COMPLAINT_WEIGHTS["sev_w"]
                curr_open = DEFAULT_COMPLAINT_WEIGHTS["open_w"]
                curr_fraud = DEFAULT_COMPLAINT_WEIGHTS["fraud_w"]
                curr_growth = DEFAULT_COMPLAINT_WEIGHTS["growth_w"]

            with st.form("weights_tuning_form"):
                w_vol_pct = st.slider("1. Complaints Volume Weight (w_vol)", 0, 50, int(curr_vol * 100), 5)
                w_neg_pct = st.slider("2. Negative Sentiment Ratio Weight (w_neg)", 0, 50, int(curr_neg * 100), 5)
                w_sev_pct = st.slider("3. High Severity Complaints Weight (w_sev)", 0, 50, int(curr_sev * 100), 5)
                w_open_pct = st.slider("4. Open / Unresolved Complaints Weight (w_open)", 0, 50, int(curr_open * 100), 5)
                w_fraud_pct = st.slider("5. Fraud & Financial Misconduct Weight (w_fraud)", 0, 50, int(curr_fraud * 100), 5)
                w_growth_pct = st.slider("6. Quarterly Complaint Growth Surge Weight (w_growth)", 0, 50, int(curr_growth * 100), 5)

                total_pct = w_vol_pct + w_neg_pct + w_sev_pct + w_open_pct + w_fraud_pct + w_growth_pct

                if total_pct == 100:
                    st.success(f"Total Model Weights Sum: {total_pct}% (Perfect 100%)")
                else:
                    st.warning(f"Total Model Weights Sum: {total_pct}% (Weights will be auto-normalized).")

                save_weights_btn = st.form_submit_button("Save & Apply Model Weights Live", type="primary", use_container_width=True)

                if save_weights_btn:
                    user_id = user.get("id")
                    new_weights = ScoringWeight(
                        vol_w=w_vol_pct / 100.0,
                        neg_w=w_neg_pct / 100.0,
                        sev_w=w_sev_pct / 100.0,
                        open_w=w_open_pct / 100.0,
                        fraud_w=w_fraud_pct / 100.0,
                        growth_w=w_growth_pct / 100.0,
                        updated_by_id=user_id,
                        updated_at=datetime.datetime.utcnow()
                    )
                    db.add(new_weights)
                    db.commit()
                    st.success("Risk Scoring Model Weights successfully updated!")
                    st.rerun()

        # -------------------------------------------------------------
        # Tab 6: SMTP Email Configuration
        # -------------------------------------------------------------
        with tab_smtp:
            st.subheader("Automated Regulatory SMTP Email Dispatch Configuration")
            st.markdown("Configure system outgoing SMTP server credentials for automated inspection assignments and manager approval email alerts.")

            smtp_cfg = get_smtp_settings(db)

            with st.form("smtp_config_form"):
                sc1, sc2 = st.columns(2)
                with sc1:
                    smtp_host = st.text_input("SMTP Server Host (e.g. smtp.gmail.com)", value=smtp_cfg.host or "smtp.gmail.com")
                    smtp_user = st.text_input("SMTP Username / Account Email", value=smtp_cfg.username or "", placeholder="e.g. notifications@fra.gov.eg")
                    sender_e = st.text_input("Sender Display Email", value=smtp_cfg.sender_email or "notifications@fra.gov.eg")
                with sc2:
                    smtp_port = st.number_input("SMTP Port (e.g. 587 or 465)", min_value=1, max_value=65535, value=int(smtp_cfg.port or 587))
                    smtp_pass = st.text_input("SMTP Password / App Password", type="password", value=smtp_cfg.password or "", placeholder="••••••••")
                    use_tls = st.checkbox("Enable TLS / SSL Encryption", value=smtp_cfg.use_tls if smtp_cfg.use_tls is not None else True)

                save_smtp_btn = st.form_submit_button("Save SMTP Server Settings", type="primary", use_container_width=True)

                if save_smtp_btn:
                    ok, msg = save_smtp_settings(db, smtp_host, int(smtp_port), smtp_user, smtp_pass, sender_e, use_tls)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        # -------------------------------------------------------------
        # Tab 7: User Management & RBAC Access
        # -------------------------------------------------------------
        with tab_users:
            st.subheader("System User Management & RBAC Roles")

            tab_user_list, tab_delete_user, tab_create_user = st.tabs([
                "Existing Accounts & Roles",
                "Delete User Account",
                "Create New User Account"
            ])

            with tab_user_list:
                users = db.query(User).order_by(User.id.asc()).all()

                # User Search & Filter
                uf1, uf2 = st.columns(2)
                with uf1:
                    u_role_filter = st.selectbox("Filter Users by Role", ["All", "Admin", "Risk Analyst", "Executive", "Inspector"], key="u_role_filt")
                with uf2:
                    u_search_q = st.text_input("Search Username / Email", "", key="u_search_q")

                user_data = []
                for u in users:
                    if u_role_filter != "All" and u.role != u_role_filter:
                        continue
                    if u_search_q.strip():
                        sq = u_search_q.strip().lower()
                        if sq not in u.username.lower() and sq not in u.email.lower():
                            continue

                    user_data.append({
                        "User ID": u.id,
                        "Username": u.username,
                        "Email": u.email,
                        "Assigned Role": u.role,
                        "Active Status": "Active" if u.is_active else "Inactive",
                        "Created At": u.created_at.strftime("%Y-%m-%d %H:%M")
                    })

                st.dataframe(user_data, use_container_width=True)

                st.markdown("---")
                st.write("#### Modify Existing User Profile & Role")
                if users:
                    user_options = {f"{u.username} ({u.email}) — [{u.role}]": u.id for u in users}
                    selected_user_str = st.selectbox("Select User Account to Edit", list(user_options.keys()))
                    selected_user_id = user_options[selected_user_str]
                    target_user = db.query(User).filter(User.id == selected_user_id).first()

                    if target_user:
                        mod_col1, mod_col2 = st.columns(2)
                        with mod_col1:
                            roles_list = ["Admin", "Risk Analyst", "Executive", "Inspector"]
                            idx = roles_list.index(target_user.role) if target_user.role in roles_list else 0
                            new_role = st.selectbox("Select New Assigned Role", roles_list, index=idx)
                        with mod_col2:
                            is_active = st.checkbox("Account Active", value=target_user.is_active)

                        if st.button("Update User Profile", type="primary"):
                            target_user.role = new_role
                            target_user.is_active = is_active
                            db.commit()
                            st.session_state["edit_success_msg"] = f"Successfully updated '{target_user.username}' account! Assigned Role: {new_role}."
                            st.rerun()

            with tab_delete_user:
                st.markdown("#### Permanent User Account Deletion")
                users = db.query(User).order_by(User.id.asc()).all()
                if users:
                    del_u_map = {f"{u.username} ({u.email}) — [{u.role}]": u.id for u in users}
                    target_del_str = st.selectbox("Select User Account to Delete", list(del_u_map.keys()), key="sel_del_u_tab")
                    target_del_id = del_u_map[target_del_str]
                    target_del_u = db.query(User).filter(User.id == target_del_id).first()

                    if target_del_u:
                        st.error(f"⚠️ DANGER ZONE: You are about to permanently delete user account '{target_del_u.username}' ({target_del_u.email}).")
                        confirm_u_del = st.checkbox(f"I confirm I want to PERMANENTLY DELETE user '{target_del_u.username}'", key=f"confirm_u_del_tab_{target_del_u.id}")
                        if st.button("Permanently Delete User Account", type="primary", disabled=not confirm_u_del, key=f"btn_u_del_tab_{target_del_u.id}", use_container_width=True):
                            del_uname = target_del_u.username
                            db.delete(target_del_u)
                            db.add(ActivityLog(username=user.get("username", "Admin"), action=f"Deleted User Account '{del_uname}'", details="Deleted by admin"))
                            db.commit()
                            st.session_state["edit_success_msg"] = f"User account '{del_uname}' was permanently deleted."
                            st.rerun()

            with tab_create_user:
                st.markdown("#### Register & Create New System Account")
                st.info("Create a new staff or regulatory inspector account with full role assignment and encrypted password credentials.")

                with st.form("create_new_user_account_form"):
                    uc1, uc2 = st.columns(2)
                    with uc1:
                        new_u_username = st.text_input("Username", placeholder="e.g. inspector_ahmed")
                        new_u_email = st.text_input("Official Email", placeholder="e.g. ahmed@fra.gov.eg")
                    with uc2:
                        new_u_password = st.text_input("Password", type="password", placeholder="••••••••")
                        new_u_role = st.selectbox("Assigned Role", ["Risk Analyst", "Inspector", "Executive", "Admin"])

                    new_u_active = st.checkbox("Activate Account Immediately", value=True)

                    submit_new_user = st.form_submit_button("Create User Account", type="primary", use_container_width=True)


                    if submit_new_user:
                        if not new_u_username.strip() or not new_u_email.strip() or not new_u_password.strip():
                            st.error("Please fill in Username, Email, and Password.")
                        else:
                            # Check existing
                            exist_user = db.query(User).filter(
                                (User.username == new_u_username.strip()) | (User.email == new_u_email.strip())
                            ).first()
                            if exist_user:
                                st.error("A user account with this username or email already exists.")
                            else:
                                pass_hash = hash_password(new_u_password.strip())
                                created_user = User(
                                    username=new_u_username.strip(),
                                    email=new_u_email.strip(),
                                    hashed_password=pass_hash,
                                    role=new_u_role,
                                    is_active=new_u_active,
                                    created_at=datetime.datetime.utcnow()
                                )
                                db.add(created_user)
                                db.add(ActivityLog(
                                    username=user.get("username", "Admin"),
                                    action=f"Created New User Account '{new_u_username.strip()}'",
                                    details=f"Role: {new_u_role}, Email: {new_u_email.strip()}"
                                ))
                                db.commit()
                                st.success(f"User account '{new_u_username.strip()}' successfully created with role '{new_u_role}'!")
                                st.rerun()

    finally:
        db.close()
