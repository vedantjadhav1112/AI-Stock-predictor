# ============================================================
# src/macro_data.py — Macroeconomic Data Fetcher
# ============================================================
# Responsibility: Fetch and organize macroeconomic data that
# contextualizes a company within the broader economy.
#
# Data sources:
#   1. FRED API (Federal Reserve) — interest rates, inflation,
#      GDP, unemployment, yield curve
#   2. yfinance — market indices, sector ETFs, VIX
#
# If FRED_API_KEY is not set, falls back to yfinance-only data.
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from cachetools import TTLCache
from typing import Optional

# In-memory cache: max 20 entries, 1-hour TTL
_macro_cache = TTLCache(maxsize=20, ttl=3600)

# Try to import fredapi (optional dependency)
try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False
    print("[MACRO] Warning: fredapi not installed. Install with: pip install fredapi")


def _get_fred_client() -> Optional[object]:
    """Get a FRED API client if key is configured."""
    if not FRED_AVAILABLE:
        return None
    try:
        from config import settings
        if settings.has_fred_key:
            return Fred(api_key=settings.FRED_API_KEY)
    except Exception:
        pass
    return None


def get_interest_rates() -> dict:
    """
    Fetch current interest rate data.

    Gets the Federal Funds Rate, 10-Year Treasury Yield,
    2-Year Treasury Yield, and calculates the yield curve spread.

    Returns
    -------
    dict
        Keys: 'fed_funds_rate', 'treasury_10y', 'treasury_2y',
              'yield_spread' (10y - 2y), 'yield_curve_status'
    """
    cache_key = "interest_rates"
    if cache_key in _macro_cache:
        return _macro_cache[cache_key]

    print("[MACRO] Fetching interest rate data...")

    rates = {
        "fed_funds_rate": None,
        "treasury_10y": None,
        "treasury_2y": None,
        "yield_spread": None,
        "yield_curve_status": "Unknown",
    }

    fred = _get_fred_client()

    if fred:
        try:
            # FRED series IDs for key rates
            ffr = fred.get_series("FEDFUNDS", observation_start=datetime.now() - timedelta(days=90))
            if not ffr.empty:
                rates["fed_funds_rate"] = round(float(ffr.iloc[-1]), 2)

            t10y = fred.get_series("DGS10", observation_start=datetime.now() - timedelta(days=30))
            if not t10y.empty:
                rates["treasury_10y"] = round(float(t10y.dropna().iloc[-1]), 2)

            t2y = fred.get_series("DGS2", observation_start=datetime.now() - timedelta(days=30))
            if not t2y.empty:
                rates["treasury_2y"] = round(float(t2y.dropna().iloc[-1]), 2)

        except Exception as e:
            print(f"[MACRO] Warning: FRED rate fetch failed: {e}")

    # Fallback: use Treasury ETFs from yfinance
    if rates["treasury_10y"] is None:
        try:
            # ^TNX = 10-Year Treasury Yield Index
            tnx = yf.Ticker("^TNX")
            hist = tnx.history(period="5d")
            if not hist.empty:
                rates["treasury_10y"] = round(float(hist["Close"].iloc[-1]), 2)
        except Exception:
            pass

    if rates["treasury_2y"] is None:
        try:
            # ^IRX = 13-Week Treasury Bill
            irx = yf.Ticker("^IRX")
            hist = irx.history(period="5d")
            if not hist.empty:
                rates["treasury_2y"] = round(float(hist["Close"].iloc[-1]), 2)
        except Exception:
            pass

    # Calculate yield spread
    if rates["treasury_10y"] is not None and rates["treasury_2y"] is not None:
        spread = rates["treasury_10y"] - rates["treasury_2y"]
        rates["yield_spread"] = round(spread, 2)
        if spread < 0:
            rates["yield_curve_status"] = "Inverted (recession signal)"
        elif spread < 0.5:
            rates["yield_curve_status"] = "Flat (slowing economy)"
        else:
            rates["yield_curve_status"] = "Normal (healthy economy)"

    _macro_cache[cache_key] = rates
    return rates


