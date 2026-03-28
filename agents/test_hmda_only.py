"""
Test HMDA Mortgage Lending Agent without location data dependency.
Run: python test_hmda_only.py

Requires:
  - GOOGLE_API_KEY set in .env or environment
"""
from __future__ import annotations

import asyncio
import os
import warnings

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
from hmda_agent.agent import root_agent


async def chat(runner: InMemoryRunner, session_id: str, user_id: str, message: str):
    """Send a message and print the agent's response."""
    print(f"\n{'─' * 70}")
    print(f"👤 YOU: {message}")
    print(f"{'─' * 70}")

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
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    print(f"🤖 AGENT: {response_text}")
    return response_text


async def main():
    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌ ERROR: Set GOOGLE_API_KEY in .env or environment")
        return

    app_name = "hmda_agent"
    user_id = "test_user_hmda"

    runner = InMemoryRunner(agent=root_agent, app_name=app_name)
    session = await runner.session_service.create_session(
        app_name=app_name, user_id=user_id
    )

    print("\n" + "=" * 70)
    print("🏦 HMDA MORTGAGE LENDING AGENT TEST")
    print("=" * 70)

    # Test 1: Overall statistics
    await chat(
        runner,
        session.id,
        user_id,
        "What are the overall mortgage approval and denial rates in NYC?"
    )

    # Test 2: Disparities by race
    await chat(
        runner,
        session.id,
        user_id,
        "What are the lending disparities by race/ethnicity?"
    )

    # Test 3: By lender
    await chat(
        runner,
        session.id,
        user_id,
        "Which lenders have the highest denial rates?"
    )

    # Test 4: By income
    await chat(
        runner,
        session.id,
        user_id,
        "How do approval rates vary by income level?"
    )

    # Test 5: By loan type
    await chat(
        runner,
        session.id,
        user_id,
        "What are the approval rates for FHA vs conventional loans?"
    )

    # Test 6: By property type
    await chat(
        runner,
        session.id,
        user_id,
        "Are there differences in approval rates by property type?"
    )

    print("\n" + "=" * 70)
    print("✅ HMDA AGENT TESTS COMPLETE")
    print("=" * 70)
    print("\n✨ All queries tested the HMDA mortgage lending agent")


if __name__ == "__main__":
    asyncio.run(main())
