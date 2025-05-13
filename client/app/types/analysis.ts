export interface AnalysisRequest {
  tickers: string[];
  selected_analysts: string[];
  initial_cash: number;
  margin_requirement: number;
  show_reasoning: boolean;
  model_name: string;
  model_provider: string;
}

export interface Ticker {
  symbol: string;
}

export interface AnalysisFormProps {
  onSubmit: (data: AnalysisRequest) => void;
  isLoading: boolean;
}

export interface ReturnData {
  decisions: {
    [ticker: string]: {
      action: string;
      quantity: number;
      confidence: number;
      reasoning: string;
    }
  };
  analyst_signals: {
    [agent: string]: {
      [ticker: string]: {
        signal?: string;
        confidence?: number;
        reasoning?: string | {
          portfolio_value: number;
          current_position: number;
          position_limit: number;
          remaining_limit: number;
          available_cash: number;
        };
        remaining_position_limit?: number;
        current_price?: number;
      }
    }
  };
} 