# Complete List of Available FinnHub Metrics

Based on the actual API response from FinnHub's `/stock/metric` endpoint, here are all the available metrics:

## Trading & Price Metrics
- `10DayAverageTradingVolume`: 10-day average trading volume
- `3MonthAverageTradingVolume`: 3-month average trading volume
- `52WeekHigh`: 52-week high price
- `52WeekHighDate`: Date of 52-week high
- `52WeekLow`: 52-week low price
- `52WeekLowDate`: Date of 52-week low
- `beta`: Stock beta coefficient

## Price Return Metrics
- `5DayPriceReturnDaily`: 5-day price return
- `13WeekPriceReturnDaily`: 13-week price return
- `26WeekPriceReturnDaily`: 26-week price return
- `52WeekPriceReturnDaily`: 52-week price return
- `monthToDatePriceReturnDaily`: Month-to-date price return
- `yearToDatePriceReturnDaily`: Year-to-date price return
- `3MonthADReturnStd`: 3-month adjusted return standard deviation

## Relative Performance
- `priceRelativeToS&P5004Week`: 4-week price relative to S&P 500
- `priceRelativeToS&P50013Week`: 13-week price relative to S&P 500
- `priceRelativeToS&P50026Week`: 26-week price relative to S&P 500
- `priceRelativeToS&P50052Week`: 52-week price relative to S&P 500
- `priceRelativeToS&P500Ytd`: Year-to-date price relative to S&P 500

## Valuation Ratios
- `pb`: Price to book ratio (current)
- `pbAnnual`: Price to book ratio (annual)
- `pbQuarterly`: Price to book ratio (quarterly)
- `peAnnual`: Price to earnings ratio (annual)
- `peBasicExclExtraTTM`: P/E ratio TTM excluding extra items
- `peExclExtraAnnual`: P/E ratio annual excluding extra items
- `peExclExtraTTM`: P/E ratio TTM excluding extra items
- `peInclExtraTTM`: P/E ratio TTM including extra items
- `peNormalizedAnnual`: Normalized P/E ratio annual
- `peTTM`: P/E ratio TTM
- `psAnnual`: Price to sales ratio annual
- `psTTM`: Price to sales ratio TTM
- `ptbvAnnual`: Price to tangible book value annual
- `ptbvQuarterly`: Price to tangible book value quarterly

## Cash Flow Ratios
- `pcfShareAnnual`: Price to cash flow per share annual
- `pcfShareTTM`: Price to cash flow per share TTM
- `pfcfShareAnnual`: Price to free cash flow per share annual
- `pfcfShareTTM`: Price to free cash flow per share TTM

## Financial Metrics
- `marketCapitalization`: Market capitalization
- `enterpriseValue`: Enterprise value
- `currentEv/freeCashFlowAnnual`: Current EV to free cash flow annual
- `currentEv/freeCashFlowTTM`: Current EV to free cash flow TTM

## Per Share Metrics
- `bookValuePerShareAnnual`: Book value per share annual
- `bookValuePerShareQuarterly`: Book value per share quarterly
- `tangibleBookValuePerShareAnnual`: Tangible book value per share annual
- `tangibleBookValuePerShareQuarterly`: Tangible book value per share quarterly
- `cashFlowPerShareAnnual`: Cash flow per share annual
- `cashFlowPerShareQuarterly`: Cash flow per share quarterly
- `cashFlowPerShareTTM`: Cash flow per share TTM
- `cashPerSharePerShareAnnual`: Cash per share annual
- `cashPerSharePerShareQuarterly`: Cash per share quarterly
- `revenuePerShareAnnual`: Revenue per share annual
- `revenuePerShareTTM`: Revenue per share TTM

## Earnings Metrics
- `epsAnnual`: Earnings per share annual
- `epsBasicExclExtraItemsAnnual`: Basic EPS excluding extra items annual
- `epsBasicExclExtraItemsTTM`: Basic EPS excluding extra items TTM
- `epsExclExtraItemsAnnual`: EPS excluding extra items annual
- `epsExclExtraItemsTTM`: EPS excluding extra items TTM
- `epsInclExtraItemsAnnual`: EPS including extra items annual
- `epsInclExtraItemsTTM`: EPS including extra items TTM
- `epsNormalizedAnnual`: Normalized EPS annual
- `epsTTM`: EPS TTM

## Growth Metrics
- `bookValueShareGrowth5Y`: Book value per share 5-year growth
- `capexCagr5Y`: Capital expenditures 5-year CAGR
- `ebitdaCagr5Y`: EBITDA 5-year CAGR
- `ebitdaInterimCagr5Y`: EBITDA interim 5-year CAGR
- `epsGrowth3Y`: EPS 3-year growth
- `epsGrowth5Y`: EPS 5-year growth
- `epsGrowthQuarterlyYoy`: EPS quarterly year-over-year growth
- `epsGrowthTTMYoy`: EPS TTM year-over-year growth
- `focfCagr5Y`: Free operating cash flow 5-year CAGR
- `netMarginGrowth5Y`: Net margin 5-year growth
- `revenueGrowth3Y`: Revenue 3-year growth
- `revenueGrowth5Y`: Revenue 5-year growth
- `revenueGrowthQuarterlyYoy`: Revenue quarterly year-over-year growth
- `revenueGrowthTTMYoy`: Revenue TTM year-over-year growth
- `revenueShareGrowth5Y`: Revenue per share 5-year growth
- `tbvCagr5Y`: Tangible book value 5-year CAGR