def get_inflation_data() -> dict:
    """
    Fetch inflation-related economic indicators.

    Returns
    -------
    dict
        Keys: 'cpi_yoy' (Consumer Price Index year-over-year change),
              'pce_yoy' (Personal Consumption Expenditures),
              'inflation_trend' (accelerating/decelerating/stable)
    """
    cache_key = "inflation"
    if cache_key in _macro_cache:
        return _macro_cache[cache_key]

    print("[MACRO] Fetching inflation data...")

    inflation = {
        "cpi_yoy": None,
        "cpi_latest": None,
        "inflation_trend": "Unknown",
    }

    fred = _get_fred_client()

    if fred:
        try:
            # CPI Year-over-Year change
            cpi = fred.get_series("CPIAUCSL", observation_start=datetime.now() - timedelta(days=400))
            if not cpi.empty and len(cpi) >= 13:
                latest = float(cpi.iloc[-1])
                year_ago = float(cpi.iloc[-13])  # ~12 months ago
                yoy = ((latest - year_ago) / year_ago) * 100
                inflation["cpi_yoy"] = round(yoy, 2)
                inflation["cpi_latest"] = round(latest, 2)

                # Trend: compare recent 3-month average to prior 3-month
                if len(cpi) >= 7:
                    recent_avg = cpi.iloc[-3:].mean()
                    prior_avg = cpi.iloc[-6:-3].mean()
                    if recent_avg > prior_avg * 1.001:
                        inflation["inflation_trend"] = "Accelerating"
                    elif recent_avg < prior_avg * 0.999:
                        inflation["inflation_trend"] = "Decelerating"
                    else:
                        inflation["inflation_trend"] = "Stable"

        except Exception as e:
            print(f"[MACRO] Warning: FRED inflation fetch failed: {e}")

    _macro_cache[cache_key] = inflation
    return inflation


def get_economic_indicators() -> dict:
    """
    Fetch key economic health indicators.

    Returns
    -------
    dict
        Keys: 'gdp_growth' (latest GDP growth rate),
              'unemployment_rate', 'consumer_sentiment'
    """
    cache_key = "economic_indicators"
    if cache_key in _macro_cache:
        return _macro_cache[cache_key]

    print("[MACRO] Fetching economic indicators...")

    indicators = {
        "gdp_growth_annualized": None,
        "unemployment_rate": None,
        "consumer_sentiment": None,
    }

    fred = _get_fred_client()

    if fred:
        try:
            # GDP growth (annualized quarterly rate)
            gdp = fred.get_series("A191RL1Q225SBEA", observation_start=datetime.now() - timedelta(days=365))
            if not gdp.empty:
                indicators["gdp_growth_annualized"] = round(float(gdp.iloc[-1]), 2)

            # Unemployment rate
            unrate = fred.get_series("UNRATE", observation_start=datetime.now() - timedelta(days=90))
            if not unrate.empty:
                indicators["unemployment_rate"] = round(float(unrate.iloc[-1]), 1)

            # University of Michigan Consumer Sentiment
            umcsent = fred.get_series("UMCSENT", observation_start=datetime.now() - timedelta(days=90))
            if not umcsent.empty:
                indicators["consumer_sentiment"] = round(float(umcsent.iloc[-1]), 1)

        except Exception as e:
            print(f"[MACRO] Warning: FRED economic indicators failed: {e}")

    _macro_cache[cache_key] = indicators
    return indicators


def get_market_overview() -> dict:
    """
    Fetch current market conditions using major indices and VIX.

    Returns
    -------
    dict
        Keys: 'sp500', 'nasdaq', 'dow', 'vix', 'sector_performance',
              'market_regime' (risk-on/risk-off/neutral)
    """
    cache_key = "market_overview"
    if cache_key in _macro_cache:
        return _macro_cache[cache_key]

    print("[MACRO] Fetching market overview...")

    overview = {
        "indices": {},
        "vix": None,
        "vix_level": "Unknown",
        "sector_performance": {},
        "market_regime": "Unknown",
    }

    # --- Major Indices ---
    index_tickers = {
        "S&P 500": "^GSPC",
        "Nasdaq": "^IXIC",
        "Dow Jones": "^DJI",
        "Russell 2000": "^RUT",
    }

    for name, symbol in index_tickers.items():
        try:
            idx = yf.Ticker(symbol)
            hist = idx.history(period="1mo")
            if not hist.empty:
                current = float(hist["Close"].iloc[-1])
                month_ago = float(hist["Close"].iloc[0])
                pct_change = ((current - month_ago) / month_ago) * 100
                overview["indices"][name] = {
                    "value": round(current, 2),
                    "1m_change_pct": round(pct_change, 2),
                }
        except Exception as e:
            print(f"[MACRO] Warning: Could not fetch {name}: {e}")

    # --- VIX (Volatility Index) ---
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="5d")
        if not hist.empty:
            vix_value = float(hist["Close"].iloc[-1])
            overview["vix"] = round(vix_value, 2)

            if vix_value < 15:
                overview["vix_level"] = "Low (complacency)"
            elif vix_value < 20:
                overview["vix_level"] = "Normal"
            elif vix_value < 30:
                overview["vix_level"] = "Elevated (fear)"
            else:
                overview["vix_level"] = "High (panic)"
    except Exception as e:
        print(f"[MACRO] Warning: Could not fetch VIX: {e}")

    # --- Sector ETF Performance (1 month) ---
    sector_etfs = {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Consumer Discretionary": "XLY",
        "Consumer Staples": "XLP",
        "Energy": "XLE",
        "Industrials": "XLI",
        "Materials": "XLB",
        "Utilities": "XLU",
        "Real Estate": "XLRE",
        "Communication Services": "XLC",
    }

    for sector, etf in sector_etfs.items():
        try:
            s = yf.Ticker(etf)
            hist = s.history(period="1mo")
            if not hist.empty and len(hist) >= 2:
                current = float(hist["Close"].iloc[-1])
                start = float(hist["Close"].iloc[0])
                pct = ((current - start) / start) * 100
                overview["sector_performance"][sector] = round(pct, 2)
        except Exception:
            pass

    # --- Determine Market Regime ---
    vix_val = overview.get("vix", 20)
    sp500_change = overview.get("indices", {}).get("S&P 500", {}).get("1m_change_pct", 0)

    if vix_val and sp500_change:
        if vix_val < 18 and sp500_change > 2:
            overview["market_regime"] = "Risk-On (bullish environment)"
        elif vix_val > 25 or sp500_change < -5:
            overview["market_regime"] = "Risk-Off (defensive environment)"
        else:
            overview["market_regime"] = "Neutral (mixed signals)"

    _macro_cache[cache_key] = overview
    return overview


