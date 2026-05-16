"""
Financial Manager App - Main Entry Point
=========================================
A comprehensive personal finance management app built with Streamlit.
Run with: streamlit run app.py
"""

from modules.reports import render_reports
from modules.forecast import render_forecast
from modules.roadmap import render_roadmap
from modules.net_worth import render_net_worth
from modules.database import init_db
import streamlit as st

# ── Page config (must be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="FinanceIQ – Personal Finance Manager",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Local module imports ─────────────────────────────────────────────────────

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Dark sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
    border-right: 1px solid #2a2a4a;
}
[data-testid="stSidebar"] * { color: #e8e8f0 !important; }
[data-testid="stSidebar"] .stRadio label { color: #b0b0cc !important; font-size: 0.95rem; }
[data-testid="stSidebar"] hr { border-color: #2a2a4a !important; }

/* Main background */
.main { background: #f7f7fc; }
.block-container { padding-top: 2rem; max-width: 1200px; }

/* Headings */
h1, h2, h3 { font-family: 'Syne', sans-serif !important; }
h1 { font-weight: 800; font-size: 2.2rem; color: #0f0f1a; }
h2 { font-weight: 700; color: #1a1a2e; }
h3 { font-weight: 600; color: #2a2a4a; }

/* Metric cards */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e8e8f0;
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 2px 12px rgba(15,15,26,0.06);
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6b6b8a;
    font-weight: 500;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.8rem;
    color: #0f0f1a;
}

/* Buttons */
.stButton > button {
    background: #0f0f1a;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.5rem;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 0.04em;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: #2a2a6e;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(15,15,26,0.25);
}

/* Inputs */
.stNumberInput input, .stTextInput input, .stSelectbox select {
    border-radius: 10px !important;
    border: 1.5px solid #e0e0f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stNumberInput input:focus, .stTextInput input:focus {
    border-color: #4a4af0 !important;
    box-shadow: 0 0 0 3px rgba(74,74,240,0.1) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: white;
    border-radius: 12px;
    border: 1px solid #e8e8f0;
    padding: 0.3rem;
    gap: 0.2rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    font-size: 0.9rem;
    color: #6b6b8a;
}
.stTabs [aria-selected="true"] {
    background: #0f0f1a !important;
    color: white !important;
}

/* Section card wrapper */
.section-card {
    background: white;
    border-radius: 20px;
    padding: 2rem;
    border: 1px solid #e8e8f0;
    box-shadow: 0 2px 16px rgba(15,15,26,0.05);
    margin-bottom: 1.5rem;
}

/* Sidebar logo area */
.sidebar-logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.6rem;
    color: white !important;
    letter-spacing: -0.02em;
    padding: 1rem 0 0.5rem 0;
}
.sidebar-tagline {
    font-size: 0.78rem;
    color: #8080aa !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 2rem;
}

/* Success / info banners */
.stSuccess, .stInfo { border-radius: 12px; }

/* Expanders */
.streamlit-expanderHeader {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Initialise DB ────────────────────────────────────────────────────────────
init_db()

# ── Sidebar navigation ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">💰 FinanceIQ</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">Personal Finance Manager</div>',
                unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio(
        "Navigation",
        options=[
            "🏦  Net Worth Calculator",
            "🗺️  Financial Roadmap",
            "📈  Forecast & Projections",
            "📊  Reports & Insights",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        "<small style='color:#1D1D36'>© 2026 FinanceIQ. All rights reserved </small>"
        "<small style='color:#1D1D36'>Contributor:  </small>"
        "<small style='color:#1D1D36'><b>Yashraj Tarte</b></small>",
        unsafe_allow_html=True,
    )

# ── Page routing ─────────────────────────────────────────────────────────────
if page.startswith("🏦"):
    render_net_worth()
elif page.startswith("🗺️"):
    render_roadmap()
elif page.startswith("📈"):
    render_forecast()
elif page.startswith("📊"):
    render_reports()
