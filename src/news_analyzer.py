# ============================================================
# src/news_analyzer.py — News & NLP Layer
# ============================================================
# Responsibility: Fetch stock news, analyze sentiment, and
# create AI-powered summaries.
#
# This module combines:
#   1. News fetching via yfinance (no API key needed!)
#   2. Sentiment analysis using FinBERT (financial-specific)
#   3. AI summarization using DistilBART
#
# NOTE: First run downloads ~1.5GB of AI models (one-time).
# After that, models are cached locally in ~/.cache/huggingface/
# ============================================================

import yfinance as yf
from transformers import pipeline
import warnings

# Suppress verbose transformer warnings (they clutter output)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# ============================================================
# Global model cache — Lazy Loading pattern
# ============================================================
# We store loaded models here so they're only loaded ONCE,
# even if the function is called multiple times.
#
# Why lazy loading?
# Loading a transformer model takes 5-15 seconds and ~500MB RAM.
# If we loaded it at import time (top of file), every import
# of this module would freeze for 15 seconds. Instead, we load
# on first use and cache the result.
#
# This is a common industry pattern called the "Singleton" pattern.
# ============================================================
_sentiment_pipeline = None
_summarizer_pipeline = None


def _get_sentiment_model():
    """Load the sentiment model on first use, then cache it."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        print("[NLP] Loading FinBERT sentiment model (first time may take a minute)...")
        # ProsusAI/finbert is trained specifically on financial text.
        # It outputs: "positive", "negative", or "neutral"
        # with a confidence score between 0 and 1.
        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            # truncation=True ensures long text is cut to model's max length
            # (512 tokens) instead of crashing
            truncation=True,
        )
        print("[NLP] Sentiment model loaded!")
    return _sentiment_pipeline


# Removed DistilBART as it's designed for long articles, not short headlines.
# We will use sentiment-aware extractive summarization instead.


# ============================================================
# News Fetching
# ============================================================

def fetch_stock_news(ticker: str, max_articles: int = 10) -> list:
    """
    Fetch the latest news articles for a stock.

    Uses yfinance's built-in news feature, which pulls from
    Yahoo Finance. No API key required!

    Parameters
    ----------
    ticker : str
        Stock symbol (e.g., "AAPL").
    max_articles : int
        Maximum number of articles to return.

    Returns
    -------
    list of dict
        Each dict has keys: 'title', 'publisher', 'link', 'published'.
    """
    print(f"[NEWS] Fetching news for {ticker}...")

    try:
        stock = yf.Ticker(ticker)

        try:
            # .news returns a list of dicts with article metadata.
            # Each article has: title, publisher, link, providerPublishTime, etc.
            raw_news = stock.news
        except Exception as e:
            print(f"[NEWS] Warning: Could not fetch news: {e}")
            return []

        if not raw_news:
            print("[NEWS] No news articles found")
            return []

        # Clean and structure the news data
        # yfinance 1.5+ nests article data inside a 'content' key.
        # Older versions use a flat structure. We handle both.
        articles = []
        for item in raw_news[:max_articles]:
            try:
                # Check if data is nested inside 'content' (new format)
                content = item.get("content", item) if isinstance(item, dict) else {}

                title = content.get("title", "")
                publisher = ""
                link = ""
                published = ""

                # Extract publisher (varies by format)
                provider = content.get("provider", {})
                if isinstance(provider, dict):
                    publisher = provider.get("displayName", "Unknown")
                else:
                    publisher = content.get("publisher", "Unknown")

                # Extract link (varies by format)
                canonical = content.get("canonicalUrl", {})
                if isinstance(canonical, dict):
                    link = canonical.get("url", "")
                else:
                    link = content.get("link", "")

                # Extract publish date
                published = content.get("pubDate", content.get("providerPublishTime", ""))

                article = {
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "published": published,
                }

                # Only include articles that have a meaningful title
                if title:
                    articles.append(article)
            except Exception as article_error:
                # Skip malformed articles instead of crashing
                print(f"[NEWS] Warning: Skipped malformed article: {article_error}")
                continue

        print(f"[NEWS] Found {len(articles)} articles")
        return articles

    except Exception as e:
        # Catch-all: if anything unexpected happens, return empty
        print(f"[NEWS] Error fetching news for {ticker}: {e}")
        return []


# ============================================================
# Sentiment Analysis
# ============================================================

def analyze_sentiment(headlines: list) -> dict:
    """
    Analyze the sentiment of stock news headlines.

    Uses FinBERT to classify each headline as:
    - "Bullish"  (positive news for the stock)
    - "Bearish"  (negative news for the stock)
    - "Neutral"  (no clear sentiment)

    Then aggregates across all headlines to produce an
    overall sentiment score and label.

    Parameters
    ----------
    headlines : list of str
        News headlines to analyze.

    Returns
    -------
    dict
        Contains:
        - 'overall_sentiment': "Bullish", "Bearish", or "Neutral"
        - 'confidence': float 0-1 (how confident the model is)
        - 'positive_pct': float (% of bullish headlines)
        - 'negative_pct': float (% of bearish headlines)
        - 'neutral_pct': float (% of neutral headlines)
        - 'details': list of per-headline results
    """
    if not headlines:
        return {
            "overall_sentiment": "Neutral",
            "confidence": 0.0,
            "positive_pct": 0.0,
            "negative_pct": 0.0,
            "neutral_pct": 100.0,
            "details": [],
        }

    # Get the sentiment model (loads on first call, cached after)
    classifier = _get_sentiment_model()

    # Analyze each headline individually
    # We process one at a time for clearer error handling
    details = []
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    total_confidence = 0

    for headline in headlines:
        try:
            # The pipeline returns a list with one result dict
            # Example: [{'label': 'positive', 'score': 0.9823}]
            result = classifier(headline)[0]

            label = result["label"].lower()  # "positive", "negative", "neutral"
            score = result["score"]          # confidence 0-1

            # Map FinBERT labels to our labels
            display_label = {
                "positive": "Bullish",
                "negative": "Bearish",
                "neutral": "Neutral",
            }.get(label, "Neutral")

            details.append({
                "headline": headline,
                "sentiment": display_label,
                "confidence": round(score, 3),
            })

            sentiment_counts[label] += 1
            total_confidence += score

        except Exception as e:
            # If one headline fails, skip it and continue
            print(f"[NLP] Warning: Skipped headline due to error: {e}")
            details.append({
                "headline": headline,
                "sentiment": "Neutral",
                "confidence": 0.0,
            })
            sentiment_counts["neutral"] += 1

    # Calculate percentages
    total = len(headlines)
    positive_pct = (sentiment_counts["positive"] / total) * 100
    negative_pct = (sentiment_counts["negative"] / total) * 100
    neutral_pct = (sentiment_counts["neutral"] / total) * 100

    # Determine overall sentiment by majority vote
    if positive_pct > negative_pct and positive_pct > neutral_pct:
        overall = "Bullish"
    elif negative_pct > positive_pct and negative_pct > neutral_pct:
        overall = "Bearish"
    else:
        overall = "Neutral"

    avg_confidence = total_confidence / total if total > 0 else 0

    return {
        "overall_sentiment": overall,
        "confidence": round(avg_confidence, 3),
        "positive_pct": round(positive_pct, 1),
        "negative_pct": round(negative_pct, 1),
        "neutral_pct": round(neutral_pct, 1),
        "details": details,
    }


# ============================================================
# AI Summarization
# ============================================================

def summarize_news(headlines: list, sentiment_result: dict) -> str:
    """
    Create a summary of stock news based on sentiment.

    Instead of forcing a heavy AI model to summarize short headlines,
    we do something smarter: we group the headlines by sentiment
    to give the user a clear picture of what's driving the stock.

    Parameters
    ----------
    headlines : list of str
        News headlines.
    sentiment_result : dict
        The output from analyze_sentiment().

    Returns
    -------
    str
        A coherent summary paragraph highlighting key sentiments.
    """
    if not headlines:
        return "No recent news available for this stock."

    details = sentiment_result.get("details", [])
    if not details:
        return ". ".join(headlines[:3]) + "."

    # Group headlines by sentiment
    bullish = [item["headline"] for item in details if item["sentiment"] == "Bullish"]
    bearish = [item["headline"] for item in details if item["sentiment"] == "Bearish"]

    summary_parts = []
    
    # Build a narrative based on the strongest signals
    if bullish:
        summary_parts.append(f"Positive drivers include: '{bullish[0]}'")
    if bearish:
        summary_parts.append(f"On the downside, concerns involve: '{bearish[0]}'")
        
    if not summary_parts:
        summary_parts.append(f"Recent news is largely neutral, such as: '{headlines[0]}'")

    overall = sentiment_result.get("overall_sentiment", "Neutral")
    summary_parts.insert(0, f"Overall news sentiment is currently {overall}.")

    return " ".join(summary_parts)


# ============================================================
# Combined Analysis — The main function for the dashboard
# ============================================================

def get_full_analysis(ticker: str) -> dict:
    """
    Perform a complete news analysis for a stock ticker.

    This is the main entry point that the Streamlit dashboard
    will call. It combines news fetching, sentiment analysis,
    and summarization into one convenient function.

    Parameters
    ----------
    ticker : str
        Stock symbol (e.g., "AAPL").

    Returns
    -------
    dict
        Contains:
        - 'articles': list of news article dicts
        - 'headlines': list of headline strings
        - 'sentiment': sentiment analysis results
        - 'summary': AI-generated summary string
    """
    # Step 1: Fetch news
    articles = fetch_stock_news(ticker)
    headlines = [a["title"] for a in articles]

    # Step 2: Analyze sentiment
    sentiment = analyze_sentiment(headlines)

    # Step 3: Generate summary based on sentiment
    summary = summarize_news(headlines, sentiment)

    return {
        "articles": articles,
        "headlines": headlines,
        "sentiment": sentiment,
        "summary": summary,
    }


# ============================================================
# Test the news analyzer
# ============================================================
if __name__ == "__main__":
    ticker = "AAPL"

    print("=" * 60)
    print(f"NEWS ANALYSIS TEST: {ticker}")
    print("=" * 60)

    # Run full analysis
    result = get_full_analysis(ticker)

    # Display results
    print(f"\n--- Headlines ({len(result['headlines'])}) ---")
    for i, article in enumerate(result["articles"], 1):
        sentiment_detail = result["sentiment"]["details"][i - 1] if i <= len(result["sentiment"]["details"]) else {}
        label = sentiment_detail.get("sentiment", "N/A")
        conf = sentiment_detail.get("confidence", 0)
        print(f"  {i}. [{label} {conf:.0%}] {article['title']}")
        print(f"     Source: {article['publisher']}")

    print(f"\n--- Overall Sentiment ---")
    s = result["sentiment"]
    print(f"  Verdict:    {s['overall_sentiment']}")
    print(f"  Confidence: {s['confidence']:.1%}")
    print(f"  Bullish:    {s['positive_pct']}%")
    print(f"  Bearish:    {s['negative_pct']}%")
    print(f"  Neutral:    {s['neutral_pct']}%")

    print(f"\n--- AI Summary ---")
    print(f"  {result['summary']}")
