import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { HedgeFundAIClient } from "./client.js";
import {
  GenerateAnalysisTool,
  GetHealthTool,
  GetSystemStatusTool,
  SearchTickersTool,
} from "./types.js";

// Custom cancellation error for MCP compliance
class CancelledError extends Error {
  constructor(message: string = "Request was cancelled") {
    super(message);
    this.name = "CancelledError";
  }
}

// MCP-compliant cancellation token interface
interface CancellationToken {
  isCancelled: boolean;
  cancel(): void;
  onCancellation(callback: () => void): void;
}

// MCP-compliant cancellation token implementation
class MCPCancellationToken implements CancellationToken {
  private _isCancelled = false;
  private _callbacks: (() => void)[] = [];

  get isCancelled(): boolean {
    return this._isCancelled;
  }

  cancel(): void {
    if (!this._isCancelled) {
      this._isCancelled = true;
      this._callbacks.forEach(callback => {
        try {
          callback();
        } catch (error) {
          console.error('Error in cancellation callback:', error);
        }
      });
      this._callbacks = [];
    }
  }

  onCancellation(callback: () => void): void {
    if (this._isCancelled) {
      callback();
    } else {
      this._callbacks.push(callback);
    }
  }
}

export class HedgeFundAITools {
  private server: Server;
  private client: HedgeFundAIClient;
  private activeRequests: Map<string, CancellationToken> = new Map();

  constructor() {
    this.server = new Server({
      name: "hedge-fund-ai-tools",
      version: "1.0.0",
      capabilities: {
        tools: {},
      },
    });

    this.client = new HedgeFundAIClient();

    this.setupToolHandlers();
    this.setupNotificationHandlers();
  }

