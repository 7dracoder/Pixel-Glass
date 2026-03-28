# HMDA RAG Agent - Quick Start Guide

## 🎯 What This Is

A real-world mortgage data analysis system that answers questions about lending patterns using 187,337 actual NYC mortgage records.

**Live Service:** https://hmda-rag-agent-339008289595.europe-west1.run.app

---

## ⚡ Quick Test (Copy & Paste)

### Test 1: Check Health
```powershell
Invoke-WebRequest https://hmda-rag-agent-339008289595.europe-west1.run.app/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "data_loaded": true,
  "data_records": 187337
}
```

---

### Test 2: Query Lenders
```powershell
$q = @{question="What are the top lenders by approval rate?"} | ConvertTo-Json
$r = Invoke-WebRequest -Uri https://hmda-rag-agent-339008289595.europe-west1.run.app/query `
  -Method POST -Headers @{"Content-Type"="application/json"} -Body $q -UseBasicParsing
$r.Content | ConvertFrom-Json | Select-Object -ExpandProperty answer
```

**What You Should See:**
Top 10 lenders with their approval/denial statistics

---

### Test 3: Query by Income
```powershell
$q = @{question="Are there differences in denial rates by applicant income?"} | ConvertTo-Json
$r = Invoke-WebRequest -Uri https://hmda-rag-agent-339008289595.europe-west1.run.app/query `
  -Method POST -Headers @{"Content-Type"="application/json"} -Body $q -UseBasicParsing
$r.Content | ConvertFrom-Json | Select-Object -ExpandProperty answer
```

**What You Should See:**
Income bracket analysis (Under $50k through Over $250k)

---

### Test 4: Query Property Types
```powershell
$q = @{question="What are the denial rates by property type?"} | ConvertTo-Json
$r = Invoke-WebRequest -Uri https://hmda-rag-agent-339008289595.europe-west1.run.app/query `
  -Method POST -Headers @{"Content-Type"="application/json"} -Body $q -UseBasicParsing
$r.Content | ConvertFrom-Json | Select-Object -ExpandProperty answer
```

**What You Should See:**
Property type breakdown (currently mostly one-to-four family dwellings)

---

## 🚀 Running Locally

### Step 1: Setup Python
```powershell
cd c:\Users\91742\OneDrive\Documents\GitHub\VisionClaw
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r gcp/requirements.txt
```

### Step 2: Authenticate with Google Cloud
```powershell
gcloud auth application-default login
```

### Step 3: Start the Server
```powershell
python gcp/hmda_rag_agent.py
# Server will start on http://localhost:8080
```

### Step 4: Test Locally
```powershell
# From another terminal:
$q = @{question="What are denial rates by income?"} | ConvertTo-Json
$r = Invoke-WebRequest -Uri http://localhost:8080/query `
  -Method POST -Headers @{"Content-Type"="application/json"} -Body $q -UseBasicParsing
$r.Content | ConvertFrom-Json | Select-Object -ExpandProperty answer
```

---

## 📊 Example Queries

Try asking these questions (via POST /query):

### Working ✅
- "What are the top lenders?"
- "Show me denial rates by income"
- "How do lending patterns differ by property type?"
- "What's the overall approval rate?"

### Known Issues ⚠️
- "What are denial rates by loan type?" → Returns empty (debugging in progress)
- Demographic disparity queries → Limited testing

---

## 🔍 Understanding the Response

```json
{
  "answer": "Denial Rates by Income:\n\nUnder $50k: 1.5% denial rate...",
  "data_records": 187337,
  "data": {
    "Under $50k": {
      "total": 45000,
      "approved": 44324,
      "denied": 676,
      "denial_rate": "1.50%"
    },
    ...
  }
}
```

- **answer** → Human-readable summary
- **data_records** → Total records processed
- **data** → Raw statistics object

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.11 |
| **Framework** | Flask + Gunicorn |
| **Data** | Google Cloud Storage |
| **Hosting** | Google Cloud Run |
| **Container** | Docker |
| **Region** | Europe-west1 |
| **Memory** | 4Gi |

---

## 📦 Deployment

The app is containerized and auto-deployed to Cloud Run. Any push to `gcp/hmda_rag_agent.py` would be deployed via:

```bash
cd gcp/
docker build -t gcr.io/tourgemini/hmda-rag-agent:latest .
docker push gcr.io/tourgemini/hmda-rag-agent:latest
gcloud run deploy hmda-rag-agent --image gcr.io/tourgemini/hmda-rag-agent:latest --region europe-west1
```

---

## 🐛 Troubleshooting

### "Connection refused" / "localhost:8080 not responding"
- Make sure Flask server is running: `python gcp/hmda_rag_agent.py`
- Check firewall isn't blocking port 8080

### "Permission denied" on GCP
- Run: `gcloud auth application-default login`
- Ensure your account has access to `tourgemini-hmda-data` bucket

### Query returns empty data
- Loan type query is known to have issues → see PROJECT_STATUS.md
- For lender/income/property type → should all work

### First request is slow (~1.5 seconds)
- Normal! This is the CSV loading time
- Subsequent requests are fast (<100ms)

---

## 📋 What's Included

- ✅ 187,337 NYC mortgage records (2023)
- ✅ 78 different data fields per record
- ✅ Real statistical analysis (not AI-generated)
- ✅ Live on Google Cloud Run
- ✅ REST API with JSON responses
- ✅ Docker containerization
- ✅ Comprehensive debug scripts

---

## 🎓 For Friends Reviewing This

1. **Test the live service** using the Quick Test section above
2. **Read [PROJECT_STATUS.md](PROJECT_STATUS.md)** for full context
3. **Check [gcp/hmda_rag_agent.py](gcp/hmda_rag_agent.py)** for implementation
4. **See [gcp/debug_loan_type.py](gcp/debug_loan_type.py)** for how we validated the data

---

Happy exploring! 🚀
