# ============================================================
# src/financial_data.py — Financial Statements & Ratios
# ============================================================
# Responsibility: Fetch and analyze financial statements.
#
# This module:
#   1. Pulls income statement, balance sheet, cash flow
#   2. Calculates key financial ratios (P/E, ROE, margins, etc.)
#   3. Computes growth rates (revenue, earnings, FCF)
#   4. Identifies peer companies for comparison
#   5. Returns everything in a structured format for AI agents
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
from cachetools import TTLCache
from typing import Optional

# In-memory cache: max 50 tickers, 6-hour TTL
_financials_cache = TTLCache(maxsize=50, ttl=21600)


def get_financial_statements(ticker: str) -> dict:
    """
    Fetch all financial statements for a company.

    Pulls annual and quarterly income statements, balance sheets,
    and cash flow statements from Yahoo Finance via yfinance.

    Parameters
    ----------
    ticker : str
        Stock symbol (e.g., "AAPL").

    Returns
    -------
    dict
        Keys: 'income_stmt', 'balance_sheet', 'cashflow',
              'quarterly_income', 'quarterly_balance', 'quarterly_cashflow'
        Each value is a pandas DataFrame (columns = fiscal dates, rows = line items).
    """
    cache_key = f"statements_{ticker.upper()}"
    if cache_key in _financials_cache:
        print(f"[FINANCIALS] Cache hit for {ticker}")
        return _financials_cache[cache_key]

    print(f"[FINANCIALS] Fetching financial statements for {ticker}...")

    stock = yf.Ticker(ticker)

    statements = {}

    # --- Annual statements ---
    try:
        statements["income_stmt"] = stock.income_stmt
    except Exception as e:
        print(f"[FINANCIALS] Warning: Could not fetch income statement: {e}")
        statements["income_stmt"] = pd.DataFrame()

    try:
        statements["balance_sheet"] = stock.balance_sheet
    except Exception as e:
        print(f"[FINANCIALS] Warning: Could not fetch balance sheet: {e}")
        statements["balance_sheet"] = pd.DataFrame()

    try:
        statements["cashflow"] = stock.cashflow
    except Exception as e:
        print(f"[FINANCIALS] Warning: Could not fetch cash flow: {e}")
        statements["cashflow"] = pd.DataFrame()

    # --- Quarterly statements ---
    try:
        statements["quarterly_income"] = stock.quarterly_income_stmt
    except Exception as e:
        print(f"[FINANCIALS] Warning: Could not fetch quarterly income: {e}")
        statements["quarterly_income"] = pd.DataFrame()

    try:
        statements["quarterly_balance"] = stock.quarterly_balance_sheet
    except Exception as e:
        print(f"[FINANCIALS] Warning: Could not fetch quarterly balance: {e}")
        statements["quarterly_balance"] = pd.DataFrame()

    try:
        statements["quarterly_cashflow"] = stock.quarterly_cashflow
    except Exception as e:
        print(f"[FINANCIALS] Warning: Could not fetch quarterly cash flow: {e}")
        statements["quarterly_cashflow"] = pd.DataFrame()

    _financials_cache[cache_key] = statements
    print(f"[FINANCIALS] Successfully fetched statements for {ticker}")
    return statements


def _safe_get(df: pd.DataFrame, row_label: str, col_idx: int = 0) -> Optional[float]:
    """
    Safely extract a value from a financial statement DataFrame.

    Financial statements have line items as rows and fiscal periods
    as columns. This helper handles missing rows/columns gracefully.

    Parameters
    ----------
    df : pd.DataFrame
        A financial statement DataFrame.
    row_label : str
        The line item name (e.g., "Total Revenue").
    col_idx : int
        Which fiscal period (0 = most recent, 1 = previous year, etc.).

    Returns
    -------
    float or None
        The value, or None if not found.
    """
    try:
        if df.empty or row_label not in df.index:
            return None
        if col_idx >= len(df.columns):
            return None
        val = df.loc[row_label].iloc[col_idx]
        if pd.isna(val):
            return None
        return float(val)
    except Exception:
        return None


