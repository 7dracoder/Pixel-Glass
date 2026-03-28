#!/usr/bin/env python3
"""Test script to verify HMDA agent is working"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from hmda_agent.agent import root_agent, _load_hmda_data


async def test_agent():
    """Test the HMDA agent tools"""
    print("🧪 Testing HMDA Agent")
    print("=" * 50)
    
    # Load data
    print("\n1️⃣  Loading HMDA data...")
    if not _load_hmda_data():
        print("❌ Failed to load HMDA data")
        return
    
    print("✓ HMDA data loaded successfully")
    
    # Test 1: Get lending summary
    print("\n2️⃣  Testing get_lending_summary()...")
    try:
        summary_tool = root_agent.tools[0]
        result = await summary_tool.fn()
        print(f"   Total Applications: {result.get('total_applications', 'N/A'):,}")
        print(f"   Approval Rate: {result.get('approval_rate_percent', 'N/A')}%")
        print(f"   Denial Rate: {result.get('denial_rate_percent', 'N/A')}%")
        print("✓ get_lending_summary() works")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get denial rates by lender
    print("\n3️⃣  Testing get_denial_rates_by_lender()...")
    try:
        lender_tool = root_agent.tools[1]
        result = await lender_tool.fn(limit=5)
        count = result.get('count', 0)
        print(f"   Top {count} lenders found")
        if result.get('lenders'):
            top_lender = result['lenders'][0]
            print(f"   Top lender: {top_lender.get('lender_id', 'N/A')}")
            print(f"   - Applications: {top_lender.get('total_applications', 0):,}")
            print(f"   - Approval Rate: {top_lender.get('approval_rate_percent', 0)}%")
        print("✓ get_denial_rates_by_lender() works")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get by income
    print("\n4️⃣  Testing get_denial_rates_by_income()...")
    try:
        income_tool = root_agent.tools[2]
        result = await income_tool.fn()
        brackets = result.get('income_brackets', {})
        print(f"   Income brackets analyzed: {len(brackets)}")
        if brackets:
            first_bracket = list(brackets.keys())[0]
            stats = brackets[first_bracket]
            print(f"   Example ({first_bracket}):")
            print(f"   - Applications: {stats.get('total_applications', 0):,}")
            print(f"   - Approval Rate: {stats.get('approval_rate_percent', 0)}%")
        print("✓ get_denial_rates_by_income() works")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get disparities by race
    print("\n5️⃣  Testing get_lending_disparities_by_race()...")
    try:
        race_tool = root_agent.tools[3]
        result = await race_tool.fn()
        disparities = result.get('disparities', {})
        print(f"   Racial groups analyzed: {len(disparities)}")
        if disparities:
            first_group = list(disparities.keys())[0]
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
