# Requirements Document

## Introduction

This document specifies the requirements for integrating three existing Google ADK agents (restaurant, location, HMDA) with the Pixel Glass iOS app. The integration adds a direct HTTP bridge (`ADKAgentBridge`) that calls the ADK orchestrator's `/run` endpoint, a new `nyc_lookup` tool declared to Gemini alongside the existing `execute` tool, automatic GPS coordinate injection for location queries, and configurable URL support for local development vs Cloud Run deployment. The existing OpenClaw path is preserved as a fallback for non-NYC queries.

## Glossary

- **ADKAgentBridge**: iOS HTTP client class that communicates with the ADK orchestrator agent's `/run` endpoint
- **ToolCallRouter**: iOS class that dispatches Gemini tool calls to the appropriate backend (ADKAgentBridge or OpenClawBridge)
- **OpenClawBridge**: Existing iOS HTTP client class that communicates with the OpenClaw gateway for general tasks
- **LocationManager**: iOS class wrapping CLLocationManager to provide on-demand GPS coordinates
- **SettingsManager**: iOS singleton managing user-configurable settings persisted in UserDefaults
- **GeminiConfig**: iOS enum providing configuration accessors and system prompt constants
- **ToolDeclarations**: iOS enum that defines tool schemas sent to Gemini during session setup
- **ADK_Orchestrator**: The Python-based `nyc_lookup_agent` root agent that delegates to sub-agents
- **A2A_Request**: The JSON payload sent to the ADK `/run` endpoint containing `app_name`, `user_id`, `session_id`, and `new_message`
- **GPS_Enrichment**: The process of prepending GPS coordinates to a query string before sending to the ADK agent

## Requirements

### Requirement 1: ADK Agent Bridge HTTP Client

**User Story:** As a Pixel Glass user, I want the app to communicate with NYC data agents, so that I can get live NYC restaurant, street, and mortgage information through voice queries.

#### Acceptance Criteria

1. WHEN a `nyc_lookup` tool call is received, THE ADKAgentBridge SHALL construct an HTTP POST request to the configured ADK agent URL appended with `/run`
2. WHEN constructing an A2A_Request, THE ADKAgentBridge SHALL include `app_name` set to `"agents"`, a stable `user_id`, a per-session `session_id`, and a `new_message` containing the query text
3. WHEN the ADK agent returns a 2xx HTTP status, THE ADKAgentBridge SHALL parse the response body and return a `ToolResult.success` containing the extracted text
4. IF the ADK agent returns a non-2xx HTTP status, THEN THE ADKAgentBridge SHALL return a `ToolResult.failure` containing the HTTP status code
5. IF the ADK agent is unreachable due to network error or timeout, THEN THE ADKAgentBridge SHALL return a `ToolResult.failure` with a descriptive error message without crashing the app
6. WHEN parsing the ADK response, THE ADKAgentBridge SHALL support both SSE format (`data: {json}` lines) and plain JSON format as fallback
7. IF the response body contains no extractable text, THEN THE ADKAgentBridge SHALL return a `ToolResult.success` with the message `"No response from agent"`

### Requirement 2: Tool Call Routing

**User Story:** As a Pixel Glass user, I want my voice queries to be automatically routed to the correct backend, so that NYC questions use the ADK agents and general tasks use OpenClaw.

#### Acceptance Criteria

1. WHEN a tool call with name `"nyc_lookup"` is received, THE ToolCallRouter SHALL route the call to ADKAgentBridge
2. WHEN a tool call with name `"execute"` is received, THE ToolCallRouter SHALL route the call to OpenClawBridge
3. IF a tool call with an unknown name is received, THEN THE ToolCallRouter SHALL return a `ToolResult.failure` indicating an unknown tool
4. THE ToolCallRouter SHALL send exactly one `toolResponse` back to Gemini for each non-cancelled tool call, containing the original `callId`
5. WHEN a `toolCallCancellation` is received for an in-flight ADK call, THE ToolCallRouter SHALL cancel the corresponding HTTP task

### Requirement 3: GPS Coordinate Injection

**User Story:** As a Pixel Glass user walking in NYC, I want the app to automatically include my GPS location when I ask location questions, so that I get relevant nearby results without stating my position.

#### Acceptance Criteria

