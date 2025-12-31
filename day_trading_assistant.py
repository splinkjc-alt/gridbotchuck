"""
Day Trading Assistant for GridBot Chuck
========================================

AI-powered trading assistant that:
1. Scans markets continuously
2. Identifies high-probability trading opportunities
3. Presents trade setups for manual approval
4. Tracks paper trading performance
5. Measures win rate toward 60% goal

Configuration:
- Virtual balance: $10,000
- Position size: $200-500 per trade
- Alert threshold: Score >= 65
- Mode: Paper trading (no real money)
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from config.config_manager import ConfigManager
from config.config_validator import ConfigValidator
from config.trading_mode import TradingMode
from core.services.exchange_service_factory import ExchangeServiceFactory
from strategies.market_analyzer import MarketAnalyzer, CoinAnalysis, TrendSignal
from strategies.candlestick_patterns import detect_patterns


class TradeAction(Enum):
    """User decision on trade opportunity."""
    ACCEPT = "accept"
    DECLINE = "decline"
    WATCH = "watch"


class TradeStatus(Enum):
    """Status of a trade."""
    PENDING = "pending"
    OPEN = "open"
    CLOSED_WIN = "closed_win"
    CLOSED_LOSS = "closed_loss"
    STOPPED_OUT = "stopped_out"


@dataclass
class TradeOpportunity:
    """A trading opportunity detected by the assistant."""

    # Identification
    opportunity_id: str
    timestamp: datetime
    pair: str

    # Analysis
    analysis: CoinAnalysis
    patterns: dict[str, bool]

    # Trade parameters
    suggested_entry: float
    suggested_stop: float
    suggested_target: float
    suggested_position_size: float

    # Risk/Reward
    risk_dollars: float
    reward_dollars: float
    risk_reward_ratio: float

    # User decision
    user_action: Optional[TradeAction] = None

    def __str__(self) -> str:
        """Format opportunity for display."""
        bullish_patterns = [p for p, detected in self.patterns.items() if detected and 'bullish' in p]
        pattern_str = ", ".join(bullish_patterns) if bullish_patterns else "Momentum/Trend"

        return f"""
================================================================
  TRADING OPPORTUNITY #{self.opportunity_id}
================================================================
  Pair: {self.pair}
  Price: ${self.analysis.price:.4f}
  Score: {self.analysis.score:.1f}/100 ({self.analysis.signal.value.upper()})
  Pattern: {pattern_str}

  ----------- INDICATORS -----------
  RSI: {self.analysis.rsi:.1f} {'(Oversold)' if self.analysis.rsi < 35 else '(Overbought)' if self.analysis.rsi > 70 else ''}
  MACD: {'Bullish cross' if self.analysis.macd_bullish else 'No signal'}
  EMA: {'Above EMAs' if self.analysis.price_above_emas else 'Below EMAs'}
  Volume: {self.analysis.volume_score:.0f}/100
  24h Change: {self.analysis.change_24h_pct:+.2f}%

  ----------- TRADE SETUP ----------
  Entry:  ${self.suggested_entry:.4f}
  Stop:   ${self.suggested_stop:.4f} ({((self.suggested_stop/self.suggested_entry - 1) * 100):.1f}%)
  Target: ${self.suggested_target:.4f} ({((self.suggested_target/self.suggested_entry - 1) * 100):.1f}%)

  Position Size: ${self.suggested_position_size:.2f}
  Risk: ${self.risk_dollars:.2f}
  Reward: ${self.reward_dollars:.2f}
  R:R Ratio: 1:{self.risk_reward_ratio:.1f}

================================================================
  [A]ccept | [D]ecline | [W]atch