## Profitability Metrics
- `grossMargin5Y`: Gross margin 5-year average
- `grossMarginAnnual`: Gross margin annual
- `grossMarginTTM`: Gross margin TTM
- `netProfitMargin5Y`: Net profit margin 5-year average
- `netProfitMarginAnnual`: Net profit margin annual
- `netProfitMarginTTM`: Net profit margin TTM
- `operatingMargin5Y`: Operating margin 5-year average
- `operatingMarginAnnual`: Operating margin annual
- `operatingMarginTTM`: Operating margin TTM
- `pretaxMargin5Y`: Pretax margin 5-year average
- `pretaxMarginAnnual`: Pretax margin annual
- `pretaxMarginTTM`: Pretax margin TTM

## Return Metrics
- `roa5Y`: Return on assets 5-year average
- `roaRfy`: Return on assets recent fiscal year
- `roaTTM`: Return on assets TTM
- `roe5Y`: Return on equity 5-year average
- `roeRfy`: Return on equity recent fiscal year
- `roeTTM`: Return on equity TTM
- `roi5Y`: Return on investment 5-year average
- `roiAnnual`: Return on investment annual
- `roiTTM`: Return on investment TTM

## Efficiency Metrics
- `assetTurnoverAnnual`: Asset turnover annual
- `assetTurnoverTTM`: Asset turnover TTM
- `inventoryTurnoverAnnual`: Inventory turnover annual
- `inventoryTurnoverTTM`: Inventory turnover TTM
- `receivablesTurnoverAnnual`: Receivables turnover annual
- `receivablesTurnoverTTM`: Receivables turnover TTM

## Liquidity Ratios
- `currentRatioAnnual`: Current ratio annual
- `currentRatioQuarterly`: Current ratio quarterly
- `quickRatioAnnual`: Quick ratio annual
- `quickRatioQuarterly`: Quick ratio quarterly

## Leverage Ratios
- `longTermDebt/equityAnnual`: Long-term debt to equity annual
- `longTermDebt/equityQuarterly`: Long-term debt to equity quarterly
- `totalDebt/totalEquityAnnual`: Total debt to total equity annual
- `totalDebt/totalEquityQuarterly`: Total debt to total equity quarterly

## Coverage Ratios
- `netInterestCoverageAnnual`: Net interest coverage annual
- `netInterestCoverageTTM`: Net interest coverage TTM

## Dividend Metrics
- `currentDividendYieldTTM`: Current dividend yield TTM
- `dividendGrowthRate5Y`: Dividend growth rate 5-year
- `dividendPerShareAnnual`: Dividend per share annual
- `dividendPerShareTTM`: Dividend per share TTM
- `dividendYieldIndicatedAnnual`: Indicated dividend yield annual
- `payoutRatioAnnual`: Payout ratio annual
- `payoutRatioTTM`: Payout ratio TTM

## EBITDA Metrics
- `ebitdPerShareAnnual`: EBITDA per share annual
- `ebitdPerShareTTM`: EBITDA per share TTM

## Employee Metrics
- `netIncomeEmployeeAnnual`: Net income per employee annual
- `netIncomeEmployeeTTM`: Net income per employee TTM
- `revenueEmployeeAnnual`: Revenue per employee annual
- `revenueEmployeeTTM`: Revenue per employee TTM

## Key Differences from Original Code

### Fixed Field Names:
- `totalDebt/totalEquityAnnual` (not `totalDebt2TotalEquityAnnual`)
- `netInterestCoverageTTM` (not `interestCoverageTTM`)
- `roiTTM` (not `roicTTM`)
- `revenueGrowthTTMYoy` (not `revenueGrowthTTM`)
- `epsGrowthTTMYoy` (not `epsGrowthTTM`)

### Missing Fields (Not Available in API):
- `evEbitdaTTM` - EV/EBITDA ratio
- `evSalesTTM` - EV/Sales ratio
- `fcfPerShareTTM` - Free cash flow per share
- `pegNonGaapFwdP1` - PEG ratio
- `dsoTTM` - Days sales outstanding
- `operatingCycleTTM` - Operating cycle
- `workingCapitalTurnoverTTM` - Working capital turnover
- `cashRatioAnnual` - Cash ratio
- `cfroiTTM` - Cash flow return on investment
- `totalDebt2TotalCapitalAnnual` - Total debt to total capital
- `fcfGrowthTTM` - Free cash flow growth

### Alternative Available Fields:
Instead of missing fields, you can use:
- `currentEv/freeCashFlowTTM` for free cash flow metrics
- `cashFlowPerShareTTM` for cash flow per share
- `longTermDebt/equityAnnual` for debt ratios
- Various growth rates with `Yoy` suffix for year-over-year comparisons 