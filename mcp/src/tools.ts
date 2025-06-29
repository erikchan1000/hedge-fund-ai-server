import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { HedgeFundAIClient } from './client.js';
import {
  GenerateAnalysisToolSchema,
  GetHealthToolSchema,
  GetSystemStatusToolSchema,
  GetPortfolioStatusToolSchema,
  GetAvailableAnalystsToolSchema,
  SearchTickersToolSchema,
  GenerateAnalysisTool,
  GetHealthTool,
  GetSystemStatusTool,
  GetPortfolioStatusTool,
  GetAvailableAnalystsTool,
  SearchTickersTool
} from './types.js';

export class HedgeFundAITools {
  private server: Server;
  private client: HedgeFundAIClient;

  constructor() {
    this.server = new Server(
      {
        name: 'hedge-fund-ai-tools',
        version: '1.0.0',
        capabilities: {
          tools: {},
        },
      }
    );

    this.client = new HedgeFundAIClient();

    this.setupToolHandlers();
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'generate_analysis',
            description: 'Generate comprehensive hedge fund analysis using multiple AI analysts',
            inputSchema: GenerateAnalysisToolSchema,
          },
          {
            name: 'get_health',
            description: 'Check the health status of the hedge fund AI server',
            inputSchema: GetHealthToolSchema,
          },
          {
            name: 'get_system_status',
            description: 'Get comprehensive system status and available endpoints',
            inputSchema: GetSystemStatusToolSchema,
          },
          {
            name: 'get_available_analysts',
            description: 'Get list of available AI analysts for analysis',
            inputSchema: GetAvailableAnalystsToolSchema,
          },
          {
            name: 'search_tickers',
            description: 'Search for stock ticker symbols',
            inputSchema: SearchTickersToolSchema,
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request: any) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case 'generate_analysis':
          return this.handleGenerateAnalysis(args as GenerateAnalysisTool);

        case 'get_health':
          return this.handleGetHealth(args as GetHealthTool);

        case 'get_system_status':
          return this.handleGetSystemStatus(args as GetSystemStatusTool);

        case 'get_portfolio_status':
          return this.handleGetPortfolioStatus(args as GetPortfolioStatusTool);

        case 'get_available_analysts':
          return this.handleGetAvailableAnalysts(args as GetAvailableAnalystsTool);

        case 'search_tickers':
          return this.handleSearchTickers(args as SearchTickersTool);

        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });
  }

  private async handleGenerateAnalysis(args: GenerateAnalysisTool) {
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
        model_provider: args.model_provider ?? "OpenAI"
      });

      const results: any[] = [];
      for await (const response of analysisGenerator) {
        results.push(response);
      }

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(results, null, 2)
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error generating analysis: ${error instanceof Error ? error.message : 'Unknown error'}`
          }
        ]
      };
    }
  }

  private async handleGetHealth(args: GetHealthTool) {
    try {
      const health = await this.client.getHealth();
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(health, null, 2)
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error getting health status: ${error instanceof Error ? error.message : 'Unknown error'}`
          }
        ]
      };
    }
  }

  private async handleGetSystemStatus(args: GetSystemStatusTool) {
    try {
      const status = await this.client.getSystemStatus();
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(status, null, 2)
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error getting system status: ${error instanceof Error ? error.message : 'Unknown error'}`
          }
        ]
      };
    }
  }

  private async handleGetPortfolioStatus(args: GetPortfolioStatusTool) {
    try {
      const status = await this.client.getPortfolioStatus();
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(status, null, 2)
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error getting portfolio status: ${error instanceof Error ? error.message : 'Unknown error'}`
          }
        ]
      };
    }
  }

  private async handleGetAvailableAnalysts(args: GetAvailableAnalystsTool) {
    try {
      const analysts = await this.client.getAvailableAnalysts();
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(analysts, null, 2)
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error getting available analysts: ${error instanceof Error ? error.message : 'Unknown error'}`
          }
        ]
      };
    }
  }

  private async handleSearchTickers(args: SearchTickersTool) {
    try {
      const tickers = await this.client.searchTickers(args.query);
      // Validate the response using the schema
      const { TickerSearchResultsSchema } = await import('./types.js');
      const validated = TickerSearchResultsSchema.parse(tickers);
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(validated, null, 2)
          }
        ]
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error searching tickers: ${error instanceof Error ? error.message : 'Unknown error'}`
          }
        ]
      };
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Hedge Fund AI MCP server started');
  }
}

// Start the server if this file is run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const tools = new HedgeFundAITools();
  tools.run().catch(console.error);
} 