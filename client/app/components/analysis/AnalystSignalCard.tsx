import { AnalystSignal } from "@/app/types/analysis";
import { AnalysisCard } from "./AnalysisCard";

interface AnalystSignalCardProps {
  ticker: string;
  signal: AnalystSignal;
}

export function AnalystSignalCard({ ticker, signal }: AnalystSignalCardProps) {
  return (
    <AnalysisCard ticker={ticker} signal={signal.signal} confidence={signal.confidence}>
      {signal.remaining_position_limit && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Position Limit</span>
            <span className="font-medium">${signal.remaining_position_limit?.toLocaleString()}</span>
          </div>
          {signal.current_price && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Current Price</span>
              <span className="font-medium">${signal.current_price?.toLocaleString()}</span>
            </div>
          )}
        </div>
      )}
      {typeof signal.reasoning === 'string' ? (
        <p className="text-sm text-muted-foreground">{signal.reasoning}</p>
      ) : signal.reasoning && (
        <div className="space-y-2">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-muted-foreground">Portfolio Value:</span>
              <span className="ml-2 font-medium">${signal.reasoning.portfolio_value?.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Current Position:</span>
              <span className="ml-2 font-medium">${signal.reasoning.current_position?.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Position Limit:</span>
              <span className="ml-2 font-medium">${signal.reasoning.position_limit?.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Available Cash:</span>
              <span className="ml-2 font-medium">${signal.reasoning.available_cash?.toLocaleString()}</span>
            </div>
          </div>
        </div>
      )}
    </AnalysisCard>
  );
} 