================================================================
"""


@dataclass
class PaperTrade:
    """A simulated trade in paper trading mode."""

    trade_id: str
    opportunity_id: str
    pair: str

    # Entry
    entry_time: datetime
    entry_price: float
    position_size_dollars: float
    quantity: float

    # Exit targets
    stop_loss: float
    take_profit: float

    # Status
    status: TradeStatus

    # Exit (if closed)
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl_dollars: Optional[float] = None
    pnl_percent: Optional[float] = None

    # Tracking for advanced exit logic
    last_significant_move_time: datetime = None
    highest_price_since_entry: float = 0.0

    def __post_init__(self):
        """Initialize tracking fields."""
        if self.last_significant_move_time is None:
            self.last_significant_move_time = self.entry_time
        if self.highest_price_since_entry == 0.0:
            self.highest_price_since_entry = self.entry_price

    def update_with_current_price(self, current_price: float, ema_9: Optional[float] = None) -> bool:
        """
        Check if stop, target, EMA cross, or time-based exit hit.
        Returns True if trade should close.
        """
        if self.status != TradeStatus.OPEN:
            return False

        # Update highest price tracker
        if current_price > self.highest_price_since_entry:
            self.highest_price_since_entry = current_price

        # Track significant price movements (>1% from entry)
        price_change_pct = abs((current_price / self.entry_price - 1) * 100)
        if price_change_pct >= 1.0:
            self.last_significant_move_time = datetime.now()

        # 1. Check EMA-based trailing stop (NEW!)
        if ema_9 is not None and current_price < ema_9:
            # Price crossed below 9-EMA = trend reversal
            self.close_trade(current_price, TradeStatus.STOPPED_OUT)
            return True

        # 2. Check traditional stop loss
        if current_price <= self.stop_loss:
            self.close_trade(current_price, TradeStatus.STOPPED_OUT)
            return True

        # 3. Check take profit
        if current_price >= self.take_profit:
            self.close_trade(current_price, TradeStatus.CLOSED_WIN)
            return True

        # 4. Check time-based exit (NEW!)
        # If no significant movement (>1%) in 6 hours, close position
        time_since_last_move = datetime.now() - self.last_significant_move_time
        if time_since_last_move.total_seconds() > (6 * 3600):  # 6 hours
            self.close_trade(current_price, TradeStatus.STOPPED_OUT)
            return True

        return False

    def close_trade(self, exit_price: float, status: TradeStatus):
        """Close the trade."""
        self.exit_time = datetime.now()
        self.exit_price = exit_price
        self.status = status

        # Calculate P&L
        self.pnl_dollars = (exit_price - self.entry_price) * self.quantity
        self.pnl_percent = ((exit_price / self.entry_price) - 1) * 100

    def __str__(self) -> str:
        """Format trade for display."""
        if self.status == TradeStatus.OPEN:
            return f"[OPEN] {self.pair} | Entry: ${self.entry_price:.4f} | Size: ${self.position_size_dollars:.0f}"
        else:
            win_label = "WIN" if self.pnl_dollars > 0 else "LOSS"
            return f"[{win_label}] [{self.status.value.upper()}] {self.pair} | P&L: ${self.pnl_dollars:+.2f} ({self.pnl_percent:+.1f}%)"


@dataclass
class TradingStats:
    """Performance statistics for paper trading."""

    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    stopped_out: int = 0

    total_pnl: float = 0.0
    total_fees: float = 0.0

    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0

    win_rate: float = 0.0
    profit_factor: float = 0.0

    trades_history: list[PaperTrade] = field(default_factory=list)

    def update(self, trade: PaperTrade):
        """Update stats with completed trade."""
        self.trades_history.append(trade)
        self.total_trades += 1

        if trade.pnl_dollars > 0:
            self.wins += 1
            self.avg_win = (self.avg_win * (self.wins - 1) + trade.pnl_dollars) / self.wins
            self.largest_win = max(self.largest_win, trade.pnl_dollars)
        else:
            if trade.status == TradeStatus.STOPPED_OUT:
                self.stopped_out += 1
            self.losses += 1
            self.avg_loss = (self.avg_loss * (self.losses - 1) + abs(trade.pnl_dollars)) / self.losses
            self.largest_loss = max(self.largest_loss, abs(trade.pnl_dollars))

        self.total_pnl += trade.pnl_dollars

        # Calculate win rate
        if self.total_trades > 0:
            self.win_rate = (self.wins / self.total_trades) * 100

        # Calculate profit factor
        total_wins = self.avg_win * self.wins if self.wins > 0 else 0
        total_losses = self.avg_loss * self.losses if self.losses > 0 else 0
        if total_losses > 0:
            self.profit_factor = total_wins / total_losses

    def __str__(self) -> str:
        """Format stats for display."""
        goal_status = " **GOAL MET!**" if self.win_rate >= 60 else f' (Target: 60%)'
        return f"""
