import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ReturnData } from "../types/analysis";

interface AnalysisResultsProps {
  data: ReturnData;
}

export function AnalysisResults({ data }: AnalysisResultsProps) {
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
                    <Badge variant={decision.action === "buy" ? "default" : "destructive"}>
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
                {Object.entries(signals).map(([ticker, signal]) => (
                  <Card key={`${agent}-${ticker}`}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">{ticker}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {signal.signal && (
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-muted-foreground">Signal:</span>
                            <Badge variant={signal.signal === "bullish" ? "default" : "destructive"}>
                              {signal.signal.toUpperCase()}
                            </Badge>
                          </div>
                        )}
                        {signal.confidence && (
                          <div className="space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-muted-foreground">Confidence</span>
                              <span className="font-medium">{signal.confidence}%</span>
                            </div>
                            <Progress value={signal.confidence} className="h-2" />
                          </div>
                        )}
                        {signal.remaining_position_limit && (
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-muted-foreground">Position Limit</span>
                              <span className="font-medium">${signal.remaining_position_limit.toLocaleString()}</span>
                            </div>
                            {signal.current_price && (
                              <div className="flex items-center justify-between">
                                <span className="text-sm text-muted-foreground">Current Price</span>
                                <span className="font-medium">${signal.current_price.toLocaleString()}</span>
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
                                <span className="ml-2 font-medium">${signal.reasoning.portfolio_value.toLocaleString()}</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Current Position:</span>
                                <span className="ml-2 font-medium">${signal.reasoning.current_position.toLocaleString()}</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Position Limit:</span>
                                <span className="ml-2 font-medium">${signal.reasoning.position_limit.toLocaleString()}</span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Available Cash:</span>
                                <span className="ml-2 font-medium">${signal.reasoning.available_cash.toLocaleString()}</span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 