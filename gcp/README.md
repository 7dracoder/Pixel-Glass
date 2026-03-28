# GCP - HMDA Mortgage Data RAG Agent

## Overview

This directory contains the **HMDA Mortgage Data Analysis Agent** — a production-ready mortgage analytics system deployed on Google Cloud Run. It analyzes 187,337 real NYC mortgage records to answer questions about lending patterns and practices.

**Status:** 🟢 **LIVE** at https://hmda-rag-agent-339008289595.europe-west1.run.app

---

## Quick Links

📖 **New here?** Start with [QUICK_START.md](QUICK_START.md) — has copy-paste test commands

📊 **Want full details?** Read [PROJECT_STATUS.md](PROJECT_STATUS.md) — complete project overview, roadblocks, and what's working

🔧 **Building/deploying?** See [Dockerfile](Dockerfile) and [deploy.sh](deploy.sh)

---

## File Guide

### Core Application
- **`hmda_rag_agent.py`** — Main Flask API (active deployment)
- **`hmda_rag_agent_fixed.py`** — Alternative version with loan type fixes
- **`requirements.txt`** — Python dependencies
- **`Dockerfile`** — Container configuration
- **`deploy.sh`** — One-command deployment to Cloud Run

### Debug & Validation Scripts
- **`debug_loan_type.py`** — Validates loan type data in CSV (used to debug the broken query)
- **`debug_data.py`** — General CSV inspection
- **`check_cols_final.py`** — Lists all CSV columns and samples
- **`check_columns.py`** — Alternative column checker
- **`quick_check.py`** — Quick validation utility

---

## Architecture

```
Your Query (JSON)
       ↓
Cloud Run Service (EU region, 4Gi memory)
       ↓
Flask App (Python 3.11)
       ├─ /query endpoint (main)
       ├─ /health endpoint
       └─ / endpoint (info)
       ↓
Google Cloud Storage
  (gs://tourgemini-hmda-data/raw/hmda_nyc.csv)
       ↓
Statistical Analysis
  ├─ By Lender ✅
  ├─ By Income ✅
  ├─ By Property Type ✅
  ├─ By Loan Type ❌ (broken)
  └─ By Demographics ⚠️  (untested)
       ↓
JSON Response
```

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Data loading | ✅ | 187,337 records cached in memory |
| Lender analysis | ✅ | Returns top 10 with stats |
| Income analysis | ✅ | 5 income brackets |
| Property type | ✅ | Working correctly |
| **Loan type** | ❌ | Returns empty (under investigation) |
| Demographics | ⚠️  | Code exists, not fully tested |
| Cloud Run deployment | ✅ | Live and serving requests |

See [PROJECT_STATUS.md](PROJECT_STATUS.md#roadblocks--) for detailed breakdown of issues.

---

## Getting Started

### Option 1: Test the Live Service (Easiest)
Follow [QUICK_START.md - Quick Test Section](QUICK_START.md#-quick-test-copy--paste)

### Option 2: Run Locally
```bash
# Clone & setup
git clone <repo>
cd VisionClaw/gcp

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Authenticate with GCP
gcloud auth application-default login

# Run the server
python hmda_rag_agent.py

# From another terminal, test:
# Use commands from QUICK_START.md but replace URL with http://localhost:8080
```

### Option 3: Deploy Your Own Version
```bash
# Build & push container
docker build -t gcr.io/your-project/hmda-rag-agent:latest .
docker push gcr.io/your-project/hmda-rag-agent:latest

# Deploy to Cloud Run
gcloud run deploy hmda-rag-agent \
  --image gcr.io/your-project/hmda-rag-agent:latest \
  --region europe-west1 \
  --memory 4Gi
```

---

## Example Queries

### ✅ Working
```json
{
  "question": "What are the top lenders?"
}
```

```json
{
  "question": "Show me denial rates by income"
}
```

```json
{
  "question": "How do lending patterns differ by property type?"
}
```

### ❌ Known Issues
```json
{
  "question": "What are denial rates by loan type?"
}
```
→ Returns empty (debugging in progress)

See [PROJECT_STATUS.md#roadblocks-](PROJECT_STATUS.md#roadblocks--) for more details.

---

## Data Source

**Dataset:** CFPB HMDA (Home Mortgage Disclosure Act) Data

**Records:** 187,337 NYC mortgage applications (2023)

**Key Fields:**
- Loan type (Conventional, FHA, VA, FSA/RHS)
- Property type
- Applicant income
- Lender information
- Action taken (approved, denied, withdrawn)
- Race/ethnicity

**Storage Location:** `gs://tourgemini-hmda-data/raw/hmda_nyc.csv`

---

## Troubleshooting

### Query returns empty
- **Loan type query** → Known issue, see PROJECT_STATUS.md
- **Other queries** → Usually means data isn't loading. Check:
  - GCP authentication: `gcloud auth application-default login`
  - GCS access: Can you read from the bucket?
  - First request? It takes ~1.5 seconds to load CSV

### First request is slow
- Normal! ~1.5 seconds for CSV download and parse
- Subsequent requests are <100ms (cached)

### Getting 404 on /debug endpoint
- Debug endpoint was added for troubleshooting but not in current deployed version
- Use queries instead to test functionality

---

## For Friends/Reviewers

1. **Want to test it?** → [QUICK_START.md](QUICK_START.md)
2. **Want full story?** → [PROJECT_STATUS.md](PROJECT_STATUS.md)
3. **Want to understand code?** → Start with `hmda_rag_agent.py` (it's well-commented)
4. **Curious about the data?** → Run `python debug_loan_type.py` to see validation

---

## What's Working Well

✅ **Production deployment** — Service is live, responding to requests  
✅ **Scalable architecture** — Cloud Run auto-scales  
✅ **Real data analysis** — Not AI-hallucinated, actual statistical calculations  
✅ **Multiple query types** — Lender, income, property analysis all functional  
✅ **REST API** — Clean JSON interface  

---

## Known Limitations

- Loan type query broken (being debugged)
- Demographic disparity analysis not fully tested
- Geographic scope limited to NYC
- Real-time updates not implemented (static 2023 data)
- No authentication/rate limiting on API

---

## Next Steps

**High Priority:**
- [ ] Fix loan type analysis function
- [ ] Test demographic disparity queries
- [ ] Replace logger.info() with print() for debugging

**Medium Priority:**
- [ ] Add BigQuery integration
- [ ] Implement caching/Redis
- [ ] Create web UI

**Low Priority:**
- [ ] API rate limiting
- [ ] Authentication
- [ ] Visualization dashboard

---

## Contact

For questions about this agent:
- Check the docs (PROJECT_STATUS.md, QUICK_START.md)
- Review debug script output (debug_loan_type.py)
- Test the live service
- Read hmda_rag_agent.py comments

---

**Last Updated:** March 28, 2026  
**Deployment Status:** 🟢 Live on Cloud Run  
**Pipeline Status:** 5/6 steps complete
