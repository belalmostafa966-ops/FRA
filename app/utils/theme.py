import streamlit as st

# World-Class Enterprise Dark Theme CSS (Bloomberg / Datadog / Palantir UI aesthetic)
ENTERPRISE_DARK_THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* -------------------------------------------------------------
       1. Clean Shell & Hide Default Streamlit Branding (Keep Sidebar Toggle)
       ------------------------------------------------------------- */
    #MainMenu { visibility: hidden !important; display: none !important; }
    footer { visibility: hidden !important; display: none !important; }
    .stDeployButton, [data-testid="stAppDeployButton"] { display: none !important; }
    #stDecoration { display: none !important; }

    /* Make Header container transparent to keep sidebar collapse button accessible */
    [data-testid="stHeader"] {
        background-color: transparent !important;
        z-index: 1000 !important;
    }

    /* Sidebar Toggle / Collapse Button Styling */
    [data-testid="stSidebarCollapseButton"], 
    [data-testid="collapsedControl"],
    button[aria-label*="sidebar"],
    button[aria-label*="Sidebar"],
    button[data-testid="baseButton-headerNoPadding"] {
        visibility: visible !important;
        display: inline-flex !important;
        color: #38BDF8 !important;
        background-color: #121824 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stSidebarCollapseButton"]:hover, 
    [data-testid="collapsedControl"]:hover,
    button[aria-label*="sidebar"]:hover {
        background-color: #1E293B !important;
        border-color: #38BDF8 !important;
        color: #7DD3FC !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.2) !important;
    }

    /* -------------------------------------------------------------
       2. Global Color Palette & Typography (Enterprise Dark Theme)
       ------------------------------------------------------------- */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI Emoji', 'Apple Color Emoji', 'Segoe UI Symbol', 'Noto Color Emoji', sans-serif !important;
        background-color: #0B0F17 !important;
        color: #F8FAFC !important;
        -webkit-font-smoothing: antialiased !important;
    }

    /* Container Widescreen Optimization */
    .block-container {
        padding-top: 1.25rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 96% !important;
    }

    /* Typography System */
    h1, h2, h3, h4, h5, h6 {
        color: #F8FAFC !important;
        font-family: 'Plus Jakarta Sans', 'Inter', 'Segoe UI Emoji', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
    }

    h1 {
        font-size: 1.85rem !important;
        margin-bottom: 0.2rem !important;
        background: linear-gradient(180deg, #FFFFFF 0%, #CBD5E1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    h2 { font-size: 1.4rem !important; }
    h3 { font-size: 1.15rem !important; color: #E2E8F0 !important; }
    
    .stMarkdown p {
        color: #94A3B8 !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
    }

    /* Horizontal Divider */
    hr {
        border-color: #1E293B !important;
        margin: 1.5rem 0 !important;
    }

    /* -------------------------------------------------------------
       3. Metric KPI Cards & Status Badges
       ------------------------------------------------------------- */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #121824 0%, #172030 100%) !important;
        border: 1px solid #1E293B !important;
        border-radius: 12px !important;
        padding: 1.2rem 1.35rem !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    div[data-testid="stMetric"]:hover {
        border-color: #38BDF8 !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(56, 189, 248, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        color: #94A3B8 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        margin-bottom: 0.35rem !important;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #F8FAFC !important;
        letter-spacing: -0.02em !important;
    }

    /* Delta Badge Styling */
    div[data-testid="stMetricDelta"] {
        display: inline-flex !important;
        align-items: center !important;
        border-radius: 9999px !important;
        padding: 0.25rem 0.75rem !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        margin-top: 0.4rem !important;
    }

    /* -------------------------------------------------------------
       4. Alert Banners & Early Warning System (EWS)
       ------------------------------------------------------------- */
    [data-testid="stAlert"] {
        background-color: rgba(153, 27, 27, 0.2) !important;
        border: 1px solid rgba(239, 68, 68, 0.35) !important;
        border-left: 5px solid #EF4444 !important;
        border-radius: 12px !important;
        color: #FCA5A5 !important;
        padding: 1.1rem 1.4rem !important;
        box-shadow: 0 4px 20px rgba(239, 68, 68, 0.15) !important;
        backdrop-filter: blur(8px) !important;
    }

    [data-testid="stAlert"] p {
        color: #FCA5A5 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    /* Expander Accordions for Entities */
    [data-testid="stExpander"] {
        background-color: #121824 !important;
        border: 1px solid #1E293B !important;
        border-radius: 10px !important;
        margin-bottom: 0.6rem !important;
        overflow: hidden !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25) !important;
        transition: border-color 0.2s ease !important;
    }

    [data-testid="stExpander"]:hover {
        border-color: #334155 !important;
    }

    [data-testid="stExpander"] summary {
        background-color: #172030 !important;
        color: #F8FAFC !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 0.85rem 1.1rem !important;
        border-bottom: 1px solid #1E293B !important;
    }

    [data-testid="stExpander"] summary:hover {
        color: #38BDF8 !important;
        background-color: #1C2638 !important;
    }

    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 1.1rem !important;
        background-color: #121824 !important;
    }

    /* -------------------------------------------------------------
       5. Sidebar & User Profile Navigation
       ------------------------------------------------------------- */
    [data-testid="stSidebar"] {
        background-color: #080C14 !important;
        border-right: 1px solid #1E293B !important;
    }

    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding-top: 0.75rem !important;
    }

    /* Sidebar Navigation Radio Buttons Custom Pills */
    div[role="radiogroup"] {
        gap: 0.45rem !important;
    }

    /* Hide standard radio circles inside sidebar radio items */
    div[role="radiogroup"] input[type="radio"],
    div[role="radiogroup"] label > div:first-child,
    div[role="radiogroup"] label > div[data-testid="stRadioButton"],
    div[role="radiogroup"] [data-baseweb="radio"] > div:first-child {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    div[role="radiogroup"] label {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        background-color: #0F1622 !important;
        border: 1px solid #1E293B !important;
        border-radius: 9px !important;
        padding: 0.65rem 0.95rem !important;
        color: #94A3B8 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
    }

    div[role="radiogroup"] label:hover {
        background-color: #162032 !important;
        color: #F8FAFC !important;
        border-color: #334155 !important;
    }

    div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(90deg, rgba(56, 189, 248, 0.16) 0%, rgba(14, 165, 233, 0.05) 100%) !important;
        color: #38BDF8 !important;
        border-color: #38BDF8 !important;
        font-weight: 700 !important;
        box-shadow: 0 0 16px rgba(56, 189, 248, 0.12) !important;
    }

    div[role="radiogroup"] label [data-testid="stMarkdownContainer"] p {
        margin: 0 !important;
    }

    /* -------------------------------------------------------------
       6. Forms, Buttons & Inputs
       ------------------------------------------------------------- */
    .stButton > button {
        background: linear-gradient(135deg, #162032 0%, #121824 100%) !important;
        color: #F8FAFC !important;
        border: 1px solid #1E293B !important;
        border-radius: 9px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 1.1rem !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #38BDF8 0%, #0284C7 100%) !important;
        color: #FFFFFF !important;
        border-color: #38BDF8 !important;
        box-shadow: 0 4px 16px rgba(56, 189, 248, 0.35) !important;
    }

    .stSelectbox div[data-baseweb="select"], 
    .stMultiSelect div[data-baseweb="select"], 
    .stTextInput input {
        background-color: #121824 !important;
        border: 1px solid #1E293B !important;
        border-radius: 9px !important;
        color: #F8FAFC !important;
        font-weight: 500 !important;
    }

    .stSelectbox div[data-baseweb="select"]:hover, .stTextInput input:focus {
        border-color: #38BDF8 !important;
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
        color: #38BDF8 !important;
        border-bottom-color: #38BDF8 !important;
        font-weight: 700 !important;
    }

    /* -------------------------------------------------------------
       7. Tables & Data Presentation
       ------------------------------------------------------------- */
    [data-testid="stDataFrame"] {
        border: 1px solid #1E293B !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        background-color: #121824 !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
    }
</style>
"""

def inject_enterprise_theme():
    """Injects the enterprise dark theme CSS stylesheet globally into Streamlit layout."""
    st.markdown(ENTERPRISE_DARK_THEME_CSS, unsafe_allow_html=True)
