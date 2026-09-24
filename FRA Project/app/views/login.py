import uuid
import datetime
import streamlit as st
from database import SessionLocal
from models import User
from auth import seed_default_users, authenticate_user, hash_password, create_access_token
from sqlalchemy.orm import Session

def start_fresh_user_session(user_obj):
    """
    Purges all previous session states and URL parameters, generates a brand new unique JWT token,
    and initializes a clean, isolated session environment for the newly authenticated user.
    """
    # 1. Clear previous session state and URL query parameters
    st.session_state.clear()
    st.query_params.clear()

    # 2. Generate unique JWT token with session nonce
    session_nonce = str(uuid.uuid4())
    token = create_access_token({
        "sub": user_obj.username,
        "role": user_obj.role,
        "id": user_obj.id,
        "session_nonce": session_nonce
    })

    # 3. Populate fresh session state
    st.session_state["jwt_token"] = token
    st.session_state["user"] = {
        "id": user_obj.id,
        "username": user_obj.username,
        "email": user_obj.email,
        "role": user_obj.role,
        "session_nonce": session_nonce
    }
    st.session_state["session_start_time"] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # 4. Set fresh URL query parameter
    st.query_params["token"] = token
    st.rerun()

def render_login_view():
    """
    Renders the secure login portal with role-based JWT authentication and quick-demo accounts.
    """
    import os
    logo_path = os.path.join("assets", "fra_logo.png")
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)

    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem; margin-top: 0.5rem;">
        <div style="font-size: 2.2rem; font-weight: 800; color: #0F172A; letter-spacing: -0.5px;">
            FRA Risk Intelligence Platform
        </div>
        <div style="font-size: 0.98rem; color: #D97706; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.2rem;">
            Financial Regulatory Authority — Supervisory Early Warning System
        </div>
        <div style="background: #EFF6FF; border: 1px solid #BFDBFE; color: #1E3A8A; font-size: 0.8rem; padding: 0.55rem 1rem; border-radius: 10px; margin-top: 1rem; font-weight: 600; display: inline-block;">
            Notice: This system is currently in experimental demo mode. Minor errors or unexpected behaviors may occur, and ongoing updates will be continuously applied as issues are identified.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-top: 4px solid #D97706; border-radius: 16px; padding: 1.5rem 1.75rem 0.5rem 1.75rem; box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-bottom: -1rem;">
            <div style="color: #0F172A; font-size: 1.3rem; font-weight: 800; letter-spacing: -0.01em;">
                Supervisory Access Login
            </div>
            <div style="color: #64748B; font-size: 0.88rem; margin-top: 0.25rem;">
                Enter your official regulatory credentials to access supervisory modules
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username_or_email = st.text_input("Username or Email", placeholder="e.g. admin@fra.gov.eg")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit_btn = st.form_submit_button("Sign In to Regulatory Portal", use_container_width=True)

            if submit_btn:
                if not username_or_email or not password:
                    st.error("Please enter both username/email and password.")
                else:
                    db: Session = SessionLocal()
                    try:
                        seed_default_users(db)
                        user = authenticate_user(db, username_or_email.strip(), password.strip())
                        if user:
                            start_fresh_user_session(user)
                        else:
                            st.error("Invalid credentials. Please check your username/password.")
                    finally:
                        db.close()

        st.markdown("---")
        st.subheader("Quick Demo Account Login")
        st.info("Select a supervisory role below to auto-authenticate instantly in demo mode:")

        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

        with btn_col1:
            if st.button("Admin", use_container_width=True, key="demo_btn_admin"):
                auto_login_role("Admin")

        with btn_col2:
            if st.button("Risk Analyst", use_container_width=True, key="demo_btn_analyst"):
                auto_login_role("Risk Analyst")

        with btn_col3:
            if st.button("Executive", use_container_width=True, key="demo_btn_executive"):
                auto_login_role("Executive")

        with btn_col4:
            if st.button("Inspector", use_container_width=True, key="demo_btn_inspector"):
                auto_login_role("Inspector")

def auto_login_role(role_name: str):
    """Helper to perform instant auto-login for quick demo mode by role."""
    db: Session = SessionLocal()
    try:
        seed_default_users(db)
        username_map = {
            "Admin": "admin",
            "Risk Analyst": "analyst",
            "Executive": "executive",
            "Inspector": "inspector"
        }
        target_username = username_map.get(role_name, role_name.lower())
        user = db.query(User).filter((User.role == role_name) | (User.username == target_username)).first()
        
        if not user:
            # Emergency fallback creation
            pass_hash = hash_password(f"{role_name}@123")
            user = User(
                username=target_username,
                email=f"{target_username}@fra.gov.eg",
                hashed_password=pass_hash,
                role=role_name,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        start_fresh_user_session(user)
    finally:
        db.close()
