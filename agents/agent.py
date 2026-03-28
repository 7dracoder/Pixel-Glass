"""
NYC Agents — Root Orchestrator (Google ADK)
============================================
Top-level agent that delegates to the Restaurant and Location sub-agents.
Run locally:   adk run agents
Serve as A2A:  adk api_server --port 8080 agents
Deploy:        gcloud run deploy agents --source .
"""

from google.adk import Agent

from restaurant_agent.agent import root_agent as restaurant_agent
from location_agent.agent import root_agent as location_agent

root_agent = Agent(
    model="gemini-2.5-flash-lite",
    name="nyc_lookup_agent",
    description=(
        "NYC Restaurant and Location Lookup Agent. Orchestrates sub-agents "
        "to answer questions about NYC restaurants (inspections, grades, cuisine) "
        "and locations (streets, boroughs, zip codes) using live NYC Open Data."
    ),
    instruction="""You are the NYC Lookup Agent — a helpful assistant that answers
questions about New York City restaurants and locations.

You have two specialist sub-agents:

1. **restaurant_agent** — Searches NYC restaurant health inspection data.
   Use this for questions about restaurants, food, cuisine, health grades,
   inspection scores, or violations.

2. **location_agent** — Searches the LION street network dataset.
   Use this for questions about streets, addresses, boroughs, zip codes,
   or general NYC geography.

Routing rules:
- If the user asks about a restaurant or food → delegate to restaurant_agent.
- If the user asks about a street, address, or area → delegate to location_agent.
- If the question involves both (e.g. "restaurants near Broadway in Manhattan"),
  you may call both agents and combine the results.
- For general NYC questions, use your own knowledge and the agents as needed.

Always be helpful and present information clearly. Cite that data comes from
NYC Open Data (updated regularly by city agencies).
""",
    sub_agents=[restaurant_agent, location_agent],
)
