<div align="center">

```
██████╗ ██╗██╗  ██╗███████╗██╗
██╔══██╗██║╚██╗██╔╝██╔════╝██║
██████╔╝██║ ╚███╔╝ █████╗  ██║
██╔═══╝ ██║ ██╔██╗ ██╔══╝  ██║
██║     ██║██╔╝ ██╗███████╗███████╗
╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
         G L A S S
```

**Ask the city anything. Hear the answer through your glasses. In under 2 seconds.**

</div>

---

## 🪄 What Is Pixel Glass?

Pixel Glass is an AI-native platform that bridges smart glasses, real-time multimodal AI, and live public city datasets into a single, seamless, hands-free experience.

Put on a pair of Meta Ray-Ban smart glasses, look at a restaurant, a street corner, or a building — and ask. Pixel Glass answers out loud, through your glasses speakers, in under two seconds. No phone. No typing. No stopping.

> *"What's the health grade of this place?"*
> *"What street segment am I standing on?"*
> *"Are people being denied mortgages in this neighborhood because of race?"*

The answer is already waiting. We just made city data speakable.

---

## ✨ Key Features

- **🔊 Hands-Free Voice Interface** — Real-time bidirectional audio via Gemini Live through Meta Ray-Ban glasses
- **🍽️ Restaurant Health Intelligence** — Live NYC DOHMH inspection grades, violations, and scores via Socrata API
- **🗺️ Street & Location Lookup** — NYC Street Centerline dataset for block IDs, geometry, and street segment data
- **🏦 HMDA Fair Lending Analysis** — Mortgage approval/denial rates by race, lender, income, loan type, and property type from CFPB data (187K+ records)
- **💬 WhatsApp Integration** — Send query results to 3.14B+ WhatsApp users with zero app install required
- **🤖 Multi-Agent Architecture** — Google ADK orchestrator with three specialized A2A sub-agents on Cloud Run
- **🔁 Nightly Data Refresh** — Cloud Scheduler auto-refreshes HMDA datasets for freshness
- **🌍 40+ Languages** — Gemini Live auto-detects language natively

---

## 🏗️ System Architecture

```
[Meta Ray-Ban Glasses]
        ↓  1fps video + mic audio
[Pixel Glass iOS App] ←→ [Gemini Live API]
        ↓  tool calls
[Cloud Run: Orchestrator Agent (ADK + A2A)]
        ↓  A2A delegation
┌────────────────────────────────────────────┐
│  🍽️ Restaurant Agent │ 🗺️ Location Agent  │
│  🏦 HMDA Agent       │ 💬 WhatsApp Agent  │
└────────────────────────────────────────────┘
        ↓  data
[Vertex AI RAG Engine] [Socrata Live API]
[BigQuery]  [Cloud Storage]  [Firestore]
        ↑
[WhatsApp Business API] → [Pub/Sub] → [Cloud Run Worker]
```

### The Five Layers

| Layer | Component | Role |
|-------|-----------|------|
| 👓 **Eyes** | Meta Ray-Ban Glasses + iOS App | Stream 1fps video + live audio |
| 🧠 **Brain** | Gemini 3.1 Flash Lite | Real-time voice, video, and reasoning |
| ⚙️ **Agents** | Google ADK Orchestrator + 3 Sub-agents | Route queries to the right specialist |
| 📊 **Data** | Socrata APIs + GCS/BigQuery (HMDA) | Live city data retrieval |
| 💬 **Reach** | WhatsApp Cloud API + Pub/Sub | Deliver results to any device |

---

## 📊 Datasets

| Dataset | Source | Access Method |
|---------|--------|---------------|
| NYC Restaurant Inspections | DOHMH / NYC Open Data | Live Socrata API (`43nn-pn8j`) |
| NYC Street Centerline (LION) | NYC City Government | Bundled GeoJSON (~122K segments) + Socrata API (`2v4z-66xt`) |
| HMDA Mortgage Data (2007–present) | CFPB — NYC MSA 35620 | GCS (`tourgemini-hmda-data`) → lazy-loaded in-memory cache (187K+ records) |

All datasets are public, free, and updated automatically.

---

## 🛠️ Tech Stack

<details>
<summary><strong>Hardware</strong></summary>

- **Meta Ray-Ban Smart Glasses** — 1fps JPEG camera stream, bidirectional mic/speaker
- **Meta DAT (Device Access Toolkit) SDK** — exposes video frames and audio to the iOS app
- **iPhone (iOS)** — runs the Pixel Glass app, bridges hardware to cloud services

</details>

<details>
<summary><strong>AI & Agent Framework</strong></summary>

