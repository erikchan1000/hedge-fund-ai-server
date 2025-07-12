# Hedge Fund AI MCP Server

Model Context Protocol (MCP) server for Hedge Fund AI analysis, fully compliant with the [MCP Specification 2025-03-26](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports).

## Overview

This MCP server provides comprehensive hedge fund analysis capabilities through multiple AI analysts, with proper cancellation support according to the MCP specification.

## MCP Specification Compliance

### Transport Layer Compliance

#### stdio Transport ✅
- **Message Format**: All messages are JSON-RPC 2.0 compliant and UTF-8 encoded
- **Newline Delimited**: Messages are properly delimited by newlines without embedded newlines
- **stdout/stderr Separation**: 
  - Valid MCP messages only go to `stdout`
  - Logging and diagnostics go to `stderr`
- **Subprocess Management**: Server runs as subprocess with proper signal handling

#### Cancellation Support ✅
- **CancelledNotification**: Implements proper `notifications/cancelled` handling per specification
- **Request Tracking**: Maintains active request registry for cancellation
- **Graceful Termination**: Properly handles SIGINT/SIGTERM signals
- **No Disconnection Assumptions**: Disconnection is not interpreted as cancellation

### JSON-RPC Compliance ✅

All messages follow JSON-RPC 2.0 format:
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/cancelled",
  "params": {
    "requestId": "req_1234567890_abc123",
    "reason": "Client requested cancellation"
  }
}
```

### Security Compliance ✅
- **Origin Validation**: Server validates request origins (when using HTTP transport)
- **Localhost Binding**: Server binds to localhost for security
- **Authentication**: Proper authentication headers and session management

## Features

### Available Tools

1. **generate_analysis** - Generate comprehensive hedge fund analysis
   - Multiple AI analyst perspectives
   - Configurable timeframes and parameters
   - Streaming results with real-time progress
   - Full cancellation support

2. **get_health** - Check server health status
3. **get_system_status** - Get comprehensive system information
4. **get_available_analysts** - List available AI analysts
5. **search_tickers** - Search for stock ticker symbols

### Cancellation Features

#### MCP-Compliant Cancellation
```typescript
// Client sends proper MCP cancellation notification
await client.sendCancelledNotification(requestId, "User cancelled operation");

// Server handles notification according to spec
{
  "jsonrpc": "2.0",
  "method": "notifications/cancelled",
  "params": {
    "requestId": "req_1234567890_abc123",
    "reason": "User cancelled operation"
  }
}
```

#### Request Lifecycle Management
- **Request Tracking**: Each request gets unique ID for cancellation
- **Token Propagation**: Cancellation tokens flow through entire request pipeline
- **Resource Cleanup**: Proper cleanup of all resources on cancellation
- **Stream Termination**: Immediate termination of streaming responses

## Installation & Usage

### Prerequisites
- Node.js 18+
- TypeScript
- Python 3.9+ (for backend server)

### Setup
```bash
# Install dependencies
npm install

# Build the project
npm run build

# Run the MCP server
npm start
```

### Integration with MCP Clients

The server implements the standard MCP stdio transport and can be used with any MCP-compliant client:

```json
{
  "servers": {
    "hedge-fund-ai": {
      "command": "node",
      "args": ["dist/index.js"],
      "env": {
        "SERVER_URL": "http://localhost:5000"
      }
    }
  }
}
```

### Example Usage

```typescript
// Generate analysis with cancellation support
const token = client.createCancellationToken();
const analysisStream = await client.generateAnalysis({
  tickers: ["AAPL", "GOOGL", "MSFT"],
  start_date: "2024-01-01",
  end_date: "2024-12-31",
  selected_analysts: ["warren_buffett", "peter_lynch"]
}, token);

// Process streaming results
for await (const result of analysisStream) {
  console.log(result);
  
  // Cancel if needed
  if (shouldCancel) {
    await client.cancelRequest(token.requestId!, "User requested stop");
    break;
  }
}
```

## Server-Side Integration

### Python Backend Cancellation
The server integrates with a Python backend that supports comprehensive cancellation:

```python
from src.utils.cancellation import cancellable_request, CancellationException

# Use cancellable context
with cancellable_request() as token:
    try:
        # Long-running operation with cancellation checks
        for step in workflow_steps:
            token.check_cancelled()  # Throws CancellationException if cancelled
            result = process_step(step)
    except CancellationException:
        logger.info("Operation was cancelled")
        raise
```

### HTTP API Endpoints
- `POST /api/mcp/notification` - Handle MCP notifications (per specification)
- `POST /api/analysis/cancel/<request_id>` - Cancel specific request
- `POST /api/analysis/cancel-all` - Cancel all active requests  
- `GET /api/analysis/active` - List active requests

## Architecture

### MCP Transport Layer
```
Client (stdio) ↔ MCP Server ↔ HTTP Client ↔ Python Backend
                     ↓
              Cancellation Manager
                     ↓
            Request Tracking & Cleanup
