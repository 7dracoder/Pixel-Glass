# VisionClaw — Complete Setup Guide

This guide walks a first-time developer through setting up and running the full Pixel Glass iOS app pipeline from scratch.

---

## How the App Works

```
[You speak into glasses / iPhone mic]
        ↓
[Gemini Live API — WebSocket]
        ↓  decides which tool to call
        ├── nyc_lookup → ADKAgentBridge → Cloud Run agents (restaurants, streets, mortgages)
        └── execute    → OpenClawBridge → OpenClaw on your Mac (messages, web search, etc.)
        ↓
[Gemini speaks the result back through your glasses / iPhone speaker]
```

Two tool paths:
- `nyc_lookup` — NYC-specific queries. The app attaches your GPS coordinates and POSTs to your ADK agent server. Results come back as structured JSON which Gemini reads aloud.
- `execute` — Everything else. Sent to OpenClaw running on your Mac, which handles WhatsApp, web search, reminders, smart home, etc.

---

## Prerequisites

- Mac running macOS
- iPhone with iOS 16+
- Xcode 15+ (see Step 1)
- Meta Ray-Ban smart glasses (optional — app works in iPhone-only mode)
- Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

---

## Step 1 — Install Xcode

1. Open the App Store on your Mac, search for **Xcode**, install it (~15GB)
2. Open Xcode once to accept the license agreement
3. Install command line tools:
   ```bash
   xcode-select --install
   ```
4. Open `pixelglass-live/samples/CameraAccess/CameraAccess.xcodeproj` in Xcode

---

## Step 2 — Install OpenClaw

OpenClaw is the Mac-side agent that handles general tasks (WhatsApp, web search, etc.).

