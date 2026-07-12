# ============================================================
# src/data_fetcher.py — Data Ingestion Layer
# ============================================================
# Responsibility: Fetch raw stock data from Yahoo Finance.
#
# This module has ONE job (Single Responsibility Principle):
#   → Download historical stock price data
#   → Return it as a clean pandas DataFrame
#
# We keep this separate from preprocessing and ML logic so
# that if Yahoo Finance changes their API, we only fix THIS
# file — nothing else breaks.
# ============================================================

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def get_stock_data(
    ticker: str,
    period_years: int = 2,
) -> pd.DataFrame:
    """
    Download historical stock data from Yahoo Finance.

    Parameters
    ----------
    ticker : str
        The stock symbol (e.g., "AAPL" for Apple, "GOOGL" for Google).
    period_years : int, optional
        How many years of historical data to fetch. Default is 2.

    Returns
    -------
    pd.DataFrame
        A DataFrame with columns: Open, High, Low, Close, Volume.
        The index is the Date.

    Raises
    ------
    ValueError
        If the ticker is invalid or no data is returned.

    Example
    -------
    >>> df = get_stock_data("AAPL", period_years=1)
    >>> print(df.head())
    """
    # --- Step 1: Calculate the date range ---
    # We use today's date and go back 'period_years' years.
    # timedelta counts in days, so we multiply years × 365.
    end_date = datetime.today()
    start_date = end_date - timedelta(days=period_years * 365)

    # --- Step 2: Download data using yfinance ---
    # yf.download() talks to Yahoo Finance's servers and returns
    # a pandas DataFrame. This is the API call.
    #
    # Parameters:
    #   tickers   → Which stock to fetch
    #   start     → First date we want
    #   end       → Last date we want
    #   progress  → Don't show a download progress bar (cleaner output)
    print(f"[DATA] Fetching {ticker} data from {start_date.date()} to {end_date.date()}...")

    df = yf.download(
        tickers=ticker,
        start=start_date.strftime("%Y-%m-%d"),  # Format as "2024-01-01"
        end=end_date.strftime("%Y-%m-%d"),
        progress=False,
    )

    # --- Step 3: Validate the data ---
    # Always check that you actually got data back.
    # The API might return an empty DataFrame if:
    #   - The ticker symbol is wrong (e.g., "XYZXYZ")
    #   - Yahoo Finance is down
    #   - The date range has no trading days
    if df.empty:
        raise ValueError(
            f"No data found for ticker '{ticker}'. "
            "Please check the symbol and try again."
        )

    # --- Step 4: Clean up column names ---
    # yfinance sometimes returns MultiIndex columns like ('Close', 'AAPL')
    # when you download a single ticker. We flatten them to just 'Close'.
    # Different yfinance versions use different MultiIndex structures,
    # so we handle all cases robustly.
    if isinstance(df.columns, pd.MultiIndex):
        # Drop the ticker level (usually the last level named 'Ticker')
        # This is more reliable than get_level_values across yfinance versions
        try:
            df.columns = df.columns.droplevel('Ticker')
        except (KeyError, ValueError):
            # Fallback: just take the first level values
            df.columns = df.columns.get_level_values(0)

    # Remove any duplicate columns that may result from flattening
    df = df.loc[:, ~df.columns.duplicated()]

    # --- Step 5: Sort by date (oldest first) ---
    # ML models need data in chronological order.
    # This ensures row 0 is the oldest date and the last row is today.
    df = df.sort_index(ascending=True)

    print(f"[OK] Successfully fetched {len(df)} trading days of data for {ticker}")

    return df


def get_current_price(ticker: str) -> dict:
    """
    Get the current (most recent) stock price and basic info.

    Parameters
    ----------
    ticker : str
        The stock symbol (e.g., "AAPL").

    Returns
    -------
    dict
        A dictionary with keys: 'price', 'name', 'currency', 'market_cap'.

    Example
    -------
    >>> info = get_current_price("AAPL")
    >>> print(info['price'])
    """
    # yf.Ticker() creates a Ticker object — a "handle" to one stock.
    # It doesn't fetch data yet; it just remembers which stock you want.
    stock = yf.Ticker(ticker)

    # .info is a dictionary with ~100+ keys of company information.
    # We pick just the fields we need for our dashboard.
    #
    # IMPORTANT: stock.info can fail for many tickers due to:
    #   - Yahoo Finance rate limiting
    #   - Missing data for smaller/international stocks
    #   - Temporary API outages
    # We wrap in try/except and fall back to historical data.
    try:
        info = stock.info
        if not info or not isinstance(info, dict):
            raise ValueError("Empty or invalid info response")

        price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
        name = info.get("longName") or info.get("shortName") or ticker
        currency = info.get("currency") or "USD"
        market_cap = info.get("marketCap") or 0

        # If we still got a zero price, fall back to history
        if price == 0:
            raise ValueError("No price found in info dict")

        return {
            "price": price,
            "name": name,
            "currency": currency,
            "market_cap": market_cap,
        }

    except Exception as e:
        # Fallback: get the last close price from recent history
        print(f"[DATA] Warning: stock.info failed for {ticker} ({e}), using fallback...")
        try:
            hist = stock.history(period="5d")
            if not hist.empty:
                last_close = float(hist["Close"].iloc[-1])
                return {
                    "price": last_close,
                    "name": ticker,
                    "currency": "USD",
                    "market_cap": 0,
                }
        except Exception as fallback_error:
            print(f"[DATA] Warning: fallback history also failed: {fallback_error}")

        # Ultimate fallback — return zeros so the dashboard doesn't crash
        return {
            "price": 0,
            "name": ticker,
            "currency": "USD",
            "market_cap": 0,
        }


# ============================================================
# This block only runs when you execute this file directly:
#   python src/data_fetcher.py
#
# It does NOT run when another file imports from this module:
#   from src.data_fetcher import get_stock_data
#
# This is a Python best practice for testing your module.
# ============================================================
if __name__ == "__main__":
    # Quick test — fetch Apple stock data
    test_ticker = "AAPL"

    # Test get_stock_data
    data = get_stock_data(test_ticker, period_years=1)
    print("\n--- First 5 rows ---")
    print(data.head())
    print("\n--- Last 5 rows ---")
    print(data.tail())
    print(f"\n--- Shape: {data.shape} (rows, columns) ---")
    print(f"--- Columns: {list(data.columns)} ---")
    print(f"--- Date range: {data.index[0].date()} to {data.index[-1].date()} ---")

    # Test get_current_price
    print("\n--- Current Price Info ---")
    price_info = get_current_price(test_ticker)
    for key, value in price_info.items():
        print(f"  {key}: {value}")
