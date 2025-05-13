"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { TickerSearch } from "./TickerSearch";
import { AnalysisRequest, AnalysisFormProps } from "../types/analysis";

const formSchema = z.object({
  tickers: z.array(z.string()).min(1, "At least one ticker is required"),
  selected_analysts: z
    .array(z.string())
    .min(1, "At least one analyst is required"),
  initial_cash: z.number().min(0, "Initial cash must be positive"),
  margin_requirement: z.number().min(0, "Margin requirement must be positive"),
  show_reasoning: z.boolean(),
  model_name: z.string(),
  model_provider: z.string(),
});

const ANALYSTS = [
  { id: "warren_buffett", name: "Warren Buffett" },
  { id: "peter_lynch", name: "Peter Lynch" },
  { id: "charlie_munger", name: "Charlie Munger" },
  { id: "phil_fisher", name: "Phil Fisher" },
  { id: "michael_burry", name: "Michael Burry" },
  { id: "stanley_druckenmiller", name: "Stanley Druckenmiller" },
  { id: "bill_ackman", name: "Bill Ackman" },
  { id: "cathie_wood", name: "Cathie Wood" },
  { id: "ben_graham", name: "Ben Graham" },
  { id: "fundamentals_analyst", name: "Fundamentals Analyst" },
  { id: "technical_analyst", name: "Technical Analyst" },
  { id: "sentiment_analyst", name: "Sentiment Analyst" },
  { id: "valuation_analyst", name: "Valuation Analyst" }
];

export function AnalysisForm({ onSubmit, isLoading }: AnalysisFormProps) {
  const [selectedTickers, setSelectedTickers] = useState<string[]>([]);
  const [selectedAnalysts, setSelectedAnalysts] = useState<string[]>([]);

  const form = useForm<AnalysisRequest>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      tickers: [],
      selected_analysts: [],
      initial_cash: 100000,
      margin_requirement: 0,
      show_reasoning: true,
      model_name: "gpt-4o-mini",
      model_provider: "OpenAI",
    },
  });

  const handleTickerSelect = (ticker: string) => {
    if (!selectedTickers.includes(ticker)) {
      const newTickers = [...selectedTickers, ticker];
      setSelectedTickers(newTickers);
      form.setValue("tickers", newTickers);
    }
  };

  const handleAnalystToggle = (analystId: string) => {
    const newAnalysts = selectedAnalysts.includes(analystId)
      ? selectedAnalysts.filter((id) => id !== analystId)
      : [...selectedAnalysts, analystId];
    setSelectedAnalysts(newAnalysts);
    form.setValue("selected_analysts", newAnalysts);
  };

  const handleSubmit = (data: AnalysisRequest) => {
    onSubmit(data);
  };

  return (
    <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
      <div className="space-y-4">
        <div>
          <Label className="mb-2">Tickers</Label>
          <TickerSearch
            selectedTickers={selectedTickers}
            onTickerSelect={handleTickerSelect}
          />
          <div className="mt-2 flex flex-wrap gap-2">
            {selectedTickers.map((ticker) => (
              <span
                key={ticker}
                className="inline-flex items-center rounded-md bg-gray-100 px-2 py-1 text-sm"
              >
                {ticker}
                <button
                  type="button"
                  onClick={() => {
                    const newTickers = selectedTickers.filter(
                      (t) => t !== ticker,
                    );
                    setSelectedTickers(newTickers);
                    form.setValue("tickers", newTickers);
                  }}
                  className="ml-1 text-gray-500 hover:text-gray-700"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        <div>
          <Label className="mb-2">Analysts</Label>
          <div className="space-y-2">
            {ANALYSTS.map((analyst) => (
              <div key={analyst.id} className="flex items-center space-x-2">
                <Checkbox
                  id={analyst.id}
                  checked={selectedAnalysts.includes(analyst.id)}
                  onCheckedChange={() => handleAnalystToggle(analyst.id)}
                />
                <Label htmlFor={analyst.id}>{analyst.name}</Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <Label htmlFor="initial_cash" className="mb-2">
            Initial Cash
          </Label>
          <Input
            id="initial_cash"
            type="number"
            {...form.register("initial_cash", { valueAsNumber: true })}
          />
        </div>

        <div>
          <Label htmlFor="margin_requirement" className="mb-2">
            Margin Requirement
          </Label>
          <Input
            id="margin_requirement"
            type="number"
            {...form.register("margin_requirement", { valueAsNumber: true })}
          />
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox id="show_reasoning" {...form.register("show_reasoning")} />
          <Label htmlFor="show_reasoning">Show Reasoning</Label>
        </div>
      </div>

      <Button type="submit" disabled={isLoading}>
        {isLoading ? "Generating Analysis..." : "Generate Analysis"}
      </Button>
    </form>
  );
}
