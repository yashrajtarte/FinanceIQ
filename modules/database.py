"""
modules/database.py
====================
SQLite database initialisation and CRUD helpers.
All data is stored in `finance.db` in the project root.
"""

import sqlite3
import os
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "finance.db")


def get_conn() -> sqlite3.Connection:
    """Return a sqlite3 connection to the local database."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    """Create all required tables if they don't already exist."""
    conn = get_conn()
    cur = conn.cursor()

    # Assets table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT NOT NULL,
            name        TEXT NOT NULL,
            amount      REAL NOT NULL DEFAULT 0,
            created_at  TEXT DEFAULT (date('now'))
        )
    """)

    # Liabilities table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS liabilities (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT NOT NULL,
            name        TEXT NOT NULL,
            amount      REAL NOT NULL DEFAULT 0,
            created_at  TEXT DEFAULT (date('now'))
        )
    """)

    # Financial goals table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_name       TEXT NOT NULL,
            target_amount   REAL NOT NULL,
            current_saved   REAL DEFAULT 0,
            target_month    INTEGER DEFAULT 1,
            target_year     INTEGER,
            priority        TEXT DEFAULT 'medium',
            created_at      TEXT DEFAULT (date('now'))
        )
    """)

    # Snapshots table — snap_name is required
    cur.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            snap_name           TEXT NOT NULL DEFAULT '',
            snap_date           TEXT NOT NULL,
            total_assets        REAL,
            total_liabilities   REAL,
            net_worth           REAL
        )
    """)

    # Migrate: add snap_name to existing DBs that were created before this change
    try:
        cur.execute(
            "ALTER TABLE snapshots ADD COLUMN snap_name TEXT NOT NULL DEFAULT ''")
        conn.commit()
    except Exception:
        pass  # Column already exists — fine

    # Backfill any rows with empty snap_name → "Snapshot N"
    cur.execute(
        "SELECT id FROM snapshots WHERE snap_name = '' OR snap_name IS NULL ORDER BY id")
    unnamed = cur.fetchall()
    for seq, (row_id,) in enumerate(unnamed, start=1):
        cur.execute("UPDATE snapshots SET snap_name=? WHERE id=?",
                    (f"Snapshot {seq}", row_id))

    conn.commit()
    conn.close()


# ── Assets ────────────────────────────────────────────────────────────────────

def add_asset(category: str, name: str, amount: float):
    conn = get_conn()
    conn.execute(
        "INSERT INTO assets (category, name, amount) VALUES (?, ?, ?)",
        (category, name, amount),
    )
    conn.commit()
    conn.close()


def get_assets() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM assets ORDER BY category, name", conn)
    conn.close()
    return df


def update_asset(asset_id: int, category: str, name: str, amount: float):
    conn = get_conn()
    conn.execute(
        "UPDATE assets SET category=?, name=?, amount=? WHERE id=?",
        (category, name, amount, asset_id),
    )
    conn.commit()
    conn.close()


