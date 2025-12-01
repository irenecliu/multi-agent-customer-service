from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

import db
from database_setup import bootstrap_database


# Ensure the dataset from database_setup.py is available before serving.
bootstrap_database(reset_existing=False)
server = FastMCP("customer-data-mcp")


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


@server.tool()
def get_customer(customer_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch a single customer by ID.
    """
    path = db.DB_PATH if db_path is None else db_path
    record = db.get_customer(customer_id, db_path=path)
    return {k: _json_safe(v) for k, v in record.items()} if record else None


@server.tool()
def list_customers(status: Optional[str] = None, limit: int = 10, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List customers, optionally filtered by status.
    """
    path = db.DB_PATH if db_path is None else db_path
    rows = db.list_customers(status=status, limit=limit, db_path=path)
    return [{k: _json_safe(v) for k, v in row.items()} for row in rows]


@server.tool()
def update_customer(customer_id: int, data: Dict[str, Any], db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Update editable customer fields (name, email, phone, status).
    """
    path = db.DB_PATH if db_path is None else db_path
    record = db.update_customer(customer_id, data=data, db_path=path)
    return {k: _json_safe(v) for k, v in record.items()} if record else None


@server.tool()
def create_ticket(
    customer_id: int,
    issue: str,
    priority: str = "medium",
    status: str = "open",
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new ticket for a customer.
    """
    path = db.DB_PATH if db_path is None else db_path
    ticket = db.create_ticket(customer_id, issue, priority=priority, status=status, db_path=path)
    return {k: _json_safe(v) for k, v in ticket.items()}


@server.tool()
def get_customer_history(customer_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all tickets for a given customer, newest first.
    """
    path = db.DB_PATH if db_path is None else db_path
    history = db.get_customer_history(customer_id, db_path=path)
    return [{k: _json_safe(v) for k, v in ticket.items()} for ticket in history]


if __name__ == "__main__":
    server.run()
