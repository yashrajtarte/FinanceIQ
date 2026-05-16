"""
modules/reports.py
===================
Reports & Insights page.
Monthly/yearly summaries, visualisations, CSV export, and example data loader.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
import io

from modules.database import (
    get_assets,
    get_liabilities,
    get_goals,
    get_snapshots,
    seed_example_data,
)


def fmt_currency(value: float) -> str:
    if abs(value) >= 1_00_00_000:
        return f"₹{value/1_00_00_000:.2f} Cr"
    elif abs(value) >= 1_00_000:
        return f"₹{value/1_00_000:.2f} L"
    return f"₹{value:,.0f}"


def render_reports():
    st.markdown("# 📊 Reports & Insights")
    st.markdown(
        "Monthly and yearly summaries, visualisations, and data exports.")

    # ── Load example data button ───────────────────────────────────────────
    with st.expander("🧪 Demo / Testing", expanded=False):
        st.markdown(
            "Load a pre-built example dataset to explore all features instantly.")
        if st.button("🚀 Load Example Dataset"):
            seed_example_data()
            st.success("✅ Example data loaded! Explore all pages now.")
            st.rerun()

    st.markdown("---")

    # ── Pull all data ──────────────────────────────────────────────────────
    assets_df = get_assets()
    liabilities_df = get_liabilities()
    goals_df = get_goals()
    snapshots_df = get_snapshots()

    total_assets = assets_df["amount"].sum() if not assets_df.empty else 0.0
    total_liabilities = liabilities_df["amount"].sum(
    ) if not liabilities_df.empty else 0.0
    net_worth = total_assets - total_liabilities

    # ── Top KPIs ───────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Assets",      fmt_currency(total_assets))
    c2.metric("Total Liabilities", fmt_currency(total_liabilities))
    c3.metric("Net Worth",         fmt_currency(net_worth))
    c4.metric("Active Goals",      str(len(goals_df))
              if not goals_df.empty else "0")

    st.markdown("---")

    # ── Snapshot history chart ─────────────────────────────────────────────
    st.markdown("### 📅 Net Worth History")
    if not snapshots_df.empty:
        snapshots_df["snap_date"] = pd.to_datetime(snapshots_df["snap_date"])
        snapshots_df = snapshots_df.sort_values("snap_date")

        fig_hist = go.Figure()
        fig_hist.add_trace(go.Scatter(
            x=snapshots_df["snap_date"],
            y=snapshots_df["net_worth"],
            mode="lines+markers",
            name="Net Worth",
            line=dict(color="#2563eb", width=3),
            marker=dict(size=7),
            fill="tozeroy",
            fillcolor="rgba(37,99,235,0.08)",
        ))
        fig_hist.add_trace(go.Scatter(
            x=snapshots_df["snap_date"],
            y=snapshots_df["total_assets"],
            mode="lines",
            name="Total Assets",
            line=dict(color="#10b981", width=2, dash="dash"),
        ))
        fig_hist.add_trace(go.Scatter(
            x=snapshots_df["snap_date"],
            y=snapshots_df["total_liabilities"],
            mode="lines",
            name="Total Liabilities",
            line=dict(color="#ef4444", width=2, dash="dot"),
        ))
        fig_hist.update_layout(
            height=380,
            margin=dict(t=10, b=40, l=60, r=20),
            xaxis_title="Date",
            yaxis_title="Amount (₹)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,248,252,1)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            hovermode="x unified",
        )
        fig_hist.update_yaxes(tickformat=",.0f", tickprefix="₹")
        st.plotly_chart(fig_hist, use_container_width=True)

        # ── Monthly change table ───────────────────────────────────────────
        st.markdown("### 📋 Monthly Summary")
        snap_monthly = snapshots_df.copy()
        snap_monthly["month"] = snap_monthly["snap_date"].dt.to_period(
            "M").astype(str)
        snap_monthly["nw_change"] = snap_monthly["net_worth"].diff().fillna(0)
        snap_monthly["nw_change_pct"] = (
            snap_monthly["net_worth"].pct_change().fillna(0) * 100
        ).round(2)

        display_cols = snap_monthly[["snap_name", "month", "total_assets",
                                     "total_liabilities", "net_worth", "nw_change", "nw_change_pct"]].copy()
        display_cols.columns = ["Snapshot Name", "Month",
                                "Assets (₹)", "Liabilities (₹)", "Net Worth (₹)", "Change (₹)", "Change (%)"]
        display_cols = display_cols.sort_values(
            "Month", ascending=False).reset_index(drop=True)

        # Format numeric columns
        for col in ["Assets (₹)", "Liabilities (₹)", "Net Worth (₹)", "Change (₹)"]:
            display_cols[col] = display_cols[col].apply(fmt_currency)

        st.dataframe(display_cols, use_container_width=True)

    else:
        st.info(
            "No snapshot history yet. Save snapshots from the Net Worth page to see trends here.")

    st.markdown("---")

    # ── Asset breakdown ────────────────────────────────────────────────────
    st.markdown("### 🏦 Asset & Liability Breakdown")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Assets by Category**")
        if not assets_df.empty:
            cat_assets = assets_df.groupby(
                "category")["amount"].sum().reset_index()
            fig_a = px.pie(
                cat_assets,
                values="amount",
                names="category",
                hole=0.4,
                color_discrete_sequence=["#1e40af",
                                         "#3b82f6", "#93c5fd", "#bfdbfe"],
            )
            fig_a.update_layout(
                height=280,
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            )
            st.plotly_chart(fig_a, use_container_width=True)
        else:
            st.info("No assets recorded.")

    with col_b:
        st.markdown("**Liabilities by Category**")
        if not liabilities_df.empty:
            cat_liab = liabilities_df.groupby(
                "category")["amount"].sum().reset_index()
            fig_l = px.pie(
                cat_liab,
                values="amount",
                names="category",
                hole=0.4,
                color_discrete_sequence=["#991b1b",
                                         "#ef4444", "#fca5a5", "#fee2e2"],
            )
            fig_l.update_layout(
                height=280,
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            )
            st.plotly_chart(fig_l, use_container_width=True)
        else:
            st.info("No liabilities recorded.")

    # ── Goals summary ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🎯 Goals Summary")
    if not goals_df.empty:
        goals_display = goals_df.copy()
        goals_display["Progress (%)"] = (
            (goals_display["current_saved"] /
             goals_display["target_amount"] * 100)
            .clip(0, 100)
            .round(1)
        )
        goals_display["Remaining (₹)"] = (
            goals_display["target_amount"] - goals_display["current_saved"]
        ).clip(lower=0).apply(fmt_currency)
        goals_display["Target (₹)"] = goals_display["target_amount"].apply(
            fmt_currency)
        goals_display["Saved (₹)"] = goals_display["current_saved"].apply(
            fmt_currency)

        st.dataframe(
            goals_display[["goal_name", "priority",
                           "Target (₹)", "Saved (₹)", "Remaining (₹)", "Progress (%)", "target_year"]]
            .rename(columns={"goal_name": "Goal", "priority": "Priority", "target_year": "Target Year"}),
            use_container_width=True,
        )

        # Goals progress bar chart
        fig_goals = px.bar(
            goals_display,
            x="Progress (%)",
            y="goal_name",
            orientation="h",
            color="priority",
            color_discrete_map={"high": "#ef4444",
                                "medium": "#f59e0b", "low": "#10b981"},
            labels={"goal_name": "Goal", "Progress (%)": "% Funded"},
            range_x=[0, 100],
        )
        fig_goals.update_layout(
            height=max(200, 55 * len(goals_display)),
            margin=dict(t=10, b=30, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,248,252,1)",
            legend_title="Priority",
        )
        st.plotly_chart(fig_goals, use_container_width=True)
    else:
        st.info("No goals set yet. Add goals from the Roadmap page.")

    # ── Financial health score ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💡 Financial Health Score")

    score = 0
    tips = []

    # Debt-to-asset ratio
    if total_assets > 0:
        dta = total_liabilities / total_assets
        if dta < 0.3:
            score += 30
        elif dta < 0.5:
            score += 20
            tips.append(
                "⚠️ Your debt-to-asset ratio is moderate. Try to pay down liabilities.")
        else:
            score += 5
            tips.append(
                "🔴 High debt-to-asset ratio. Focus on reducing liabilities.")
    else:
        tips.append(
            "🔴 No assets recorded — add your assets to get a health score.")

    # Net worth positive
    if net_worth > 0:
        score += 25
    else:
        tips.append("🔴 Your net worth is negative. Focus on reducing debt.")

    # Savings / goals coverage
    if not goals_df.empty:
        avg_progress = (goals_df["current_saved"] /
                        goals_df["target_amount"]).mean() * 100
        if avg_progress >= 50:
            score += 25
        elif avg_progress >= 25:
            score += 15
            tips.append(
                "⚠️ Your goals are partially funded. Increase monthly contributions.")
        else:
            score += 5
            tips.append("🔴 Goals are underfunded. Set up automatic savings.")
    else:
        tips.append(
            "⚠️ No financial goals set. Define goals to track progress.")

    # Snapshot history (engagement)
    if len(snapshots_df) >= 6:
        score += 20
    elif len(snapshots_df) >= 3:
        score += 10
        tips.append(
            "💡 Save snapshots monthly to track your progress accurately.")
    else:
        tips.append(
            "💡 Save regular net worth snapshots to track your financial journey.")

    score = min(score, 100)

    # Display score
    score_color = "#10b981" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"
    score_label = "Excellent 🌟" if score >= 80 else "Good 👍" if score >= 60 else "Fair ⚡" if score >= 40 else "Needs Work 🔧"

    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        st.markdown(
            f"""
            <div style="text-align:center;padding:1.5rem;background:white;border-radius:20px;
                        border:2px solid {score_color};box-shadow:0 4px 20px rgba(0,0,0,0.08)">
                <div style="font-size:3.5rem;font-weight:800;color:{score_color};
                            font-family:'Syne',sans-serif">{score}</div>
                <div style="font-size:0.85rem;color:#6b7280;text-transform:uppercase;
                            letter-spacing:0.08em">out of 100</div>
                <div style="font-size:1.1rem;font-weight:600;color:{score_color};
                            margin-top:0.5rem">{score_label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_s2:
        if tips:
            for tip in tips:
                st.markdown(tip)
        else:
            st.success(
                "🎉 Your finances look great! Keep up the excellent work.")

    # ── CSV Export ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 Export Data")

    col_e1, col_e2, col_e3, col_e4 = st.columns(4)

    def to_csv_bytes(df: pd.DataFrame) -> bytes:
        return df.to_csv(index=False).encode("utf-8")

    with col_e1:
        if not assets_df.empty:
            st.download_button(
                "⬇️ Assets CSV",
                data=to_csv_bytes(assets_df),
                file_name="assets.csv",
                mime="text/csv",
            )
        else:
            st.button("⬇️ Assets CSV", disabled=True)

    with col_e2:
        if not liabilities_df.empty:
            st.download_button(
                "⬇️ Liabilities CSV",
                data=to_csv_bytes(liabilities_df),
                file_name="liabilities.csv",
                mime="text/csv",
            )
        else:
            st.button("⬇️ Liabilities CSV", disabled=True)

    with col_e3:
        if not goals_df.empty:
            st.download_button(
                "⬇️ Goals CSV",
                data=to_csv_bytes(goals_df),
                file_name="goals.csv",
                mime="text/csv",
            )
        else:
            st.button("⬇️ Goals CSV", disabled=True)

    with col_e4:
        if not snapshots_df.empty:
            st.download_button(
                "⬇️ History CSV",
                data=to_csv_bytes(snapshots_df),
                file_name="net_worth_history.csv",
                mime="text/csv",
            )
        else:
            st.button("⬇️ History CSV", disabled=True)