1. WHEN a `nyc_lookup` query has `category` equal to `"location"`, THE ADKAgentBridge SHALL prepend the device GPS coordinates to the query text in the format `"User's current GPS location: latitude=<lat>, longitude=<lon>. <original_query>"`
2. WHEN a `nyc_lookup` query text contains location keywords such as `"near me"`, `"nearby"`, `"where am I"`, or `"this street"`, THE ADKAgentBridge SHALL prepend GPS coordinates regardless of the `category` value
3. WHILE the LocationManager has no available location (permission denied or location unavailable), THE ADKAgentBridge SHALL send the query without GPS enrichment
4. WHEN a `nyc_lookup` query has `category` equal to `"restaurant"` or `"mortgage"` and contains no location keywords, THE ADKAgentBridge SHALL send the query without GPS enrichment

### Requirement 4: Tool Declaration to Gemini

**User Story:** As a developer, I want the `nyc_lookup` tool declared to Gemini alongside `execute`, so that Gemini can route NYC queries to the correct tool.

#### Acceptance Criteria

1. WHEN a Gemini session is established, THE ToolDeclarations SHALL include both the `execute` tool and the `nyc_lookup` tool in the setup message
2. THE `nyc_lookup` tool declaration SHALL specify a required `query` parameter of type string and an optional `category` parameter with enum values `["restaurant", "location", "mortgage", "general"]`
3. THE `nyc_lookup` tool declaration SHALL include a description that mentions NYC restaurants, streets, neighborhoods, boroughs, and mortgage data

### Requirement 5: Configurable ADK Agent URL

**User Story:** As a developer, I want to configure the ADK agent URL in the app settings, so that I can switch between local development and Cloud Run deployment.

#### Acceptance Criteria

1. THE SettingsManager SHALL provide an `adkAgentURL` property persisted in UserDefaults with a default empty value
2. THE GeminiConfig SHALL expose an `adkAgentURL` accessor and an `isADKConfigured` computed property that returns true when the URL is non-empty
3. WHEN the ADK agent URL is empty or not configured, THE ADKAgentBridge SHALL report `ADKConnectionState.notConfigured`
4. WHEN the ADK agent URL is changed in settings, THE ADKAgentBridge SHALL use the new URL for subsequent requests without requiring an app restart

### Requirement 6: Updated System Prompt

**User Story:** As a Pixel Glass user, I want Gemini to understand when to use NYC data tools vs general tools, so that my queries are handled by the right backend.

#### Acceptance Criteria

1. THE GeminiConfig SHALL provide a default system instruction that describes both the `nyc_lookup` and `execute` tools with routing rules
2. THE default system instruction SHALL instruct Gemini to route NYC restaurant questions to `nyc_lookup` with category `"restaurant"`, street/navigation questions with category `"location"`, and mortgage questions with category `"mortgage"`
3. THE default system instruction SHALL instruct Gemini to route non-NYC tasks (messages, web searches, reminders) to the `execute` tool
4. THE default system instruction SHALL instruct Gemini to speak a brief verbal acknowledgment before calling any tool

### Requirement 7: Connection State and Health Check

**User Story:** As a Pixel Glass user, I want to see whether the NYC data service is reachable, so that I know if NYC queries will work.

#### Acceptance Criteria

1. WHEN a Gemini session starts, THE ADKAgentBridge SHALL perform a connection health check against the configured ADK agent URL
2. THE ADKAgentBridge SHALL publish its connection state as one of `notConfigured`, `checking`, `connected`, or `unreachable` with an error description
3. WHEN the health check receives a 2xx response, THE ADKAgentBridge SHALL set the connection state to `connected`
4. IF the health check fails, THEN THE ADKAgentBridge SHALL set the connection state to `unreachable` with the error description

### Requirement 8: Session Identity Management

**User Story:** As a developer, I want stable user identity and per-session IDs sent to the ADK agent, so that the agent can maintain conversation context within a session.

#### Acceptance Criteria

1. THE ADKAgentBridge SHALL generate a stable `userId` based on a random UUID stored in UserDefaults, consistent across app launches
2. WHEN a new Gemini session starts, THE ADKAgentBridge SHALL generate a new `sessionId` UUID
3. THE ADKAgentBridge SHALL include the `userId` and `sessionId` in every A2A_Request sent to the ADK orchestrator

### Requirement 9: Location Permission Management

**User Story:** As a Pixel Glass user, I want the app to request location permission when needed, so that GPS-enriched queries work seamlessly.

#### Acceptance Criteria

1. WHEN the app first needs location data for a query, THE LocationManager SHALL request location authorization from the user
2. THE LocationManager SHALL expose the current authorization status for UI display
3. WHILE location authorization is granted, THE LocationManager SHALL provide the last-known GPS coordinates on demand without continuous tracking
