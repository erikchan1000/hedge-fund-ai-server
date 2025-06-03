import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { PersonalityAgent, SignalType } from "../../types/analysis";
import { cn } from "@/lib/utils";

interface PersonalityCardProps {
  ticker: string;
  analysis: PersonalityAgent[string];
}

export function PersonalityCard({ ticker, analysis }: PersonalityCardProps) {
  const signalStyles = {
    bullish: "bg-green-100 text-green-800 border-green-200",
    bearish: "bg-red-100 text-red-800 border-red-200",
    neutral: "bg-gray-100 text-gray-800 border-gray-200",
    hold: "bg-yellow-100 text-yellow-800 border-yellow-200"
  };

  const confidenceColor = analysis.confidence > 75 
    ? "text-green-600" 
    : analysis.confidence > 50 
    ? "text-yellow-600" 
    : "text-red-600";

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">{ticker}</CardTitle>
          <Badge 
            variant="outline" 
            className={cn(signalStyles[analysis.signal as keyof typeof signalStyles])}
          >
            {analysis.signal.toUpperCase()}
          </Badge>
        </div>
        <CardDescription>Personality-based investment analysis</CardDescription>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {/* Confidence Section */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">Confidence Level</span>
              <span className={cn("text-sm font-semibold", confidenceColor)}>
                {analysis.confidence}%
              </span>
            </div>
            <Progress 
              value={analysis.confidence} 
              className="h-2"
            />
          </div>

          {/* Signal Indicator */}
          <div className="flex items-center justify-between py-2 px-3 bg-muted rounded-lg">
            <span className="text-sm font-medium">Investment Signal</span>
            <div className="flex items-center space-x-2">
              <div 
                className={cn(
                  "w-3 h-3 rounded-full",
                  analysis.signal === SignalType.BULLISH && "bg-green-500",
                  analysis.signal === SignalType.BEARISH && "bg-red-500",
                  analysis.signal === SignalType.NEUTRAL && "bg-gray-500",
                  analysis.signal === SignalType.HOLD && "bg-yellow-500"
                )}
              />
              <span className="text-sm font-medium capitalize">
                {analysis.signal}
              </span>
            </div>
          </div>

          {/* Reasoning Section */}
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-muted-foreground">Analysis Reasoning</h4>
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm leading-relaxed">
                {analysis.reasoning}
              </p>
            </div>
          </div>

          {/* Personality Traits Indicator */}
          <div className="flex items-center justify-between pt-2 border-t">
            <span className="text-xs text-muted-foreground">Personality-driven Analysis</span>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 rounded-full bg-blue-500"></div>
              <div className="w-2 h-2 rounded-full bg-purple-500"></div>
              <div className="w-2 h-2 rounded-full bg-pink-500"></div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 