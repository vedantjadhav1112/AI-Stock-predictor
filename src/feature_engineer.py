# ============================================================
# src/feature_engineer.py — Feature Engineering Layer
# ============================================================
# Responsibility: Transform clean stock data into ML-ready
# features that help the model detect patterns.
#
# Features we create:
#   1. Price changes (daily returns)
#   2. Moving Averages (SMA 5, 10, 20)
#   3. RSI (Relative Strength Index)
#   4. Volatility (rolling standard deviation)
#   5. Price ratios (Close vs Moving Averages)
#   6. Lag features (prices from N days ago)
#   7. Volume change
#   8. Day of week (stocks behave differently Mon vs Fri)
#   9. Target variable (next day's Close price)
# ============================================================

import pandas as pd
import numpy as np


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create ML features from clean stock data.

    Takes a preprocessed DataFrame (from preprocessor.py) and
    adds ~15 new columns that capture trends, momentum, and
    volatility — all signals that help predict future prices.

    Parameters
    ----------
    df : pd.DataFrame
        Clean stock data with columns: Open, High, Low, Close, Volume.

    Returns
    -------
    pd.DataFrame
        The same DataFrame with additional feature columns and
        a 'Target' column (next day's Close price).
        Rows with NaN (from rolling calculations) are dropped.
    """
    df = df.copy()  # Don't modify the original (no side effects)

    # ==========================================================
    # FEATURE 1: Daily Price Change (Returns)
    # ==========================================================
    # How much did the price change from yesterday to today?
    # .pct_change() calculates: (today - yesterday) / yesterday
    #
    # Example: yesterday = $100, today = $105
    #   pct_change = (105 - 100) / 100 = 0.05 = 5% increase
    #
    # Why useful? A model can learn "stocks that rose 3%+ in a
    # day tend to pull back the next day."
    df["Daily_Return"] = df["Close"].pct_change()

    # Absolute price change in dollars (not percentage)
    df["Price_Change"] = df["Close"].diff()
    # .diff() = today's value minus yesterday's value

    # ==========================================================
    # FEATURE 2: Simple Moving Averages (SMA)
    # ==========================================================
    # A moving average smooths out daily noise to show the trend.
    # .rolling(window=N) creates a sliding window of N rows,
    # then .mean() averages the values in that window.
    #
    # SMA_5  = average of last 5 days  (short-term trend)
    # SMA_10 = average of last 10 days (medium-term trend)
    # SMA_20 = average of last 20 days (longer-term trend)
    df["SMA_5"] = df["Close"].rolling(window=5).mean()
    df["SMA_10"] = df["Close"].rolling(window=10).mean()
    df["SMA_20"] = df["Close"].rolling(window=20).mean()

    # ==========================================================
    # FEATURE 3: Price vs. Moving Average Ratios
    # ==========================================================
    # Instead of raw SMA values, we calculate HOW FAR the current
    # price is from its moving average. This is more meaningful:
    #   ratio > 1.0 → price is ABOVE the average (bullish)
    #   ratio < 1.0 → price is BELOW the average (bearish)
    #   ratio ≈ 1.0 → price is near the average (neutral)
    df["Close_to_SMA5"] = df["Close"] / df["SMA_5"]
    df["Close_to_SMA20"] = df["Close"] / df["SMA_20"]

    # ==========================================================
    # FEATURE 4: RSI (Relative Strength Index)
    # ==========================================================
    # RSI measures momentum on a scale of 0-100.
    # It answers: "Are buyers or sellers winning recently?"
    df["RSI"] = _calculate_rsi(df["Close"], period=14)

    # ==========================================================
    # FEATURE 5: Volatility (Rolling Standard Deviation)
    # ==========================================================
    # Volatility = how much the price "jumps around."
    # High volatility = risky, unpredictable
    # Low volatility  = stable, predictable
    #
    # We use the standard deviation of daily returns over 10 days.
    # std() measures "how spread out the values are from the mean."
    df["Volatility_10"] = df["Daily_Return"].rolling(window=10).std()

    # ==========================================================
    # FEATURE 6: Lag Features
    # ==========================================================
    # "What was the close price N days ago?"
    # .shift(N) moves the column DOWN by N rows.
    #
    # If today is row 10:
    #   Lag_1 = row 9's Close (yesterday)
    #   Lag_5 = row 5's Close (5 trading days ago, ~1 week)
    df["Lag_1"] = df["Close"].shift(1)
    df["Lag_2"] = df["Close"].shift(2)
    df["Lag_5"] = df["Close"].shift(5)

    # ==========================================================
    # FEATURE 7: Volume Change
    # ==========================================================
    # Did trading volume increase or decrease vs yesterday?
    # Sudden volume spikes often signal big price moves.
    df["Volume_Change"] = df["Volume"].pct_change()

    # ==========================================================
    # FEATURE 8: High-Low Spread
    # ==========================================================
    # The difference between the day's high and low price.
    # A large spread means the stock was very volatile that day.
    df["High_Low_Spread"] = (df["High"] - df["Low"]) / df["Close"]

    # ==========================================================
    # FEATURE 9: Day of Week
    # ==========================================================
    # Stocks sometimes behave differently on certain days.
    # Monday effect: stocks tend to drop on Mondays.
    # Friday effect: some traders sell before the weekend.
    # 0 = Monday, 1 = Tuesday, ..., 4 = Friday
    df["Day_of_Week"] = df.index.dayofweek

    # ==========================================================
    # TARGET VARIABLE: Next Day's Close Price
    # ==========================================================
    # This is what we want the ML model to PREDICT.
    # .shift(-1) moves the column UP by 1 row, so each row
    # now has "tomorrow's close" aligned with "today's features."
    #
    # Before shift(-1):
    #   Row 0: Close=150  →  Target=NaN (no "previous" target)
    # After shift(-1):
    #   Row 0: Close=150  →  Target=153 (row 1's Close)
    #   Row 1: Close=153  →  Target=155 (row 2's Close)
    #   Last:  Close=160  →  Target=NaN (future is unknown!)
    df["Target"] = df["Close"].shift(-1)

    # ==========================================================
    # CLEANUP: Drop rows with NaN values
    # ==========================================================
    # Rolling calculations (SMA_20, RSI, etc.) produce NaN for
    # the first N rows because there aren't enough previous rows
    # to fill the window. The Target column has NaN on the last
    # row (we can't know tomorrow's price yet).
    #
    # We must drop these rows — ML models can't learn from NaN.
    rows_before = len(df)
    df = df.dropna()
    rows_dropped = rows_before - len(df)
    print(f"[FEATURES] Created {len(df.columns) - 5} new features")
    print(f"[FEATURES] Dropped {rows_dropped} rows with NaN (from rolling windows)")
    print(f"[FEATURES] Final dataset: {len(df)} rows x {len(df.columns)} columns")

    # Guard: ensure we have enough data to train a model
    if len(df) < 50:
        raise ValueError(
            f"Not enough data after feature engineering ({len(df)} rows). "
            f"Need at least 50 trading days of history. "
            f"This stock may be too new or have limited data on Yahoo Finance."
        )

    return df


def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate the Relative Strength Index (RSI).

    RSI Formula:
        RSI = 100 - (100 / (1 + RS))
        RS  = Average Gain / Average Loss (over 'period' days)

    Parameters
    ----------
    prices : pd.Series
        A series of closing prices.
    period : int
        Number of days to look back. Default is 14 (industry standard).

    Returns
    -------
    pd.Series
        RSI values ranging from 0 to 100.
    """
    # Step 1: Calculate daily price changes
    delta = prices.diff()

    # Step 2: Separate gains (positive changes) and losses (negative changes)
    # .clip(lower=0) keeps only values >= 0 (sets negatives to 0)
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)  # Negate so losses become positive numbers

    # Step 3: Calculate the average gain and average loss over 'period' days
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # Step 4: Calculate RS (Relative Strength)
    # Add a tiny number (1e-10) to avoid division by zero
    rs = avg_gain / (avg_loss + 1e-10)

    # Step 5: Convert RS to RSI (scale of 0-100)
    rsi = 100 - (100 / (1 + rs))

    return rsi