- **Google Gemini 2.5 Flash Lite** — LLM for reasoning, tool routing, and multimodal processing
- **Gemini Live API** — real-time bidirectional audio + video over WebSocket
- **Google ADK v0.3.0+** — multi-agent framework, orchestrator + A2A sub-agents
- **A2A Protocol** — inter-agent communication; each Cloud Run agent exposes `/.well-known/agent.json` + `/run`
- **Vertex AI Agent Engine** — managed runtime for ADK deployment

</details>

<details>
<summary><strong>GCP Services</strong></summary>

| Service | Purpose |
|---------|---------|
| Cloud Run | Serverless hosting for all agents + webhook handler |
| Vertex AI | Gemini calls, RAG Engine, Agent Engine |
| BigQuery | Structured SQL queries over HMDA dataset |
| Cloud Storage | Raw HMDA CSV files + embeddings |
| Pub/Sub | Decouples WhatsApp webhook from agent processing |
| Firestore | Per-user conversation history and session state |
| Secret Manager | All API keys and tokens |
| Artifact Registry | Docker images for Cloud Run |
| Cloud Build | CI/CD container builds |
| Cloud Scheduler | Nightly HMDA data refresh |
| Cloud Logging + Monitoring | Full observability |

</details>

<details>
<summary><strong>Backend</strong></summary>

- Python 3.12, FastAPI, Flask, Docker
- `google-adk>=0.3.0`, `google-cloud-aiplatform`, `google-cloud-pubsub`
- `httpx>=0.27.0` for live Socrata API calls

</details>

---

## 📁 Project Structure

```
Pixel-Glass/
│
├── README.md
├── .gitignore
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
│
├── agents/                             # Core ADK agent implementations
│   ├── agent.py                        # Orchestrator — routes all requests via A2A
│   ├── socrata_client.py               # Async NYC Open Data (Socrata) client
│   ├── centerline.py                   # Street Centerline spatial index (GPS lookup)
│   ├── download_centerline.py          # Script to fetch centerline GeoJSON (~120MB)
│   ├── verify_hmda.py                  # HMDA setup verification script
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   ├── data/
│   │   └── centerline.geojson          # NYC Street Centerline dataset (~122K segments)
│   ├── restaurant_agent/               # Socrata restaurant health queries (3 tools)
│   │   └── agent.py
│   ├── location_agent/                 # Street segment / GPS location queries (5 tools)
│   │   └── agent.py
│   ├── hmda_agent/                     # HMDA fair-lending analysis (6 tools)
│   │   └── agent.py
│   ├── test_agents.py                  # Root orchestrator integration tests
│   ├── test_socrata.py                 # Socrata API client tests
│   ├── test_hmda_agent.py              # HMDA agent end-to-end tests
│   └── test_hmda_only.py              # Simplified HMDA tests
│
├── gcp/                                # Legacy: Flask-based HMDA prototype (superseded by agents/hmda_agent)
│   ├── hmda_rag_agent.py               # Original Flask app (deprecated)
│   ├── create_rag_corpus.py
│   ├── deploy.sh
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── assets/                             # Images and visual assets
│   ├── cover.png
│   ├── teaserimage.png
│   ├── how.png
│   ├── dev_mode.png
│   └── title.png
│
└── test_query.py                       # Quick end-to-end test script
```

---

## 🚀 Quickstart

### Prerequisites