================================================================
  PAPER TRADING PERFORMANCE
================================================================
  Total Trades: {self.total_trades}
  Wins: {self.wins} | Losses: {self.losses} | Stopped Out: {self.stopped_out}

  Win Rate: {self.win_rate:.1f}%{goal_status}
  Profit Factor: {self.profit_factor:.2f}

  Total P&L: ${self.total_pnl:+.2f}
  Avg Win: ${self.avg_win:+.2f}
  Avg Loss: ${self.avg_loss:+.2f}
  Largest Win: ${self.largest_win:+.2f}
  Largest Loss: ${self.largest_loss:+.2f}
================================================================
"""


class DayTradingAssistant:
    """
    AI-powered day trading assistant with paper trading.
    """

    def __init__(
        self,
        config_path: str,
        virtual_balance: float = 10000.0,
        position_size_min: float = 200.0,
        position_size_max: float = 500.0,
        score_threshold: float = 65.0,
        scan_interval_seconds: int = 60,
        auto_accept: bool = False,
        max_concurrent_trades: int = 3,
    ):
        """
        Initialize the trading assistant.

        Args:
            config_path: Path to GridBot config file
            virtual_balance: Starting paper trading balance
            position_size_min: Minimum position size per trade
            position_size_max: Maximum position size per trade
            score_threshold: Minimum score to alert (0-100)
            scan_interval_seconds: How often to scan markets
            auto_accept: If True, automatically accept all qualifying trades
            max_concurrent_trades: Maximum number of open trades at once
        """
        self.config_manager = ConfigManager(config_path, ConfigValidator())
        # Use LIVE mode for real-time price data (but paper trading for orders)
        self.trading_mode = TradingMode.PAPER_TRADING
        self.exchange_service = ExchangeServiceFactory.create_exchange_service(
            self.config_manager,
            self.trading_mode,
        )
        self.market_analyzer = MarketAnalyzer(self.exchange_service, self.config_manager)

        # Configuration
        self.virtual_balance = virtual_balance
        self.available_cash = virtual_balance
        self.position_size_min = position_size_min
        self.position_size_max = position_size_max
        self.score_threshold = score_threshold
        self.scan_interval = scan_interval_seconds
        self.auto_accept = auto_accept
        self.max_concurrent_trades = max_concurrent_trades

        # State
        self.open_trades: list[PaperTrade] = []
        self.opportunities: list[TradeOpportunity] = []
        self.stats = TradingStats()
        self.next_opportunity_id = 1
        self.next_trade_id = 1

        # Candidate pairs to scan (from config)
        self.candidate_pairs = self._load_candidate_pairs()

        logging.info(f"Day Trading Assistant initialized")
        logging.info(f"Virtual balance: ${self.virtual_balance:,.2f}")
        logging.info(f"Position size: ${self.position_size_min}-${self.position_size_max}")
        logging.info(f"Score threshold: {self.score_threshold}")
        logging.info(f"Scanning {len(self.candidate_pairs)} pairs every {self.scan_interval}s")

    def _load_candidate_pairs(self) -> list[str]:
        """Load candidate pairs from config."""
        # Try to get from market_scanner config
        try:
            scanner_config = self.config_manager.config.get("market_scanner", {})
            pairs = scanner_config.get("candidate_pairs", [])
            if pairs:
                return pairs
        except:
            pass

        # Default list of active crypto pairs
        return [
            "XRP/USD", "ADA/USD", "SOL/USD", "DOGE/USD", "MATIC/USD",
            "AVAX/USD", "DOT/USD", "LINK/USD", "ATOM/USD", "UNI/USD",
            "NEAR/USD", "APT/USD", "ARB/USD", "OP/USD", "FIL/USD",
            "0G/USD", "API3/USD", "FOLKS/USD", "DAG/USD", "CPOOL/USD",
        ]

    async def prompt_user_action(self, opportunity: TradeOpportunity) -> TradeAction:
        """
        Prompt user to accept, decline, or watch an opportunity.
        Uses asyncio executor to avoid blocking the event loop.
        """
        loop = asyncio.get_event_loop()

        while True:
            try:
                # Run input() in thread pool to avoid blocking
                response = await loop.run_in_executor(None, input, "")
                response = response.strip().upper()

                if response == 'A':
                    return TradeAction.ACCEPT
                elif response == 'D':
                    return TradeAction.DECLINE
                elif response == 'W':
                    return TradeAction.WATCH
                else:
                    print("Invalid input. Please enter A (Accept), D (Decline), or W (Watch): ", end='', flush=True)
            except Exception as e:
                logging.error(f"Error reading user input: {e}")
                return TradeAction.DECLINE

    def _calculate_mean_reversion_score(self, analysis) -> float:
        """
        Calculate mean reversion score (0-100).
        Higher score = better mean reversion setup.

        Focus on:
        - RSI oversold (< 30) or overbought (> 70)
        - Bollinger band bounces
        - High volatility (for action)
        """
        score = 0.0

        # 1. RSI Mean Reversion (40 points max)
        rsi = analysis.rsi
        if rsi < 30:
            # Oversold - BUY signal
            score += 40 * (30 - rsi) / 30  # More oversold = higher score
        elif rsi > 70:
            # Overbought - potential short (skip for now, only do longs)
            score += 0  # We're only doing long trades

        # 2. Bollinger Band Position (30 points max)
        bb_score = analysis.bollinger_score
        if bb_score >= 80:  # Near lower band (oversold)
            score += 30
        elif bb_score >= 60:
            score += 20

        # 3. Volume (confirms move) (20 points max)
        score += analysis.volume_score * 0.20

        # 4. CCI oversold confirmation (10 points max)
        if analysis.cci < -100:  # Oversold
            score += 10

        return min(score, 100)

    async def scan_for_opportunities(self):
        """Scan all pairs for MEAN REVERSION opportunities."""
        logging.info(f"Scanning {len(self.candidate_pairs)} pairs for mean reversion setups...")

        opportunities_found = 0
        new_opportunities = []

        try:
            # Use MarketAnalyzer to analyze all pairs at once
            analyses = await self.market_analyzer.find_best_trading_pairs(
                candidate_pairs=self.candidate_pairs,
                timeframe="5m",  # 5-minute timeframe for quick reversals
                min_volume_threshold=100000,  # $100k 24h volume minimum
                min_price=0.01,
                max_price=100.0,
            )

            # MEAN REVERSION FILTER: Look for oversold conditions
            for analysis in analyses:
                # Calculate mean reversion score instead of trend score
                mr_score = self._calculate_mean_reversion_score(analysis)

                # Only take oversold setups (RSI < 45 as starting filter)
                if analysis.rsi < 45 and mr_score >= self.score_threshold:
                    # Create opportunity with mean reversion score
                    opportunity = self._create_opportunity(analysis.pair, analysis)
                    # Override score with mean reversion score
                    opportunity.analysis.score = mr_score
                    new_opportunities.append(opportunity)
                    opportunities_found += 1

                    logging.info(f"MEAN REVERSION: {analysis.pair} - RSI:{analysis.rsi:.1f}, MR Score:{mr_score:.1f}")

        except Exception as e:
            logging.error(f"Error in scan_for_opportunities: {e}", exc_info=True)

        logging.info(f"Scan complete. Found {opportunities_found} opportunities (score >= {self.score_threshold})")

        # Present each opportunity and handle based on auto_accept mode
        for opportunity in new_opportunities:
            print(opportunity)

            # Check if we can accept more trades
            can_accept = len(self.open_trades) < self.max_concurrent_trades

            if self.auto_accept and can_accept:
                # Auto-accept mode
                try:
                    trade = self.accept_trade(opportunity)
                    opportunity.user_action = TradeAction.ACCEPT
                    print(f"\n>>> AUTO-ACCEPTED! Opened {trade.trade_id} for {trade.pair}\n")
                    logging.info(f"Auto-accepted trade: {trade.trade_id} - {trade.pair}")
                except Exception as e:
                    print(f"\n>>> ERROR: Could not accept trade: {e}\n")
                    logging.error(f"Error accepting trade: {e}")
                    opportunity.user_action = TradeAction.DECLINE
            elif self.auto_accept and not can_accept:
                # Max concurrent trades reached
                print(f"\n>>> SKIPPED: Max concurrent trades ({self.max_concurrent_trades}) reached\n")
                opportunity.user_action = TradeAction.DECLINE
            else:
                # Interactive mode
                action = await self.prompt_user_action(opportunity)
                opportunity.user_action = action

                if action == TradeAction.ACCEPT:
                    try:
                        trade = self.accept_trade(opportunity)
                        print(f"\n>>> TRADE ACCEPTED! Opened {trade.trade_id} for {trade.pair}\n")
                    except Exception as e:
                        print(f"\n>>> ERROR: Could not accept trade: {e}\n")
                        logging.error(f"Error accepting trade: {e}")
                elif action == TradeAction.DECLINE:
                    print(f"\n>>> Trade declined for {opportunity.pair}\n")
                elif action == TradeAction.WATCH:
                    self.opportunities.append(opportunity)
                    print(f"\n>>> Added {opportunity.pair} to watchlist\n")

        return opportunities_found


    def _create_opportunity(self, pair: str, analysis: CoinAnalysis) -> TradeOpportunity:
        """Create a trade opportunity from analysis."""
        current_price = analysis.price

        # Detect candlestick patterns
        # (Would need OHLCV data here - simplified for now)
        patterns = {}

        # MEAN REVERSION: Smaller targets, tighter stops
        # We're buying dips, so we want quick bounces (3-5%), not big trends
        if analysis.rsi < 40:  # Oversold mean reversion trade
            entry = current_price * 0.999  # Buy slightly below current (limit order)
            stop = current_price * 0.97    # 3% stop loss (tighter)
            target = current_price * 1.04  # 4% target (quick bounce)
        else:
            # Default conservative
            entry = current_price
            stop = current_price * 0.97
            target = current_price * 1.09

        # Calculate position size (based on risk %)
        risk_per_trade_pct = 0.02  # 2% risk
        risk_dollars_max = self.virtual_balance * risk_per_trade_pct
        stop_distance_pct = abs((stop / entry) - 1)

        # Position size = risk / stop distance
        suggested_size = risk_dollars_max / stop_distance_pct if stop_distance_pct > 0 else self.position_size_min

        # Cap at min/max
        suggested_size = max(self.position_size_min, min(self.position_size_max, suggested_size))

        # Calculate risk/reward
        risk_dollars = suggested_size * stop_distance_pct
        reward_dollars = suggested_size * abs((target / entry) - 1)
        risk_reward = reward_dollars / risk_dollars if risk_dollars > 0 else 0

        opportunity_id = f"{self.next_opportunity_id:04d}"
        self.next_opportunity_id += 1

        return TradeOpportunity(
            opportunity_id=opportunity_id,
            timestamp=datetime.now(),
            pair=pair,
            analysis=analysis,
            patterns=patterns,
            suggested_entry=entry,
            suggested_stop=stop,
            suggested_target=target,
            suggested_position_size=suggested_size,
            risk_dollars=risk_dollars,
            reward_dollars=reward_dollars,
            risk_reward_ratio=risk_reward,
        )

    def accept_trade(self, opportunity: TradeOpportunity) -> PaperTrade:
        """Accept a trade opportunity and execute in paper trading mode."""
        if opportunity.suggested_position_size > self.available_cash:
            raise ValueError(f"Insufficient cash. Need ${opportunity.suggested_position_size:.2f}, have ${self.available_cash:.2f}")

        # Create paper trade
        quantity = opportunity.suggested_position_size / opportunity.suggested_entry

        trade = PaperTrade(
            trade_id=f"T{self.next_trade_id:04d}",
            opportunity_id=opportunity.opportunity_id,
            pair=opportunity.pair,
            entry_time=datetime.now(),
            entry_price=opportunity.suggested_entry,
            position_size_dollars=opportunity.suggested_position_size,
            quantity=quantity,
            stop_loss=opportunity.suggested_stop,
            take_profit=opportunity.suggested_target,
            status=TradeStatus.OPEN,
        )

        self.next_trade_id += 1
        self.open_trades.append(trade)
        self.available_cash -= opportunity.suggested_position_size

        logging.info(f"PAPER TRADE OPENED: {trade}")
        print(f"\n>> Trade opened: {trade}\n")

        return trade

    async def monitor_open_trades(self):
        """Monitor open trades and close if stop/target/EMA/time hit."""
        if not self.open_trades:
            return

        logging.debug(f"Monitoring {len(self.open_trades)} open trades...")

        for trade in self.open_trades[:]:  # Copy list to allow removal
            try:
                # Get current price
                current_price = await self.exchange_service.get_current_price(trade.pair)
                if not current_price:
                    continue

                # Get current EMA for trailing stop
                ema_9 = None
                try:
                    # Quick analysis to get current EMA
                    analysis_results = await self.market_analyzer.find_best_trading_pairs(
                        candidate_pairs=[trade.pair],
                        timeframe="5m",  # Match scanning timeframe
                        min_volume_threshold=0,
                        min_price=0,
                        max_price=1000000,
                    )
                    if analysis_results:
                        # Extract EMA from analysis (available in CoinAnalysis object)
                        # For now, use a simple calculation: EMA ~= price if above EMAs
                        # TODO: Access actual EMA value from analysis object if available
                        ema_9 = current_price * 0.98  # Conservative 2% trailing stop as proxy
                except Exception as e:
                    logging.debug(f"Could not fetch EMA for {trade.pair}: {e}")

                # Check if stop, target, EMA, or time-based exit hit
                if trade.update_with_current_price(current_price, ema_9):
                    # Trade closed
                    self.open_trades.remove(trade)
                    self.available_cash += trade.position_size_dollars + trade.pnl_dollars
                    self.stats.update(trade)

                    logging.info(f"Trade closed: {trade}")
                    print(f"\n{trade}\n")
                    print(self.stats)

            except Exception as e:
                logging.error(f"Error monitoring trade {trade.trade_id}: {e}")

    async def run(self):
        """Main loop: scan markets, present opportunities, monitor trades."""
        mode_str = "AUTO-ACCEPT MODE" if self.auto_accept else "INTERACTIVE MODE"
        print(f"""
