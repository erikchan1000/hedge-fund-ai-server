import { TechnicalAnalysis } from "@/app/types/analysis";
import { AnalysisCard, SignalBadge } from "./AnalysisCard";
import { Progress } from "@/components/ui/progress";

interface TechnicalAnalysisCardProps {
  ticker: string;
  analysis: TechnicalAnalysis;
}

export function TechnicalAnalysisCard({ ticker, analysis }: TechnicalAnalysisCardProps) {
  return (
    <AnalysisCard ticker={ticker} signal={analysis.signal} confidence={analysis.confidence}>
      <div className="space-y-4">
        {Object.entries(analysis.strategy_signals).map(([strategy, data]) => (
          <div key={strategy} className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium capitalize">{strategy.replace(/_/g, ' ')}:</span>
              <SignalBadge signal={data.signal} />
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Confidence</span>
                <span className="font-medium">{data.confidence}%</span>
              </div>
              <Progress value={data.confidence} className="h-2" />
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {Object.entries(data.metrics).map(([metric, value]) => (
                <div key={metric}>
                  <span className="text-muted-foreground capitalize">{metric.replace(/_/g, ' ')}:</span>
                  <span className="ml-2 font-medium">{value?.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </AnalysisCard>
  );
} 