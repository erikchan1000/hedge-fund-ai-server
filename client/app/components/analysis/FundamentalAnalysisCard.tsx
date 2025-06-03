import { FundamentalAnalysis } from "@/app/types/analysis";
import { AnalysisCard, SignalBadge } from "./AnalysisCard";

interface FundamentalAnalysisCardProps {
  ticker: string;
  analysis: FundamentalAnalysis;
}

export function FundamentalAnalysisCard({ ticker, analysis }: FundamentalAnalysisCardProps) {
  return (
    <AnalysisCard ticker={ticker} signal={analysis.signal} confidence={analysis.confidence}>
      <div className="space-y-2">
        {Object.entries(analysis.reasoning).map(([key, value]) => (
          <div key={key} className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium capitalize">{key.replace(/_/g, ' ')}:</span>
              <SignalBadge signal={value.signal} />
            </div>
            <p className="text-sm text-muted-foreground">{value.details}</p>
          </div>
        ))}
      </div>
    </AnalysisCard>
  );
} 