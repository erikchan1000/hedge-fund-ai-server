# FinnHub and Alpaca API Documentation Summary

## FinnHub API

### Authentication
- **Method**: Query parameter authentication
- **Parameter**: `token=YOUR_API_KEY`
- **Example**: `https://finnhub.io/api/v1/quote?symbol=AAPL&token=YOUR_API_KEY`

### Key Endpoints

#### 1. Stock Metrics (`/stock/metric`)
- **Purpose**: Get comprehensive financial metrics and ratios
- **Parameters**: 
  - `symbol`: Stock symbol (required)
  - `metric`: "all" for all metrics (recommended)
- **Response Structure**:
  ```json
  {
    "metric": {
      "peBasicExclExtraTTM": 28.5,
      "pbAnnual": 6.2,
      "psAnnual": 7.8,
      "evEbitdaTTM": 22.1,
      "roeTTM": 0.95,
      "roaTTM": 0.22,
      // ... many more metrics
    },
    "series": {
      "annual": {
        "currentRatioAnnual": [
          {"period": "2023-09-30", "v": 1.05},
          {"period": "2022-09-30", "v": 1.04}
        ]
        // ... historical series data
      }
    }
  }
  ```

#### 2. Stock Prices (`/stock/candle`)
- **Purpose**: Get historical price data
- **Parameters**:
  - `symbol`: Stock symbol
  - `resolution`: "D" for daily, "W" for weekly, etc.
  - `from`: Start timestamp (Unix)
  - `to`: End timestamp (Unix)

#### 3. Company Profile (`/stock/profile2`)
- **Purpose**: Get company basic information
- **Response**: Company name, market cap, currency, etc.

#### 4. Insider Transactions (`/stock/insider-transactions`)
- **Purpose**: Get insider trading data
- **Parameters**: `symbol`

#### 5. Company News (`/company-news`)
- **Purpose**: Get company-specific news
- **Parameters**: `symbol`, `from` (date), `to` (date)

### Rate Limiting
- **Free Plan**: 60 calls/minute, 30 calls/second
- **Paid Plans**: Higher limits available

### Important Field Mappings for Financial Metrics
```python
# Common FinnHub metric field names:
"peBasicExclExtraTTM"        # P/E Ratio TTM
"pbAnnual"                   # Price to Book Annual
"psAnnual"                   # Price to Sales Annual
"evEbitdaTTM"               # EV/EBITDA TTM
"roeTTM"                    # Return on Equity TTM
"roaTTM"                    # Return on Assets TTM
"currentRatioAnnual"        # Current Ratio
"totalDebt2TotalEquityAnnual" # Debt to Equity
"epsBasicExclExtraItemsTTM" # Earnings Per Share TTM
"revenueTTM"                # Revenue TTM
"netIncomeTTM"              # Net Income TTM
```

---

## Alpaca API

### Authentication
- **Method**: HTTP Headers
- **Headers**:
  - `APCA-API-KEY-ID`: Your API key
  - `APCA-API-SECRET-KEY`: Your secret key

### Base URLs
- **Live Trading**: `https://api.alpaca.markets`
- **Paper Trading**: `https://paper-api.alpaca.markets`
- **Market Data**: `https://data.alpaca.markets`

### Key Endpoints

#### 1. Historical Bars (`/v2/stocks/bars`)
- **Purpose**: Get historical price data (OHLCV)
- **Parameters**:
  - `symbols`: Comma-separated stock symbols
  - `timeframe`: "1Day", "1Hour", "1Min", etc.
  - `start`: ISO datetime string
  - `end`: ISO datetime string
  - `limit`: Max 10,000 bars per request
- **Response Structure**:
  ```json
  {
    "bars": {
      "AAPL": [
        {
          "t": "2023-01-03T05:00:00Z",
          "o": 130.28,
          "h": 130.9,
          "l": 124.17,
          "c": 125.07,
          "v": 112117471
        }
      ]
    }
  }
  ```

#### 2. Latest Quotes (`/v2/stocks/quotes/latest`)
- **Purpose**: Get latest bid/ask prices
- **Parameters**: `symbols`

#### 3. Real-time Streaming
- **WebSocket URL**: `wss://stream.data.alpaca.markets/v2/iex`
- **Authentication**: Via WebSocket connection
- **Channels**: trades, quotes, bars

### Subscription Plans
- **Basic (Free)**: 
  - 200 API calls/minute
  - IEX data (15-minute delayed)
  - 5 years historical data
  
- **Algo Trader Plus ($99/month)**:
  - Unlimited API calls
  - Real-time data
  - Full market data access

### Python SDK Usage Example
```python
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime

# Initialize client
client = StockHistoricalDataClient("api_key", "secret_key")

# Create request
request = StockBarsRequest(
    symbol_or_symbols=["AAPL", "MSFT"],
    timeframe=TimeFrame.Day,
    start=datetime(2023, 1, 1),
    end=datetime(2023, 12, 31)
)

# Get data
bars = client.get_stock_bars(request)

# Convert to DataFrame
df = bars.df
```

---

## Key Implementation Notes

### FinnHub Best Practices
1. Use `/stock/metric` endpoint for financial ratios and metrics
2. Handle rate limiting appropriately (60 calls/minute for free)
3. Use query parameter authentication (`token=YOUR_API_KEY`)
4. Check for data availability - not all metrics available for all stocks
5. Handle both "metric" (current) and "series" (historical) data in responses

### Alpaca Best Practices
1. Use proper header authentication
2. Handle pagination for large datasets (limit=10,000)
3. Use appropriate timeframes for your use case
4. Consider using real-time streams for live data
5. Paper trading environment available for testing

### Error Handling
- Both APIs return different error structures
- Implement proper retry logic for rate limits
- Handle missing data gracefully (some stocks may not have all metrics)
- Log errors appropriately for debugging

### Data Freshness
- **FinnHub**: Updates vary by data type (real-time for prices, quarterly for fundamentals)
- **Alpaca**: Real-time for subscribed data feeds, historical data available with slight delays 