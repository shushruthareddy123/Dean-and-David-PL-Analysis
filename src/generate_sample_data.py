"""
generate_sample_data.py
------------------------
Generates synthetic, restaurant-style sample data (menu, daily sales,
labor, overheads) styled after a Dean & David outlet.

Run this once to (re)populate the /data folder:
    python src/generate_sample_data.py

NOTE: This is synthetic/illustrative data created for portfolio and
learning purposes. It is NOT real Dean & David financial data.
"""
import random
import csv
import os
from datetime import date, timedelta

random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------------------------------------------------------
# 1. Menu
# ---------------------------------------------------------------
menu = [
    ("Chicken Teriyaki Bowl", "Bowl", 9.90, 3.35),
    ("Falafel Power Bowl", "Bowl", 8.90, 2.70),
    ("Salmon Poke Bowl", "Bowl", 11.90, 4.50),
    ("Caesar Salad", "Salad", 8.50, 2.60),
    ("Greek Salad", "Salad", 7.90, 2.20),
    ("Beef Wrap", "Wrap", 8.90, 3.10),
    ("Veggie Wrap", "Wrap", 7.50, 2.00),
    ("Fresh Orange Juice", "Drink", 4.50, 1.20),
    ("Iced Matcha Latte", "Drink", 4.90, 1.30),
    ("Sparkling Water", "Drink", 2.90, 0.55),
]
weights = [22, 15, 12, 10, 8, 14, 9, 10, 8, 12]

with open(os.path.join(DATA_DIR, "menu.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["item", "category", "price_eur", "unit_cost_eur"])
    for item, cat, price, cost in menu:
        writer.writerow([item, cat, price, cost])

# ---------------------------------------------------------------
# 2. Daily sales for 60 days
# ---------------------------------------------------------------
start = date(2026, 5, 1)
n_days = 60

with open(os.path.join(DATA_DIR, "daily_sales.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["date", "item", "category", "quantity_sold", "unit_price_eur", "unit_cost_eur"])
    for d in range(n_days):
        the_date = start + timedelta(days=d)
        weekday = the_date.weekday()
        if weekday in (0, 1, 2, 3, 4):
            base_customers = random.randint(140, 190)
        else:
            base_customers = random.randint(90, 130)
        if weekday == 4:
            base_customers = int(base_customers * 1.1)

        for (item, cat, price, cost), w in zip(menu, weights):
            expected = base_customers * (w / sum(weights))
            qty = max(0, int(random.gauss(expected, expected * 0.18)))
            writer.writerow([the_date.isoformat(), item, cat, qty, price, cost])

# ---------------------------------------------------------------
# 3. Labor
# ---------------------------------------------------------------
base_wage = 13.50
with open(os.path.join(DATA_DIR, "labor.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["date", "total_staff_hours", "blended_wage_rate_eur"])
    for d in range(n_days):
        the_date = start + timedelta(days=d)
        weekday = the_date.weekday()
        if weekday in (0, 1, 2, 3, 4):
            hours = round(random.uniform(38, 46), 1)
        else:
            hours = round(random.uniform(28, 36), 1)
        wage = round(base_wage + random.uniform(-0.3, 0.8), 2)
        writer.writerow([the_date.isoformat(), hours, wage])

# ---------------------------------------------------------------
# 4. Overheads (fixed monthly assumptions)
# ---------------------------------------------------------------
overheads = [
    ("Rent", 4200.00),
    ("Utilities", 650.00),
    ("Franchise/License Fee", 900.00),
    ("Cleaning & Waste Disposal", 300.00),
    ("Insurance", 220.00),
    ("Miscellaneous/Admin", 180.00),
]
with open(os.path.join(DATA_DIR, "overheads.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["overhead_item", "monthly_cost_eur"])
    for name, val in overheads:
        writer.writerow([name, val])

print("Sample data generated in:", DATA_DIR)
