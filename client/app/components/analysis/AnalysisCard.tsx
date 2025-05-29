import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { SignalType } from "@/app/types/analysis";

interface AnalysisCardProps {
  ticker: string;
  signal?: SignalType;
  confidence?: number;
  children?: React.ReactNode;
}

export function SignalBadge({ signal }: { signal: string }) {
  return (
    <Badge variant={signal === "bullish" ? "default" : "destructive"}>
      {signal.toUpperCase()}
    </Badge>
  );
}

export function AnalysisCard({ ticker, signal, confidence, children }: AnalysisCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">{ticker}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {signal && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Signal:</span>
              <SignalBadge signal={signal} />
            </div>
          )}
          {confidence && (
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Confidence</span>
                <span className="font-medium">{confidence}%</span>
              </div>
              <Progress value={confidence} className="h-2" />
            </div>
          )}
          {children}
        </div>
      </CardContent>
    </Card>
  );
} 