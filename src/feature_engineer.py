# ============================================================
# src/feature_engineer.py — Feature Engineering Layer
# ============================================================
# Responsibility: Transform clean stock data into ML-ready
# features that help the model detect patterns.
#
# Features we create:
#   BASIC (original):
#     1. Price changes (daily returns)
#     2. Moving Averages (SMA 5, 10, 20)
#     3. RSI (Relative Strength Index)
#     4. Volatility (rolling standard deviation)
#     5. Price ratios (Close vs Moving Averages)
#     6. Lag features (prices from N days ago)
#     7. Volume change
#     8. Day of week
#     9. Target variable (next day's Close price)
#
#   ADVANCED (new for AI Research Platform):
#     10. MACD (Moving Average Convergence Divergence)
#     11. Bollinger Bands (upper, lower, width, %B)
#     12. ATR (Average True Range)
#     13. OBV (On-Balance Volume)
#     14. Stochastic Oscillator (%K, %D)
#     15. ADX (Average Directional Index)
#     16. SMA 50 & SMA 200 (long-term trend)
#     17. Golden/Death Cross signals
#     18. Support & Resistance levels
#     19. EMA 12 & EMA 26
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
    # ADVANCED FEATURE 10: MACD (Moving Average Convergence
    #                       Divergence)
    # ==========================================================
    # MACD shows the relationship between two EMAs.
    #   MACD Line = EMA(12) - EMA(26)
    #   Signal Line = EMA(9) of MACD Line
    #   Histogram = MACD Line - Signal Line
    #
    # Interpretation:
    #   MACD > Signal → Bullish momentum
    #   MACD < Signal → Bearish momentum
    #   Histogram growing → Momentum accelerating
    df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA_26"] = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Histogram"] = df["MACD"] - df["MACD_Signal"]

    # ==========================================================
    # ADVANCED FEATURE 11: Bollinger Bands
    # ==========================================================
    # Bollinger Bands = SMA(20) ± 2 standard deviations
    #   Upper Band = SMA20 + 2*std
    #   Lower Band = SMA20 - 2*std
    #   Band Width = (Upper - Lower) / SMA20
    #   %B = (Close - Lower) / (Upper - Lower)
    #
    # Interpretation:
    #   Price near upper band → potentially overbought
    #   Price near lower band → potentially oversold
    #   Narrow bands → low volatility, breakout likely
    bb_std = df["Close"].rolling(window=20).std()
    df["BB_Upper"] = df["SMA_20"] + (bb_std * 2)
    df["BB_Lower"] = df["SMA_20"] - (bb_std * 2)
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / df["SMA_20"]
    df["BB_Percent_B"] = (df["Close"] - df["BB_Lower"]) / (df["BB_Upper"] - df["BB_Lower"])

    # ==========================================================
    # ADVANCED FEATURE 12: ATR (Average True Range)
    # ==========================================================
    # ATR measures volatility by looking at the full range of
    # price movement including gaps. Used for stop-loss placement.
    #
    # True Range = max of:
    #   (High - Low), abs(High - Previous Close), abs(Low - Previous Close)
    # ATR = rolling mean of True Range over 14 days
    prev_close = df["Close"].shift(1)
    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - prev_close).abs()
    tr3 = (df["Low"] - prev_close).abs()
    df["True_Range"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["ATR_14"] = df["True_Range"].rolling(window=14).mean()

    # ==========================================================
    # ADVANCED FEATURE 13: OBV (On-Balance Volume)
    # ==========================================================
    # OBV tracks cumulative volume flow. It adds volume on up days
    # and subtracts on down days. Divergences between OBV and
    # price can signal trend reversals.
    obv = [0]
    for i in range(1, len(df)):
        if df["Close"].iloc[i] > df["Close"].iloc[i - 1]:
            obv.append(obv[-1] + df["Volume"].iloc[i])
        elif df["Close"].iloc[i] < df["Close"].iloc[i - 1]:
            obv.append(obv[-1] - df["Volume"].iloc[i])
        else:
            obv.append(obv[-1])
    df["OBV"] = obv
    # Normalize OBV to make it comparable across stocks
    df["OBV_SMA_20"] = df["OBV"].rolling(window=20).mean()

    # ==========================================================
    # ADVANCED FEATURE 14: Stochastic Oscillator (%K, %D)
    # ==========================================================
    # Stochastic measures where the close is relative to the
    # high-low range over the last 14 days.
    #   %K = (Close - Lowest Low) / (Highest High - Lowest Low) × 100
    #   %D = SMA(3) of %K (signal line)
    #
    # Interpretation:
    #   %K > 80 → Overbought
    #   %K < 20 → Oversold
    #   %K crosses above %D → Buy signal
    low_14 = df["Low"].rolling(window=14).min()
    high_14 = df["High"].rolling(window=14).max()
    df["Stochastic_K"] = ((df["Close"] - low_14) / (high_14 - low_14 + 1e-10)) * 100
    df["Stochastic_D"] = df["Stochastic_K"].rolling(window=3).mean()

    # ==========================================================
    # ADVANCED FEATURE 15: ADX (Average Directional Index)
    # ==========================================================
    # ADX measures trend strength (NOT direction) on a 0-100 scale.
    #   ADX > 25 → Strong trend (good for trend-following)
    #   ADX < 20 → Weak/no trend (range-bound, mean reversion)
    df["ADX"] = _calculate_adx(df, period=14)

    # ==========================================================
    # ADVANCED FEATURE 16: Long-Term Moving Averages
    # ==========================================================
    # SMA_50 and SMA_200 are the most watched institutional levels.
    # These require at least 200 days of data to compute.
    df["SMA_50"] = df["Close"].rolling(window=50).mean()
    df["SMA_200"] = df["Close"].rolling(window=200).mean()
    df["Close_to_SMA50"] = df["Close"] / df["SMA_50"]
    df["Close_to_SMA200"] = df["Close"] / df["SMA_200"]

    # ==========================================================
    # ADVANCED FEATURE 17: Golden Cross / Death Cross
    # ==========================================================
    # Golden Cross: SMA_50 crosses ABOVE SMA_200 (bullish)
    # Death Cross:  SMA_50 crosses BELOW SMA_200 (bearish)
    # We encode as: 1 = above (bullish), 0 = below (bearish)
    df["SMA50_above_SMA200"] = (df["SMA_50"] > df["SMA_200"]).astype(int)

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
    # Rolling calculations (SMA_200, RSI, etc.) produce NaN for
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


def _calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate the Average Directional Index (ADX).

    ADX measures trend strength on a 0-100 scale.
    It uses the Directional Movement (DM) system:
      +DI measures upward movement strength
      -DI measures downward movement strength
      ADX = smoothed average of abs(+DI - -DI) / (+DI + -DI)

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with High, Low, Close columns.
    period : int
        Lookback period. Default is 14.

    Returns
    -------
    pd.Series
        ADX values (0-100).
    """
    # Calculate +DM and -DM
    high_diff = df["High"].diff()
    low_diff = -df["Low"].diff()  # Negative because low going down is positive DM

    plus_dm = pd.Series(0.0, index=df.index)
    minus_dm = pd.Series(0.0, index=df.index)

    # +DM: when high moved up more than low moved down
    plus_dm[(high_diff > low_diff) & (high_diff > 0)] = high_diff
    # -DM: when low moved down more than high moved up
    minus_dm[(low_diff > high_diff) & (low_diff > 0)] = low_diff

    # Calculate True Range
    prev_close = df["Close"].shift(1)
    tr1 = df["High"] - df["Low"]
    tr2 = (df["High"] - prev_close).abs()
    tr3 = (df["Low"] - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Smoothed averages (Wilder's smoothing)
    atr = true_range.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / (atr + 1e-10))
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / (atr + 1e-10))

    # DX and ADX
    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di + 1e-10))
    adx = dx.rolling(window=period).mean()

    return adx


def detect_support_resistance(df: pd.DataFrame, window: int = 20, num_levels: int = 3) -> dict:
    """
    Detect key support and resistance price levels.

    Uses rolling window local minima/maxima to identify price
    levels where the stock has historically reversed direction.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with at least a 'Close' column.
    window : int
        Rolling window size for finding local extremes.
    num_levels : int
        Number of support/resistance levels to return.

    Returns
    -------
    dict
        Keys: 'support_levels', 'resistance_levels', 'current_price'
        Each level is a float price.
    """
    close = df["Close"]
    current_price = float(close.iloc[-1])

    # Find local minima (support) and maxima (resistance)
    local_min = close[(close.shift(window) > close) & (close.shift(-window) > close)]
    local_max = close[(close.shift(window) < close) & (close.shift(-window) < close)]

    # Get unique levels, sorted by proximity to current price
    support_candidates = sorted(
        [float(p) for p in local_min.values if p < current_price],
        key=lambda x: abs(x - current_price),
    )[:num_levels]

    resistance_candidates = sorted(
        [float(p) for p in local_max.values if p > current_price],
        key=lambda x: abs(x - current_price),
    )[:num_levels]

    # Sort support descending (closest first), resistance ascending
    support_candidates.sort(reverse=True)
    resistance_candidates.sort()

    return {
        "support_levels": support_candidates,
        "resistance_levels": resistance_candidates,
        "current_price": current_price,
    }


def get_technical_summary(df: pd.DataFrame, ticker: str = "") -> dict:
    """
    Generate a comprehensive technical analysis summary.

    This is designed for AI agents — it provides all technical
    indicators in a structured format that can be included in
    an LLM prompt for interpretation.

    Parameters
    ----------
    df : pd.DataFrame
        Feature-engineered DataFrame (output of add_features).
    ticker : str
        Stock symbol for display.

    Returns
    -------
    dict
        Complete technical analysis data package including:
        - Current indicator values
        - Signal interpretations
        - Trend classification
        - Support/resistance levels
    """
    if df.empty:
        return {"error": "No data available"}

    latest = df.iloc[-1]
    current_price = float(latest["Close"])

    # --- Trend Analysis ---
    sma_50 = float(latest["SMA_50"]) if "SMA_50" in df.columns else None
    sma_200 = float(latest["SMA_200"]) if "SMA_200" in df.columns else None

    if sma_50 and sma_200:
        if sma_50 > sma_200 and current_price > sma_50:
            trend = "Strong Uptrend"
        elif sma_50 > sma_200:
            trend = "Uptrend (weakening)"
        elif sma_50 < sma_200 and current_price < sma_50:
            trend = "Strong Downtrend"
        elif sma_50 < sma_200:
            trend = "Downtrend (weakening)"
        else:
            trend = "Sideways / Transitioning"
    else:
        trend = "Insufficient data for trend"

    # --- RSI Interpretation ---
    rsi = float(latest["RSI"])
    if rsi > 70:
        rsi_signal = "Overbought"
    elif rsi > 60:
        rsi_signal = "Bullish"
    elif rsi < 30:
        rsi_signal = "Oversold"
    elif rsi < 40:
        rsi_signal = "Bearish"
    else:
        rsi_signal = "Neutral"

    # --- MACD Interpretation ---
    macd_signal = "N/A"
    if "MACD" in df.columns and "MACD_Signal" in df.columns:
        macd_val = float(latest["MACD"])
        macd_sig = float(latest["MACD_Signal"])
        macd_hist = float(latest["MACD_Histogram"])

        if macd_val > macd_sig and macd_hist > 0:
            macd_signal = "Bullish (MACD above signal, positive histogram)"
        elif macd_val > macd_sig:
            macd_signal = "Bullish (MACD above signal)"
        elif macd_val < macd_sig and macd_hist < 0:
            macd_signal = "Bearish (MACD below signal, negative histogram)"
        elif macd_val < macd_sig:
            macd_signal = "Bearish (MACD below signal)"
        else:
            macd_signal = "Neutral (MACD at signal line)"

    # --- Bollinger Bands Interpretation ---
    bb_signal = "N/A"
    if "BB_Percent_B" in df.columns:
        pct_b = float(latest["BB_Percent_B"])
        if pct_b > 1.0:
            bb_signal = "Above upper band (overbought / breakout)"
        elif pct_b > 0.8:
            bb_signal = "Near upper band (potentially overbought)"
        elif pct_b < 0.0:
            bb_signal = "Below lower band (oversold / breakdown)"
        elif pct_b < 0.2:
            bb_signal = "Near lower band (potentially oversold)"
        else:
            bb_signal = "Within bands (normal)"

    # --- ADX Interpretation ---
    adx_signal = "N/A"
    if "ADX" in df.columns:
        adx_val = float(latest["ADX"])
        if adx_val > 40:
            adx_signal = f"Very strong trend ({adx_val:.1f})"
        elif adx_val > 25:
            adx_signal = f"Strong trend ({adx_val:.1f})"
        elif adx_val > 20:
            adx_signal = f"Developing trend ({adx_val:.1f})"
        else:
            adx_signal = f"Weak/no trend ({adx_val:.1f}) — range-bound"

    # --- Stochastic Interpretation ---
    stoch_signal = "N/A"
    if "Stochastic_K" in df.columns:
        stoch_k = float(latest["Stochastic_K"])
        if stoch_k > 80:
            stoch_signal = f"Overbought ({stoch_k:.1f})"
        elif stoch_k < 20:
            stoch_signal = f"Oversold ({stoch_k:.1f})"
        else:
            stoch_signal = f"Neutral ({stoch_k:.1f})"

    # --- Support & Resistance ---
    sr_levels = detect_support_resistance(df)

    # --- Volatility ---
    volatility_10d = float(latest["Volatility_10"]) * 100
    atr = float(latest["ATR_14"]) if "ATR_14" in df.columns else None

    summary = {
        "ticker": ticker,
        "current_price": round(current_price, 2),
        "trend": {
            "classification": trend,
            "sma_50": round(sma_50, 2) if sma_50 else None,
            "sma_200": round(sma_200, 2) if sma_200 else None,
            "sma_20": round(float(latest["SMA_20"]), 2),
            "golden_cross": bool(latest.get("SMA50_above_SMA200", 0)),
        },
        "momentum": {
            "rsi": round(rsi, 2),
            "rsi_signal": rsi_signal,
            "macd": round(float(latest.get("MACD", 0)), 4),
            "macd_signal_line": round(float(latest.get("MACD_Signal", 0)), 4),
            "macd_histogram": round(float(latest.get("MACD_Histogram", 0)), 4),
            "macd_interpretation": macd_signal,
            "stochastic_k": round(float(latest.get("Stochastic_K", 0)), 2),
            "stochastic_d": round(float(latest.get("Stochastic_D", 0)), 2),
            "stochastic_signal": stoch_signal,
        },
        "volatility": {
            "volatility_10d_pct": round(volatility_10d, 2),
            "atr_14": round(atr, 2) if atr else None,
            "bb_upper": round(float(latest.get("BB_Upper", 0)), 2),
            "bb_lower": round(float(latest.get("BB_Lower", 0)), 2),
            "bb_width": round(float(latest.get("BB_Width", 0)), 4),
            "bb_percent_b": round(float(latest.get("BB_Percent_B", 0)), 4),
            "bb_signal": bb_signal,
        },
        "trend_strength": {
            "adx": round(float(latest.get("ADX", 0)), 2),
            "adx_signal": adx_signal,
        },
        "volume": {
            "current_volume": int(latest["Volume"]),
            "volume_change_pct": round(float(latest["Volume_Change"]) * 100, 2),
            "obv_trend": "Rising" if float(latest.get("OBV", 0)) > float(latest.get("OBV_SMA_20", 0)) else "Falling",
        },
        "support_resistance": sr_levels,
        "daily_return_pct": round(float(latest["Daily_Return"]) * 100, 2),
    }

    return summary


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

    # Step 1: Fetch raw data (need 2+ years for SMA_200)
    raw_data = get_stock_data("AAPL", period_years=2)

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

    # Test advanced features
    print(f"\n--- Technical Summary ---")
    tech = get_technical_summary(featured_data, "AAPL")
    print(f"  Trend: {tech['trend']['classification']}")
    print(f"  RSI:   {tech['momentum']['rsi']} ({tech['momentum']['rsi_signal']})")
    print(f"  MACD:  {tech['momentum']['macd_interpretation']}")
    print(f"  ADX:   {tech['trend_strength']['adx_signal']}")
    print(f"  BB:    {tech['volatility']['bb_signal']}")
    print(f"  Support:    {tech['support_resistance']['support_levels']}")
    print(f"  Resistance: {tech['support_resistance']['resistance_levels']}")
