"""
EMA Crossover Bot Runner

Cancels existing orders and runs the EMA 9/20 crossover strategy.
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from datetime import datetime

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

import ccxt.async_support as ccxt
import pandas as pd
from dotenv import load_dotenv

# Load env
script_dir = Path(__file__).parent
load_dotenv(script_dir / ".env")


class EMACrossoverBot:
    """EMA 9/20 Crossover Trading Bot"""
    
    def __init__(self):
        self.logger = logging.getLogger("EMABot")
        self.exchange = None
        self.running = False
        
        # Strategy params
        self.ema_fast = 9
        self.ema_slow = 20
        self.max_positions = 2
        self.position_size_pct = 20.0  # 20% per trade
        self.min_reserve_pct = 10.0    # Keep 10% in reserve
        
        # State
        self.positions = {}  # pair -> {qty, entry_price, entry_time}
        self.monitored_pairs = []
        
        # Pairs to scan
        self.candidate_pairs = [
            "UNI/USD", "SOL/USD", "XRP/USD", "ADA/USD", "DOGE/USD",
            "AVAX/USD", "DOT/USD", "LINK/USD", "ATOM/USD",
            "FIL/USD", "NEAR/USD", "APT/USD", "ARB/USD", "OP/USD",
            "SUI/USD", "TIA/USD", "INJ/USD", "FET/USD",
        ]
        
    async def start(self):
        """Start the bot."""
        self.running = True
        
        # Connect to exchange
        self.exchange = ccxt.kraken({
            "apiKey": os.getenv("EXCHANGE_API_KEY"),
            "secret": os.getenv("EXCHANGE_SECRET_KEY"),
            "enableRateLimit": True,
        })
        
        self.logger.info("=" * 60)
        self.logger.info("EMA 9/20 CROSSOVER BOT STARTED")
        self.logger.info("=" * 60)
        self.logger.info(f"Strategy: Buy when EMA {self.ema_fast} > EMA {self.ema_slow} with widening gap")
        self.logger.info(f"Position Size: {self.position_size_pct}% | Reserve: {self.min_reserve_pct}%")
        self.logger.info(f"Max Positions: {self.max_positions}")
        self.logger.info("=" * 60)
        
        try:
            # Cancel all existing orders
            await self.cancel_all_orders()
            
            # Check existing balances for positions
            await self.sync_positions()
            
            # Main loop
            while self.running:
                try:
                    await self.run_cycle()
                    await asyncio.sleep(60)  # Check every minute
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Cycle error: {e}")
                    await asyncio.sleep(30)
                    
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        """Cleanup."""
        self.running = False
        if self.exchange:
            await self.exchange.close()
        self.logger.info("Bot shutdown complete")
        
    async def cancel_all_orders(self):
        """Cancel all open orders."""
        try:
            orders = await self.exchange.fetch_open_orders()
            if orders:
                self.logger.info(f"Cancelling {len(orders)} open orders...")
                for order in orders:
                    try:
                        await self.exchange.cancel_order(order["id"], order["symbol"])
                        self.logger.info(f"  Cancelled: {order['side']} {order['amount']} {order['symbol']} @ ${order['price']}")
                    except Exception as e:
                        self.logger.warning(f"  Failed to cancel {order['id']}: {e}")
            else:
                self.logger.info("No open orders to cancel")
        except Exception as e:
            self.logger.error(f"Error cancelling orders: {e}")
            
    async def sync_positions(self):
        """Check existing crypto balances as positions."""
        try:
            balance = await self.exchange.fetch_balance()
            
            self.logger.info("Current balances:")
            for currency, amount in balance["total"].items():
                if amount > 0 and currency != "USD":
                    pair = f"{currency}/USD"
                    if pair in self.candidate_pairs:
                        # Get current price
                        try:
                            ticker = await self.exchange.fetch_ticker(pair)
                            price = ticker["last"]
                            value = amount * price
                            if value > 5:  # Only track if worth > $5
                                self.positions[pair] = {
                                    "qty": amount,
                                    "entry_price": price,  # Assume current price as entry
                                    "entry_time": datetime.now(),
                                }
                                self.logger.info(f"  {pair}: {amount:.4f} (~${value:.2f})")
                        except:
                            pass
                            
            usd = balance["total"].get("USD", 0)
            self.logger.info(f"  USD: ${usd:.2f}")
            self.logger.info(f"Active positions: {len(self.positions)}")
            
        except Exception as e:
            self.logger.error(f"Error syncing positions: {e}")
            
    async def run_cycle(self):
        """Run one analysis cycle."""
        self.logger.info(f"\n--- Cycle at {datetime.now().strftime('%H:%M:%S')} ---")
        
        # Analyze all pairs
        signals = await self.scan_all_pairs()
        
        # Get actionable signals
        buy_signals = [(p, s) for p, s in signals.items() if s["action"] in ("BUY", "SAFE_BUY")]
        sell_signals = [(p, s) for p, s in signals.items() if s["action"] == "SELL"]
        
        # Process sells first (for positions we hold)
        for pair, sig in sell_signals:
            if pair in self.positions:
                await self.execute_sell(pair, sig)
                
        # Process buys (if we have room)
        if len(self.positions) < self.max_positions:
            # Sort by spread change (momentum)
            buy_signals.sort(key=lambda x: x[1]["spread_change"], reverse=True)
            
            for pair, sig in buy_signals:
                if pair not in self.positions and len(self.positions) < self.max_positions:
                    await self.execute_buy(pair, sig)
                    
    async def scan_all_pairs(self) -> dict:
        """Scan all pairs for signals."""
        signals = {}
        
        for pair in self.candidate_pairs:
            try:
                sig = await self.analyze_pair(pair)
                if sig:
                    signals[pair] = sig
                    
                    # Log significant signals
                    if sig["action"] in ("BUY", "SAFE_BUY"):
                        self.logger.info(f"  [BUY] {pair}: {sig['action']} - spread {sig['spread']:.2f}%, delta {sig['spread_change']:+.3f}%")
                    elif sig["action"] == "SELL":
                        self.logger.info(f"  [SELL] {pair}: SELL signal")
                        
            except Exception as e:
                self.logger.debug(f"Error analyzing {pair}: {e}")
                
        return signals
        
    async def analyze_pair(self, pair: str) -> dict:
        """Analyze a single pair for EMA signals."""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(pair, "15m", limit=50)
            df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
            
            if len(df) < 25:
                return None
                
            # Calculate EMAs
            ema_9 = df["close"].ewm(span=self.ema_fast, adjust=False).mean()
            ema_20 = df["close"].ewm(span=self.ema_slow, adjust=False).mean()
            
            current_9 = ema_9.iloc[-1]
            current_20 = ema_20.iloc[-1]
            prev_9 = ema_9.iloc[-2]
            prev_20 = ema_20.iloc[-2]
            prev2_9 = ema_9.iloc[-3]
            prev2_20 = ema_20.iloc[-3]
            price = df["close"].iloc[-1]
            
            # Calculate spreads
            spread = ((current_9 - current_20) / current_20) * 100
            prev_spread = ((prev_9 - prev_20) / prev_20) * 100
            prev2_spread = ((prev2_9 - prev2_20) / prev2_20) * 100
            spread_change = spread - prev_spread
            spread_trend = spread - prev2_spread
            
            # Determine action
            if prev_9 <= prev_20 and current_9 > current_20:
                action = "BUY"  # Fresh crossover
            elif prev_9 >= prev_20 and current_9 < current_20:
                action = "SELL"  # Bearish crossover
            elif current_9 > current_20:
                if spread_change > 0 and spread_trend > 0:
                    action = "SAFE_BUY"  # Gap widening
                elif spread < 0.1 or spread_change < -0.05:
                    action = "WARN_SELL"  # Gap closing
                else:
                    action = "HOLD"
            else:
                action = "AVOID"
                
            return {
                "price": price,
                "ema_9": current_9,
                "ema_20": current_20,
                "spread": spread,
                "spread_change": spread_change,
                "action": action,
            }
            
        except Exception:
            return None
            
    async def execute_buy(self, pair: str, signal: dict):
        """Execute a market buy."""
        try:
            # Get balance
            balance = await self.exchange.fetch_balance()
            usd = balance["total"].get("USD", 0)
            
            # Calculate position size
            reserve = usd * (self.min_reserve_pct / 100)
            available = usd - reserve
            
            if available < 10:
                self.logger.warning(f"Insufficient funds: ${usd:.2f} (reserve ${reserve:.2f})")
                return
                
            position_value = available * (self.position_size_pct / 100)
            price = signal["price"]
            qty = position_value / price
            
            # Round to appropriate precision
            try:
                market = await self.exchange.load_markets()
                if pair in market:
                    amount_precision = market[pair].get("precision", {}).get("amount", 8)
                    if isinstance(amount_precision, int):
                        qty = round(qty, amount_precision)
                    else:
                        qty = round(qty, 4)  # Default to 4 decimals
            except:
                qty = round(qty, 4)  # Fallback
                
            self.logger.info(f">>> BUYING {qty:.4f} {pair} @ ${price:.4f} (${position_value:.2f})")
            
            # Execute
            order = await self.exchange.create_market_buy_order(pair, qty)
            
            if order:
                self.positions[pair] = {
                    "qty": qty,
                    "entry_price": price,
                    "entry_time": datetime.now(),
                }
                self.logger.info(f"[OK] BUY FILLED: {pair}")
            
        except Exception as e:
            self.logger.error(f"Buy error for {pair}: {e}")
            
    async def execute_sell(self, pair: str, signal: dict):
        """Execute a market sell."""
        try:
            pos = self.positions.get(pair)
            if not pos:
                return
                
            qty = pos["qty"]
            entry = pos["entry_price"]
            price = signal["price"]
            pnl = (price - entry) * qty
            pnl_pct = ((price / entry) - 1) * 100
            
            self.logger.info(f"<<< SELLING {qty:.4f} {pair} @ ${price:.4f} (P&L: ${pnl:.2f} / {pnl_pct:+.2f}%)")
            
            # Execute
            order = await self.exchange.create_market_sell_order(pair, qty)
            
            if order:
                del self.positions[pair]
                self.logger.info(f"[OK] SELL FILLED: {pair} | P&L: ${pnl:.2f}")
                
        except Exception as e:
            self.logger.error(f"Sell error for {pair}: {e}")


async def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("ema_bot.log"),
        ]
    )
    
    bot = EMACrossoverBot()
    
    # Handle Ctrl+C
    def handle_signal(sig, frame):
        print("\nShutting down...")
        bot.running = False
        
    signal.signal(signal.SIGINT, handle_signal)
    
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
