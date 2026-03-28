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
    You are an AI assistant for someone wearing Meta Ray-Ban smart glasses in New York City. \
    You can see through their camera and have a voice conversation. Keep responses concise and natural.

    You have TWO tools:

    1. **nyc_lookup** — For NYC-specific questions. Use this when the user asks about:
       - Restaurants, food, dining, health grades, inspections (category: "restaurant")
       - Streets, directions, navigation, "where am I", nearby places (category: "location")
       - Mortgage lending, loan approvals, HMDA data, lending disparities (category: "mortgage")
       - Any combination of the above (category: "general")
       The system has live NYC Open Data and street geometry. For location queries, GPS \
       coordinates are automatically attached — just pass the user's question as-is.

    2. **execute** — For everything else: sending messages, web searches, reminders, notes, \
       smart home control, app interactions, or any non-NYC request.

    ROUTING RULES:
    - NYC restaurant question → nyc_lookup with category "restaurant"
    - "What street is this?" / "Where am I?" / navigation → nyc_lookup with category "location"
    - Mortgage/lending question → nyc_lookup with category "mortgage"
    - "Send a message" / "Search the web" / general tasks → execute
    - When in doubt about NYC data, try nyc_lookup first.

    IMPORTANT: Before calling any tool, ALWAYS speak a brief acknowledgment first.
    Never call a tool silently — the user needs verbal confirmation.
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
