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
    update_snapshot,
    delete_snapshot,
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
        snap_monthly = snap_monthly.sort_values(
            "snap_date", ascending=False).reset_index(drop=True)

        # ── Column headers ────────────────────────────────────────────────
        hc = st.columns([2.5, 1.5, 1.8, 1.8, 1.8, 1.5, 1.2, 0.8, 0.8])
        for col_h, label in zip(hc, ["Snapshot Name", "Month", "Assets (₹)", "Liabilities (₹)",
                                     "Net Worth (₹)", "Change (₹)", "Change (%)", "", ""]):
            col_h.markdown(f"<small style='color:#6060a0;font-weight:700;text-transform:uppercase;"
                           f"letter-spacing:0.07em;font-size:0.7rem;'>{label}</small>",
                           unsafe_allow_html=True)
        st.markdown("<hr style='margin:0.3rem 0 0.5rem 0;border-color:#2a2a4a;'>",
                    unsafe_allow_html=True)

        # ── Rows ──────────────────────────────────────────────────────────
        for _, row in snap_monthly.iterrows():
            rid = int(row["id"])
            edit_key = f"edit_snap_{rid}"
            if edit_key not in st.session_state:
                st.session_state[edit_key] = False

            change_color = "#10b981" if row["nw_change"] >= 0 else "#ef4444"
            change_arrow = "▲" if row["nw_change"] >= 0 else "▼"

            if st.session_state[edit_key]:
                # ── Edit mode ─────────────────────────────────────────────
                with st.container():
                    st.markdown(f"**✏️ Editing:** {row['snap_name']}")
                    e1, e2, e3, e4 = st.columns([2.5, 1.8, 1.8, 1.8])
                    new_sname = e1.text_input(
                        "Snapshot Name", value=row["snap_name"],  key=f"esn_name_{rid}")
                    new_assets = e2.number_input("Assets (₹)",  value=float(row["total_assets"]),
                                                 min_value=0.0, step=1000.0, key=f"esn_assets_{rid}")
                    new_liab = e3.number_input("Liabilities (₹)", value=float(row["total_liabilities"]),
                                               min_value=0.0, step=1000.0, key=f"esn_liab_{rid}")
                    new_nw = e4.number_input("Net Worth (₹)", value=float(row["net_worth"]),
                                             step=1000.0, key=f"esn_nw_{rid}")

                    st.markdown("""
                        <style>
                        div[data-testid="stHorizontalBlock"] div:nth-child(1) .stButton > button {
                            background: linear-gradient(135deg,#16a34a,#15803d) !important;
                            color:#fff !important; border:none !important;
                            border-radius:8px !important; font-weight:700 !important;
                            width:100% !important; white-space:nowrap !important;
                            padding:0.5rem 0.8rem !important;
                        }
                        div[data-testid="stHorizontalBlock"] div:nth-child(2) .stButton > button {
                            background:transparent !important; color:#f87171 !important;
                            border:1.5px solid #ef4444 !important; border-radius:8px !important;
                            font-weight:700 !important; width:100% !important;
                            white-space:nowrap !important; padding:0.5rem 0.8rem !important;
                        }
                        </style>
                    """, unsafe_allow_html=True)

                    bc1, bc2, _ = st.columns([1.2, 1.2, 5])
                    with bc1:
                        if st.button("💾  Save", key=f"save_snap_{rid}", use_container_width=True):
                            update_snapshot(
                                rid, new_sname, new_assets, new_liab, new_nw)
                            st.session_state[edit_key] = False
                            st.success(f"✅ '{new_sname}' updated!")
                            st.rerun()
                    with bc2:
                        if st.button("✖  Cancel", key=f"cancel_snap_{rid}", use_container_width=True):
                            st.session_state[edit_key] = False
                            st.rerun()
                    st.markdown("<hr style='margin:0.4rem 0;border-color:#2a2a4a;'>",
                                unsafe_allow_html=True)

            else:
                # ── View mode ─────────────────────────────────────────────
                rc = st.columns([2.5, 1.5, 1.8, 1.8, 1.8, 1.5, 1.2, 0.8, 0.8])
                rc[0].markdown(f"**{row['snap_name']}**")
                rc[1].markdown(
                    f"<small>{row['month']}</small>", unsafe_allow_html=True)
                rc[2].markdown(fmt_currency(row["total_assets"]))
                rc[3].markdown(fmt_currency(row["total_liabilities"]))
                rc[4].markdown(fmt_currency(row["net_worth"]))
                rc[5].markdown(
                    f"<span style='color:{change_color};font-weight:600;'>"
                    f"{change_arrow} {fmt_currency(abs(row['nw_change']))}</span>",
                    unsafe_allow_html=True,
                )
                rc[6].markdown(
                    f"<span style='color:{change_color};font-weight:600;'>"
                    f"{row['nw_change_pct']:+.1f}%</span>",
                    unsafe_allow_html=True,
                )
                if rc[7].button("✏️", key=f"edit_snap_btn_{rid}", help="Edit snapshot"):
                    st.session_state[edit_key] = True
                    st.rerun()
                if rc[8].button("🗑️", key=f"del_snap_{rid}", help="Delete snapshot"):
                    delete_snapshot(rid)
                    st.rerun()
                st.markdown("<hr style='margin:0.2rem 0;border-color:#1a1a30;'>",
                            unsafe_allow_html=True)

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
    st.caption(
        "Your score is calculated across 5 pillars. Each pillar shows exactly what to do to max it out.")

    # ── Scoring engine ─────────────────────────────────────────────────────
    # Each pillar: (label, icon, earned, max, status, what_to_do)
    pillars = []

    # 1. Debt Control (25 pts)
    if total_assets > 0:
        dta = total_liabilities / total_assets
        if dta < 0.2:
            d_earned, d_status = 25, "perfect"
            d_action = "✅ Excellent! Debt-to-asset ratio below 20% — keep it up."
        elif dta < 0.4:
            d_earned, d_status = 18, "good"
            d_action = f"📌 Ratio is {dta*100:.0f}%. Pay down liabilities to get below 20% and earn full 25 pts."
        elif dta < 0.6:
            d_earned, d_status = 10, "fair"
            d_action = f"⚠️ Ratio is {dta*100:.0f}%. Focus extra payments on high-interest debt first."
        else:
            d_earned, d_status = 3, "poor"
            d_action = f"🔴 Ratio is {dta*100:.0f}%! Prioritise debt repayment over new investments."
    else:
        d_earned, d_status = 0, "poor"
        d_action = "🔴 Add your assets to unlock this pillar."
    pillars.append(("Debt Control", "🏦", d_earned, 25, d_status, d_action))

    # 2. Net Worth (20 pts)
    if net_worth > 500000:
        nw_earned, nw_status = 20, "perfect"
        nw_action = "✅ Strong positive net worth above ₹5L — great foundation!"
    elif net_worth > 100000:
        nw_earned, nw_status = 15, "good"
        nw_action = "📌 Keep growing. Hit ₹5L+ net worth for full 20 pts."
    elif net_worth > 0:
        nw_earned, nw_status = 8, "fair"
        nw_action = f"⚠️ Net worth is ₹{net_worth:,.0f}. Grow assets and pay down debt consistently."
    else:
        nw_earned, nw_status = 0, "poor"
        nw_action = "🔴 Net worth is negative. Stop taking on new debt and build assets."
    pillars.append(("Net Worth", "📈", nw_earned, 20, nw_status, nw_action))

    # 3. Goal Funding (20 pts)
    if not goals_df.empty:
        avg_prog = (goals_df["current_saved"] /
                    goals_df["target_amount"]).clip(0, 1).mean() * 100
        high_goals = goals_df[goals_df["priority"] == "high"]
        high_funded = (high_goals["current_saved"] / high_goals["target_amount"]).clip(
            0, 1).mean() * 100 if not high_goals.empty else avg_prog
        if avg_prog >= 60 and high_funded >= 50:
            g_earned, g_status = 20, "perfect"
            g_action = "✅ Goals well-funded across the board!"
        elif avg_prog >= 35:
            g_earned, g_status = 13, "good"
            g_action = f"📌 Avg goal progress {avg_prog:.0f}%. Automate monthly SIPs to reach 60%+ for full pts."
        elif avg_prog >= 15:
            g_earned, g_status = 7, "fair"
            g_action = f"⚠️ Only {avg_prog:.0f}% avg. Set up standing instructions for each goal."
        else:
            g_earned, g_status = 2, "poor"
            g_action = "🔴 Goals barely started. Even ₹1,000/month per goal compounds significantly."
    else:
        g_earned, g_status = 0, "poor"
        g_action = "🔴 No goals set. Go to the Roadmap page and add at least 3 goals."
    pillars.append(("Goal Funding", "🎯", g_earned, 20, g_status, g_action))

    # 4. Diversification (20 pts)
    if not assets_df.empty:
        cats = assets_df["category"].nunique()
        has_invest = "Investments" in assets_df["category"].values
        has_cash = "Cash" in assets_df["category"].values
        has_prop = "Property" in assets_df["category"].values
        invest_pct = assets_df[assets_df["category"] == "Investments"]["amount"].sum(
        ) / total_assets * 100 if total_assets > 0 else 0
        if cats >= 3 and has_invest and invest_pct >= 20:
            dv_earned, dv_status = 20, "perfect"
            dv_action = "✅ Well-diversified portfolio across multiple asset classes!"
        elif cats >= 2 and has_invest:
            dv_earned, dv_status = 13, "good"
            dv_action = f"📌 {cats} categories. Add Property/Real-estate or Gold to diversify further."
        elif cats >= 2:
            dv_earned, dv_status = 8, "fair"
            dv_action = "⚠️ Add investment assets (mutual funds, stocks, ETFs) to earn full pts."
        else:
            dv_earned, dv_status = 3, "poor"
            dv_action = "🔴 All eggs in one basket! Spread across Cash, Investments, and Property."
    else:
        dv_earned, dv_status = 0, "poor"
        dv_action = "🔴 Add assets to assess diversification."
    pillars.append(("Diversification", "🌐", dv_earned,
                   20, dv_status, dv_action))

    # 5. Tracking Consistency (15 pts)
    snap_count = len(snapshots_df)
    if snap_count >= 12:
        t_earned, t_status = 15, "perfect"
        t_action = "✅ Excellent tracking discipline — 12+ snapshots saved!"
    elif snap_count >= 6:
        t_earned, t_status = 10, "good"
        t_action = f"📌 {snap_count} snapshots saved. Save monthly to hit 12 for full 15 pts."
    elif snap_count >= 3:
        t_earned, t_status = 6, "fair"
        t_action = f"⚠️ Only {snap_count} snapshots. Save a snapshot after every major financial event."
    else:
        t_earned, t_status = 1, "poor"
        t_action = "🔴 Barely any history. Save a net worth snapshot today — it takes 10 seconds!"
    pillars.append(("Tracking", "📊", t_earned, 15, t_status, t_action))

    # Total score
    score = sum(p[2] for p in pillars)
    max_score = sum(p[3] for p in pillars)  # = 100
    score_color = "#10b981" if score >= 75 else "#f59e0b" if score >= 45 else "#ef4444"
    score_label = "Excellent 🌟" if score >= 85 else "Good 👍" if score >= 65 else "Fair ⚡" if score >= 45 else "Needs Work 🔧"

    # ── Score display ──────────────────────────────────────────────────────
    sc1, sc2 = st.columns([1, 2])

    with sc1:
        st.markdown(
            f"<div style='text-align:center;padding:1.8rem 1rem;border-radius:20px;"
            f"border:2px solid {score_color};'>"
            f"<div style='font-size:3.8rem;font-weight:800;color:{score_color};'>{score}</div>"
            f"<div style='font-size:0.78rem;color:#6b7280;text-transform:uppercase;"
            f"letter-spacing:0.1em;margin-bottom:0.4rem;'>out of 100</div>"
            f"<div style='font-size:1.05rem;font-weight:700;color:{score_color};'>{score_label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown("")

        # Mini radar / bar chart of pillars
        import plotly.graph_objects as _pgo
        fig_radar = _pgo.Figure()
        pillar_names = [p[0] for p in pillars]
        pillar_earned = [p[2] for p in pillars]
        pillar_max = [p[3] for p in pillars]
        pillar_pct = [e/m*100 for e, m in zip(pillar_earned, pillar_max)]

        fig_radar.add_trace(_pgo.Bar(
            x=pillar_pct,
            y=pillar_names,
            orientation="h",
            marker=dict(
                color=["#10b981" if v >= 75 else "#f59e0b" if v >=
                       45 else "#ef4444" for v in pillar_pct],
                cornerradius=6,
            ),
            text=[f"{e}/{m}" for e, m in zip(pillar_earned, pillar_max)],
            textposition="inside",
            insidetextanchor="middle",
        ))
        fig_radar.update_layout(
            height=220,
            margin=dict(t=5, b=5, l=5, r=5),
            xaxis=dict(range=[0, 100], showticklabels=False, showgrid=False),
            yaxis=dict(showgrid=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with sc2:
        st.markdown("#### 🗺️ Your Roadmap to 100")
        st.caption("Here's exactly what to fix, pillar by pillar:")

        status_colors = {"perfect": "#10b981", "good": "#3b82f6",
                         "fair": "#f59e0b", "poor": "#ef4444"}
        status_labels = {"perfect": "MAX",
                         "good": "GOOD", "fair": "FAIR", "poor": "LOW"}

        for label, icon, earned, maximum, status, action in pillars:
            pct = earned / maximum * 100
            bar_color = status_colors[status]
            badge = status_labels[status]

            st.markdown(
                f"<div style='margin-bottom:0.9rem;padding:0.8rem 1rem;border-radius:12px;"
                f"border:1px solid #2a2a4a;background:#13132a;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;'>"
                f"<span style='font-weight:700;font-size:0.92rem;color:#e0e0ff;'>{icon} {label}</span>"
                f"<span style='font-size:0.72rem;font-weight:700;padding:0.15rem 0.6rem;"
                f"border-radius:20px;background:{bar_color}22;color:{bar_color};'>"
                f"{earned}/{maximum} pts · {badge}</span>"
                f"</div>"
                f"<div style='background:#2a2a4a;border-radius:6px;height:6px;margin-bottom:0.5rem;'>"
                f"<div style='background:{bar_color};width:{pct:.0f}%;height:6px;border-radius:6px;'></div>"
                f"</div>"
                f"<div style='font-size:0.82rem;color:#a0a0cc;'>{action}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # Perfect score checklist
        missing = sum(1 for p in pillars if p[4] != "perfect")
        if missing == 0:
            st.success("🎉 Perfect score! You're a financial role model.")
        else:
            st.info(
                f"💪 Fix **{missing} pillar{'s' if missing>1 else ''}** above to reach 100. You're {100-score} points away!")

    # ── Quick Tips ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🚀 Quick Wins — Do These Today")
    q1, q2, q3 = st.columns(3)
    with q1:
        st.markdown(
            "<div style='padding:1rem;border-radius:12px;border:1px solid #1e3a5f;background:#0d1f35;'>"
            "<div style='font-size:1.4rem;margin-bottom:0.4rem;'>⚡</div>"
            "<div style='font-weight:700;color:#60a5fa;margin-bottom:0.3rem;'>5-Minute Win</div>"
            "<div style='font-size:0.83rem;color:#94a3b8;'>Save today's net worth snapshot. "
            "One click → historical data starts building immediately.</div></div>",
            unsafe_allow_html=True,
        )
    with q2:
        st.markdown(
            "<div style='padding:1rem;border-radius:12px;border:1px solid #1e3a2a;background:#0d1f18;'>"
            "<div style='font-size:1.4rem;margin-bottom:0.4rem;'>🎯</div>"
            "<div style='font-weight:700;color:#34d399;margin-bottom:0.3rem;'>This Week</div>"
            "<div style='font-size:0.83rem;color:#94a3b8;'>Set up an auto-SIP for your top priority goal. "
            "Even ₹500/month invested for 20 years = significant wealth.</div></div>",
            unsafe_allow_html=True,
        )
    with q3:
        st.markdown(
            "<div style='padding:1rem;border-radius:12px;border:1px solid #3a1e2a;background:#1f0d18;'>"
            "<div style='font-size:1.4rem;margin-bottom:0.4rem;'>📅</div>"
            "<div style='font-weight:700;color:#f472b6;margin-bottom:0.3rem;'>This Month</div>"
            "<div style='font-size:0.83rem;color:#94a3b8;'>Review and pay more than the minimum on "
            "your highest-interest liability to improve your Debt Control score.</div></div>",
            unsafe_allow_html=True,
        )

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
