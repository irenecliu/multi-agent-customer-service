import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "customer_service.db"


def _connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def get_customer(customer_id: int, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    with closing(_connect(db_path)) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cur.fetchone()
        return _row_to_dict(row) if row else None


def list_customers(status: Optional[str] = None, limit: int = 10, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    with closing(_connect(db_path)) as conn, closing(conn.cursor()) as cur:
        if status:
            cur.execute(
                "SELECT * FROM customers WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            )
        else:
            cur.execute("SELECT * FROM customers ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        return [_row_to_dict(r) for r in rows]


def update_customer(customer_id: int, data: Dict[str, Any], db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    if not data:
        return get_customer(customer_id, db_path=db_path)

    valid_fields = {"name", "email", "phone", "status"}
    updates = {k: v for k, v in data.items() if k in valid_fields}
    if not updates:
        return get_customer(customer_id, db_path=db_path)

    columns = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [customer_id]
    with closing(_connect(db_path)) as conn, closing(conn.cursor()) as cur:
        cur.execute(f"UPDATE customers SET {columns}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
        conn.commit()
    return get_customer(customer_id, db_path=db_path)


def create_ticket(
    customer_id: int,
    issue: str,
    priority: str = "medium",
    status: str = "open",
    db_path: Path = DB_PATH,
) -> Dict[str, Any]:
    with closing(_connect(db_path)) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            """
            INSERT INTO tickets (customer_id, issue, status, priority, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (customer_id, issue, status, priority),
        )
        conn.commit()
        ticket_id = cur.lastrowid
        cur.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        return _row_to_dict(cur.fetchone())


def get_customer_history(customer_id: int, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    with closing(_connect(db_path)) as conn, closing(conn.cursor()) as cur:
        cur.execute(
            "SELECT * FROM tickets WHERE customer_id = ? ORDER BY created_at DESC",
            (customer_id,),
        )
        return [_row_to_dict(r) for r in cur.fetchall()]


def list_open_tickets(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    with closing(_connect(db_path)) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT * FROM tickets WHERE status != 'resolved' ORDER BY priority DESC, created_at DESC")
        return [_row_to_dict(r) for r in cur.fetchall()]