  private setupNotificationHandlers() {
    // Handle MCP CancelledNotification according to specification
    // Using a more generic approach since the SDK may not have specific schemas for all notifications
    this.server.setNotificationHandler(
      {
        method: "notifications/cancelled",
        params: {
          type: "object",
          properties: {
            requestId: { type: "string" },
            reason: { type: "string" }
          }
        }
      } as any,
      async (notification: any) => {
        const { requestId, reason } = notification.params || {};
        
        if (requestId && this.activeRequests.has(requestId)) {
          console.error(`Received cancellation for request: ${requestId}, reason: ${reason || 'No reason provided'}`);
          const token = this.activeRequests.get(requestId);
          if (token) {
            token.cancel();
          }
          this.activeRequests.delete(requestId);
        }
      }
    );
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "generate_analysis",
            description:
              "Generate comprehensive hedge fund analysis using multiple AI analysts",
            inputSchema: {
              type: "object",
              properties: {
                tickers: {
                  type: "array",
                  items: { type: "string" },
                  description: "List of stock tickers to analyze"
                },
                start_date: {
                  type: "string",
                  description: "Start date for analysis (YYYY-MM-DD)"
                },
                end_date: {
                  type: "string",
                  description: "End date for analysis (YYYY-MM-DD)"
                },
                initial_cash: {
                  type: "number",
                  description: "Initial cash amount for portfolio"
                },
                margin_requirement: {
                  type: "number",
                  description: "Margin requirement percentage"
                },
                show_reasoning: {
                  type: "boolean",
                  description: "Whether to show detailed reasoning"
                },
                selected_analysts: {
                  type: "array",
                  items: { type: "string" },
                  description: "List of analyst names to use"
                },
                model_name: {
                  type: "string",
                  description: "LLM model name to use"
                },
                model_provider: {
                  type: "string",
                  description: "LLM provider (OpenAI, etc.)"
                }
              },
              required: ["tickers"]
            },
          },
          {
            name: "get_health",
            description: "Check the health status of the hedge fund AI server",
            inputSchema: {
              type: "object",
              properties: {},
              required: []
            },
          },
          {
            name: "get_system_status",
            description:
              "Get comprehensive system status and available endpoints",
            inputSchema: {
              type: "object",
              properties: {},
              required: []
            },
          },
          {
            name: "get_available_analysts",
            description: "Get list of available AI analysts for analysis",
            inputSchema: {
              type: "object",
              properties: {},
              required: []
            },
          },
          {
            name: "search_tickers",
            description: "Search for stock ticker symbols",
            inputSchema: {
              type: "object",
              properties: {
                query: {
                  type: "string",
                  description: "Search query for ticker symbols"
                }
              },
              required: ["query"]
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(
      CallToolRequestSchema,
      async (request: any) => {
        const { name, arguments: args } = request.params;
        const requestId = this.generateRequestId();
        const cancellationToken = new MCPCancellationToken();
        
        // Track the request for potential cancellation
        this.activeRequests.set(requestId, cancellationToken);
        
        try {
          let result;
          
          switch (name) {
            case "generate_analysis":
              result = await this.handleGenerateAnalysis(args as GenerateAnalysisTool, cancellationToken, requestId);
              break;

            case "get_health":
              result = await this.handleGetHealth(args as GetHealthTool, cancellationToken);
              break;

            case "get_system_status":
              result = await this.handleGetSystemStatus(args as GetSystemStatusTool, cancellationToken);
              break;

            case "get_available_analysts":
              result = await this.handleGetAvailableAnalysts(cancellationToken);
              break;

            case "search_tickers":
              result = await this.handleSearchTickers(args as SearchTickersTool, cancellationToken);
              break;

            default:
              throw new Error(`Unknown tool: ${name}`);
          }
          
          return result;
        } catch (error) {
          if (cancellationToken.isCancelled) {
            throw new CancelledError("Request was cancelled");
          }
          throw error;
        } finally {
          // Clean up the request tracking
          this.activeRequests.delete(requestId);
        }
      },
    );
  }

  private async handleGenerateAnalysis(args: GenerateAnalysisTool, cancellationToken: CancellationToken, requestId: string) {
    if (cancellationToken.isCancelled) {
      throw new CancelledError("Request was cancelled");
    }

    try {
      const analysisGenerator = await this.client.generateAnalysis({
        tickers: args.tickers,
        start_date: args.start_date,
        end_date: args.end_date,
        initial_cash: args.initial_cash ?? 100000.0,
        margin_requirement: args.margin_requirement ?? 0.0,
        show_reasoning: args.show_reasoning ?? false,
        selected_analysts: args.selected_analysts,
        model_name: args.model_name ?? "gpt-4o",
        model_provider: args.model_provider ?? "OpenAI",
      }, cancellationToken);

      const results: any[] = [];
      for await (const response of analysisGenerator) {
        if (cancellationToken.isCancelled) {
          throw new CancelledError("Request was cancelled");
        }
        results.push(response);
      }

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(results, null, 2),
          },
        ],
        _meta: {
          requestId: requestId
        }
      };
    } catch (error) {
      if (cancellationToken.isCancelled) {
        throw new CancelledError("Request was cancelled");
      }
      return {
        content: [
          {
            type: "text",
            text: `Error generating analysis: ${error instanceof Error ? error.message : "Unknown error"}`,
          },
        ],
        isError: true,
        _meta: {
          requestId: requestId
        }
      };
    }
  }

  private async handleGetHealth(args: GetHealthTool, cancellationToken: CancellationToken) {
    if (cancellationToken.isCancelled) {
      throw new CancelledError("Request was cancelled");
    }

    try {
      const health = await this.client.getHealth();
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(health, null, 2),
          },
        ],
      };
    } catch (error) {
      if (cancellationToken.isCancelled) {
        throw new CancelledError("Request was cancelled");
      }
      return {
        content: [
          {
            type: "text",
            text: `Error getting health status: ${error instanceof Error ? error.message : "Unknown error"}`,
          },
        ],
        isError: true
      };
    }
  }

  private async handleGetSystemStatus(args: GetSystemStatusTool, cancellationToken: CancellationToken) {
    if (cancellationToken.isCancelled) {
      throw new CancelledError("Request was cancelled");
    }

    try {
      const status = await this.client.getSystemStatus();
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(status, null, 2),
          },
        ],
      };
    } catch (error) {
      if (cancellationToken.isCancelled) {
        throw new CancelledError("Request was cancelled");
      }
      return {
        content: [
          {
            type: "text",
            text: `Error getting system status: ${error instanceof Error ? error.message : "Unknown error"}`,
          },
        ],
        isError: true
      };
    }
  }

  private async handleGetAvailableAnalysts(cancellationToken: CancellationToken) {
    if (cancellationToken.isCancelled) {
      throw new CancelledError("Request was cancelled");
    }

    try {
      const analysts = await this.client.getAvailableAnalysts();
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(analysts, null, 2),
          },
        ],
      };
    } catch (error) {
      if (cancellationToken.isCancelled) {
        throw new CancelledError("Request was cancelled");
      }
      return {
        content: [
          {
            type: "text",
            text: `Error getting available analysts: ${error instanceof Error ? error.message : "Unknown error"}`,
          },
        ],
        isError: true
      };
    }
  }

  private async handleSearchTickers(args: SearchTickersTool, cancellationToken: CancellationToken) {
    if (cancellationToken.isCancelled) {
      throw new CancelledError("Request was cancelled");
    }

    try {
      const tickers = await this.client.searchTickers(args.query);
      // Validate the response using the schema
      const { TickerSearchResultsSchema } = await import("./types.js");
      const validated = TickerSearchResultsSchema.parse(tickers);
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(validated, null, 2),
          },
        ],
      };
    } catch (error) {
      if (cancellationToken.isCancelled) {
        throw new CancelledError("Request was cancelled");
      }
      return {
        content: [
          {
            type: "text",
            text: `Error searching tickers: ${error instanceof Error ? error.message : "Unknown error"}`,
          },
        ],
        isError: true
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    
    // According to MCP spec, we should only write valid MCP messages to stdout
    // Logging should go to stderr
    console.error("Hedge Fund AI MCP server started using stdio transport");
    
    // Handle process termination gracefully per MCP stdio requirements
    process.on('SIGINT', () => {
      console.error('Received SIGINT, shutting down gracefully...');
      this.cleanup();
      process.exit(0);
    });

    process.on('SIGTERM', () => {
      console.error('Received SIGTERM, shutting down gracefully...');
      this.cleanup();
      process.exit(0);
    });
  }

  private cleanup() {
    // Cancel all active requests
    for (const [requestId, token] of this.activeRequests) {
      console.error(`Cancelling active request: ${requestId}`);
      token.cancel();
    }
    this.activeRequests.clear();
  }
}

// Start the server if this file is run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const tools = new HedgeFundAITools();
  tools.run().catch((error) => {
    console.error('Failed to start MCP server:', error);
    process.exit(1);
  });
}
