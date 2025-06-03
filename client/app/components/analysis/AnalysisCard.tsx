import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { SignalType } from "@/app/types/analysis";
import { cn } from "@/lib/utils";

interface AnalysisCardProps {
  ticker: string;
  signal?: SignalType;
  confidence?: number;
  children?: React.ReactNode;
}

type BadgeVariant = "default" | "destructive" | "secondary";

export function SignalBadge({ signal }: { signal: string }) {
  const signalStyles: Record<SignalType, string> = {
    bullish: "bg-green-500 hover:bg-green-600 text-white",
    bearish: "bg-red-500 hover:bg-red-600 text-white",
    neutral: "bg-yellow-500 hover:bg-yellow-600 text-white"
  };

  return (
    <Badge className={cn(signalStyles[signal as keyof typeof signalStyles])}>
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
          {signal && signal !== 'hold' && (
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