def get_full_macro_analysis() -> dict:
    """
    Run the complete macroeconomic analysis.

    Combines interest rates, inflation, economic indicators,
    and market overview into a single analysis package.

    Returns
    -------
    dict
        Complete macro context for AI agents.
    """
    print("\n[MACRO] Starting full macroeconomic analysis...")

    result = {
        "interest_rates": get_interest_rates(),
        "inflation": get_inflation_data(),
        "economic_indicators": get_economic_indicators(),
        "market_overview": get_market_overview(),
        "timestamp": datetime.now().isoformat(),
    }

    # Generate a human-readable summary
    rates = result["interest_rates"]
    infl = result["inflation"]
    econ = result["economic_indicators"]
    market = result["market_overview"]

    summary_parts = []

    if rates.get("treasury_10y"):
        summary_parts.append(f"10Y Treasury at {rates['treasury_10y']}%")
    if rates.get("yield_curve_status") and rates["yield_curve_status"] != "Unknown":
        summary_parts.append(f"Yield curve: {rates['yield_curve_status']}")
    if infl.get("cpi_yoy"):
        summary_parts.append(f"CPI inflation at {infl['cpi_yoy']}% YoY ({infl.get('inflation_trend', '')})")
    if econ.get("unemployment_rate"):
        summary_parts.append(f"Unemployment at {econ['unemployment_rate']}%")
    if market.get("vix"):
        summary_parts.append(f"VIX at {market['vix']} ({market.get('vix_level', '')})")
    if market.get("market_regime") and market["market_regime"] != "Unknown":
        summary_parts.append(f"Market regime: {market['market_regime']}")

    result["summary"] = ". ".join(summary_parts) if summary_parts else "Macro data unavailable."

    print(f"[MACRO] Macro analysis complete")
    return result


# ============================================================
# Test the macro data module
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("MACROECONOMIC DATA TEST")
    print("=" * 60)

    result = get_full_macro_analysis()

    print(f"\n--- Interest Rates ---")
    for k, v in result["interest_rates"].items():
        print(f"  {k}: {v}")

    print(f"\n--- Inflation ---")
    for k, v in result["inflation"].items():
        print(f"  {k}: {v}")

    print(f"\n--- Economic Indicators ---")
    for k, v in result["economic_indicators"].items():
        print(f"  {k}: {v}")

    print(f"\n--- Market Overview ---")
    print(f"  VIX: {result['market_overview']['vix']} ({result['market_overview']['vix_level']})")
    print(f"  Market Regime: {result['market_overview']['market_regime']}")

    print(f"\n--- Indices ---")
    for name, data in result["market_overview"]["indices"].items():
        print(f"  {name}: {data['value']:,.2f} ({data['1m_change_pct']:+.2f}% 1M)")

    print(f"\n--- Sector Performance (1 Month) ---")
    sorted_sectors = sorted(
        result["market_overview"]["sector_performance"].items(),
        key=lambda x: x[1], reverse=True
    )
    for sector, pct in sorted_sectors:
        print(f"  {sector:30s}: {pct:+.2f}%")

    print(f"\n--- Summary ---")
    print(f"  {result['summary']}")
