"""
Asset Optimizer
===============

Runs backtests on each asset with different timeframe/indicator combinations
to find the optimal configuration.

Usage:
    python asset_optimizer.py --optimize-all
    python asset_optimizer.py --symbol BTC/USD
"""

import argparse
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

import ccxt
import pandas as pd
import numpy as np

from indicator_combos import INDICATOR_COMBOS, TIMEFRAMES, STRATEGIES, DEFAULT_CONFIG


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
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


# ============== BACKTEST RESULT ==============

@dataclass
class BacktestResult:
    """Results from a single backtest run."""
    symbol: str
    timeframe: str
    indicator_combo: str
    strategy: str
    profit_pct: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    sharpe_ratio: float


# ============== ASSET OPTIMIZER ==============

class AssetOptimizer:
    """Optimizes trading parameters for a single asset."""

    def __init__(self, symbol: str, initial_balance: float = 100.0):
        self.symbol = symbol
        self.initial_balance = initial_balance
        self.exchange = ccxt.kraken()
        self.results = []

    def fetch_data(self, timeframe: str, days: int = 30) -> pd.DataFrame:
        """Fetch historical OHLCV data."""
        since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

        all_candles = []
        while True:
            try:
                candles = self.exchange.fetch_ohlcv(
                    self.symbol,
                    timeframe,
                    since=since,
                    limit=500
                )
                if not candles:
                    break
                all_candles.extend(candles)
                since = candles[-1][0] + 1
                if len(candles) < 500:
                    break
            except Exception as e:
                print(f"    Error fetching {self.symbol} {timeframe}: {e}")
                break

        if not all_candles:
            return pd.DataFrame()

        df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df

    def run_backtest(self, df: pd.DataFrame, combo_name: str, strategy: str) -> Optional[BacktestResult]:
        """Run backtest with specific indicator combo and strategy."""
        if df.empty or len(df) < 50:
            return None

        combo = INDICATOR_COMBOS[combo_name]
        params = combo['params']
        close = df['close']
        high = df['high']
        low = df['low']

        # Calculate indicators based on combo
        df_copy = df.copy()
        df_copy['rsi'] = calculate_rsi(close, params.get('rsi_period', 14))

        if 'bb_period' in params:
            df_copy['bb_upper'], df_copy['bb_mid'], df_copy['bb_lower'] = calculate_bollinger_bands(
                close, params['bb_period'], params.get('bb_std', 2.0)
            )

        if 'ema_fast' in params:
            df_copy['ema_fast'] = calculate_ema(close, params['ema_fast'])
            df_copy['ema_slow'] = calculate_ema(close, params['ema_slow'])

        if 'macd_fast' in params:
            df_copy['macd'], df_copy['macd_signal'], df_copy['macd_hist'] = calculate_macd(
                close, params['macd_fast'], params['macd_slow'], params['macd_signal']
            )

        # Run strategy simulation
        if strategy == 'grid':
            result = self._simulate_grid(df_copy, params, combo_name)
        elif strategy == 'mean_reversion':
            result = self._simulate_mean_reversion(df_copy, params, combo_name)
        else:  # momentum
            result = self._simulate_momentum(df_copy, params, combo_name)

        return result

    def _simulate_grid(self, df: pd.DataFrame, params: dict, combo_name: str) -> BacktestResult:
        """Simulate grid trading strategy."""
        close = df['close']
        balance = self.initial_balance
        crypto = 0.0
        trades = []
        balance_history = [balance]
        position_size = balance * 0.2

        rsi_buy = params.get('rsi_buy', 35)
        rsi_sell = params.get('rsi_sell', 65)

        for i in range(50, len(df)):
            price = close.iloc[i]
            rsi = df['rsi'].iloc[i]

            # Buy conditions
            buy_signal = rsi < rsi_buy

            # Add BB condition if available
            if 'bb_lower' in df.columns:
                buy_signal = buy_signal and (price <= df['bb_lower'].iloc[i] * 1.02)

            # Add EMA trend filter if available
            if 'ema_fast' in df.columns:
                # For grid, we want to buy in any trend
                pass

            # Sell conditions
            sell_signal = rsi > rsi_sell

            if 'bb_upper' in df.columns:
                sell_signal = sell_signal and (price >= df['bb_upper'].iloc[i] * 0.98)

            if buy_signal and balance >= position_size:
                crypto_amount = position_size / price
                balance -= position_size
                crypto += crypto_amount
                trades.append({'type': 'buy', 'price': price, 'rsi': rsi})

            elif sell_signal and crypto > 0:
                sell_value = crypto * price
                balance += sell_value
                trades.append({'type': 'sell', 'price': price, 'value': sell_value})
                crypto = 0

            total = balance + (crypto * price)
            balance_history.append(total)

        final_balance = balance + (crypto * close.iloc[-1])
        profit_pct = ((final_balance - self.initial_balance) / self.initial_balance) * 100

        sells = [t for t in trades if t['type'] == 'sell']
        win_rate = 100.0 if sells else 0.0

        return BacktestResult(
            symbol=self.symbol,
            timeframe=df.index.freq if hasattr(df.index, 'freq') else 'unknown',
            indicator_combo=combo_name,
            strategy='grid',
            profit_pct=round(profit_pct, 2),
            win_rate=win_rate,
            total_trades=len(trades),
            max_drawdown=round(self._max_drawdown(balance_history), 2),
            sharpe_ratio=round(self._sharpe_ratio(balance_history), 2)
        )

    def _simulate_mean_reversion(self, df: pd.DataFrame, params: dict, combo_name: str) -> BacktestResult:
        """Simulate mean reversion strategy."""
        close = df['close']
        balance = self.initial_balance
        crypto = 0.0
        trades = []
        balance_history = [balance]
        position_size = balance * 0.15

        entry_price = None

        for i in range(50, len(df)):
            price = close.iloc[i]
            rsi = df['rsi'].iloc[i]

            # Mean reversion: buy extreme oversold
            if rsi < 25 and balance >= position_size and crypto == 0:
                crypto_amount = position_size / price
                balance -= position_size
                crypto += crypto_amount
                entry_price = price
                trades.append({'type': 'buy', 'price': price})

            # Exit when RSI normalizes or profit target
            elif crypto > 0:
                profit = (price - entry_price) / entry_price if entry_price else 0
                if rsi > 50 or profit > 0.04 or profit < -0.03:
                    sell_value = crypto * price
                    balance += sell_value
                    pnl = sell_value - (crypto * entry_price) if entry_price else 0
                    trades.append({'type': 'sell', 'price': price, 'pnl': pnl})
                    crypto = 0
                    entry_price = None

            balance_history.append(balance + (crypto * price))

        final_balance = balance + (crypto * close.iloc[-1])
        profit_pct = ((final_balance - self.initial_balance) / self.initial_balance) * 100

        wins = len([t for t in trades if t.get('pnl', 0) > 0])
        total_sells = len([t for t in trades if t['type'] == 'sell'])
        win_rate = (wins / total_sells * 100) if total_sells > 0 else 0

        return BacktestResult(
            symbol=self.symbol,
            timeframe='unknown',
            indicator_combo=combo_name,
            strategy='mean_reversion',
            profit_pct=round(profit_pct, 2),
            win_rate=round(win_rate, 1),
            total_trades=len(trades),
            max_drawdown=round(self._max_drawdown(balance_history), 2),
            sharpe_ratio=round(self._sharpe_ratio(balance_history), 2)
        )

    def _simulate_momentum(self, df: pd.DataFrame, params: dict, combo_name: str) -> BacktestResult:
        """Simulate momentum/trend following strategy."""
        close = df['close']
        balance = self.initial_balance
        crypto = 0.0
        trades = []
        balance_history = [balance]
        position_size = balance * 0.2

        for i in range(50, len(df)):
            price = close.iloc[i]
            rsi = df['rsi'].iloc[i]

            # Momentum: buy when trending up
            buy_signal = False
            sell_signal = False

            if 'ema_fast' in df.columns:
                ema_fast = df['ema_fast'].iloc[i]
                ema_slow = df['ema_slow'].iloc[i]
                trend_up = ema_fast > ema_slow

                if trend_up and rsi > 50 and rsi < 70:
                    buy_signal = True
                elif not trend_up or rsi > 75:
                    sell_signal = True
            else:
                # Simple RSI momentum
                if rsi > 55 and rsi < 70:
                    buy_signal = True
                elif rsi > 75 or rsi < 45:
                    sell_signal = True

            if buy_signal and balance >= position_size and crypto == 0:
                crypto = position_size / price
                balance -= position_size
                trades.append({'type': 'buy', 'price': price})

            elif sell_signal and crypto > 0:
                sell_value = crypto * price
                balance += sell_value
                trades.append({'type': 'sell', 'price': price})
                crypto = 0

            balance_history.append(balance + (crypto * price))

        final_balance = balance + (crypto * close.iloc[-1])
        profit_pct = ((final_balance - self.initial_balance) / self.initial_balance) * 100

        return BacktestResult(
            symbol=self.symbol,
            timeframe='unknown',
            indicator_combo=combo_name,
            strategy='momentum',
            profit_pct=round(profit_pct, 2),
            win_rate=100.0 if trades else 0.0,
            total_trades=len(trades),
            max_drawdown=round(self._max_drawdown(balance_history), 2),
            sharpe_ratio=round(self._sharpe_ratio(balance_history), 2)
        )

    def _max_drawdown(self, balance_history: list) -> float:
        """Calculate maximum drawdown percentage."""
        peak = balance_history[0]
        max_dd = 0
        for val in balance_history:
            if val > peak:
                peak = val
            dd = (peak - val) / peak * 100
            max_dd = max(max_dd, dd)
        return max_dd

    def _sharpe_ratio(self, balance_history: list, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        if len(balance_history) < 2:
            return 0.0
        returns = pd.Series(balance_history).pct_change().dropna()
        if returns.std() == 0:
            return 0.0
        excess = returns.mean() - (risk_free_rate / 252)
        return (excess / returns.std()) * np.sqrt(252)

    def optimize(self) -> dict:
        """Run all combinations and find the best config."""
        print(f"\n  Optimizing {self.symbol}...")
        all_results = []

        for timeframe in TIMEFRAMES:
            print(f"    Testing {timeframe}...", end=" ", flush=True)
            df = self.fetch_data(timeframe, days=30)

            if df.empty:
                print("no data")
                continue

            for combo_name in INDICATOR_COMBOS.keys():
                for strategy in STRATEGIES:
                    result = self.run_backtest(df, combo_name, strategy)
                    if result:
                        result.timeframe = timeframe
                        all_results.append(result)

            print(f"{len(df)} candles")

        if not all_results:
            print(f"    No valid results for {self.symbol}")
            return DEFAULT_CONFIG.copy()

        # Find best result by profit
        best = max(all_results, key=lambda x: x.profit_pct)

        config = {
            'best_timeframe': best.timeframe,
            'strategy': best.strategy,
            'indicator_combo': best.indicator_combo,
            'indicators': INDICATOR_COMBOS[best.indicator_combo]['indicators'],
            'params': INDICATOR_COMBOS[best.indicator_combo]['params'],
            'profit_pct': best.profit_pct,
            'win_rate': best.win_rate,
            'max_drawdown': best.max_drawdown,
            'sharpe_ratio': best.sharpe_ratio,
            'total_trades': best.total_trades,
            'last_optimized': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

        print(f"    Best: {best.timeframe} / {best.strategy} / {best.indicator_combo} = {best.profit_pct:+.2f}%")

        return config


# ============== BATCH OPTIMIZATION ==============

def optimize_asset(symbol: str) -> dict:
    """Optimize a single asset."""
    optimizer = AssetOptimizer(symbol)
    return optimizer.optimize()


def optimize_all(symbols: list[str], output_file: str = None) -> dict:
    """Optimize all assets and save results."""
    configs = {}

    print("=" * 60)
    print("ASSET OPTIMIZATION")
    print(f"Testing {len(symbols)} assets x {len(TIMEFRAMES)} timeframes x {len(INDICATOR_COMBOS)} combos x {len(STRATEGIES)} strategies")
    print("=" * 60)

    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] {symbol}")
        try:
            configs[symbol] = optimize_asset(symbol)
        except Exception as e:
            print(f"    Error: {e}")
            configs[symbol] = DEFAULT_CONFIG.copy()

    # Save to file
    if output_file is None:
        output_file = Path(__file__).parent / 'optimal_configs.json'

    with open(output_file, 'w') as f:
        json.dump(configs, f, indent=2)

    print("\n" + "=" * 60)
    print("OPTIMIZATION COMPLETE")
    print("=" * 60)
    print(f"\nResults saved to: {output_file}")

    # Summary
    print("\nBest configurations:")
    print("-" * 60)
    for symbol, config in configs.items():
        print(f"{symbol:12} | {config['best_timeframe']:4} | {config['strategy']:15} | {config['profit_pct']:+6.2f}%")

    return configs


def load_optimal_configs(config_file: str = None) -> dict:
    """Load optimal configs from file."""
    if config_file is None:
        config_file = Path(__file__).parent / 'optimal_configs.json'

    if not Path(config_file).exists():
        return {}

    with open(config_file, 'r') as f:
        return json.load(f)


# ============== CLI ==============

def main():
    parser = argparse.ArgumentParser(description='Optimize trading parameters per asset')
    parser.add_argument('--optimize-all', action='store_true', help='Optimize all assets in watchlist')
    parser.add_argument('--symbol', type=str, help='Optimize a specific symbol')
    parser.add_argument('--watchlist', type=str, help='Path to watchlist.json')

    args = parser.parse_args()

    if args.symbol:
        config = optimize_asset(args.symbol)
        print(json.dumps(config, indent=2))

    elif args.optimize_all:
        # Load watchlist
        watchlist_file = args.watchlist or Path(__file__).parent.parent / 'config' / 'watchlist.json'

        if Path(watchlist_file).exists():
            with open(watchlist_file, 'r') as f:
                watchlist = json.load(f)
            symbols = watchlist.get('crypto', [])
        else:
            # Default watchlist
            symbols = [
                'BTC/USD', 'ETH/USD', 'ADA/USD', 'SOL/USD', 'XRP/USD',
                'DOGE/USD', 'AVAX/USD', 'MATIC/USD', 'DOT/USD', 'LINK/USD',
                'ATOM/USD', 'UNI/USD', 'LTC/USD', 'NEAR/USD', 'APT/USD'
            ]

        optimize_all(symbols)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
