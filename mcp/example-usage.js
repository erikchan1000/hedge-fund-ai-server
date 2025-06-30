// Example usage of the Hedge Fund AI MCP tools
// This file demonstrates how to interact with the MCP server

// Example 1: Generate analysis for multiple stocks
const analysisExample = {
  name: "generate_analysis",
  arguments: {
    tickers: ["AAPL", "MSFT", "GOOGL", "TSLA"],
    start_date: "2024-01-01",
    end_date: "2024-12-31",
    initial_cash: 100000,
    selected_analysts: ["warren_buffett", "ben_graham", "technical_analyst"],
    show_reasoning: true,
    model_name: "gpt-4o",
    model_provider: "OpenAI"
  }
};

// Example 2: Check server health
const healthExample = {
  name: "get_health",
  arguments: {}
};

// Example 3: Get system status
const statusExample = {
  name: "get_system_status",
  arguments: {}
};

// Example 4: Get available analysts
const analystsExample = {
  name: "get_available_analysts",
  arguments: {}
};

// Example 5: Search for tickers
const searchExample = {
  name: "search_tickers",
  arguments: {
    query: "AAPL"
  }
};

// Example 6: Portfolio analysis with specific analysts
const portfolioAnalysisExample = {
  name: "generate_analysis",
  arguments: {
    tickers: ["JPM", "BAC", "WFC", "GS"],
    start_date: "2024-06-01",
    end_date: "2024-12-31",
    initial_cash: 50000,
    selected_analysts: ["michael_burry", "stanley_druckenmiller"],
    show_reasoning: true,
    margin_requirement: 0.5
  }
};

// Example 7: Tech sector analysis
const techAnalysisExample = {
  name: "generate_analysis",
  arguments: {
    tickers: ["NVDA", "AMD", "INTC", "QCOM"],
    start_date: "2024-01-01",
    end_date: "2024-12-31",
    initial_cash: 75000,
    selected_analysts: ["cathie_wood", "technical_analyst", "sentiment_analyst"],
    show_reasoning: true
  }
};

console.log("Example MCP tool calls:");
console.log("1. Multi-stock analysis:", JSON.stringify(analysisExample, null, 2));
console.log("2. Health check:", JSON.stringify(healthExample, null, 2));
console.log("3. System status:", JSON.stringify(statusExample, null, 2));
console.log("4. Available analysts:", JSON.stringify(analystsExample, null, 2));
console.log("5. Ticker search:", JSON.stringify(searchExample, null, 2));
console.log("6. Portfolio analysis:", JSON.stringify(portfolioAnalysisExample, null, 2));
console.log("7. Tech sector analysis:", JSON.stringify(techAnalysisExample, null, 2)); 