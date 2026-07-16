# ============================================================
# src/__init__.py
# ============================================================
# This file makes the 'src' directory a Python PACKAGE.
#
# What is a Python package?
# -------------------------
# When Python sees a folder with __init__.py inside it,
# it treats that folder as a "package" — a bundle of modules
# you can import from.
#
# Without this file:
#   from src.data_fetcher import get_stock_data  ← ERROR ❌
#
# With this file:
#   from src.data_fetcher import get_stock_data  ← Works ✅
#
# Modules in this package:
#   - data_fetcher:     Stock price data from Yahoo Finance
#   - preprocessor:     Data cleaning and validation
#   - feature_engineer: Technical indicators and ML features
#   - model:            ML model training and prediction
#   - news_analyzer:    FinBERT sentiment analysis (legacy)
#   - financial_data:   Financial statements and ratios
#   - macro_data:       Macroeconomic indicators
#   - news_collector:   Multi-source news aggregation
# ============================================================

