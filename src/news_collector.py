# ============================================================
# src/news_collector.py — Enhanced Multi-Source News Collection
# ============================================================
# Responsibility: Collect news from multiple sources with full
# article body text for deeper AI analysis.
#
# Data sources (in priority order):
#   1. yfinance — built-in Yahoo Finance news (no API key)
#   2. NewsAPI.org — 80,000+ sources (free tier: 100 req/day)
#   3. RSS Feeds — Bloomberg, Reuters, CNBC, MarketWatch
#   4. SEC EDGAR — Company filings (10-K, 10-Q, 8-K)
#
# Unlike the original news_analyzer.py which only fetched
# headlines, this module also extracts article body text
# using trafilatura for deeper AI analysis.
# ============================================================

import yfinance as yf
import requests
import feedparser
import hashlib
from datetime import datetime, timedelta
from cachetools import TTLCache
from typing import Optional

# Try to import trafilatura for article body extraction
try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    print("[NEWS] Warning: trafilatura not installed. Article body extraction disabled.")

# In-memory cache: max 50 tickers, 15-minute TTL
_news_cache = TTLCache(maxsize=50, ttl=900)


# ============================================================
# Source 1: yfinance News (always available)
# ============================================================

def _fetch_yfinance_news(ticker: str, max_articles: int = 10) -> list:
    """
    Fetch news from Yahoo Finance via yfinance.

    This is the same source as the original news_analyzer.py,
    but restructured into the unified article format.
    """
    print(f"[NEWS] Fetching yfinance news for {ticker}...")
    articles = []

    try:
        stock = yf.Ticker(ticker)
        raw_news = stock.news or []

        for item in raw_news[:max_articles]:
            try:
                content = item.get("content", item) if isinstance(item, dict) else {}

                title = content.get("title", "")
                if not title:
                    continue

                # Extract publisher
                provider = content.get("provider", {})
                publisher = provider.get("displayName", "Unknown") if isinstance(provider, dict) else content.get("publisher", "Unknown")

                # Extract URL
                canonical = content.get("canonicalUrl", {})
                url = canonical.get("url", "") if isinstance(canonical, dict) else content.get("link", "")

                # Extract date
                published = content.get("pubDate", content.get("providerPublishTime", ""))

                articles.append({
                    "title": title,
                    "publisher": publisher,
                    "url": url,
                    "published": str(published),
                    "body": "",  # yfinance doesn't provide body text
                    "source": "Yahoo Finance",
                    "category": _categorize_headline(title),
                })
            except Exception:
                continue

    except Exception as e:
        print(f"[NEWS] Warning: yfinance news failed: {e}")

    print(f"[NEWS] yfinance: {len(articles)} articles")
    return articles


# ============================================================
# Source 2: NewsAPI.org (requires API key)
# ============================================================

def _fetch_newsapi_articles(ticker: str, company_name: str = "", max_articles: int = 10) -> list:
    """
    Fetch news from NewsAPI.org.

    Searches by ticker symbol and company name for broader coverage.
    Requires NEWS_API_KEY in environment.
    """
    try:
        from config import settings
        if not settings.has_news_key:
            return []
    except Exception:
        return []

    print(f"[NEWS] Fetching NewsAPI articles for {ticker}...")
    articles = []

    try:
        # Search by ticker and/or company name
        query = f'"{ticker}"'
        if company_name:
            query = f'"{ticker}" OR "{company_name}"'

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max_articles,
            "apiKey": settings.NEWS_API_KEY,
        }

        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("articles", []):
                title = item.get("title", "")
                if not title or title == "[Removed]":
                    continue

                articles.append({
                    "title": title,
                    "publisher": item.get("source", {}).get("name", "Unknown"),
                    "url": item.get("url", ""),
                    "published": item.get("publishedAt", ""),
                    "body": item.get("content", "") or item.get("description", ""),
                    "source": "NewsAPI",
                    "category": _categorize_headline(title),
                })
        else:
            print(f"[NEWS] NewsAPI returned status {response.status_code}")

    except Exception as e:
        print(f"[NEWS] Warning: NewsAPI fetch failed: {e}")

    print(f"[NEWS] NewsAPI: {len(articles)} articles")
    return articles


