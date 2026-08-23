"""
app.py — Interactive P&L Dashboard
------------------------------------
Streamlit dashboard for the Dean & David restaurant P&L analysis
project. Reads the same /data CSVs used by src/pl_calculations.py
and renders an interactive, filterable, narrative-driven view.

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
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "src"))

from pl_calculations import (  # noqa: E402
    load_data, daily_pl, weekly_pl, item_profitability, weekday_pattern
)

st.set_page_config(
    page_title="Dean & David — P&L Analysis",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===================================================================
# DESIGN TOKENS
# ===================================================================
INK = "#2B2B26"
INK_SOFT = "#55554C"
CREAM = "#FAF7F0"
CARD = "#FFFFFF"
GREEN = "#1F3D2B"
GREEN_SOFT = "rgba(31,61,43,0.35)"
GREEN_FAINT = "rgba(31,61,43,0.15)"
GOLD = "#C9A227"
CLAY = "#C1502E"
SAGE = "#8FA688"

FONT_DISPLAY = "'Fraunces', Georgia, serif"
FONT_BODY = "'Inter', -apple-system, sans-serif"
FONT_MONO = "'IBM Plex Mono', ui-monospace, monospace"

# ===================================================================
# GLOBAL CSS + FONT IMPORT
# ===================================================================
st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>
    .stApp {{
        background-color: {CREAM};
    }}
    html, body, [class*="css"] {{
        font-family: {FONT_BODY};
        color: {INK} !important;
    }}
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stText,
    p, span, li, label, h1, h2, h3, h4, h5, h6,
    .stDateInput label, .stMultiSelect label {{
        color: {INK} !important;
    }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

    .block-container {{
        padding-top: 2.2rem;
        padding-bottom: 3rem;
        max-width: 1180px;
    }}

    .eyebrow {{
        font-family: {FONT_MONO};
        font-size: 12px;
        letter-spacing: 2.5px;
        color: {GREEN};
        text-transform: uppercase;
        margin-bottom: 8px;
        font-weight: 500;
    }}
    .hero-title {{
        font-family: {FONT_DISPLAY};
        font-weight: 600;
        font-size: 44px;
        line-height: 1.18;
        color: {GREEN};
        margin: 0 0 16px 0;
        max-width: 760px;
    }}
    .hero-title .accent {{ color: {CLAY}; font-style: italic; }}
    .hero-sub {{
        font-family: {FONT_BODY};
        font-size: 16.5px;
        color: {INK_SOFT};
        max-width: 620px;
        line-height: 1.6;
        margin-bottom: 6px;
    }}

    .section-eyebrow {{
        font-family: {FONT_MONO};
        font-size: 12px;
        letter-spacing: 2.5px;
        color: {GREEN};
        text-transform: uppercase;
        margin: 8px 0 2px 0;
        font-weight: 500;
    }}
    .section-title {{
        font-family: {FONT_DISPLAY};
        font-weight: 600;
        font-size: 26px;
        color: {INK};
        margin: 0 0 6px 0;
    }}
    .section-rule {{
        border: none;
        border-top: 1px solid {GREEN_FAINT};
        margin: 34px 0 22px 0;
    }}

    .receipt {{
        background: {CARD};
        border: 1px solid {GREEN_FAINT};
        box-shadow: 0 2px 0 rgba(31,61,43,0.05);
        max-width: 480px;
        margin: 18px 0 8px 0;
    }}
    .receipt-head {{
        padding: 18px 26px 12px 26px;
        border-bottom: 1px dashed {GREEN_SOFT};
        font-family: {FONT_MONO};
        font-size: 12.5px;
        letter-spacing: 1.5px;
        color: {GREEN};
        text-transform: uppercase;
        font-weight: 500;
    }}
    .receipt-row {{
        display: flex;
        justify-content: space-between;
        padding: 10px 26px;
        font-family: {FONT_MONO};
        font-size: 14px;
        border-bottom: 1px dotted {GREEN_FAINT};
    }}
    .receipt-row.total {{
        border-bottom: none;
        border-top: 1px solid {GREEN_SOFT};
        font-weight: 600;
        padding-top: 13px;
        padding-bottom: 13px;
    }}
    .receipt-label {{ color: {INK_SOFT}; }}
    .receipt-value {{ color: {GREEN}; font-weight: 600; }}
    .receipt-value.bad {{ color: {CLAY}; }}
    .receipt-foot {{
        text-align: center;
        padding: 9px;
        font-family: {FONT_MONO};
        font-size: 9.5px;
        letter-spacing: 2px;
        color: rgba(31,61,43,0.35);
    }}

    .note {{
        max-width: 480px;
        background: #FFFDF6;
        border-left: 4px solid {GOLD};
        padding: 16px 20px;
        margin: 22px 0 8px 0;
        font-family: {FONT_BODY};
        font-size: 14.5px;
        line-height: 1.6;
        color: #3A3A32;
    }}
    .note-label {{
        font-family: {FONT_MONO};
        font-size: 10.5px;
        letter-spacing: 1.5px;
        color: {GOLD};
        text-transform: uppercase;
        display: block;
        margin-bottom: 8px;
        font-weight: 600;
    }}

    div[data-testid="stMetric"] {{
        background: {CARD};
        border: 1px solid {GREEN_FAINT};
        padding: 14px 18px 12px 18px;
        border-radius: 2px;
    }}
    div[data-testid="stMetricLabel"] {{
        font-family: {FONT_MONO} !important;
        font-size: 11.5px !important;
        letter-spacing: 1px;
        color: {INK_SOFT} !important;
        text-transform: uppercase;
    }}
    div[data-testid="stMetricValue"] {{
        font-family: {FONT_DISPLAY} !important;
        color: {GREEN} !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: #F2EEE4;
        border-right: 1px solid {GREEN_FAINT};
    }}
    section[data-testid="stSidebar"] .eyebrow {{ margin-top: 6px; }}

    .streamlit-expanderHeader {{
        font-family: {FONT_MONO};
        font-size: 13px;
        color: {GREEN};
    }}

    .footnote {{
        font-family: {FONT_MONO};
        font-size: 11.5px;
        color: rgba(43,43,38,0.45);
        margin-top: 10px;
    }}
</style>
""", unsafe_allow_html=True)


