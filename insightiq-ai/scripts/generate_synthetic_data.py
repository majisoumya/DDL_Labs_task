"""Synthetic Retail E-Commerce Dataset Generator for InsightIQ AI.

Generates realistic CSV datasets matching the target schema:
- customers.csv (100 customers)
- products.csv (30 products across 5 categories)
- orders.csv (500 orders spanning 2024-01 to 2024-06, including revenue drop trends)
- order_items.csv (1,200 line items)
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
import pandas as pd


def generate_synthetic_data(output_dir: str | Path, seed: int = 42) -> dict[str, Path]:
    """Generates synthetic datasets in the specified directory."""
    random.seed(seed)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Customers
    cities = [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin",
        "San Jose", "Seattle", "Denver", "Boston", "Atlanta"
    ]
    first_names = [
        "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
        "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
        "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
        "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra"
    ]
    last_names = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
        "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White"
    ]

    base_customer_date = datetime(2023, 6, 1, 9, 0, 0)
    customers_data = []
    for cid in range(1, 101):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        name = f"{fn} {ln}"
        email = f"{fn.lower()}.{ln.lower()}{cid}@example.com"
        city = random.choice(cities)
        created_at = base_customer_date + timedelta(days=random.randint(0, 300), hours=random.randint(0, 23))
        customers_data.append({
            "customer_id": cid,
            "name": name,
            "email": email,
            "city": city,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    # Add 1 slight data quirk: 1 customer with untrimmed city whitespace
    customers_data[10]["city"] = "  Seattle  "

    df_customers = pd.DataFrame(customers_data)
    cust_file = out_path / "customers.csv"
    df_customers.to_csv(cust_file, index=False)

    # 2. Products
    product_catalog = [
        # Electronics
        ("Noise-Canceling Headphones", "Electronics", 199.99, 150),
        ("Mechanical Gaming Keyboard", "Electronics", 89.99, 200),
        ("4K Ultra HD Monitor 27-inch", "Electronics", 349.99, 80),
        ("Ergonomic Wireless Mouse", "Electronics", 49.99, 250),
        ("USB-C Multi-Port Hub", "Electronics", 39.99, 300),
        ("Smart Fitness Watch", "Electronics", 149.99, 120),
        ("Portable Bluetooth Speaker", "Electronics", 59.99, 180),
        # Apparel
        ("Classic Cotton Crewneck T-Shirt", "Apparel", 24.99, 500),
        ("Slim-Fit Denim Jeans", "Apparel", 59.99, 300),
        ("Waterproof Hooded Rain Jacket", "Apparel", 119.99, 140),
        ("Breathable Athletic Running Shoes", "Apparel", 89.99, 220),
        ("Merino Wool Knit Sweater", "Apparel", 79.99, 160),
        ("Canvas Everyday Backpack", "Apparel", 45.00, 210),
        # Home & Kitchen
        ("Stainless Steel French Press", "Home & Kitchen", 34.99, 180),
        ("Cast Iron Skillet 12-inch", "Home & Kitchen", 42.50, 150),
        ("Electric Gooseneck Kettle", "Home & Kitchen", 54.99, 110),
        ("Ceramic Non-Stick Chef Pan", "Home & Kitchen", 64.99, 130),
        ("Vacuum Insulated Water Bottle 32oz", "Home & Kitchen", 29.99, 400),
        ("Smart LED Desk Lamp", "Home & Kitchen", 39.99, 190),
        # Books
        ("Designing Data-Intensive Applications", "Books", 44.99, 250),
        ("Fluent Python 2nd Edition", "Books", 52.00, 190),
        ("Machine Learning Systems in Production", "Books", 49.50, 175),
        ("Clean Architecture and Design", "Books", 38.00, 220),
        ("The Pragmatic Programmer 20th Anniv", "Books", 42.00, 260),
        # Sports & Outdoors
        ("High-Density Yoga Mat with Strap", "Sports", 28.50, 240),
        ("Adjustable Neoprene Dumbbell Set", "Sports", 74.99, 90),
        ("Hydro Carbon Trekking Poles", "Sports", 49.99, 115),
        ("Insulated Double-Wall Camping Mug", "Sports", 19.99, 310),
        ("Quick-Dry Microfiber Sports Towel", "Sports", 14.99, 350),
        ("Waterproof Bike Pannier Bag", "Sports", 69.99, 85),
    ]

    products_data = []
    for pid, (pname, cat, price, stock) in enumerate(product_catalog, start=1):
        products_data.append({
            "product_id": pid,
            "product_name": pname,
            "category": cat,
            "price": float(price),
            "stock": stock,
        })
    df_products = pd.DataFrame(products_data)
    prod_file = out_path / "products.csv"
    df_products.to_csv(prod_file, index=False)

    # 3. Orders (2024-01-01 to 2024-06-30)
    # Notice: To support Phase 12 (Why did revenue decline last month?), we design a drop in May 2024 vs April 2024:
    # Jan: 80 orders, Feb: 85 orders, Mar: 90 orders, Apr: 110 orders (peak), May: 65 orders (decline!), Jun: 70 orders
    orders_data = []
    month_distribution = [
        (1, 80),   # Jan 2024
        (2, 85),   # Feb 2024
        (3, 90),   # Mar 2024
        (4, 110),  # Apr 2024 (Peak month)
        (5, 65),   # May 2024 (Decline month)
        (6, 70),   # Jun 2024
    ]

    statuses = ["completed"] * 82 + ["pending"] * 8 + ["cancelled"] * 7 + ["returned"] * 3
    order_id = 1

    for month, count in month_distribution:
        start_m = datetime(2024, month, 1)
        for _ in range(count):
            day_offset = random.randint(0, 27)
            order_dt = start_m + timedelta(days=day_offset, hours=random.randint(8, 21), minutes=random.randint(0, 59))
            cust_id = random.randint(1, 100)
            status = random.choice(statuses)

            orders_data.append({
                "order_id": order_id,
                "customer_id": cust_id,
                "order_date": order_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "status": status,
            })
            order_id += 1

    df_orders = pd.DataFrame(orders_data)
    ord_file = out_path / "orders.csv"
    df_orders.to_csv(ord_file, index=False)

    # 4. Order Items
    order_items_data = []
    item_id = 1
    prod_price_map = {p["product_id"]: p["price"] for p in products_data}

    for ord_entry in orders_data:
        oid = ord_entry["order_id"]
        # 1 to 4 items per order
        num_items = random.choices([1, 2, 3, 4], weights=[40, 35, 18, 7])[0]
        selected_prods = random.sample(range(1, 31), num_items)

        for pid in selected_prods:
            qty = random.choices([1, 2, 3, 4], weights=[65, 22, 9, 4])[0]
            unit_price = prod_price_map[pid]
            order_items_data.append({
                "item_id": item_id,
                "order_id": oid,
                "product_id": pid,
                "quantity": qty,
                "unit_price": unit_price,
            })
            item_id += 1

    # Include 1 duplicate row test case at the end to verify profiler detects duplicates
    df_order_items = pd.DataFrame(order_items_data)
    # Add a duplicate of row 0 with identical item_id or duplicate entry
    duplicate_row = df_order_items.iloc[0:1].copy()
    df_order_items_with_dup = pd.concat([df_order_items, duplicate_row], ignore_index=True)

    items_file = out_path / "order_items.csv"
    df_order_items_with_dup.to_csv(items_file, index=False)

    return {
        "customers": cust_file,
        "products": prod_file,
        "orders": ord_file,
        "order_items": items_file,
    }


if __name__ == "__main__":
    import sys
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "data/raw"
    created = generate_synthetic_data(out_dir)
    print(f"Generated {len(created)} datasets in {out_dir}:")
    for k, v in created.items():
        print(f"  - {k}: {v}")
