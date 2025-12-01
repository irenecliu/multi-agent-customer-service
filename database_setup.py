import sqlite3
from pathlib import Path

from db import DATA_DIR, DB_PATH


CUSTOMERS = [
    (1, "Alice Carter", "alice@example.com", "555-1000", "active"),
    (2, "Ben Smith", "ben@example.com", "555-2000", "disabled"),
    (3, "Carla Gomez", "carla@example.com", "555-3000", "active"),
    (4, "Derek Yang", "derek@example.com", "555-4000", "active"),
    (5, "Elena Novak", "elena@example.com", "555-5000", "active"),
    (12345, "Pat Premium", "pat.premium@example.com", "555-1234", "active"),
]

TICKETS = [
    (1, 1, "Password reset assistance", "resolved", "low"),
    (2, 3, "App keeps crashing on login", "open", "high"),
    (3, 4, "Refund pending for last order", "in_progress", "medium"),
    (4, 5, "Urgent: Payment failed and account locked", "open", "high"),
    (5, 12345, "Upgrade request to premium plus", "open", "medium"),
    (6, 12345, "Billing inquiry: duplicate charge detected", "open", "high"),
]


def bootstrap_database(db_path: Path = DB_PATH, reset_existing: bool = True) -> None:
    """
    Build the demo database from the dataset in this file.

    reset_existing=False will keep an existing DB intact; reset_existing=True recreates tables.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if db_path.exists() and not reset_existing:
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS tickets")
    cur.execute("DROP TABLE IF EXISTS customers")

    cur.execute(
        """
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            status TEXT CHECK(status IN ('active', 'disabled')) NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            issue TEXT NOT NULL,
            status TEXT CHECK(status IN ('open', 'in_progress', 'resolved')) NOT NULL DEFAULT 'open',
            priority TEXT CHECK(priority IN ('low', 'medium', 'high')) NOT NULL DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
        """
    )

    cur.executemany(
        "INSERT INTO customers (id, name, email, phone, status) VALUES (?, ?, ?, ?, ?)",
        CUSTOMERS,
    )
    cur.executemany(
        "INSERT INTO tickets (id, customer_id, issue, status, priority) VALUES (?, ?, ?, ?, ?)",
        TICKETS,
    )

    conn.commit()
    conn.close()
    print(f"Database initialized with {len(CUSTOMERS)} customers and {len(TICKETS)} tickets at {db_path}")


if __name__ == "__main__":
    bootstrap_database()
