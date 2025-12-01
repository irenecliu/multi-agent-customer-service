import re
from typing import Dict, List, Optional, Tuple

from agents.base import Agent, AgentMessage, AgentLogger
from agents.customer_data_agent import CustomerDataAgent
from agents.support_agent import SupportAgent


class RouterAgent(Agent):
    """
    Orchestrates intent detection, task allocation, negotiation, and multi-step flows.
    """

    def __init__(self, logger: AgentLogger, data_agent: CustomerDataAgent, support_agent: SupportAgent) -> None:
        super().__init__("router-agent", logger)
        self.data_agent = data_agent
        self.support_agent = support_agent

    def handle_user_query(self, query: str) -> Dict[str, str]:
        """
        Entry point for user requests. Returns the final response and a transcript reference.
        """
        intent = self._detect_intent(query)
        self.send("user", f"Received query: {query}", intent=intent)
        if intent == "customer_info":
            return self._handle_customer_info(query)
        if intent == "upgrade":
            return self._handle_upgrade(query)
        if intent == "cancel_and_billing":
            return self._handle_billing_negotiation(query)
        if intent == "high_priority_report":
            return self._handle_multi_step_report(query)
        if intent == "active_with_open_tickets":
            return self._handle_active_with_open_tickets(query)
        if intent == "update_email_and_history":
            return self._handle_update_and_history(query)
        # fallback
        response = self.support_agent.handle(
            AgentMessage(sender=self.name, recipient=self.support_agent.name, content=query, intent="general_support")
        )
        return {"response": response.content}

    def _detect_intent(self, query: str) -> str:
        text = query.lower()
        if "charged twice" in text or ("refund" in text and "charged" in text):
            return "cancel_and_billing"
        if "high-priority" in text or "high priority" in text:
            return "high_priority_report"
        if "cancel" in text and "billing" in text:
            return "cancel_and_billing"
        if "upgrade" in text or "upgrad" in text:
            return "upgrade"
        if "update my email" in text and "history" in text:
            return "update_email_and_history"
        if "open tickets" in text and "active customers" in text:
            return "active_with_open_tickets"
        if "customer information" in text or text.startswith("get customer information"):
            return "customer_info"
        return "general_support"

    def _extract_customer_id(self, text: str) -> Optional[int]:
        match = re.search(r"(?:id|customer)\s*(\d+)", text.lower())
        return int(match.group(1)) if match else None

    def _handle_customer_info(self, query: str) -> Dict[str, str]:
        customer_id = self._extract_customer_id(query)
        request = self.send(
            self.data_agent.name,
            f"Fetch details for customer {customer_id}",
            intent="get_customer",
            payload={"customer_id": customer_id},
        )
        reply = self.data_agent.handle(request)
        customer = reply.payload.get("customer")
        if not customer:
            return {"response": "Customer not found."}
        summary = f"Customer {customer['id']}: {customer['name']} ({customer['status']}). Email: {customer['email']}, Phone: {customer['phone']}."
        return {"response": summary}

    def _handle_upgrade(self, query: str) -> Dict[str, str]:
        customer_id = self._extract_customer_id(query) or 12345
        data_request = self.send(
            self.data_agent.name,
            f"Need data for upgrade for customer {customer_id}",
            intent="get_customer",
            payload={"customer_id": customer_id},
        )
        data_reply = self.data_agent.handle(data_request)
        support_request = AgentMessage(
            sender=self.name,
            recipient=self.support_agent.name,
            content="Provide upgrade guidance",
            intent="upgrade",
            payload={"customer": data_reply.payload.get("customer")},
        )
        self.logger.record(support_request)
        support_reply = self.support_agent.handle(support_request)
        return {"response": support_reply.content}

    def _handle_billing_negotiation(self, query: str) -> Dict[str, str]:
        # Negotiation: support requests billing context, router fetches via data agent, then loops back.
        support_probe = AgentMessage(
            sender=self.name,
            recipient=self.support_agent.name,
            content="Can you handle cancellation plus billing?",
            intent="billing_help",
            payload={"issue": query},
        )
        self.logger.record(support_probe)
        # Support replies asking for context
        support_reply = self.support_agent.handle(support_probe)
        # Router fetches customer data for billing context
        customer_id = self._extract_customer_id(query) or 12345
        data_request = self.send(
            self.data_agent.name,
            "Need billing context for cancellation and double charge",
            intent="get_customer",
            payload={"customer_id": customer_id},
        )
        data_reply = self.data_agent.handle(data_request)
        enriched_request = AgentMessage(
            sender=self.name,
            recipient=self.support_agent.name,
            content="Provide coordinated cancellation + billing resolution",
            intent="billing_help",
            payload={"customer": data_reply.payload.get("customer"), "issue": query},
        )
        self.logger.record(enriched_request)
        final_reply = self.support_agent.handle(enriched_request)
        return {"response": final_reply.content}

    def _handle_multi_step_report(self, query: str) -> Dict[str, str]:
        # Multi-step: fetch customers then tickets then compose report
        customers_request = self.send(
            self.data_agent.name,
            "Fetch premium customers (modeled as active for demo)",
            intent="list_customers",
            payload={"status": "active", "limit": 100},
        )
        customers_reply = self.data_agent.handle(customers_request)
        customers = customers_reply.payload.get("customers", [])
        tickets = self.data_agent.get_open_tickets_for_active_customers(priority="high")
        support_request = AgentMessage(
            sender=self.name,
            recipient=self.support_agent.name,
            content="Format high-priority ticket report",
            intent="ticket_report",
            payload={"tickets": tickets, "customers": customers},
        )
        self.logger.record(support_request)
        support_reply = self.support_agent.handle(support_request)
        return {"response": support_reply.content}

    def _handle_active_with_open_tickets(self, query: str) -> Dict[str, str]:
        # Negotiation between agents to combine filters
        active_customers = self.data_agent.handle(
            AgentMessage(
                sender=self.name,
                recipient=self.data_agent.name,
                content="List active customers",
                intent="list_customers",
                payload={"status": "active", "limit": 50},
            )
        ).payload.get("customers", [])

        open_tickets = self.data_agent.get_open_tickets_for_active_customers()
        relevant_ids = {t["customer_id"] for t in open_tickets}
        filtered = [c for c in active_customers if c["id"] in relevant_ids]

        support_request = AgentMessage(
            sender=self.name,
            recipient=self.support_agent.name,
            content="Combine customer and ticket filters",
            intent="ticket_report",
            payload={"tickets": open_tickets, "customers": filtered},
        )
        self.logger.record(support_request)
        support_reply = self.support_agent.handle(support_request)
        return {"response": support_reply.content}

    def _handle_update_and_history(self, query: str) -> Dict[str, str]:
        # Parallel tasks: update email + fetch history
        customer_id = self._extract_customer_id(query) or 5
        # parse email simple
        email_match = re.search(r"update my email to ([^\s]+)", query.lower())
        new_email = email_match.group(1) if email_match else None

        update_request = self.send(
            self.data_agent.name,
            "Update email",
            intent="update_customer",
            payload={"customer_id": customer_id, "data": {"email": new_email}},
        )
        update_reply = self.data_agent.handle(update_request)

        history_request = self.send(
            self.data_agent.name,
            "Get history",
            intent="get_history",
            payload={"customer_id": customer_id},
        )
        history_reply = self.data_agent.handle(history_request)

        support_request = AgentMessage(
            sender=self.name,
            recipient=self.support_agent.name,
            content="Share updated profile plus history",
            intent="history",
            payload={
                "customer": update_reply.payload.get("customer"),
                "history": history_reply.payload.get("history", []),
            },
        )
        self.logger.record(support_request)
        support_reply = self.support_agent.handle(support_request)
        return {"response": support_reply.content}
