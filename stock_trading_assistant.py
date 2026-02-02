"""
Stock Day Trading Assistant
============================

Mean reversion day trading bot for US stocks.
Uses Yahoo Finance for FREE market data + Alpaca for paper trading.

Strategy:
- Scans high-volatility stocks every 60s
- Buys oversold conditions (RSI < 40)
- Quick 3-5% bounces with tight stops
- Paper trading mode (virtual $25,000)

Trading Hours: 9:30 AM - 4:00 PM ET
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, time
import logging
import os

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from dotenv import load_dotenv
import pandas as pd
import pytz
import yfinance as yf

# News analyzer integration
try:
    from news_analyzer import NewsAnalyzer, NewsBacktester

    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False

# News-Market learning integration
try:
    from news_market_learner import NewsMarketLearner, fetch_live_news

    LEARNER_AVAILABLE = True
except ImportError:
    LEARNER_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@dataclass
class StockAnalysis:
    """Technical analysis for a stock."""

    symbol: str
    price: float
    rsi: float
    bb_position: float  # 0 = lower band, 100 = upper band
    volume_ratio: float  # Current volume vs average
    mean_reversion_score: float
    news_sentiment: float = 0.0  # -1 to +1 from news analyzer
    news_confidence: float = 0.0  # 0 to 1


class StockTradingAssistant:
    """
    Day trading assistant for US stocks.

    Uses mean reversion strategy:
    - Buy oversold (RSI < 40)
    - Target 4% bounce
    - 3% stop loss
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper: bool = True,
        watchlist: list[str] | None = None,
        threshold: float = 60.0,
    ):
        """
        Initialize stock trading assistant.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Use paper trading (default True)
            watchlist: List of stock symbols to scan
            threshold: Minimum mean reversion score to trade (0-100)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self.threshold = threshold

        # Default high-volatility watchlist
        self.watchlist = watchlist or [
            # Tech/High Beta
            "TSLA",
            "NVDA",
            "AMD",
            "PLTR",
            "HOOD",
            # Leveraged ETFs (3x volatility)
            "TQQQ",
            "SOXL",
            "UPRO",
            "SPXL",
            # Meme/Volatile
            "MARA",
            "RIOT",
            "COIN",
            "SHOP",
            "SOFI",
            # Large cap momentum
            "AAPL",
            "MSFT",
            "META",
            "GOOGL",
            "AMZN",
        ]

        # Initialize Alpaca clients (for paper trading only)
        self.trading_client = TradingClient(
            api_key=api_key, secret_key=secret_key, paper=paper
        )

        # Track open positions
        self.open_trades = {}

        # Eastern timezone for market hours
        self.et_tz = pytz.timezone("US/Eastern")

        # News analyzer integration
        self.news_analyzer = None
        self.news_backtester = None
        self.news_signals = {}  # Cache for pre-market news analysis
        self.use_news = False

        if NEWS_AVAILABLE:
            try:
                self.news_analyzer = NewsAnalyzer()
                self.news_backtester = NewsBacktester()
                self.use_news = True
                logging.info("News analyzer ENABLED")
            except Exception as e:
                logging.warning(f"News analyzer disabled: {e}")

        # News-Market learner (learns cause-effect patterns)
        self.learner = None
        if LEARNER_AVAILABLE:
            try:
                self.learner = NewsMarketLearner()
                logging.info("News-Market LEARNER ENABLED")
            except Exception as e:
                logging.warning(f"News learner disabled: {e}")

        logging.info("Stock Trading Assistant initialized")
        logging.info("Data source: Yahoo Finance (FREE)")
        logging.info(f"Paper trading: {paper}")
        logging.info(f"Watchlist: {len(self.watchlist)} stocks")
        logging.info(f"Threshold: {threshold}")
        logging.info(f"News analysis: {'ENABLED' if self.use_news else 'DISABLED'}")

    def is_market_open(self) -> bool:
        """Check if market is currently open (9:30 AM - 4:00 PM ET)."""
        now_et = datetime.now(self.et_tz)

        # Check if weekday (0 = Monday, 4 = Friday)
        if now_et.weekday() > 4:  # Saturday (5) or Sunday (6)
            return False

        # Check time
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = now_et.time()

        return market_open <= current_time <= market_close

    def is_premarket(self) -> bool:
        """Check if we're in pre-market hours (6:00 AM - 9:30 AM ET)."""
        now_et = datetime.now(self.et_tz)

        if now_et.weekday() > 4:  # Weekend
            return False

        premarket_start = time(6, 0)
        market_open = time(9, 30)
        current_time = now_et.time()

        return premarket_start <= current_time < market_open

    async def scan_premarket_news(self):
        """
        Scan news for all watchlist stocks before market opens.

        Call this during pre-market hours to prepare for the trading day.
        """
        if not self.use_news or not self.news_analyzer:
            return

        logging.info("=" * 50)
        logging.info("PRE-MARKET NEWS SCAN")
        logging.info("=" * 50)

        self.news_signals = {}

        for symbol in self.watchlist:
            try:
                signal = self.news_analyzer.analyze_symbol(symbol, track=True)
                self.news_signals[symbol] = signal

                if signal.headline_count > 0:
                    emoji = (
                        "+"
                        if signal.score > 0.15
                        else ("-" if signal.score < -0.15 else "~")
                    )
                    logging.info(
                        f"  {symbol}: {emoji} {signal.sentiment} ({signal.score:+.2f}) "
                        f"- {signal.headline_count} headlines - {signal.recommendation.upper()}"
                    )

                    # Log top headline
                    if signal.top_headlines:
                        logging.info(f"    -> {signal.top_headlines[0][:60]}...")

            except Exception as e:
                logging.error(f"Error analyzing news for {symbol}: {e}")

        # Summary
        bullish = sum(1 for s in self.news_signals.values() if s.sentiment == "bullish")
        bearish = sum(1 for s in self.news_signals.values() if s.sentiment == "bearish")
        logging.info("-" * 50)
        logging.info(
            f"NEWS SUMMARY: {bullish} bullish, {bearish} bearish, {len(self.news_signals) - bullish - bearish} neutral"
        )
        logging.info("=" * 50)

    def get_news_score_adjustment(self, symbol: str) -> tuple[float, float]:
        """
        Get news-based score adjustment for a symbol.

        Returns:
            (score_adjustment, confidence)
            score_adjustment: -20 to +20 points
            confidence: 0 to 1
        """
        if not self.use_news or symbol not in self.news_signals:
            return 0.0, 0.0

        signal = self.news_signals[symbol]

        # Scale sentiment (-1 to +1) to score adjustment (-20 to +20)
        adjustment = signal.score * 20

        return adjustment, signal.confidence

    def get_news_accuracy_report(self) -> str:
        """Get accuracy report for news sources."""
        if not self.news_backtester:
            return "News analyzer not available"

        return self.news_backtester.generate_backtest_report()

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return 50.0  # Neutral if insufficient data

        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0.0)
        losses = -deltas.where(deltas < 0, 0.0)

        avg_gain = gains.rolling(window=period).mean()
        avg_loss = losses.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1]

    def calculate_bollinger_position(
        self, prices: pd.Series, period: int = 20
    ) -> float:
        """
        Calculate position within Bollinger Bands (0-100).
        0 = at lower band (oversold)
        100 = at upper band (overbought)
        """
        if len(prices) < period:
            return 50.0

        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        upper_band = sma + (2 * std)
        lower_band = sma - (2 * std)

        current_price = prices.iloc[-1]
        band_width = upper_band.iloc[-1] - lower_band.iloc[-1]

        if band_width == 0:
            return 50.0

        position = ((current_price - lower_band.iloc[-1]) / band_width) * 100
        return max(0, min(100, position))

    async def analyze_stock(self, symbol: str) -> StockAnalysis | None:
        """
        Analyze a stock for mean reversion opportunity using Yahoo Finance.

        Returns:
            StockAnalysis if successful, None if error
        """
        try:
            # Get intraday data from Yahoo Finance (5-minute bars)
            ticker = yf.Ticker(symbol)

            # Get last 7 days of 5-minute bars (to ensure we have 100+ bars)
            df = ticker.history(period="7d", interval="5m")

            if df.empty or len(df) < 20:
                return None

            # Use Close and Volume columns
            prices = df["Close"]
            current_price = prices.iloc[-1]

            # Calculate indicators
            rsi = self.calculate_rsi(prices)
            bb_position = self.calculate_bollinger_position(prices)

            # Volume ratio (current vs 20-bar average)
            avg_volume = df["Volume"].rolling(20).mean().iloc[-1]
            current_volume = df["Volume"].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

            # Mean reversion score (0-100)
            score = 0.0

            # 1. RSI oversold (40 points)
            if rsi < 30:
                score += 40 * (30 - rsi) / 30
            elif rsi < 40:
                score += 20 * (40 - rsi) / 10

            # 2. Bollinger band position (30 points)
            if bb_position < 20:  # Near lower band
                score += 30
            elif bb_position < 40:
                score += 15

            # 3. Volume confirmation (20 points)
            if volume_ratio > 1.5:  # High volume
                score += 20
            elif volume_ratio > 1.0:
                score += 10

            # 4. Extreme RSI bonus (10 points)
            if rsi < 25:
                score += 10

            # 5. News sentiment adjustment (+/- 20 points)
            news_adj, news_conf = self.get_news_score_adjustment(symbol)
            score += news_adj

            return StockAnalysis(
                symbol=symbol,
                price=current_price,
                rsi=rsi,
                bb_position=bb_position,
                volume_ratio=volume_ratio,
                mean_reversion_score=max(0, min(score, 100)),
                news_sentiment=news_adj / 20
                if news_adj
                else 0,  # Convert back to -1 to +1
                news_confidence=news_conf,
            )

        except Exception as e:
            logging.error(f"Error analyzing {symbol}: {e}")
            return None

    async def scan_for_opportunities(self) -> list[StockAnalysis]:
        """
        Scan watchlist for oversold mean reversion setups.

        Returns:
            List of stocks meeting criteria (RSI < 40, score >= threshold)
        """
        logging.info(f"Scanning {len(self.watchlist)} stocks for mean reversion...")

        opportunities = []

        # Analyze all stocks concurrently
        tasks = [self.analyze_stock(symbol) for symbol in self.watchlist]
        results = await asyncio.gather(*tasks)

        for analysis in results:
            if analysis is None:
                continue

            # Filter: Oversold + meets threshold
            # Also filter out strongly bearish news (avoid buying into bad news)
            if analysis.rsi < 40 and analysis.mean_reversion_score >= self.threshold:
                # Skip if news is strongly bearish (unless oversold is extreme)
                if analysis.news_sentiment < -0.5 and analysis.rsi > 30:
                    logging.info(
                        f"SKIPPED: {analysis.symbol} - Bearish news ({analysis.news_sentiment:.2f})"
                    )
                    continue

                opportunities.append(analysis)
                news_str = (
                    f", News: {analysis.news_sentiment:+.2f}"
                    if analysis.news_confidence > 0
                    else ""
                )
                logging.info(
                    f"MEAN REVERSION: {analysis.symbol} - "
                    f"Price: ${analysis.price:.2f}, "
                    f"RSI: {analysis.rsi:.1f}, "
                    f"Score: {analysis.mean_reversion_score:.1f}{news_str}"
                )

        logging.info(
            f"Found {len(opportunities)} opportunities (score >= {self.threshold})"
        )

        # Record news snapshots for learning (cause-effect correlation)
        if self.learner and LEARNER_AVAILABLE:
            for analysis in results:
                if analysis is None:
                    continue
                try:
                    headlines = fetch_live_news(analysis.symbol)
                    if headlines:
                        self.learner.record_snapshot(
                            analysis.symbol, headlines, analysis.price
                        )
                except Exception:
                    pass  # Silent fail - learning is optional

            # Periodically update outcomes
            try:
                self.learner.update_outcomes()
            except Exception:
                pass

        return opportunities

    async def open_paper_trade(
        self, analysis: StockAnalysis, position_size: float = 500.0
    ):
        """
        Open a LIVE trade on Alpaca for mean reversion opportunity.

        Args:
            analysis: Stock analysis
            position_size: Dollar amount to trade (default $500)
        """
        # Calculate trade parameters
        entry = analysis.price
        stop = entry * 0.97  # 3% stop loss
        target = entry * 1.04  # 4% target (quick bounce)

        shares = int(position_size / entry)

        if shares < 1:
            logging.warning(f"Position too small for {analysis.symbol} at ${entry:.2f}")
            return

        # Calculate risk/reward
        risk = (entry - stop) * shares
        reward = (target - entry) * shares

        # Submit LIVE order to Alpaca
        try:
            order_request = MarketOrderRequest(
                symbol=analysis.symbol,
                qty=shares,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
            )
            order = self.trading_client.submit_order(order_request)

            logging.info(
                f"LIVE ORDER SUBMITTED: {analysis.symbol}\n"
                f"  Order ID: {order.id}\n"
                f"  Entry: ${entry:.2f}\n"
                f"  Stop: ${stop:.2f} (-3%)\n"
                f"  Target: ${target:.2f} (+4%)\n"
                f"  Shares: {shares}\n"
                f"  Risk: ${risk:.2f} | Reward: ${reward:.2f} (1:{reward/risk:.1f})"
            )

            # Track position
            self.open_trades[analysis.symbol] = {
                "entry": entry,
                "stop": stop,
                "target": target,
                "shares": shares,
                "order_id": str(order.id),
                "opened_at": datetime.now(),
            }

        except Exception as e:
            logging.error(f"Failed to submit order for {analysis.symbol}: {e}")

    async def monitor_open_trades(self):
        """Check open positions for stop/target hits and execute sells."""
        if not self.open_trades:
            return

        for symbol, trade in list(self.open_trades.items()):
            try:
                # Get current price
                analysis = await self.analyze_stock(symbol)
                if analysis is None:
                    continue

                current_price = analysis.price
                entry = trade["entry"]
                pnl_pct = ((current_price - entry) / entry) * 100
                shares = trade["shares"]

                # Check stop loss
                if current_price <= trade["stop"]:
                    await self.close_position(
                        symbol, shares, "STOP LOSS", current_price, pnl_pct
                    )

                # Check target
                elif current_price >= trade["target"]:
                    await self.close_position(
                        symbol, shares, "TARGET HIT", current_price, pnl_pct
                    )

            except Exception as e:
                logging.error(f"Error monitoring {symbol}: {e}")

    async def close_position(
        self, symbol: str, shares: int, reason: str, price: float, pnl_pct: float
    ):
        """Close a position by selling shares."""
        try:
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=shares,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )
            order = self.trading_client.submit_order(order_request)

            logging.info(
                f"{reason}: {symbol} at ${price:.2f} ({pnl_pct:+.1f}%)\n"
                f"  Sold {shares} shares\n"
                f"  Order ID: {order.id}"
            )

            del self.open_trades[symbol]

        except Exception as e:
            logging.error(f"Failed to close position {symbol}: {e}")

    async def run(self, max_concurrent_trades: int = 3):
        """
        Main loop: scan for opportunities and manage trades.

        Args:
            max_concurrent_trades: Maximum number of open positions
        """
        logging.info("Starting Stock Day Trading Assistant...")
        logging.info("Market hours: 9:30 AM - 4:00 PM ET")
        logging.info(f"Max concurrent trades: {max_concurrent_trades}")

        # Track if we've done pre-market news scan today
        last_news_scan_date = None

        while True:
            try:
                now_et = datetime.now(self.et_tz)
                today = now_et.date()

                # Pre-market news scan (once per day)
                if self.is_premarket() and last_news_scan_date != today:
                    logging.info(f"Pre-market hours ({now_et.strftime('%I:%M %p ET')})")
                    await self.scan_premarket_news()
                    last_news_scan_date = today

                    # Update backtest outcomes
                    if self.news_backtester:
                        updated = self.news_backtester.update_all_outcomes()
                        if updated:
                            logging.info(f"Updated {updated} news prediction outcomes")

                    await asyncio.sleep(300)  # Wait 5 min
                    continue

                # Check if market is open
                if not self.is_market_open():
                    logging.info(
                        f"Market closed ({now_et.strftime('%I:%M %p ET')}). Sleeping 5 min..."
                    )
                    await asyncio.sleep(300)  # 5 minutes
                    continue

                # Monitor existing trades
                await self.monitor_open_trades()

                # Scan for new opportunities if under limit
                if len(self.open_trades) < max_concurrent_trades:
                    opportunities = await self.scan_for_opportunities()

                    # Open trades for top opportunities
                    for opp in opportunities[
                        : max_concurrent_trades - len(self.open_trades)
                    ]:
                        if opp.symbol not in self.open_trades:
                            await self.open_paper_trade(opp)

                # Wait 60 seconds before next scan
                await asyncio.sleep(60)

            except KeyboardInterrupt:
                logging.info("Shutting down...")
                break
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)


async def main():
    """Main entry point."""
    # Load environment variables from .env file
    load_dotenv()

    # Get API keys from environment
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")

    if not api_key or not secret_key:
        return

    # Initialize assistant
    assistant = StockTradingAssistant(
        api_key=api_key,
        secret_key=secret_key,
        paper=False,  # LIVE trading with real money
        threshold=60.0,  # Mean reversion score threshold
    )

    # Run
    await assistant.run(max_concurrent_trades=3)


if __name__ == "__main__":
    asyncio.run(main())
