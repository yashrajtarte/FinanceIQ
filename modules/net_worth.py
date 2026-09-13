"""
modules/net_worth.py
======================
Net Worth Calculator page — redesigned charts section.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from modules.animations import page_enter

from modules.database import (
    add_asset, get_assets, delete_asset, update_asset,
    add_liability, get_liabilities, delete_liability, update_liability,
    save_snapshot, get_next_snapshot_number,
)

ASSET_CATEGORIES = ["Cash", "Investments", "Property", "Other"]
LIABILITY_CATEGORIES = ["Loan", "Credit Card", "Mortgage", "Other"]

EDIT_BTN_CSS = """
<style>
div[data-testid="stHorizontalBlock"] div:nth-child(1) .stButton > button {
    background: #16a34a !important; color: #ffffff !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 700 !important; white-space: nowrap !important;
    width: 100% !important; padding: 0.5rem 0.8rem !important;
}
div[data-testid="stHorizontalBlock"] div:nth-child(1) .stButton > button:hover {
    background: #15803d !important; box-shadow: 0 3px 12px rgba(22,163,74,0.4) !important;
}
div[data-testid="stHorizontalBlock"] div:nth-child(2) .stButton > button {
    background: transparent !important; color: #ef4444 !important;
    border: 1.5px solid #ef4444 !important; border-radius: 8px !important;
    font-weight: 700 !important; white-space: nowrap !important;
    width: 100% !important; padding: 0.5rem 0.8rem !important;
}
div[data-testid="stHorizontalBlock"] div:nth-child(2) .stButton > button:hover {
    background: rgba(239,68,68,0.1) !important;
}
</style>
"""

COL_HEADER_STYLE = (
    "color:#6060a0;font-weight:700;text-transform:uppercase;"
    "letter-spacing:0.07em;font-size:0.7rem;"
)

CHART_BG = "rgba(0,0,0,0)"
CHART_FONT = dict(family="DM Sans, sans-serif", color="#c0c0d0")

# Vibrant palette for pie/donut
ASSET_COLORS = [
    "#6366f1", "#8b5cf6", "#a78bfa", "#38bdf8", "#34d399",
    "#fbbf24", "#f472b6", "#fb923c", "#4ade80", "#60a5fa",
]


def fmt_currency(value: float) -> str:
    if abs(value) >= 1_00_00_000:
        return f"₹{value/1_00_00_000:.2f} Cr"
    elif abs(value) >= 1_00_000:
        return f"₹{value/1_00_000:.2f} L"
    return f"₹{value:,.0f}" if value >= 0 else f"-₹{abs(value):,.0f}"


def _name_cell(name: str) -> str:
    safe = name.replace("'", "&#39;")
    return (f"<div style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
            f"font-weight:600;padding-top:6px;' title='{safe}'>{name}</div>")


def _muted_cell(text: str) -> str:
    return f"<div style='padding-top:6px;color:#8080aa;font-size:0.88rem;'>{text}</div>"


def _value_cell(text: str) -> str:
    return f"<div style='padding-top:6px;font-weight:600;'>{text}</div>"


def _col_headers():
    h1, h2, h3, _, _ = st.columns([3, 2, 2, 0.7, 0.7])
    for h, label in [(h1, "Name"), (h2, "Category"), (h3, "Amount")]:
        h.markdown(
            f"<small style='{COL_HEADER_STYLE}'>{label}</small>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:0.25rem 0 0.5rem 0;border-color:#2a2a4a;'>",
                unsafe_allow_html=True)


def _asset_rows(assets_df: pd.DataFrame):
    for _, row in assets_df.iterrows():
        rid = int(row["id"])
        edit_key = f"edit_asset_{rid}"
        if edit_key not in st.session_state:
            st.session_state[edit_key] = False

        if st.session_state[edit_key]:
            with st.container():
                st.markdown(f"**✏️ Editing:** {row['name']}")
                ec1, ec2, ec3 = st.columns([2, 2, 2])
                new_name = ec1.text_input(
                    "Name", value=row["name"], key=f"ea_name_{rid}")
                new_cat = ec2.selectbox("Category", ASSET_CATEGORIES,
                                        index=ASSET_CATEGORIES.index(
                                            row["category"]) if row["category"] in ASSET_CATEGORIES else 0,
                                        key=f"ea_cat_{rid}")
                new_amt = ec3.number_input("Amount (₹)", value=float(row["amount"]),
                                           min_value=0.0, step=1000.0, key=f"ea_amt_{rid}")
                st.markdown(EDIT_BTN_CSS, unsafe_allow_html=True)
                bc1, bc2, _ = st.columns([1.2, 1.2, 3])
                with bc1:
                    if st.button("💾  Save", key=f"save_a_{rid}", use_container_width=True):
                        update_asset(rid, new_cat, new_name.strip(), new_amt)
                        st.session_state[edit_key] = False
                        st.success(f"✅ Updated: {new_name}")
                        st.rerun()
                with bc2:
                    if st.button("✖  Cancel", key=f"cancel_a_{rid}", use_container_width=True):
                        st.session_state[edit_key] = False
                        st.rerun()
            st.markdown(
                "<hr style='margin:0.3rem 0;border-color:#1a1a30;'>", unsafe_allow_html=True)
        else:
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 0.7, 0.7])
            c1.markdown(_name_cell(row["name"]),
                        unsafe_allow_html=True)
            c2.markdown(_muted_cell(row["category"]),
                        unsafe_allow_html=True)
            c3.markdown(_value_cell(fmt_currency(
                row["amount"])), unsafe_allow_html=True)
            if c4.button("✏️", key=f"edit_btn_a_{rid}", help="Edit"):
                st.session_state[edit_key] = True
                st.rerun()
            if c5.button("🗑️", key=f"del_a_{rid}", help="Delete"):
                delete_asset(rid)
                st.rerun()
            st.markdown(
                "<hr style='margin:0.15rem 0;border-color:#1a1a30;'>", unsafe_allow_html=True)


def _liability_rows(liabilities_df: pd.DataFrame):
    for _, row in liabilities_df.iterrows():
        rid = int(row["id"])
        edit_key = f"edit_liability_{rid}"
        if edit_key not in st.session_state:
            st.session_state[edit_key] = False

        if st.session_state[edit_key]:
            with st.container():
                st.markdown(f"**✏️ Editing:** {row['name']}")
                ec1, ec2, ec3 = st.columns([2, 2, 2])
                new_name = ec1.text_input(
                    "Name", value=row["name"], key=f"el_name_{rid}")
                new_cat = ec2.selectbox("Category", LIABILITY_CATEGORIES,
                                        index=LIABILITY_CATEGORIES.index(
                                            row["category"]) if row["category"] in LIABILITY_CATEGORIES else 0,
                                        key=f"el_cat_{rid}")
                new_amt = ec3.number_input("Amount (₹)", value=float(row["amount"]),
                                           min_value=0.0, step=1000.0, key=f"el_amt_{rid}")
                st.markdown(EDIT_BTN_CSS, unsafe_allow_html=True)
                bc1, bc2, _ = st.columns([1.2, 1.2, 3])
                with bc1:
                    if st.button("💾  Save", key=f"save_l_{rid}", use_container_width=True):
                        update_liability(
                            rid, new_cat, new_name.strip(), new_amt)
                        st.session_state[edit_key] = False
                        st.success(f"✅ Updated: {new_name}")
                        st.rerun()
                with bc2:
                    if st.button("✖  Cancel", key=f"cancel_l_{rid}", use_container_width=True):
                        st.session_state[edit_key] = False
                        st.rerun()
            st.markdown(
                "<hr style='margin:0.3rem 0;border-color:#1a1a30;'>", unsafe_allow_html=True)
        else:
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 0.7, 0.7])
            c1.markdown(_name_cell(row["name"]),
                        unsafe_allow_html=True)
            c2.markdown(_muted_cell(row["category"]),
                        unsafe_allow_html=True)
            c3.markdown(_value_cell(fmt_currency(
                row["amount"])), unsafe_allow_html=True)
            if c4.button("✏️", key=f"edit_btn_l_{rid}", help="Edit"):
                st.session_state[edit_key] = True
                st.rerun()
            if c5.button("🗑️", key=f"del_l_{rid}", help="Delete"):
                delete_liability(rid)
                st.rerun()
            st.markdown(
                "<hr style='margin:0.15rem 0;border-color:#1a1a30;'>", unsafe_allow_html=True)


# ── REDESIGNED CHARTS ────────────────────────────────────────────────────────

def _render_charts(assets_df, liabilities_df, total_assets, total_liabilities, net_worth):

    # ── 1. Mini stat pills ────────────────────────────────────────────────
    debt_ratio = (total_liabilities / total_assets *
                  100) if total_assets > 0 else 0
    invest_amt = assets_df[assets_df["category"] == "Investments"]["amount"].sum(
    ) if not assets_df.empty else 0
    invest_pct = (invest_amt / total_assets * 100) if total_assets > 0 else 0
    num_assets = len(assets_df)

    p1, p2, p3 = st.columns(3)
    for col, label, value, color in [
        (p1, "Debt Ratio",     f"{debt_ratio:.1f}%",
         "#f87171" if debt_ratio > 40 else "#34d399"),
        (p2, "In Investments", f"{invest_pct:.1f}%",   "#a78bfa"),
        (p3, "Asset Items",    str(num_assets),         "#38bdf8"),
    ]:
        col.markdown(
            f"<div style='background:#13132a;border:1px solid #2a2a4a;border-radius:12px;"
            f"padding:0.7rem 1rem;text-align:center;'>"
            f"<div style='font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;"
            f"color:#6060a0;font-weight:700;margin-bottom:0.25rem;'>{label}</div>"
            f"<div style='font-size:1.4rem;font-weight:800;color:{color};font-family:Syne,sans-serif;'>"
            f"{value}</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin:0.8rem 0;'></div>", unsafe_allow_html=True)

    # ── 2a. Donut chart — standalone full width ──────────────────────────
    if not assets_df.empty:
        df_sorted = assets_df.sort_values(
            "amount", ascending=False).reset_index(drop=True)
        n = len(df_sorted)

        st.markdown("#### 🎨 Asset Breakdown")

        # ── Donut ──────────────────────────────────────────────────────────
        fig_donut = go.Figure(go.Pie(
            labels=df_sorted["name"],
            values=df_sorted["amount"],
            hole=0.58,
            marker=dict(
                colors=ASSET_COLORS[:n],
                line=dict(color="#0e0e20", width=2),
            ),
            textinfo="label+percent",
            textposition="outside",
            textfont=dict(size=11, color="#c0c0d0"),
            hovertemplate="<b>%{label}</b><br>₹%{value:,.0f} (%{percent})<extra></extra>",
            showlegend=False,
            pull=[0.03] * n,
        ))
        fig_donut.add_annotation(
            text=f"<b>{fmt_currency(total_assets)}</b><br><span>Total</span>",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=14, color="#e0e0ff", family="Syne,sans-serif"),
            align="center",
        )
        fig_donut.update_layout(
            height=max(360, 30 * n + 200),
            margin=dict(t=30, b=30, l=60, r=60),
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            font=CHART_FONT,
        )
        st.plotly_chart(fig_donut, use_container_width=True)

        # ── Ranked horizontal bars ─────────────────────────────────────────
        st.markdown("#### 📊 Assets Ranked")
        max_val = df_sorted["amount"].max()
        bar_height = max(40, 45 * n)   # ~45px per bar row

        fig_bars = go.Figure(go.Bar(
            y=df_sorted["name"],
            x=df_sorted["amount"],
            orientation="h",
            marker=dict(color=ASSET_COLORS[:n], cornerradius=6),
            text=[fmt_currency(v) for v in df_sorted["amount"]],
            textposition="outside",
            textfont=dict(size=11, color="#a0a0cc"),
            hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>",
        ))
        fig_bars.update_layout(
            height=bar_height,
            margin=dict(t=5, b=5, l=10, r=90),
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            font=CHART_FONT,
            xaxis=dict(
                showgrid=False, showticklabels=False,
                zeroline=False, range=[0, max_val * 1.45],
            ),
            yaxis=dict(
                showgrid=False,
                tickfont=dict(size=11, color="#c0c0d0"),
                autorange="reversed",
                tickmode="array",
                tickvals=list(df_sorted["name"]),
                ticktext=[
                    n if len(n) <= 18 else n[:16] + "…"
                    for n in df_sorted["name"]
                ],
            ),
            showlegend=False,
        )
        st.plotly_chart(fig_bars, use_container_width=True)

    # ── 3. Gauge — net worth health ──────────────────────────────────────
    st.markdown("#### ⚡ Financial Position")

    fig_gauge = go.Figure()

    # Background bar (total assets = 100%)
    fig_gauge.add_trace(go.Bar(
        x=["Assets", "Liabilities", "Net Worth"],
        y=[total_assets, total_liabilities, max(net_worth, 0)],
        marker=dict(
            color=["#6366f1", "#f43f5e", "#10b981"],
            cornerradius=8,
        ),
        text=[fmt_currency(total_assets),
              fmt_currency(total_liabilities),
              fmt_currency(net_worth)],
        textposition="outside",
        textfont=dict(size=12, color="#c0c0d0"),
        hovertemplate="%{x}: ₹%{y:,.0f}<extra></extra>",
        width=0.5,
    ))

    fig_gauge.update_layout(
        height=260,
        margin=dict(t=30, b=10, l=10, r=10),
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=CHART_FONT,
        yaxis=dict(
            showgrid=True, gridcolor="#1e1e38",
            tickformat=",.0f", tickprefix="₹",
            zeroline=False, tickfont=dict(color="#6060a0", size=10),
        ),
        xaxis=dict(tickfont=dict(size=12, color="#c0c0d0")),
        showlegend=False,
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    # ── 4. Category treemap ──────────────────────────────────────────────
    if not assets_df.empty:
        cat_group = assets_df.groupby("category")["amount"].sum().reset_index()

        st.markdown("#### 🗂️ Category Breakdown")

        fig_tree = go.Figure(go.Treemap(
            labels=cat_group["category"],
            parents=[""] * len(cat_group),
            values=cat_group["amount"],
            marker=dict(
                colors=["#6366f1", "#8b5cf6", "#38bdf8",
                        "#34d399"][:len(cat_group)],
                cornerradius=8,
                line=dict(width=2, color="#0e0e20"),
            ),
            texttemplate="<b>%{label}</b><br>%{value:,.0f}",
            hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{percentRoot:.1%} of total<extra></extra>",
            textfont=dict(size=13, color="#ffffff", family="Syne,sans-serif"),
            tiling=dict(packing="squarify", pad=4),
        ))

        fig_tree.update_layout(
            height=200,
            margin=dict(t=5, b=5, l=5, r=5),
            paper_bgcolor=CHART_BG,
            font=CHART_FONT,
        )
        st.plotly_chart(fig_tree, use_container_width=True)

    # ── 5. Liabilities breakdown (if any) ───────────────────────────────
    if not liabilities_df.empty:
        st.markdown("#### 🔴 Liabilities Breakdown")
        liab_sorted = liabilities_df.sort_values("amount", ascending=True)
        fig_liab = go.Figure(go.Bar(
            x=liab_sorted["amount"],
            y=liab_sorted["name"],
            orientation="h",
            marker=dict(
                color="#f43f5e",
                opacity=0.85,
                cornerradius=6,
            ),
            text=[fmt_currency(v) for v in liab_sorted["amount"]],
            textposition="outside",
            textfont=dict(size=10, color="#fca5a5"),
            hovertemplate="<b>%{y}</b><br>₹%{x:,.0f}<extra></extra>",
        ))
        fig_liab.update_layout(
            height=max(120, 45 * len(liab_sorted)),
            margin=dict(t=5, b=5, l=5, r=80),
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            font=CHART_FONT,
            xaxis=dict(showgrid=False, showticklabels=False,
                       range=[0, liab_sorted["amount"].max() * 1.35]),
            yaxis=dict(showgrid=False, tickfont=dict(
                size=11, color="#fca5a5")),
            showlegend=False,
        )
        st.plotly_chart(fig_liab, use_container_width=True)


# ── MAIN ─────────────────────────────────────────────────────────────────────

def render_net_worth():
    page_enter("net_worth")
    st.markdown("# 🏦 Net Worth Calculator")
    st.markdown(
        "Track your assets and liabilities to see your real-time net worth.")

    assets_df = get_assets()
    liabilities_df = get_liabilities()

    total_assets = assets_df["amount"].sum() if not assets_df.empty else 0.0
    total_liabilities = liabilities_df["amount"].sum(
    ) if not liabilities_df.empty else 0.0
    net_worth = total_assets - total_liabilities

    # ── KPI row ────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Assets",      fmt_currency(total_assets))
    c2.metric("Total Liabilities", fmt_currency(total_liabilities))
    c3.metric("Net Worth", fmt_currency(net_worth),
              "Positive ✅" if net_worth >= 0 else "Negative ⚠️")

    st.markdown("---")

    left, right = st.columns([1, 1], gap="large")

    with left:
        tab_a, tab_l = st.tabs(["➕ Add Asset", "➖ Add Liability"])

        with tab_a:
            st.markdown("#### New Asset")
            cat = st.selectbox("Category", ASSET_CATEGORIES, key="a_cat")
            name = st.text_input("Name (e.g. SBI Savings)", key="a_name")
            amt = st.number_input(
                "Amount (₹)", min_value=0.0, step=1000.0, key="a_amt")
            if st.button("Add Asset", key="btn_add_asset"):
                if name.strip():
                    add_asset(cat, name.strip(), amt)
                    st.success(f"✅ Added: {name}")
                    st.rerun()
                else:
                    st.warning("Please enter a name.")

        with tab_l:
            st.markdown("#### New Liability")
            lcat = st.selectbox("Category", LIABILITY_CATEGORIES, key="l_cat")
            lname = st.text_input("Name (e.g. HDFC Home Loan)", key="l_name")
            lamt = st.number_input(
                "Amount (₹)", min_value=0.0, step=1000.0, key="l_amt")
            if st.button("Add Liability", key="btn_add_liability"):
                if lname.strip():
                    add_liability(lcat, lname.strip(), lamt)
                    st.success(f"✅ Added: {lname}")
                    st.rerun()
                else:
                    st.warning("Please enter a name.")

        st.markdown("#### 📋 Current Assets")
        if assets_df.empty:
            st.info("No assets yet. Add your first asset above.")
        else:
            _col_headers()
            _asset_rows(assets_df)

        st.markdown("#### 📋 Current Liabilities")
        if liabilities_df.empty:
            st.info("No liabilities yet.")
        else:
            _col_headers()
            _liability_rows(liabilities_df)

        st.markdown("#### 💾 Save Snapshot")
        next_num = get_next_snapshot_number()
        snap_name = st.text_input(
            "Snapshot Name *(required)",
            value=f"Snapshot {next_num}",
            placeholder=f"e.g. Snapshot {next_num} or May 2026",
            key="snap_name_input",
        )
        if st.button("💾 Save Today's Snapshot",
                     help="Saves current net worth to history for trend tracking"):
            if snap_name.strip():
                save_snapshot(snap_name.strip(), total_assets,
                              total_liabilities, net_worth)
                st.success(f"✅ Snapshot **'{snap_name.strip()}'** saved!")
            else:
                st.error("⚠️ Snapshot name is required.")

    with right:
        _render_charts(assets_df, liabilities_df, total_assets,
                       total_liabilities, net_worth)
