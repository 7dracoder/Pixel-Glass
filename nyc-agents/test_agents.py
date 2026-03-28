"""
Test the ADK agents end-to-end.
Run: python test_agents.py

Requires:
  - Python 3.10+ (Google ADK requirement)
  - GOOGLE_API_KEY set in .env or environment
"""
from __future__ import annotations

import asyncio
import os
import warnings

# Suppress noisy deprecation warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Load .env file if present
try:
    with open(os.path.join(os.path.dirname(__file__), ".env")) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())
except FileNotFoundError:
    pass

from google.adk.runners import InMemoryRunner
from google.genai import types
from agent import root_agent


async def chat(runner: InMemoryRunner, session_id: str, user_id: str, message: str):
    """Send a message and print the agent's response."""
    print(f"\n{'─' * 60}")
    print(f"YOU: {message}")
    print(f"{'─' * 60}")

    content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )

    response_text = ""
    async for event in runner.run_async(
        session_id=session_id,
        user_id=user_id,
        new_message=content,
    ):
        # Collect text from the agent's final response
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    print(f"AGENT: {response_text}")
    return response_text


async def main():
    # Verify API key is set
    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: Set GOOGLE_API_KEY in .env or environment")
        print("Get a free key at: https://aistudio.google.com/apikey")
        return

    app_name = "nyc_lookup_agent"
    user_id = "test_user"

    runner = InMemoryRunner(agent=root_agent, app_name=app_name)
    session = await runner.session_service.create_session(
        app_name=app_name, user_id=user_id
    )

    print("NYC Lookup Agent — Interactive Test")
    print("=" * 60)

    # Test restaurant search
    await chat(runner, session.id, user_id,
               "Find Italian restaurants in Manhattan with grade A")

    # Test location lookup
    await chat(runner, session.id, user_id,
               "What streets are near Times Square? My GPS is 40.7580, -73.9855")

    # Test combined query
    await chat(runner, session.id, user_id,
               "Are there any good Chinese restaurants in Brooklyn?")

    print("\n\nDone! All queries used live Socrata API + bundled centerline data.")


if __name__ == "__main__":
    asyncio.run(main())
