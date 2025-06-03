import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ReturnData, AgentType } from "../types/analysis";
import { FundamentalAnalysisCard } from "./analysis/FundamentalAnalysisCard";
import { TechnicalAnalysisCard } from "./analysis/TechnicalAnalysisCard";
import { ValuationAnalysisCard } from "./analysis/ValuationAnalysisCard";
import { AnalystSignalCard } from "./analysis/AnalystSignalCard";
import { RiskAnalysisCard } from "./analysis/RiskAnalysisCard";
import { PersonalityCard } from "./analysis/PersonalityCard";
import { cn } from "@/lib/utils";

interface AnalysisResultsProps {
  data: ReturnData;
}

export function AnalysisResults({ data }: AnalysisResultsProps) {
  const actionStyles = {
    buy: "bg-green-500 hover:bg-green-600 text-white",
    sell: "bg-yellow-500 hover:bg-yellow-600 text-white",
    short: "bg-red-500 hover:bg-red-600 text-white",
    cover: "bg-yellow-500 hover:bg-yellow-600 text-white",
    hold: "bg-yellow-500 hover:bg-yellow-600 text-white"
  };

  return (
    <div className="space-y-6">
      {/* Decisions Section */}
      <Card>
        <CardHeader>
          <CardTitle>Investment Decisions</CardTitle>
          <CardDescription>Final trading decisions based on analysis</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(data.decisions).map(([ticker, decision]) => (
              <Card key={ticker}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{ticker}</CardTitle>
                    <Badge className={cn(actionStyles[decision.action as keyof typeof actionStyles])}>
                      {decision.action.toUpperCase()}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Quantity</span>
                      <span className="font-medium">{decision.quantity} shares</span>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Confidence</span>
                        <span className="font-medium">{decision.confidence}%</span>
                      </div>
                      <Progress value={decision.confidence} className="h-2" />
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">{decision.reasoning}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Analyst Signals Section */}
      <Card>
        <CardHeader>
          <CardTitle>Analyst Signals</CardTitle>
          <CardDescription>Detailed analysis from each agent</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {Object.entries(data.analyst_signals).map(([agent, signals]) => (
              <div key={agent} className="space-y-4">
                <h3 className="text-lg font-semibold capitalize">{agent.replace(/_/g, ' ')}</h3>
                {Object.entries(signals).map(([ticker, signal]) => {
                  switch (agent) {
                    case AgentType.FUNDAMENTALS:
                      return <FundamentalAnalysisCard key={ticker} ticker={ticker} analysis={signal} />;
                    case AgentType.TECHNICAL:
                      return <TechnicalAnalysisCard key={ticker} ticker={ticker} analysis={signal} />;
                    case AgentType.VALUATION:
                      return <ValuationAnalysisCard key={ticker} ticker={ticker} analysis={signal} />;
                    case AgentType.SENTIMENT:
                      return <AnalystSignalCard key={ticker} ticker={ticker} signal={signal} />;
                    case AgentType.RISK:
                      return <RiskAnalysisCard key={ticker} ticker={ticker} analysis={signal} />;
                    default:
                      return <PersonalityCard key={ticker} ticker={ticker} analysis={signal} />;
                  }
                })}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 