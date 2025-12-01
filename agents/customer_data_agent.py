from typing import Dict, List, Optional

import db
from agents.base import Agent, AgentMessage


class CustomerDataAgent(Agent):
    """
    Specialist agent that wraps MCP data access tools.
    For the demo it calls the same functions used by the MCP server.
    """

    def __init__(self, logger, db_path: Optional[str] = None) -> None:
        super().__init__("customer-data-agent", logger)
        self.db_path = db_path

    def handle(self, message: AgentMessage) -> AgentMessage:
        intent = message.intent or "info"
        payload = message.payload or {}
        response_payload: Dict = {}
        content: str

        if intent == "get_customer":
            customer_id = int(payload["customer_id"])
            customer = db.get_customer(customer_id, db_path=self.db_path or db.DB_PATH)
            response_payload["customer"] = customer
            content = f"Customer {customer_id} fetched"
        elif intent == "list_customers":
            customers = db.list_customers(payload.get("status"), limit=payload.get("limit", 10), db_path=self.db_path or db.DB_PATH)
            response_payload["customers"] = customers
            content = f"Listed {len(customers)} customers"
        elif intent == "update_customer":
            updated = db.update_customer(payload["customer_id"], data=payload.get("data", {}), db_path=self.db_path or db.DB_PATH)
            response_payload["customer"] = updated
            content = f"Customer {payload['customer_id']} updated"
        elif intent == "create_ticket":
            ticket = db.create_ticket(
                payload["customer_id"],
                payload["issue"],
                priority=payload.get("priority", "medium"),
                status=payload.get("status", "open"),
                db_path=self.db_path or db.DB_PATH,
            )
            response_payload["ticket"] = ticket
            content = f"Ticket created for customer {payload['customer_id']}"
        elif intent == "get_history":
            history = db.get_customer_history(payload["customer_id"], db_path=self.db_path or db.DB_PATH)
            response_payload["history"] = history
            content = f"Fetched history for customer {payload['customer_id']}"
        else:
            content = f"Unknown intent: {intent}"

        reply = AgentMessage(
            sender=self.name,
            recipient=message.sender,
            content=content,
            intent=intent,
            payload=response_payload,
        )
        self.logger.record(reply)
        return reply

    def get_open_tickets_for_active_customers(self, priority: Optional[str] = None) -> List[dict]:
        """
        Helper used in multi-step coordination.
        """
        customers = db.list_customers(status="active", limit=100, db_path=self.db_path or db.DB_PATH)
        active_ids = {c["id"] for c in customers}
        tickets = db.list_open_tickets(db_path=self.db_path or db.DB_PATH)
        results = [t for t in tickets if t["customer_id"] in active_ids]
        if priority:
            results = [t for t in results if t.get("priority") == priority]
        return results
