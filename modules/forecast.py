"""
modules/forecast.py
====================
Net Worth Forecasting page.
Uses scikit-learn LinearRegression on historical snapshots for short-term trends,
and a compound-growth model for long-range projections.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

from modules.database import get_snapshots, get_assets, get_liabilities


def fmt_currency(value: float) -> str:
    if abs(value) >= 1_00_00_000:
        return f"₹{value/1_00_00_000:.2f} Cr"
    elif abs(value) >= 1_00_000:
        return f"₹{value/1_00_000:.2f} L"
    return f"₹{value:,.0f}"


def compound_projection(
    current_nw: float,
    monthly_savings: float,
    annual_return_pct: float,
    years: int,
) -> pd.DataFrame:
    """
    Project net worth year-by-year using compound growth + monthly contributions.
    Formula: FV = PV*(1+r)^n + PMT * [((1+r)^n - 1) / r]
    """
    r = annual_return_pct / 100  # annual rate
    records = []
    nw = current_nw
    for y in range(1, years + 1):
        # Year-end value with compound growth
        nw = nw * (1 + r) + monthly_savings * 12
        records.append({"year": date.today().year + y, "projected_nw": nw})
    return pd.DataFrame(records)


def ml_trend_projection(snapshots_df: pd.DataFrame, future_years: int = 5) -> pd.DataFrame:
    """
    Fit a polynomial regression on historical snapshot data and project forward.
    Returns a DataFrame with year and predicted net worth.
    """
    if len(snapshots_df) < 3:
        return pd.DataFrame()

    snapshots_df = snapshots_df.copy()
    snapshots_df["snap_date"] = pd.to_datetime(snapshots_df["snap_date"])
    snapshots_df["year_float"] = (
        snapshots_df["snap_date"].dt.year
        + snapshots_df["snap_date"].dt.month / 12
    )

    X = snapshots_df[["year_float"]].values
    y = snapshots_df["net_worth"].values

    # Polynomial degree 2 for a smoother trend
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(X)
    model = LinearRegression()
    model.fit(X_poly, y)  # type: ignore

    # Predict for past + future
    current_year_float = date.today().year + date.today().month / 12
    future_floats = np.linspace(X.min(), current_year_float + future_years, 60)
    future_poly = poly.transform(future_floats.reshape(-1, 1))
    preds = model.predict(future_poly)

    return pd.DataFrame({
        "year_float": future_floats,
        "ml_predicted_nw": preds,
    })


def render_forecast():
    st.markdown("# 📈 Forecast & Projections")
    st.markdown("Compare your **current trajectory** with your **projected net worth** using ML trend analysis and compound growth models.")

    # ── Current net worth ──────────────────────────────────────────────────
    assets_df = get_assets()
    liabilities_df = get_liabilities()
    current_assets = assets_df["amount"].sum() if not assets_df.empty else 0.0
    current_liabilities = liabilities_df["amount"].sum(
    ) if not liabilities_df.empty else 0.0
    current_nw = current_assets - current_liabilities

    # ── Sidebar inputs ─────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Projection Settings**")

    monthly_savings = st.sidebar.slider(
        "Monthly Savings (₹)", 0, 200000, 15000, step=1000
    )
    annual_return = st.sidebar.slider(
        "Expected Annual Return (%)", 1.0, 20.0, 10.0, step=0.5
    )
    inflation_rate = st.sidebar.slider(
        "Inflation Rate (%)", 0.0, 10.0, 6.0, step=0.5
    )
    projection_years = st.sidebar.slider(
        "Projection Horizon (Years)", 5, 40, 20, step=5
    )

    real_return = annual_return - inflation_rate  # real rate of return

    # ── KPI row ────────────────────────────────────────────────────────────
    proj_df = compound_projection(
        current_nw, monthly_savings, annual_return, projection_years)
    real_proj_df = compound_projection(
        current_nw, monthly_savings, real_return, projection_years)
    end_nw = proj_df["projected_nw"].iloc[-1] if not proj_df.empty else current_nw
    end_real_nw = real_proj_df["projected_nw"].iloc[-1] if not real_proj_df.empty else current_nw
    inflation_drag = end_nw - end_real_nw

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Net Worth", fmt_currency(current_nw))
    c2.metric(f"Projected NW ({projection_years}Y)", fmt_currency(end_nw))
    c3.metric("Real (Inflation-adj)", fmt_currency(end_real_nw))
    c4.metric("Inflation Drag", fmt_currency(inflation_drag))

    st.markdown("---")

    # ── Main forecast chart ────────────────────────────────────────────────
    st.markdown("### 📊 Compound Growth Projection")

    fig = go.Figure()

    # Projected nominal
    fig.add_trace(go.Scatter(
        x=proj_df["year"].tolist(),
        y=proj_df["projected_nw"].tolist(),
        mode="lines",
        name=f"Projected NW ({annual_return}% return)",
        line=dict(color="#2563eb", width=3),
        fill="tozeroy",
        fillcolor="rgba(37,99,235,0.08)",
    ))

    # Real (inflation-adjusted)
    fig.add_trace(go.Scatter(
        x=real_proj_df["year"].tolist(),
        y=real_proj_df["projected_nw"].tolist(),
        mode="lines",
        name=f"Real NW ({real_return:.1f}% real return)",
        line=dict(color="#10b981", width=2, dash="dash"),
    ))

    # Current NW marker
    fig.add_trace(go.Scatter(
        x=[date.today().year],
        y=[current_nw],
        mode="markers",
        name="Current NW",
        marker=dict(size=14, color="#ef4444", symbol="star"),
    ))

    fig.update_layout(
        height=420,
        margin=dict(t=20, b=40, l=60, r=20),
        xaxis_title="Year",
        yaxis_title="Net Worth (₹)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,252,1)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        hovermode="x unified",
    )
    fig.update_yaxes(tickformat=",.0f", tickprefix="₹")
    st.plotly_chart(fig, use_container_width=True)

    # ── ML trend projection ────────────────────────────────────────────────
    snapshots_df = get_snapshots()
    if len(snapshots_df) >= 3:
        st.markdown("### 🤖 ML Trend Analysis (Historical Regression)")
        ml_df = ml_trend_projection(snapshots_df, future_years=5)

        fig_ml = go.Figure()

        # Historical actual
        snap = snapshots_df.copy()
        snap["snap_date"] = pd.to_datetime(snap["snap_date"])
        fig_ml.add_trace(go.Scatter(
            x=snap["snap_date"],
            y=snap["net_worth"],
            mode="lines+markers",
            name="Actual Net Worth",
            line=dict(color="#2563eb", width=2),
            marker=dict(size=7),
        ))

        # ML prediction
        if not ml_df.empty:
            current_year_float = date.today().year + date.today().month / 12
            split_idx = ml_df["year_float"] <= current_year_float
            hist_ml = ml_df[split_idx]
            future_ml = ml_df[~split_idx]

            # Convert year_float to approximate datetime for display
            def yf_to_date(yf):
                yr = int(yf)
                mo = int((yf - yr) * 12) + 1
                return f"{yr}-{mo:02d}-01"

            fig_ml.add_trace(go.Scatter(
                x=[yf_to_date(y) for y in hist_ml["year_float"]],
                y=hist_ml["ml_predicted_nw"],
                mode="lines",
                name="ML Fitted Trend",
                line=dict(color="#8b5cf6", width=2, dash="dot"),
            ))
            fig_ml.add_trace(go.Scatter(
                x=[yf_to_date(y) for y in future_ml["year_float"]],
                y=future_ml["ml_predicted_nw"],
                mode="lines",
                name="ML Forecast (5Y)",
                line=dict(color="#f59e0b", width=2, dash="dash"),
                fill="tozeroy",
                fillcolor="rgba(245,158,11,0.07)",
            ))

        fig_ml.update_layout(
            height=380,
            margin=dict(t=20, b=40, l=60, r=20),
            xaxis_title="Date",
            yaxis_title="Net Worth (₹)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,248,252,1)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        )
        fig_ml.update_yaxes(tickformat=",.0f", tickprefix="₹")
        st.plotly_chart(fig_ml, use_container_width=True)

        st.caption(
            "📌 The ML trend uses polynomial regression on your snapshot history. "
            "The compound-growth chart uses your inputs above."
        )
    else:
        st.info(
            "💡 Save at least 3 net-worth snapshots (from the Net Worth page) "
            "to unlock ML trend analysis."
        )

    # ── Scenario comparison ────────────────────────────────────────────────
    st.markdown("### 🔁 Scenario Comparison")
    scenarios = {
        "Conservative (6%)": compound_projection(current_nw, monthly_savings, 6, projection_years),
        "Moderate (10%)": compound_projection(current_nw, monthly_savings, 10, projection_years),
        "Aggressive (15%)": compound_projection(current_nw, monthly_savings, 15, projection_years),
    }
    colors = {"Conservative (6%)": "#94a3b8",
              "Moderate (10%)": "#3b82f6", "Aggressive (15%)": "#10b981"}

    fig_sc = go.Figure()
    for label, df in scenarios.items():
        fig_sc.add_trace(go.Scatter(
            x=df["year"],
            y=df["projected_nw"],
            mode="lines",
            name=label,
            line=dict(color=colors[label], width=2.5),
        ))
    fig_sc.add_hline(y=current_nw, line_dash="dot", line_color="#ef4444",
                     annotation_text="Current NW", annotation_position="right")
    fig_sc.update_layout(
        height=360,
        margin=dict(t=10, b=40, l=60, r=20),
        xaxis_title="Year",
        yaxis_title="Net Worth (₹)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,248,252,1)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
    )
    fig_sc.update_yaxes(tickformat=",.0f", tickprefix="₹")
    st.plotly_chart(fig_sc, use_container_width=True)

    # ── Summary table ──────────────────────────────────────────────────────
    st.markdown("### 📋 Projection Summary Table")
    milestones_years = [5, 10, 15, 20, 25, 30]
    rows = []
    for yr in milestones_years:
        if yr <= projection_years:
            row = {"Year": date.today().year + yr}
            for label, df in scenarios.items():
                nw_at_yr = df[df["year"] == date.today().year +
                              yr]["projected_nw"]
                row[label] = fmt_currency(  # type: ignore
                    nw_at_yr.values[0]) if len(nw_at_yr) else "—"
            rows.append(row)

    if rows:
        st.dataframe(pd.DataFrame(rows).set_index(
            "Year"), use_container_width=True)
