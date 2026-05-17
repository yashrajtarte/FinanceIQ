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

from modules.database import add_goal, get_goals, delete_goal, update_goal, get_assets, get_liabilities

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


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
    target_month = int(goal.get("target_month", 12)
                       ) if goal.get("target_month") else 12
    today = date.today()
    months_left = max((target_year - today.year) * 12 +
                      (target_month - today.month), 1)
    years_left = months_left / 12

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
        required_monthly = remaining / months_left if months_left > 0 else remaining
        if monthly_contribution >= required_monthly:
            lines.append(
                f"✅ Your current monthly savings of ₹{monthly_contribution:,.0f} is sufficient "
                f"(need ₹{required_monthly:,.0f}/month to hit target by {MONTHS[target_month-1]} {target_year})."
            )
        else:
            shortfall = required_monthly - monthly_contribution
            lines.append(
                f"⚠️ You need **₹{required_monthly:,.0f}/month** but are saving ₹{monthly_contribution:,.0f}/month. "
                f"Increase savings by ₹{shortfall:,.0f}/month to reach your {MONTHS[target_month-1]} {target_year} target."
            )
    elif years_left <= 0:
        lines.append(
            f"⏰ This goal's target ({MONTHS[target_month-1]} {target_year}) has passed – consider updating it.")

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
    today = date.today()
    end_year = int(goal.get("target_year", today.year + 5))
    end_month = int(goal.get("target_month", 12)
                    ) if goal.get("target_month") else 12
    total_months = max((end_year - today.year) * 12 +
                       (end_month - today.month), 1)

    milestones = []
    for pct in [25, 50, 75, 100]:
        amt = target * pct / 100
        months_to_ms = int(total_months * pct / 100)
        ms_year = today.year + (today.month - 1 + months_to_ms) // 12
        ms_month = (today.month - 1 + months_to_ms) % 12 + 1
        achieved = saved >= amt
        milestones.append({
            "milestone": f"{pct}% – ₹{amt:,.0f}",
            "year": f"{MONTHS[ms_month-1][:3]} {ms_year}",
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
        col_m, col_y = st.columns(2)
        target_month = col_m.selectbox(
            "Target Month", MONTHS, index=11, key="add_tmonth")
        target_year = col_y.number_input(
            "Target Year", min_value=date.today().year, max_value=2075,
            value=date.today().year + 5, step=1,
        )
        if st.button("🚀 Add Goal"):
            if goal_name.strip():
                add_goal(goal_name.strip(), target_amt, current_saved, int(
                    target_year), priority, MONTHS.index(target_month)+1)  # type: ignore
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
            text=[
                "Now", f"{MONTHS[int(g.get('target_month',12))-1]} {int(g['target_year'])} — ₹{g['target_amount']:,.0f}"],
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
        rid = int(g["id"])
        edit_key = f"edit_goal_{rid}"
        priority_emoji = {"high": "🔴", "medium": "🟡",
                          "low": "🟢"}.get(g["priority"], "⚪")
        pct = min((g["current_saved"] / g["target_amount"] * 100),
                  100) if g["target_amount"] > 0 else 0

        if edit_key not in st.session_state:
            st.session_state[edit_key] = False

        with st.expander(f"{priority_emoji} {g['goal_name']} — {pct:.0f}% complete", expanded=True):

            # ── Edit mode ──────────────────────────────────────────────────
            if st.session_state[edit_key]:
                st.markdown("#### ✏️ Edit Goal")
                e1, e2 = st.columns(2)
                new_name = e1.text_input(
                    "Goal Name",     value=g["goal_name"],      key=f"eg_name_{rid}")
                new_pri = e2.selectbox("Priority",       ["high", "medium", "low"],
                                       index=["high", "medium", "low"].index(g["priority"]) if g["priority"] in [
                    "high", "medium", "low"] else 1,
                    key=f"eg_pri_{rid}")
                new_target = e1.number_input("Target Amount (₹)", value=float(g["target_amount"]),
                                             min_value=0.0, step=5000.0, key=f"eg_target_{rid}")
                new_saved = e2.number_input("Already Saved (₹)", value=float(g["current_saved"]),
                                            min_value=0.0, step=1000.0, key=f"eg_saved_{rid}")
                em1, em2 = st.columns(2)
                _cur_month = int(g.get('target_month', 12)) if g.get(
                    'target_month') else 12
                new_month_name = em1.selectbox("Target Month", MONTHS,
                                               index=_cur_month - 1,
                                               key=f"eg_month_{rid}")
                new_year = em2.number_input("Target Year", value=int(g["target_year"]),
                                            min_value=date.today().year, max_value=2075,
                                            step=1, key=f"eg_year_{rid}")
                new_month = MONTHS.index(new_month_name) + 1

                st.markdown("""
                    <style>
                    div[data-testid="stHorizontalBlock"] div:nth-child(1) .stButton > button {
                        background: #16a34a !important; color: #fff !important;
                        border: none !important; border-radius: 8px !important;
                        font-weight: 700 !important; white-space: nowrap !important;
                        width: 100% !important; padding: 0.5rem 0.8rem !important;
                    }
                    div[data-testid="stHorizontalBlock"] div:nth-child(2) .stButton > button {
                        background: transparent !important; color: #ef4444 !important;
                        border: 1.5px solid #ef4444 !important; border-radius: 8px !important;
                        font-weight: 700 !important; white-space: nowrap !important;
                        width: 100% !important; padding: 0.5rem 0.8rem !important;
                    }
                    </style>
                """, unsafe_allow_html=True)

                bc1, bc2, _ = st.columns([1.2, 1.2, 3])
                with bc1:
                    if st.button("💾  Save", key=f"save_goal_{rid}", use_container_width=True):
                        update_goal(rid, new_name.strip(), new_target,
                                    new_saved, int(new_year), new_month, new_pri)
                        st.session_state[edit_key] = False
                        st.success(f"✅ Goal '{new_name.strip()}' updated!")
                        st.rerun()
                with bc2:
                    if st.button("✖  Cancel", key=f"cancel_goal_{rid}", use_container_width=True):
                        st.session_state[edit_key] = False
                        st.rerun()

            # ── View mode ──────────────────────────────────────────────────
            else:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Target",      f"₹{g['target_amount']:,.0f}")
                col2.metric("Saved",       f"₹{g['current_saved']:,.0f}")
                col3.metric(
                    "Remaining",   f"₹{max(g['target_amount'] - g['current_saved'], 0):,.0f}")
                _tm = int(g.get('target_month', 12)) if g.get(
                    'target_month') else 12
                col4.metric(
                    "Target", f"{MONTHS[_tm-1][:3]} {int(g['target_year'])}")

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

                # Action buttons row
                st.markdown("---")
                ab1, ab2, _ = st.columns([1.2, 1.2, 3])
                with ab1:
                    if st.button("✏️  Edit Goal", key=f"edit_btn_goal_{rid}", use_container_width=True):
                        st.session_state[edit_key] = True
                        st.rerun()
                with ab2:
                    if st.button("🗑️  Delete", key=f"del_goal_{rid}", use_container_width=True):
                        delete_goal(rid)
                        st.rerun()
