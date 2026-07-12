# ============================================================
# src/preprocessor.py — Data Preprocessing Layer
# ============================================================
# Responsibility: Clean and validate raw stock data.
#
# This module transforms messy, real-world data into a clean
# DataFrame that the ML model can safely learn from.
#
# Pipeline steps:
#   1. Remove duplicate rows
#   2. Handle missing values (forward fill)
#   3. Validate data types
#   4. Remove rows with zero/negative prices (bad data)
#   5. Generate a data quality report
# ============================================================

import pandas as pd
import numpy as np


def preprocess_stock_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate raw stock data for ML readiness.

    This function applies a series of cleaning steps (a "pipeline")
    to the raw DataFrame returned by data_fetcher.get_stock_data().

    Parameters
    ----------
    df : pd.DataFrame
        Raw stock data with columns: Open, High, Low, Close, Volume.
        The index should be DatetimeIndex.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame, ready for feature engineering.

    Raises
    ------
    ValueError
        If the DataFrame is empty or missing required columns.
    """
    # --- Step 0: Make a copy ---
    # IMPORTANT: We work on a copy, not the original.
    # Why? In Python, DataFrames are passed by reference.
    # If we modify 'df' directly, the caller's original data
    # gets modified too — a sneaky bug called a "side effect."
    # Professional code avoids side effects.
    df = df.copy()

    # --- Step 1: Validate required columns ---
    # Before doing anything, check that the data has the columns
    # we expect. This is called "defensive programming."
    required_columns = ["Open", "High", "Low", "Close", "Volume"]
    missing_cols = [col for col in required_columns if col not in df.columns]

    if missing_cols:
        raise ValueError(
            f"Missing required columns: {missing_cols}. "
            f"Available columns: {list(df.columns)}"
        )

    # Keep only the columns we need (drop any extras)
    df = df[required_columns]

    # --- Step 2: Print initial data quality report ---
    print("\n" + "=" * 50)
    print("DATA QUALITY REPORT (Before Cleaning)")
    print("=" * 50)
    print(f"  Total rows:        {len(df)}")
    print(f"  Date range:        {df.index[0].date()} to {df.index[-1].date()}")
    print(f"  Duplicate rows:    {df.duplicated().sum()}")
    print(f"  Missing values:")
    for col in required_columns:
        missing_count = df[col].isna().sum()
        # .isna() returns True/False for each cell; .sum() counts the Trues
        if missing_count > 0:
            print(f"    {col}: {missing_count} missing")
    if df.isna().sum().sum() == 0:
        print("    None found!")
    print("=" * 50)

    # --- Step 3: Remove duplicate rows ---
    # Sometimes data sources send the same trading day twice.
    # keep='first' means: if there are duplicates, keep the
    # first occurrence and delete the rest.
    rows_before = len(df)
    df = df[~df.index.duplicated(keep="first")]
    rows_removed = rows_before - len(df)
    if rows_removed > 0:
        print(f"  [CLEAN] Removed {rows_removed} duplicate rows")

    # --- Step 4: Handle missing values (Forward Fill) ---
    # Forward fill: replace NaN with the most recent valid value.
    #
    # Before:  [150, NaN, NaN, 155]
    # After:   [150, 150, 150, 155]
    #
    # Why forward fill for stocks?
    # If the market was closed, the last known price is the
    # best estimate — the price didn't change.
    missing_before = df.isna().sum().sum()
    df = df.ffill()  # ffill = "forward fill"

    # After forward fill, there might still be NaN at the very
    # beginning (if the FIRST row had missing data — nothing
    # before it to fill from). We use backward fill for those.
    df = df.bfill()  # bfill = "backward fill"

    missing_after = df.isna().sum().sum()
    if missing_before > 0:
        print(f"  [CLEAN] Filled {missing_before - missing_after} missing values")

    # --- Step 5: Remove rows with invalid prices ---
    # Stock prices should NEVER be zero or negative.
    # If they are, it's a data error from the source.
    price_columns = ["Open", "High", "Low", "Close"]
    invalid_mask = (df[price_columns] <= 0).any(axis=1)
    # .any(axis=1) checks: "is ANY price column <= 0 in this row?"
    invalid_count = invalid_mask.sum()

    if invalid_count > 0:
        df = df[~invalid_mask]  # Keep only rows where the mask is False
        print(f"  [CLEAN] Removed {invalid_count} rows with zero/negative prices")

    # --- Step 6: Ensure correct data types ---
    # Sometimes values come in as strings or integers.
    # We want all prices as float64 (decimal numbers) and
    # Volume as int64 (whole numbers).
    for col in price_columns:
        df[col] = df[col].astype(np.float64)
    df["Volume"] = df["Volume"].astype(np.int64)

    # --- Step 7: Ensure the index is a proper DatetimeIndex ---
    # This lets us do time-based operations like "get all Mondays"
    # or "resample to weekly data."
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df.index.name = "Date"

    # --- Step 8: Sort by date (oldest first) ---
    df = df.sort_index(ascending=True)

    # --- Step 9: Final quality report ---
    print("\n" + "=" * 50)
    print("DATA QUALITY REPORT (After Cleaning)")
    print("=" * 50)
    print(f"  Total rows:        {len(df)}")
    print(f"  Missing values:    {df.isna().sum().sum()}")
    print(f"  Date range:        {df.index[0].date()} to {df.index[-1].date()}")
    print(f"  Price range:       ${df['Close'].min():.2f} - ${df['Close'].max():.2f}")
    print("=" * 50 + "\n")

    return df


# ============================================================
# Test the preprocessor independently
# ============================================================
if __name__ == "__main__":
    from data_fetcher import get_stock_data

    # Fetch raw data
    raw_data = get_stock_data("AAPL", period_years=1)
    print(f"\nRaw data shape: {raw_data.shape}")
    print(f"Raw data types:\n{raw_data.dtypes}\n")

    # Clean it
    clean_data = preprocess_stock_data(raw_data)
    print(f"Clean data shape: {clean_data.shape}")
    print(f"\nFirst 5 rows of clean data:")
    print(clean_data.head())
    print(f"\nClean data types:\n{clean_data.dtypes}")
