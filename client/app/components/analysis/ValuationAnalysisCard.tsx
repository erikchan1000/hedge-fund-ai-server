import { ValuationAnalysis } from "@/app/types/analysis";
import { AnalysisCard, SignalBadge } from "./AnalysisCard";

interface ValuationAnalysisCardProps {
  ticker: string;
  analysis: ValuationAnalysis;
}

export function ValuationAnalysisCard({ ticker, analysis }: ValuationAnalysisCardProps) {
  return (
    <AnalysisCard ticker={ticker} signal={analysis.signal} confidence={analysis.confidence}>
      <div className="space-y-2">
        {Object.entries(analysis.reasoning).map(([key, value]) => (
          value && (
            <div key={key} className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium capitalize">{key.replace(/_/g, ' ')}:</span>
                <SignalBadge signal={value.signal} />
              </div>
              <p className="text-sm text-muted-foreground">{value.details}</p>
            </div>
          )
        ))}
      </div>
    </AnalysisCard>
  );
} 