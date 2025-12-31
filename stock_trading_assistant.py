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
from datetime import datetime, time, timedelta
import logging
import os
from dataclasses import dataclass
from typing import List, Optional
import pytz
from dotenv import load_dotenv

import pandas as pd
import yfinance as yf
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
        watchlist: Optional[List[str]] = None,
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
            "TSLA", "NVDA", "AMD", "PLTR", "HOOD",
            # Leveraged ETFs (3x volatility)
            "TQQQ", "SOXL", "UPRO", "SPXL",
            # Meme/Volatile
            "MARA", "RIOT", "COIN", "SQ", "SOFI",
            # Large cap momentum
            "AAPL", "MSFT", "META", "GOOGL", "AMZN",
        ]

        # Initialize Alpaca clients (for paper trading only)
        self.trading_client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper
        )

        # Track open positions
        self.open_trades = {}

        # Eastern timezone for market hours
        self.et_tz = pytz.timezone('US/Eastern')

        logging.info("Stock Trading Assistant initialized")
        logging.info(f"Data source: Yahoo Finance (FREE)")
        logging.info(f"Paper trading: {paper}")
        logging.info(f"Watchlist: {len(self.watchlist)} stocks")
        logging.info(f"Threshold: {threshold}")

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

    def calculate_bollinger_position(self, prices: pd.Series, period: int = 20) -> float:
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

    async def analyze_stock(self, symbol: str) -> Optional[StockAnalysis]:
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
            prices = df['Close']
            current_price = prices.iloc[-1]

            # Calculate indicators
            rsi = self.calculate_rsi(prices)
            bb_position = self.calculate_bollinger_position(prices)

            # Volume ratio (current vs 20-bar average)
            avg_volume = df['Volume'].rolling(20).mean().iloc[-1]
            current_volume = df['Volume'].iloc[-1]
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

            return StockAnalysis(
                symbol=symbol,
                price=current_price,
                rsi=rsi,
                bb_position=bb_position,
                volume_ratio=volume_ratio,
                mean_reversion_score=min(score, 100)
            )

        except Exception as e:
            logging.error(f"Error analyzing {symbol}: {e}")
            return None

    async def scan_for_opportunities(self) -> List[StockAnalysis]:
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
            if analysis.rsi < 40 and analysis.mean_reversion_score >= self.threshold:
                opportunities.append(analysis)
                logging.info(
                    f"MEAN REVERSION: {analysis.symbol} - "
                    f"Price: ${analysis.price:.2f}, "
                    f"RSI: {analysis.rsi:.1f}, "
                    f"Score: {analysis.mean_reversion_score:.1f}"
                )

        logging.info(f"Found {len(opportunities)} opportunities (score >= {self.threshold})")
        return opportunities

    async def open_paper_trade(self, analysis: StockAnalysis, position_size: float = 500.0):
        """
        Open a paper trade for mean reversion opportunity.

        Args:
            analysis: Stock analysis
            position_size: Dollar amount to trade (default $500)
        """
        # Calculate trade parameters
        entry = analysis.price
        stop = entry * 0.97   # 3% stop loss
        target = entry * 1.04  # 4% target (quick bounce)

        shares = int(position_size / entry)

        if shares < 1:
            logging.warning(f"Position too small for {analysis.symbol} at ${entry:.2f}")
            return

        # Calculate risk/reward
        risk = (entry - stop) * shares
        reward = (target - entry) * shares

        logging.info(
            f"PAPER TRADE OPENED: {analysis.symbol}\n"
            f"  Entry: ${entry:.2f}\n"
            f"  Stop: ${stop:.2f} (-3%)\n"
            f"  Target: ${target:.2f} (+4%)\n"
            f"  Shares: {shares}\n"
            f"  Risk: ${risk:.2f} | Reward: ${reward:.2f} (1:{reward/risk:.1f})"
        )

        # Track position
        self.open_trades[analysis.symbol] = {
            'entry': entry,
            'stop': stop,
            'target': target,
            'shares': shares,
            'opened_at': datetime.now()
        }

    async def monitor_open_trades(self):
        """Check open positions for stop/target hits."""
        if not self.open_trades:
            return

        for symbol, trade in list(self.open_trades.items()):
            try:
                # Get current price
                analysis = await self.analyze_stock(symbol)
                if analysis is None:
                    continue

                current_price = analysis.price
                entry = trade['entry']
                pnl_pct = ((current_price - entry) / entry) * 100

                # Check stop loss
                if current_price <= trade['stop']:
                    logging.info(
                        f"STOP LOSS HIT: {symbol} at ${current_price:.2f} "
                        f"({pnl_pct:.1f}%)"
                    )
                    del self.open_trades[symbol]

                # Check target
                elif current_price >= trade['target']:
                    logging.info(
                        f"TARGET HIT: {symbol} at ${current_price:.2f} "
                        f"({pnl_pct:.1f}%)"
                    )
                    del self.open_trades[symbol]

            except Exception as e:
                logging.error(f"Error monitoring {symbol}: {e}")

    async def run(self, max_concurrent_trades: int = 3):
        """
        Main loop: scan for opportunities and manage trades.

        Args:
            max_concurrent_trades: Maximum number of open positions
        """
        logging.info("Starting Stock Day Trading Assistant...")
        logging.info(f"Market hours: 9:30 AM - 4:00 PM ET")
        logging.info(f"Max concurrent trades: {max_concurrent_trades}")

        while True:
            try:
                # Check if market is open
                if not self.is_market_open():
                    now_et = datetime.now(self.et_tz)
                    logging.info(f"Market closed ({now_et.strftime('%I:%M %p ET')}). Sleeping 5 min...")
                    await asyncio.sleep(300)  # 5 minutes
                    continue

                # Monitor existing trades
                await self.monitor_open_trades()

                # Scan for new opportunities if under limit
                if len(self.open_trades) < max_concurrent_trades:
                    opportunities = await self.scan_for_opportunities()

                    # Open trades for top opportunities
                    for opp in opportunities[:max_concurrent_trades - len(self.open_trades)]:
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
        print("ERROR: Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables")
        print("\nGet free paper trading keys from: https://app.alpaca.markets/signup")
        return

    # Initialize assistant
    assistant = StockTradingAssistant(
        api_key=api_key,
        secret_key=secret_key,
        paper=True,  # Paper trading
        threshold=60.0  # Mean reversion score threshold
    )

    # Run
    await assistant.run(max_concurrent_trades=3)


if __name__ == "__main__":
    asyncio.run(main())