def plotly_theme(fig, height=380):
    fig.update_layout(
        font=dict(family=FONT_BODY, color=INK, size=13),
        plot_bgcolor=CARD,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=28, b=10, l=10, r=10),
        height=height,
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=12)),
    )
    fig.update_xaxes(showgrid=False, linecolor=GREEN_FAINT)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(31,61,43,0.08)", linecolor=GREEN_FAINT)
    return fig


@st.cache_data
def get_data():
    menu, sales, labor, overheads = load_data()
    daily = daily_pl(sales, labor, overheads)
    weekly = weekly_pl(daily)
    by_item = item_profitability(sales)
    pattern = weekday_pattern(sales)
    return menu, sales, labor, overheads, daily, weekly, by_item, pattern


menu, sales, labor, overheads, daily, weekly, by_item, pattern = get_data()

total_rev_all = daily["revenue_eur"].sum()
total_cogs_all = daily["cogs_eur"].sum()
total_gp_all = daily["gross_profit_eur"].sum()
total_labor_all = daily["labor_cost_eur"].sum()
total_oh_all = daily["overhead_eur"].sum()
total_op_all = daily["operating_profit_eur"].sum()
avg_gm_all = daily["gross_margin_pct"].mean()
avg_om_all = daily["operating_margin_pct"].mean()
avg_labor_pct_all = daily["labor_pct_of_revenue"].mean()

# ===================================================================
# HERO
# ===================================================================
st.markdown('<div class="eyebrow">Dean &amp; David — 60-day sample analysis</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-title">Strong margins. Thin profit.<br>'
    '<span class="accent">Here\'s where it\'s leaking.</span></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="hero-sub">A full P&L pipeline built from raw sales, labor, and overhead '
    'data — structured to mirror a real POS export from a fast-casual restaurant. '
    'Filter below to explore any window of the 60-day period.</div>',
    unsafe_allow_html=True,
)

rc1, rc2 = st.columns([1, 1], gap="large")

