import Foundation

@MainActor
class ToolCallRouter {
  private let bridge: OpenClawBridge
  private let adkBridge: ADKAgentBridge
  private let locationManager: LocationManager
  private var inFlightTasks: [String: Task<Void, Never>] = [:]

  init(bridge: OpenClawBridge, adkBridge: ADKAgentBridge, locationManager: LocationManager) {
    self.bridge = bridge
    self.adkBridge = adkBridge
    self.locationManager = locationManager
  }

  /// Route a tool call from Gemini to the appropriate backend.
  func handleToolCall(
    _ call: GeminiFunctionCall,
    sendResponse: @escaping ([String: Any]) -> Void
  ) {
    let callId = call.id
    let callName = call.name

    NSLog("[ToolCall] Received: %@ (id: %@) args: %@",
          callName, callId, String(describing: call.args))

    let task = Task { @MainActor in
      let result: ToolResult

      switch callName {
      case "nyc_lookup":
        let query = call.args["query"] as? String ?? ""
        let category = call.args["category"] as? String
        let location = locationManager.getCurrentLocation()
        result = await adkBridge.sendQuery(query: query, category: category, location: location)

      case "execute":
        let taskDesc = call.args["task"] as? String ?? String(describing: call.args)
        result = await bridge.delegateTask(task: taskDesc, toolName: callName)

      default:
        result = .failure("Unknown tool: \(callName)")
      }

      guard !Task.isCancelled else {
        NSLog("[ToolCall] Task %@ was cancelled, skipping response", callId)
        return
      }

      NSLog("[ToolCall] Result for %@ (id: %@): %@",
            callName, callId, String(describing: result))

      let response = self.buildToolResponse(callId: callId, name: callName, result: result)
      sendResponse(response)

      self.inFlightTasks.removeValue(forKey: callId)
    }

    inFlightTasks[callId] = task
  }

  /// Cancel specific in-flight tool calls (from toolCallCancellation)
  func cancelToolCalls(ids: [String]) {
    for id in ids {
      if let task = inFlightTasks[id] {
        NSLog("[ToolCall] Cancelling in-flight call: %@", id)
        task.cancel()
        inFlightTasks.removeValue(forKey: id)
      }
    }
    bridge.lastToolCallStatus = .cancelled(ids.first ?? "unknown")
  }

  /// Cancel all in-flight tool calls (on session stop)
  func cancelAll() {
    for (id, task) in inFlightTasks {
      NSLog("[ToolCall] Cancelling in-flight call: %@", id)
      task.cancel()
    }
    inFlightTasks.removeAll()
  }

  // MARK: - Private

  private func buildToolResponse(
    callId: String,
    name: String,
    result: ToolResult
  ) -> [String: Any] {
    return [
      "toolResponse": [
        "functionResponses": [
          [
            "id": callId,
            "name": name,
            "response": result.responseValue
          ]
        ]
      ]
    ]
  }
}