# ============================================================
# Source 3: RSS Feeds (no API key needed)
# ============================================================

# Financial news RSS feeds that cover individual companies
RSS_FEEDS = {
    "MarketWatch": "https://feeds.marketwatch.com/marketwatch/marketpulse/",
    "CNBC": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Seeking Alpha": "https://seekingalpha.com/market_currents.xml",
}


def _fetch_rss_news(ticker: str, max_per_feed: int = 5) -> list:
    """
    Fetch news from financial RSS feeds.

    Parses RSS feeds and filters articles mentioning the ticker.
    This provides no-API-key news as a supplementary source.
    """
    print(f"[NEWS] Checking RSS feeds for {ticker}...")
    articles = []
    ticker_upper = ticker.upper()

    for feed_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            count = 0

            for entry in feed.entries:
                if count >= max_per_feed:
                    break

                title = entry.get("title", "")
                summary = entry.get("summary", "")
                combined_text = (title + " " + summary).upper()

                # Only include if the ticker is mentioned
                if ticker_upper in combined_text:
                    pub_date = entry.get("published", entry.get("updated", ""))

                    articles.append({
                        "title": title,
                        "publisher": feed_name,
                        "url": entry.get("link", ""),
                        "published": pub_date,
                        "body": summary,
                        "source": f"RSS ({feed_name})",
                        "category": _categorize_headline(title),
                    })
                    count += 1

        except Exception as e:
            print(f"[NEWS] Warning: RSS feed {feed_name} failed: {e}")

    print(f"[NEWS] RSS feeds: {len(articles)} articles mentioning {ticker}")
    return articles


# ============================================================
# Source 4: SEC EDGAR Filings (no API key needed)
# ============================================================

def _fetch_sec_filings(ticker: str, max_filings: int = 5) -> list:
    """
    Fetch recent SEC filings from EDGAR RSS.

    Searches for 10-K (annual), 10-Q (quarterly), and 8-K
    (current event) filings for the company.
    """
    print(f"[NEWS] Checking SEC EDGAR for {ticker}...")
    filings = []

    try:
        # SEC EDGAR full-text search RSS
        url = f"https://efts.sec.gov/LATEST/search-index?q={ticker}&dateRange=custom&startdt={_days_ago(90)}&enddt={_today()}&forms=10-K,10-Q,8-K"

        # SEC requires a User-Agent header
        headers = {
            "User-Agent": "AIFinancialResearch research@example.com",
            "Accept": "application/json",
        }

        # Use EDGAR EFTS API
        search_url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&forms=10-K,10-Q,8-K&dateRange=custom&startdt={_days_ago(180)}&enddt={_today()}"

        response = requests.get(
            f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&forms=10-K,10-Q,8-K",
            headers=headers,
            timeout=15,
        )

        if response.status_code == 200:
            data = response.json()
            for hit in data.get("hits", {}).get("hits", [])[:max_filings]:
                source = hit.get("_source", {})
                form_type = source.get("form_type", "")
                filing_date = source.get("file_date", "")
                entity_name = source.get("entity_name", "")

                form_desc = {
                    "10-K": "Annual Report",
                    "10-Q": "Quarterly Report",
                    "8-K": "Current Event Report",
                }.get(form_type, form_type)

                filings.append({
                    "title": f"SEC {form_type}: {entity_name} — {form_desc}",
                    "publisher": "SEC EDGAR",
                    "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={ticker}&type={form_type}",
                    "published": filing_date,
                    "body": f"Filing type: {form_type} ({form_desc}). Filed on {filing_date}.",
                    "source": "SEC EDGAR",
                    "category": "Filing",
                })

    except Exception as e:
        print(f"[NEWS] Warning: SEC EDGAR fetch failed: {e}")

    print(f"[NEWS] SEC EDGAR: {len(filings)} filings")
    return filings


