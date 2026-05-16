"""
modules/net_worth.py
======================
Net Worth Calculator page.
Users add/remove assets and liabilities; net worth is computed in real-time.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from modules.database import (
    add_asset, get_assets, delete_asset,
    add_liability, get_liabilities, delete_liability,
    save_snapshot,
)

ASSET_CATEGORIES = ["Cash", "Investments", "Property", "Other"]
LIABILITY_CATEGORIES = ["Loan", "Credit Card", "Mortgage", "Other"]


def fmt_currency(value: float) -> str:
    return f"₹{value:,.0f}" if value >= 0 else f"-₹{abs(value):,.0f}"


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
    c1.metric("Total Assets", fmt_currency(total_assets))
    c2.metric("Total Liabilities", fmt_currency(total_liabilities))
    nw_delta = "Positive" if net_worth >= 0 else "Negative"
    c3.metric("Net Worth", fmt_currency(net_worth), nw_delta)

    st.markdown("---")

    # ── Main layout: inputs left, charts right ─────────────────────────────
    left, right = st.columns([1, 1], gap="large")

    # ── Left: Add assets / liabilities ────────────────────────────────────
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
                    st.success(f"✅ Added asset: {name}")
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
                    st.success(f"✅ Added liability: {lname}")
                    st.rerun()
                else:
                    st.warning("Please enter a name.")

        # ── Asset table ────────────────────────────────────────────────────
        st.markdown("#### 📋 Current Assets")
        if assets_df.empty:
            st.info("No assets yet. Add your first asset above.")
        else:
            for _, row in assets_df.iterrows():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                col1.write(f"**{row['name']}**")
                col2.write(row["category"])
                col3.write(fmt_currency(row["amount"]))
                if col4.button("🗑️", key=f"del_a_{row['id']}"):
                    delete_asset(int(row["id"]))
                    st.rerun()

        # ── Liabilities table ──────────────────────────────────────────────
        st.markdown("#### 📋 Current Liabilities")
        if liabilities_df.empty:
            st.info("No liabilities yet.")
        else:
            for _, row in liabilities_df.iterrows():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                col1.write(f"**{row['name']}**")
                col2.write(row["category"])
                col3.write(fmt_currency(row["amount"]))
                if col4.button("🗑️", key=f"del_l_{row['id']}"):
                    delete_liability(int(row["id"]))
                    st.rerun()

        # ── Save snapshot ──────────────────────────────────────────────────
        if st.button("💾 Save Today's Snapshot", help="Saves current net worth to history"):
            save_snapshot(total_assets, total_liabilities, net_worth)
            st.success("Snapshot saved to history!")

    # ── Right: Visualisations ──────────────────────────────────────────────
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

        # ── Category breakdown ─────────────────────────────────────────────
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
