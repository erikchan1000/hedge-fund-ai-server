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

export enum SignalType {
  BULLISH = 'bullish',
  BEARISH = 'bearish',
  NEUTRAL = 'neutral',
  HOLD = 'hold'
}

export enum AgentType {
  FUNDAMENTALS = 'fundamentals_agent',
  SENTIMENT = 'sentiment_agent',
  TECHNICAL = 'technical_analyst_agent',
  VALUATION = 'valuation_agent',
  RISK = 'risk_management_agent'
}

export interface FundamentalAnalysis {
  signal: SignalType;
  confidence: number;
  reasoning: {
    profitability_signal: {
      signal: SignalType;
      details: string;
    };
    growth_signal: {
      signal: SignalType;
      details: string;
    };
    financial_health_signal: {
      signal: SignalType;
      details: string;
    };
    price_ratios_signal: {
      signal: SignalType;
      details: string;
    };
  };
}

export interface ValuationMethod {
  value: number;
  weight: number;
  gap?: number;
}

export interface ValuationAnalysis {
  signal: SignalType;
  confidence: number;
  reasoning: {
    dcf_analysis?: {
      signal: SignalType;
      details: string;
    };
    owner_earnings_analysis?: {
      signal: SignalType;
      details: string;
    };
    ev_ebitda_analysis?: {
      signal: SignalType;
      details: string;
    };
    residual_income_analysis?: {
      signal: SignalType;
      details: string;
    };
  };
}

export interface TechnicalMetrics {
  [key: string]: number;
}

export interface TechnicalStrategy {
  signal: SignalType;
  confidence: number;
  metrics: TechnicalMetrics;
}

export interface TechnicalAnalysis {
  signal: SignalType;
  confidence: number;
  strategy_signals: {
    trend_following: TechnicalStrategy;
    mean_reversion: TechnicalStrategy;
    momentum: TechnicalStrategy;
    volatility: TechnicalStrategy;
    statistical_arbitrage: TechnicalStrategy;
  };
}

export interface PortfolioMetrics {
  portfolio_value: number;
  current_position: number;
  position_limit: number;
  remaining_limit: number;
  available_cash: number;
}

export interface AnalystSignal {
  signal?: SignalType;
  confidence?: number;
  reasoning?: string | PortfolioMetrics;
  remaining_position_limit?: number;
  current_price?: number;
}

export interface RiskAnalysis {
  remaining_position_limit: number;
  current_price: number;
  reasoning: {
    portfolio_value: number;
    current_position: number;
    position_limit: number;
    remaining_limit: number;
    available_cash: number;
  };
}

export type AgentAnalysisMap = {
  [AgentType.FUNDAMENTALS]: FundamentalAnalysis;
  [AgentType.VALUATION]: ValuationAnalysis;
  [AgentType.TECHNICAL]: TechnicalAnalysis;
  [AgentType.SENTIMENT]: AnalystSignal;
  [AgentType.RISK]: RiskAnalysis;
};

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
    [K in AgentType]: {
      [ticker: string]: AgentAnalysisMap[K];
    };
  };
}