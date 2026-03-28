#!/usr/bin/env python3
"""
HMDA Agent with Real Data Analysis - FIXED VERSION
Loads HMDA CSV and performs actual statistical analysis on each query
"""

from flask import Flask, request, jsonify
import logging
import os
import csv
from google.cloud import storage
from collections import defaultdict
import json

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global HMDA data
hmda_records = []
data_loaded = False

def load_hmda_data():
    """Load HMDA data from GCS and parse into memory"""
    global hmda_records, data_loaded
    
    logger.info("📥 Loading HMDA CSV from GCS...")
    
    try:
        client = storage.Client(project="tourgemini")
        bucket = client.bucket("tourgemini-hmda-data")
        blob = bucket.blob("raw/hmda_nyc.csv")
        
        logger.info("   Downloading CSV...")
        csv_text = blob.download_as_text()
        
        logger.info("   Parsing CSV...")
        lines = csv_text.split('\n')
        reader = csv.DictReader(lines)
        
        hmda_records = [row for row in reader if row and row.get('respondent_id')]
        data_loaded = True
        
        logger.info(f"✅ Loaded {len(hmda_records)} HMDA records successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading data: {str(e)}", exc_info=True)
        return False

def get_denial_rates():
    """Calculate overall denial rates from data"""
    if not hmda_records:
        return None
    
    total = len(hmda_records)
    approved = sum(1 for r in hmda_records if r.get('action_taken') == '1')
    denied = sum(1 for r in hmda_records if r.get('action_taken') == '3')
    withdrawn = sum(1 for r in hmda_records if r.get('action_taken') == '4')
    
    return {
        "total": total,
        "approved": approved,
        "denied": denied,
        "withdrawn": withdrawn,
        "approval_rate": (approved / total * 100) if total > 0 else 0,
        "denial_rate": (denied / total * 100) if total > 0 else 0,
        "withdrawal_rate": (withdrawn / total * 100) if total > 0 else 0
    }

def get_denial_rates_by_lender():
    """Calculate denial rates broken down by lender"""
    if not hmda_records:
        return {}
    
    lender_stats = defaultdict(lambda: {"total": 0, "denied": 0, "approved": 0})
    
    for record in hmda_records:
        lender = record.get('respondent_id', 'Unknown')
        action = record.get('action_taken', '')
        
        lender_stats[lender]["total"] += 1
        if action == '3':
            lender_stats[lender]["denied"] += 1
        elif action == '1':
            lender_stats[lender]["approved"] += 1
    
    # Calculate rates and sort by total applications
    result = []
    for lender, stats in lender_stats.items():
        denial_rate = (stats['denied'] / stats['total'] * 100) if stats['total'] > 0 else 0
        approval_rate = (stats['approved'] / stats['total'] * 100) if stats['total'] > 0 else 0
        result.append({
            "lender": lender,
            "total": stats['total'],
            "denied": stats['denied'],
            "approved": stats['approved'],
            "denial_rate": denial_rate,
            "approval_rate": approval_rate
        })
    
    # Sort by total applications (descending)
    return sorted(result, key=lambda x: x['total'], reverse=True)

def get_denial_rates_by_race():
    """Calculate denial rates by applicant race/ethnicity"""
    if not hmda_records:
        return {}
    
    race_stats = defaultdict(lambda: {"total": 0, "denied": 0, "approved": 0})
    
    race_map = {
        '1': 'White',
        '2': 'Black/African American',
        '3': 'Asian',
        '4': 'Native American',
        '5': 'Pacific Islander',
        '6': 'Hispanic',
        '7': 'Multiple Race'
    }
    
    for record in hmda_records:
        race_code = record.get('applicant_race_1', '')
        action = record.get('action_taken', '')
        
        if race_code in race_map:
            race = race_map[race_code]
            race_stats[race]["total"] += 1
            if action == '3':
                race_stats[race]["denied"] += 1
            elif action == '1':
                race_stats[race]["approved"] += 1
    
    # Calculate rates
    result = {}
    for race, stats in race_stats.items():
        denial_rate = (stats['denied'] / stats['total'] * 100) if stats['total'] > 0 else 0
        approval_rate = (stats['approved'] / stats['total'] * 100) if stats['total'] > 0 else 0
        result[race] = {
            "total": stats['total'],
            "denied": stats['denied'],
            "approved": stats['approved'],
            "denial_rate": denial_rate,
            "approval_rate": approval_rate
        }
    
    return result

