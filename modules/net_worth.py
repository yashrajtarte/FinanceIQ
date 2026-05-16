"""
modules/net_worth.py
======================
Net Worth Calculator page.
Users can add, edit, and delete assets and liabilities.
Net worth is computed in real-time.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from modules.database import (
    add_asset, get_assets, delete_asset, update_asset,
    add_liability, get_liabilities, delete_liability, update_liability,
    save_snapshot, get_next_snapshot_number,
)

ASSET_CATEGORIES = ["Cash", "Investments", "Property", "Other"]
LIABILITY_CATEGORIES = ["Loan", "Credit Card", "Mortgage", "Other"]


def fmt_currency(value: float) -> str:
    return f"₹{value:,.0f}" if value >= 0 else f"-₹{abs(value):,.0f}"


def _asset_rows(assets_df: pd.DataFrame):
    """Render each asset row with View / Edit / Delete actions."""

    for _, row in assets_df.iterrows():
        rid = int(row["id"])
        edit_key = f"edit_asset_{rid}"

        # Toggle edit mode via session state
        if edit_key not in st.session_state:
            st.session_state[edit_key] = False

        if st.session_state[edit_key]:
            # ── Edit mode ─────────────────────────────────────────────────
            with st.container():
                st.markdown(f"**Editing:** {row['name']}")
                ec1, ec2, ec3 = st.columns([2, 2, 2])
                new_name = ec1.text_input(
                    "Name", value=row["name"], key=f"ea_name_{rid}"
                )
                new_cat = ec2.selectbox(
                    "Category",
                    ASSET_CATEGORIES,
                    index=ASSET_CATEGORIES.index(row["category"])
                    if row["category"] in ASSET_CATEGORIES else 0,
                    key=f"ea_cat_{rid}",
                )
                new_amt = ec3.number_input(
                    "Amount (₹)",
                    value=float(row["amount"]),
                    min_value=0.0,
                    step=1000.0,
                    key=f"ea_amt_{rid}",
                )

                st.markdown("""
                    <style>
                    /* Save button — green */
                    div[data-testid="stHorizontalBlock"] div:nth-child(1) .stButton > button {
                        background: #16a34a !important;
                        color: #ffffff !important;
                        border: none !important;
                        border-radius: 8px !important;
                        font-weight: 700 !important;
                        font-size: 0.9rem !important;
                        white-space: nowrap !important;
                        width: 100% !important;
                        padding: 0.5rem 0.8rem !important;
                    }
                    div[data-testid="stHorizontalBlock"] div:nth-child(1) .stButton > button:hover {
                        background: #15803d !important;
                        box-shadow: 0 3px 12px rgba(22,163,74,0.4) !important;
                    }
                    /* Cancel button — red outline */
                    div[data-testid="stHorizontalBlock"] div:nth-child(2) .stButton > button {
                        background: transparent !important;
                        color: #ef4444 !important;
                        border: 1.5px solid #ef4444 !important;
                        border-radius: 8px !important;
                        font-weight: 700 !important;
                        font-size: 0.9rem !important;
                        white-space: nowrap !important;
                        width: 100% !important;
                        padding: 0.5rem 0.8rem !important;
                    }
                    div[data-testid="stHorizontalBlock"] div:nth-child(2) .stButton > button:hover {
                        background: rgba(239,68,68,0.1) !important;
                    }
                    </style>
                """, unsafe_allow_html=True)

                btn_col1, btn_col2, _ = st.columns([1.2, 1.2, 3])
                with btn_col1:
                    if st.button("💾  Save", key=f"save_a_{rid}", use_container_width=True):
                        update_asset(rid, new_cat, new_name.strip(),  # type: ignore
                                     new_amt)
                        st.session_state[edit_key] = False
                        st.success(f"✅ Updated: {new_name}")
                        st.rerun()
                with btn_col2:
                    if st.button("✖  Cancel", key=f"cancel_a_{rid}", use_container_width=True):
                        st.session_state[edit_key] = False
                        st.rerun()
            st.markdown("---")

        else:
            # ── View mode ─────────────────────────────────────────────────
            c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1])
            c1.write(f"**{row['name']}**")
            c2.write(row["category"])
            c3.write(fmt_currency(row["amount"]))

            if c4.button("✏️", key=f"edit_btn_a_{rid}", help="Edit"):
                st.session_state[edit_key] = True
                st.rerun()
            if c5.button("🗑️", key=f"del_a_{rid}", help="Delete"):
                delete_asset(rid)
                st.rerun()


def _liability_rows(liabilities_df: pd.DataFrame):
    """Render each liability row with View / Edit / Delete actions."""

    for _, row in liabilities_df.iterrows():
        rid = int(row["id"])
        edit_key = f"edit_liability_{rid}"

        if edit_key not in st.session_state:
            st.session_state[edit_key] = False

        if st.session_state[edit_key]:
            # ── Edit mode ─────────────────────────────────────────────────
            with st.container():
                st.markdown(f"**Editing:** {row['name']}")
                ec1, ec2, ec3 = st.columns([2, 2, 2])
                new_name = ec1.text_input(
                    "Name", value=row["name"], key=f"el_name_{rid}"
                )
                new_cat = ec2.selectbox(
                    "Category",
                    LIABILITY_CATEGORIES,
                    index=LIABILITY_CATEGORIES.index(row["category"])
                    if row["category"] in LIABILITY_CATEGORIES else 0,
                    key=f"el_cat_{rid}",
                )
                new_amt = ec3.number_input(
                    "Amount (₹)",
                    value=float(row["amount"]),
                    min_value=0.0,
                    step=1000.0,
                    key=f"el_amt_{rid}",
                )

                st.markdown("""
                    <style>
                    div[data-testid="stHorizontalBlock"] div:nth-child(1) .stButton > button {
                        background: #16a34a !important;
                        color: #ffffff !important;
                        border: none !important;
                        border-radius: 8px !important;
                        font-weight: 700 !important;
                        font-size: 0.9rem !important;
                        white-space: nowrap !important;
                        width: 100% !important;
                        padding: 0.5rem 0.8rem !important;
                    }
                    div[data-testid="stHorizontalBlock"] div:nth-child(1) .stButton > button:hover {
                        background: #15803d !important;
                        box-shadow: 0 3px 12px rgba(22,163,74,0.4) !important;
                    }
                    div[data-testid="stHorizontalBlock"] div:nth-child(2) .stButton > button {
                        background: transparent !important;
                        color: #ef4444 !important;
                        border: 1.5px solid #ef4444 !important;
                        border-radius: 8px !important;
                        font-weight: 700 !important;
                        font-size: 0.9rem !important;
                        white-space: nowrap !important;
                        width: 100% !important;
                        padding: 0.5rem 0.8rem !important;
                    }
                    div[data-testid="stHorizontalBlock"] div:nth-child(2) .stButton > button:hover {
                        background: rgba(239,68,68,0.1) !important;
                    }
                    </style>
                """, unsafe_allow_html=True)

                btn_col1, btn_col2, _ = st.columns([1.2, 1.2, 3])
                with btn_col1:
                    if st.button("💾  Save", key=f"save_l_{rid}", use_container_width=True):
                        update_liability(
                            rid, new_cat, new_name.strip(), new_amt)  # type: ignore
                        st.session_state[edit_key] = False
                        st.success(f"✅ Updated: {new_name}")
                        st.rerun()
                with btn_col2:
                    if st.button("✖  Cancel", key=f"cancel_l_{rid}", use_container_width=True):
                        st.session_state[edit_key] = False
                        st.rerun()
            st.markdown("---")

        else:
            # ── View mode ─────────────────────────────────────────────────
            c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1])
            c1.write(f"**{row['name']}**")
            c2.write(row["category"])
            c3.write(fmt_currency(row["amount"]))

            if c4.button("✏️", key=f"edit_btn_l_{rid}", help="Edit"):
                st.session_state[edit_key] = True
                st.rerun()
            if c5.button("🗑️", key=f"del_l_{rid}", help="Delete"):
                delete_liability(rid)
                st.rerun()


def render_net_worth():
    st.markdown("# 🏦 Net Worth Calculator")
    st.markdown(
        "Track your assets and liabilities to see your real-time net worth.")

    # ── Load current data ──────────────────────────────────────────────────
    assets_df = get_assets()
    liabilities_df = get_liabilities()

    total_assets = assets_df["amount"].sum() if not assets_df.empty else 0.0
    total_liabilities = liabilities_df["amount"].sum(
    ) if not liabilities_df.empty else 0.0
    net_worth = total_assets - total_liabilities

    # ── Top KPI cards ─────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Assets",      fmt_currency(total_assets))
    c2.metric("Total Liabilities", fmt_currency(total_liabilities))
    c3.metric("Net Worth", fmt_currency(net_worth),
              "Positive ✅" if net_worth >= 0 else "Negative ⚠️")

    st.markdown("---")

    # ── Main layout ────────────────────────────────────────────────────────
    left, right = st.columns([1, 1], gap="large")

    with left:
        # ── Add forms ──────────────────────────────────────────────────────
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

        # ── Assets list ────────────────────────────────────────────────────
        st.markdown("#### 📋 Current Assets")
        st.caption("Use ✏️ to edit · 🗑️ to delete")
        if assets_df.empty:
            st.info("No assets yet. Add your first asset above.")
        else:
            _asset_rows(assets_df)

        # ── Liabilities list ───────────────────────────────────────────────
        st.markdown("#### 📋 Current Liabilities")
        st.caption("Use ✏️ to edit · 🗑️ to delete")
        if liabilities_df.empty:
            st.info("No liabilities yet.")
        else:
            _liability_rows(liabilities_df)

        # ── Snapshot ───────────────────────────────────────────────────────
        st.markdown("#### 💾 Save Snapshot")
        next_num = get_next_snapshot_number()
        snap_name = st.text_input(
            "Snapshot Name \*(required)",
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

    # ── Right: charts ──────────────────────────────────────────────────────
    with right:
        st.markdown("#### 📊 Asset Breakdown")
        if not assets_df.empty:
            fig_assets = px.pie(
                assets_df,
                values="amount",
                names="name",
                hole=0.45,
                color_discrete_sequence=px.colors.sequential.Blues_r,
            )
            fig_assets.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.25),
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_assets, use_container_width=True)
        else:
            st.info("Add assets to see the breakdown.")

        st.markdown("#### 📊 Assets vs Liabilities")
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Assets",
            x=["Financial Position"],
            y=[total_assets],
            marker_color="#2563eb",
            width=0.35,
        ))
        fig_bar.add_trace(go.Bar(
            name="Liabilities",
            x=["Financial Position"],
            y=[total_liabilities],
            marker_color="#ef4444",
            width=0.35,
        ))
        fig_bar.add_trace(go.Bar(
            name="Net Worth",
            x=["Financial Position"],
            y=[net_worth],
            marker_color="#10b981" if net_worth >= 0 else "#f59e0b",
            width=0.35,
        ))
        fig_bar.update_layout(
            barmode="group",
            margin=dict(t=10, b=10, l=10, r=10),
            height=280,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_title="Amount (₹)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        if not assets_df.empty:
            st.markdown("#### Assets by Category")
            cat_group = assets_df.groupby(
                "category")["amount"].sum().reset_index()
            fig_cat = px.bar(
                cat_group,
                x="category",
                y="amount",
                color="category",
                color_discrete_sequence=["#1e40af",
                                         "#3b82f6", "#93c5fd", "#bfdbfe"],
                labels={"amount": "Amount (₹)", "category": "Category"},
            )
            fig_cat.update_layout(
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=240,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_cat, use_container_width=True)