================================================================
  DAY TRADING ASSISTANT - PAPER TRADING
================================================================
  Mode: {mode_str}
  Virtual Balance: ${self.virtual_balance:,.0f}
  Position Size: ${self.position_size_min:.0f}-${self.position_size_max:.0f} per trade
  Alert Threshold: Score >= {self.score_threshold}
  Max Concurrent: {self.max_concurrent_trades} trades
  Target Win Rate: 60%

  STATUS: Running... Scanning markets every {self.scan_interval} seconds
================================================================
""")

        while True:
            try:
                # Scan for new opportunities
                await self.scan_for_opportunities()

                # Monitor open trades
                await self.monitor_open_trades()

                # Show status
                print(f"\nCash: ${self.available_cash:.2f} | Open Trades: {len(self.open_trades)} | Stats: {self.stats.total_trades} trades, {self.stats.win_rate:.1f}% win rate\n")

                # Wait before next scan
                await asyncio.sleep(self.scan_interval)

            except KeyboardInterrupt:
                logging.info("Shutting down...")
                print("\n\nGoodbye! Final stats:")
                print(self.stats)
                break
            except Exception as e:
                logging.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(10)


async def main():
    """Run the day trading assistant."""
    from dotenv import load_dotenv
    load_dotenv()  # Load API keys from .env file

    config_path = "config/config.json"

    assistant = DayTradingAssistant(
        config_path=config_path,
        virtual_balance=10000.0,
        position_size_min=200.0,
        position_size_max=500.0,
        score_threshold=60.0,  # Mean reversion threshold (different scoring)
        scan_interval_seconds=60,
        auto_accept=True,  # Auto-accept trades for paper testing
        max_concurrent_trades=3,  # Limit to 3 open trades at once
    )

    await assistant.run()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    asyncio.run(main())
