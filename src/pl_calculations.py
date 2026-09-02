"""
pl_calculations.py
-------------------
Core Profit & Loss calculation logic for the restaurant analysis project.
Loads raw sample data (sales, labor, overheads) and computes:
    - Revenue, COGS, Gross Profit, Gross Margin
    - Labor cost, allocated overhead, Operating Profit, Operating Margin
    - Item-level profitability rankings
    - Weekly and monthly rollups
    - A simple trend-based forecast for future revenue and labor cost

Designed so real POS/labor exports can be swapped in later with the
same column names (see data/README or the CSV headers).
"""
import os
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def load_data():
    """Load all raw CSVs into DataFrames."""
    menu = pd.read_csv(os.path.join(DATA_DIR, "menu.csv"))
    sales = pd.read_csv(os.path.join(DATA_DIR, "daily_sales.csv"), parse_dates=["date"])
    labor = pd.read_csv(os.path.join(DATA_DIR, "labor.csv"), parse_dates=["date"])
    overheads = pd.read_csv(os.path.join(DATA_DIR, "overheads.csv"))
    return menu, sales, labor, overheads


def add_revenue_cogs(sales: pd.DataFrame) -> pd.DataFrame:
    """Add per-row revenue and COGS columns to the sales data."""
    sales = sales.copy()
    sales["revenue_eur"] = sales["quantity_sold"] * sales["unit_price_eur"]
    sales["cogs_eur"] = sales["quantity_sold"] * sales["unit_cost_eur"]
    sales["gross_profit_eur"] = sales["revenue_eur"] - sales["cogs_eur"]
    return sales


def add_labor_cost(labor: pd.DataFrame) -> pd.DataFrame:
    labor = labor.copy()
    labor["labor_cost_eur"] = labor["total_staff_hours"] * labor["blended_wage_rate_eur"]
    return labor


def monthly_overhead_total(overheads: pd.DataFrame) -> float:
    return overheads["monthly_cost_eur"].sum()


def daily_pl(sales: pd.DataFrame, labor: pd.DataFrame, overheads: pd.DataFrame) -> pd.DataFrame:
    """Build a day-by-day P&L table."""
    sales = add_revenue_cogs(sales)
    labor = add_labor_cost(labor)

    daily_sales_agg = sales.groupby("date").agg(
        revenue_eur=("revenue_eur", "sum"),
        cogs_eur=("cogs_eur", "sum"),
    ).reset_index()

    daily = daily_sales_agg.merge(labor[["date", "labor_cost_eur"]], on="date", how="left")

    monthly_overhead = monthly_overhead_total(overheads)
    daily["overhead_eur"] = monthly_overhead / 30.44  # avg days/month allocation

    daily["gross_profit_eur"] = daily["revenue_eur"] - daily["cogs_eur"]
    daily["gross_margin_pct"] = daily["gross_profit_eur"] / daily["revenue_eur"]
    daily["operating_profit_eur"] = (
        daily["gross_profit_eur"] - daily["labor_cost_eur"] - daily["overhead_eur"]
    )
    daily["operating_margin_pct"] = daily["operating_profit_eur"] / daily["revenue_eur"]
    daily["labor_pct_of_revenue"] = daily["labor_cost_eur"] / daily["revenue_eur"]

    return daily.sort_values("date").reset_index(drop=True)


def weekly_pl(daily: pd.DataFrame) -> pd.DataFrame:
    """Roll the daily P&L up into ISO weeks."""
    df = daily.copy()
    df["week"] = df["date"].dt.to_period("W").apply(lambda p: p.start_time)
    weekly = df.groupby("week").agg(
        revenue_eur=("revenue_eur", "sum"),
        cogs_eur=("cogs_eur", "sum"),
        gross_profit_eur=("gross_profit_eur", "sum"),
        labor_cost_eur=("labor_cost_eur", "sum"),
        overhead_eur=("overhead_eur", "sum"),
        operating_profit_eur=("operating_profit_eur", "sum"),
    ).reset_index()
    weekly["gross_margin_pct"] = weekly["gross_profit_eur"] / weekly["revenue_eur"]
    weekly["operating_margin_pct"] = weekly["operating_profit_eur"] / weekly["revenue_eur"]
    weekly["labor_pct_of_revenue"] = weekly["labor_cost_eur"] / weekly["revenue_eur"]
    return weekly