def delete_asset(asset_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM assets WHERE id=?", (asset_id,))
    conn.commit()
    conn.close()


# ── Liabilities ───────────────────────────────────────────────────────────────

def add_liability(category: str, name: str, amount: float):
    conn = get_conn()
    conn.execute(
        "INSERT INTO liabilities (category, name, amount) VALUES (?, ?, ?)",
        (category, name, amount),
    )
    conn.commit()
    conn.close()


def get_liabilities() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM liabilities ORDER BY category, name", conn)
    conn.close()
    return df


def update_liability(liability_id: int, category: str, name: str, amount: float):
    conn = get_conn()
    conn.execute(
        "UPDATE liabilities SET category=?, name=?, amount=? WHERE id=?",
        (category, name, amount, liability_id),
    )
    conn.commit()
    conn.close()


def delete_liability(liability_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM liabilities WHERE id=?", (liability_id,))
    conn.commit()
    conn.close()


# ── Goals ─────────────────────────────────────────────────────────────────────

def add_goal(goal_name: str, target_amount: float, current_saved: float,
             target_year: int, priority: str, target_month: int = 12):
    conn = get_conn()
    conn.execute(
        """INSERT INTO goals (goal_name, target_amount, current_saved, target_year, target_month, priority)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (goal_name, target_amount, current_saved,
         target_year, target_month, priority),
    )
    conn.commit()
    conn.close()


def get_goals() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM goals ORDER BY target_year", conn)
    conn.close()
    return df


def update_goal(goal_id: int, goal_name: str, target_amount: float,
                current_saved: float, target_year: int, target_month: int, priority: str):
    conn = get_conn()
    conn.execute(
        """UPDATE goals
           SET goal_name=?, target_amount=?, current_saved=?, target_year=?, target_month=?, priority=?
           WHERE id=?""",
        (goal_name, target_amount, current_saved,
         target_year, target_month, priority, goal_id),
    )
    conn.commit()
    conn.close()


def delete_goal(goal_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM goals WHERE id=?", (goal_id,))
    conn.commit()
    conn.close()


# ── Snapshots ─────────────────────────────────────────────────────────────────

def get_next_snapshot_number() -> int:
    """Return the next sequence number for auto-naming snapshots."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM snapshots")
    count = cur.fetchone()[0]
    conn.close()
    return count + 1


def save_snapshot(snap_name: str, total_assets: float,
                  total_liabilities: float, net_worth: float):
    from datetime import date
    conn = get_conn()
    conn.execute(
        """INSERT INTO snapshots (snap_name, snap_date, total_assets, total_liabilities, net_worth)
           VALUES (?, ?, ?, ?, ?)""",
        (snap_name.strip(), str(date.today()),
         total_assets, total_liabilities, net_worth),
    )
    conn.commit()
    conn.close()


def update_snapshot(snapshot_id: int, snap_name: str,
                    total_assets: float, total_liabilities: float, net_worth: float):
    conn = get_conn()
    conn.execute(
        """UPDATE snapshots
           SET snap_name=?, total_assets=?, total_liabilities=?, net_worth=?
           WHERE id=?""",
        (snap_name.strip(), total_assets, total_liabilities, net_worth, snapshot_id),
    )
    conn.commit()
    conn.close()


def delete_snapshot(snapshot_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM snapshots WHERE id=?", (snapshot_id,))
    conn.commit()
    conn.close()


def get_snapshots() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM snapshots ORDER BY snap_date", conn)
    conn.close()
    return df


# ── Seed example data ─────────────────────────────────────────────────────────

def seed_example_data():
    """Populate the database with sample data for demo / testing purposes."""
    conn = get_conn()
    conn.execute("DELETE FROM assets")
    conn.execute("DELETE FROM liabilities")
    conn.execute("DELETE FROM goals")
    conn.execute("DELETE FROM snapshots")
    conn.commit()
    conn.close()

    # Assets
    for cat, name, amt in [
        ("Cash", "Savings Account", 25000),
        ("Cash", "Checking Account", 5000),
        ("Investments", "Stock Portfolio", 45000),
        ("Investments", "Mutual Funds", 30000),
        ("Investments", "401(k) / PF", 80000),
        ("Property", "Primary Residence", 350000),
    ]:
        add_asset(cat, name, amt)

    # Liabilities
    for cat, name, amt in [
        ("Loan", "Home Mortgage", 220000),
        ("Loan", "Car Loan", 15000),
        ("Credit Card", "Visa Card", 3500),
        ("Credit Card", "MasterCard", 1200),
    ]:
        add_liability(cat, name, amt)

    # Goals
    for g in [
        ("Emergency Fund", 30000, 25000, 2025, "high", 6),
        ("Buy a House", 500000, 350000, 2027, "high", 3),
        ("Retirement", 1500000, 80000, 2045, "medium", 12),
        ("World Travel Fund", 20000, 5000, 2026, "low", 9),
    ]:
        # goal_name, target_amount, current_saved, target_year, priority, target_month
        add_goal(*g)

    # Snapshots — seeded with auto sequence names
    import datetime
    import random
    base_nw = 250000
    today = datetime.date.today()
    conn = get_conn()
    for i in range(12, 0, -1):
        seq = 12 - i + 1
        snap_date = (today - datetime.timedelta(days=30 * i)
                     ).strftime("%Y-%m-%d")
        nw = base_nw + random.uniform(-5000, 12000) * seq / 2
        assets_total = nw + random.uniform(230000, 250000)
        liabilities_total = assets_total - nw
        conn.execute(
            """INSERT INTO snapshots (snap_name, snap_date, total_assets, total_liabilities, net_worth)
               VALUES (?,?,?,?,?)""",
            (f"Snapshot {seq}", snap_date,
             round(assets_total, 2), round(liabilities_total, 2), round(nw, 2)),
        )
    conn.commit()
    conn.close()
