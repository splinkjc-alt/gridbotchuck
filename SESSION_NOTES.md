# GridBot Chuck - Session Notes
## Date: 2026-01-08 06:02

## Current Bot Status

### 1. Chuck (Kraken)
- Pair: PEPE/USD
- Strategy: Grid trading with auto-pair selection
- Runner: run_smart_chuck.py

### 2. Growler (Kraken)
- Pair: VET/USD
- Strategy: Grid trading with auto-pair selection
- Runner: run_smart_growler.py
- Note: Auto-restarts if subprocess dies

### 3. CrossKiller (Coinbase)
- Strategy: EMA 9/20 Crossover
- Runner: run_crosskiller.py
- Safety: Stop-Loss -7%, Take-Profit +5%, Max Hold 6h

## Portfolio
- Kraken: ~\,910 USD
- Coinbase: ~\,100 USD
- Total: ~\,010 USD

## Recent Fixes
1. Fixed _get_balance() in ema_crossover_strategy.py
2. Fixed run_crosskiller.py startup balance check
3. Renamed COINBASE_PRIVATE_KEY to COINBASE_SECRET_KEY

## Bot Coordination
- shared_pair_tracker.py prevents trading same pairs
- Staggered scan times prevent API conflicts