# ============================================================
# Article Body Extraction
# ============================================================

def extract_article_body(url: str, max_chars: int = 3000) -> str:
    """
    Extract the main text body from a news article URL.

    Uses trafilatura for robust extraction that strips ads,
    navigation, footers, etc. Falls back to empty string
    if extraction fails.

    Parameters
    ----------
    url : str
        The article URL.
    max_chars : int
        Maximum characters to extract (to avoid huge articles).

    Returns
    -------
    str
        The extracted article body text.
    """
    if not TRAFILATURA_AVAILABLE or not url:
        return ""

    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if text:
                return text[:max_chars]
    except Exception:
        pass

    return ""


# ============================================================
# Headline Categorization
# ============================================================

def _categorize_headline(title: str) -> str:
    """
    Categorize a news headline by topic.

    Simple keyword-based classification that helps AI agents
    focus on the most relevant news for their analysis.
    """
    title_lower = title.lower()

    # Category keywords
    categories = {
        "Earnings": ["earnings", "revenue", "profit", "loss", "eps", "quarterly", "q1", "q2", "q3", "q4", "fiscal", "beat", "miss"],
        "M&A": ["acquisition", "acquire", "merger", "takeover", "buyout", "deal"],
        "Regulation": ["regulation", "sec", "fda", "ftc", "antitrust", "lawsuit", "fine", "compliance", "congress", "legislation"],
        "Product": ["launch", "release", "product", "innovation", "patent", "technology", "ai ", "new feature"],
        "Management": ["ceo", "cfo", "cto", "executive", "resign", "appoint", "hire", "board"],
        "Analyst": ["upgrade", "downgrade", "target price", "buy rating", "sell rating", "analyst", "outperform", "underperform"],
        "Macro": ["fed", "interest rate", "inflation", "recession", "gdp", "economy", "tariff", "trade war"],
        "Market": ["stock", "share", "rally", "plunge", "surge", "crash", "ipo", "offering"],
    }

    for category, keywords in categories.items():
        if any(kw in title_lower for kw in keywords):
            return category

    return "General"


# ============================================================
# Deduplication
# ============================================================

def _deduplicate_articles(articles: list) -> list:
    """
    Remove duplicate articles based on title similarity.

    Uses a hash of the normalized title to detect duplicates
    across different sources.
    """
    seen_hashes = set()
    unique = []

    for article in articles:
        # Normalize title for dedup
        normalized = article["title"].lower().strip()
        # Remove common prefixes like "AAPL: " or "Breaking: "
        for prefix in ["breaking:", "exclusive:", "update:"]:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()

        title_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]

        if title_hash not in seen_hashes:
            seen_hashes.add(title_hash)
            unique.append(article)

    return unique


# ============================================================
# Helper Functions
# ============================================================

