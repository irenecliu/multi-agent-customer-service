"""
End-to-end demo runner for the multi-agent customer service system.
Scenarios exercise task allocation, negotiation, and multi-step coordination.
"""
from typing import List, Tuple

from agents.base import AgentLogger
from agents.customer_data_agent import CustomerDataAgent
from agents.router_agent import RouterAgent
from agents.support_agent import SupportAgent
from database_setup import bootstrap_database
from db import DB_PATH


SCENARIOS: List[Tuple[str, str]] = [
    ("Simple Query", "Get customer information for ID 5"),
    ("Coordinated Query", "I'm customer 12345 and need help upgrading my account"),
    ("Complex Query", "Show me all active customers who have open tickets"),
    ("Escalation", "I've been charged twice, please refund immediately!"),
    ("Multi-Intent", "Update my email to new@email.com and show my ticket history"),
    ("Multi-Step Report", "What's the status of all high-priority tickets for premium customers?"),
]


def run() -> None:
    # Always align with the dataset defined in database_setup.py.
    bootstrap_database()

    logger = AgentLogger()
    data_agent = CustomerDataAgent(logger)
    support_agent = SupportAgent(logger)
    router = RouterAgent(logger, data_agent, support_agent)

    for title, query in SCENARIOS:
        print(f"\n=== {title} ===")
        result = router.handle_user_query(query)
        print(f"User: {query}")
        print(f"Assistant: {result['response']}")

    print("\n=== Transcript (Agent-to-Agent messages) ===")
    logger.print_log()


if __name__ == "__main__":
    run()
