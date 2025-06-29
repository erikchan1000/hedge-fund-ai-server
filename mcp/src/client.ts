import axios, { AxiosInstance } from 'axios';
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
  PortfolioStatusSchema
} from './types.js';

export class HedgeFundAIClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:5000') {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 300000, // 5 minutes for long-running analysis
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });
  }

  /**
   * Generate hedge fund analysis
   */
  async generateAnalysis(request: AnalysisRequest): Promise<AsyncGenerator<AnalysisResponse, void, unknown>> {
    // Validate request
    AnalysisRequestSchema.parse(request);

    const response = await this.client.post('/api/analysis/generate', request, {
      responseType: 'stream',
      headers: {
        'Accept': 'application/json',
        'Cache-Control': 'no-cache'
      }
    });

    return this.parseStreamResponse(response.data);
  }

  /**
   * Get system health status
   */
  async getHealth(): Promise<HealthCheck> {
    const response = await this.client.get('/api/health');
    return HealthCheckSchema.parse(response.data);
  }

  /**
   * Get comprehensive system status
   */
  async getSystemStatus(): Promise<SystemStatus> {
    const response = await this.client.get('/api/status');
    return SystemStatusSchema.parse(response.data);
  }

  /**
   * Get portfolio service status
   */
  async getPortfolioStatus(): Promise<PortfolioStatus> {
    const response = await this.client.get('/api/portfolio/status');
    return PortfolioStatusSchema.parse(response.data);
  }

  /**
   * Get available analysts
   */
  async getAvailableAnalysts(): Promise<AvailableAnalysts> {
    // This would need to be implemented on the server side
    // For now, return a hardcoded list based on the server's analyst configuration
    return {
      "ben_graham": { display_name: "Ben Graham", order: 0 },
      "bill_ackman": { display_name: "Bill Ackman", order: 1 },
      "cathie_wood": { display_name: "Cathie Wood", order: 2 },
      "charlie_munger": { display_name: "Charlie Munger", order: 3 },
      "michael_burry": { display_name: "Michael Burry", order: 4 },
      "peter_lynch": { display_name: "Peter Lynch", order: 5 },
      "phil_fisher": { display_name: "Phil Fisher", order: 6 },
      "stanley_druckenmiller": { display_name: "Stanley Druckenmiller", order: 7 },
      "warren_buffett": { display_name: "Warren Buffett", order: 8 },
      "technical_analyst": { display_name: "Technical Analyst", order: 9 },
      "fundamentals_analyst": { display_name: "Fundamentals Analyst", order: 10 },
      "sentiment_analyst": { display_name: "Sentiment Analyst", order: 11 },
      "valuation_analyst": { display_name: "Valuation Analyst", order: 12 }
    };
  }

  /**
   * Search for ticker symbols
   */
  async searchTickers(query: string): Promise<any[]> {
    const response = await this.client.get('/api/search_tickers', { params: { query } });
    return response.data.results;
  }

  /**
   * Parse streaming response from the analysis endpoint
   */
  private async *parseStreamResponse(stream: any): AsyncGenerator<AnalysisResponse, void, unknown> {
    const decoder = new TextDecoder();
    let buffer = '';

    for await (const chunk of stream) {
      buffer += decoder.decode(chunk, { stream: true });
      
      // Split by newlines to get individual JSON objects
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.trim()) {
          try {
            const data = JSON.parse(line);
            yield data as AnalysisResponse;
          } catch (error) {
            console.warn('Failed to parse JSON from stream:', line, error);
          }
        }
      }
    }

    // Process any remaining data in buffer
    if (buffer.trim()) {
      try {
        const data = JSON.parse(buffer);
        yield data as AnalysisResponse;
      } catch (error) {
        console.warn('Failed to parse final JSON from stream:', buffer, error);
      }
    }
  }
} 