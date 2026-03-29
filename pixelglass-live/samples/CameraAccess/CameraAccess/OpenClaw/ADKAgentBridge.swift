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

        guard isConfigured, let url = URL(string: baseURL) else {
            lastToolCallStatus = .failed("nyc_lookup", "ADK agent URL not configured")
            return .failure("ADK agent URL not configured")
        }

        // Enrich query with GPS if location-relevant
        var enrichedQuery = query
        if let loc = location, isLocationRelevant(query: query, category: category) {
            enrichedQuery = "User's current GPS location: latitude=\(loc.coordinate.latitude), longitude=\(loc.coordinate.longitude). \(query)"
        }

        // Map category to mode expected by the server
        let mode: String
        switch category {
        case "restaurant": mode = "restaurant"
        case "location":   mode = "location"
        default:           mode = "restaurant" // default fallback
        }

        let body: [String: Any] = [
            "message": enrichedQuery,
            "mode": mode
        ]

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
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
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return String(data: data, encoding: .utf8) ?? "Unable to parse response"
        }

        // Restaurant response: {"count": N, "restaurants": [...], "query": "..."}
        if let restaurants = json["restaurants"] as? [[String: Any]], !restaurants.isEmpty {
            var lines: [String] = []
            let count = json["count"] as? Int ?? restaurants.count
            lines.append("Found \(count) restaurant(s):")
            for r in restaurants.prefix(5) {
                let name    = r["name"]            as? String ?? "Unknown"
                let address = r["address"]         as? String ?? ""
                let borough = r["borough"]         as? String ?? ""
                let cuisine = r["cuisine"]         as? String ?? ""
                let grade   = r["grade"]           as? String ?? "N/A"
                lines.append("• \(name) — \(cuisine), \(address) \(borough), Grade: \(grade)")
            }
            return lines.joined(separator: "\n")
        }

        // Street/location response: {"count": N, "streets": [...], "query": "..."}
        if let streets = json["streets"] as? [[String: Any]], !streets.isEmpty {
            var lines: [String] = []
            let count = json["count"] as? Int ?? streets.count
            lines.append("Found \(count) street(s):")
            for s in streets.prefix(5) {
                let name    = s["full_name"]  as? String ?? s["street"] as? String ?? "Unknown"
                let borough = s["boro_name"]  as? String ?? s["borough"] as? String ?? ""
                let zip     = s["zip_code"]   as? String ?? "N/A"
                lines.append("• \(name), \(borough) (zip: \(zip))")
            }
            return lines.joined(separator: "\n")
        }

        // Error response
        if let error = json["error"] as? String { return "Error: \(error)" }

        // Fallback: return raw JSON as string
        return String(data: data, encoding: .utf8) ?? "No response from agent"
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
