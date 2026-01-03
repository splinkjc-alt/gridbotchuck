"""
Auto-Portfolio Manager for GridBot Chuck
==========================================

Autonomous multi-pair trading manager that:
- Monitors multiple pairs in real-time
- Analyzes entry signals using RSI, price position, and volume
- Waits for optimal entry conditions before entering trades
- Automatically allocates capital across best opportunities
- Prioritizes top-ranked pairs but jumps on excellent signals

Smart Prioritization:
1. EXCELLENT signals (any rank) - Best opportunities anywhere
2. Top 3 ranked pairs with GOOD+ signals - Proven performers
3. Others ranked by score - Backup opportunities
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from typing import Any

from core.services.exchange_interface import ExchangeInterface
from strategies.entry_signals import EntrySignal, EntrySignalAnalyzer
from strategies.pair_scanner import PairScanner, PairScanResult


class PositionStatus(Enum):
    """Status of a portfolio position."""

    PENDING = "pending"  # Waiting for entry signal
    ENTERING = "entering"  # Entry order placed
    ACTIVE = "active"  # Grid trading active
    EXITING = "exiting"  # Exit in progress
    CLOSED = "closed"  # Position closed
    ERROR = "error"  # Error state


@dataclass
class PortfolioPosition:
    """Represents a position in the portfolio."""

    pair: str
    status: PositionStatus = PositionStatus.PENDING

    # Capital allocation
    allocated_capital: float = 0.0
    entry_price: float = 0.0
    current_price: float = 0.0

    # Entry signal that triggered position
    entry_signal: EntrySignal | None = None
    scan_result: PairScanResult | None = None

    # Grid configuration
    grid_top: float = 0.0
    grid_bottom: float = 0.0
    num_grids: int = 6

    # Performance tracking
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    trades_count: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    entered_at: datetime | None = None
    closed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API/display."""
        return {
            "pair": self.pair,
            "status": self.status.value,
            "allocated_capital": round(self.allocated_capital, 2),
            "entry_price": round(self.entry_price, 6),
            "current_price": round(self.current_price, 6),
            "entry_signal": self.entry_signal.to_dict() if self.entry_signal else None,
            "grid": {
                "top": self.grid_top,
                "bottom": self.grid_bottom,
                "num_grids": self.num_grids,
            },
            "performance": {
                "realized_pnl": round(self.realized_pnl, 2),
                "unrealized_pnl": round(self.unrealized_pnl, 2),
                "total_pnl": round(self.realized_pnl + self.unrealized_pnl, 2),
                "trades_count": self.trades_count,
            },
            "timestamps": {
                "created_at": self.created_at.isoformat(),
                "entered_at": self.entered_at.isoformat() if self.entered_at else None,
                "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            },
        }


@dataclass
class PortfolioState:
    """Current state of the auto-portfolio."""

    total_capital: float
    deployed_capital: float = 0.0
    available_capital: float = 0.0

    max_positions: int = 5
    active_positions: int = 0

    positions: list[PortfolioPosition] = field(default_factory=list)

    # Performance
    total_realized_pnl: float = 0.0
    total_unrealized_pnl: float = 0.0

    # Status
    is_running: bool = False
    scan_cycle: int = 0
    last_scan_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API/display."""
        return {
            "capital": {
                "total": round(self.total_capital, 2),
                "deployed": round(self.deployed_capital, 2),
                "available": round(self.available_capital, 2),
            },
            "positions": {
                "max": self.max_positions,
                "active": self.active_positions,
                "list": [p.to_dict() for p in self.positions],
            },
            "performance": {
                "realized_pnl": round(self.total_realized_pnl, 2),
                "unrealized_pnl": round(self.total_unrealized_pnl, 2),
                "total_pnl": round(self.total_realized_pnl + self.total_unrealized_pnl, 2),
            },
            "status": {
                "is_running": self.is_running,
                "scan_cycle": self.scan_cycle,
                "last_scan_at": self.last_scan_at.isoformat() if self.last_scan_at else None,
            },
        }


class AutoPortfolioManager:
    """
    Autonomous portfolio manager for grid trading.

    Manages multiple trading pairs simultaneously, allocating capital
    based on entry signals and pair suitability scores.
    """

    # Configuration
    DEFAULT_SCAN_INTERVAL = 300  # 5 minutes between scans
    DEFAULT_MIN_ENTRY_SCORE = 65
    DEFAULT_POSITION_SIZE_PCT = 0.20  # 20% of capital per position

    def __init__(
        self,
        exchange_service: ExchangeInterface,
        total_capital: float = 500.0,
        max_positions: int = 5,
        min_entry_score: float = 65,
        scan_interval: int = 300,
        on_position_entered: Callable[[PortfolioPosition], None] | None = None,
        on_position_closed: Callable[[PortfolioPosition], None] | None = None,
    ):
        """
        Initialize the auto-portfolio manager.

        Args:
            exchange_service: Exchange service for market data
            total_capital: Total capital to deploy
            max_positions: Maximum simultaneous positions
            min_entry_score: Minimum signal score to enter (0-100)
            scan_interval: Seconds between scan cycles
            on_position_entered: Callback when position is entered
            on_position_closed: Callback when position is closed
        """
        self.exchange_service = exchange_service
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize components
        self.pair_scanner = PairScanner(exchange_service)
        self.signal_analyzer = EntrySignalAnalyzer()

        # Configuration
        self.scan_interval = scan_interval
        self.min_entry_score = min_entry_score

        # Portfolio state
        self.state = PortfolioState(
            total_capital=total_capital,
            available_capital=total_capital,
            max_positions=max_positions,
        )

        # Callbacks
        self.on_position_entered = on_position_entered
        self.on_position_closed = on_position_closed

        # Control
        self._running = False
        self._stop_event = asyncio.Event()

        # Cache
        self._scan_results: list[PairScanResult] = []
        self._monitored_pairs: list[str] = []

    async def start(
        self,
        pairs: list[str] | None = None,
        quote_currency: str = "USD",
        num_pairs: int = 10,
    ) -> None:
        """
        Start the auto-portfolio manager.

        Args:
            pairs: Specific pairs to monitor (None = auto-scan)
            quote_currency: Quote currency for pair scanning
            num_pairs: Number of pairs to monitor
        """
        if self._running:
            self.logger.warning("Auto-portfolio manager already running")
            return

        self.logger.info(
            f"Starting Auto-Portfolio Manager: "
            f"Capital=${self.state.total_capital:.2f}, "
            f"Max Positions={self.state.max_positions}, "
            f"Min Entry Score={self.min_entry_score}"
        )

        self._running = True
        self.state.is_running = True
        self._stop_event.clear()

        try:
            # Initial scan to find pairs
            if pairs:
                self._monitored_pairs = pairs
            else:
                self.logger.info("Running initial pair scan...")
                self._scan_results = await self.pair_scanner.scan_pairs(
                    quote_currency=quote_currency,
                    max_results=num_pairs,
                )
                self._monitored_pairs = [r.pair for r in self._scan_results]
                self.pair_scanner.print_scan_results(self._scan_results)

            self.logger.info(f"Monitoring {len(self._monitored_pairs)} pairs")

            # Main loop
            await self._run_loop()

        except asyncio.CancelledError:
            self.logger.info("Auto-portfolio manager cancelled")
        except Exception as e:
            self.logger.error(f"Error in auto-portfolio manager: {e}", exc_info=True)
        finally:
            self._running = False
            self.state.is_running = False

    async def stop(self) -> None:
        """Stop the auto-portfolio manager."""
        self.logger.info("Stopping auto-portfolio manager...")
        self._stop_event.set()
        self._running = False

    async def _run_loop(self) -> None:
        """Main monitoring loop."""
        while self._running and not self._stop_event.is_set():
            try:
                self.state.scan_cycle += 1
                self.state.last_scan_at = datetime.utcnow()

                self.logger.info(f"\n{'=' * 60}")
                self.logger.info(f"Scan Cycle {self.state.scan_cycle}")
                self.logger.info(f"{'=' * 60}")

                # Check if we have capacity for new positions
                if self.state.active_positions < self.state.max_positions:
                    await self._scan_for_entries()
                else:
                    self.logger.info(f"At max positions ({self.state.active_positions}/{self.state.max_positions})")

                # Update existing positions
                await self._update_positions()

                # Print status
                self._print_status()

                # Wait for next cycle
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self.scan_interval)
                except TimeoutError:
                    pass  # Normal timeout, continue loop

            except Exception as e:
                self.logger.error(f"Error in scan cycle: {e}", exc_info=True)
                await asyncio.sleep(30)  # Wait before retrying

    async def _scan_for_entries(self) -> None:
        """Scan monitored pairs for entry opportunities."""
        self.logger.info(f"Scanning {len(self._monitored_pairs)} pairs for entries...")

        # Get OHLCV data and analyze signals for all pairs
        signals: list[EntrySignal] = []

        for pair in self._monitored_pairs:
            # Skip pairs we already have positions in
            if any(
                p.pair == pair and p.status in (PositionStatus.ACTIVE, PositionStatus.ENTERING)
                for p in self.state.positions
            ):
                continue

            try:
                # Fetch data
                ohlcv = await self.exchange_service.fetch_ohlcv_simple(pair, "1h", 100)
                if ohlcv is None or len(ohlcv) < 24:
                    continue

                # Get grid range from scan results or calculate
                scan_result = next((r for r in self._scan_results if r.pair == pair), None)
                if scan_result:
                    grid_top = scan_result.suggested_grid_top
                    grid_bottom = scan_result.suggested_grid_bottom
                    grid_score = scan_result.total_score
                else:
                    # Calculate grid range from recent data
                    grid_top = float(ohlcv["high"].tail(168).max()) * 1.02
                    grid_bottom = float(ohlcv["low"].tail(168).min()) * 0.98
                    grid_score = 50.0  # Default score

                # Analyze entry signal
                signal = self.signal_analyzer.analyze_entry(
                    pair=pair,
                    ohlcv_data=ohlcv,
                    grid_top=grid_top,
                    grid_bottom=grid_bottom,
                    grid_suitability_score=grid_score,
                    min_entry_score=self.min_entry_score,
                )

                signals.append(signal)

                self.logger.info(
                    f"  {pair}: Score={signal.score:.1f} ({signal.strength.value}), "
                    f"RSI={signal.rsi:.0f}, Position={signal.price_position_pct:.0f}%"
                )

            except Exception as e:
                self.logger.warning(f"Error analyzing {pair}: {e}")

        # Get best entries
        best_entries = self.signal_analyzer.get_best_entries(
            signals,
            max_positions=self.state.max_positions - self.state.active_positions,
            prioritize_excellent=True,
        )

        # Enter positions
        for signal in best_entries:
            if self.state.active_positions >= self.state.max_positions:
                break

            if self.state.available_capital < self._calculate_position_size():
                self.logger.warning("Insufficient capital for new position")
                break

            await self._enter_position(signal)

    async def _enter_position(self, signal: EntrySignal) -> None:
        """Enter a new position based on entry signal."""
        position_size = self._calculate_position_size()

        self.logger.info(f"\n{'*' * 40}")
        self.logger.info(f"ENTERING POSITION: {signal.pair}")
        self.logger.info(f"  Signal Score: {signal.score:.1f} ({signal.strength.value})")
        self.logger.info(f"  Capital: ${position_size:.2f}")
        self.logger.info(f"  Entry Price: ${signal.current_price:.6f}")
        self.logger.info(f"  Reason: {signal.reason}")
        self.logger.info(f"{'*' * 40}\n")

        # Get scan result for grid config
        scan_result = next((r for r in self._scan_results if r.pair == signal.pair), None)

        # Create position
        position = PortfolioPosition(
            pair=signal.pair,
            status=PositionStatus.ACTIVE,
            allocated_capital=position_size,
            entry_price=signal.current_price,
            current_price=signal.current_price,
            entry_signal=signal,
            scan_result=scan_result,
            grid_top=signal.grid_top,
            grid_bottom=signal.grid_bottom,
            num_grids=scan_result.suggested_num_grids if scan_result else 6,
            entered_at=datetime.utcnow(),
        )

        # Update portfolio state
        self.state.positions.append(position)
        self.state.active_positions += 1
        self.state.deployed_capital += position_size
        self.state.available_capital -= position_size

        # Callback
        if self.on_position_entered:
            self.on_position_entered(position)

    async def _update_positions(self) -> None:
        """Update prices and PnL for active positions."""
        for position in self.state.positions:
            if position.status != PositionStatus.ACTIVE:
                continue

            try:
                current_price = await self.exchange_service.get_current_price(position.pair)
                position.current_price = current_price

                # Calculate unrealized PnL (simplified)
                price_change_pct = (current_price - position.entry_price) / position.entry_price
                position.unrealized_pnl = position.allocated_capital * price_change_pct

            except Exception as e:
                self.logger.warning(f"Error updating {position.pair}: {e}")

        # Update totals
        self.state.total_unrealized_pnl = sum(
            p.unrealized_pnl for p in self.state.positions if p.status == PositionStatus.ACTIVE
        )

    def _calculate_position_size(self) -> float:
        """Calculate position size for a new entry."""
        # Equal allocation per position
        return self.state.total_capital / self.state.max_positions

    def _print_status(self) -> None:
        """Print current portfolio status."""

        for position in self.state.positions:
            if position.status == PositionStatus.ACTIVE:
                (
                    (position.unrealized_pnl / position.allocated_capital) * 100
                    if position.allocated_capital > 0
                    else 0
                )


    async def close_position(self, pair: str) -> bool:
        """
        Close a specific position.

        Args:
            pair: Trading pair to close

        Returns:
            True if position was closed
        """
        position = next((p for p in self.state.positions if p.pair == pair and p.status == PositionStatus.ACTIVE), None)

        if not position:
            self.logger.warning(f"No active position found for {pair}")
            return False

        position.status = PositionStatus.CLOSED
        position.closed_at = datetime.utcnow()

        # Update state
        self.state.active_positions -= 1
        self.state.deployed_capital -= position.allocated_capital
        self.state.available_capital += position.allocated_capital + position.unrealized_pnl
        self.state.total_realized_pnl += position.unrealized_pnl

        position.realized_pnl = position.unrealized_pnl
        position.unrealized_pnl = 0

        self.logger.info(f"Closed position in {pair}: PnL=${position.realized_pnl:+.2f}")

        if self.on_position_closed:
            self.on_position_closed(position)

        return True

    async def close_all_positions(self) -> int:
        """
        Close all active positions.

        Returns:
            Number of positions closed
        """
        closed = 0
        for position in self.state.positions:
            if position.status == PositionStatus.ACTIVE and await self.close_position(position.pair):
                closed += 1
        return closed

    def get_state(self) -> dict[str, Any]:
        """Get current portfolio state as dictionary."""
        return self.state.to_dict()

    def save_state(self, filepath: str = "portfolio_state.json") -> None:
        """Save portfolio state to file."""
        with open(filepath, "w") as f:
            json.dump(self.get_state(), f, indent=2, default=str)
        self.logger.info(f"Portfolio state saved to {filepath}")

    @classmethod
    def load_state(cls, filepath: str) -> dict[str, Any] | None:
        """Load portfolio state from file."""
        try:
            with open(filepath) as f:
                return json.load(f)
        except FileNotFoundError:
            return None


async def run_auto_portfolio(
    exchange_service: ExchangeInterface,
    total_capital: float = 500.0,
    max_positions: int = 5,
    min_entry_score: float = 65,
    scan_interval: int = 300,
    quote_currency: str = "USD",
    num_pairs: int = 10,
    min_volume_24h: float = 500000,
    duration_minutes: int | None = None,
) -> PortfolioState:
    """
    Convenience function to run the auto-portfolio manager.

    Args:
        exchange_service: Exchange service instance
        total_capital: Total capital to deploy
        max_positions: Maximum simultaneous positions
        min_entry_score: Minimum signal score to enter
        scan_interval: Seconds between scan cycles
        quote_currency: Quote currency for pair scanning
        num_pairs: Number of pairs to monitor
        min_volume_24h: Minimum 24h volume for active pairs (default $500k)
        duration_minutes: How long to run (None = indefinitely)

    Returns:
        Final portfolio state
    """
    manager = AutoPortfolioManager(
        exchange_service=exchange_service,
        total_capital=total_capital,
        max_positions=max_positions,
        min_entry_score=min_entry_score,
        scan_interval=scan_interval,
    )

    async def run_with_timeout():
        await manager.start(
            quote_currency=quote_currency,
            num_pairs=num_pairs,
            min_volume_24h=min_volume_24h,
        )

    if duration_minutes:
        try:
            await asyncio.wait_for(run_with_timeout(), timeout=duration_minutes * 60)
        except TimeoutError:
            await manager.stop()
    else:
        # Run indefinitely until interrupted
        try:
            await run_with_timeout()
        except KeyboardInterrupt:
            await manager.stop()

    return manager.state