def _safe_divide(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """Safe division that handles None and zero denominators."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def calculate_financial_ratios(ticker: str) -> dict:
    """
    Calculate key financial ratios from financial statements.

    Computes profitability, liquidity, leverage, efficiency, and
    valuation ratios that institutional analysts use.

    Parameters
    ----------
    ticker : str
        Stock symbol.

    Returns
    -------
    dict
        Organized by category:
        - 'profitability': gross_margin, operating_margin, net_margin, roe, roa
        - 'liquidity': current_ratio, quick_ratio
        - 'leverage': debt_to_equity, interest_coverage
        - 'valuation': pe_ratio, pb_ratio, ps_ratio, ev_to_ebitda, peg_ratio
        - 'efficiency': asset_turnover, inventory_turnover
        - 'cash_flow': fcf_yield, operating_cf_to_revenue
    """
    cache_key = f"ratios_{ticker.upper()}"
    if cache_key in _financials_cache:
        return _financials_cache[cache_key]

    print(f"[FINANCIALS] Calculating financial ratios for {ticker}...")

    statements = get_financial_statements(ticker)
    income = statements["income_stmt"]
    balance = statements["balance_sheet"]
    cashflow = statements["cashflow"]

    # Also get market data for valuation ratios
    stock = yf.Ticker(ticker)
    try:
        info = stock.info or {}
    except Exception:
        info = {}

    # --- Extract key line items (most recent annual) ---
    revenue = _safe_get(income, "Total Revenue", 0)
    gross_profit = _safe_get(income, "Gross Profit", 0)
    operating_income = _safe_get(income, "Operating Income", 0)
    net_income = _safe_get(income, "Net Income", 0)
    ebitda = _safe_get(income, "EBITDA", 0)
    interest_expense = _safe_get(income, "Interest Expense", 0)

    total_assets = _safe_get(balance, "Total Assets", 0)
    total_liabilities = _safe_get(balance, "Total Liabilities Net Minority Interest", 0)
    stockholders_equity = _safe_get(balance, "Stockholders Equity", 0)
    current_assets = _safe_get(balance, "Current Assets", 0)
    current_liabilities = _safe_get(balance, "Current Liabilities", 0)
    inventory = _safe_get(balance, "Inventory", 0)
    total_debt = _safe_get(balance, "Total Debt", 0)

    operating_cf = _safe_get(cashflow, "Operating Cash Flow", 0)
    capex = _safe_get(cashflow, "Capital Expenditure", 0)

    # Market data
    market_cap = info.get("marketCap")
    share_price = info.get("currentPrice") or info.get("regularMarketPrice")
    shares_outstanding = info.get("sharesOutstanding")
    enterprise_value = info.get("enterpriseValue")
    book_value_per_share = info.get("bookValue")
    trailing_pe = info.get("trailingPE")
    forward_pe = info.get("forwardPE")
    peg_ratio = info.get("pegRatio")

    # --- Calculate ratios ---

    # Profitability
    gross_margin = _safe_divide(gross_profit, revenue)
    operating_margin = _safe_divide(operating_income, revenue)
    net_margin = _safe_divide(net_income, revenue)
    roe = _safe_divide(net_income, stockholders_equity)
    roa = _safe_divide(net_income, total_assets)

    # Liquidity
    current_ratio = _safe_divide(current_assets, current_liabilities)
    quick_ratio = None
    if current_assets is not None and current_liabilities is not None:
        inv = inventory if inventory is not None else 0
        quick_ratio = _safe_divide(current_assets - inv, current_liabilities)

    # Leverage
    debt_to_equity = _safe_divide(total_debt, stockholders_equity)
    interest_coverage = None
    if operating_income is not None and interest_expense is not None and interest_expense != 0:
        interest_coverage = abs(operating_income / interest_expense)

    # Valuation (from market data)
    pe_ratio = trailing_pe
    pb_ratio = None
    if share_price and book_value_per_share and book_value_per_share > 0:
        pb_ratio = share_price / book_value_per_share
    ps_ratio = _safe_divide(market_cap, revenue) if market_cap else None
    ev_to_ebitda = _safe_divide(enterprise_value, ebitda) if enterprise_value else None

    # Efficiency
    asset_turnover = _safe_divide(revenue, total_assets)

    # Cash Flow
    fcf = None
    if operating_cf is not None and capex is not None:
        fcf = operating_cf + capex  # capex is typically negative
    fcf_yield = _safe_divide(fcf, market_cap) if market_cap else None
    operating_cf_to_revenue = _safe_divide(operating_cf, revenue)

    ratios = {
        "profitability": {
            "gross_margin": _round(gross_margin),
            "operating_margin": _round(operating_margin),
            "net_margin": _round(net_margin),
            "roe": _round(roe),
            "roa": _round(roa),
        },
        "liquidity": {
            "current_ratio": _round(current_ratio),
            "quick_ratio": _round(quick_ratio),
        },
        "leverage": {
            "debt_to_equity": _round(debt_to_equity),
            "interest_coverage": _round(interest_coverage),
            "total_debt": total_debt,
        },
        "valuation": {
            "pe_ratio": _round(pe_ratio),
            "forward_pe": _round(forward_pe),
            "pb_ratio": _round(pb_ratio),
            "ps_ratio": _round(ps_ratio),
            "ev_to_ebitda": _round(ev_to_ebitda),
            "peg_ratio": _round(peg_ratio),
            "market_cap": market_cap,
            "enterprise_value": enterprise_value,
        },
        "efficiency": {
            "asset_turnover": _round(asset_turnover),
        },
        "cash_flow": {
            "free_cash_flow": fcf,
            "fcf_yield": _round(fcf_yield),
            "operating_cf_to_revenue": _round(operating_cf_to_revenue),
        },
    }

    _financials_cache[cache_key] = ratios
    print(f"[FINANCIALS] Ratios calculated for {ticker}")
    return ratios


def _round(val: Optional[float], decimals: int = 4) -> Optional[float]:
    """Round a value if it's not None."""
    if val is None:
        return None
    return round(val, decimals)


def calculate_growth_rates(ticker: str) -> dict:
    """
    Calculate revenue, earnings, and cash flow growth rates.

    Computes year-over-year (YoY) growth and 3-year compound annual
    growth rate (CAGR) to identify acceleration or deceleration.

    Parameters
    ----------
    ticker : str
        Stock symbol.

    Returns
    -------
    dict
        Keys: 'revenue_growth', 'earnings_growth', 'fcf_growth',
              'revenue_cagr_3y', 'earnings_cagr_3y'
        Each is a float (e.g., 0.15 = 15% growth) or None.
    """
    cache_key = f"growth_{ticker.upper()}"
    if cache_key in _financials_cache:
        return _financials_cache[cache_key]

    print(f"[FINANCIALS] Calculating growth rates for {ticker}...")

    statements = get_financial_statements(ticker)
    income = statements["income_stmt"]
    cashflow = statements["cashflow"]

    growth = {}

    # --- Revenue Growth (YoY) ---
    rev_current = _safe_get(income, "Total Revenue", 0)
    rev_prior = _safe_get(income, "Total Revenue", 1)
    growth["revenue_yoy"] = _round(_safe_divide(
        (rev_current - rev_prior) if rev_current and rev_prior else None,
        abs(rev_prior) if rev_prior else None
    ))

    # --- Earnings Growth (YoY) ---
    ni_current = _safe_get(income, "Net Income", 0)
    ni_prior = _safe_get(income, "Net Income", 1)
    growth["earnings_yoy"] = _round(_safe_divide(
        (ni_current - ni_prior) if ni_current and ni_prior else None,
        abs(ni_prior) if ni_prior else None
    ))

    # --- FCF Growth (YoY) ---
    ocf_current = _safe_get(cashflow, "Operating Cash Flow", 0)
    capex_current = _safe_get(cashflow, "Capital Expenditure", 0)
    ocf_prior = _safe_get(cashflow, "Operating Cash Flow", 1)
    capex_prior = _safe_get(cashflow, "Capital Expenditure", 1)

    fcf_current = (ocf_current + capex_current) if ocf_current is not None and capex_current is not None else None
    fcf_prior = (ocf_prior + capex_prior) if ocf_prior is not None and capex_prior is not None else None
    growth["fcf_yoy"] = _round(_safe_divide(
        (fcf_current - fcf_prior) if fcf_current and fcf_prior else None,
        abs(fcf_prior) if fcf_prior else None
    ))

    # --- Revenue CAGR (3-year) ---
    rev_3y_ago = _safe_get(income, "Total Revenue", 3)  # 3 years ago
    if rev_current and rev_3y_ago and rev_3y_ago > 0:
        growth["revenue_cagr_3y"] = _round((rev_current / rev_3y_ago) ** (1/3) - 1)
    else:
        growth["revenue_cagr_3y"] = None

    # --- Earnings CAGR (3-year) ---
    ni_3y_ago = _safe_get(income, "Net Income", 3)
    if ni_current and ni_3y_ago and ni_3y_ago > 0 and ni_current > 0:
        growth["earnings_cagr_3y"] = _round((ni_current / ni_3y_ago) ** (1/3) - 1)
    else:
        growth["earnings_cagr_3y"] = None

    # --- Revenue history for trend (most recent 4 years) ---
    revenue_history = []
    for i in range(min(4, len(income.columns) if not income.empty else 0)):
        rev = _safe_get(income, "Total Revenue", i)
        if rev is not None:
            period = str(income.columns[i].date()) if hasattr(income.columns[i], 'date') else str(income.columns[i])
            revenue_history.append({"period": period, "revenue": rev})
    growth["revenue_history"] = revenue_history

    # --- Earnings history ---
    earnings_history = []
    for i in range(min(4, len(income.columns) if not income.empty else 0)):
        ni = _safe_get(income, "Net Income", i)
        if ni is not None:
            period = str(income.columns[i].date()) if hasattr(income.columns[i], 'date') else str(income.columns[i])
            earnings_history.append({"period": period, "net_income": ni})
    growth["earnings_history"] = earnings_history

    _financials_cache[cache_key] = growth
    print(f"[FINANCIALS] Growth rates calculated for {ticker}")
    return growth


def get_company_profile(ticker: str) -> dict:
    """
    Get comprehensive company profile and metadata.

    Parameters
    ----------
    ticker : str
        Stock symbol.

    Returns
    -------
    dict
        Company name, sector, industry, description, employees,
        website, officers, and other key metadata.
    """
    cache_key = f"profile_{ticker.upper()}"
    if cache_key in _financials_cache:
        return _financials_cache[cache_key]

    print(f"[FINANCIALS] Fetching company profile for {ticker}...")

    stock = yf.Ticker(ticker)
    try:
        info = stock.info or {}
    except Exception:
        info = {}

    profile = {
        "ticker": ticker.upper(),
        "name": info.get("longName") or info.get("shortName") or ticker,
        "sector": info.get("sector", "Unknown"),
        "industry": info.get("industry", "Unknown"),
        "description": info.get("longBusinessSummary", "No description available."),
        "website": info.get("website", ""),
        "employees": info.get("fullTimeEmployees", 0),
        "country": info.get("country", "Unknown"),
        "city": info.get("city", ""),
        "state": info.get("state", ""),
        "currency": info.get("currency", "USD"),
        "exchange": info.get("exchange", ""),
        "market_cap": info.get("marketCap", 0),
        "share_price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
        "52w_high": info.get("fiftyTwoWeekHigh", 0),
        "52w_low": info.get("fiftyTwoWeekLow", 0),
        "avg_volume": info.get("averageVolume", 0),
        "dividend_yield": info.get("dividendYield", 0),
        "beta": info.get("beta", 0),
    }

    _financials_cache[cache_key] = profile
    return profile


def get_peer_tickers(ticker: str, max_peers: int = 5) -> list:
    """
    Find peer/competitor tickers in the same sector and industry.

    Uses the company's sector and industry classification to find
    relevant peers for comparison.

    Parameters
    ----------
    ticker : str
        Stock symbol.
    max_peers : int
        Maximum number of peers to return.

    Returns
    -------
    list of str
        Ticker symbols of peer companies.
    """
    cache_key = f"peers_{ticker.upper()}"
    if cache_key in _financials_cache:
        return _financials_cache[cache_key]

    print(f"[FINANCIALS] Finding peers for {ticker}...")

    # Well-known peer mappings by sector/industry
    # This is a curated fallback since yfinance doesn't provide
    # peer data directly. In production, you'd use an API like
    # FinancialModelingPrep or Polygon.io for this.
    PEER_MAPPINGS = {
        "AAPL": ["MSFT", "GOOGL", "AMZN", "META", "NVDA"],
        "MSFT": ["AAPL", "GOOGL", "AMZN", "CRM", "ORCL"],
        "GOOGL": ["META", "MSFT", "AMZN", "SNAP", "PINS"],
        "AMZN": ["MSFT", "GOOGL", "WMT", "SHOP", "BABA"],
        "META": ["GOOGL", "SNAP", "PINS", "TWTR", "MSFT"],
        "TSLA": ["F", "GM", "RIVN", "NIO", "LCID"],
        "NVDA": ["AMD", "INTC", "AVGO", "QCOM", "TSM"],
        "JPM": ["BAC", "GS", "MS", "WFC", "C"],
        "JNJ": ["PFE", "UNH", "MRK", "ABBV", "LLY"],
        "XOM": ["CVX", "COP", "SLB", "EOG", "PXD"],
    }

    ticker_upper = ticker.upper()
    if ticker_upper in PEER_MAPPINGS:
        peers = PEER_MAPPINGS[ticker_upper][:max_peers]
    else:
        # Fallback: try to get peers from yfinance sector info
        try:
            profile = get_company_profile(ticker)
            sector = profile.get("sector", "")
            industry = profile.get("industry", "")

            # Get sector ETF holdings as proxy peers
            # For now, return major indices as generic peers
            sector_peers = {
                "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "META"],
                "Healthcare": ["JNJ", "UNH", "PFE", "MRK", "ABBV"],
                "Financial Services": ["JPM", "BAC", "GS", "MS", "WFC"],
                "Consumer Cyclical": ["AMZN", "TSLA", "HD", "NKE", "MCD"],
                "Communication Services": ["GOOGL", "META", "DIS", "NFLX", "CMCSA"],
                "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
                "Industrials": ["CAT", "HON", "UPS", "BA", "GE"],
                "Consumer Defensive": ["PG", "KO", "PEP", "WMT", "COST"],
                "Utilities": ["NEE", "DUK", "SO", "D", "AEP"],
                "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "SPG"],
                "Basic Materials": ["LIN", "APD", "ECL", "SHW", "FCX"],
            }

            peers = sector_peers.get(sector, ["SPY", "QQQ", "DIA", "IWM", "VTI"])
            # Remove self from peers list
            peers = [p for p in peers if p != ticker_upper][:max_peers]
        except Exception:
            peers = ["SPY", "QQQ", "DIA"]

    _financials_cache[cache_key] = peers
    print(f"[FINANCIALS] Found peers for {ticker}: {peers}")
    return peers


def get_full_financial_analysis(ticker: str) -> dict:
    """
    Run the complete financial analysis pipeline.

    This is the main entry point that combines:
    - Company profile
    - Financial statements
    - Financial ratios
    - Growth rates
    - Peer identification

    Parameters
    ----------
    ticker : str
        Stock symbol.

    Returns
    -------
    dict
        Complete financial analysis package ready for AI agents.
    """
    print(f"\n[FINANCIALS] Starting full financial analysis for {ticker}...")

    profile = get_company_profile(ticker)
    statements = get_financial_statements(ticker)
    ratios = calculate_financial_ratios(ticker)
    growth = calculate_growth_rates(ticker)
    peers = get_peer_tickers(ticker)

    # Convert statement DataFrames to dicts for JSON serialization
    statements_serializable = {}
    for key, df in statements.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            # Convert to dict with fiscal periods as keys
            try:
                serialized = {}
                for col in df.columns:
                    period_key = str(col.date()) if hasattr(col, 'date') else str(col)
                    period_data = {}
                    for idx in df.index:
                        val = df.loc[idx, col]
                        if pd.notna(val):
                            period_data[str(idx)] = float(val)
                    serialized[period_key] = period_data
                statements_serializable[key] = serialized
            except Exception:
                statements_serializable[key] = {}
        else:
            statements_serializable[key] = {}

    result = {
        "profile": profile,
        "statements": statements_serializable,
        "ratios": ratios,
        "growth": growth,
        "peers": peers,
    }

    print(f"[FINANCIALS] Full financial analysis complete for {ticker}")
    return result


# ============================================================
# Test the financial data module
# ============================================================
if __name__ == "__main__":
    ticker = "AAPL"

    print("=" * 60)
    print(f"FINANCIAL ANALYSIS TEST: {ticker}")
    print("=" * 60)

    # Test company profile
    profile = get_company_profile(ticker)
    print(f"\n--- Company Profile ---")
    print(f"  Name:     {profile['name']}")
    print(f"  Sector:   {profile['sector']}")
    print(f"  Industry: {profile['industry']}")
    print(f"  Market Cap: ${profile['market_cap']:,.0f}")

    # Test financial ratios
    ratios = calculate_financial_ratios(ticker)
    print(f"\n--- Key Ratios ---")
    for category, metrics in ratios.items():
        print(f"  {category}:")
        for metric, value in metrics.items():
            if value is not None:
                if isinstance(value, float) and abs(value) < 100:
                    print(f"    {metric}: {value:.4f}")
                else:
                    print(f"    {metric}: {value:,.0f}" if isinstance(value, (int, float)) and abs(value) > 100 else f"    {metric}: {value}")

    # Test growth rates
    growth = calculate_growth_rates(ticker)
    print(f"\n--- Growth Rates ---")
    for key, value in growth.items():
        if key not in ("revenue_history", "earnings_history"):
            if value is not None:
                print(f"  {key}: {value:.2%}" if isinstance(value, float) else f"  {key}: {value}")

    # Test peers
    peers = get_peer_tickers(ticker)
    print(f"\n--- Peers ---")
    print(f"  {', '.join(peers)}")
