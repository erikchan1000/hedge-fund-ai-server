# Hedge Fund AI MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with the Hedge Fund AI analysis server.

## Features

This MCP server provides the following tools:

- **generate_analysis**: Generate comprehensive hedge fund analysis using multiple AI analysts
- **get_health**: Check the health status of the hedge fund AI server
- **get_system_status**: Get comprehensive system status and available endpoints
- **get_portfolio_status**: Get portfolio service status and information
- **get_available_analysts**: Get list of available AI analysts for analysis
- **search_tickers**: Search for stock ticker symbols

## Installation

1. Install dependencies:
```bash
npm install
```

2. Build the project:
```bash
npm run build
```

## Usage

### Running the MCP Server

```bash
npm start
```

### Using with MCP Clients

Add this to your MCP client configuration:

```json
{
  "mcpServers": {
    "hedge-fund-ai": {
      "command": "node",
      "args": ["dist/index.js"],
      "env": {}
    }
  }
}
```

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