1. Download and install OpenClaw from [openclaw.ai](https://openclaw.ai)
2. Open OpenClaw and complete the setup wizard
3. Find your gateway token:
   ```bash
   cat ~/.openclaw/openclaw.json | grep -A3 '"auth"'
   ```
4. Note your Mac's local hostname:
   ```bash
   scutil --get LocalHostName
   # e.g. "johns-macbook-pro" → use "http://johns-macbook-pro.local"
   ```
5. Make sure OpenClaw is running (menu bar app)

---

## Step 3 — Configure Secrets

```bash
cp pixelglass-live/samples/CameraAccess/CameraAccess/Secrets.swift.example \
   pixelglass-live/samples/CameraAccess/CameraAccess/Secrets.swift
```

Edit `Secrets.swift`:

```swift
enum Secrets {
  // REQUIRED — https://aistudio.google.com/apikey
  static let geminiAPIKey = "YOUR_GEMINI_API_KEY"

  // OpenClaw — your Mac's address and tokens
  static let openClawHost = "http://your-mac.local"   // or ngrok URL (see Step 4)
  static let openClawPort = 18789
  static let openClawHookToken = "YOUR_GATEWAY_TOKEN"
  static let openClawGatewayToken = "YOUR_GATEWAY_TOKEN"

  // WebRTC signaling server
  static let webrtcSignalingURL = "ws://localhost:8080"

  // ADK Agent URL — NYC data agents
  // Cloud Run: "https://your-agents-xxxx-uc.a.run.app"
  // Local:     "http://your-mac.local:8081"
  static let adkAgentURL = "https://your-agents-xxxx-uc.a.run.app"
}
```

`Secrets.swift` is gitignored and will never be committed.

---

## Step 4 — Network Setup (ngrok for public WiFi)

If your iPhone can't reach your Mac directly (public WiFi, university network), use ngrok.

```bash
brew install ngrok
ngrok config add-authtoken YOUR_NGROK_TOKEN   # from ngrok.com (free tier works)
ngrok http 18789
```

You'll see:
```
Forwarding  https://xxxx-xxxx.ngrok-free.app -> http://localhost:18789
```

Use that URL as `openClawHost` in `Secrets.swift`. On the same local WiFi you can skip ngrok and use `http://your-mac.local:18789` directly.

---

## Step 5 — Start the WebRTC Signaling Server

```bash
cd pixelglass-live/samples/CameraAccess/server
npm install
npm start
```

Runs on port 8080. If port 8080 is busy:
```bash
lsof -ti :8080 | xargs kill
npm start
```

---

## Step 6 — ADK Agent URL

Set `adkAgentURL` in `Secrets.swift` to your NYC data agents.

**Option A — Cloud Run (recommended):**
```swift
static let adkAgentURL = "https://agents-c5nlrwz5vq-ue.a.run.app"
```

**Option B — Run locally:**
```bash
cd agents
pip install -r requirements.txt
adk api_server --port 8081 .
```
```swift
static let adkAgentURL = "http://your-mac.local:8081"
```

Test the agents work:
```bash
cd agents
python3 test_pipeline.py
```

---

## Step 7 — Build and Run the iOS App

1. Open `CameraAccess.xcodeproj` in Xcode
2. Connect your iPhone via USB
3. Select your iPhone as the build target
4. Xcode → Signing & Capabilities → select your Apple ID team
5. **Cmd+R** to build and run

If you see "Missing package product" errors:
```
File → Packages → Reset Package Caches
File → Packages → Resolve Package Versions
```
Wait for packages to download, then rebuild.

---

## Step 8 — First Launch

1. Tap the gear icon (⚙️) top-right
2. Verify Gemini API key, OpenClaw host, ADK Agent URL are loaded
3. If you changed `Secrets.swift` after a previous run → tap **Reset to Defaults** → Save
4. Tap **Start on iPhone** (or connect glasses)
5. Grant microphone and location permissions when prompted
6. Start talking

---

## Testing the Pipeline

**Test NYC agents:**
```bash
cd agents && python3 test_pipeline.py
```
Expected: list of restaurants near your coordinates.

**Test a voice query in the app:**
Say: *"Find Italian restaurants near me"*

Watch Xcode console for:
```
[ToolCall] Received: nyc_lookup (id: ...)
[ADKBridge] Agent result: Found 10 restaurant(s)...
```

---

## Common Problems & Fixes

**"Missing package product" (WebRTC, MWDATCore)**
```
File → Packages → Reset Package Caches
File → Packages → Resolve Package Versions
```

**App says "service not available" for every query**
System prompt is cached from an old version.
- Settings → Reset to Defaults → Save → restart session

**Location queries return no GPS**
- iPhone Settings → Privacy & Security → Location Services → VisionClaw → "While Using"
- App falls back to a hardcoded NYC location if GPS is unavailable

**OpenClaw shows as unreachable**
- Make sure OpenClaw is running on your Mac
- On public WiFi: start ngrok (`ngrok http 18789`) and update `openClawHost`
- Rebuild the app after changing `Secrets.swift`

**ADK agent returns 404**
The app POSTs to `POST /` (root), not `/run`. Make sure `adkAgentURL` has no path suffix — just the base URL.

**SSL certificate error downloading centerline data**
```bash
/Applications/Python\ 3.*/Install\ Certificates.command
```
Or download manually: [NYC Open Data Centerline](https://data.cityofnewyork.us/City-Government/Centerline/3mf9-qshr) → Export → GeoJSON → save to `agents/data/centerline.geojson`

**Port 8080 already in use**
```bash
lsof -ti :8080 | xargs kill
```

**Stale Xcode build / DerivedData issues**
```bash
rm -rf ~/Library/Developer/Xcode/DerivedData
```
Then Xcode: Product → Clean Build Folder (Cmd+Shift+K) → rebuild.

---

## Full Pipeline Checklist

- [ ] `Secrets.swift` created with valid Gemini API key
- [ ] `openClawHost` set to Mac's local address or ngrok URL
- [ ] `openClawGatewayToken` set (from `~/.openclaw/openclaw.json`)
- [ ] `adkAgentURL` set to Cloud Run URL or local `adk api_server`
- [ ] OpenClaw running on Mac
- [ ] ngrok running if on public WiFi: `ngrok http 18789`
- [ ] WebRTC server running: `npm start` in `server/`
- [ ] App built and running on iPhone
- [ ] Location permission granted ("While Using")
- [ ] System prompt reset to defaults in Settings
- [ ] Xcode console open to monitor logs
