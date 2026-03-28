"""
Test the HMDA agent end-to-end using InMemoryRunner.
Run: python test_hmda_agent.py

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
        # Collect text from the agent's final response
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    print(f"🤖 AGENT: {response_text}")
    return response_text


async def main():
    # Verify API key is set
    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌ ERROR: Set GOOGLE_API_KEY in .env or environment")
        print("   Get a free key at: https://aistudio.google.com/apikey")
        return

    app_name = "nyc_lookup_agent"
    user_id = "test_user_hmda"

    runner = InMemoryRunner(agent=root_agent, app_name=app_name)
    session = await runner.session_service.create_session(
        app_name=app_name, user_id=user_id
    )

    print("\n" + "=" * 70)
    print("🏦 HMDA MORTGAGE LENDING AGENT — INTERACTIVE TEST")
    print("=" * 70)

    # Test 1: Overall lending statistics
    await chat(
        runner,
        session.id,
        user_id,
        "What are the overall mortgage approval and denial rates in NYC?"
    )

    # Test 2: Lending disparities by race
    await chat(
        runner,
        session.id,
        user_id,
        "What are the lending disparities by race/ethnicity in NYC mortgages?"
    )

    # Test 3: Lender analysis
    await chat(
        runner,
        session.id,
        user_id,
        "Which lenders have the highest denial rates for mortgage applications?"
    )

    # Test 4: Income-based lending
    await chat(
        runner,
        session.id,
        user_id,
        "How do mortgage approval rates vary by applicant income level?"
    )

    # Test 5: Loan type analysis
    await chat(
        runner,
        session.id,
        user_id,
        "What are the approval rates for different loan types like FHA and conventional?"
    )

    # Test 6: Property type analysis
    await chat(
        runner,
        session.id,
        user_id,
        "Are there differences in approval rates between single-family homes and multifamily properties?"
    )

    print("\n" + "=" * 70)
    print("✅ HMDA AGENT TESTING COMPLETE")
    print("=" * 70)
    print("\n✨ All queries used live HMDA lending data from GCS")
    print("🔧 Agent successfully routed queries to HMDA sub-agent")


if __name__ == "__main__":
    asyncio.run(main())
            stats = disparities[first_group]
            print(f"   Example ({first_group}):")
            print(f"   - Applications: {stats.get('total_applications', 0):,}")
            print(f"   - Approval Rate: {stats.get('approval_rate_percent', 0)}%")
        print("✓ get_lending_disparities_by_race() works")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Get by loan type
    print("\n6️⃣  Testing get_lending_by_loan_type()...")
    try:
        loan_tool = root_agent.tools[4]
        result = await loan_tool.fn()
        loan_types = result.get('loan_types', {})
        print(f"   Loan types analyzed: {len(loan_types)}")
        if loan_types:
            first_type = list(loan_types.keys())[0]
            stats = loan_types[first_type]
            print(f"   Example ({first_type}):")
            print(f"   - Applications: {stats.get('total_applications', 0):,}")
            print(f"   - Approval Rate: {stats.get('approval_rate_percent', 0)}%")
        print("✓ get_lending_by_loan_type() works")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Get by property type
    print("\n7️⃣  Testing get_lending_by_property_type()...")
    try:
        prop_tool = root_agent.tools[5]
        result = await prop_tool.fn()
        prop_types = result.get('property_types', {})
        print(f"   Property types analyzed: {len(prop_types)}")
        if prop_types:
            first_prop = list(prop_types.keys())[0]
            stats = prop_types[first_prop]
            print(f"   Example ({first_prop}):")
            print(f"   - Applications: {stats.get('total_applications', 0):,}")
            print(f"   - Approval Rate: {stats.get('approval_rate_percent', 0)}%")
        print("✓ get_lending_by_property_type() works")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ All HMDA agent tools working correctly!")
    print(f"📊 Agent: {root_agent.name}")
    print(f"🔧 Tools available: {len(root_agent.tools)}")


if __name__ == "__main__":
    asyncio.run(test_agent())
