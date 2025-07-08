from langchain_core.messages import HumanMessage
from src.graph.state import AgentState, show_agent_reasoning
from src.utils.progress import progress
import pandas as pd
import numpy as np
import json

from src.external.clients.api import get_company_news
from src.utils.streaming import with_streaming_progress, emit_ticker_progress
from src.data.models import SentimentType


##### Sentiment Agent #####
@with_streaming_progress("sentiment")
def sentiment_agent(state: AgentState):
    """Analyzes market sentiment and generates trading signals for multiple tickers."""
    data = state.get("data", {})
    end_date = data.get("end_date")
    tickers = data.get("tickers")

    # Initialize sentiment analysis for each ticker
    sentiment_analysis = {}

    for ticker in tickers:
        progress.update_status("sentiment_agent", ticker, "Fetching insider trades")

        # Insider trades functionality has been removed

        progress.update_status("sentiment_agent", ticker, "Analyzing trading patterns")

        # Insider signals have been removed

        progress.update_status("sentiment_agent", ticker, "Fetching company news")

        # Get the company news
        company_news = get_company_news(ticker, end_date, limit=10)

        # Get the sentiment from the company news
        sentiment = pd.Series([n.sentiment for n in company_news]).dropna()
        news_signals = np.where(sentiment == SentimentType.NEGATIVE, "bearish", 
                              np.where(sentiment == SentimentType.POSITIVE, "bullish", "neutral")).tolist()
        
        progress.update_status("sentiment_agent", ticker, "Analyzing news signals")
        # Analyze news signals only
        
        # Count signal types
        bullish_count = news_signals.count("bullish")
        bearish_count = news_signals.count("bearish")
        neutral_count = news_signals.count("neutral")
        
        total_signals = len(news_signals)
        
        if bullish_count > bearish_count:
            overall_signal = "bullish"
        elif bearish_count > bullish_count:
            overall_signal = "bearish"
        else:
            overall_signal = "neutral"

        # Calculate confidence level based on signal dominance
        confidence = 0  # Default confidence when there are no signals
        if total_signals > 0:
            confidence = round(max(bullish_count, bearish_count, neutral_count) / total_signals, 2) * 100
        reasoning = f"News signals - Bullish: {bullish_count}, Bearish: {bearish_count}, Neutral: {neutral_count}"

        sentiment_analysis[ticker] = {
            "signal": overall_signal,
            "confidence": confidence,
            "reasoning": reasoning,
        }

        progress.update_status("sentiment_agent", ticker, "Done")

    # Create the sentiment message
    message = HumanMessage(
        content=json.dumps(sentiment_analysis),
        name="sentiment_agent",
    )

    # Print the reasoning if the flag is set
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(sentiment_analysis, "Sentiment Analysis Agent")

    # Add the signal to the analyst_signals list
    state["data"]["analyst_signals"]["sentiment_agent"] = sentiment_analysis

    return {
        "messages": [message],
        "data": data,
    }
