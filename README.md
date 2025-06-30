# AI Hedge Fund

This project consists of a Python backend server and a Next.js frontend client for an AI-powered hedge fund system. 

## Project Structure

- `server/` - Python backend server with MCP support
- `client/` - Next.js frontend application

## Features

- 🤖 **13+ AI Analyst Agents** - Warren Buffett, Peter Lynch, Charlie Munger, and more
- 📊 **Real-time Financial Data** - Polygon.io, Finnhub, Alpaca integration  
- 🔄 **Model Context Protocol** - Direct integration with Claude Desktop and other AI assistants
- 📈 **Advanced Analytics** - Financial ratios, sentiment analysis, risk management
- ⚡ **Streaming Analysis** - Real-time progress updates during analysis

## Server Setup

1. Navigate to the server directory:
```bash
cd server
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file in the server directory with the following variables:
```env
OPENAI_API_KEY=your_openai_api_key
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_API_SECRET=your_alpaca_api_secret
POLYGON_API_KEY=your_polygon_api_key <- recommended
```

4. Start the server:
- On Windows:
```bash
.\start.bat
```
- On macOS/Linux:
```bash
./start.sh
```

## MCP Server Setup (AI Assistant Integration)

The AI Hedge Fund now supports **Model Context Protocol (MCP)** for direct integration with AI assistants like Claude Desktop. The MCP server is a TypeScript/Node.js application that connects to the Python Flask server.

### Quick MCP Setup

1. **Start the Python Flask server first:**
```bash
cd server
# On Windows:
.\start.bat
# On macOS/Linux:
./start.sh
```

2. **Install and build the MCP server:**
```bash
cd mcp
npm install
npm run build
```

3. **Start the MCP server:**
```bash
cd mcp
npm start
```

### Claude Desktop Integration

Add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "hedge-fund-ai": {
      "command": "node",
      "args": ["dist/index.js"],
      "cwd": "/path/to/your/ai-hedge-fund/mcp"
    }
  }
}
```

### MCP Capabilities

Once connected, you can ask Claude:

- **"Generate analysis for Apple stock using multiple AI analysts"**
- **"Check the health status of the hedge fund system"**
- **"Get system status and available endpoints"**
- **"Search for ticker symbols"**
- **"Get available analysts for analysis"**

## Detailed MCP Documentation

### Prerequisites

#### Required API Keys

1. **Polygon.io API Key** - For financial data
   - Sign up: https://polygon.io/
   - Free tier available, paid plans recommended for production

2. **OpenAI API Key** - For AI analysis
   - Sign up: https://platform.openai.com/
   - Required for the analyst agents

3. **Finnhub API Key** (Optional) - Additional financial data
   - Sign up: https://finnhub.io/
   - Free tier available

### Available MCP Tools

#### 1. `generate_analysis`
Generate comprehensive hedge fund analysis using multiple AI analysts.

**Parameters:**
- `tickers` (required): Array of stock ticker symbols
- `start_date` (optional): Analysis start date (YYYY-MM-DD)
- `end_date` (optional): Analysis end date (YYYY-MM-DD)
- `initial_cash` (optional): Initial cash amount for portfolio
- `margin_requirement` (optional): Margin requirement percentage
- `show_reasoning` (optional): Whether to show detailed reasoning
- `selected_analysts` (optional): List of analyst names to use
- `model_name` (optional): LLM model name to use
- `model_provider` (optional): LLM provider (OpenAI, etc.)

#### 2. `get_health`
Check the health status of the hedge fund AI server.

#### 3. `get_system_status`
Get comprehensive system status and available endpoints.

#### 4. `search_tickers`
Search for stock ticker symbols.

**Parameters:**
- `query` (required): Search query for ticker symbols

#### 5. `get_available_analysts`
Get list of available AI analysts for analysis.

### Usage Examples

#### Basic Stock Analysis
```
Can you analyze Apple stock using Warren Buffett's methodology?
```

#### Multi-Stock Comparison
```
Compare Apple, Google, and Microsoft using both value and growth investing approaches. Show detailed reasoning.
```

#### Financial Data Deep Dive
```
Get comprehensive financial data for Tesla including all available metrics and ratios.
```

#### Market Sentiment Analysis
```
What's the recent market sentiment for NVIDIA based on the last week's news?
```

#### MCP Development Testing
```bash
cd mcp
yarn dev
```

## Client Setup

1. Navigate to the client directory:
```bash
cd client
```

2. Install dependencies:
```bash
yarn
```

3. Start the development server:
```bash
yarn dev
```

The client will be available at `http://localhost:3000`

## Environment Variables

### Server (.env)
Required environment variables for the server:
- `OPENAI_API_KEY`: Your OpenAI API key for AI analyst agents
- `POLYGON_API_KEY`: Your Polygon.io API key for financial data (recommended)
- `ALPACA_API_KEY`: Your Alpaca API key for trading (optional)
- `ALPACA_API_SECRET`: Your Alpaca API secret (optional)
- `FINNHUB_API_KEY`: Your Finnhub API key for additional data (optional)

## Development

- **Flask Server** (Python backend) runs on `http://localhost:5000` by default
- **MCP Server** (Node.js) communicates via stdio with MCP clients
- **Client** (Next.js frontend) runs on `http://localhost:3000` by default

### MCP Development Mode

For MCP server development:
```bash
cd mcp
npm run dev  # Watch mode with TypeScript compilation
```

### Available AI Analysts

The system includes 13+ AI analyst agents:
- **Value Investors**: Warren Buffett, Ben Graham, Charlie Munger
- **Growth Investors**: Peter Lynch, Phil Fisher, Cathie Wood  
- **Specialists**: Michael Burry, Stanley Druckenmiller, Bill Ackman
- **Technical/Fundamental**: Technical Analyst, Fundamentals Analyst, Sentiment Analyst, Valuation Analyst

## Demo
![image](https://github.com/user-attachments/assets/c5fdaf4c-d650-4c17-b2c1-c3720e32a847)
![image](https://github.com/user-attachments/assets/80bd0fa6-cfda-4f3d-b2a8-ef66a0eddc68)

