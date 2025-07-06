import axios, { AxiosInstance, AxiosRequestConfig } from "axios";
import {
  AnalysisRequest,
  AnalysisResponse,
  HealthCheck,
  SystemStatus,
  PortfolioStatus,
  AvailableAnalysts,
  AnalysisRequestSchema,
  HealthCheckSchema,
  SystemStatusSchema,
  PortfolioStatusSchema,
} from "./types.js";

// MCP-compliant cancellation token interface
interface CancellationToken {
  isCancelled: boolean;
  requestId?: string;
  cancel(): void;
  onCancellation(callback: () => void): void;
}

// MCP-compliant cancellation token implementation
class MCPCancellationToken implements CancellationToken {
  private _isCancelled = false;
  private _callbacks: (() => void)[] = [];
  
  constructor(public requestId?: string) {}

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

export class HedgeFundAIClient {
  private client: AxiosInstance;
  private baseURL: string;
  private activeCancellationTokens: Map<string, CancellationToken> = new Map();

  constructor(baseURL: string = "http://localhost:5000") {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 300000, // 5 minutes for long-running analysis
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    });
  }

  /**
   * Send MCP CancelledNotification according to specification
   */
  async sendCancelledNotification(requestId: string, reason?: string): Promise<void> {
    try {
      // According to MCP spec, we should send notifications/cancelled
      const notification = {
        jsonrpc: "2.0",
        method: "notifications/cancelled",
        params: {
          requestId,
          reason: reason || "Client requested cancellation"
        }
      };

      // Send notification to the server
      await this.client.post("/api/mcp/notification", notification);
      
      // Cancel the local token if it exists
      const token = this.activeCancellationTokens.get(requestId);
      if (token) {
        token.cancel();
        this.activeCancellationTokens.delete(requestId);
      }
    } catch (error) {
      console.error(`Failed to send cancellation notification for request ${requestId}:`, error);
      throw error;
    }
  }

  /**
   * Create a new cancellation token
   */
  createCancellationToken(requestId?: string): CancellationToken {
    const id = requestId || `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const token = new MCPCancellationToken(id);
    this.activeCancellationTokens.set(id, token);
    return token;
  }

  /**
   * Cancel a request by ID
   */
  async cancelRequest(requestId: string, reason?: string): Promise<void> {
    await this.sendCancelledNotification(requestId, reason);
  }

  /**
   * Generate hedge fund analysis with MCP-compliant cancellation support
   */
  async generateAnalysis(
    request: AnalysisRequest,
    cancellationToken?: CancellationToken
  ): Promise<AsyncGenerator<AnalysisResponse, void, unknown>> {
    // Validate request
    AnalysisRequestSchema.parse(request);

    // Create cancellation token if not provided
    const token = cancellationToken || this.createCancellationToken();

    // Create abort controller for HTTP cancellation
    const abortController = new AbortController();
    
    // Set up cancellation handling
    token.onCancellation(() => {
      abortController.abort();
      // Send MCP cancellation notification if we have a request ID
      if (token.requestId) {
        this.sendCancelledNotification(token.requestId, "Client cancelled request").catch(console.error);
      }
    });

    const config: AxiosRequestConfig = {
      responseType: "stream",
      headers: {
        Accept: "application/json",
        "Cache-Control": "no-cache",
        // Include request ID in headers if available
        ...(token.requestId && { 'X-Request-ID': token.requestId })
      },
      signal: abortController.signal,
    };

    try {
      const response = await this.client.post("/api/analysis/generate", request, config);
      return this.parseStreamResponse(response.data, token);
    } catch (error) {
      if (abortController.signal.aborted) {
        throw new Error("Request was cancelled");
      }
      throw error;
    }
  }

  /**
   * Get system health status
   */
  async getHealth(): Promise<HealthCheck> {
    const response = await this.client.get("/api/health");
    return HealthCheckSchema.parse(response.data);
  }

  /**
   * Get comprehensive system status
   */
  async getSystemStatus(): Promise<SystemStatus> {
    const response = await this.client.get("/api/status");
    return SystemStatusSchema.parse(response.data);
  }

  /**
   * Get available analysts
   */
  async getAvailableAnalysts(): Promise<AvailableAnalysts> {
    // This would need to be implemented on the server side
    // For now, return a hardcoded list based on the server's analyst configuration
    return {
      ben_graham: { display_name: "Ben Graham", order: 0 },
      bill_ackman: { display_name: "Bill Ackman", order: 1 },
      cathie_wood: { display_name: "Cathie Wood", order: 2 },
      charlie_munger: { display_name: "Charlie Munger", order: 3 },
      michael_burry: { display_name: "Michael Burry", order: 4 },
      peter_lynch: { display_name: "Peter Lynch", order: 5 },
      phil_fisher: { display_name: "Phil Fisher", order: 6 },
      stanley_druckenmiller: {
        display_name: "Stanley Druckenmiller",
        order: 7,
      },
      warren_buffett: { display_name: "Warren Buffett", order: 8 },
      technical_analyst: { display_name: "Technical Analyst", order: 9 },
      fundamentals_analyst: { display_name: "Fundamentals Analyst", order: 10 },
      sentiment_analyst: { display_name: "Sentiment Analyst", order: 11 },
      valuation_analyst: { display_name: "Valuation Analyst", order: 12 },
    };
  }

  /**
   * Search for ticker symbols
   */
  async searchTickers(query: string): Promise<any[]> {
    const response = await this.client.get("/api/search_tickers", {
      params: { query },
    });
    return response.data.results;
  }

  /**
   * Parse streaming response with MCP-compliant cancellation support
   */
  private async *parseStreamResponse(
    stream: any,
    cancellationToken?: CancellationToken
  ): AsyncGenerator<AnalysisResponse, void, unknown> {
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      for await (const chunk of stream) {
        // Check for cancellation according to MCP spec
        if (cancellationToken?.isCancelled) {
          throw new Error("Request was cancelled");
        }

        buffer += decoder.decode(chunk, { stream: true });

        // Split by newlines to get individual JSON objects
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.trim()) {
            // Check for cancellation before processing each line
            if (cancellationToken?.isCancelled) {
              throw new Error("Request was cancelled");
            }

            try {
              // Handle Server-Sent Events format
              let jsonData = line;
              if (line.startsWith("data: ")) {
                jsonData = line.substring(6);
              }
              
              if (jsonData.trim()) {
                const data = JSON.parse(jsonData);
                
                // Check if this is a cancellation event from the server
                if (data.type === "cancelled") {
                  if (cancellationToken?.requestId) {
                    cancellationToken.cancel();
                  }
                  throw new Error("Request was cancelled by server");
                }
                
                yield data as AnalysisResponse;
              }
            } catch (error) {
              if (error instanceof Error && error.message.includes("cancelled")) {
                throw error;
              }
              console.warn("Failed to parse JSON from stream:", line, error);
            }
          }
        }
      }

      // Process any remaining data in buffer
      if (buffer.trim() && !cancellationToken?.isCancelled) {
        try {
          let jsonData = buffer;
          if (buffer.startsWith("data: ")) {
            jsonData = buffer.substring(6);
          }
          
          if (jsonData.trim()) {
            const data = JSON.parse(jsonData);
            
            // Check if this is a cancellation event from the server
            if (data.type === "cancelled") {
              if (cancellationToken?.requestId) {
                cancellationToken.cancel();
              }
              throw new Error("Request was cancelled by server");
            }
            
            yield data as AnalysisResponse;
          }
        } catch (error) {
          if (error instanceof Error && error.message.includes("cancelled")) {
            throw error;
          }
          console.warn("Failed to parse final JSON from stream:", buffer, error);
        }
      }
    } catch (error) {
      if (cancellationToken?.isCancelled) {
        throw new Error("Request was cancelled");
      }
      throw error;
    } finally {
      // Clean up the cancellation token
      if (cancellationToken?.requestId) {
        this.activeCancellationTokens.delete(cancellationToken.requestId);
      }
    }
  }
}