- Google AI API key (Gemini) — from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- GCP project with billing enabled (for HMDA data from GCS)
- `gcloud` CLI authenticated
- Python 3.12+
- Meta Ray-Ban glasses (hardware) + iOS device
- NYC Open Data app token — free at [data.cityofnewyork.us](https://data.cityofnewyork.us/profile/edit/developer_settings) *(optional, increases rate limits)*

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/pixel-glass.git
cd pixel-glass/agents
cp .env.example .env
# Fill in GOOGLE_API_KEY and optionally SOCRATA_APP_TOKEN
```

### 2. Download Street Centerline Data

```bash
cd agents
python download_centerline.py
# Downloads NYC Street Centerline GeoJSON (~120MB) to data/centerline.geojson
```

### 3. Run Agents Locally

```bash
# Test the orchestrator locally
adk run agents

# Or start as an A2A HTTP server
adk api_server --port 8080 ./agents
```

### 4. Deploy to Cloud Run

```bash
cd agents

# Deploy sub-agents first
adk deploy cloud_run --project $PROJECT_ID --region us-central1 ./restaurant_agent
adk deploy cloud_run --project $PROJECT_ID --region us-central1 ./location_agent
adk deploy cloud_run --project $PROJECT_ID --region us-central1 ./hmda_agent

# Update sub-agent URLs in agent.py, then deploy orchestrator
adk deploy cloud_run --project $PROJECT_ID --region us-central1 .
```

Alternatively, deploy the whole agents directory directly:

```bash
gcloud run deploy pixel-glass-agents \
  --source ./agents \
  --region us-central1 \
  --set-env-vars="GOOGLE_API_KEY=$GOOGLE_API_KEY,SOCRATA_APP_TOKEN=$SOCRATA_APP_TOKEN"
```

### 5. Deploy WhatsApp Webhook Handler

```bash
gcloud run deploy webhook-handler \
  --source ./webhook_handler \
  --region us-central1 \
  --set-secrets="WHATSAPP_TOKEN=whatsapp-token:latest,GEMINI_KEY=gemini-key:latest"
```

### 7. Connect the iOS App

Update your iOS app tool config with your Cloud Run orchestrator URL:

```json
{
  "name": "nyc_assistant",
  "description": "Search NYC restaurants, streets, or housing/HMDA data",
  "endpoint": "https://YOUR-ORCHESTRATOR-URL.run.app/run",
  "method": "POST",
  "auth": "Bearer YOUR_CLOUD_RUN_ID_TOKEN"
}
```

### 8. Test End-to-End

```bash
# Run unit and integration tests
pytest agents/

# Quick smoke test
python test_query.py
```

---

## 🔧 Agent Tools

### 🍽️ Restaurant Agent
| Tool | Description |
|------|-------------|
| `search_restaurants()` | Search by name, zip, cuisine, borough, grade (up to 50 results) |
| `get_restaurant_details(camis)` | Full inspection history by CAMIS ID |
| `get_grade_summary()` | Grade distribution (A/B/C) in an area |

### 🗺️ Location Agent
| Tool | Description |
|------|-------------|
| `search_streets()` | Find streets by name, borough, zip code |
| `find_nearby_streets()` | Find streets within radius of GPS coordinates (ideal for glasses) |
| `get_route_segments()` | Get ordered street geometry for navigation |
| `get_streets_in_area()` | List all streets in a borough/zip code |
| `find_restaurants_on_street()` | Find restaurants on a specific street |

### 🏦 HMDA Agent
| Tool | Description |
|------|-------------|
| `get_lending_summary()` | Overall NYC approval/denial/withdrawal rates |
| `get_denial_rates_by_lender()` | Statistics broken down by lender (top 10 by volume) |
| `get_denial_rates_by_income()` | Analysis by income bracket (Under $50K to Over $250K) |
| `get_lending_disparities_by_race()` | Fair Housing Act compliance — approval/denial by race/ethnicity |
| `get_lending_by_loan_type()` | Stats for conventional, FHA, VA, USDA loans |
| `get_lending_by_property_type()` | Analysis by single-family, multifamily, manufactured homes, etc. |

---

## 💡 Example Queries

```
"What's the health grade of this restaurant?"
→ Live Socrata API → grade, violations, last inspection date

"What street am I on?"
→ Centerline spatial index → block ID, segment name, traffic direction

"What are the mortgage denial rates for Black applicants in zip 11212?"
→ Vertex AI RAG + BigQuery → full HMDA analysis in <15 seconds

"Send that to my WhatsApp."
→ WhatsApp Cloud API → delivered instantly
```

---

## 📈 Impact by the Numbers

| Metric | Before | After |
|--------|--------|-------|
| Restaurant health lookup | 3–5 min | 5 seconds |
| Street/location lookup | 2–3 min | 3 seconds |
| HMDA zip analysis | 30–60 min | 15 seconds |
| Fair-lending report | days | real-time |
| Infrastructure cost/month | ~$890 | ~$65 (93% reduction) |
| Fair-lending reports (per nonprofit) | $5K–$25K each | $0 |

---

## 🗺️ Roadmap

- **Week 2** — Core live: restaurants, location, HMDA, WhatsApp, full GCP deployment
- **Month 2** — HPD housing violations + NYC 311 complaints as new agents
- **Month 3** — Android support · Multi-user WhatsApp sessions · Long-term memory
- **Month 4** — Spanish, Mandarin & Bengali via Gemini auto-detection
- **Month 5–6** — Looker Studio dashboard for nonprofits · Partner portal
- **Month 6+** — Chicago. Los Angeles. Houston. Same codebase. New city in under a week.

---

## 👥 Team

| Name | Email |
|------|-------|------|
| **Yash Jain** | yashjain778@gmail.com |
| **Subhradeep Acharjee** | subhradeep246@gmail.com |
| **Somaditya Singh** | somadisingh13@gmail.com |
| **Tanmay Sahu** | ts3915789@gmail.com |

---

## 🤝 Partners & Powered By

<div align="center">

Google Cloud · Vertex AI · Gemini Live · Meta Ray-Ban
WhatsApp Business API · NYC Open Data · CFPB HMDA · Google ADK

</div>

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Every city has public data. Every city deserves this.

⭐ Star this repo if you believe information should meet people where they are.

</div>
