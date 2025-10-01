#!/usr/bin/env python3
"""
Quick SQLite inspector for ARTGRID.

- Lists tables
- Shows row counts per table
- Prints a few sample rows from each table
- Verifies foreign-keys setting
"""

import sqlite3
from textwrap import shorten

DB_PATH = "instance/artgrid.db"
SAMPLE_LIMIT = 10  # how many rows to preview per table

TABLES = {
    "user": [
        "id", "full_name", "email", "role", "verification_status", "created_at"
    ],
    "artwork": [
        "id", "user_id", "title", "status", "likes_count", "views_count",
        "is_featured", "submission_date", "approval_date"
    ],
    "like": [
        "id", "user_id", "artwork_id", "timestamp"
    ],
    "comment": [
        "id", "user_id", "artwork_id", "content", "timestamp", "is_flagged"
    ],
    "moderation": [
        "id", "artwork_id", "moderator_id", "action", "feedback", "timestamp"
    ],
}

def table_exists(cur, name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,))
    return cur.fetchone() is not None

def count_rows(cur, name: str) -> int:
    cur.execute(f"SELECT COUNT(*) FROM {name};")
    return cur.fetchone()[0]

def preview_rows(cur, name: str, cols: list[str], limit: int = SAMPLE_LIMIT):
    sel = ", ".join(cols)
    cur.execute(f"SELECT {sel} FROM {name} ORDER BY ROWID DESC LIMIT ?;", (limit,))
    rows = cur.fetchall()
    return rows

def print_section(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def main():
    print_section(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Check foreign keys
    cur.execute("PRAGMA foreign_keys;")
    fk = cur.fetchone()[0]
    print(f"Foreign keys enabled: {bool(fk)} (0 = off, 1 = on)")
    if not fk:
        print("TIP: You can enable them at runtime via: PRAGMA foreign_keys = ON;")

    # List all tables
    print_section("Tables present")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    all_tables = [r[0] for r in cur.fetchall()]
    if not all_tables:
        print("No tables found. Start your Flask app once so it can create them.")
        return
    for t in all_tables:
        print(f"- {t}")

    # Per-table details (only for known app tables)
    for tname, cols in TABLES.items():
        print_section(f"Table: {tname}")
        if not table_exists(cur, tname):
            print(f"(missing) — this table does not exist yet.")
            continue

        # Show DDL
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (tname,))
        ddl = cur.fetchone()
        if ddl and ddl["sql"]:
            print("Schema:")
            print(ddl["sql"])

        # Row count
        total = count_rows(cur, tname)
        print(f"\nRow count: {total}")

        # Preview rows
        if total > 0:
            print(f"\nLast {min(SAMPLE_LIMIT, total)} rows:")
            rows = preview_rows(cur, tname, cols)
            for r in rows:
                # pretty-print with truncated long fields
                line = []
                for c in cols:
                    val = r[c] if c in r.keys() else None
                    if isinstance(val, str):
                        val = shorten(val, width=80, placeholder="…")
                    line.append(f"{c}={val}")
                print("  - " + " | ".join(line))
        else:
            print("No data to preview.")

    conn.close()
    print_section("Done")

if __name__ == "__main__":
    main()
