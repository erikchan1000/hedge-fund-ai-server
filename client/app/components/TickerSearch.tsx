"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Check, ChevronsUpDown } from "lucide-react";
import { Ticker } from "../types/analysis";
import debounce from "lodash/debounce";
import { cn } from "@/lib/utils";

interface TickerSearchProps {
  selectedTickers: string[];
  onTickerSelect: (ticker: string) => void;
}

export function TickerSearch({
  selectedTickers,
  onTickerSelect,
}: TickerSearchProps) {
  const [open, setOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredTickers, setFilteredTickers] = useState<Ticker[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchTickers = async (term: string, isInitial: boolean = false) => {
    setIsLoading(true);
    try {
      const url = isInitial
        ? `/api/search-tickers?initial=true`
        : `/api/search-tickers?q=${encodeURIComponent(term)}`;

      const response = await fetch(url);
      if (!response.ok) throw new Error("Failed to fetch tickers");
      const data = await response.json();
      setFilteredTickers(data);
    } catch (error) {
      console.error("Error searching tickers:", error);
      setFilteredTickers([]);
    } finally {
      setIsLoading(false);
    }
  };

  const searchTickers = useCallback(
    debounce(async (term: string) => {
      if (!term) {
        // If search term is empty, show initial results
        await fetchTickers("", true);
        return;
      }
      await fetchTickers(term);
    }, 300),
    [],
  );

  useEffect(() => {
    if (open) {
      searchTickers(searchTerm);
    }
  }, [searchTerm, searchTickers, open]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between"
        >
          Search tickers...
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0" align="start">
        <Command shouldFilter={false} className="rounded-lg border shadow-md">
          <CommandInput
            placeholder="Search tickers..."
            value={searchTerm}
            onValueChange={(value) => {
              setSearchTerm(value);
            }}
            className="border-b"
          />
          <CommandEmpty className="py-6 text-center text-sm">
            {isLoading ? "Searching..." : "No ticker found."}
          </CommandEmpty>
          <CommandGroup className="max-h-[600px] overflow-y-auto">
            {filteredTickers.map((ticker) => (
              <CommandItem
                key={ticker.symbol}
                onSelect={() => {
                  onTickerSelect(ticker.symbol);
                  setOpen(false);
                }}
                className="cursor-pointer px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground"
              >
                <Check
                  className={cn(
                    "mr-2 h-4 w-4",
                    selectedTickers.includes(ticker.symbol)
                      ? "opacity-100"
                      : "opacity-0",
                  )}
                />
                {ticker.symbol}
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
