# Tasks

## Task 1: Create ADKAgentBridge HTTP Client
- [x] 1.1 Create `ADKAgentBridge.swift` with `ADKConnectionState` enum and `@Published` properties for `connectionState` and `lastToolCallStatus`
- [x] 1.2 Implement `ADKRunRequest` Codable struct with `app_name`, `user_id`, `session_id`, and `new_message` fields using snake_case CodingKeys
- [x] 1.3 Implement stable `userId` generation (random UUID stored in UserDefaults) and per-session `sessionId` UUID generation
- [x] 1.4 Implement `sendQuery(query:category:location:)` method that constructs the A2A request, sends HTTP POST to `{baseURL}/run`, and returns `ToolResult`
- [x] 1.5 Implement `extractTextFromResponse(_:)` that parses both SSE format (`data: {json}` lines) and plain JSON fallback
- [x] 1.6 Implement `checkConnection()` health check method that updates `connectionState`
- [x] 1.7 Implement `isLocationRelevant(query:category:)` helper with keyword matching for GPS enrichment decisions

## Task 2: Create LocationManager
- [x] 2.1 Create `LocationManager.swift` wrapping `CLLocationManager` with `@Published` properties for `lastLocation` and `authorizationStatus`
- [x] 2.2 Implement `requestPermission()` and `getCurrentLocation()` methods
- [x] 2.3 Implement `CLLocationManagerDelegate` to update published properties on authorization and location changes

## Task 3: Update ToolCallRouter for Dual Routing
- [x] 3.1 Add `adkBridge: ADKAgentBridge` and `locationManager: LocationManager` parameters to `ToolCallRouter` initializer
- [x] 3.2 Update `handleToolCall` to route `"nyc_lookup"` calls to `ADKAgentBridge.sendQuery()` with query, category, and location from `LocationManager`
- [x] 3.3 Preserve existing `"execute"` routing to `OpenClawBridge.delegateTask()`
- [x] 3.4 Add fallback for unknown tool names returning `ToolResult.failure`

## Task 4: Update ToolDeclarations with nyc_lookup
- [x] 4.1 Add `nycLookup` static declaration in `ToolDeclarations` with `query` (required) and `category` (optional enum) parameters
- [x] 4.2 Update `allDeclarations()` to return both `execute` and `nycLookup`

## Task 5: Update SettingsManager and GeminiConfig
- [x] 5.1 Add `adkAgentURL` property to `SettingsManager` persisted in UserDefaults with empty default
- [x] 5.2 Add `adkAgentURL` accessor and `isADKConfigured` computed property to `GeminiConfig`
- [x] 5.3 Update `defaultSystemInstruction` in `GeminiConfig` with dual-tool routing rules for `nyc_lookup` and `execute`
- [x] 5.4 Add `adkAgentURL` key to `SettingsManager.resetAll()`

## Task 6: Wire Up GeminiSessionViewModel
- [x] 6.1 Add `LocationManager` and `ADKAgentBridge` instances to `GeminiSessionViewModel`
- [x] 6.2 Update `startSession()` to initialize `ADKAgentBridge`, run health check, and pass both bridges + location manager to `ToolCallRouter`
- [x] 6.3 Add `adkConnectionState` published property and poll it in the state observation loop
- [x] 6.4 Update `stopSession()` to clean up ADK bridge state

## Task 7: Add Settings UI for ADK Agent URL
- [x] 7.1 Add ADK Agent URL text field to the Settings view bound to `SettingsManager.adkAgentURL`

## Task 8: Write Unit Tests
- [ ] 8.1 Test `isLocationRelevant()` with various query strings and categories (property: GPS enrichment/non-enrichment)
- [ ] 8.2 Test `extractTextFromResponse()` with SSE format, plain JSON, empty data, and malformed input (property: response parsing robustness)
- [ ] 8.3 Test `ADKRunRequest` serialization produces correct JSON structure (property: A2A request construction validity)
- [ ] 8.4 Test `ToolCallRouter` routing logic for `"nyc_lookup"`, `"execute"`, and unknown tool names (property: tool routing determinism)
- [ ] 8.5 Test `ADKAgentBridge` returns correct `ToolResult` for 2xx, non-2xx, and network error scenarios (property: HTTP status to result type mapping)
