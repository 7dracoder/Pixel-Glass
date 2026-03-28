import Foundation
import CoreLocation

// MARK: - ADK Connection State

enum ADKConnectionState: Equatable {
    case notConfigured
    case checking
    case connected
    case unreachable(String)
}

// MARK: - A2A Request Models

struct ADKRunRequest: Encodable {
    let appName: String
    let userId: String
    let sessionId: String
    let newMessage: ADKMessage

    struct ADKMessage: Encodable {
        let role: String
        let parts: [ADKPart]
    }

    struct ADKPart: Encodable {
        let text: String
    }

    enum CodingKeys: String, CodingKey {
        case appName = "app_name"
        case userId = "user_id"
        case sessionId = "session_id"
        case newMessage = "new_message"
    }
}

// MARK: - ADK Agent Bridge

@MainActor
class ADKAgentBridge: ObservableObject {
    @Published var connectionState: ADKConnectionState = .notConfigured
    @Published var lastToolCallStatus: ToolCallStatus = .idle

    private let session: URLSession
    private let pingSession: URLSession
    private let userId: String
    private(set) var sessionId: String

    private static let userIdKey = "com.pixelglass.adkUserId"

    init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 120
        self.session = URLSession(configuration: config)

        let pingConfig = URLSessionConfiguration.default
        pingConfig.timeoutIntervalForRequest = 5
        self.pingSession = URLSession(configuration: pingConfig)

        // Stable userId: stored in UserDefaults, consistent across launches
        if let stored = UserDefaults.standard.string(forKey: ADKAgentBridge.userIdKey) {
            self.userId = stored
        } else {
            let newId = UUID().uuidString
            UserDefaults.standard.set(newId, forKey: ADKAgentBridge.userIdKey)
            self.userId = newId
        }

        // Per-session sessionId: new UUID each time
        self.sessionId = UUID().uuidString
    }

    func resetSession() {
        sessionId = UUID().uuidString
    }

    // MARK: - Base URL

    private var baseURL: String {
        SettingsManager.shared.adkAgentURL
    }

    private var isConfigured: Bool {
        !baseURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    // MARK: - Health Check

    func checkConnection() async {
        guard isConfigured else {
            connectionState = .notConfigured
            return
        }
        connectionState = .checking
        guard let url = URL(string: baseURL) else {
            connectionState = .unreachable("Invalid URL")
            return
        }
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        do {
            let (_, response) = try await pingSession.data(for: request)
            if let http = response as? HTTPURLResponse, (200...299).contains(http.statusCode) {
                connectionState = .connected
                NSLog("[ADKBridge] Agent reachable (HTTP %d)", http.statusCode)
            } else {
                connectionState = .unreachable("Unexpected response")
            }
        } catch {
            connectionState = .unreachable(error.localizedDescription)
            NSLog("[ADKBridge] Agent unreachable: %@", error.localizedDescription)
        }
    }

    // MARK: - Send Query

    func sendQuery(query: String, category: String?, location: CLLocation?) async -> ToolResult {
        lastToolCallStatus = .executing("nyc_lookup")

        guard isConfigured, let url = URL(string: "\(baseURL)/run") else {
            lastToolCallStatus = .failed("nyc_lookup", "ADK agent URL not configured")
            return .failure("ADK agent URL not configured")
        }

        // Enrich query with GPS if location-relevant
        var enrichedQuery = query
        if let loc = location, isLocationRelevant(query: query, category: category) {
            enrichedQuery = "User's current GPS location: latitude=\(loc.coordinate.latitude), longitude=\(loc.coordinate.longitude). \(query)"
        }

        // Build A2A request
        let body = ADKRunRequest(
            appName: "agents",
            userId: userId,
            sessionId: sessionId,
            newMessage: .init(role: "user", parts: [.init(text: enrichedQuery)])
        )

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            request.httpBody = try JSONEncoder().encode(body)
        } catch {
            lastToolCallStatus = .failed("nyc_lookup", "Failed to encode request")
            return .failure("Failed to encode request")
        }

        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                lastToolCallStatus = .failed("nyc_lookup", "Invalid response")
                return .failure("Invalid response from ADK agent")
            }
            guard (200...299).contains(http.statusCode) else {
                let msg = "ADK agent returned HTTP \(http.statusCode)"
                NSLog("[ADKBridge] %@", msg)
                lastToolCallStatus = .failed("nyc_lookup", msg)
                return .failure(msg)
            }

            let text = extractTextFromResponse(data)
            NSLog("[ADKBridge] Agent result: %@", String(text.prefix(200)))
            lastToolCallStatus = .completed("nyc_lookup")
            return .success(text)
        } catch {
            let msg = "ADK agent unreachable: \(error.localizedDescription)"
            NSLog("[ADKBridge] %@", msg)
            lastToolCallStatus = .failed("nyc_lookup", error.localizedDescription)
            return .failure(msg)
        }
    }

    // MARK: - Response Parsing

    func extractTextFromResponse(_ data: Data) -> String {
        guard let raw = String(data: data, encoding: .utf8) else {
            return "Unable to parse response"
        }

        var texts: [String] = []

        // Try SSE format first (data: {...}\n lines)
        let lines = raw.components(separatedBy: "\n")
        for line in lines {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            guard trimmed.hasPrefix("data:") else { continue }
            let jsonStr = String(trimmed.dropFirst(5)).trimmingCharacters(in: .whitespaces)
            guard let jsonData = jsonStr.data(using: .utf8),
                  let json = try? JSONSerialization.jsonObject(with: jsonData) as? [String: Any],
                  let content = json["content"] as? [String: Any],
                  let parts = content["parts"] as? [[String: Any]] else { continue }
            for part in parts {
                if let text = part["text"] as? String, !text.isEmpty {
                    texts.append(text)
                }
            }
        }

        // Fallback: try parsing as plain JSON
        if texts.isEmpty, let json = try? JSONSerialization.jsonObject(with: data) {
            if let arr = json as? [[String: Any]] {
                for event in arr {
                    if let content = event["content"] as? [String: Any],
                       let parts = content["parts"] as? [[String: Any]] {
                        for part in parts {
                            if let text = part["text"] as? String, !text.isEmpty {
                                texts.append(text)
                            }
                        }
                    }
                }
            } else if let dict = json as? [String: Any],
                      let text = dict["text"] as? String, !text.isEmpty {
                texts.append(text)
            }
        }

        return texts.isEmpty ? "No response from agent" : texts.joined(separator: "\n")
    }

    // MARK: - Location Relevance

    func isLocationRelevant(query: String, category: String?) -> Bool {
        if category == "location" { return true }
        let locationKeywords = [
            "near me", "nearby", "around here", "where am i",
            "this street", "this area", "close to me", "my location"
        ]
        let lower = query.lowercased()
        return locationKeywords.contains { lower.contains($0) }
    }
}
