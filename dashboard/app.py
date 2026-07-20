"""
app.py — Interactive P&L Dashboard
------------------------------------
Streamlit dashboard for the Dean & David restaurant P&L analysis
project. Reads the same /data CSVs used by src/pl_calculations.py
and renders an interactive, filterable view.

Run locally:
    pip install -r requirements.txt
    streamlit run dashboard/app.py

Deploy for free:
    Push this repo to GitHub, then go to share.streamlit.io,
    connect your GitHub account, pick this repo, and set the
    main file path to: dashboard/app.py
"""
import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Allow importing src/pl_calculations.py regardless of where streamlit is launched from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "src"))

from pl_calculations import (  # noqa: E402
    load_data, daily_pl, weekly_pl, item_profitability, weekday_pattern
)

st.set_page_config(
    page_title="Dean & David — P&L Dashboard",
    page_icon="📊",
    layout="wide",
)

GREEN = "#2F5233"
GOLD = "#C9A227"
RED = "#B23A48"

# -----------------------------------------------------------------
# Load & compute (cached so it doesn't recompute on every interaction)
# -----------------------------------------------------------------
@st.cache_data
def get_data():
    menu, sales, labor, overheads = load_data()
    daily = daily_pl(sales, labor, overheads)
    weekly = weekly_pl(daily)
    by_item = item_profitability(sales)
    pattern = weekday_pattern(sales)
    return menu, sales, labor, overheads, daily, weekly, by_item, pattern


menu, sales, labor, overheads, daily, weekly, by_item, pattern = get_data()

# -----------------------------------------------------------------
# Header
# -----------------------------------------------------------------
st.title("📊 Dean & David — Restaurant P&L Dashboard")
st.caption(
    "Interactive view of the profit & loss analysis. Data is synthetic/sample "
    "(see project README) — structured to mirror a real POS + labor export."
)

# -----------------------------------------------------------------
# Sidebar filters
# -----------------------------------------------------------------
st.sidebar.header("Filters")
min_date, max_date = daily["date"].min(), daily["date"].max()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_d, end_d = date_range
else:
    start_d, end_d = min_date.date(), max_date.date()

categories = sorted(sales["category"].unique().tolist())
selected_categories = st.sidebar.multiselect("Menu category", categories, default=categories)

mask_daily = (daily["date"].dt.date >= start_d) & (daily["date"].dt.date <= end_d)
daily_f = daily.loc[mask_daily]

mask_sales = (
    (sales["date"].dt.date >= start_d)
    & (sales["date"].dt.date <= end_d)
    & (sales["category"].isin(selected_categories))
)
sales_f = sales.loc[mask_sales]
by_item_f = item_profitability(sales_f) if len(sales_f) else by_item.iloc[0:0]

# -----------------------------------------------------------------
# KPI row
# -----------------------------------------------------------------
total_rev = daily_f["revenue_eur"].sum()
total_op_profit = daily_f["operating_profit_eur"].sum()
avg_gm = daily_f["gross_margin_pct"].mean() if len(daily_f) else 0
avg_labor_pct = daily_f["labor_pct_of_revenue"].mean() if len(daily_f) else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue", f"€{total_rev:,.0f}")
k2.metric("Operating Profit", f"€{total_op_profit:,.0f}")
k3.metric("Avg Gross Margin", f"{avg_gm*100:.1f}%")
k4.metric(
    "Avg Labor % of Revenue",
    f"{avg_labor_pct*100:.1f}%",
    delta=f"{(avg_labor_pct-0.30)*100:+.1f} pts vs 30% guideline",
    delta_color="inverse",
)

st.divider()

# -----------------------------------------------------------------
# Row 1: Revenue vs Profit trend, Labor % trend
# -----------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Weekly Revenue vs Operating Profit")
    weekly_f = weekly[(weekly["week"].dt.date >= start_d) & (weekly["week"].dt.date <= end_d)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=weekly_f["week"], y=weekly_f["revenue_eur"],
                              mode="lines+markers", name="Revenue", line=dict(color=GREEN, width=3)))
    fig.add_trace(go.Scatter(x=weekly_f["week"], y=weekly_f["operating_profit_eur"],
                              mode="lines+markers", name="Operating Profit", line=dict(color=GOLD, width=3)))
    fig.update_layout(yaxis_title="EUR", legend=dict(orientation="h", y=1.1), margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Labor Cost as % of Revenue")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=weekly_f["week"], y=weekly_f["labor_pct_of_revenue"] * 100,
                               mode="lines+markers", name="Labor %", line=dict(color=RED, width=3)))
    fig2.add_hline(y=30, line_dash="dash", line_color="gray", annotation_text="30% guideline")
    fig2.update_layout(yaxis_title="%", margin=dict(t=10))
    st.plotly_chart(fig2, use_container_width=True)

# -----------------------------------------------------------------
# Row 2: Item margin ranking, profit contribution
# -----------------------------------------------------------------
col3, col4 = st.columns(2)

with col3:
    st.subheader("Item Gross Margin (%)")
    if len(by_item_f):
        top = by_item_f.sort_values("margin_pct", ascending=True)
        fig3 = px.bar(top, x="margin_pct", y="item", orientation="h",
                      color="margin_pct", color_continuous_scale=[RED, GOLD, GREEN])
        fig3.update_layout(xaxis_tickformat=".0%", coloraxis_showscale=False, margin=dict(t=10))
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No data for selected filters.")

with col4:
    st.subheader("Gross Profit Contribution by Item")
    if len(by_item_f):
        top2 = by_item_f.sort_values("gross_profit_eur", ascending=False)
        fig4 = px.bar(top2, x="item", y="gross_profit_eur", color_discrete_sequence=[GREEN])
        fig4.update_layout(yaxis_title="EUR", xaxis_title="", margin=dict(t=10))
        fig4.update_xaxes(tickangle=-45)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No data for selected filters.")

# -----------------------------------------------------------------
# Row 3: Weekday demand pattern
# -----------------------------------------------------------------
st.subheader("Average Revenue by Day of Week")
pattern_f = weekday_pattern(sales_f) if len(sales_f) else pattern.iloc[0:0]
if len(pattern_f):
    fig5 = px.bar(pattern_f, x="weekday", y="avg_daily_revenue_eur", color_discrete_sequence=[GREEN])
    fig5.update_layout(yaxis_title="EUR", xaxis_title="", margin=dict(t=10))
    st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("No data for selected filters.")

# -----------------------------------------------------------------
# Raw data explorer
# -----------------------------------------------------------------
with st.expander("🔍 View raw filtered sales data"):
    st.dataframe(sales_f, use_container_width=True)

st.caption(
    "Data is synthetic sample data generated for portfolio purposes — "
    "see README for how to swap in real POS/labor exports."
)