def get_loan_types():
    """Get loan type distribution - FIXED VERSION"""
    if not hmda_records:
        logger.info(f"DEBUG get_loan_types: hmda_records is empty!")
        return {}
    
    logger.info(f"DEBUG get_loan_types: Processing {len(hmda_records)} records")
    
    type_stats = defaultdict(lambda: {"total": 0, "denied": 0, "approved": 0})
    
    found_any = False
    for record in hmda_records:
        loan_type_name = record.get('loan_type_name', '')
        action = record.get('action_taken', '')
        
        if loan_type_name:  # Use the name directly from CSV
            found_any = True
            type_stats[loan_type_name]["total"] += 1
            if action == '3':
                type_stats[loan_type_name]["denied"] += 1
            elif action == '1':
                type_stats[loan_type_name]["approved"] += 1
    
    logger.info(f"DEBUG get_loan_types: found_any={found_any}, type_stats keys={list(type_stats.keys())}")
    
    result = {}
    for loan_type, stats in type_stats.items():
        denial_rate = (stats['denied'] / stats['total'] * 100) if stats['total'] > 0 else 0
        approval_rate = (stats['approved'] / stats['total'] * 100) if stats['total'] > 0 else 0
        result[loan_type] = {
            "total": stats['total'],
            "denied": stats['denied'],
            "approved": stats['approved'],
            "denial_rate": denial_rate,
            "approval_rate": approval_rate
        }
    
    logger.info(f"DEBUG get_loan_types: Returning {len(result)} loan types: {list(result.keys())}")
    return result

def get_denial_rates_by_income():
    """Calculate denial rates by income bracket - FIXED VERSION"""
    if not hmda_records:
        return {}
    
    income_stats = defaultdict(lambda: {"total": 0, "denied": 0, "approved": 0})
    
    for record in hmda_records:
        try:
            income = int(record.get('applicant_income_000s', '0') or '0')
            action = record.get('action_taken', '')
            
            # Bracket by income (in thousands)
            if income < 50:
                bracket = "Under $50k"
            elif income < 100:
                bracket = "$50k-$100k"
            elif income < 150:
                bracket = "$100k-$150k"
            elif income < 250:
                bracket = "$150k-$250k"
            else:
                bracket = "Over $250k"
            
            income_stats[bracket]["total"] += 1
            if action == '3':
                income_stats[bracket]["denied"] += 1
            elif action == '1':
                income_stats[bracket]["approved"] += 1
        except:
            pass
    
    result = {}
    for bracket in ["Under $50k", "$50k-$100k", "$100k-$150k", "$150k-$250k", "Over $250k"]:
        if bracket in income_stats:
            stats = income_stats[bracket]
            denial_rate = (stats['denied'] / stats['total'] * 100) if stats['total'] > 0 else 0
            approval_rate = (stats['approved'] / stats['total'] * 100) if stats['total'] > 0 else 0
            result[bracket] = {
                "total": stats['total'],
                "denied": stats['denied'],
                "approved": stats['approved'],
                "denial_rate": denial_rate,
                "approval_rate": approval_rate
            }
    
    return result

def get_denial_rates_by_property_type():
    """Calculate denial rates by property type - FIXED VERSION"""
    if not hmda_records:
        return {}
    
    property_stats = defaultdict(lambda: {"total": 0, "denied": 0, "approved": 0})
    
    for record in hmda_records:
        prop_type = record.get('property_type_name', '')
        action = record.get('action_taken', '')
        
        if prop_type:  # Use the name directly from CSV
            property_stats[prop_type]["total"] += 1
            if action == '3':
                property_stats[prop_type]["denied"] += 1
            elif action == '1':
                property_stats[prop_type]["approved"] += 1
    
    result = {}
    for prop_type, stats in property_stats.items():
        denial_rate = (stats['denied'] / stats['total'] * 100) if stats['total'] > 0 else 0
        approval_rate = (stats['approved'] / stats['total'] * 100) if stats['total'] > 0 else 0
        result[prop_type] = {
            "total": stats['total'],
            "denied": stats['denied'],
            "approved": stats['approved'],
            "denial_rate": denial_rate,
            "approval_rate": approval_rate
        }
    
    return result

