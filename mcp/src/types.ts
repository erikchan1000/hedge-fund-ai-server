import { z } from "zod";

// Portfolio schema
export const PortfolioSchema = z.object({
  cash: z.number(),
  positions: z.record(
    z.object({
      ticker: z.string(),
      shares: z.number(),
      avg_price: z.number(),
      current_price: z.number().optional(),
      market_value: z.number().optional(),
    }),
  ),
});

// Analysis request schema
export const AnalysisRequestSchema = z.object({
  tickers: z.array(z.string()),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
  initial_cash: z.number().default(100000.0),
  margin_requirement: z.number().default(0.0),
  portfolio: PortfolioSchema.optional(),
  show_reasoning: z.boolean().default(false),
  selected_analysts: z.array(z.string()).optional(),
  model_name: z.string().default("gpt-4o"),
  model_provider: z.string().default("OpenAI"),
});

// Analysis response schemas
export const ProgressUpdateSchema = z.object({
  type: z.literal("progress"),
  stage: z.enum([
    "initialization",
    "analysis",
    "risk_management",
    "portfolio_management",
  ]),
  message: z.string(),
  progress: z.number(),
  current_analyst: z.string().optional(),
  analyst_progress: z.string().optional(),
  analysts: z.array(z.string()).optional(),
  tickers: z.array(z.string()).optional(),
});

export const AnalysisResultSchema = z.object({
  type: z.literal("result"),
  data: z.object({
    decisions: z.any(),
    analyst_signals: z.record(z.any()),
  }),
});

export const ErrorResponseSchema = z.object({
  type: z.literal("error"),
  message: z.string(),
  stage: z.string(),
});

export const AnalysisResponseSchema = z.union([
  ProgressUpdateSchema,
  AnalysisResultSchema,
  ErrorResponseSchema,
]);

// Health check schemas
export const HealthCheckSchema = z.object({
  status: z.string(),
  timestamp: z.string(),
  service: z.string(),
  version: z.string().optional(),
  components: z.record(z.string()).optional(),
});

export const SystemStatusSchema = z.object({
  status: z.string(),
  timestamp: z.string(),
  api_version: z.string(),
  endpoints: z.record(z.string()),
  architecture: z.string(),
  documentation: z.string(),
});

// Portfolio status schema
export const PortfolioStatusSchema = z.object({
  message: z.string(),
  endpoints: z.array(z.string()),
});

// Analyst configuration
export const AnalystConfigSchema = z.object({
  display_name: z.string(),
  order: z.number(),
});

export const AvailableAnalystsSchema = z.record(AnalystConfigSchema);

// Type exports
export type Portfolio = z.infer<typeof PortfolioSchema>;
export type AnalysisRequest = z.infer<typeof AnalysisRequestSchema>;
export type ProgressUpdate = z.infer<typeof ProgressUpdateSchema>;
export type AnalysisResult = z.infer<typeof AnalysisResultSchema>;
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;
export type AnalysisResponse = z.infer<typeof AnalysisResponseSchema>;
export type HealthCheck = z.infer<typeof HealthCheckSchema>;
export type SystemStatus = z.infer<typeof SystemStatusSchema>;
export type PortfolioStatus = z.infer<typeof PortfolioStatusSchema>;
export type AnalystConfig = z.infer<typeof AnalystConfigSchema>;
export type AvailableAnalysts = z.infer<typeof AvailableAnalystsSchema>;

// MCP Tool schemas
export const GenerateAnalysisToolSchema = z.object({
  tickers: z.array(z.string()).describe("List of stock tickers to analyze"),
  start_date: z
    .string()
    .optional()
    .describe("Start date for analysis (YYYY-MM-DD)"),
  end_date: z
    .string()
    .optional()
    .describe("End date for analysis (YYYY-MM-DD)"),
  initial_cash: z
    .number()
    .optional()
    .describe("Initial cash amount for portfolio"),
  margin_requirement: z
    .number()
    .optional()
    .describe("Margin requirement percentage"),
  show_reasoning: z
    .boolean()
    .optional()
    .describe("Whether to show detailed reasoning"),
  selected_analysts: z
    .array(z.string())
    .optional()
    .describe("List of analyst names to use"),
  model_name: z.string().optional().describe("LLM model name to use"),
  model_provider: z.string().optional().describe("LLM provider (OpenAI, etc.)"),
});

export const GetHealthToolSchema = z.object({});
export const GetSystemStatusToolSchema = z.object({});
export const GetPortfolioStatusToolSchema = z.object({});
export const SearchTickersToolSchema = z.object({
  query: z.string().describe("Search query for ticker symbols"),
});

export type GenerateAnalysisTool = z.infer<typeof GenerateAnalysisToolSchema>;
export type GetHealthTool = z.infer<typeof GetHealthToolSchema>;
export type GetSystemStatusTool = z.infer<typeof GetSystemStatusToolSchema>;
export type GetPortfolioStatusTool = z.infer<
  typeof GetPortfolioStatusToolSchema
>;
export type SearchTickersTool = z.infer<typeof SearchTickersToolSchema>;

export const TickerSearchResultSchema = z.object({
  symbol: z.string(),
  name: z.string().nullable(),
  market: z.string().nullable(),
  locale: z.string().nullable(),
  primary_exchange: z.string().nullable(),
  currency_name: z.string().nullable(),
  active: z.boolean().nullable(),
  type: z.string().nullable(),
});

export const TickerSearchResultsSchema = z.array(TickerSearchResultSchema);

export type TickerSearchResult = z.infer<typeof TickerSearchResultSchema>;
export type TickerSearchResults = z.infer<typeof TickerSearchResultsSchema>;