def item_profitability(sales: pd.DataFrame) -> pd.DataFrame:
    """Rank menu items by total profit contribution and margin %."""
    sales = add_revenue_cogs(sales)
    by_item = sales.groupby(["item", "category"]).agg(
        units_sold=("quantity_sold", "sum"),
        revenue_eur=("revenue_eur", "sum"),
        cogs_eur=("cogs_eur", "sum"),
        gross_profit_eur=("gross_profit_eur", "sum"),
    ).reset_index()
    by_item["margin_pct"] = by_item["gross_profit_eur"] / by_item["revenue_eur"]
    by_item["pct_of_total_revenue"] = by_item["revenue_eur"] / by_item["revenue_eur"].sum()
    return by_item.sort_values("gross_profit_eur", ascending=False).reset_index(drop=True)


def weekday_pattern(sales: pd.DataFrame) -> pd.DataFrame:
    """Average revenue by day of week - useful for staffing/demand alignment."""
    sales = add_revenue_cogs(sales)
    df = sales.copy()
    df["weekday"] = df["date"].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    agg = df.groupby("weekday").agg(
        avg_daily_revenue_eur=("revenue_eur", "sum"),
    ).reindex(order)
    n_weeks = df["date"].dt.isocalendar().week.nunique()
    agg["avg_daily_revenue_eur"] = agg["avg_daily_revenue_eur"] / max(n_weeks, 1)
    return agg.reset_index()


def forecast_series(daily: pd.DataFrame, column: str, periods: int = 14) -> pd.DataFrame:
    """
    Simple trend-based forecast for a single daily column (e.g. revenue_eur,
    operating_profit_eur, labor_pct_of_revenue).

    Uses ordinary least squares (numpy.polyfit, degree 1) on day-index vs.
    the column's value, plus each weekday's average deviation from the
    overall daily mean, so the forecast keeps a weekly seasonality shape
    instead of a flat trend line. This is intentionally simple and
    transparent (no external forecasting library) - good enough to show
    direction and magnitude, not a substitute for a production forecasting
    model if this is ever pointed at real, longer-running data.

    Returns a DataFrame with columns: date, value, is_forecast
    """
    df = daily[["date", column]].dropna().sort_values("date").reset_index(drop=True)
    df["day_index"] = np.arange(len(df))
    df["weekday"] = df["date"].dt.day_name()

    # Linear trend
    slope, intercept = np.polyfit(df["day_index"], df[column], 1)

    # Weekday seasonality: average deviation from the trend line, per weekday
    df["trend_value"] = slope * df["day_index"] + intercept
    df["residual"] = df[column] - df["trend_value"]
    weekday_adj = df.groupby("weekday")["residual"].mean()

    last_date = df["date"].max()
    last_index = df["day_index"].max()

    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=periods, freq="D")
    future_indices = np.arange(last_index + 1, last_index + 1 + periods)
    future_weekdays = future_dates.day_name()

    future_trend = slope * future_indices + intercept
    future_adj = np.array([weekday_adj.get(wd, 0.0) for wd in future_weekdays])
    future_values = future_trend + future_adj

    # Never forecast a negative revenue/profit-like value below zero for display sanity
    if column in ("revenue_eur",):
        future_values = np.clip(future_values, a_min=0, a_max=None)

    history = pd.DataFrame({
        "date": df["date"], "value": df[column], "is_forecast": False,
    })
    forecast = pd.DataFrame({
        "date": future_dates, "value": future_values, "is_forecast": True,
    })
    return pd.concat([history, forecast], ignore_index=True)


if __name__ == "__main__":
    menu, sales, labor, overheads = load_data()
    daily = daily_pl(sales, labor, overheads)
    print(daily.head())
    fc = forecast_series(daily, "revenue_eur", periods=14)
    print(fc.tail(14))