def _today() -> str:
    """Return today's date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def _days_ago(days: int) -> str:
    """Return a date N days ago as YYYY-MM-DD."""
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


# ============================================================
# Main Entry Point: Collect All News
# ============================================================

def collect_all_news(ticker: str, company_name: str = "", enrich_bodies: bool = True, max_articles: int = 20) -> dict:
    """
    Collect and merge news from all available sources.

    This is the main function that orchestrates news collection
    across all sources, deduplicates, optionally enriches with
    article body text, and returns the complete news package.

    Parameters
    ----------
    ticker : str
        Stock symbol (e.g., "AAPL").
    company_name : str
        Full company name (e.g., "Apple Inc.") for broader searches.
    enrich_bodies : bool
        If True, attempt to extract article body text from URLs.
        Set to False for faster results (headlines only).
    max_articles : int
        Maximum total articles to return after deduplication.

    Returns
    -------
    dict
        Keys:
        - 'articles': list of article dicts (title, publisher, url, body, etc.)
        - 'total_count': total articles found
        - 'sources_used': list of sources that contributed
        - 'categories': dict of category counts
    """
    cache_key = f"news_{ticker.upper()}_{enrich_bodies}"
    if cache_key in _news_cache:
        print(f"[NEWS] Cache hit for {ticker}")
        return _news_cache[cache_key]

    print(f"\n[NEWS] Collecting news for {ticker} from all sources...")

    all_articles = []

    # Source 1: yfinance (always available)
    yf_articles = _fetch_yfinance_news(ticker)
    all_articles.extend(yf_articles)

    # Source 2: NewsAPI (if API key configured)
    newsapi_articles = _fetch_newsapi_articles(ticker, company_name)
    all_articles.extend(newsapi_articles)

    # Source 3: RSS feeds (no API key needed)
    rss_articles = _fetch_rss_news(ticker)
    all_articles.extend(rss_articles)

    # Source 4: SEC EDGAR filings
    sec_filings = _fetch_sec_filings(ticker)
    all_articles.extend(sec_filings)

    # Deduplicate
    unique_articles = _deduplicate_articles(all_articles)

    # Sort by published date (newest first)
    def _parse_date(article):
        try:
            date_str = article.get("published", "")
            if isinstance(date_str, (int, float)):
                return datetime.fromtimestamp(date_str)
            if date_str:
                # Try various date formats
                for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%a, %d %b %Y %H:%M:%S %Z"]:
                    try:
                        return datetime.strptime(date_str[:19], fmt[:len(date_str)])
                    except ValueError:
                        continue
            return datetime.min
        except Exception:
            return datetime.min

    unique_articles.sort(key=_parse_date, reverse=True)

    # Limit total articles
    unique_articles = unique_articles[:max_articles]

    # Optionally enrich with article body text
    if enrich_bodies and TRAFILATURA_AVAILABLE:
        print(f"[NEWS] Enriching {len(unique_articles)} articles with body text...")
        enriched_count = 0
        for article in unique_articles:
            if not article["body"] and article["url"]:
                body = extract_article_body(article["url"])
                if body:
                    article["body"] = body
                    enriched_count += 1
        print(f"[NEWS] Enriched {enriched_count} articles with body text")

    # Count by category
    categories = {}
    for article in unique_articles:
        cat = article.get("category", "General")
        categories[cat] = categories.get(cat, 0) + 1

    # Which sources contributed
    sources_used = list(set(a["source"] for a in unique_articles))

    result = {
        "articles": unique_articles,
        "total_count": len(unique_articles),
        "sources_used": sources_used,
        "categories": categories,
        "ticker": ticker.upper(),
    }

    _news_cache[cache_key] = result
    print(f"[NEWS] Total: {len(unique_articles)} unique articles from {len(sources_used)} sources")
    return result


# ============================================================
# Test the news collector
# ============================================================
if __name__ == "__main__":
    ticker = "AAPL"

    print("=" * 60)
    print(f"NEWS COLLECTION TEST: {ticker}")
    print("=" * 60)

    result = collect_all_news(ticker, company_name="Apple Inc.", enrich_bodies=False)

    print(f"\n--- Results ---")
    print(f"  Total articles: {result['total_count']}")
    print(f"  Sources: {', '.join(result['sources_used'])}")
    print(f"  Categories: {result['categories']}")

    print(f"\n--- Articles ---")
    for i, article in enumerate(result['articles'][:10], 1):
        body_len = len(article.get('body', ''))
        print(f"  {i}. [{article['category']}] {article['title']}")
        print(f"     Source: {article['source']} | Publisher: {article['publisher']}")
        print(f"     Body: {body_len} chars | URL: {article['url'][:60]}...")
        print()
