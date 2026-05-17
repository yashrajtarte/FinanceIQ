"""
Financial Manager App - Main Entry Point
Run with: streamlit run app.py
"""

from modules.reports import render_reports
from modules.forecast import render_forecast
from modules.roadmap import render_roadmap
from modules.net_worth import render_net_worth
from modules.database import init_db
import streamlit as st

st.set_page_config(
    page_title="FinanceIQ – Personal Finance Manager",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
    border-right: 1px solid #2a2a4a;
}
[data-testid="stSidebar"] * { color: #e8e8f0 !important; }
[data-testid="stSidebar"] .stRadio label { color: #b0b0cc !important; font-size: 0.95rem; }
[data-testid="stSidebar"] hr { border-color: #2a2a4a !important; }

/* ── Main area ── */
.block-container { padding-top: 2rem; max-width: 1200px; }
h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 500;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1.8rem;
}

/* ── Inputs ── */
.stNumberInput input, .stTextInput input {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0e0e20 !important;
    border-radius: 14px !important;
    border: 1.5px solid #252545 !important;
    padding: 0.3rem !important;
    gap: 0.2rem !important;
    box-shadow: inset 0 1px 4px rgba(0,0,0,0.5) !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    color: #55558a !important;
    background: transparent !important;
    border: none !important;
    padding: 0.55rem 1.6rem !important;
    transition: all 0.18s ease !important;
    letter-spacing: 0.02em !important;
    white-space: nowrap !important;
}
.stTabs [data-baseweb="tab"]:hover {
    background: #1a1a38 !important;
    color: #c0c0ff !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #4338ca 0%, #7c3aed 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 2px 14px rgba(99,74,237,0.55) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"]    { display: none !important; }
.stTabs [data-baseweb="tab-panel"]     { padding-top: 1.4rem !important; }

/* ── Buttons — purple gradient default ── */
.stButton > button {
    background: linear-gradient(135deg, #4338ca, #7c3aed) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.5rem !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.04em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 10px rgba(99,74,237,0.3) !important;
    white-space: nowrap !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #3730a3, #6d28d9) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 18px rgba(99,74,237,0.5) !important;
}

/* ── Save button — 1st child in horizontal block → green ── */
div[data-testid="stHorizontalBlock"] div:nth-child(1) .stButton > button {
    background: linear-gradient(135deg, #16a34a, #15803d) !important;
    box-shadow: 0 2px 10px rgba(22,163,74,0.35) !important;
    width: 100% !important;
    padding: 0.55rem 0.8rem !important;
}
div[data-testid="stHorizontalBlock"] div:nth-child(1) .stButton > button:hover {
    background: linear-gradient(135deg, #15803d, #166534) !important;
    box-shadow: 0 4px 16px rgba(22,163,74,0.5) !important;
}

/* ── Cancel button — 2nd child in horizontal block → red outline ── */
div[data-testid="stHorizontalBlock"] div:nth-child(2) .stButton > button {
    background: transparent !important;
    color: #f87171 !important;
    border: 1.5px solid #ef4444 !important;
    box-shadow: none !important;
    width: 100% !important;
    padding: 0.55rem 0.8rem !important;
}
div[data-testid="stHorizontalBlock"] div:nth-child(2) .stButton > button:hover {
    background: rgba(239,68,68,0.12) !important;
    border-color: #f87171 !important;
}

/* ── Download buttons ── */
.stDownloadButton > button {
    background: #13132a !important;
    color: #a78bfa !important;
    border: 1.5px solid #2a2a50 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.18s ease !important;
}
.stDownloadButton > button:hover {
    background: #1e1e40 !important;
    border-color: #7c3aed !important;
    color: #c4b5fd !important;
    box-shadow: 0 2px 12px rgba(124,58,237,0.3) !important;
}

/* ── Sidebar logo / tagline ── */
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

/* ── Expanders ── */
.streamlit-expanderHeader {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Init DB ──────────────────────────────────────────────────────────────────
init_db()

# ── Sidebar ──────────────────────────────────────────────────────────────────
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

    # Contributor card
    st.markdown(
        "<style>"
        ".contrib-wrap{background:linear-gradient(135deg,#1a1a3e,#2a1a4e);"
        "border:1px solid #3a2a6e;border-radius:14px;padding:0.85rem 1rem 0.75rem 1rem;"
        "margin-bottom:0.6rem;}"
        ".contrib-built{font-size:0.6rem;text-transform:uppercase;letter-spacing:0.13em;"
        "color:#4a4a7a;font-weight:600;margin:0 0 0.7rem 0;display:block;}"
        ".contrib-label{font-size:0.58rem;text-transform:uppercase;letter-spacing:0.18em;"
        "color:#7c5cbf;font-weight:700;margin:0 0 0.3rem 0;display:block;}"
        ".contrib-name{font-size:1.12rem;font-weight:800;color:#a78bfa;"
        "margin:0 0 0.15rem 0;display:block;font-family:sans-serif;}"
        ".contrib-role{font-size:0.67rem;color:#6a5a9a;letter-spacing:0.07em;display:block;}"
        ".contrib-copy{font-size:0.58rem;color:#3a3a6a;text-align:center;"
        "letter-spacing:0.04em;margin-top:0.5rem;display:block;}"
        "</style>"
        "<span class='contrib-built'>Built with Streamlit · SQLite · Scikit-learn</span>"
        "<div class='contrib-wrap'>"
        "<span class='contrib-label'>✦ Contributor</span>"
        "<span class='contrib-name'>Yashraj Tarte</span>"
        "<span class='contrib-role'>Developer &amp; Designer</span>"
        "</div>"
        "<span class='contrib-copy'>© 2026 FinanceIQ · All rights reserved</span>",
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
