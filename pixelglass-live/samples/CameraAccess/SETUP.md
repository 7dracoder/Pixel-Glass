# Setup Instructions

## Secrets Configuration

Before building the app, you need to create a `Secrets.swift` file with your API keys and tokens.

1. Copy the example file:
   ```bash
   cp CameraAccess/Secrets.swift.example CameraAccess/Secrets.swift
   ```

2. Edit `CameraAccess/Secrets.swift` and fill in your values:

| Key | Required | Description |
|-----|----------|-------------|
| `geminiAPIKey` | Yes | Your Gemini API key from [AI Studio](https://aistudio.google.com/apikey) |
| `openClawHost` | No | OpenClaw gateway hostname (e.g., `http://your-mac.local` or ngrok URL) |
| `openClawPort` | No | OpenClaw gateway port (default: 18789) |
| `openClawHookToken` | No | Token for OpenClaw webhook authentication |
| `openClawGatewayToken` | No | Token for OpenClaw gateway authentication |
| `webrtcSignalingURL` | No | WebRTC signaling server URL for live POV streaming |

The `Secrets.swift` file is gitignored and will not be committed to the repository.

## Optional: ADK Agent URL

For NYC data queries (restaurants, streets, mortgages), configure the ADK Agent URL in the app's Settings screen after launching. This can point to:
- Local development: `http://macbook.local:8080`
- Cloud Run deployment: `https://your-agent-xxxx-uc.a.run.app`
