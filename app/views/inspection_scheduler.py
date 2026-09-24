import streamlit as st
import pandas as pd
import datetime
import os
from sqlalchemy.orm import Session

from models import Company, InspectionTask, User, RiskScoreHistory, CompanyReport, CompanyHistory, ActivityLog
from utils.security import sanitize_input
from utils.email_service import send_smtp_email, get_smtp_settings

EVIDENCE_DIR = os.path.join("uploads", "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

def render_inspection_scheduler_view(db: Session, user_obj: User):
    """
    Renders the Field Inspection & Regulatory Audit Management Module with strict RBAC:
    - Admin/Risk Analyst: Assign tasks to inspectors, dispatch task forces, review findings & approve reports.
    - Inspector: View assigned tasks, log field findings, upload evidence, and submit to manager.
    """
    if "edit_success_msg" in st.session_state:
        st.success(st.session_state.pop("edit_success_msg"))
        st.toast("Action executed successfully!", icon="✅")

    st.title("Field Inspection & Regulatory Audit Management")
    st.markdown("Algorithmic prioritization, task force dispatch, inspector evidence uploads, manager supervisory review, and SMTP notifications.")

    user_dict = st.session_state.get("user", {})
    username = user_dict.get("username", "Staff")
    role = user_dict.get("role", "Staff")

    # Strict RBAC Tab Navigation
    if role in ["Admin", "Risk Analyst"]:
        tab_scheduler, tab_manager, tab_pipeline = st.tabs([
            "Assign & Dispatch Tasks",
            "Manager Supervisory Review",
            "Task Force Pipeline"
        ])
        tab_inspector = None
    else:  # Inspector
        tab_inspector, tab_pipeline = st.tabs([
            "My Assigned Tasks & Findings",
            "Task Force Pipeline"
        ])
        tab_scheduler = None
        tab_manager = None

    companies = db.query(Company).all()

    # -------------------------------------------------------------
    # MANAGER / ADMIN TAB 1: Assign & Dispatch Inspection Tasks
    # -------------------------------------------------------------
    if tab_scheduler:
        with tab_scheduler:
            st.subheader("Algorithmic Inspection Priority Queue")
            st.caption("Prioritization scores combine Composite Risk Levels, EWS alert triggers, and historical complaint severity.")

            scheduler_data = []
            for comp in companies:
                latest_risk = db.query(RiskScoreHistory).filter(
                    RiskScoreHistory.company_id == comp.id
                ).order_by(RiskScoreHistory.created_at.desc()).first()

                composite_score = latest_risk.composite_score if latest_risk else 50.0
                ews_flag = latest_risk.ews_alert_flag if latest_risk else False

                risk_weights = {"Critical": 40, "High": 30, "Medium": 15, "Low": 5}
                risk_base_score = risk_weights.get(comp.risk_level, 10)
                ews_score = 35 if ews_flag else 0
                total_priority = min(100.0, risk_base_score + ews_score + (composite_score * 0.25))

                if total_priority >= 70:
                    rec_action = "Urgent On-Site Audit"
                    urgency = "Critical"
                elif total_priority >= 45:
                    rec_action = "Comprehensive Routine Audit"
                    urgency = "Medium"
                else:
                    rec_action = "Standard Off-Site Monitoring"
                    urgency = "Low"

                scheduler_data.append({
                    "Tax ID": comp.tax_id,
                    "Company Name": comp.name,
                    "Sector": comp.sector,
                    "Risk Level": comp.risk_level,
                    "Composite Risk Score": f"{composite_score:.1f}",
                    "EWS Alert": "Yes" if ews_flag else "No",
                    "Priority Score": round(total_priority, 1),
                    "Regulatory Recommendation": rec_action,
                    "Urgency Level": urgency,
                    "comp_id": comp.id
                })

            df_sched = pd.DataFrame(scheduler_data)
            if not df_sched.empty:
                df_sched = df_sched.sort_values(by="Priority Score", ascending=False)

            # Filters & Metrics
            f1, f2 = st.columns(2)
            with f1:
                sec_opt = ["All"] + (list(df_sched["Sector"].unique()) if not df_sched.empty else [])
                sec_filter = st.selectbox("Filter Queue by Sector", sec_opt)
            with f2:
                urg_filter = st.selectbox("Filter Queue by Urgency Level", ["All", "Critical", "Medium", "Low"])

            filt_df = df_sched.copy() if not df_sched.empty else pd.DataFrame()
            if not filt_df.empty:
                if sec_filter != "All":
                    filt_df = filt_df[filt_df["Sector"] == sec_filter]
                if urg_filter != "All":
                    filt_df = filt_df[filt_df["Urgency Level"] == urg_filter]

            m1, m2, m3 = st.columns(3)
            m1.metric("Monitored Scope", len(filt_df))
            urgent_count = len(filt_df[filt_df["Urgency Level"] == "Critical"]) if not filt_df.empty else 0
            m2.metric("Critical Priority Queue", urgent_count)
            avg_p = f"{filt_df['Priority Score'].mean():.1f}" if not filt_df.empty else "0"
            m3.metric("Average Priority Score", avg_p)

            st.markdown("---")
            st.subheader("Dispatch Field Inspection Task Force & Assign Lead Inspector")
            st.info("Assign an inspection task to a specific inspector account. An automated email notification will be dispatched to the assigned inspector.")

            with st.form("dispatch_task_form"):
                q1, q2 = st.columns(2)
                with q1:
                    comp_names = [c.name for c in companies]
                    target_comp_name = st.selectbox("Select Target Entity for Inspection", options=comp_names if comp_names else ["None"])
                    task_urgency = st.selectbox("Urgency / Priority Level", ["Critical", "High", "Medium", "Routine"])
                with q2:
                    scheduled_date_val = st.date_input("Scheduled Audit Date", min_value=datetime.date.today())
                    
                    # Fetch inspectors from DB
                    inspectors = db.query(User).filter(User.role.in_(["Inspector", "Risk Analyst", "Admin"])).all()
                    insp_map = {f"{u.username} ({u.email}) — [{u.role}]": u for u in inspectors} if inspectors else {}
                    
                    if insp_map:
                        inspector_choice_str = st.selectbox("Assigned Inspector Account", list(insp_map.keys()))
                        assigned_inspector_user = insp_map[inspector_choice_str]
                    else:
                        st.warning("No inspector accounts found.")
                        assigned_inspector_user = user_obj

                task_title = st.text_input("Task Title", f"On-Site Audit - {target_comp_name}")
                task_directives = st.text_area("Audit Directives & Manager Instructions", "Inspect loan provisions, fraud allegation records, liquidity ratios, and customer complaint logs.")

                dispatch_btn = st.form_submit_button("Dispatch Task to Inspector & Send Email", type="primary", use_container_width=True)

                if dispatch_btn and target_comp_name != "None":
                    target_c = db.query(Company).filter(Company.name == target_comp_name).first()

                    new_task = InspectionTask(
                        company_id=target_c.id,
                        assigned_to_user_id=assigned_inspector_user.id,
                        inspector_username=assigned_inspector_user.username,
                        title=sanitize_input(task_title),
                        urgency=task_urgency,
                        status="Scheduled",
                        scheduled_date=datetime.datetime.combine(scheduled_date_val, datetime.time.min),
                        findings_notes=sanitize_input(task_directives),
                        approval_status="Pending Review",
                        created_at=datetime.datetime.utcnow()
                    )
                    db.add(new_task)
                    db.commit()

                    # SMTP Email to Inspector
                    if assigned_inspector_user.email:
                        email_body = f"""Dear Inspector {assigned_inspector_user.username},

You have been assigned as Lead Inspector for an official supervisory audit task:

Task Title: {task_title}
Target Entity: {target_c.name} (Tax ID: {target_c.tax_id})
Urgency Level: {task_urgency}
Scheduled Audit Date: {scheduled_date_val}

Manager Directives:
{task_directives}

Please log into the FRA Supervisory Portal to review your assigned task, log field findings, and upload evidence documents.

Financial Regulatory Authority (FRA)
Supervisory Inspection Division"""
                        send_smtp_email(assigned_inspector_user.email, f"New Inspection Task Assigned: {target_c.name}", email_body, db)

                    db.add(ActivityLog(
                        username=username,
                        action=f"Dispatched Inspection Task #{new_task.id} to Inspector '{assigned_inspector_user.username}'",
                        details=f"Entity: {target_c.name}, Urgency: {task_urgency}"
                    ))
                    db.commit()

                    st.session_state["edit_success_msg"] = f"Successfully assigned Inspection Task #{new_task.id} to Inspector '{assigned_inspector_user.username}' for '{target_c.name}'!"
                    st.rerun()

    # -------------------------------------------------------------
    # INSPECTOR TAB 1: My Assigned Tasks & Findings Submission
    # -------------------------------------------------------------
    if tab_inspector:
        with tab_inspector:
            st.subheader("Inspector Assigned Tasks & Evidence Submission")
            st.markdown("View tasks assigned to your inspector account, log audit findings, upload evidence files, and submit to your manager for approval.")

            # Filter tasks assigned specifically to this inspector user
            my_tasks = db.query(InspectionTask).filter(
                (InspectionTask.assigned_to_user_id == user_obj.id) | (InspectionTask.inspector_username == username)
            ).order_by(InspectionTask.created_at.desc()).all()

            if not my_tasks:
                st.info("You currently have no assigned inspection tasks.")
            else:
                task_options = {f"Task #{t.id}: {t.title} ({t.company.name if t.company else ''}) — Status: {t.status}": t.id for t in my_tasks}
                sel_task_str = st.selectbox("Select Assigned Task to Work On", list(task_options.keys()))
                sel_task_id = task_options[sel_task_str]

                task_obj = db.query(InspectionTask).filter(InspectionTask.id == sel_task_id).first()

                if task_obj:
                    st.markdown(f"#### Task Details: #{task_obj.id} — {task_obj.title}")
                    st.markdown(f"""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
                        <b>Target Entity:</b> {task_obj.company.name if task_obj.company else ''} (Tax ID: {task_obj.company.tax_id if task_obj.company else ''})<br>
                        <b>Urgency Level:</b> <span style="color: {'#991B1B' if task_obj.urgency=='Critical' else '#D97706'}; font-weight: 800;">{task_obj.urgency}</span> | 
                        <b>Scheduled Date:</b> {task_obj.scheduled_date.strftime('%Y-%m-%d') if task_obj.scheduled_date else 'N/A'}<br>
                        <b>Manager Directives:</b> {task_obj.findings_notes or 'None'}
                    </div>
                    """, unsafe_allow_html=True)

                    with st.form("inspector_submission_form"):
                        st.markdown("##### 1. Lifecycle Status & Risk Rating")
                        ist1, ist2 = st.columns(2)
                        with ist1:
                            status_opts = ["Scheduled", "In Progress", "Completed", "Cancelled"]
                            cur_status_idx = status_opts.index(task_obj.status) if task_obj.status in status_opts else 0
                            ins_new_status = st.selectbox("Task Lifecycle Status", status_opts, index=cur_status_idx)
                        with ist2:
                            risk_opts = ["Low", "Medium", "High", "Critical"]
                            cur_risk = task_obj.company.risk_level if task_obj.company else "Low"
                            cur_risk_idx = risk_opts.index(cur_risk) if cur_risk in risk_opts else 0
                            ins_risk_level = st.selectbox("Evaluated Entity Risk Rating", risk_opts, index=cur_risk_idx)

                        st.markdown("##### 2. Detailed Inspection Findings & Violation Notes")
                        ins_findings = st.text_area("Field Inspection Findings & Evidence Summary", value=task_obj.inspector_notes or "", placeholder="Log details of non-compliance, financial discrepancies, complaint evidence, or statutory violations discovered during on-site audit...")

                        st.markdown("##### 3. Evidence Document Upload (.pdf, .docx, .xlsx, .png, .jpg)")
                        evidence_file = st.file_uploader("Upload Audit Evidence File", type=["pdf", "docx", "xlsx", "png", "jpg"])

                        submit_findings_btn = st.form_submit_button("Submit Findings to Supervisory Manager", type="primary", use_container_width=True)

                        if submit_findings_btn:
                            task_obj.status = ins_new_status
                            task_obj.inspector_notes = sanitize_input(ins_findings)
                            task_obj.approval_status = "Pending Review"

                            if task_obj.company:
                                task_obj.company.risk_level = ins_risk_level

                            # Handle evidence file upload
                            if evidence_file:
                                evidence_fname = f"EVIDENCE_Task_{task_obj.id}_{int(datetime.datetime.utcnow().timestamp())}_{evidence_file.name}"
                                evidence_path = os.path.join(EVIDENCE_DIR, evidence_fname)
                                with open(evidence_path, "wb") as f:
                                    f.write(evidence_file.getbuffer())

                                task_obj.evidence_filename = evidence_fname

                                # Also attach to CompanyReport table
                                db.add(CompanyReport(
                                    company_id=task_obj.company_id,
                                    title=f"Field Evidence: Task #{task_obj.id}",
                                    filename=evidence_fname,
                                    file_type=evidence_file.name.split(".")[-1].upper(),
                                    file_size_kb=round(len(evidence_file.getbuffer()) / 1024.0, 2),
                                    uploaded_by=username,
                                    notes=f"Evidence uploaded by inspector {username} for task: {task_obj.title}",
                                    created_at=datetime.datetime.utcnow()
                                ))

                            # Log Audit History
                            db.add(CompanyHistory(
                                company_id=task_obj.company_id,
                                modified_by=username,
                                modified_role=role,
                                field_name=f"Field Inspection Submission (Task #{task_obj.id})",
                                old_value=task_obj.status,
                                new_value=ins_new_status,
                                audit_note=f"Findings submitted by inspector {username}",
                                created_at=datetime.datetime.utcnow()
                            ))

                            db.commit()

                            # Email notification to Managers/Admins
                            admins = db.query(User).filter(User.role.in_(["Admin", "Executive"])).all()
                            for adm in admins:
                                if adm.email:
                                    email_body = f"""Inspector {username} has submitted inspection findings for Task #{task_obj.id} ({task_obj.company.name}).

Status: {ins_new_status}
Risk Rating: {ins_risk_level}
Findings Summary: {ins_findings[:200]}

Please review and approve in the FRA Supervisory Portal."""
                                    send_smtp_email(adm.email, f"Inspection Findings Submitted: Task #{task_obj.id}", email_body, db)

                            st.session_state["edit_success_msg"] = f"Findings and evidence for Task #{task_obj.id} successfully submitted for Manager Review!"
                            st.rerun()

    # -------------------------------------------------------------
    # MANAGER / ADMIN TAB 2: Manager Review & Supervisory Comments
    # -------------------------------------------------------------
    if tab_manager:
        with tab_manager:
            st.subheader("Supervisory Manager Review & Approval Portal")
            st.markdown("Review inspector submissions, inspect uploaded evidence documents, add supervisory comments, and set approval status.")

            pending_tasks = db.query(InspectionTask).order_by(InspectionTask.created_at.desc()).all()

            if not pending_tasks:
                st.info("No tasks available for review.")
            else:
                rev_options = {f"Task #{t.id}: {t.title} ({t.company.name if t.company else ''}) — Approval: {t.approval_status}": t.id for t in pending_tasks}
                rev_task_str = st.selectbox("Select Task to Review & Approve", list(rev_options.keys()))
                rev_task_id = rev_options[rev_task_str]

                rev_task = db.query(InspectionTask).filter(InspectionTask.id == rev_task_id).first()

                if rev_task:
                    rcol1, rcol2 = st.columns(2)
                    with rcol1:
                        st.write(f"**Target Entity:** {rev_task.company.name if rev_task.company else 'N/A'}")
                        st.write(f"**Lead Inspector:** {rev_task.inspector_username}")
                        st.write(f"**Current Status:** {rev_task.status}")
                    with rcol2:
                        st.write(f"**Inspection Urgency:** {rev_task.urgency}")
                        st.write(f"**Current Approval:** {rev_task.approval_status}")
                        st.write(f"**Evidence Attached:** {rev_task.evidence_filename or 'None'}")

                    st.markdown("---")
                    st.markdown("##### Inspector Findings Note")
                    st.info(rev_task.inspector_notes or "No detailed inspector findings logged yet.")

                    if rev_task.evidence_filename:
                        ev_path = os.path.join(EVIDENCE_DIR, rev_task.evidence_filename)
                        if os.path.exists(ev_path):
                            with open(ev_path, "rb") as f:
                                st.download_button(
                                    label=f"Download Attached Evidence File ({rev_task.evidence_filename})",
                                    data=f.read(),
                                    file_name=rev_task.evidence_filename,
                                    mime="application/octet-stream",
                                    key=f"dl_ev_mgr_{rev_task.id}"
                                )

                    st.markdown("---")
                    with st.form("manager_review_form"):
                        st.markdown("##### Supervisory Manager Action & Directives")
                        m_status_choice = st.selectbox("Set Approval Status", ["Approved", "Requires Follow-Up Action", "Escalated to Enforcement", "Pending Review"], index=["Approved", "Requires Follow-Up Action", "Escalated to Enforcement", "Pending Review"].index(rev_task.approval_status) if rev_task.approval_status in ["Approved", "Requires Follow-Up Action", "Escalated to Enforcement", "Pending Review"] else 0)

                        m_comments = st.text_area("Supervisory Manager Comments & Directives", value=rev_task.manager_comments or "", placeholder="Enter official manager comments, corrective actions required, or enforcement penalties...")

                        manager_submit_btn = st.form_submit_button("Save Supervisory Review & Send Notification", type="primary", use_container_width=True)

                        if manager_submit_btn:
                            rev_task.approval_status = m_status_choice
                            rev_task.manager_comments = sanitize_input(m_comments)

                            db.add(CompanyHistory(
                                company_id=rev_task.company_id,
                                modified_by=username,
                                modified_role=role,
                                field_name=f"Supervisory Manager Review (Task #{rev_task.id})",
                                old_value=rev_task.approval_status,
                                new_value=m_status_choice,
                                audit_note=f"Manager comments: {m_comments[:100]}...",
                                created_at=datetime.datetime.utcnow()
                            ))

                            db.commit()

                            # Email Notification to Inspector
                            inspector_user = db.query(User).filter(User.username == rev_task.inspector_username).first()
                            if inspector_user and inspector_user.email:
                                email_body = f"""Supervisory Manager {username} has reviewed your findings for Task #{rev_task.id} ({rev_task.company.name}).

Approval Status: {m_status_choice}
Manager Comments:
{m_comments}

Please view the task in the FRA Supervisory Portal for details."""
                                send_smtp_email(inspector_user.email, f"Inspection Task #{rev_task.id} Reviewed ({m_status_choice})", email_body, db)

                            st.session_state["edit_success_msg"] = f"Supervisory review saved for Task #{rev_task.id} and email notification dispatched to Inspector '{rev_task.inspector_username}'!"
                            st.rerun()

    # -------------------------------------------------------------
    # ALL ROLES TAB: Active Inspection Pipeline Table
    # -------------------------------------------------------------
    with tab_pipeline:
        st.subheader("Active Inspection Pipeline Directory")

        if role == "Inspector":
            all_tasks = db.query(InspectionTask).filter(
                (InspectionTask.assigned_to_user_id == user_obj.id) | (InspectionTask.inspector_username == username)
            ).order_by(InspectionTask.created_at.desc()).all()
        else:
            all_tasks = db.query(InspectionTask).order_by(InspectionTask.created_at.desc()).all()

        if not all_tasks:
            st.info("No inspection tasks recorded.")
        else:
            t_data = []
            for t in all_tasks:
                t_data.append({
                    "Task ID": t.id,
                    "Entity Name": t.company.name if t.company else "N/A",
                    "Title": t.title,
                    "Inspector": t.inspector_username,
                    "Urgency": t.urgency,
                    "Status": t.status,
                    "Approval Status": t.approval_status,
                    "Scheduled Date": t.scheduled_date.strftime("%Y-%m-%d") if t.scheduled_date else "N/A",
                    "Evidence": "Attached" if t.evidence_filename else "None",
                    "Inspector Notes": t.inspector_notes or "-",
                    "Manager Comments": t.manager_comments or "-"
                })
            st.dataframe(pd.DataFrame(t_data), use_container_width=True)