with rc1:
    st.markdown(f"""
    <div class="receipt">
        <div class="receipt-head">P &amp; L — Full Period Summary</div>
        <div class="receipt-row"><span class="receipt-label">Revenue</span><span class="receipt-value">€{total_rev_all:,.2f}</span></div>
        <div class="receipt-row"><span class="receipt-label">COGS</span><span class="receipt-value">−€{total_cogs_all:,.2f}</span></div>
        <div class="receipt-row"><span class="receipt-label">Gross profit ({avg_gm_all*100:.1f}%)</span><span class="receipt-value">€{total_gp_all:,.2f}</span></div>
        <div class="receipt-row"><span class="receipt-label">Labor ({avg_labor_pct_all*100:.1f}% of rev)</span><span class="receipt-value bad">−€{total_labor_all:,.2f}</span></div>
        <div class="receipt-row"><span class="receipt-label">Overhead</span><span class="receipt-value">−€{total_oh_all:,.2f}</span></div>
        <div class="receipt-row total"><span class="receipt-label">Operating profit ({avg_om_all*100:.1f}%)</span><span class="receipt-value">€{total_op_all:,.2f}</span></div>
        <div class="receipt-foot">* * * synthetic sample data * * *</div>
    </div>
    """, unsafe_allow_html=True)

