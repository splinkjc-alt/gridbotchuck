"""
EMA Crossover Scanner (Dry Run)

Scans market and shows EMA 9/20 signals WITHOUT placing trades.

SMART ENTRY LOGIC:
- BUY on crossover (EMA 9 crosses above EMA 20)
- SAFE TO BUY if missed crossover but gap is WIDENING (momentum growing)
- HOLD/WAIT if gap is narrowing (momentum fading)
- SELL when gap narrows significantly or crossover occurs
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime

import ccxt
import pandas as pd
from dotenv import load_dotenv

# Load environment
script_dir = Path(__file__).parent
load_dotenv(script_dir / ".env")


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calculate EMA."""
    return prices.ewm(span=period, adjust=False).mean()


async def main():
    print("=" * 80)
    print("EMA 9/20 MOMENTUM SCANNER")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("STRATEGY:")
    print("  ✅ BUY when EMA 9 crosses above EMA 20 (crossover)")
    print("  ✅ SAFE TO BUY if gap is WIDENING (momentum growing)")
    print("  ⚠️  CAUTION if gap is narrowing (momentum fading)")
    print("  🔴 SELL when EMAs converge or cross bearish")
    print()
    
    # Connect to Kraken
    exchange = ccxt.kraken({
        "apiKey": os.getenv("EXCHANGE_API_KEY"),
        "secret": os.getenv("EXCHANGE_SECRET_KEY"),
    })
    
    # Candidate pairs to scan
    pairs = [
        "UNI/USD", "SOL/USD", "XRP/USD", "ADA/USD", "DOGE/USD",
        "AVAX/USD", "DOT/USD", "LINK/USD", "ATOM/USD",
        "FIL/USD", "NEAR/USD", "APT/USD", "ARB/USD", "OP/USD",
        "SUI/USD", "TIA/USD", "INJ/USD", "FET/USD", "RENDER/USD",
    ]
    
    results = []
    
    print("Scanning pairs...")
    print()
    
    for pair in pairs:
        try:
            # Fetch OHLCV (15m candles)
            ohlcv = exchange.fetch_ohlcv(pair, "15m", limit=50)
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            
            if len(df) < 25:
                continue
                
            # Calculate EMAs
            ema_9 = calculate_ema(df["close"], 9)
            ema_20 = calculate_ema(df["close"], 20)
            
            current_9 = ema_9.iloc[-1]
            current_20 = ema_20.iloc[-1]
            prev_9 = ema_9.iloc[-2]
            prev_20 = ema_20.iloc[-2]
            prev2_9 = ema_9.iloc[-3]
            prev2_20 = ema_20.iloc[-3]
            price = df["close"].iloc[-1]
            
            # Calculate spreads (gap between EMAs)
            current_spread = ((current_9 - current_20) / current_20) * 100
            prev_spread = ((prev_9 - prev_20) / prev_20) * 100
            prev2_spread = ((prev2_9 - prev2_20) / prev2_20) * 100
            
            # Calculate if gap is widening or narrowing (over last 3 candles)
            spread_change = current_spread - prev_spread
            spread_trend = current_spread - prev2_spread  # Longer term trend
            
            # Determine signal
            if prev_9 <= prev_20 and current_9 > current_20:
                # Fresh crossover!
                signal = "🟢 BUY SIGNAL (crossover)"
                signal_type = "BUY"
                action = "BUY NOW"
            elif prev_9 >= prev_20 and current_9 < current_20:
                # Bearish crossover
                signal = "🔴 SELL SIGNAL (crossover)"
                signal_type = "SELL"
                action = "SELL NOW"
            elif current_9 > current_20:
                # Bullish - EMA 9 above 20
                if spread_change > 0 and spread_trend > 0:
                    # Gap is WIDENING - safe to buy
                    signal = f"✅ SAFE TO BUY (gap widening +{spread_change:.3f}%)"
                    signal_type = "SAFE_BUY"
                    action = "BUY"
                elif spread_change > 0:
                    # Gap widening but short term
                    signal = f"📈 Bullish (gap +{spread_change:.3f}%)"
                    signal_type = "BULLISH"
                    action = "CONSIDER BUY"
                elif current_spread > 0.5:
                    # Gap narrowing but still decent spread
                    signal = f"⚠️  Gap narrowing ({spread_change:.3f}%) - HOLD"
                    signal_type = "HOLD"
                    action = "HOLD"
                else:
                    # Gap very small and narrowing - sell warning
                    signal = f"⚠️  Gap closing ({current_spread:.2f}%) - CONSIDER SELL"
                    signal_type = "WARN_SELL"
                    action = "CONSIDER SELL"
            else:
                # Bearish - EMA 9 below 20
                if spread_change < 0 and spread_trend < 0:
                    # Gap widening bearish
                    signal = f"📉 Bearish (avoid)"
                    signal_type = "BEARISH"
                    action = "AVOID"
                elif abs(current_spread) < 0.2:
                    # Close to crossover
                    signal = f"👀 Watch for crossover ({current_spread:.2f}%)"
                    signal_type = "WATCH"
                    action = "WATCH"
                else:
                    signal = f"📉 Bearish ({current_spread:.2f}%)"
                    signal_type = "BEARISH"
                    action = "AVOID"
                
            # Get 24h change
            ticker = exchange.fetch_ticker(pair)
            change_24h = ticker.get("percentage", 0) or 0
            
            results.append({
                "pair": pair,
                "price": price,
                "ema_9": current_9,
                "ema_20": current_20,
                "spread": current_spread,
                "spread_change": spread_change,
                "signal": signal,
                "signal_type": signal_type,
                "action": action,
                "change_24h": change_24h,
            })
            
        except Exception as e:
            if "does not have market" not in str(e):
                print(f"  ⚠️  {pair}: Error - {e}")
            
    # Sort by action priority
    priority = {"BUY": 0, "SAFE_BUY": 1, "BULLISH": 2, "WATCH": 3, "HOLD": 4, "WARN_SELL": 5, "SELL": 6, "BEARISH": 7}
    results.sort(key=lambda x: (priority.get(x["signal_type"], 8), -x["spread_change"]))
    
    # Display results
    print("=" * 95)
    print(f"{'PAIR':<12} {'PRICE':>10} {'SPREAD':>8} {'Δ SPREAD':>9} {'24H':>8}  {'ACTION':<12} {'SIGNAL'}")
    print("-" * 95)
    
    for r in results:
        spread_arrow = "↑" if r["spread_change"] > 0 else "↓" if r["spread_change"] < 0 else "→"
        print(f"{r['pair']:<12} ${r['price']:>9.4f} {r['spread']:>+7.2f}% {spread_arrow}{abs(r['spread_change']):>7.3f}% {r['change_24h']:>+7.2f}%  {r['action']:<12} {r['signal']}")
        
    print("=" * 95)
    print()
    
    # Actionable Summary
    buy_now = [r for r in results if r["signal_type"] == "BUY"]
    safe_buy = [r for r in results if r["signal_type"] == "SAFE_BUY"]
    sell_now = [r for r in results if r["signal_type"] in ("SELL", "WARN_SELL")]
    
    print("🎯 ACTIONABLE SIGNALS:")
    print()
    
    if buy_now:
        print("  🟢 BUY NOW (fresh crossover):")
        for r in buy_now:
            print(f"      → {r['pair']} @ ${r['price']:.4f} (24h: {r['change_24h']:+.2f}%)")
    
    if safe_buy:
        print("  ✅ SAFE TO BUY (momentum growing):")
        for r in safe_buy:
            print(f"      → {r['pair']} @ ${r['price']:.4f} | Gap widening: +{r['spread_change']:.3f}% | 24h: {r['change_24h']:+.2f}%")
            
    if sell_now:
        print("  🔴 CONSIDER SELLING:")
        for r in sell_now:
            print(f"      → {r['pair']} @ ${r['price']:.4f} | {r['signal']}")
            
    if not buy_now and not safe_buy:
        print("  ⏳ No strong buy signals - wait for crossover or widening gap")
        
    print()
    
    # Best opportunities
    all_buys = [r for r in results if r["signal_type"] in ("BUY", "SAFE_BUY", "BULLISH")]
    if all_buys:
        print("📊 TOP MOMENTUM OPPORTUNITIES:")
        top = sorted(all_buys, key=lambda x: (x["spread_change"], x["change_24h"]), reverse=True)[:5]
        for i, r in enumerate(top, 1):
            print(f"  {i}. {r['pair']}: spread {r['spread']:+.2f}%, Δ{r['spread_change']:+.3f}%, 24h {r['change_24h']:+.2f}%")


if __name__ == "__main__":
    asyncio.run(main())
