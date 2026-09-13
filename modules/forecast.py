"""
modules/forecast.py — Redesigned Forecast & Projections page.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

from modules.animations import page_enter
from modules.database import get_snapshots, get_assets, get_liabilities

# ── Shared dark theme for all charts ─────────────────────────────────────────
BG = "rgba(0,0,0,0)"
GRID_COLOR = "#1e1e38"
TICK_COLOR = "#6060a0"
FONT = dict(family="DM Sans, sans-serif", color="#c0c0d0")


def _dark_layout(**kwargs):
    base = dict(
        paper_bgcolor=BG,
        plot_bgcolor="#0d0d1f",
        font=FONT,
        xaxis=dict(showgrid=False, zeroline=False,
                   tickfont=dict(color=TICK_COLOR, size=11),
                   linecolor="#2a2a4a"),
        yaxis=dict(showgrid=True, gridcolor=GRID_COLOR, zeroline=False,
                   tickfont=dict(color=TICK_COLOR, size=11),
                   linecolor="#2a2a4a"),
        legend=dict(
            bgcolor="rgba(13,13,31,0.8)",
            bordercolor="#2a2a4a",
            borderwidth=1,
            font=dict(size=11, color="#c0c0d0"),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1a1a3a",
            bordercolor="#3a3a6a",
            font=dict(color="#e0e0ff", size=12),
        ),
    )
    base.update(kwargs)
    return base


def fmt_inr(value: float) -> str:
    if abs(value) >= 1_00_00_000:
        return f"₹{value/1_00_00_000:.2f} Cr"
    elif abs(value) >= 1_00_000:
        return f"₹{value/1_00_000:.1f} L"
    return f"₹{value:,.0f}"


def _tick_fmt(values):
    """Auto-pick tick format based on magnitude."""
    mx = max(abs(v) for v in values if v)
    if mx >= 1_00_00_000:
        return [f"₹{v/1_00_00_000:.1f}Cr" for v in values]
    elif mx >= 1_00_000:
        return [f"₹{v/1_00_000:.0f}L" for v in values]
    return [f"₹{v:,.0f}" for v in values]


def compound_projection(current_nw, monthly_savings, annual_return_pct, years):
    r, nw, records = annual_return_pct / 100, current_nw, []
    for y in range(1, years + 1):
        nw = nw * (1 + r) + monthly_savings * 12
        records.append({"year": date.today().year + y, "projected_nw": nw})
    return pd.DataFrame(records)


def ml_trend_projection(snapshots_df, future_years=5):
    if len(snapshots_df) < 3:
        return pd.DataFrame()
    df = snapshots_df.copy()
    df["snap_date"] = pd.to_datetime(df["snap_date"])
    df["year_float"] = df["snap_date"].dt.year + df["snap_date"].dt.month / 12
    X = df[["year_float"]].values
    y = df["net_worth"].values
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(X)
    model = LinearRegression()
    model.fit(X_poly, y)
    cyf = date.today().year + date.today().month / 12
    future_floats = np.linspace(X.min(), cyf + future_years, 60)
    preds = model.predict(poly.transform(future_floats.reshape(-1, 1)))
    return pd.DataFrame({"year_float": future_floats, "ml_predicted_nw": preds})


def yf_to_date(yf):
    yr, mo = int(yf), int((yf - int(yf)) * 12) + 1
    return f"{yr}-{mo:02d}-01"


def render_forecast():
    page_enter("forecast")
    st.markdown("# 📈 Forecast & Projections")
    st.markdown(
        "Model your financial future with compound growth and ML-powered trend analysis.")

    assets_df = get_assets()
    liabilities_df = get_liabilities()
    current_assets = assets_df["amount"].sum() if not assets_df.empty else 0.0
    current_liab = liabilities_df["amount"].sum(
    ) if not liabilities_df.empty else 0.0
    current_nw = current_assets - current_liab

    # ── Sidebar ───────────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown("**⚙️ Projection Settings**")
    monthly_savings = st.sidebar.slider(
        "Monthly Savings (₹)",   0,      200000, 15000, step=1000)
    annual_return = st.sidebar.slider(
        "Expected Return (%)",    1.0,    20.0,   10.0,  step=0.5)
    inflation_rate = st.sidebar.slider(
        "Inflation Rate (%)",     0.0,    10.0,   6.0,   step=0.5)
    projection_years = st.sidebar.slider(
        "Horizon (Years)",        5,      40,     20,    step=5)
    real_return = annual_return - inflation_rate

    proj_df = compound_projection(
        current_nw, monthly_savings, annual_return, projection_years)
    real_proj_df = compound_projection(
        current_nw, monthly_savings, real_return,   projection_years)
    end_nw = proj_df["projected_nw"].iloc[-1] if not proj_df.empty else current_nw
    end_real_nw = real_proj_df["projected_nw"].iloc[-1] if not real_proj_df.empty else current_nw
    inflation_drag = end_nw - end_real_nw
    growth_mult = end_nw / current_nw if current_nw > 0 else 0

    # ── KPI pills ─────────────────────────────────────────────────────────
    pill_data = [
        ("Current NW",                  fmt_inr(current_nw),    "#6366f1", "💼"),
        (f"Projected ({projection_years}Y)", fmt_inr(end_nw),  "#34d399", "🚀"),
        ("Inflation-Adj",               fmt_inr(end_real_nw),   "#38bdf8", "📉"),
        ("Growth Multiple",
         f"{growth_mult:.1f}×",  "#fbbf24", "⚡"),
    ]
    cols = st.columns(4)
    for col, (label, value, color, icon) in zip(cols, pill_data):
        col.markdown(
            f"<div style='background:#13132a;border:1px solid #2a2a4a;border-radius:14px;"
            f"padding:1rem 1rem 0.8rem;text-align:center;'>"
            f"<div style='font-size:1.4rem;margin-bottom:0.2rem;'>{icon}</div>"
            f"<div style='font-size:0.62rem;text-transform:uppercase;letter-spacing:0.12em;"
            f"color:#6060a0;font-weight:700;margin-bottom:0.35rem;'>{label}</div>"
            f"<div style='font-size:1.25rem;font-weight:800;color:{color};"
            f"font-family:Syne,sans-serif;'>{value}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin:1.2rem 0 0.5rem;'></div>",
                unsafe_allow_html=True)

    # ── 1. Main Growth Chart ───────────────────────────────────────────────
    st.markdown("### 🚀 Compound Growth Projection")

    fig = go.Figure()

    # Filled area — nominal
    fig.add_trace(go.Scatter(
        x=proj_df["year"], y=proj_df["projected_nw"],
        mode="lines", name=f"Nominal ({annual_return}% return)",
        line=dict(color="#6366f1", width=3),
        fill="tozeroy", fillcolor="rgba(99,102,241,0.12)",
        hovertemplate="<b>%{x}</b><br>Nominal: " + "%{y:,.0f}<extra></extra>",
    ))

    # Real return line
    fig.add_trace(go.Scatter(
        x=real_proj_df["year"], y=real_proj_df["projected_nw"],
        mode="lines", name=f"Real ({real_return:.1f}% after inflation)",
        line=dict(color="#34d399", width=2.5, dash="dash"),
        hovertemplate="<b>%{x}</b><br>Real: ₹%{y:,.0f}<extra></extra>",
    ))

    # Inflation drag shaded area between nominal and real
    fig.add_trace(go.Scatter(
        x=list(proj_df["year"]) + list(real_proj_df["year"])[::-1],
        y=list(proj_df["projected_nw"]) +
        list(real_proj_df["projected_nw"])[::-1],
        fill="toself", fillcolor="rgba(251,191,36,0.06)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Inflation Drag Zone", showlegend=True,
        hoverinfo="skip",
    ))

    # Current NW star
    fig.add_trace(go.Scatter(
        x=[date.today().year], y=[current_nw],
        mode="markers+text",
        name="Today",
        marker=dict(size=16, color="#f43f5e", symbol="star",
                    line=dict(color="#fff", width=1.5)),
        text=[f"  {fmt_inr(current_nw)}"],
        textposition="top right",
        textfont=dict(color="#f43f5e", size=11),
        hovertemplate="<b>Today</b><br>₹%{y:,.0f}<extra></extra>",
    ))

    # 5-year milestone annotations
    for yr_offset in [5, 10, 15, 20]:
        if yr_offset <= projection_years:
            target_yr = date.today().year + yr_offset
            subset = proj_df[proj_df["year"] == target_yr]
            if not subset.empty:
                val = subset["projected_nw"].values[0]
                fig.add_annotation(
                    x=target_yr, y=val,
                    text=fmt_inr(val),
                    showarrow=True, arrowhead=2,
                    arrowcolor="#6366f1", arrowsize=0.8,
                    ax=0, ay=-36,
                    font=dict(size=10, color="#a0a0cc"),
                    bgcolor="rgba(13,13,31,0.85)",
                    bordercolor="#2a2a4a", borderwidth=1,
                )

    fig.update_layout(
        **_dark_layout(
            height=440,
            margin=dict(t=30, b=50, l=70, r=30),
            xaxis_title="Year",
            yaxis_title="Net Worth",
            legend=dict(orientation="h", yanchor="bottom", y=-0.22),
        )
    )
    fig.update_yaxes(tickprefix="₹", tickformat=".2s")
    st.plotly_chart(fig, use_container_width=True)

    # ── 2. ML Trend ───────────────────────────────────────────────────────
    snapshots_df = get_snapshots()
    if len(snapshots_df) >= 3:
        st.markdown("### 🤖 ML Trend Analysis")
        col_info1, col_info2 = st.columns([3, 1])
        col_info1.caption(
            "Polynomial regression fitted on your snapshot history, projected 5 years forward.")

        ml_df = ml_trend_projection(snapshots_df, future_years=5)
        snap = snapshots_df.copy()
        snap["snap_date"] = pd.to_datetime(snap["snap_date"])

        fig_ml = go.Figure()

        # Actual history
        fig_ml.add_trace(go.Scatter(
            x=snap["snap_date"], y=snap["net_worth"],
            mode="lines+markers",
            name="Actual Net Worth",
            line=dict(color="#6366f1", width=2.5),
            marker=dict(size=8, color="#6366f1",
                        line=dict(color="#fff", width=1.5)),
            hovertemplate="<b>%{x|%b %Y}</b><br>₹%{y:,.0f}<extra></extra>",
        ))

        if not ml_df.empty:
            cyf = date.today().year + date.today().month / 12
            hist_ml = ml_df[ml_df["year_float"] <= cyf]
            future_ml = ml_df[ml_df["year_float"] > cyf]

            fig_ml.add_trace(go.Scatter(
                x=[yf_to_date(y) for y in hist_ml["year_float"]],
                y=hist_ml["ml_predicted_nw"],
                mode="lines", name="ML Fitted",
                line=dict(color="#8b5cf6", width=2, dash="dot"),
                hovertemplate="ML: ₹%{y:,.0f}<extra></extra>",
            ))
            fig_ml.add_trace(go.Scatter(
                x=[yf_to_date(y) for y in future_ml["year_float"]],
                y=future_ml["ml_predicted_nw"],
                mode="lines", name="ML Forecast (5Y)",
                line=dict(color="#fbbf24", width=2.5, dash="dash"),
                fill="tozeroy", fillcolor="rgba(251,191,36,0.07)",
                hovertemplate="Forecast: ₹%{y:,.0f}<extra></extra>",
            ))

            # Confidence band (±15%)
            future_upper = future_ml["ml_predicted_nw"] * 1.15
            future_lower = future_ml["ml_predicted_nw"] * 0.85
            x_band = [yf_to_date(y) for y in future_ml["year_float"]]
            fig_ml.add_trace(go.Scatter(
                x=x_band + x_band[::-1],
                y=list(future_upper) + list(future_lower)[::-1],
                fill="toself", fillcolor="rgba(251,191,36,0.08)",
                line=dict(color="rgba(0,0,0,0)"),
                name="±15% Confidence Band",
                hoverinfo="skip",
            ))

        fig_ml.update_layout(
            **_dark_layout(
                height=380,
                margin=dict(t=20, b=50, l=70, r=30),
                xaxis_title="Date",
                yaxis_title="Net Worth",
                legend=dict(orientation="h", yanchor="bottom", y=-0.28),
            )
        )
        fig_ml.update_yaxes(tickprefix="₹", tickformat=".2s")
        st.plotly_chart(fig_ml, use_container_width=True)

    else:
        st.markdown(
            "<div style='background:#13132a;border:1px solid #2a2a4a;border-radius:12px;"
            "padding:1rem 1.2rem;color:#8080aa;font-size:0.9rem;'>"
            "🤖 <b style='color:#a0a0cc'>ML Trend unlocks after 3 snapshots.</b> "
            "Save a net worth snapshot from the Net Worth page after each major financial event.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin:0.5rem 0;'></div>", unsafe_allow_html=True)

    # ── 3. Scenario Comparison ────────────────────────────────────────────
    st.markdown("### 🔁 Scenario Comparison")

    scenarios = {
        "Conservative (6%)":  (compound_projection(current_nw, monthly_savings,  6, projection_years), "#94a3b8"),
        "Your Input ({}%)".format(annual_return): (proj_df, "#6366f1"),
        "Aggressive (15%)":   (compound_projection(current_nw, monthly_savings, 15, projection_years), "#34d399"),
    }

    fig_sc = go.Figure()
    for label, (df, color) in scenarios.items():
        is_main = "Input" in label
        fig_sc.add_trace(go.Scatter(
            x=df["year"], y=df["projected_nw"],
            mode="lines", name=label,
            line=dict(color=color, width=3.5 if is_main else 2,
                      dash="solid" if is_main else "dot"),
            fill="tozeroy" if is_main else "none",
            fillcolor="rgba(99,102,241,0.07)" if is_main else "rgba(0,0,0,0)",
            hovertemplate=f"<b>{label}</b><br>%{{x}}: ₹%{{y:,.0f}}<extra></extra>",
        ))

    # Current NW reference line
    fig_sc.add_hline(
        y=current_nw, line_dash="dot", line_color="#f43f5e", line_width=1.5,
        annotation=dict(text=f"  Today: {fmt_inr(current_nw)}",
                        font=dict(color="#f43f5e", size=11),
                        bgcolor="rgba(13,13,31,0.8)"),
        annotation_position="right",
    )

    fig_sc.update_layout(
        **_dark_layout(
            height=380,
            margin=dict(t=20, b=50, l=70, r=120),
            xaxis_title="Year",
            yaxis_title="Net Worth",
            legend=dict(orientation="h", yanchor="bottom", y=-0.25),
        )
    )
    fig_sc.update_yaxes(tickprefix="₹", tickformat=".2s")
    st.plotly_chart(fig_sc, use_container_width=True)

    # ── 4. Summary Table + mini sparkline ────────────────────────────────
    st.markdown("### 📋 Projection Milestones")

    milestone_yrs = [y for y in [5, 10, 15,
                                 20, 25, 30] if y <= projection_years]
    rows = []
    for yr in milestone_yrs:
        target_yr = date.today().year + yr
        conservative = compound_projection(current_nw, monthly_savings, 6, yr)
        aggressive = compound_projection(current_nw, monthly_savings, 15, yr)
        nominal = compound_projection(
            current_nw, monthly_savings, annual_return, yr)

        rows.append({
            "Year": target_yr,
            "Years Away": f"{yr}Y",
            f"Conservative (6%)":  fmt_inr(conservative["projected_nw"].iloc[-1]),
            f"Your Rate ({annual_return}%)": fmt_inr(nominal["projected_nw"].iloc[-1]),
            "Aggressive (15%)":    fmt_inr(aggressive["projected_nw"].iloc[-1]),
            "Multiple": f"{nominal['projected_nw'].iloc[-1] / current_nw:.1f}×" if current_nw > 0 else "—",
        })

    if rows:
        st.dataframe(
            pd.DataFrame(rows).set_index("Year"),
            use_container_width=True,
        )