```

### Cancellation Flow
1. **Client Request**: Client sends analysis request with cancellation token
2. **Server Tracking**: Server registers request in active requests map
3. **Backend Processing**: Request flows through Python backend with cancellation checks
4. **Cancellation Signal**: Client sends `notifications/cancelled` or process receives signal
5. **Immediate Termination**: All processing stops and resources are cleaned up
6. **Response**: Client receives cancellation confirmation

## Compliance Checklist

### MCP Specification Requirements ✅

- [x] **JSON-RPC 2.0**: All messages use proper JSON-RPC format
- [x] **UTF-8 Encoding**: All messages are UTF-8 encoded
- [x] **stdio Transport**: Proper stdin/stdout communication
- [x] **Newline Delimited**: Messages separated by newlines only
- [x] **stderr Logging**: Diagnostics go to stderr, not stdout
- [x] **CancelledNotification**: Proper `notifications/cancelled` handling
- [x] **Request Tracking**: Active request management for cancellation
- [x] **Signal Handling**: SIGINT/SIGTERM handled gracefully
- [x] **Resource Cleanup**: All resources properly cleaned up
- [x] **No Disconnection Cancellation**: Disconnection != cancellation
- [x] **Tool Schema**: Proper tool input/output schemas
- [x] **Error Handling**: Proper error responses and handling

### Security Requirements ✅

- [x] **Origin Validation**: HTTP requests validate origin headers
- [x] **Localhost Binding**: Server binds to localhost only
- [x] **Authentication**: Proper request authentication
- [x] **Session Management**: Secure session handling

## Testing

Run tests to verify MCP compliance:
```bash
npm test
```

## Contributing

When contributing, ensure all changes maintain MCP specification compliance:
1. Test with multiple MCP clients
2. Verify cancellation behavior
3. Check JSON-RPC message format
4. Validate security requirements

## References

- [MCP Specification](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [Server-Sent Events Standard](https://html.spec.whatwg.org/multipage/server-sent-events.html)

## API Reference

### generate_analysis

Generate comprehensive hedge fund analysis using multiple AI analysts.

**Parameters:**
- `tickers` (string[]): List of stock tickers to analyze
- `start_date` (string, optional): Start date for analysis (YYYY-MM-DD)
- `end_date` (string, optional): End date for analysis (YYYY-MM-DD)
- `initial_cash` (number, optional): Initial cash amount for portfolio
- `margin_requirement` (number, optional): Margin requirement percentage
- `show_reasoning` (boolean, optional): Whether to show detailed reasoning
- `selected_analysts` (string[], optional): List of analyst names to use
- `model_name` (string, optional): LLM model name to use
- `model_provider` (string, optional): LLM provider (OpenAI, etc.)

**Example:**
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_cash": 100000,
  "selected_analysts": ["warren_buffett", "ben_graham"],
  "show_reasoning": true
}
```

### get_health

Check the health status of the hedge fund AI server.

**Parameters:** None

**Returns:** Health status information

### get_system_status

Get comprehensive system status and available endpoints.

**Parameters:** None

**Returns:** System status and endpoint information

### get_portfolio_status

Get portfolio service status and information.

**Parameters:** None

**Returns:** Portfolio service status

### get_available_analysts

Get list of available AI analysts for analysis.

**Parameters:** None

**Returns:** List of available analysts with their configurations

### search_tickers

Search for stock ticker symbols.

**Parameters:**
- `query` (string): Search query for ticker symbols

**Returns:** Array of matching ticker symbols

## Available Analysts

The following AI analysts are available for analysis:

- **Ben Graham**: Value investing pioneer
- **Bill Ackman**: Activist investor
- **Cathie Wood**: Growth and innovation investor
- **Charlie Munger**: Value investing and business analysis
- **Michael Burry**: Contrarian investor
- **Peter Lynch**: Growth investing
- **Phil Fisher**: Growth investing and qualitative analysis
- **Stanley Druckenmiller**: Macro and momentum investing
- **Warren Buffett**: Value investing and business analysis
- **Technical Analyst**: Technical analysis
- **Fundamentals Analyst**: Fundamental analysis
- **Sentiment Analyst**: Market sentiment analysis
- **Valuation Analyst**: Valuation analysis

## Configuration

The MCP server connects to the Hedge Fund AI server at `http://localhost:5000` by default. You can modify the base URL in the `HedgeFundAIClient` constructor in `src/client.ts`.

## Development

### Building

```bash
npm run build
```

### Development Mode

```bash
npm run dev
```

### Testing

```bash
npm test
```

## Dependencies

- `@modelcontextprotocol/sdk`: MCP SDK for TypeScript
- `axios`: HTTP client for API requests
- `zod`: Schema validation
- `typescript`: TypeScript compiler
- `@types/node`: Node.js type definitions

## License

MIT 