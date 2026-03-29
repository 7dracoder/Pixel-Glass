import Foundation

enum GeminiConfig {
  static let websocketBaseURL = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
  static let model = "models/gemini-2.5-flash-native-audio-preview-12-2025"

  static let inputAudioSampleRate: Double = 16000
  static let outputAudioSampleRate: Double = 24000
  static let audioChannels: UInt32 = 1
  static let audioBitsPerSample: UInt32 = 16

  static let videoFrameInterval: TimeInterval = 1.0
  static let videoJPEGQuality: CGFloat = 0.5

  static var systemInstruction: String { SettingsManager.shared.geminiSystemPrompt }

  static let defaultSystemInstruction = """
    You are an AI assistant for someone wearing smart glasses in New York City. \
    You can see through their camera and have a voice conversation. Keep responses concise and natural.

    You have TWO tools. You MUST call a tool for every user request — never respond without using a tool first.

    1. **nyc_lookup** — Use for ANY location, restaurant, street, or mortgage question:
       - "Where am I?" / "What street is this?" / "What's nearby?" → category: "location"
       - Restaurant, food, dining questions → category: "restaurant"
       - Mortgage/lending questions → category: "mortgage"
       - Mixed or unclear → category: "general"
       GPS coordinates are automatically attached to your query — just pass the user's question as-is.

    2. **execute** — Use for EVERYTHING else: sending messages, web searches, reminders, notes, \
       smart home control, app interactions, general tasks.

    MANDATORY RULES:
    - ALWAYS call a tool before responding. Never answer directly without a tool call.
    - For location/nearby questions → ALWAYS call nyc_lookup with category "location".
    - For general tasks → ALWAYS call execute. Never say the service is unavailable.
    - If unsure which tool → use execute.
    - Speak a brief acknowledgment BEFORE calling the tool (e.g. "Let me check that for you.").
    - NEVER say "I cannot do that", "service not available", or "I don't have access". Always use a tool instead.
    """

  // User-configurable values (Settings screen overrides, falling back to Secrets.swift)
  static var apiKey: String { SettingsManager.shared.geminiAPIKey }
  static var openClawHost: String { SettingsManager.shared.openClawHost }
  static var openClawPort: Int { SettingsManager.shared.openClawPort }
  static var openClawHookToken: String { SettingsManager.shared.openClawHookToken }
  static var openClawGatewayToken: String { SettingsManager.shared.openClawGatewayToken }

  static func websocketURL() -> URL? {
    guard apiKey != "YOUR_GEMINI_API_KEY" && !apiKey.isEmpty else { return nil }
    return URL(string: "\(websocketBaseURL)?key=\(apiKey)")
  }

  static var isConfigured: Bool {
    return apiKey != "YOUR_GEMINI_API_KEY" && !apiKey.isEmpty
  }

  static var isOpenClawConfigured: Bool {
    return openClawGatewayToken != "YOUR_OPENCLAW_GATEWAY_TOKEN"
      && !openClawGatewayToken.isEmpty
      && openClawHost != "http://YOUR_MAC_HOSTNAME.local"
  }

  static var adkAgentURL: String { SettingsManager.shared.adkAgentURL }

  static var isADKConfigured: Bool {
    return !adkAgentURL.isEmpty
  }
}
