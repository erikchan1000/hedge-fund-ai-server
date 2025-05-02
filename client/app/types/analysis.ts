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