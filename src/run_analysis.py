"""
run_analysis.py
-----------------
Main entry point. Loads the sample data, computes the full P&L,
saves summary CSVs, generates charts, and prints a plain-text
insights report to the console (and to outputs/insights_report.txt).

Usage:
    python src/run_analysis.py
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from pl_calculations import (
    load_data, daily_pl, weekly_pl, item_profitability, weekday_pattern
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
CHARTS_DIR = os.path.join(OUTPUT_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid")
GREEN = "#2F5233"
GOLD = "#C9A227"


def euro_fmt(ax, axis="y"):
    fmt = mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}")
    if axis == "y":
        ax.yaxis.set_major_formatter(fmt)
    else:
        ax.xaxis.set_major_formatter(fmt)


def chart_weekly_pl(weekly):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(weekly["week"], weekly["revenue_eur"], marker="o", label="Revenue", color=GREEN, linewidth=2)
    ax.plot(weekly["week"], weekly["operating_profit_eur"], marker="o", label="Operating Profit", color=GOLD, linewidth=2)
    ax.set_title("Weekly Revenue vs Operating Profit")
    ax.set_ylabel("EUR")
    euro_fmt(ax)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "weekly_revenue_vs_profit.png"), dpi=150)
    plt.close(fig)


def chart_item_margins(by_item):
    top = by_item.sort_values("margin_pct", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = [GREEN if v >= top["margin_pct"].median() else GOLD for v in top["margin_pct"]]
    ax.barh(top["item"], top["margin_pct"] * 100, color=colors)
    ax.set_xlabel("Gross Margin %")
    ax.set_title("Menu Item Gross Margin (%)")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "item_margin_ranking.png"), dpi=150)
    plt.close(fig)


def chart_item_profit_contribution(by_item):
    fig, ax = plt.subplots(figsize=(9, 5))
    top = by_item.sort_values("gross_profit_eur", ascending=False)
    ax.bar(top["item"], top["gross_profit_eur"], color=GREEN)
    ax.set_ylabel("Total Gross Profit (EUR)")
    ax.set_title("Total Gross Profit Contribution by Item (60-day period)")
    euro_fmt(ax)
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "item_profit_contribution.png"), dpi=150)
    plt.close(fig)


def chart_labor_pct(weekly):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(weekly["week"], weekly["labor_pct_of_revenue"] * 100, marker="o", color="#B23A48", linewidth=2)
    ax.axhline(30, color="gray", linestyle="--", linewidth=1, label="30% healthy-range guideline")
    ax.set_title("Labor Cost as % of Revenue (Weekly)")
    ax.set_ylabel("%")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "labor_pct_of_revenue.png"), dpi=150)
    plt.close(fig)


def chart_weekday_pattern(pattern):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(pattern["weekday"], pattern["avg_daily_revenue_eur"], color=GREEN)
    ax.set_title("Average Revenue by Day of Week")
    ax.set_ylabel("EUR")
    euro_fmt(ax)
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "weekday_revenue_pattern.png"), dpi=150)
    plt.close(fig)


def build_insights(daily, weekly, by_item, pattern):
    lines = []
    lines.append("DEAN & DAVID — SAMPLE P&L ANALYSIS: KEY INSIGHTS")
    lines.append("=" * 55)
    total_rev = daily["revenue_eur"].sum()
    total_op_profit = daily["operating_profit_eur"].sum()
    avg_gm = daily["gross_margin_pct"].mean()
    avg_om = daily["operating_margin_pct"].mean()
    avg_labor_pct = daily["labor_pct_of_revenue"].mean()

    lines.append(f"- Total revenue (60-day sample period): EUR {total_rev:,.2f}")
    lines.append(f"- Total operating profit: EUR {total_op_profit:,.2f}")
    lines.append(f"- Average gross margin: {avg_gm*100:.1f}%")
    lines.append(f"- Average operating margin: {avg_om*100:.1f}%")
    lines.append(f"- Average labor cost as % of revenue: {avg_labor_pct*100:.1f}%")
    lines.append("")

    best_item = by_item.iloc[0]
    worst_margin_item = by_item.sort_values("margin_pct").iloc[0]
    lines.append(f"- Top profit contributor: {best_item['item']} "
                 f"(EUR {best_item['gross_profit_eur']:,.2f} gross profit, "
                 f"{best_item['margin_pct']*100:.1f}% margin)")
    lines.append(f"- Lowest margin item: {worst_margin_item['item']} "
                 f"({worst_margin_item['margin_pct']*100:.1f}% margin) — "
                 f"consider a price review or cost renegotiation")
    lines.append("")

    best_day = pattern.sort_values("avg_daily_revenue_eur", ascending=False).iloc[0]
    worst_day = pattern.sort_values("avg_daily_revenue_eur").iloc[0]
    lines.append(f"- Highest average revenue day: {best_day['weekday']} "
                 f"(EUR {best_day['avg_daily_revenue_eur']:,.2f})")
    lines.append(f"- Lowest average revenue day: {worst_day['weekday']} "
                 f"(EUR {worst_day['avg_daily_revenue_eur']:,.2f}) — "
                 f"review staffing levels against this demand")
    lines.append("")

    peak_labor_week = weekly.sort_values("labor_pct_of_revenue", ascending=False).iloc[0]
    lines.append(f"- Week with highest labor-cost ratio: week of "
                 f"{peak_labor_week['week'].date()} "
                 f"({peak_labor_week['labor_pct_of_revenue']*100:.1f}% of revenue)")
    lines.append("")
    lines.append("NOTE: This analysis runs on synthetic/sample data generated for")
    lines.append("portfolio purposes. Replace the CSVs in /data with real exports")
    lines.append("(same column structure) to produce a live analysis.")
    return "\n".join(lines)


def main():
    menu, sales, labor, overheads = load_data()
    daily = daily_pl(sales, labor, overheads)
    weekly = weekly_pl(daily)
    by_item = item_profitability(sales)
    pattern = weekday_pattern(sales)

    # Save summary tables
    daily.to_csv(os.path.join(OUTPUT_DIR, "daily_pl_summary.csv"), index=False)
    weekly.to_csv(os.path.join(OUTPUT_DIR, "weekly_pl_summary.csv"), index=False)
    by_item.to_csv(os.path.join(OUTPUT_DIR, "item_profitability.csv"), index=False)

    # Charts
    chart_weekly_pl(weekly)
    chart_item_margins(by_item)
    chart_item_profit_contribution(by_item)
    chart_labor_pct(weekly)
    chart_weekday_pattern(pattern)

    # Insights report
    report = build_insights(daily, weekly, by_item, pattern)
    with open(os.path.join(OUTPUT_DIR, "insights_report.txt"), "w") as f:
        f.write(report)

    print(report)
    print("\nCharts saved to:", CHARTS_DIR)
    print("Summary CSVs saved to:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
