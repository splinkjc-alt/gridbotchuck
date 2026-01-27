"""
TRIPLE-THREAT TRADING BOT
=========================

Three strategies in one bot:
1. MEAN REVERSION - Buy dips (RSI < 45)
2. MOMENTUM - Ride trends (RSI 60-70)
3. BREAKOUT - Catch pumps (Volume spike + Price surge)

Paper Trading: $3,000 virtual capital
Max Risk: 2% per trade ($60)
Position Size: $200-300 per trade
Max Concurrent: 5 trades

Run: python triple_threat_trader.py
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

from config.config_manager import ConfigManager
from config.config_validator import ConfigValidator
from config.trading_mode import TradingMode
from core.services.exchange_service_factory import ExchangeServiceFactory
from strategies.market_analyzer import CoinAnalysis, MarketAnalyzer

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class StrategyType(Enum):
    """Trading strategy types."""

    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    BREAKOUT = "breakout"


@dataclass
class TripleThreatSignal:
    """Trading signal with strategy type."""

    pair: str
    strategy: StrategyType
    score: float
    entry: float
    target: float
    stop: float

    # Metrics
    rsi: float
    price_change_15m: float
    volume_ratio: float

    # Risk/Reward
    risk_pct: float
    reward_pct: float
    risk_reward_ratio: float


class TripleThreatTrader:
    """
    Advanced trading bot with 3 strategies:
    - Mean Reversion
    - Momentum
    - Breakout Detection
    """

    def __init__(
        self,
        capital: float = 3000.0,
        max_risk_per_trade: float = 0.02,  # 2%
        max_concurrent: int = 7,  # Increased to catch more opportunities
    ):
        """Initialize the Triple-Threat Trader."""
        self.capital = capital
        self.initial_capital = capital
        self.max_risk_per_trade = max_risk_per_trade
        self.max_concurrent = max_concurrent

        # Trading state
        self.open_trades = {}
        self.trade_history = []
        self.trade_counter = 0

        # Strategy thresholds
        self.mean_reversion_threshold = 60.0
        self.momentum_threshold = 65.0
        self.breakout_threshold = 70.0

        # Candidate pairs (high liquidity)
        self.pairs = [
            "XRP/USD",
            "ADA/USD",
            "DOGE/USD",
            "DOT/USD",
            "LINK/USD",
            "ATOM/USD",
            "UNI/USD",
            "AVAX/USD",
            "FIL/USD",
            "NEAR/USD",
            "APT/USD",
            "ARB/USD",
            "OP/USD",
            "SOL/USD",
        ]

        # Initialize services
        self.config_manager = ConfigManager("config/config.json", ConfigValidator())
        self.trading_mode = TradingMode.PAPER_TRADING

        self.exchange_service = ExchangeServiceFactory.create_exchange_service(
            self.config_manager, self.trading_mode
        )

        self.market_analyzer = MarketAnalyzer(
            self.exchange_service, self.config_manager
        )

        logging.info("=" * 60)
        logging.info("TRIPLE-THREAT TRADER INITIALIZED")
        logging.info("=" * 60)
        logging.info(f"Capital: ${self.capital:,.2f}")
        logging.info(
            f"Max Risk/Trade: {self.max_risk_per_trade*100:.1f}% (${self.capital * self.max_risk_per_trade:.2f})"
        )
        logging.info(f"Max Concurrent: {self.max_concurrent} trades")
        logging.info(f"Scanning: {len(self.pairs)} pairs")
        logging.info("=" * 60)

    def calculate_position_size(self, strategy: StrategyType, stop_pct: float) -> float:
        """
        Calculate position size based on strategy and risk.

        Args:
            strategy: Which strategy (affects sizing)
            stop_pct: Stop loss percentage (e.g., 0.03 for 3%)

        Returns:
            Position size in dollars
        """
        # Maximum dollar risk per trade
        max_risk_dollars = self.capital * self.max_risk_per_trade

        # Calculate position size to risk exactly max_risk_dollars
        position_size = max_risk_dollars / stop_pct

        # Strategy-specific adjustments
        if strategy == StrategyType.BREAKOUT:
            # Bigger positions for breakouts (higher potential)
            position_size = min(position_size, 300.0)
        elif strategy == StrategyType.MOMENTUM:
            position_size = min(position_size, 250.0)
        else:  # Mean reversion
            position_size = min(position_size, 200.0)

        # Never exceed 10% of capital per trade
        position_size = min(position_size, self.capital * 0.10)

        return position_size

    def detect_mean_reversion(
        self, analysis: CoinAnalysis
    ) -> TripleThreatSignal | None:
        """
        Detect mean reversion opportunity (oversold bounce).

        Criteria:
        - RSI(7) < 30 (oversold) - OPTIMIZED FROM 7-DAY BACKTEST
        - Near Bollinger lower band
        - Volume confirmation
        """
        if analysis.rsi >= 30:  # Changed from 45 to 30 - winning strategy!
            return None

        score = 0.0

        # RSI oversold (40 points)
        if analysis.rsi < 20:  # Extremely oversold
            score += 40 * (20 - analysis.rsi) / 20
        elif analysis.rsi < 30:  # Very oversold
            score += 30 * (30 - analysis.rsi) / 10

        # Bollinger position (30 points)
        if analysis.bollinger_score >= 80:
            score += 30
        elif analysis.bollinger_score >= 60:
            score += 15

        # Volume (20 points)
        score += analysis.volume_score * 0.20

        # CCI confirmation (10 points)
        if analysis.cci < -100:
            score += 10

        if score < self.mean_reversion_threshold:
            return None

        # Calculate entry/targets
        entry = analysis.price * 0.999  # Slightly below current
        stop = entry * 0.97  # 3% stop
        target = entry * 1.04  # 4% target (quick bounce)

        return TripleThreatSignal(
            pair=analysis.pair,
            strategy=StrategyType.MEAN_REVERSION,
            score=score,
            entry=entry,
            target=target,
            stop=stop,
            rsi=analysis.rsi,
            price_change_15m=0.0,  # Not relevant for MR
            volume_ratio=analysis.volume_score / 100,
            risk_pct=3.0,
            reward_pct=4.0,
            risk_reward_ratio=4.0 / 3.0,
        )

    def detect_momentum(self, analysis: CoinAnalysis) -> TripleThreatSignal | None:
        """
        Detect momentum opportunity (trend continuation).

        Criteria:
        - RSI 60-75 (strong but not overbought)
        - Price above EMAs
        - MACD bullish
        - Good volume
        """
        if not (60 <= analysis.rsi <= 75):
            return None

        score = 0.0

        # RSI in sweet spot (30 points)
        if 65 <= analysis.rsi <= 70:
            score += 30
        elif 60 <= analysis.rsi < 65 or 70 < analysis.rsi <= 75:
            score += 20

        # Price above EMAs (25 points)
        if analysis.price_above_emas:
            score += 25

        # MACD bullish (20 points)
        if analysis.macd_bullish:
            score += 20

        # Volume (15 points)
        score += analysis.volume_score * 0.15

        # Trend strength (10 points)
        if analysis.cci > 100:  # Strong uptrend
            score += 10

        if score < self.momentum_threshold:
            return None

        # Calculate entry/targets
        entry = analysis.price * 1.001  # Slightly above (confirm momentum)
        stop = entry * 0.97  # 3% stop
        target = entry * 1.08  # 8% target (ride trend)

        return TripleThreatSignal(
            pair=analysis.pair,
            strategy=StrategyType.MOMENTUM,
            score=score,
            entry=entry,
            target=target,
            stop=stop,
            rsi=analysis.rsi,
            price_change_15m=0.0,
            volume_ratio=analysis.volume_score / 100,
            risk_pct=3.0,
            reward_pct=8.0,
            risk_reward_ratio=8.0 / 3.0,
        )

    async def detect_breakout(
        self, analysis: CoinAnalysis
    ) -> TripleThreatSignal | None:
        """
        Detect breakout/pump opportunity (steep climb).

        Criteria:
        - Price +5%+ in last 15-30 min
        - Volume spike (3x+ average)
        - RSI > 70 (strong momentum)
        - Breaking recent highs
        """
        # Get recent price data to calculate % change
        try:
            # Fetch 15min candles (last 10 = 2.5 hours)
            df = await self.exchange_service.fetch_ohlcv_simple(
                pair=analysis.pair, timeframe="15m", limit=10
            )

            if len(df) < 2:
                return None

            # Calculate price change over last 15-30 min
            current_price = df["close"].iloc[-1]
            price_30min_ago = df["close"].iloc[-2]
            df["close"].iloc[-1]

            pct_change_30m = ((current_price - price_30min_ago) / price_30min_ago) * 100

            # Calculate volume ratio
            avg_volume = df["volume"].iloc[:-1].mean()
            current_volume = df["volume"].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

            # BREAKOUT CRITERIA
            if pct_change_30m < 5.0:  # Need at least +5% move
                return None

            if volume_ratio < 2.0:  # Need at least 2x volume
                return None

            if analysis.rsi < 70:  # Need strong RSI
                return None

            # Calculate breakout score
            score = 0.0

            # Price surge (40 points)
            if pct_change_30m >= 10:
                score += 40
            elif pct_change_30m >= 7:
                score += 30
            elif pct_change_30m >= 5:
                score += 20

            # Volume explosion (30 points)
            if volume_ratio >= 5:
                score += 30
            elif volume_ratio >= 3:
                score += 20
            elif volume_ratio >= 2:
                score += 10

            # RSI strength (20 points)
            if analysis.rsi >= 80:
                score += 20
            elif analysis.rsi >= 75:
                score += 15
            elif analysis.rsi >= 70:
                score += 10

            # Momentum confirmation (10 points)
            if analysis.macd_bullish and analysis.price_above_emas:
                score += 10

            if score < self.breakout_threshold:
                return None

            # Calculate entry/targets (more aggressive)
            entry = current_price * 1.002  # Enter slightly above (confirm breakout)
            stop = current_price * 0.96  # 4% stop (wider for volatility)
            target = current_price * 1.15  # 15% target (ride the pump!)

            return TripleThreatSignal(
                pair=analysis.pair,
                strategy=StrategyType.BREAKOUT,
                score=score,
                entry=entry,
                target=target,
                stop=stop,
                rsi=analysis.rsi,
                price_change_15m=pct_change_30m,
                volume_ratio=volume_ratio,
                risk_pct=4.0,
                reward_pct=15.0,
                risk_reward_ratio=15.0 / 4.0,
            )

        except Exception as e:
            logging.error(f"Error detecting breakout for {analysis.pair}: {e}")
            return None

    async def scan_all_strategies(self):
        """
        Scan for opportunities across all 3 strategies.
        """
        logging.info("=" * 60)
        logging.info(f"SCANNING {len(self.pairs)} PAIRS - ALL STRATEGIES")
        logging.info("=" * 60)

        signals = []

        try:
            # Get market analysis for all pairs
            analyses = await self.market_analyzer.find_best_trading_pairs(
                candidate_pairs=self.pairs,
                timeframe="5m",
                min_volume_threshold=100000,
                min_price=0.01,
                max_price=100.0,
            )

            # Check each analysis against all strategies
            for analysis in analyses:
                # 1. Check Mean Reversion
                mr_signal = self.detect_mean_reversion(analysis)
                if mr_signal:
                    signals.append(mr_signal)
                    logging.info(
                        f"🔵 MEAN REVERSION: {mr_signal.pair} | RSI: {mr_signal.rsi:.1f} | Score: {mr_signal.score:.1f}"
                    )

                # 2. Check Momentum
                mom_signal = self.detect_momentum(analysis)
                if mom_signal:
                    signals.append(mom_signal)
                    logging.info(
                        f"🟢 MOMENTUM: {mom_signal.pair} | RSI: {mom_signal.rsi:.1f} | Score: {mom_signal.score:.1f}"
                    )

                # 3. Check Breakout
                bo_signal = await self.detect_breakout(analysis)
                if bo_signal:
                    signals.append(bo_signal)
                    logging.info(
                        f"🔴 BREAKOUT: {bo_signal.pair} | +{bo_signal.price_change_15m:.1f}% | Vol: {bo_signal.volume_ratio:.1f}x | Score: {bo_signal.score:.1f}"
                    )

        except Exception as e:
            logging.error(f"Error scanning: {e}", exc_info=True)

        logging.info(f"Scan complete. Found {len(signals)} total opportunities")
        logging.info(
            f"  - Mean Reversion: {sum(1 for s in signals if s.strategy == StrategyType.MEAN_REVERSION)}"
        )
        logging.info(
            f"  - Momentum: {sum(1 for s in signals if s.strategy == StrategyType.MOMENTUM)}"
        )
        logging.info(
            f"  - Breakout: {sum(1 for s in signals if s.strategy == StrategyType.BREAKOUT)}"
        )
        logging.info("=" * 60)

        # Auto-accept top signals if under max concurrent
        signals_to_take = signals[: self.max_concurrent - len(self.open_trades)]

        for signal in signals_to_take:
            await self.open_paper_trade(signal)

        return signals

    async def open_paper_trade(self, signal: TripleThreatSignal):
        """Open a paper trade based on signal."""
        self.trade_counter += 1
        trade_id = f"T{self.trade_counter:04d}"

        # Calculate position size
        position_size = self.calculate_position_size(
            signal.strategy, signal.risk_pct / 100
        )

        shares = position_size / signal.entry
        risk_dollars = shares * (signal.entry - signal.stop)
        reward_dollars = shares * (signal.target - signal.entry)

        trade = {
            "id": trade_id,
            "pair": signal.pair,
            "strategy": signal.strategy.value,
            "entry": signal.entry,
            "stop": signal.stop,
            "target": signal.target,
            "shares": shares,
            "position_size": position_size,
            "opened_at": datetime.now(),
            "risk_dollars": risk_dollars,
            "reward_dollars": reward_dollars,
        }

        self.open_trades[trade_id] = trade

        # Deduct from capital
        self.capital -= position_size

        strategy_icon = {
            StrategyType.MEAN_REVERSION: "🔵",
            StrategyType.MOMENTUM: "🟢",
            StrategyType.BREAKOUT: "🔴",
        }[signal.strategy]

        logging.info("")
        logging.info(f"{strategy_icon} PAPER TRADE OPENED: {trade_id}")
        logging.info(f"  Pair: {signal.pair}")
        logging.info(f"  Strategy: {signal.strategy.value.upper()}")
        logging.info(f"  Entry: ${signal.entry:.6f}")
        logging.info(f"  Stop: ${signal.stop:.6f} ({-signal.risk_pct:.1f}%)")
        logging.info(f"  Target: ${signal.target:.6f} (+{signal.reward_pct:.1f}%)")
        logging.info(f"  Size: {shares:.2f} units = ${position_size:.2f}")
        logging.info(
            f"  Risk: ${risk_dollars:.2f} | Reward: ${reward_dollars:.2f} (1:{signal.risk_reward_ratio:.1f})"
        )
        logging.info(f"  Capital remaining: ${self.capital:.2f}")
        logging.info("")

    async def monitor_open_trades(self):
        """Monitor and close trades when targets/stops hit."""
        if not self.open_trades:
            return

        for trade_id, trade in list(self.open_trades.items()):
            try:
                # Get current price
                current_price = await self.exchange_service.get_current_price(
                    trade["pair"]
                )

                ((current_price - trade["entry"]) / trade["entry"]) * 100
                (current_price - trade["entry"]) * trade["shares"]

                # Check stop loss
                if current_price <= trade["stop"]:
                    self.close_trade(trade_id, current_price, "STOP LOSS")

                # Check target
                elif current_price >= trade["target"]:
                    self.close_trade(trade_id, current_price, "TARGET HIT")

            except Exception as e:
                logging.error(f"Error monitoring {trade_id}: {e}")

    def close_trade(self, trade_id: str, exit_price: float, reason: str):
        """Close a paper trade."""
        trade = self.open_trades.pop(trade_id)

        # Calculate P&L
        pnl_dollars = (exit_price - trade["entry"]) * trade["shares"]
        pnl_pct = ((exit_price - trade["entry"]) / trade["entry"]) * 100

        # Return capital + P&L
        self.capital += trade["position_size"] + pnl_dollars

        # Record trade
        trade["exit"] = exit_price
        trade["closed_at"] = datetime.now()
        trade["pnl_dollars"] = pnl_dollars
        trade["pnl_pct"] = pnl_pct
        trade["reason"] = reason

        self.trade_history.append(trade)

        result_icon = "✅" if pnl_dollars > 0 else "❌"

        logging.info("")
        logging.info(f"{result_icon} TRADE CLOSED: {trade_id} - {reason}")
        logging.info(f"  Pair: {trade['pair']}")
        logging.info(f"  Entry: ${trade['entry']:.6f} → Exit: ${exit_price:.6f}")
        logging.info(f"  P&L: ${pnl_dollars:+.2f} ({pnl_pct:+.2f}%)")
        logging.info(f"  Capital: ${self.capital:.2f}")
        logging.info("")

        # Print stats
        self.print_stats()

    def print_stats(self):
        """Print trading statistics."""
        if not self.trade_history:
            return

        total_trades = len(self.trade_history)
        wins = sum(1 for t in self.trade_history if t["pnl_dollars"] > 0)
        losses = total_trades - wins
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

        total_pnl = sum(t["pnl_dollars"] for t in self.trade_history)
        roi = ((self.capital - self.initial_capital) / self.initial_capital) * 100

        logging.info("=" * 60)
        logging.info("TRADING STATS")
        logging.info("=" * 60)
        logging.info(f"Total Trades: {total_trades} ({wins}W - {losses}L)")
        logging.info(f"Win Rate: {win_rate:.1f}%")
        logging.info(f"Total P&L: ${total_pnl:+.2f}")
        logging.info(f"Capital: ${self.initial_capital:.2f} → ${self.capital:.2f}")
        logging.info(f"ROI: {roi:+.2f}%")
        logging.info("=" * 60)

    async def run(self):
        """Main trading loop."""
        logging.info("Starting Triple-Threat Trader...")
        logging.info("Press Ctrl+C to stop")
        logging.info("")

        while True:
            try:
                # Scan for opportunities
                await self.scan_all_strategies()

                # Monitor open trades
                await self.monitor_open_trades()

                # Wait 60 seconds
                await asyncio.sleep(60)

            except KeyboardInterrupt:
                logging.info("Shutting down...")
                self.print_stats()
                break
            except Exception as e:
                logging.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(60)


async def main():
    """Entry point."""
    from dotenv import load_dotenv

    load_dotenv()  # Load API keys from .env file

    trader = TripleThreatTrader(
        capital=3000.0,
        max_risk_per_trade=0.02,  # 2%
        max_concurrent=7,  # Increased to catch more opportunities
    )

    await trader.run()


if __name__ == "__main__":
    asyncio.run(main())
