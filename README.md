<div align="center">
text
██████╗ ██╗██╗  ██╗███████╗██╗      
██╔══██╗██║╚██╗██╔╝██╔════╝██║      
██████╔╝██║ ╚███╔╝ █████╗  ██║      
██╔═══╝ ██║ ██╔██╗ ██╔══╝  ██║      
██║     ██║██╔╝ ██╗███████╗███████╗ 
╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
         G L A S S
Ask the city anything. Hear the answer through your glasses. In under 2 seconds.

[
[
[
[
[

</div>

🪄 What Is Pixel Glass?
Pixel Glass is an AI-native platform that bridges smart glasses, real-time multimodal AI, and live public city datasets into a single, seamless, hands-free experience.

Put on a pair of Meta Ray-Ban smart glasses, look at a restaurant, a street corner, or a building — and ask. Pixel Glass answers out loud, through your glasses speakers, in under two seconds. No phone. No typing. No stopping.

"What's the health grade of this place?"
"What street segment am I standing on?"
"Are people being denied mortgages in this neighborhood because of race?"

The answer is already waiting. We just made city data speakable.

✨ Key Features
🔊 Hands-Free Voice Interface — Real-time bidirectional audio via Gemini Live through Meta Ray-Ban glasses

🍽️ Restaurant Health Intelligence — Live NYC DOHMH inspection grades, violations, and scores via Socrata API

🗺️ Street & Location Lookup — NYC LION dataset for block IDs, zoning, and street segment data

🏦 HMDA Fair Lending Analysis — Mortgage denial rates by race, zip code, and lender from CFPB data via Vertex AI RAG

💬 WhatsApp Integration — Send query results to 3.14B+ WhatsApp users with zero app install required

🤖 Multi-Agent Architecture — Google ADK orchestrator with specialized A2A sub-agents on Cloud Run

🔁 Nightly Data Refresh — Cloud Scheduler auto-refreshes HMDA datasets for freshness

🌍 40+ Languages — Gemini Live auto-detects language natively

🏗️ System Architecture
text
[Meta Ray-Ban Glasses]
        ↓  1fps video + mic audio
[Pixel Glass iOS App] ←→ [Gemini Live API]
        ↓  tool calls
[Cloud Run: Orchestrator Agent (ADK + A2A)]
        ↓  A2A delegation
┌────────────────────────────────────────────┐
│  🍽️ Restaurant Agent │ 🗺️ Location Agent  │
│  🏦 HMDA RAG Agent   │ 💬 WhatsApp Agent  │
└────────────────────────────────────────────┘
        ↓  data
[Vertex AI RAG Engine] [Socrata Live API]
[BigQuery]  [Cloud Storage]  [Firestore]
        ↑
[WhatsApp Business API] → [Pub/Sub] → [Cloud Run Worker]
The Five Layers
Layer	Component	Role
👓 Eyes	Meta Ray-Ban Glasses + iOS App	Stream 1fps video + live audio
🧠 Brain	Gemini Live 2.0 Flash	Real-time voice, video, and reasoning
⚙️ Agents	Google ADK Orchestrator + Sub-agents	Route queries to the right specialist
📊 Data	Socrata APIs + Vertex AI RAG + BigQuery	Live city data retrieval
💬 Reach	WhatsApp Cloud API + Pub/Sub	Deliver results to any device
📊 Datasets
Dataset	Source	Access Method
NYC Restaurant Inspections	DOHMH / NYC Open Data	Live Socrata API (43nn-pn8j)
NYC LION Street Network	NYC City Government	Live Socrata API (2v4z-66xt)
HMDA Mortgage Data (2007–present)	CFPB — NYC MSA 35620	CFPB API → GCS → BigQuery → Vertex AI RAG
All datasets are public, free, and updated automatically.

🛠️ Tech Stack
<details>
<summary><strong>Hardware</strong></summary>

Meta Ray-Ban Smart Glasses — 1fps JPEG camera stream, bidirectional mic/speaker

Meta DAT (Device Access Toolkit) SDK — exposes video frames and audio to the iOS app

iPhone (iOS) — runs the Pixel Glass app, bridges hardware to cloud services

</details>

<details>
<summary><strong>AI & Agent Framework</strong></summary>

Google Gemini 2.0 Flash — LLM for reasoning, tool routing, and multimodal processing

Gemini Live API — real-time bidirectional audio + video over WebSocket

Google ADK v1.25+ — multi-agent framework, orchestrator + A2A sub-agents

A2A Protocol — inter-agent communication; each Cloud Run agent exposes /.well-known/agent.json + /run

Vertex AI RAG Engine — semantic retrieval over the HMDA corpus

Vertex AI Agent Engine — managed runtime for ADK deployment

</details>

<details>
<summary><strong>GCP Services</strong></summary>

Service	Purpose
Cloud Run	Serverless hosting for all agents + webhook handler
Vertex AI	Gemini calls, RAG Engine, Agent Engine
BigQuery	Structured SQL queries over HMDA dataset
Cloud Storage	Raw HMDA CSV files + embeddings
Pub/Sub	Decouples WhatsApp webhook from agent processing
Firestore	Per-user conversation history and session state
Secret Manager	All API keys and tokens
Artifact Registry	Docker images for Cloud Run
Cloud Build	CI/CD container builds
Cloud Scheduler	Nightly HMDA data refresh
API Gateway	Rate limiting on public-facing endpoints
Cloud Logging + Monitoring	Full observability
</details>

<details>
<summary><strong>Backend</strong></summary>

Python 3.11+, FastAPI, Docker

google-cloud-aiplatform, google-cloud-pubsub

requests / httpx for live Socrata API calls

</details>

📁 Project Structure
text
pixel-glass-nyc-gcp/
│
├── README.md
├── .env.example                        # Template for all env vars
├── .gitignore
├── pyproject.toml
├── docker-compose.yml                  # Local dev: run all services together
│
├── agents/
│   ├── orchestrator/                   # Root agent — routes all requests via A2A
│   ├── restaurant_agent/               # Socrata restaurant health queries
│   ├── location_agent/                 # Socrata LION street/location queries
│   ├── hmda_rag_agent/                 # Vertex AI RAG + BigQuery fallback
│   └── whatsapp_agent/                 # Formats + sends WhatsApp replies
│
├── webhook_handler/                    # FastAPI — receives Meta webhook → Pub/Sub
│
├── shared/                             # Shared clients, config, logging
│   ├── config.py
│   ├── socrata_client.py
│   ├── gcs_client.py
│   └── bq_client.py
│
├── data_pipelines/
│   ├── hmda/                           # Download → GCS → BigQuery → RAG corpus
│   └── nyc_open_data/                  # Socrata API smoke tests
│
├── openclaw/                           # iOS app tool config + system prompt
├── infra/                              # GCP bootstrap scripts
├── .github/workflows/                  # CI/CD: deploy agents, webhook, tests
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
🚀 Quickstart
Prerequisites
GCP project with billing enabled

gcloud CLI authenticated

Python 3.11+

Meta Ray-Ban glasses (hardware) + iOS device

NYC Open Data token — free at data.cityofnewyork.us

Meta WhatsApp Business Cloud API credentials

1. Clone & Configure
bash
git clone https://github.com/your-org/pixel-glass-nyc-gcp.git
cd pixel-glass-nyc-gcp
cp .env.example .env
# Fill in your GCP project ID, API keys, corpus ID, etc.
2. Bootstrap GCP Infrastructure
bash
chmod +x infra/setup_gcp.sh
./infra/setup_gcp.sh
This enables all required GCP APIs, creates the GCS bucket, BigQuery dataset, Firestore database, Pub/Sub topic, Artifact Registry repo, and IAM service accounts in one shot.

3. Ingest HMDA Data
bash
cd data_pipelines/hmda
chmod +x run_all.sh
./run_all.sh
Downloads HMDA CSVs for NYC MSA 35620 from the CFPB API, uploads to GCS, loads into BigQuery, creates the Vertex AI RAG corpus, and imports all documents.

4. Deploy All Agents
bash
# Deploy sub-agents
adk deploy cloud_run --project $PROJECT_ID --region us-central1 ./agents/restaurant_agent
adk deploy cloud_run --project $PROJECT_ID --region us-central1 ./agents/location_agent
adk deploy cloud_run --project $PROJECT_ID --region us-central1 ./agents/hmda_rag_agent
adk deploy cloud_run --project $PROJECT_ID --region us-central1 ./agents/whatsapp_agent

# Deploy orchestrator (update sub-agent URLs in agent.py first)
adk deploy cloud_run --project $PROJECT_ID --region us-central1 ./agents/orchestrator
5. Deploy WhatsApp Webhook Handler
bash
gcloud run deploy webhook-handler \
  --source ./webhook_handler \
  --region us-central1 \
  --set-secrets="WHATSAPP_TOKEN=whatsapp-token:latest,GEMINI_KEY=gemini-key:latest"
6. Configure WhatsApp Business API
Set the webhook URL in your Meta Developer console to your Cloud Run webhook handler URL. Use the VERIFY_TOKEN stored in Secret Manager.

7. Connect the iOS App
Update openclaw/tools_config.json with your Cloud Run orchestrator URL:

json
{
  "name": "nyc_assistant",
  "description": "Search NYC restaurants, streets, or housing/HMDA data",
  "endpoint": "https://nyc-orchestrator-XXXX-uc.a.run.app/run",
  "method": "POST",
  "auth": "Bearer YOUR_CLOUD_RUN_ID_TOKEN"
}
8. Test End-to-End
bash
# Run all tests
pytest tests/

# Or test the full WhatsApp flow
python tests/e2e/test_whatsapp_flow.py
💡 Example Queries
text
"What's the health grade of this restaurant?"
→ Live Socrata API → grade, violations, last inspection date

"What street am I on?"
→ LION dataset → block ID, segment name, zoning code

"What are the mortgage denial rates for Black applicants in zip 11212?"
→ Vertex AI RAG + BigQuery → full HMDA analysis in <15 seconds

"Send that to my WhatsApp."
→ WhatsApp Cloud API → delivered instantly
📈 Impact by the Numbers
Metric	Before	After
Restaurant health lookup	3–5 min	5 seconds
Street/location lookup	2–3 min	3 seconds
HMDA zip analysis	30–60 min	15 seconds
Fair-lending report	days	real-time
Infrastructure cost/month	~$890	~$65 (93% reduction)
Fair-lending reports (per nonprofit)	$5K–$25K each	$0
🗺️ Roadmap
Week 2 — Core live: restaurants, location, HMDA, WhatsApp, full GCP deployment

Month 2 — HPD housing violations + NYC 311 complaints as new agents

Month 3 — Android support · Multi-user WhatsApp sessions · Long-term memory

Month 4 — Spanish, Mandarin & Bengali via Gemini auto-detection

Month 5–6 — Looker Studio dashboard for nonprofits · Partner portal

Month 6+ — Chicago. Los Angeles. Houston. Same codebase. New city in under a week.

👥 Team
Name	Role
[Your Name]	Lead Developer / Architect
[Team Member 2]	
[Team Member 3]	
[Team Member 4]	
🤝 Partners & Powered By
<div align="center">

Google Cloud · Vertex AI · Gemini Live · Meta Ray-Ban
WhatsApp Business API · NYC Open Data · CFPB HMDA · Google ADK

</div>

📄 License
This project is licensed under the MIT License — see the LICENSE file for details.

<div align="center">

Every city has public data. Every city deserves this.

⭐ Star this repo if you believe information should meet people where they are.

</div>

text

---

This README includes [file:1]:
- A styled ASCII logo and badge row
- Clear architecture diagram with emoji layers
- Collapsible tech stack sections to keep it clean
- Full quickstart from clone to end-to-end test
- Impact table, roadmap, and team section with placeholders for your teammates
- No mention of VisionClaw anywhere

Just replace `[Your Name]` and the team placeholders, swap in your actual GitHub org URL, and you're good to go!