def get_feature_names(df: pd.DataFrame) -> list:
    """
    Return the list of feature column names (everything except Target).

    This is a helper function used when training the model to
    separate features (X) from the target (y).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with engineered features and a 'Target' column.

    Returns
    -------
    list
        Column names that are features (not the target).
    """
    # Everything except the Target and original OHLCV columns
    exclude = ["Target"]
    return [col for col in df.columns if col not in exclude]


# ============================================================
# Test the feature engineer independently
# ============================================================
if __name__ == "__main__":
    from data_fetcher import get_stock_data
    from preprocessor import preprocess_stock_data

    # Step 1: Fetch raw data
    raw_data = get_stock_data("AAPL", period_years=1)

    # Step 2: Clean it
    clean_data = preprocess_stock_data(raw_data)

    # Step 3: Engineer features
    featured_data = add_features(clean_data)

    # Show results
    print("\n--- All Columns ---")
    for i, col in enumerate(featured_data.columns, 1):
        print(f"  {i:2d}. {col}")

    print(f"\n--- Feature columns (for ML) ---")
    feature_names = get_feature_names(featured_data)
    for name in feature_names:
        print(f"  - {name}")

    print(f"\n--- Sample row (last row) ---")
    last_row = featured_data.iloc[-1]
    for col, val in last_row.items():
        if isinstance(val, float):
            print(f"  {col:20s}: {val:.4f}")
        else:
            print(f"  {col:20s}: {val}")

    print(f"\n--- RSI Statistics ---")
    print(f"  Min RSI:  {featured_data['RSI'].min():.1f}")
    print(f"  Max RSI:  {featured_data['RSI'].max():.1f}")
    print(f"  Mean RSI: {featured_data['RSI'].mean():.1f}")
