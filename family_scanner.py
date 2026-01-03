"""
Bot Family Scanner
==================

Scans for optimal entry opportunities for all bots:
- GridBot Chuck: BTC/USD grid entries (30m, RSI+BB)
- Growler: ADA/USD bearish setups (30m, EMA cross + RSI)
- Sleeping Marketbot: Stock mean reversion (when market open)

Runs continuously, alerts when opportunities found.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional
import logging

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
log = logging.getLogger("FamilyScanner")


# ============== INDICATORS ==============

def rsi(prices: pd.Series, period: int = 14) -> float:
    """Calculate current RSI."""
    if len(prices) < period + 1:
        return 50.0
    deltas = prices.diff()
    gains = deltas.where(deltas > 0, 0.0)
    losses = -deltas.where(deltas < 0, 0.0)
    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val.iloc[-1]


def bollinger_position(prices: pd.Series, period: int = 20) -> tuple[float, float, float, float]:
    """Calculate Bollinger Band position (0-100) and bands."""
    if len(prices) < period:
        return 50.0, prices.iloc[-1], prices.iloc[-1], prices.iloc[-1]
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (2 * std)
    lower = sma - (2 * std)
    current = prices.iloc[-1]
    width = upper.iloc[-1] - lower.iloc[-1]
    if width == 0:
        return 50.0, upper.iloc[-1], sma.iloc[-1], lower.iloc[-1]
    pos = ((current - lower.iloc[-1]) / width) * 100
    return max(0, min(100, pos)), upper.iloc[-1], sma.iloc[-1], lower.iloc[-1]


def ema(prices: pd.Series, period: int) -> float:
    """Calculate current EMA."""
    return prices.ewm(span=period, adjust=False).mean().iloc[-1]


# ============== OPPORTUNITY CLASSES ==============

@dataclass
class Opportunity:
    """Trading opportunity."""
    bot: str
    pair: str
    signal: str  # BUY, SELL, WAIT
    strength: int  # 1-100
    price: float
    reason: str
    indicators: dict
    timestamp: datetime


# ============== SCANNERS ==============

class GridBotScanner:
    """Scan for GridBot Chuck opportunities on BTC/USD."""

    def __init__(self):
        self.exchange = ccxt.kraken()
        self.pair = "BTC/USD"
        self.timeframe = "30m"

    async def scan(self) -> Optional[Opportunity]:
        """Scan for grid entry opportunity."""
        try:
            # Fetch recent candles
            candles = self.exchange.fetch_ohlcv(self.pair, self.timeframe, limit=100)
            df = pd.DataFrame(candles, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
            close = df['close']

            current_price = close.iloc[-1]
            current_rsi = rsi(close)
            bb_pos, bb_upper, bb_mid, bb_lower = bollinger_position(close)

            # Grid opportunity scoring
            signal = "WAIT"
            strength = 0
            reasons = []

            # Strong buy: RSI oversold + near lower BB
            if current_rsi < 35:
                strength += 40
                reasons.append(f"RSI oversold ({current_rsi:.1f})")
            elif current_rsi < 45:
                strength += 20
                reasons.append(f"RSI low ({current_rsi:.1f})")

            if bb_pos < 20:
                strength += 40
                reasons.append(f"Near lower BB ({bb_pos:.0f}%)")
            elif bb_pos < 35:
                strength += 20
                reasons.append(f"Below mid BB ({bb_pos:.0f}%)")

            # Price volatility check
            price_range = (df['high'].max() - df['low'].min()) / df['close'].mean() * 100
            if price_range > 3:
                strength += 20
                reasons.append(f"Good volatility ({price_range:.1f}%)")

            if strength >= 60:
                signal = "BUY"
            elif strength >= 40:
                signal = "WATCH"

            return Opportunity(
                bot="GridBot Chuck",
                pair=self.pair,
                signal=signal,
                strength=min(strength, 100),
                price=current_price,
                reason=" | ".join(reasons) if reasons else "Neutral market",
                indicators={
                    "RSI": round(current_rsi, 1),
                    "BB_pos": round(bb_pos, 1),
                    "BB_upper": round(bb_upper, 2),
                    "BB_lower": round(bb_lower, 2)
                },
                timestamp=datetime.now()
            )

        except Exception as e:
            log.error(f"GridBot scan error: {e}")
            return None


class GrowlerScanner:
    """Scan for Growler bearish opportunities on ADA/USD."""

    def __init__(self):
        self.exchange = ccxt.kraken()
        self.pair = "ADA/USD"
        self.timeframe = "30m"

    async def scan(self) -> Optional[Opportunity]:
        """Scan for bearish scalp opportunity."""
        try:
            candles = self.exchange.fetch_ohlcv(self.pair, self.timeframe, limit=100)
            df = pd.DataFrame(candles, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
            close = df['close']

            current_price = close.iloc[-1]
            current_rsi = rsi(close)
            ema_20 = ema(close, 20)
            ema_50 = ema(close, 50)

            # Bearish trend detection
            is_bearish = ema_20 < ema_50
            trend_strength = abs(ema_20 - ema_50) / ema_50 * 100

            signal = "WAIT"
            strength = 0
            reasons = []

            if is_bearish:
                strength += 30
                reasons.append(f"Bearish trend (EMA20 < EMA50)")

                # Oversold bounce opportunity in downtrend
                if current_rsi < 30:
                    strength += 40
                    reasons.append(f"Extreme oversold ({current_rsi:.1f})")
                    signal = "BUY"  # Counter-trend scalp
                elif current_rsi < 40:
                    strength += 25
                    reasons.append(f"Oversold ({current_rsi:.1f})")
                    signal = "WATCH"
            else:
                reasons.append("Bullish trend - Growler sleeps")

            return Opportunity(
                bot="Growler",
                pair=self.pair,
                signal=signal,
                strength=min(strength, 100),
                price=current_price,
                reason=" | ".join(reasons) if reasons else "No bearish setup",
                indicators={
                    "RSI": round(current_rsi, 1),
                    "EMA20": round(ema_20, 4),
                    "EMA50": round(ema_50, 4),
                    "Trend": "BEAR" if is_bearish else "BULL"
                },
                timestamp=datetime.now()
            )

        except Exception as e:
            log.error(f"Growler scan error: {e}")
            return None


class StockScanner:
    """Scan for Sleeping Marketbot stock opportunities."""

    def __init__(self):
        self.watchlist = ["TSLA", "NVDA", "AMD", "TQQQ", "SOXL", "MARA", "COIN"]
        self.et_tz = pytz.timezone("US/Eastern")

    def is_market_open(self) -> bool:
        """Check if US market is open."""
        now = datetime.now(self.et_tz)
        if now.weekday() > 4:
            return False
        market_open = time(9, 30)
        market_close = time(16, 0)
        return market_open <= now.time() <= market_close

    async def scan(self) -> Optional[Opportunity]:
        """Scan for mean reversion opportunities."""
        if not YFINANCE_AVAILABLE:
            return Opportunity(
                bot="Sleeping Marketbot",
                pair="STOCKS",
                signal="DISABLED",
                strength=0,
                price=0,
                reason="yfinance not installed",
                indicators={},
                timestamp=datetime.now()
            )

        if not self.is_market_open():
            now = datetime.now(self.et_tz)
            return Opportunity(
                bot="Sleeping Marketbot",
                pair="STOCKS",
                signal="SLEEPING",
                strength=0,
                price=0,
                reason=f"Market closed ({now.strftime('%I:%M %p ET')})",
                indicators={"market": "CLOSED"},
                timestamp=datetime.now()
            )

        try:
            best_opp = None
            best_score = 0

            for symbol in self.watchlist:
                try:
                    ticker = yf.Ticker(symbol)
                    df = ticker.history(period="5d", interval="30m")

                    if df.empty or len(df) < 20:
                        continue

                    close = df['Close']
                    current_price = close.iloc[-1]
                    current_rsi = rsi(close)
                    bb_pos, _, _, _ = bollinger_position(close)

                    # Mean reversion score
                    score = 0
                    reasons = []

                    if current_rsi < 30:
                        score += 50
                        reasons.append(f"RSI extreme ({current_rsi:.1f})")
                    elif current_rsi < 40:
                        score += 30
                        reasons.append(f"RSI low ({current_rsi:.1f})")

                    if bb_pos < 15:
                        score += 40
                        reasons.append(f"At lower BB")
                    elif bb_pos < 30:
                        score += 20
                        reasons.append(f"Near lower BB")

                    if score > best_score:
                        best_score = score
                        best_opp = Opportunity(
                            bot="Sleeping Marketbot",
                            pair=symbol,
                            signal="BUY" if score >= 60 else "WATCH" if score >= 40 else "WAIT",
                            strength=min(score, 100),
                            price=current_price,
                            reason=" | ".join(reasons) if reasons else "Neutral",
                            indicators={
                                "RSI": round(current_rsi, 1),
                                "BB_pos": round(bb_pos, 1)
                            },
                            timestamp=datetime.now()
                        )

                except Exception:
                    continue

            if best_opp:
                return best_opp
            else:
                return Opportunity(
                    bot="Sleeping Marketbot",
                    pair="STOCKS",
                    signal="WAIT",
                    strength=0,
                    price=0,
                    reason="No opportunities in watchlist",
                    indicators={},
                    timestamp=datetime.now()
                )

        except Exception as e:
            log.error(f"Stock scan error: {e}")
            return None


# ============== MAIN SCANNER ==============

class FamilyScanner:
    """Unified scanner for all bots."""

    def __init__(self):
        self.gridbot = GridBotScanner()
        self.growler = GrowlerScanner()
        self.stocks = StockScanner()
        self.scan_interval = 60  # seconds

    def print_header(self):
        """Print scanner header."""
        print("\n" + "="*70)
        print("  BOT FAMILY SCANNER - Watching for Opportunities")
        print("="*70)
        print("  GridBot Chuck  : BTC/USD  (30m, RSI+BB)")
        print("  Growler        : ADA/USD  (30m, Bearish)")
        print("  Sleeping Bot   : Stocks   (30m, Mean Reversion)")
        print("="*70)
        print("  Signal Guide: BUY = Strong entry | WATCH = Prepare | WAIT = Hold")
        print("="*70 + "\n")

    def print_opportunity(self, opp: Opportunity):
        """Print a single opportunity."""
        # Color codes (for terminals that support it)
        if opp.signal == "BUY":
            signal_str = f">>> BUY <<<"
        elif opp.signal == "WATCH":
            signal_str = f"~~~ WATCH ~~~"
        elif opp.signal == "SLEEPING":
            signal_str = f"zzz SLEEP zzz"
        else:
            signal_str = f"... WAIT ..."

        print(f"{opp.bot:20} | {opp.pair:10} | {signal_str:15} | Str: {opp.strength:3}%")
        if opp.reason and opp.signal in ["BUY", "WATCH"]:
            print(f"{'':20} | Reason: {opp.reason}")
        if opp.signal == "BUY":
            print(f"{'':20} | Price: ${opp.price:,.2f}")
            for k, v in opp.indicators.items():
                print(f"{'':20} | {k}: {v}")
        print("-"*70)

    async def scan_all(self):
        """Scan all bots once."""
        results = await asyncio.gather(
            self.gridbot.scan(),
            self.growler.scan(),
            self.stocks.scan(),
            return_exceptions=True
        )

        opportunities = []
        for r in results:
            if isinstance(r, Opportunity):
                opportunities.append(r)

        return opportunities

    async def run(self):
        """Main scanning loop."""
        self.print_header()

        scan_count = 0
        while True:
            try:
                scan_count += 1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[Scan #{scan_count}] {now}")
                print("-"*70)

                opportunities = await self.scan_all()

                # Sort by signal priority and strength
                priority = {"BUY": 0, "WATCH": 1, "SLEEPING": 2, "WAIT": 3, "DISABLED": 4}
                opportunities.sort(key=lambda x: (priority.get(x.signal, 5), -x.strength))

                # Print all opportunities
                for opp in opportunities:
                    self.print_opportunity(opp)

                # Alert on BUY signals
                buy_signals = [o for o in opportunities if o.signal == "BUY"]
                if buy_signals:
                    print("\n" + "!"*70)
                    print("  OPPORTUNITY ALERT!")
                    for opp in buy_signals:
                        print(f"  -> {opp.bot}: {opp.pair} @ ${opp.price:,.2f} (Strength: {opp.strength}%)")
                    print("!"*70)

                # Wait for next scan
                print(f"\nNext scan in {self.scan_interval}s... (Ctrl+C to stop)")
                await asyncio.sleep(self.scan_interval)

            except KeyboardInterrupt:
                print("\n\nScanner stopped. Bots are ready when you are!")
                break
            except Exception as e:
                log.error(f"Scan error: {e}")
                await asyncio.sleep(10)


async def main():
    scanner = FamilyScanner()
    await scanner.run()


if __name__ == "__main__":
    asyncio.run(main())