with rc2:
    narrative_text = None
    narrative_path = os.path.join(BASE_DIR, "outputs", "ai_generated_insights.md")
    if os.path.exists(narrative_path):
        with open(narrative_path) as f:
            content = f.read()
        parts = content.split("\n\n", 2)
        narrative_text = parts[-1].strip() if len(parts) > 1 else content

    if not narrative_text:
        narrative_text = (
            f"Labor cost is running {(avg_labor_pct_all*100 - 30):.1f} points above the "
            f"30% guideline and is the main reason gross margin isn't reaching the bottom "
            f"line. Start by reviewing staffing against the weekday demand curve below."
        )

    st.markdown(f"""
    <div class="note">
        <span class="note-label">Manager's note — AI-generated</span>
        {narrative_text}
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
        '<div class="footnote">Generated'
        'from the computed metrics — see README.</div>',
        unsafe_allow_html=True,
    )

# ===================================================================
# SIDEBAR FILTERS
# ===================================================================
st.sidebar.markdown('<div class="eyebrow">Filter the data</div>', unsafe_allow_html=True)
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

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<div class="footnote">Data is synthetic, generated to mirror a real '
    'POS + labor export. See README for how to point this at real data.</div>',
    unsafe_allow_html=True,
)

mask_daily = (daily["date"].dt.date >= start_d) & (daily["date"].dt.date <= end_d)
daily_f = daily.loc[mask_daily]

mask_sales = (
    (sales["date"].dt.date >= start_d)
    & (sales["date"].dt.date <= end_d)
    & (sales["category"].isin(selected_categories))
)
sales_f = sales.loc[mask_sales]
by_item_f = item_profitability(sales_f) if len(sales_f) else by_item.iloc[0:0]

# ===================================================================
# FILTERED KPI ROW
# ===================================================================
st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
st.markdown('<div class="section-eyebrow">01 — filtered view</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Your selected window</div>', unsafe_allow_html=True)

total_rev = daily_f["revenue_eur"].sum()
total_op_profit = daily_f["operating_profit_eur"].sum()
avg_gm = daily_f["gross_margin_pct"].mean() if len(daily_f) else 0
avg_labor_pct = daily_f["labor_pct_of_revenue"].mean() if len(daily_f) else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Revenue", f"€{total_rev:,.0f}")
k2.metric("Operating profit", f"€{total_op_profit:,.0f}")
k3.metric("Gross margin", f"{avg_gm*100:.1f}%")
k4.metric("Labor % of revenue", f"{avg_labor_pct*100:.1f}%",
          delta=f"{(avg_labor_pct-0.30)*100:+.1f} pts vs 30% guideline", delta_color="inverse")

# ===================================================================
# SECTION: TREND
# ===================================================================
st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
st.markdown('<div class="section-eyebrow">02 — the trend</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Revenue holds. Profit doesn\'t follow.</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

weekly_f = weekly[(weekly["week"].dt.date >= start_d) & (weekly["week"].dt.date <= end_d)]

with col1:
    st.markdown("**Weekly revenue vs. operating profit**")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=weekly_f["week"], y=weekly_f["revenue_eur"],
                              mode="lines+markers", name="Revenue",
                              line=dict(color=GREEN, width=3), marker=dict(size=6)))
    fig.add_trace(go.Scatter(x=weekly_f["week"], y=weekly_f["operating_profit_eur"],
                              mode="lines+markers", name="Operating profit",
                              line=dict(color=GOLD, width=3), marker=dict(size=6)))
    fig.update_layout(yaxis_title="EUR")
    st.plotly_chart(plotly_theme(fig), use_container_width=True)

with col2:
    st.markdown("**Labor cost as % of revenue**")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=weekly_f["week"], y=weekly_f["labor_pct_of_revenue"] * 100,
                               mode="lines+markers", name="Labor %",
                               line=dict(color=CLAY, width=3), marker=dict(size=6)))
    fig2.add_hline(y=30, line_dash="dot", line_color=INK_SOFT,
                   annotation_text="30% guideline", annotation_font_size=11)
    fig2.update_layout(yaxis_title="%")
    st.plotly_chart(plotly_theme(fig2), use_container_width=True)

# ===================================================================
# SECTION: MENU
# ===================================================================
st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
st.markdown('<div class="section-eyebrow">03 — the menu</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Which items actually make money</div>', unsafe_allow_html=True)

col3, col4 = st.columns(2, gap="large")

with col3:
    st.markdown("**Gross margin by item**")
    if len(by_item_f):
        top = by_item_f.sort_values("margin_pct", ascending=True)
        colors = [CLAY if v < 0.65 else (GOLD if v < 0.73 else GREEN) for v in top["margin_pct"]]
        fig3 = go.Figure(go.Bar(
            x=top["margin_pct"] * 100, y=top["item"], orientation="h",
            marker_color=colors,
        ))
        fig3.update_layout(xaxis_title="Gross margin %")
        st.plotly_chart(plotly_theme(fig3, height=360), use_container_width=True)
    else:
        st.info("No data for selected filters.")

with col4:
    st.markdown("**Total gross profit contribution**")
    if len(by_item_f):
        top2 = by_item_f.sort_values("gross_profit_eur", ascending=False)
        fig4 = go.Figure(go.Bar(x=top2["item"], y=top2["gross_profit_eur"], marker_color=GREEN))
        fig4.update_layout(yaxis_title="EUR")
        fig4.update_xaxes(tickangle=-40)
        st.plotly_chart(plotly_theme(fig4, height=360), use_container_width=True)
    else:
        st.info("No data for selected filters.")

# ===================================================================
# SECTION: DEMAND PATTERN
# ===================================================================
st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
st.markdown('<div class="section-eyebrow">04 — the calendar</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Demand doesn\'t match staffing</div>', unsafe_allow_html=True)

pattern_f = weekday_pattern(sales_f) if len(sales_f) else pattern.iloc[0:0]
if len(pattern_f):
    colors5 = [GOLD if d == "Friday" else (CLAY if d == "Saturday" else GREEN) for d in pattern_f["weekday"]]
    fig5 = go.Figure(go.Bar(x=pattern_f["weekday"], y=pattern_f["avg_daily_revenue_eur"], marker_color=colors5))
    fig5.update_layout(yaxis_title="Average revenue (EUR)")
    st.plotly_chart(plotly_theme(fig5, height=340), use_container_width=True)
else:
    st.info("No data for selected filters.")

# ===================================================================
# RAW DATA
# ===================================================================
st.markdown('<hr class="section-rule">', unsafe_allow_html=True)
with st.expander("🔍 View raw filtered sales data"):
    st.dataframe(sales_f, use_container_width=True)

st.markdown(
    '<div class="footnote">Data is synthetic sample data generated for portfolio '
    'purposes — see README for how to swap in real POS/labor exports.</div>',
    unsafe_allow_html=True,
)
