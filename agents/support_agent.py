from typing import Dict, List, Optional

from agents.base import Agent, AgentMessage


class SupportAgent(Agent):
    """
    Handles customer-facing responses and uses context supplied by other agents.
    """

    def __init__(self, logger, escalation_email: str = "billing@support.local") -> None:
        super().__init__("support-agent", logger)
        self.escalation_email = escalation_email

    def handle(self, message: AgentMessage) -> AgentMessage:
        intent = message.intent or "support"
        payload = message.payload or {}
        content = ""
        response_payload: Dict = {}

        if intent == "upgrade":
            customer = payload.get("customer")
            content = self._handle_upgrade(customer)
            response_payload["resolution"] = "upgrade_guidance"
        elif intent == "billing_help":
            customer = payload.get("customer")
            content = self._handle_billing(customer, payload.get("issue"))
            response_payload["resolution"] = "billing_investigation"
        elif intent == "ticket_report":
            tickets: List[dict] = payload.get("tickets", [])
            content = self._format_ticket_report(tickets)
            response_payload["resolution"] = "report_shared"
        elif intent == "history":
            customer = payload.get("customer")
            history = payload.get("history", [])
            content = self._format_history(customer, history)
            response_payload["resolution"] = "history_shared"
        elif intent == "general_support":
            content = "Happy to help! Please share more details about your issue."
            response_payload["resolution"] = "pending_details"
        else:
            content = f"Unknown request for support: {intent}"

        reply = AgentMessage(
            sender=self.name,
            recipient=message.sender,
            content=content,
            intent=intent,
            payload=response_payload,
        )
        self.logger.record(reply)
        return reply

    def _handle_upgrade(self, customer: Optional[dict]) -> str:
        if not customer:
            return "I could not find your account. Please provide your customer ID."
        status = customer.get("status")
        if status == "disabled":
            return "Your account is disabled. I can re-enable it and process an upgrade if you confirm."
        return (
            f"Thanks {customer['name']}! I can upgrade your account now. "
            "I'll apply premium benefits and send a confirmation email shortly."
        )

    def _handle_billing(self, customer: Optional[dict], issue: Optional[str]) -> str:
        prefix = f"Hi {customer['name']}, " if customer else ""
        investigation = "I'll open a billing ticket and alert the finance team."
        detail = f"I see the issue you reported: {issue}. " if issue else ""
        return prefix + detail + "I will secure your account and process a refund if needed. " + investigation

    def _format_ticket_report(self, tickets: List[dict]) -> str:
        if not tickets:
            return "No high-priority open tickets found for the target customers."
        all_high = all(t.get("priority") == "high" for t in tickets)
        lines = ["High-priority open tickets:" if all_high else "Open tickets for target customers:"]
        for t in tickets:
            lines.append(f"- Ticket {t['id']} for customer {t['customer_id']}: {t['issue']} (priority={t['priority']}, status={t['status']})")
        return "\n".join(lines)

    def _format_history(self, customer: Optional[dict], history: List[dict]) -> str:
        if not customer:
            return "I could not load your account to show history."
        if not history:
            return f"{customer['name']}, you have no ticket history yet."
        lines = [f"{customer['name']}, here is your ticket history:"]
        for t in history:
            lines.append(f"- [{t['status']}] {t['issue']} (priority={t['priority']}, id={t['id']})")
        return "\n".join(lines)
