"""
create_bike_store_db.py

Usage:
    python create_bike_store_db.py                          # uses archive.zip and outputs bike_store.db in current dir
    python create_bike_store_db.py --zip path/to/archive.zip --out bike_store.db
"""

import sqlite3
import zipfile
import io
import csv
import argparse
from pathlib import Path


# ─── Schema (order matters for FK dependencies) ───────────────────────────────

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS brands (
    brand_id    INTEGER PRIMARY KEY,
    brand_name  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    category_id   INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    brand_id     INTEGER NOT NULL,
    category_id  INTEGER NOT NULL,
    model_year   INTEGER NOT NULL,
    list_price   REAL NOT NULL,
    FOREIGN KEY (brand_id)    REFERENCES brands(brand_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE IF NOT EXISTS stores (
    store_id   INTEGER PRIMARY KEY,
    store_name TEXT NOT NULL,
    phone      TEXT,
    email      TEXT,
    street     TEXT,
    city       TEXT,
    state      TEXT,
    zip_code   TEXT
);

CREATE TABLE IF NOT EXISTS staffs (
    staff_id   INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name  TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    phone      TEXT,
    active     INTEGER NOT NULL,
    store_id   INTEGER NOT NULL,
    manager_id INTEGER,
    FOREIGN KEY (store_id)   REFERENCES stores(store_id),
    FOREIGN KEY (manager_id) REFERENCES staffs(staff_id)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    phone       TEXT,
    email       TEXT NOT NULL,
    street      TEXT,
    city        TEXT,
    state       TEXT,
    zip_code    TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    order_id      INTEGER PRIMARY KEY,
    customer_id   INTEGER,
    order_status  INTEGER NOT NULL,
    order_date    TEXT NOT NULL,
    required_date TEXT NOT NULL,
    shipped_date  TEXT,
    store_id      INTEGER NOT NULL,
    staff_id      INTEGER NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (store_id)    REFERENCES stores(store_id),
    FOREIGN KEY (staff_id)    REFERENCES staffs(staff_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id   INTEGER NOT NULL,
    item_id    INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity   INTEGER NOT NULL,
    list_price REAL NOT NULL,
    discount   REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (order_id, item_id),
    FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS stocks (
    store_id   INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity   INTEGER,
    PRIMARY KEY (store_id, product_id),
    FOREIGN KEY (store_id)   REFERENCES stores(store_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
"""

# Load order: tables with no deps first, then dependents
LOAD_ORDER = [
    "brands",
    "categories",
    "products",
    "stores",
    "staffs",
    "customers",
    "orders",
    "order_items",
    "stocks",
]


def load_csv_from_zip(zf: zipfile.ZipFile, table_name: str) -> list[dict]:
    filename = f"{table_name}.csv"
    with zf.open(filename) as f:
        content = io.TextIOWrapper(f, encoding="utf-8")
        reader = csv.DictReader(content)
        return list(reader)


def insert_rows(conn: sqlite3.Connection, table: str, rows: list[dict]):
    if not rows:
        print(f"  ⚠️  No data found for {table}")
        return

    columns = rows[0].keys()
    placeholders = ", ".join(["?" for _ in columns])
    col_names = ", ".join(columns)
    sql = f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})"

    # Convert empty strings and literal "NULL" to None for nullable fields
    def clean(row):
        return [None if v in ("", "NULL", "null", "None") else v for v in row.values()]

    conn.executemany(sql, [clean(r) for r in rows])
    print(f"  ✅ {table}: {len(rows)} rows inserted")


def create_db(zip_path: str, output_path: str):
    print(f"\n📦 Reading: {zip_path}")
    print(f"💾 Output:  {output_path}\n")

    # Delete existing DB so we start fresh
    if Path(output_path).exists():
        Path(output_path).unlink()
        print("🗑️  Removed existing DB\n")

    conn = sqlite3.connect(output_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Create schema
    conn.executescript(SCHEMA)
    conn.commit()
    print("🏗️  Schema created\n")

    # Load data
    with zipfile.ZipFile(zip_path, "r") as zf:
        available = [Path(n).stem for n in zf.namelist() if n.endswith(".csv")]
        print(f"📄 CSVs found in zip: {available}\n")

        for table in LOAD_ORDER:
            if table not in available:
                print(f"  ⚠️  {table}.csv not found in zip, skipping")
                continue
            rows = load_csv_from_zip(zf, table)
            insert_rows(conn, table, rows)

    conn.commit()

    # Verify FK integrity
    print("\n🔍 Running FK integrity check...")
    issues = conn.execute("PRAGMA foreign_key_check").fetchall()
    if issues:
        print(f"  ❌ FK violations found: {issues}")
    else:
        print("  ✅ No FK violations — all references intact!")

    # Summary
    print("\n📊 Row counts:")
    for table in LOAD_ORDER:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:<15} {count:>6} rows")

    conn.close()
    print(f"\n🎉 Done! SQLite DB saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Bike Store Kaggle zip to SQLite DB")
    parser.add_argument("--zip", default="archive.zip", help="Path to archive.zip (default: archive.zip)")
    parser.add_argument("--out", default="bike_store.db", help="Output DB filename (default: bike_store.db)")
    args = parser.parse_args()

    create_db(args.zip, args.out)