# Multi-Agent Customer Service (A2A + MCP)

This is an agent2agent coordination with an MCP-backed customer data service. The Router Agent delegates to a Customer Data Agent (via MCP-style tools) and a Support Agent to handle routing, negotiation, and multi-step workflows.

## Quickstart
- Create and activate a virtual environment.
- Install dependencies: `pip install -r requirements.txt`
- Seed setup data: `python database_setup.py` (uses the dataset baked into `database_setup.py`)
- Start the MCP server: `python mcp_server.py`
- Run the end-to-end scenarios: `python run_demo.py`. This runs all five queries that required in the assignment test scenario.

## Project Structure
- `database_setup.py` – builds the SQLite database with demo customers and tickets.
- `db.py` – shared SQLite helpers used by both the MCP tools and agents.
- `mcp_server.py` – FastMCP server exposing data tools.
- `agents/base.py` – simple message object and logger for A2A transcripts.
- `agents/customer_data_agent.py` – specialist agent that wraps MCP data access.
- `agents/support_agent.py` – specialist agent for responses, escalation, and reporting.
- `agents/router_agent.py` – orchestrator handling routing, negotiation, and multi-step flows.
- `run_demo.py` – runs the required scenarios and prints the agent-to-agent transcript.

## How to Start and Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt # Create and activate a virtual environment

python database_setup.py # database embed

python mcp_server.py # start the mcp

python run_demo.py # run the end-to-end scenario test

```

## Scenarios Covered (assignment requirements)
- Task allocation: Router to Data Agent to Support Agent for “I’m customer 12345 and need help upgrading my account”.

- Negotiation/escalation: Router mediates billing and cancellation by looping Support and retrieving from dataset.

- Multi-step: Router decomposes “What’s the status of all high-priority tickets for premium customers?” into customer lookup and ticket report.

- Additional tests: simple info lookup, active customers with open tickets, and parallel update with history retrieval.

## Notebook option that runs the project end to end 
This will be covered in colab - upload the database to colab and run through that. There is another .ipynb notebook. I uploaded the files into Colab and run over that, but there is another way that can colone the github repo to run the agent through colab. 

## Conclusion
This project provides a really useful and perfect hands-on experience in designing and debugging a practical multi-agent customer service system using both Agent2Agent coordination and an MCP-backed data layer. By separating tasks across a Router Agent, a Customer Data Agent, and a Support Agent, I was able to clearly model task allocation, negotiation, escalation, and multi-step workflows in a realistic customer support setting.

One of the main challenges in this project was deciding how much structure to hard-code into the agents in order to satisfy all of the assignment queries and constraints. To support upgrades, billing issues, ticket reports, and history lookups, I ended up defining a fairly rich intent space in the Router and several specialized handlers in the SupportAgent and CustomerDataAgent. This also forced me to think more like a real system designer. In practice, larger production systems would push some of this logic into configuration, workflow engines, or LLM-driven routing, but going through the manual design here was useful. It made me think of that scalable multi-agent systems are about clean intent design and clear agent boundaries, designing and make them work as expected, not just about calling an LLM.
