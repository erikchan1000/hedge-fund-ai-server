import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { RiskAnalysis } from "@/app/types/analysis";
import { AnalysisCard } from "./AnalysisCard";

interface RiskAnalysisCardProps {
  ticker: string;
  analysis: RiskAnalysis;
}

const formatCurrency = (value: number) => {
  return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

export function RiskAnalysisCard({ ticker, analysis }: RiskAnalysisCardProps) {
  return (
    <AnalysisCard ticker={ticker}>
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <Label className="text-sm text-muted-foreground">Current Price</Label>
            <p className="font-medium">{formatCurrency(analysis.current_price)}</p>
          </div>
          <div className="space-y-1">
            <Label className="text-sm text-muted-foreground">Position Limit</Label>
            <p className="font-medium">{formatCurrency(analysis.reasoning.position_limit)}</p>
          </div>
        </div>

        <div className="space-y-1">
          <Label className="text-sm text-muted-foreground">Remaining Position Limit</Label>
          <p className="font-medium">{formatCurrency(analysis.remaining_position_limit)}</p>
        </div>

        <div className="space-y-3">
          <h4 className="text-sm font-medium">Portfolio Metrics</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <Label className="text-sm text-muted-foreground">Portfolio Value</Label>
              <p className="font-medium">{formatCurrency(analysis.reasoning.portfolio_value)}</p>
            </div>
            <div className="space-y-1">
              <Label className="text-sm text-muted-foreground">Current Position</Label>
              <p className="font-medium">{formatCurrency(analysis.reasoning.current_position)}</p>
            </div>
            <div className="space-y-1">
              <Label className="text-sm text-muted-foreground">Available Cash</Label>
              <p className="font-medium">{formatCurrency(analysis.reasoning.available_cash)}</p>
            </div>
            <div className="space-y-1">
              <Label className="text-sm text-muted-foreground">Remaining Limit</Label>
              <p className="font-medium">{formatCurrency(analysis.reasoning.remaining_limit)}</p>
            </div>
          </div>
        </div>
      </div>
    </AnalysisCard>
  );
} 