"""
Adaptive Multi-Asset Scanner
============================

Scans multiple assets using their individually optimized configurations.
Each asset uses the best timeframe and indicators discovered through backtesting.

Usage:
    python adaptive_scanner.py              # Run scanner
    python adaptive_scanner.py --show-configs   # Show current optimal configs
    python adaptive_scanner.py --optimize       # Run optimization first
"""

import argparse
import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, time
import json
import logging
from pathlib import Path

import ccxt
import pandas as pd
import pytz

# Try importing yfinance for stocks
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("AdaptiveScanner")


# ============== TECHNICAL INDICATORS ==============

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator."""
    deltas = prices.diff()
    gains = deltas.where(deltas > 0, 0.0)
    losses = -deltas.where(deltas < 0, 0.0)
    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calculate EMA."""
    return prices.ewm(span=period, adjust=False).mean()


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0):
    """Calculate Bollinger Bands."""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return upper, sma, lower


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculate MACD."""
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    return macd_line, signal_line


# ============== OPPORTUNITY ==============

@dataclass
class Opportunity:
    """Trading opportunity."""
    symbol: str
    timeframe: str
    strategy: str
    signal: str  # BUY, SELL, WATCH, WAIT
    strength: int  # 0-100
    price: float
    reason: str
    indicators: dict
    timestamp: datetime


# ============== DEFAULT CONFIG ==============

DEFAULT_CONFIG = {
    "best_timeframe": "30m",
    "strategy": "grid",
    "indicator_combo": "rsi_bb",
    "indicators": ["RSI(14)", "Bollinger(20,2)"],
    "params": {
        "rsi_period": 14,
        "rsi_buy": 35,
        "rsi_sell": 65,
        "bb_period": 20,
        "bb_std": 2.0
    },
    "profit_pct": 0.0,
    "win_rate": 0.0
}


# ============== ADAPTIVE SCANNER ==============

class AdaptiveScanner:
    """Scans multiple assets using their optimal configurations."""

    def __init__(self, watchlist_file: str | None = None, configs_file: str | None = None):
        self.exchange = ccxt.kraken()
        self.et_tz = pytz.timezone("US/Eastern")

        # Load watchlist
        watchlist_path = watchlist_file or Path(__file__).parent / "config" / "watchlist.json"
        if Path(watchlist_path).exists():
            with open(watchlist_path) as f:
                data = json.load(f)
            self.crypto_watchlist = data.get("crypto", [])
            self.stock_watchlist = data.get("stocks", [])
        else:
            self.crypto_watchlist = ["BTC/USD", "ETH/USD", "ADA/USD"]
            self.stock_watchlist = []

        # Load optimal configs
        configs_path = configs_file or Path(__file__).parent / "optimization" / "optimal_configs.json"
        if Path(configs_path).exists():
            with open(configs_path) as f:
                self.configs = json.load(f)
        else:
            self.configs = {}

        self.scan_interval = 60  # seconds

    def get_config(self, symbol: str) -> dict:
        """Get optimal config for symbol, or default if not optimized."""
        return self.configs.get(symbol, DEFAULT_CONFIG)

    def fetch_data(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """Fetch OHLCV data for symbol."""
        try:
            candles = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
            return df
        except Exception as e:
            log.error(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()

    async def scan_crypto(self, symbol: str) -> Opportunity | None:
        """Scan a single crypto asset using its optimal config."""
        config = self.get_config(symbol)
        timeframe = config.get("best_timeframe", "30m")
        strategy = config.get("strategy", "grid")
        params = config.get("params", DEFAULT_CONFIG["params"])

        df = self.fetch_data(symbol, timeframe)
        if df.empty:
            return None

        close = df["close"]
        current_price = close.iloc[-1]

        # Calculate indicators
        rsi = calculate_rsi(close, params.get("rsi_period", 14))
        current_rsi = rsi.iloc[-1]

        indicators = {"RSI": round(current_rsi, 1)}

        # Calculate additional indicators if in config
        if "bb_period" in params:
            bb_upper, _bb_mid, bb_lower = calculate_bollinger_bands(
                close, params["bb_period"], params.get("bb_std", 2.0)
            )
            bb_pos = ((current_price - bb_lower.iloc[-1]) /
                      (bb_upper.iloc[-1] - bb_lower.iloc[-1])) * 100
            indicators["BB_pos"] = round(bb_pos, 1)

        if "ema_fast" in params:
            ema_fast = calculate_ema(close, params["ema_fast"]).iloc[-1]
            ema_slow = calculate_ema(close, params["ema_slow"]).iloc[-1]
            indicators["EMA_trend"] = "UP" if ema_fast > ema_slow else "DOWN"

        if "macd_fast" in params:
            macd, macd_signal = calculate_macd(
                close, params["macd_fast"], params["macd_slow"], params["macd_signal"]
            )
            indicators["MACD"] = "BULL" if macd.iloc[-1] > macd_signal.iloc[-1] else "BEAR"

        # Generate signal based on strategy
        signal, strength, reasons = self._generate_signal(strategy, params, indicators, current_rsi)

        return Opportunity(
            symbol=symbol,
            timeframe=timeframe,
            strategy=strategy,
            signal=signal,
            strength=strength,
            price=current_price,
            reason=" | ".join(reasons) if reasons else "Neutral",
            indicators=indicators,
            timestamp=datetime.now(tz=UTC)
        )

    def _generate_signal(self, strategy: str, params: dict, indicators: dict, rsi: float) -> tuple:
        """Generate trading signal based on strategy and indicators."""
        signal = "WAIT"
        strength = 0
        reasons = []

        rsi_buy = params.get("rsi_buy", 35)
        rsi_sell = params.get("rsi_sell", 65)

        if strategy == "grid":
            # Grid: buy oversold, sell overbought
            if rsi < rsi_buy:
                strength += 50
                reasons.append(f"RSI oversold ({rsi:.1f})")

            if "BB_pos" in indicators and indicators["BB_pos"] < 20:
                strength += 30
                reasons.append("Near lower BB")

            if rsi > rsi_sell:
                signal = "SELL"
                strength = 60
                reasons = [f"RSI overbought ({rsi:.1f})"]
            elif strength >= 60:
                signal = "BUY"
            elif strength >= 40:
                signal = "WATCH"

        elif strategy == "mean_reversion":
            # Mean reversion: extreme oversold only
            if rsi < 25:
                signal = "BUY"
                strength = 80
                reasons.append(f"Extreme oversold ({rsi:.1f})")
            elif rsi < 35:
                signal = "WATCH"
                strength = 50
                reasons.append(f"Oversold ({rsi:.1f})")
            elif rsi > 75:
                signal = "SELL"
                strength = 70
                reasons.append(f"Overbought ({rsi:.1f})")

        elif strategy == "momentum":
            # Momentum: follow trend
            trend = indicators.get("EMA_trend", "UP")
            macd = indicators.get("MACD", "BULL")

            if trend == "UP" and macd == "BULL" and rsi > 50 and rsi < 70:
                signal = "BUY"
                strength = 65
                reasons.append("Uptrend + MACD bullish")
            elif trend == "DOWN" or rsi > 75:
                signal = "SELL"
                strength = 55
                reasons.append("Trend reversal")
            elif trend == "UP" and rsi > 45:
                signal = "WATCH"
                strength = 40
                reasons.append("Trend developing")

        return signal, min(strength, 100), reasons

    async def scan_stock(self, symbol: str) -> Opportunity | None:
        """Scan a single stock."""
        if not YFINANCE_AVAILABLE:
            return Opportunity(
                symbol=symbol,
                timeframe="N/A",
                strategy="N/A",
                signal="DISABLED",
                strength=0,
                price=0,
                reason="yfinance not installed",
                indicators={},
                timestamp=datetime.now(tz=UTC)
            )

        # Check market hours
        now = datetime.now(self.et_tz)
        if now.weekday() > 4:
            return Opportunity(
                symbol=symbol,
                timeframe="N/A",
                strategy="mean_reversion",
                signal="SLEEPING",
                strength=0,
                price=0,
                reason="Weekend",
                indicators={"market": "CLOSED"},
                timestamp=datetime.now(tz=UTC)
            )

        market_open = time(9, 30)
        market_close = time(16, 0)
        if not (market_open <= now.time() <= market_close):
            return Opportunity(
                symbol=symbol,
                timeframe="N/A",
                strategy="mean_reversion",
                signal="SLEEPING",
                strength=0,
                price=0,
                reason=f'Market closed ({now.strftime("%I:%M %p ET")})',
                indicators={"market": "CLOSED"},
                timestamp=datetime.now(tz=UTC)
            )

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="5d", interval="30m")

            if df.empty:
                return None

            close = df["Close"]
            current_price = close.iloc[-1]
            rsi = calculate_rsi(close).iloc[-1]

            signal = "WAIT"
            strength = 0
            reasons = []

            if rsi < 30:
                signal = "BUY"
                strength = 70
                reasons.append(f"Oversold ({rsi:.1f})")
            elif rsi < 40:
                signal = "WATCH"
                strength = 45
                reasons.append(f"RSI low ({rsi:.1f})")
            elif rsi > 70:
                signal = "SELL"
                strength = 60
                reasons.append(f"Overbought ({rsi:.1f})")

            return Opportunity(
                symbol=symbol,
                timeframe="30m",
                strategy="mean_reversion",
                signal=signal,
                strength=strength,
                price=current_price,
                reason=" | ".join(reasons) if reasons else "Neutral",
                indicators={"RSI": round(rsi, 1)},
                timestamp=datetime.now(tz=UTC)
            )

        except Exception as e:
            log.error(f"Error scanning {symbol}: {e}")
            return None

    async def scan_all(self) -> list[Opportunity]:
        """Scan all assets in watchlist."""
        tasks = []

        # Crypto
        for symbol in self.crypto_watchlist:
            tasks.append(self.scan_crypto(symbol))

        # Stocks
        for symbol in self.stock_watchlist:
            tasks.append(self.scan_stock(symbol))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        opportunities = []
        for r in results:
            if isinstance(r, Opportunity):
                opportunities.append(r)

        return opportunities

    def print_header(self):
        """Print scanner header."""
        print("\n" + "=" * 80)
        print("  ADAPTIVE MULTI-ASSET SCANNER")
        print("=" * 80)
        print(f"  Crypto: {len(self.crypto_watchlist)} assets | Stocks: {len(self.stock_watchlist)} assets")
        print(f"  Configs loaded: {len(self.configs)} assets with optimal settings")
        print("=" * 80)
        print("  Signals: BUY | WATCH | WAIT | SELL | SLEEPING")
        print("=" * 80 + "\n")

    def print_configs(self):
        """Print current optimal configs."""
        print("\n" + "=" * 80)
        print("  OPTIMAL CONFIGURATIONS")
        print("=" * 80)

        if not self.configs:
            print("  No optimized configs found. Run with --optimize first.")
            return

        print(f"\n{'Symbol':<12} {'TF':<5} {'Strategy':<16} {'Indicators':<35} {'Profit':>8}")
        print("-" * 80)

        for symbol, config in sorted(self.configs.items()):
            tf = config.get("best_timeframe", "?")
            strategy = config.get("strategy", "?")
            indicators = ", ".join(config.get("indicators", [])[:3])
            profit = config.get("profit_pct", 0)
            print(f"{symbol:<12} {tf:<5} {strategy:<16} {indicators:<35} {profit:>+7.2f}%")

        print("=" * 80)

    def print_opportunity(self, opp: Opportunity):
        """Print a single opportunity."""
        if opp.signal == "BUY":
            signal_str = ">>> BUY <<<"
        elif opp.signal == "SELL":
            signal_str = "<<< SELL >>>"
        elif opp.signal == "WATCH":
            signal_str = "~~~ WATCH ~~~"
        elif opp.signal == "SLEEPING":
            signal_str = "zzz SLEEP zzz"
        else:
            signal_str = "... WAIT ..."

        # Format price
        if opp.price > 1000:
            price_str = f"${opp.price:,.0f}"
        elif opp.price > 1:
            price_str = f"${opp.price:.2f}"
        else:
            price_str = f"${opp.price:.4f}"

        config_str = f"{opp.timeframe}/{opp.strategy}"

        print(f"{opp.symbol:<12} | {config_str:<20} | {signal_str:<14} | {opp.strength:>3}% | {price_str:>12}")

        if opp.reason and opp.signal in ["BUY", "SELL", "WATCH"]:
            print(f"{'':12} | Reason: {opp.reason}")
            ind_str = " | ".join([f"{k}:{v}" for k, v in opp.indicators.items()])
            print(f"{'':12} | {ind_str}")

        print("-" * 80)

    async def run(self):
        """Main scanning loop."""
        self.print_header()

        scan_count = 0
        while True:
            try:
                scan_count += 1
                now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[Scan #{scan_count}] {now}")
                print("-" * 80)

                opportunities = await self.scan_all()

                # Sort by signal priority then strength
                priority = {"BUY": 0, "SELL": 1, "WATCH": 2, "SLEEPING": 3, "WAIT": 4, "DISABLED": 5}
                opportunities.sort(key=lambda x: (priority.get(x.signal, 6), -x.strength))

                for opp in opportunities:
                    self.print_opportunity(opp)

                # Alert on actionable signals
                actionable = [o for o in opportunities if o.signal in ["BUY", "SELL"]]
                if actionable:
                    print("\n" + "!" * 80)
                    print("  OPPORTUNITIES DETECTED!")
                    for opp in actionable:
                        print(f"  -> {opp.symbol}: {opp.signal} @ {opp.price:.4f} (Strength: {opp.strength}%)")
                    print("!" * 80)

                print(f"\nNext scan in {self.scan_interval}s... (Ctrl+C to stop)")
                await asyncio.sleep(self.scan_interval)

            except KeyboardInterrupt:
                print("\n\nScanner stopped.")
                break
            except Exception as e:
                log.error(f"Scan error: {e}")
                await asyncio.sleep(10)


# ============== CLI ==============

async def main():
    parser = argparse.ArgumentParser(description="Adaptive Multi-Asset Scanner")
    parser.add_argument("--show-configs", action="store_true", help="Show current optimal configs")
    parser.add_argument("--optimize", action="store_true", help="Run optimization before scanning")
    parser.add_argument("--watchlist", type=str, help="Path to watchlist.json")
    parser.add_argument("--configs", type=str, help="Path to optimal_configs.json")

    args = parser.parse_args()

    scanner = AdaptiveScanner(
        watchlist_file=args.watchlist,
        configs_file=args.configs
    )

    if args.show_configs:
        scanner.print_configs()
        return

    if args.optimize:
        print("Running optimization first...")
        from optimization.asset_optimizer import optimize_all
        optimize_all(scanner.crypto_watchlist)
        # Reload configs
        scanner = AdaptiveScanner(
            watchlist_file=args.watchlist,
            configs_file=args.configs
        )

    await scanner.run()


if __name__ == "__main__":
    asyncio.run(main())
