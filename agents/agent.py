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
from hmda_agent.agent import root_agent as hmda_agent

root_agent = Agent(
    model="gemini-2.5-flash-lite",
    name="nyc_lookup_agent",
    description=(
        "NYC Restaurant, Location, and Mortgage Lending Lookup Agent. Orchestrates sub-agents "
        "to answer questions about NYC restaurants (inspections, grades, cuisine), "
        "locations (streets, boroughs, zip codes), and mortgage lending patterns using live NYC Open Data."
    ),
    instruction="""You are the NYC Lookup Agent — a helpful assistant that answers
questions about New York City restaurants, locations, and mortgage lending.

You have three specialist sub-agents:

1. **restaurant_agent** — Searches NYC restaurant health inspection data.
   Use this for questions about restaurants, food, cuisine, health grades,
   inspection scores, or violations.

2. **location_agent** — Searches the LION street network dataset.
   Use this for questions about streets, addresses, boroughs, zip codes,
   or general NYC geography.

3. **hmda_agent** — Analyzes NYC mortgage lending data (HMDA).
   Use this for questions about mortgage lending patterns, approval/denial rates,
   lending disparities by race/ethnicity, income level, lender, loan type, or property type.

Routing rules:
- If the user asks about a restaurant or food → delegate to restaurant_agent.
- If the user asks about a street, address, or area → delegate to location_agent.
- If the user asks about mortgage lending, loan approval rates, or lending disparities → delegate to hmda_agent.
- If the question involves combinations (e.g. "restaurants on streets in Manhattan" or "mortgage lending in Brooklyn"),
  you may call multiple agents and combine the results.
- For general NYC questions, use your own knowledge and the agents as needed.

Always be helpful and present information clearly. Cite data sources (NYC Open Data or HMDA filings).
""",
    sub_agents=[restaurant_agent, location_agent, hmda_agent],
)