@app.route("/query", methods=["POST"])
def query_hmda():
    """Query and analyze HMDA data based on question"""
    try:
        # Load data on first query
        global data_loaded
        if not data_loaded:
            if not load_hmda_data():
                return jsonify({"error": "Failed to load HMDA data"}), 500
        
        data = request.get_json()
        question = data.get("question", "").lower()
        
        if not question:
            return jsonify({"error": "No question provided"}), 400
        
        logger.info(f"Query: {question}")
        
        answer_text = ""
        sources = []
        
        # Route to appropriate analysis
        if "lender" in question and ("denial" in question or "rate" in question or "approval" in question):
            # Lender-specific analysis
            lender_data = get_denial_rates_by_lender()[:10]  # Top 10
            answer_text = "Mortgage Denial Rates by Lender (Top 10 by Volume):\n\n"
            for idx, lender in enumerate(lender_data, 1):
                answer_text += f"{idx}. {lender['lender']}\n"
                answer_text += f"   Total Applications: {lender['total']:,}\n"
                answer_text += f"   Approval Rate: {lender['approval_rate']:.1f}%\n"
                answer_text += f"   Denial Rate: {lender['denial_rate']:.1f}%\n\n"
            sources.append("Lender-specific analysis")
            
        elif "income" in question or "income level" in question:
            # Income-based analysis
            income_data = get_denial_rates_by_income()
            answer_text = "Mortgage Approval/Denial Rates by Income Level:\n\n"
            for bracket in ["Under $50k", "$50k-$100k", "$100k-$150k", "$150k-$250k", "Over $250k"]:
                if bracket in income_data:
                    stats = income_data[bracket]
                    answer_text += f"{bracket}:\n"
                    answer_text += f"  Applications: {stats['total']:,}\n"
                    answer_text += f"  Approval Rate: {stats['approval_rate']:.1f}%\n"
                    answer_text += f"  Denial Rate: {stats['denial_rate']:.1f}%\n\n"
            sources.append("Income-based analysis")
            
        elif "race" in question or "ethnicity" in question or "demographic" in question or "disparity" in question:
            # Demographic analysis
            race_data = get_denial_rates_by_race()
            answer_text = "Mortgage Approval Rates by Race/Ethnicity:\n\n"
            for race in sorted(race_data.keys()):
                stats = race_data[race]
                if stats['total'] > 100:  # Only show groups with significant data
                    answer_text += f"{race}:\n"
                    answer_text += f"  Total Applications: {stats['total']:,}\n"
                    answer_text += f"  Approval Rate: {stats['approval_rate']:.1f}%\n"
                    answer_text += f"  Denial Rate: {stats['denial_rate']:.1f}%\n\n"
            answer_text += "Note: Disparities in approval rates by race are tracked to monitor fair lending practices.\n"
            sources.append("Demographic disparity analysis")
            
        elif "loan type" in question or "loan product" in question or "conventional" in question or "fha" in question:
            # Loan type analysis
            type_data = get_loan_types()
            logger.info(f"DEBUG: Loan type data returned: {type_data}")
            answer_text = "Mortgage Approval Rates by Loan Type:\n\n"
            if type_data:
                for loan_type in sorted(type_data.keys()):
                    stats = type_data[loan_type]
                    answer_text += f"{loan_type}:\n"
                    answer_text += f"  Total Applications: {stats['total']:,}\n"
                    answer_text += f"  Denial Rate: {stats['denial_rate']:.1f}%\n"
                    answer_text += f"  Approval Rate: {stats['approval_rate']:.1f}%\n\n"
            else:
                answer_text += "[No loan type data found]\n"
            sources.append("Loan type analysis")
            
        elif "property type" in question or "single family" in question or "multifamily" in question:
            # Property type analysis
            property_data = get_denial_rates_by_property_type()
            logger.info(f"DEBUG: Property type data returned: {property_data}")
            answer_text = "Mortgage Approval Rates by Property Type:\n\n"
            if property_data:
                for prop_type in sorted(property_data.keys()):
                    stats = property_data[prop_type]
                    answer_text += f"{prop_type}:\n"
                    answer_text += f"  Total Applications: {stats['total']:,}\n"
                    answer_text += f"  Denial Rate: {stats['denial_rate']:.1f}%\n"
                    answer_text += f"  Approval Rate: {stats['approval_rate']:.1f}%\n\n"
            else:
                answer_text += "[No property type data found]\n"
            sources.append("Property type analysis")
            
        elif "denial" in question or "approve" in question or "approval" in question:
            # Overall rates
            rates = get_denial_rates()
            answer_text = f"NYC Mortgage Lending Statistics:\n\n"
            answer_text += f"Total Applications Analyzed: {rates['total']:,}\n\n"
            answer_text += f"Approval Rate: {rates['approval_rate']:.1f}%\n"
            answer_text += f"Denial Rate: {rates['denial_rate']:.1f}%\n"
            answer_text += f"Withdrawn Rate: {rates['withdrawal_rate']:.1f}%\n\n"
            answer_text += f"Breakdown:\n"
            answer_text += f"- Approved: {rates['approved']:,} applications\n"
            answer_text += f"- Denied: {rates['denied']:,} applications\n"
            answer_text += f"- Withdrawn: {rates['withdrawn']:,} applications\n"
            sources.append("Overall approval/denial statistics")
            
        else:
            # Default: show summary
            rates = get_denial_rates()
            answer_text = f"NYC HMDA Mortgage Lending Summary:\n\n"
            answer_text += f"Dataset Size: {rates['total']:,} loan applications\n"
            answer_text += f"Approval Rate: {rates['approval_rate']:.1f}%\n"
            answer_text += f"Denial Rate: {rates['denial_rate']:.1f}%\n\n"
            answer_text += f"I can analyze lending patterns by:\n"
            answer_text += f"• Lender (bank/institution)\n"
            answer_text += f"• Applicant income level\n"
            answer_text += f"• Race/ethnicity (disparities)\n"
            answer_text += f"• Loan type (conventional, FHA, VA, USDA)\n"
            answer_text += f"• Property type\n\n"
            answer_text += f"Your question: '{data.get('question')}'"
            sources.append("General information")
        
        result = {
            "question": data.get("question"),
            "answer": answer_text,
            "sources": sources,
            "data_records": len(hmda_records)
        }
        
        logger.info(f"Returned response with {len(result['answer'])} characters")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/debug", methods=["GET"])
