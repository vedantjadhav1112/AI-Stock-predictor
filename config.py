# ============================================================
# config.py — Centralized Configuration Management
# ============================================================
# Single source of truth for all API keys, model settings,
# caching policies, and runtime configuration.
#
# Usage:
#   from config import settings
#   api_key = settings.GEMINI_API_KEY
# ============================================================

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """
    Application settings loaded from environment variables.
    
    All API keys, model configurations, and runtime settings
    are centralized here so nothing is hardcoded across modules.
    """

    # ==============================================================
    # API Keys
    # ==============================================================

    # Google Gemini — Required for AI agent reasoning
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Federal Reserve Economic Data — Optional (macroeconomic data)
    FRED_API_KEY: str = os.getenv("FRED_API_KEY", "")

    # NewsAPI.org — Optional (enhanced news collection)
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")

    # Alpha Vantage — Optional (additional financial data)
    ALPHA_VANTAGE_KEY: str = os.getenv("ALPHA_VANTAGE_KEY", "")

    # ==============================================================
    # LLM Configuration
    # ==============================================================

    # Which Gemini model to use for agent reasoning
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.0-flash")

    # Temperature controls randomness (0 = deterministic, 1 = creative)
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))

    # Max tokens per LLM response
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    # ==============================================================
    # Data Fetching Configuration
    # ==============================================================

    # How many years of historical price data to fetch
    PRICE_HISTORY_YEARS: int = 5

    # How many news articles to fetch per source
    NEWS_MAX_ARTICLES: int = 15

    # Request timeout in seconds
    REQUEST_TIMEOUT: int = 30

    # ==============================================================
    # Caching Configuration (TTL in seconds)
    # ==============================================================

    # Price data: cache for 5 minutes (near real-time)
    CACHE_TTL_PRICE: int = 300

    # Financial statements: cache for 6 hours (updated quarterly)
    CACHE_TTL_FINANCIALS: int = 21600

    # News: cache for 15 minutes
    CACHE_TTL_NEWS: int = 900

    # Macro data: cache for 1 hour
    CACHE_TTL_MACRO: int = 3600

    # Full research report: cache for 30 minutes
    CACHE_TTL_REPORT: int = 1800

    # ==============================================================
    # Agent Configuration
    # ==============================================================

    # Maximum time (seconds) each agent gets to complete analysis
    AGENT_TIMEOUT: int = 60

    # Whether to run agents in parallel (requires async)
    AGENTS_PARALLEL: bool = True

    # ==============================================================
    # Paths
    # ==============================================================

    MODELS_DIR: str = "models"
    REPORTS_DIR: str = "reports"
    CACHE_DIR: str = ".cache"

    # ==============================================================
    # Validation
    # ==============================================================

    @property
    def has_gemini_key(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self.GEMINI_API_KEY)

    @property
    def has_fred_key(self) -> bool:
        """Check if FRED API key is configured."""
        return bool(self.FRED_API_KEY)

    @property
    def has_news_key(self) -> bool:
        """Check if NewsAPI key is configured."""
        return bool(self.NEWS_API_KEY)

    def validate(self) -> list:
        """
        Check which API keys are configured and return warnings.

        Returns
        -------
        list of str
            Warning messages for missing optional keys.
        """
        warnings = []

        if not self.has_gemini_key:
            warnings.append(
                "⚠️  GEMINI_API_KEY not set. AI agent reasoning will be disabled. "
                "Get a free key at: https://aistudio.google.com/apikey"
            )

        if not self.has_fred_key:
            warnings.append(
                "ℹ️  FRED_API_KEY not set. Macro data will use yfinance fallback. "
                "Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html"
            )

        if not self.has_news_key:
            warnings.append(
                "ℹ️  NEWS_API_KEY not set. News will use yfinance only. "
                "Get a free key at: https://newsapi.org"
            )

        return warnings

    def print_status(self):
        """Print the current configuration status."""
        print("\n" + "=" * 60)
        print("CONFIGURATION STATUS")
        print("=" * 60)
        print(f"  Gemini API Key:  {'[OK] Configured' if self.has_gemini_key else '[X] Missing'}")
        print(f"  FRED API Key:    {'[OK] Configured' if self.has_fred_key else '[--] Not set (optional)'}")
        print(f"  NewsAPI Key:     {'[OK] Configured' if self.has_news_key else '[--] Not set (optional)'}")
        print(f"  LLM Model:       {self.LLM_MODEL}")
        print(f"  LLM Temperature: {self.LLM_TEMPERATURE}")
        print("=" * 60 + "\n")


# Global settings instance — import this everywhere
settings = Settings()


# ============================================================
# Quick test
# ============================================================
if __name__ == "__main__":
    settings.print_status()
    warnings = settings.validate()
    for w in warnings:
        print(f"  {w}")
