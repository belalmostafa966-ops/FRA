import streamlit as st

# Official FRA Regulatory Supervisory Theme CSS
LIGHT_ADMIN_THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* -------------------------------------------------------------
       1. Clean Shell & Header Customization
       ------------------------------------------------------------- */
    #MainMenu { visibility: hidden !important; display: none !important; }
    footer { visibility: hidden !important; display: none !important; }
    .stDeployButton, [data-testid="stAppDeployButton"] { display: none !important; }
    #stDecoration { display: none !important; }

    [data-testid="stHeader"] {
        background-color: transparent !important;
        z-index: 1000 !important;
    }

    /* Sidebar Collapse Button */
    [data-testid="stSidebarCollapseButton"], 
    [data-testid="collapsedControl"],
    button[aria-label*="sidebar"],
    button[aria-label*="Sidebar"] {
        visibility: visible !important;
        display: inline-flex !important;
        color: #1E3A8A !important;
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }

    /* -------------------------------------------------------------
       2. Global Color Palette & Typography (FRA Official Palette)
       ------------------------------------------------------------- */
    html, body, [class*="css"], .stApp, input, button, select, textarea {
        font-family: 'Plus Jakarta Sans', 'Inter', system-ui, -apple-system, sans-serif !important;
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        -webkit-font-smoothing: antialiased !important;
        font-variant-numeric: lining-nums tabular-nums !important;
        font-feature-settings: 'lnum' 1, 'tnum' 1 !important;
    }

    input[type="number"], .stNumberInput input, .stTextInput input, [data-testid="stMetricValue"] {
        direction: ltr !important;
        font-variant-numeric: lining-nums tabular-nums !important;
        font-feature-settings: 'lnum' 1, 'tnum' 1 !important;
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
    }

    .block-container {
        padding-top: 1.25rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 96% !important;
    }

    /* Typography System */
    h1, h2, h3, h4, h5, h6 {
        color: #0F172A !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
    }

    h1 { font-size: 1.75rem !important; }
    h2 { font-size: 1.35rem !important; }
    h3 { font-size: 1.1rem !important; color: #1E293B !important; }
    
    .stMarkdown p {
        color: #475569 !important;
        font-size: 0.92rem !important;
        line-height: 1.5 !important;
    }

    hr {
        border-color: #E2E8F0 !important;
        margin: 1.5rem 0 !important;
    }

    /* -------------------------------------------------------------
       3. Metric KPI Cards (FRA Navy & Gold Borders)
       ------------------------------------------------------------- */
    div[data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-top: 4px solid #D97706 !important;
        border-radius: 14px !important;
        padding: 1.2rem 1.35rem !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.2s ease-in-out !important;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08) !important;
        border-top-color: #1E3A8A !important;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        color: #64748B !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        margin-bottom: 0.35rem !important;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em !important;
    }

    /* -------------------------------------------------------------
       4. Early Warning Alert Banners
       ------------------------------------------------------------- */
    [data-testid="stAlert"] {
        background-color: #FEF2F2 !important;
        border: 1px solid #FECACA !important;
        border-left: 5px solid #EF4444 !important;
        border-radius: 12px !important;
        color: #991B1B !important;
        padding: 1rem 1.25rem !important;
        box-shadow: 0 2px 6px rgba(239, 68, 68, 0.06) !important;
    }

    /* -------------------------------------------------------------
       5. Clean White Sidebar & FRA Regulatory Navigation
       ------------------------------------------------------------- */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
        box-shadow: 2px 0 15px rgba(0, 0, 0, 0.03) !important;
    }

    div[role="radiogroup"] {
        gap: 0.35rem !important;
    }

    /* Hide standard radio input circle */
    div[role="radiogroup"] input[type="radio"],
    div[role="radiogroup"] label > div:first-child,
    div[role="radiogroup"] label > div[data-testid="stRadioButton"],
    div[role="radiogroup"] [data-baseweb="radio"] > div:first-child {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
    }

    div[role="radiogroup"] label {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        background-color: transparent !important;
        border: none !important;
        border-left: 5px solid transparent !important;
        border-radius: 0 10px 10px 0 !important;
        padding: 0.75rem 1.1rem !important;
        color: #64748B !important;
        font-weight: 600 !important;
        font-size: 0.93rem !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }

    div[role="radiogroup"] label:hover {
        background-color: #FFFBEB !important;
        color: #D97706 !important;
    }

    div[role="radiogroup"] label:has(input:checked) {
        background-color: #FFFBEB !important;
        color: #0F172A !important;
        border-left: 5px solid #D97706 !important;
        font-weight: 800 !important;
    }

    div[role="radiogroup"] label:has(input:checked) p {
        color: #0F172A !important;
        font-weight: 800 !important;
    }

    /* -------------------------------------------------------------
       6. Buttons & Inputs System (Navy & Gold Accent)
       ------------------------------------------------------------- */
    .stButton > button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border: 1px solid #1E3A8A !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        padding: 0.6rem 1.25rem !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.15) !important;
    }

    .stButton > button:hover {
        background-color: #D97706 !important;
        border-color: #B45309 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 15px rgba(217, 119, 6, 0.3) !important;
    }

    .stSelectbox div[data-baseweb="select"], 
    .stMultiSelect div[data-baseweb="select"], 
    .stTextInput input {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        color: #0F172A !important;
        font-weight: 500 !important;
    }

    .stSelectbox div[data-baseweb="select"]:hover, .stTextInput input:focus {
        border-color: #D97706 !important;
    }

    /* Tabs Styling */
    button[data-baseweb="tab"] {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
        border-bottom: 2px solid transparent !important;
        padding: 0.65rem 1.25rem !important;
    }

    button[aria-selected="true"] {
        color: #D97706 !important;
        border-bottom-color: #D97706 !important;
        font-weight: 800 !important;
    }

    /* Data Tables */
    [data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03) !important;
    }

    /* FRA Custom Regulatory Widget Cards */
    .fra-card-navy {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%) !important;
        border-radius: 18px !important;
        padding: 1.5rem 1.75rem !important;
        color: #FFFFFF !important;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.2) !important;
    }

    .fra-card-gold {
        background: linear-gradient(135deg, #78350F 0%, #D97706 100%) !important;
        border-radius: 18px !important;
        padding: 1.5rem 1.75rem !important;
        color: #FFFFFF !important;
        box-shadow: 0 10px 25px rgba(217, 119, 6, 0.2) !important;
    }

    .fra-card-white {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 18px !important;
        padding: 1.5rem !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03) !important;
    }

    .fra-card-slate {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%) !important;
        border-radius: 18px !important;
        padding: 1.5rem 1.75rem !important;
        color: #FFFFFF !important;
        box-shadow: 0 10px 25px rgba(30, 41, 59, 0.25) !important;
    }
</style>
"""

def inject_light_admin_theme():
    """Injects the Official FRA Regulatory Supervisory CSS theme into Streamlit."""
    st.markdown(LIGHT_ADMIN_THEME_CSS, unsafe_allow_html=True)
