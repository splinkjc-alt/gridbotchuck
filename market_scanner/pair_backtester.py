"""
Multi-Pair Backtester for Grid Trading
=======================================
Tests multiple coin pairs across timeframes and indicators
to find the best opportunities for grid trading.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json

import ccxt
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Results from backtesting a pair."""

    pair: str
    timeframe: str
    total_return_pct: float
    num_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    volatility: float
    avg_trade_pct: float
    grid_score: float  # Overall score for grid trading suitability
    best_range_pct: float  # Optimal grid range as % of price
    recommended_grids: int
    indicators: dict


class PairBacktester:
    """
    Backtests multiple pairs to find best grid trading opportunities.
    """

    # Popular trading pairs to test
    PAIRS_TO_TEST = [
        # Major coins
        "BTC/USD",
        "ETH/USD",
        "SOL/USD",
        "XRP/USD",
        "ADA/USD",
        "DOGE/USD",
        "AVAX/USD",
        "DOT/USD",
        "LINK/USD",
        "MATIC/USD",
        # High volatility
        "SHIB/USD",
        "PEPE/USD",
        "BONK/USD",
        "WIF/USD",
        # DeFi
        "UNI/USD",
        "AAVE/USD",
        "MKR/USD",
        "CRV/USD",
        # Layer 2
        "ARB/USD",
        "OP/USD",
        "IMX/USD",
        # Other popular
        "LTC/USD",
        "BCH/USD",
        "ATOM/USD",
        "NEAR/USD",
        "FTM/USD",
        "ALGO/USD",
        "XLM/USD",
        "VET/USD",
        "HBAR/USD",
        "ICP/USD",
    ]

    TIMEFRAMES = ["15m", "1h", "4h", "1d"]

    def __init__(self, exchange_id: str = "kraken"):
        self.exchange = getattr(ccxt, exchange_id)(
            {
                "enableRateLimit": True,
            }
        )
        self.results = []

    async def fetch_ohlcv(
        self, pair: str, timeframe: str, limit: int = 500
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data for a pair."""
        try:
            ohlcv = self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
            if not ohlcv:
                return None

            df = pd.DataFrame(
                ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            return df

        except Exception as e:
            logger.debug(f"Could not fetch {pair}: {e}")
            return None

    def calculate_indicators(self, df: pd.DataFrame) -> dict:
        """Calculate technical indicators for analysis."""
        indicators = {}

        # RSI
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        indicators["rsi"] = (100 - (100 / (1 + rs))).iloc[-1]
        indicators["rsi_avg"] = (100 - (100 / (1 + rs))).mean()

        # Bollinger Bands
        sma20 = df["close"].rolling(20).mean()
        std20 = df["close"].rolling(20).std()
        indicators["bb_width"] = ((std20 * 4) / sma20 * 100).mean()  # Avg BB width as %

        # Volatility (ATR-based)
        high_low = df["high"] - df["low"]
        high_close = abs(df["high"] - df["close"].shift())
        low_close = abs(df["low"] - df["close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        indicators["atr_pct"] = (atr / df["close"] * 100).mean()

        # Price range analysis
        indicators["range_pct"] = (
            (df["high"].max() - df["low"].min()) / df["close"].mean() * 100
        )
        indicators["daily_range_pct"] = (
            (df["high"] - df["low"]) / df["close"] * 100
        ).mean()

        # Trend strength (ADX approximation)
        plus_dm = df["high"].diff()
        minus_dm = -df["low"].diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

        atr14 = tr.rolling(14).mean()
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr14)
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr14)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        indicators["adx"] = dx.rolling(14).mean().iloc[-1]

        # Volume analysis
        indicators["volume_ratio"] = (
            df["volume"].iloc[-20:].mean() / df["volume"].mean()
        )

        # Mean reversion tendency
        returns = df["close"].pct_change()
        indicators["mean_reversion"] = -returns.autocorr(
            lag=1
        )  # Negative autocorr = mean reverting

        return indicators

    def simulate_grid_trading(
        self, df: pd.DataFrame, grid_count: int = 6, range_pct: float = 5.0
    ) -> dict:
        """
        Simulate grid trading on historical data.

        Args:
            df: OHLCV dataframe
            grid_count: Number of grid levels
            range_pct: Grid range as percentage of mid price
        """
        prices = df["close"].values
        mid_price = prices.mean()

        # Set up grid
        range_half = mid_price * (range_pct / 100) / 2
        grid_low = mid_price - range_half
        grid_high = mid_price + range_half
        grid_step = (grid_high - grid_low) / grid_count

        # Grid levels
        buy_levels = [grid_low + i * grid_step for i in range(grid_count)]
        sell_levels = [grid_low + (i + 1) * grid_step for i in range(grid_count)]

        # Simulate
        position = 0
        cash = 10000
        initial_cash = cash
        trades = []
        peak_value = cash

        for i, price in enumerate(prices):
            portfolio_value = cash + position * price

            # Track drawdown
            if portfolio_value > peak_value:
                peak_value = portfolio_value

            # Check buy levels
            for j, buy_price in enumerate(buy_levels):
                if price <= buy_price and cash >= buy_price:
                    # Buy
                    qty = (cash * 0.1) / price  # 10% of cash per grid
                    cost = qty * price
                    if cost <= cash:
                        cash -= cost
                        position += qty
                        trades.append(
                            {"type": "buy", "price": price, "qty": qty, "idx": i}
                        )

            # Check sell levels
            for j, sell_price in enumerate(sell_levels):
                if price >= sell_price and position > 0:
                    # Sell
                    qty = min(position, position * 0.2)  # Sell 20% of position
                    revenue = qty * price
                    cash += revenue
                    position -= qty
                    trades.append(
                        {"type": "sell", "price": price, "qty": qty, "idx": i}
                    )

        # Final portfolio value
        final_value = cash + position * prices[-1]
        total_return = (final_value - initial_cash) / initial_cash * 100

        # Calculate metrics
        buy_trades = [t for t in trades if t["type"] == "buy"]
        sell_trades = [t for t in trades if t["type"] == "sell"]

        # Win rate (simplified - sells above avg buy price)
        if buy_trades and sell_trades:
            avg_buy = sum(t["price"] for t in buy_trades) / len(buy_trades)
            wins = sum(1 for t in sell_trades if t["price"] > avg_buy)
            win_rate = wins / len(sell_trades) * 100 if sell_trades else 0
        else:
            win_rate = 0

        # Max drawdown
        max_dd = 0
        running_max = initial_cash
        portfolio_values = []
        pos = 0
        c = initial_cash
        for i, price in enumerate(prices):
            # Rough portfolio tracking
            val = c + pos * price
            portfolio_values.append(val)
            if val > running_max:
                running_max = val
            dd = (running_max - val) / running_max * 100
            if dd > max_dd:
                max_dd = dd

        # Sharpe ratio (simplified)
        if len(portfolio_values) > 1:
            returns = pd.Series(portfolio_values).pct_change().dropna()
            if returns.std() > 0:
                sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
            else:
                sharpe = 0
        else:
            sharpe = 0

        return {
            "total_return_pct": total_return,
            "num_trades": len(trades),
            "win_rate": win_rate,
            "max_drawdown": max_dd,
            "sharpe_ratio": sharpe,
            "avg_trade_pct": total_return / len(trades) if trades else 0,
        }

    def calculate_grid_score(self, indicators: dict, sim_results: dict) -> float:
        """
        Calculate overall grid trading suitability score (0-100).

        Factors:
        - High volatility (good for grids)
        - Mean reversion tendency (very good for grids)
        - Moderate ADX (too trendy = bad for grids)
        - Good backtest results
        """
        score = 0

        # Volatility score (0-25) - higher is better for grids
        vol = indicators.get("atr_pct", 0)
        if vol > 5:
            score += 25
        elif vol > 3:
            score += 20
        elif vol > 2:
            score += 15
        elif vol > 1:
            score += 10
        else:
            score += 5

        # Mean reversion score (0-25) - higher is better
        mr = indicators.get("mean_reversion", 0)
        if mr > 0.2:
            score += 25
        elif mr > 0.1:
            score += 20
        elif mr > 0:
            score += 15
        elif mr > -0.1:
            score += 10
        else:
            score += 5

        # ADX score (0-20) - moderate is best (not too trendy)
        adx = indicators.get("adx", 25)
        if 15 <= adx <= 30:
            score += 20  # Ideal range
        elif 10 <= adx <= 40:
            score += 15
        elif adx < 10:
            score += 10  # Too flat
        else:
            score += 5  # Too trendy

        # Backtest performance score (0-30)
        ret = sim_results.get("total_return_pct", 0)
        if ret > 10:
            score += 30
        elif ret > 5:
            score += 25
        elif ret > 2:
            score += 20
        elif ret > 0:
            score += 15
        elif ret > -2:
            score += 10
        else:
            score += 5

        return min(100, score)

    async def backtest_pair(
        self, pair: str, timeframe: str = "1h"
    ) -> Optional[BacktestResult]:
        """Run full backtest on a single pair."""
        logger.info(f"Testing {pair} on {timeframe}...")

        df = await self.fetch_ohlcv(pair, timeframe, limit=500)
        if df is None or len(df) < 100:
            return None

        # Calculate indicators
        indicators = self.calculate_indicators(df)

        # Determine optimal range based on volatility
        optimal_range = min(20, max(3, indicators["atr_pct"] * 3))

        # Simulate grid trading
        sim_results = self.simulate_grid_trading(
            df, grid_count=6, range_pct=optimal_range
        )

        # Calculate grid score
        grid_score = self.calculate_grid_score(indicators, sim_results)

        # Recommended grid count based on range
        if optimal_range > 10:
            rec_grids = 8
        elif optimal_range > 5:
            rec_grids = 6
        else:
            rec_grids = 4

        return BacktestResult(
            pair=pair,
            timeframe=timeframe,
            total_return_pct=sim_results["total_return_pct"],
            num_trades=sim_results["num_trades"],
            win_rate=sim_results["win_rate"],
            max_drawdown=sim_results["max_drawdown"],
            sharpe_ratio=sim_results["sharpe_ratio"],
            volatility=indicators["atr_pct"],
            avg_trade_pct=sim_results["avg_trade_pct"],
            grid_score=grid_score,
            best_range_pct=optimal_range,
            recommended_grids=rec_grids,
            indicators=indicators,
        )

    async def run_full_scan(
        self, pairs: list = None, timeframes: list = None
    ) -> list[BacktestResult]:
        """
        Run backtest on all pairs and timeframes.

        Returns sorted list of results (best first).
        """
        pairs = pairs or self.PAIRS_TO_TEST
        timeframes = timeframes or ["1h"]  # Default to 1h for speed

        results = []
        total = len(pairs) * len(timeframes)
        completed = 0

        for pair in pairs:
            for tf in timeframes:
                try:
                    result = await self.backtest_pair(pair, tf)
                    if result:
                        results.append(result)
                        logger.info(
                            f"  {pair} ({tf}): Score={result.grid_score:.0f}, "
                            f"Return={result.total_return_pct:.1f}%, "
                            f"Volatility={result.volatility:.1f}%"
                        )
                except Exception as e:
                    logger.debug(f"Error testing {pair}: {e}")

                completed += 1
                if completed % 10 == 0:
                    logger.info(f"Progress: {completed}/{total} pairs tested")

                # Rate limiting
                await asyncio.sleep(0.5)

        # Sort by grid score
        results.sort(key=lambda x: x.grid_score, reverse=True)
        self.results = results

        return results

    def generate_report(self) -> str:
        """Generate a text report of backtest results."""
        if not self.results:
            return "No results available. Run scan first."

        report = []
        report.append("=" * 80)
        report.append("GRID TRADING PAIR SCANNER - BACKTEST RESULTS")
        report.append("=" * 80)
        report.append("")

        # Top 10 pairs
        report.append("TOP 10 PAIRS FOR GRID TRADING:")
        report.append("-" * 80)
        report.append(
            f"{'Rank':<5} {'Pair':<12} {'Score':<7} {'Return%':<9} {'Vol%':<7} {'Trades':<7} {'Range%':<8} {'Grids':<6}"
        )
        report.append("-" * 80)

        for i, r in enumerate(self.results[:10], 1):
            report.append(
                f"{i:<5} {r.pair:<12} {r.grid_score:<7.0f} {r.total_return_pct:<9.1f} "
                f"{r.volatility:<7.1f} {r.num_trades:<7} {r.best_range_pct:<8.1f} {r.recommended_grids:<6}"
            )

        report.append("")

        # Best pick details
        if self.results:
            best = self.results[0]
            report.append("=" * 80)
            report.append(f"RECOMMENDED: {best.pair}")
            report.append("=" * 80)
            report.append(f"  Grid Score:        {best.grid_score:.0f}/100")
            report.append(f"  Backtest Return:   {best.total_return_pct:.1f}%")
            report.append(f"  Volatility (ATR):  {best.volatility:.1f}%")
            report.append(f"  Win Rate:          {best.win_rate:.0f}%")
            report.append(f"  Max Drawdown:      {best.max_drawdown:.1f}%")
            report.append(f"  Optimal Range:     {best.best_range_pct:.1f}%")
            report.append(f"  Recommended Grids: {best.recommended_grids}")
            report.append(
                f"  Mean Reversion:    {best.indicators.get('mean_reversion', 0):.2f}"
            )
            report.append(f"  ADX (trend):       {best.indicators.get('adx', 0):.1f}")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def save_results(self, filepath: str = "data/backtest_results.json"):
        """Save results to JSON file."""
        if not self.results:
            return

        data = []
        for r in self.results:
            data.append(
                {
                    "pair": r.pair,
                    "timeframe": r.timeframe,
                    "grid_score": r.grid_score,
                    "total_return_pct": r.total_return_pct,
                    "volatility": r.volatility,
                    "num_trades": r.num_trades,
                    "win_rate": r.win_rate,
                    "max_drawdown": r.max_drawdown,
                    "best_range_pct": r.best_range_pct,
                    "recommended_grids": r.recommended_grids,
                    "indicators": r.indicators,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Results saved to {filepath}")


async def main():
    """Run the pair scanner."""
    print("\n" + "=" * 60)
    print("GRID TRADING PAIR SCANNER")
    print("=" * 60 + "\n")

    scanner = PairBacktester(exchange_id="kraken")

    print("Scanning pairs on Kraken...")
    print("This will test multiple coins for grid trading suitability.\n")

    # Run scan
    results = await scanner.run_full_scan(timeframes=["1h"])

    # Print report
    print("\n" + scanner.generate_report())

    # Save results
    scanner.save_results("D:/gridbotchuck/data/backtest_results.json")

    return results


if __name__ == "__main__":
    asyncio.run(main())
