"""
News Fetcher Module
===================
Fetches stock news from multiple free APIs.
"""

import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import logging

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """A news article."""
    headline: str
    summary: str
    source: str
    url: str
    published: datetime
    symbols: list[str]
    api_source: str  # Which API provided this


class NewsFetcher:
    """
    Fetches news from multiple APIs.

    Supported APIs:
    - Alpaca (included with trading account - PREFERRED)
    - Finnhub (free tier: 60 calls/min)
    - Alpha Vantage (free tier: 5 calls/min)
    - NewsAPI (free tier: 100 calls/day)
    """

    def __init__(self):
        self.alpaca_key = os.getenv("ALPACA_API_KEY")
        self.alpaca_secret = os.getenv("ALPACA_SECRET_KEY")
        self.finnhub_key = os.getenv("FINNHUB_API_KEY")
        self.alphavantage_key = os.getenv("ALPHAVANTAGE_API_KEY")
        self.newsapi_key = os.getenv("NEWSAPI_KEY")

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GridBotChuck/1.0'
        })

        # Rate limiting
        self.last_call = {}

    def _rate_limit(self, api: str, min_interval: float):
        """Enforce rate limiting."""
        if api in self.last_call:
            elapsed = time.time() - self.last_call[api]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        self.last_call[api] = time.time()

    def fetch_alpaca(self, symbol: str) -> list[NewsArticle]:
        """
        Fetch news from Alpaca (included with trading account).

        This is the preferred source - no additional API key needed!
        """
        if not self.alpaca_key or not self.alpaca_secret:
            logger.warning("Alpaca API keys not set")
            return []

        self._rate_limit('alpaca', 0.5)  # 2 calls/sec allowed

        url = "https://data.alpaca.markets/v1beta1/news"
        headers = {
            'APCA-API-KEY-ID': self.alpaca_key,
            'APCA-API-SECRET-KEY': self.alpaca_secret
        }
        params = {
            'symbols': symbol,
            'limit': 50,
            'sort': 'desc'
        }

        try:
            resp = self.session.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            articles = []
            for item in data.get('news', []):
                try:
                    # Parse time
                    time_str = item.get('created_at', '')
                    if time_str:
                        pub_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        pub_time = pub_time.replace(tzinfo=None)
                    else:
                        pub_time = datetime.now()

                    articles.append(NewsArticle(
                        headline=item.get('headline', ''),
                        summary=item.get('summary', ''),
                        source=item.get('source', 'Unknown'),
                        url=item.get('url', ''),
                        published=pub_time,
                        symbols=item.get('symbols', [symbol]),
                        api_source='alpaca'
                    ))
                except Exception as e:
                    logger.debug(f"Error parsing Alpaca article: {e}")

            logger.info(f"Alpaca: fetched {len(articles)} articles for {symbol}")
            return articles

        except Exception as e:
            logger.error(f"Alpaca News API error: {e}")
            return []

    def fetch_finnhub(self, symbol: str, from_date: Optional[datetime] = None,
                      to_date: Optional[datetime] = None) -> list[NewsArticle]:
        """
        Fetch news from Finnhub.

        Free tier: 60 calls/minute
        """
        if not self.finnhub_key:
            logger.warning("Finnhub API key not set")
            return []

        self._rate_limit('finnhub', 1.0)  # 1 second between calls

        if not from_date:
            from_date = datetime.now() - timedelta(days=7)
        if not to_date:
            to_date = datetime.now()

        url = "https://finnhub.io/api/v1/company-news"
        params = {
            'symbol': symbol,
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'token': self.finnhub_key
        }

        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            articles = []
            for item in data[:50]:  # Limit to 50 articles
                try:
                    articles.append(NewsArticle(
                        headline=item.get('headline', ''),
                        summary=item.get('summary', ''),
                        source=item.get('source', 'Unknown'),
                        url=item.get('url', ''),
                        published=datetime.fromtimestamp(item.get('datetime', 0)),
                        symbols=[symbol],
                        api_source='finnhub'
                    ))
                except Exception as e:
                    logger.debug(f"Error parsing Finnhub article: {e}")

            return articles

        except Exception as e:
            logger.error(f"Finnhub API error: {e}")
            return []

    def fetch_alphavantage(self, symbol: str, topics: str = "earnings") -> list[NewsArticle]:
        """
        Fetch news from Alpha Vantage.

        Free tier: 5 calls/minute, 500/day
        Topics: earnings, ipo, mergers_and_acquisitions, financial_markets, etc.
        """
        if not self.alphavantage_key:
            logger.warning("Alpha Vantage API key not set")
            return []

        self._rate_limit('alphavantage', 12.0)  # 12 seconds between calls

        url = "https://www.alphavantage.co/query"
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': symbol,
            'topics': topics,
            'apikey': self.alphavantage_key,
            'limit': 50
        }

        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            articles = []
            for item in data.get('feed', []):
                try:
                    # Parse time
                    time_str = item.get('time_published', '')
                    if time_str:
                        pub_time = datetime.strptime(time_str[:15], '%Y%m%dT%H%M%S')
                    else:
                        pub_time = datetime.now()

                    # Get symbols
                    symbols = [t['ticker'] for t in item.get('ticker_sentiment', [])]

                    articles.append(NewsArticle(
                        headline=item.get('title', ''),
                        summary=item.get('summary', ''),
                        source=item.get('source', 'Unknown'),
                        url=item.get('url', ''),
                        published=pub_time,
                        symbols=symbols or [symbol],
                        api_source='alphavantage'
                    ))
                except Exception as e:
                    logger.debug(f"Error parsing AlphaVantage article: {e}")

            return articles

        except Exception as e:
            logger.error(f"Alpha Vantage API error: {e}")
            return []

    def fetch_newsapi(self, symbol: str, company_name: str = None) -> list[NewsArticle]:
        """
        Fetch news from NewsAPI.

        Free tier: 100 calls/day, 1 month history
        """
        if not self.newsapi_key:
            logger.warning("NewsAPI key not set")
            return []

        self._rate_limit('newsapi', 1.0)

        # Search by symbol or company name
        query = company_name if company_name else symbol

        url = "https://newsapi.org/v2/everything"
        params = {
            'q': f'"{query}" stock OR shares',
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 50,
            'apiKey': self.newsapi_key
        }

        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            articles = []
            for item in data.get('articles', []):
                try:
                    # Parse time
                    time_str = item.get('publishedAt', '')
                    if time_str:
                        pub_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        pub_time = pub_time.replace(tzinfo=None)
                    else:
                        pub_time = datetime.now()

                    articles.append(NewsArticle(
                        headline=item.get('title', ''),
                        summary=item.get('description', ''),
                        source=item.get('source', {}).get('name', 'Unknown'),
                        url=item.get('url', ''),
                        published=pub_time,
                        symbols=[symbol],
                        api_source='newsapi'
                    ))
                except Exception as e:
                    logger.debug(f"Error parsing NewsAPI article: {e}")

            return articles

        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return []

    def fetch_all(self, symbol: str, company_name: str = None) -> list[NewsArticle]:
        """Fetch from all available APIs and combine results."""
        all_articles = []

        # Alpaca first (preferred - included with trading account)
        if self.alpaca_key and self.alpaca_secret:
            all_articles.extend(self.fetch_alpaca(symbol))

        if self.finnhub_key:
            all_articles.extend(self.fetch_finnhub(symbol))

        if self.alphavantage_key:
            all_articles.extend(self.fetch_alphavantage(symbol))

        if self.newsapi_key:
            all_articles.extend(self.fetch_newsapi(symbol, company_name))

        # Sort by published date (newest first)
        all_articles.sort(key=lambda x: x.published, reverse=True)

        # Remove duplicates by headline similarity
        seen_headlines = set()
        unique_articles = []
        for article in all_articles:
            # Simple dedup by first 50 chars of headline
            key = article.headline[:50].lower()
            if key not in seen_headlines:
                seen_headlines.add(key)
                unique_articles.append(article)

        return unique_articles