def debug():
    """Debug endpoint to show loaded data sample"""
    if not hmda_records:
        return jsonify({"error": "No data loaded yet"}), 400
    
    # Show first record
    first_record = hmda_records[0]
    
    # Check which fields are populated
    populated_fields = {k: v for k, v in first_record.items() if v and len(str(v)) > 0}
    
    return jsonify({
        "total_records": len(hmda_records),
        "first_record_populated_fields": populated_fields,
        "has_loan_type_name": bool(first_record.get('loan_type_name')),
        "loan_type_name_value": first_record.get('loan_type_name', ''),
        "has_property_type_name": bool(first_record.get('property_type_name')),
        "property_type_name_value": first_record.get('property_type_name', '')
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "hmda-agent",
        "data_loaded": data_loaded,
        "data_records": len(hmda_records)
    }), 200

@app.route("/", methods=["GET"])
def index():
    """Root endpoint"""
    if data_loaded:
        rates = get_denial_rates()
    else:
        rates = None
    
    return jsonify({
        "service": "HMDA Analysis Agent",
        "description": "Real-time analysis of NYC mortgage lending data",
        "version": "2.0-fixed",
        "data_status": "loaded" if data_loaded else "loading",
        "data_records": len(hmda_records),
        "endpoints": {
            "POST /query": "Query and analyze HMDA data",
            "GET /health": "Health check"
        },
        "example_questions": [
            "What are the denial rates by lender?",
            "How does income level affect approval rates?",
            "Are there demographic disparities?",
            "What are denial rates by loan type?",
            "What are overall approval and denial rates?"
        ]
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting HMDA Agent on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
