"""
modules/roadmap.py
===================
Financial Roadmap page.
Users set financial goals; the app generates milestones, a timeline,
and rule-based AI explanations for each goal.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date

from modules.database import add_goal, get_goals, delete_goal, get_assets, get_liabilities


# ── Rule-based insight engine ─────────────────────────────────────────────────

def generate_goal_insight(goal: dict, monthly_contribution: float) -> str:
    """
    Generate a human-readable roadmap explanation using rule-based logic.
    No external AI API required – pure Python heuristics.
    """
    name = goal["goal_name"]
    target = goal["target_amount"]
    saved = goal["current_saved"]
    remaining = target - saved
    target_year = int(goal["target_year"])
    priority = goal["priority"]
    years_left = target_year - date.today().year

    pct = (saved / target * 100) if target > 0 else 0

    lines = []

    # Progress statement
    if pct >= 100:
        lines.append(
            f"🎉 **Congratulations!** You've fully funded your **{name}** goal.")
        return "\n".join(lines)
    elif pct >= 75:
        lines.append(
            f"You're in the **final stretch** for your **{name}** goal – {pct:.1f}% funded.")
    elif pct >= 50:
        lines.append(
            f"You're **halfway there** on your **{name}** goal ({pct:.1f}% complete).")
    elif pct >= 25:
        lines.append(
            f"Good start on your **{name}** goal – {pct:.1f}% funded so far.")
    else:
        lines.append(
            f"Your **{name}** goal is just getting started ({pct:.1f}% funded).")

    # Monthly requirement
    if years_left > 0 and monthly_contribution > 0:
        months_left = years_left * 12
        required_monthly = remaining / months_left if months_left > 0 else remaining
        if monthly_contribution >= required_monthly:
            lines.append(
                f"✅ Your current monthly savings of ₹{monthly_contribution:,.0f} is sufficient "
                f"(need ₹{required_monthly:,.0f}/month to hit target by {target_year})."
            )
        else:
            shortfall = required_monthly - monthly_contribution
            lines.append(
                f"⚠️ You need **₹{required_monthly:,.0f}/month** but are saving ₹{monthly_contribution:,.0f}/month. "
                f"Increase savings by ₹{shortfall:,.0f}/month to stay on track."
            )
    elif years_left <= 0:
        lines.append(
            f"⏰ This goal's target year ({target_year}) has passed – consider updating it.")

    # Priority advice
    if priority == "high":
        lines.append("🔴 **High priority** – make this a top budget item.")
    elif priority == "medium":
        lines.append("🟡 **Medium priority** – balance this with other goals.")
    else:
        lines.append("🟢 **Low priority** – contribute when budget allows.")

    # General tip
    if "retirement" in name.lower():
        lines.append(
            "💡 *Tip:* Maximise EPF/NPS contributions for tax benefits and compound growth.")
    elif "house" in name.lower() or "home" in name.lower():
        lines.append(
            "💡 *Tip:* Keep the down payment in a high-yield savings or FD account.")
    elif "emergency" in name.lower():
        lines.append(
            "💡 *Tip:* Target 6 months of expenses; keep in a liquid fund.")
    elif "travel" in name.lower():
        lines.append(
            "💡 *Tip:* Book flights 3-4 months ahead for the best deals.")
    else:
        lines.append(
            "💡 *Tip:* Automate monthly contributions via a SIP or standing instruction.")

    return "\n\n".join(lines)


def build_milestones(goal: dict) -> list[dict]:
    """Return a list of milestone dicts (25%, 50%, 75%, 100%) for a goal."""
    target = goal["target_amount"]
    saved = goal["current_saved"]
    start_year = date.today().year
    end_year = int(goal["target_year"])
    years_left = max(end_year - start_year, 1)

    milestones = []
    for pct in [25, 50, 75, 100]:
        amt = target * pct / 100
        years_to_milestone = years_left * pct / 100
        milestone_year = int(start_year + years_to_milestone)
        achieved = saved >= amt
        milestones.append({
            "milestone": f"{pct}% – ₹{amt:,.0f}",
            "year": milestone_year,
            "achieved": achieved,
            "amount": amt,
        })
    return milestones


# ── Render ────────────────────────────────────────────────────────────────────

def render_roadmap():
    st.markdown("# 🗺️ Financial Roadmap")
    st.markdown(
        "Set your goals, get AI-powered milestones and actionable advice.")

    # Monthly savings input (used for feasibility analysis)
    st.sidebar.markdown("---")
    monthly_savings = st.sidebar.number_input(
        "Monthly Savings (₹)",
        min_value=0.0,
        value=15000.0,
        step=1000.0,
        help="Used to assess goal feasibility",
    )

    # ── Add goal form ──────────────────────────────────────────────────────
    with st.expander("➕ Add a New Financial Goal", expanded=False):
        c1, c2 = st.columns(2)
        goal_name = c1.text_input("Goal Name", placeholder="e.g. Buy a House")
        priority = c2.selectbox("Priority", ["high", "medium", "low"])
        target_amt = c1.number_input(
            "Target Amount (₹)", min_value=0.0, step=5000.0)
        current_saved = c2.number_input(
            "Already Saved (₹)", min_value=0.0, step=1000.0)
        target_year = c1.number_input(
            "Target Year", min_value=date.today().year, max_value=2075,
            value=date.today().year + 5, step=1,
        )
        if st.button("🚀 Add Goal"):
            if goal_name.strip():
                add_goal(goal_name.strip(), target_amt,
                         current_saved, int(target_year), priority)
                st.success(f"Goal '{goal_name}' added!")
                st.rerun()
            else:
                st.warning("Please enter a goal name.")

    # ── Load goals ─────────────────────────────────────────────────────────
    goals_df = get_goals()
    if goals_df.empty:
        st.info(
            "No goals yet. Add your first goal above, or load the example dataset from Reports.")
        return

    # ── Timeline chart ─────────────────────────────────────────────────────
    st.markdown("### 📅 Goals Timeline")
    today_year = date.today().year
    fig_timeline = go.Figure()

    priority_colors = {"high": "#ef4444",
                       "medium": "#f59e0b", "low": "#10b981"}

    for _, g in goals_df.iterrows():
        pct = min((g["current_saved"] / g["target_amount"] * 100),
                  100) if g["target_amount"] > 0 else 0
        color = priority_colors.get(g["priority"], "#6b7280")
        fig_timeline.add_trace(go.Scatter(
            x=[today_year, g["target_year"]],
            y=[g["goal_name"], g["goal_name"]],
            mode="lines+markers+text",
            line=dict(color=color, width=3),
            marker=dict(size=[10, 16], color=[color, color],
                        symbol=["circle", "star"]),
            text=["Now", f"₹{g['target_amount']:,.0f}"],
            textposition="top center",
            name=g["goal_name"],
        ))

    fig_timeline.update_layout(
        height=max(300, 80 * len(goals_df)),
        margin=dict(t=30, b=30, l=120, r=30),
        xaxis=dict(title="Year", tickformat="%d"),
        yaxis=dict(title=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

    # ── Progress overview chart ────────────────────────────────────────────
    st.markdown("### 📊 Progress Overview")
    goals_df["progress_pct"] = (
        (goals_df["current_saved"] / goals_df["target_amount"] * 100)
        .clip(0, 100)
        .fillna(0)
    )
    goals_df["remaining_pct"] = 100 - goals_df["progress_pct"]

    fig_prog = go.Figure()
    fig_prog.add_trace(go.Bar(
        name="Saved",
        y=goals_df["goal_name"],
        x=goals_df["progress_pct"],
        orientation="h",
        marker_color="#2563eb",
        text=[f"{p:.0f}%" for p in goals_df["progress_pct"]],
        textposition="inside",
    ))
    fig_prog.add_trace(go.Bar(
        name="Remaining",
        y=goals_df["goal_name"],
        x=goals_df["remaining_pct"],
        orientation="h",
        marker_color="#e5e7eb",
    ))
    fig_prog.update_layout(
        barmode="stack",
        height=max(250, 60 * len(goals_df)),
        margin=dict(t=10, b=30, l=10, r=10),
        xaxis=dict(title="Progress (%)", range=[0, 100]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
    )
    st.plotly_chart(fig_prog, use_container_width=True)

    # ── Per-goal cards ─────────────────────────────────────────────────────
    st.markdown("### 🎯 Goal Details & AI Insights")
    for _, g in goals_df.iterrows():
        g_dict = g.to_dict()
        priority_emoji = {"high": "🔴", "medium": "🟡",
                          "low": "🟢"}.get(g["priority"], "⚪")
        pct = min((g["current_saved"] / g["target_amount"] * 100),
                  100) if g["target_amount"] > 0 else 0

        with st.expander(f"{priority_emoji} {g['goal_name']} — {pct:.0f}% complete", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Target", f"₹{g['target_amount']:,.0f}")
            col2.metric("Saved", f"₹{g['current_saved']:,.0f}")
            col3.metric(
                "Remaining", f"₹{max(g['target_amount'] - g['current_saved'], 0):,.0f}")
            col4.metric("Target Year", str(int(g["target_year"])))

            # Progress bar
            st.progress(int(pct) / 100, text=f"{pct:.1f}% funded")

            # Milestones
            milestones = build_milestones(g_dict)
            cols = st.columns(4)
            for i, ms in enumerate(milestones):
                icon = "✅" if ms["achieved"] else "⬜"
                cols[i].markdown(
                    f"<div style='text-align:center;font-size:0.8rem'>"
                    f"{icon}<br><b>{ms['milestone']}</b><br>{ms['year']}</div>",
                    unsafe_allow_html=True,
                )

            # AI insight
            st.markdown("---")
            st.markdown("**💡 Roadmap Insight**")
            insight = generate_goal_insight(g_dict, monthly_savings)
            st.markdown(insight)

            # Delete button
            if st.button(f"🗑️ Delete Goal", key=f"del_goal_{g['id']}"):
                delete_goal(int(g["id"]))
                st.rerun()
