import streamlit as st

# Page Configuration - Must be the first Streamlit command
st.set_page_config(
    page_title="FRA Risk Intelligence Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

from database import init_db, SessionLocal
from auth import seed_default_users, decode_access_token
from models import User
from utils.data_seeder import seed_sample_data
from custom_theme import inject_light_admin_theme
from views.login import render_login_view
from views.executive_dashboard import render_executive_dashboard
from views.company_deepdive import render_company_deepdive_view
from views.analyst_hub import render_analyst_hub_view
from views.admin_panel import render_admin_panel_view
from views.inspection_scheduler import render_inspection_scheduler_view
from utils.notifications import render_notification_center_ui

# Inject Clean Light SaaS Admin Theme
inject_light_admin_theme()

def initialize_app():
    """Initializes DB schema and seeds sample dataset if required."""
    init_db()
    db = SessionLocal()
    try:
        seed_default_users(db)
        seed_sample_data(db)
    finally:
        db.close()

def main():
    initialize_app()

    # -------------------------------------------------------------
    # Session Persistence Restoration across F5 Browser Reloads
    # -------------------------------------------------------------
    token = None
    if "token" in st.query_params:
        raw_token = st.query_params["token"]
        token = raw_token[0] if isinstance(raw_token, list) else str(raw_token)

    if ("user" not in st.session_state or st.session_state["user"] is None) and token:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            db = SessionLocal()
            try:
                user_obj = db.query(User).filter(User.username == payload["sub"]).first()
                if user_obj and user_obj.is_active:
                    st.session_state["user"] = {
                        "id": user_obj.id,
                        "username": user_obj.username,
                        "email": user_obj.email,
                        "role": user_obj.role
                    }
                    st.session_state["jwt_token"] = token
            finally:
                db.close()

    # Session State Authentication Guard
    if "user" not in st.session_state or st.session_state["user"] is None:
        render_login_view()
        return

    # Keep URL Token query_param synced for session persistence
    if "jwt_token" in st.session_state and st.session_state["jwt_token"]:
        st.query_params["token"] = st.session_state["jwt_token"]

    user = st.session_state["user"]
    role = user["role"]

    # -------------------------------------------------------------
    # Clean Light Sidebar Navigation & User Profile Card
    # -------------------------------------------------------------
    with st.sidebar:
        import os
        logo_path = os.path.join("assets", "fra_logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        
        st.markdown("""
        <div style="padding: 0.2rem 0.2rem 0.8rem 0.2rem; margin-bottom: 0.8rem; border-bottom: 1px solid #E2E8F0; text-align: center;">
            <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em;">
                الهيئة العامة للرقابة المالية
            </div>
            <div style="font-size: 0.72rem; color: #D97706; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.1rem;">
                Financial Regulatory Authority
            </div>
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; color: #92400E; font-size: 0.72rem; padding: 0.4rem 0.6rem; border-radius: 8px; margin-top: 0.6rem; font-weight: 600; text-align: left; line-height: 1.3;">
                Notice: This system is currently in experimental demo mode. Minor errors may occur and will be continuously addressed.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background: #FFFBEB; border-radius: 12px; padding: 0.75rem 0.9rem; margin-bottom: 1rem; border: 1px solid #FEF3C7; display: flex; align-items: center; gap: 0.75rem;">
            <div style="background: #0F172A; color: #D97706; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 800;">
                {user['username'][:2].upper()}
            </div>
            <div>
                <div style="font-size: 0.68rem; color: #D97706; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">SUPERVISORY OFFICER</div>
                <div style="font-weight: 800; color: #0F172A; font-size: 0.92rem;">{user['username']}</div>
                <span style="display: inline-block; background: #0F172A; color: #FFFFFF; border-radius: 9999px; padding: 0.08rem 0.55rem; font-size: 0.68rem; font-weight: 700;">{role}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Role-Based Access Control (RBAC) Menu Options
        available_views = []

        if role == "Admin":
            available_views = [
                "Executive Oversight",
                "Regulated Entities",
                "Risk Engine & EWS",
                "Inspection Task Force",
                "Admin Controls"
            ]
        elif role == "Risk Analyst":
            available_views = [
                "Executive Oversight",
                "Regulated Entities",
                "Risk Engine & EWS",
                "Inspection Task Force"
            ]
        elif role == "Inspector":
            available_views = [
                "Inspection Task Force",
                "Regulated Entities",
                "Executive Oversight"
            ]
        else:  # Executive
            available_views = [
                "Executive Oversight",
                "Regulated Entities"
            ]

        # View Selector
        selected_view = st.radio("Go to Section", available_views, key="main_navigation", label_visibility="collapsed")

        st.markdown("---")
        if st.button("Logout", key="logout_btn", use_container_width=True):
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()

    # -------------------------------------------------------------
    # View Router
    # -------------------------------------------------------------
    if selected_view in ["Executive Oversight", "Dashboard", "Executive Dashboard"]:
        render_executive_dashboard()
    elif selected_view in ["Regulated Entities", "Company Risk Deep-Dive"]:
        render_company_deepdive_view()
    elif selected_view in ["Risk Engine & EWS", "Risk Analytics & EWS", "Risk Analyst Hub"] and role in ["Admin", "Risk Analyst"]:
        render_analyst_hub_view()
    elif selected_view in ["Inspection Task Force", "Inspection Tasks"] and role in ["Admin", "Risk Analyst", "Inspector"]:
        db = SessionLocal()
        try:
            user_obj = db.query(User).filter(User.id == user["id"]).first()
            render_inspection_scheduler_view(db, user_obj)
        finally:
            db.close()
    elif selected_view in ["Admin Controls", "Admin Control Panel"] and role == "Admin":
        render_admin_panel_view()
    else:
        st.error("Unauthorized access to this module.")

if __name__ == "__main__":
    main()
