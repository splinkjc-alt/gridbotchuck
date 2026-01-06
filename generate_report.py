"""
Bot Performance Report Generator
================================
Generates daily/weekly reports for all trading bots.
"""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class BotStats:
    """Statistics for a single bot."""
    name: str
    exchange: str
    strategy: str
    mode: str = "LIVE"
    runtime_hours: float = 0
    current_price: float = 0
    grid_range: str = ""
    total_trades: int = 0
    buys: int = 0
    sells: int = 0
    realized_pnl: float = 0
    wins: int = 0
    losses: int = 0
    biggest_win: float = 0
    biggest_loss: float = 0
    biggest_win_pair: str = ""
    biggest_loss_pair: str = ""
    current_positions: list = field(default_factory=list)
    status: str = "Unknown"
    start_time: datetime = None


def parse_crosskiller_log(log_path: str) -> BotStats:
    """Parse Crosskiller EMA bot log file."""
    stats = BotStats(
        name="Crosskiller",
        exchange="Coinbase",
        strategy="EMA 9/20 Crossover"
    )

    if not os.path.exists(log_path):
        stats.status = "Log not found"
        return stats

    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Count trades
    buy_matches = re.findall(r'\[OK\] BUY FILLED: (\w+/\w+)', content)
    sell_matches = re.findall(r'\[OK\] SELL FILLED: (\w+/\w+) \| P&L: \$([+-]?\d+\.?\d*)', content)

    stats.buys = len(buy_matches)
    stats.sells = len(sell_matches)
    stats.total_trades = stats.buys + stats.sells

    # Calculate P&L
    for pair, pnl_str in sell_matches:
        pnl = float(pnl_str)
        stats.realized_pnl += pnl

        if pnl > 0:
            stats.wins += 1
            if pnl > stats.biggest_win:
                stats.biggest_win = pnl
                stats.biggest_win_pair = pair
        elif pnl < 0:
            stats.losses += 1
            if pnl < stats.biggest_loss:
                stats.biggest_loss = pnl
                stats.biggest_loss_pair = pair

    # Get current positions (last balance sync)
    balance_matches = re.findall(r'(\w+)/USD: [\d.]+ \(~\$[\d.]+\)', content)
    if balance_matches:
        # Get unique pairs from last few matches
        stats.current_positions = list(set(balance_matches[-6:]))

    # Get start time
    time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', content)
    if time_match:
        stats.start_time = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S')
        stats.runtime_hours = (datetime.now() - stats.start_time).total_seconds() / 3600

    # Check if still running (recent activity)
    last_cycle = re.findall(r'--- Cycle at (\d{2}:\d{2}:\d{2}) ---', content)
    if last_cycle:
        stats.status = "Active - Scanning"
    else:
        stats.status = "Unknown"

    return stats


def parse_grid_bot_log(log_path: str, name: str, pair: str) -> BotStats:
    """Parse grid trading bot log file."""
    stats = BotStats(
        name=name,
        exchange="Kraken",
        strategy=f"{pair} Grid Trading"
    )

    if not os.path.exists(log_path):
        stats.status = "Log not found"
        return stats

    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Get current price
    price_matches = re.findall(r'ticker current price: ([\d.]+)', content)
    if price_matches:
        stats.current_price = float(price_matches[-1])

    # Get grid range from filename
    range_match = re.search(r'range([\d.]+-[\d.]+)', log_path)
    if range_match:
        stats.grid_range = range_match.group(1).replace('-', ' - ')

    # Count grid executions
    exec_matches = re.findall(r'Executed|Grid level|order filled', content, re.IGNORECASE)
    stats.total_trades = len(exec_matches)

    # Check health status
    if "Bot health is within acceptable parameters" in content[-5000:]:
        stats.status = "Healthy"
    elif "error" in content[-1000:].lower():
        stats.status = "Error detected"
    else:
        stats.status = "Running"

    # Get start time
    time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', content)
    if time_match:
        stats.start_time = datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S')
        stats.runtime_hours = (datetime.now() - stats.start_time).total_seconds() / 3600

    return stats


def parse_marketbot_log(log_path: str) -> BotStats:
    """Parse stock trading bot log file."""
    stats = BotStats(
        name="Sleeping Marketbot",
        exchange="Alpaca",
        strategy="Mean Reversion (RSI < 40)"
    )

    if not os.path.exists(log_path):
        stats.status = "Log not found"
        return stats

    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Check if market is open
    if "Market closed" in content[-500:]:
        stats.status = "Waiting for market open"
    else:
        stats.status = "Active"

    # Get paper trades
    paper_trades = re.findall(r'PAPER TRADE OPENED: (\w+)', content)
    stats.current_positions = list(set(paper_trades))

    # Count opportunities found
    opps = re.findall(r'Found (\d+) opportunities', content)
    if opps:
        stats.total_trades = sum(int(o) for o in opps)

    return stats


def generate_markdown_report(stats_list: list[BotStats]) -> str:
    """Generate a markdown report from bot statistics."""
    now = datetime.now()

    report = f"""# Trading Bot Daily Report
**Generated:** {now.strftime('%B %d, %Y at %I:%M %p')}

---

"""

    for stats in stats_list:
        win_rate = 0
        if stats.wins + stats.losses > 0:
            win_rate = (stats.wins / (stats.wins + stats.losses)) * 100

        report += f"""## {stats.name}
**Exchange:** {stats.exchange} | **Mode:** {stats.mode} | **Strategy:** {stats.strategy}

| Metric | Value |
|--------|-------|
"""

        if stats.runtime_hours > 0:
            report += f"| **Runtime** | {stats.runtime_hours:.1f} hours |\n"

        if stats.current_price > 0:
            report += f"| **Current Price** | ${stats.current_price:,.4f} |\n"

        if stats.grid_range:
            report += f"| **Grid Range** | ${stats.grid_range} |\n"

        if stats.total_trades > 0:
            if stats.buys > 0 or stats.sells > 0:
                report += f"| **Total Trades** | {stats.total_trades} ({stats.buys} buys, {stats.sells} sells) |\n"
            else:
                report += f"| **Grid Executions** | {stats.total_trades} |\n"

        if stats.realized_pnl != 0 or stats.sells > 0:
            pnl_color = "+" if stats.realized_pnl >= 0 else ""
            report += f"| **Realized P&L** | **{pnl_color}${stats.realized_pnl:.2f}** |\n"

        if stats.wins + stats.losses > 0:
            report += f"| **Win Rate** | {win_rate:.0f}% ({stats.wins}W / {stats.losses}L) |\n"

        if stats.biggest_win > 0:
            report += f"| **Biggest Win** | {stats.biggest_win_pair} +${stats.biggest_win:.2f} |\n"

        if stats.biggest_loss < 0:
            report += f"| **Biggest Loss** | {stats.biggest_loss_pair} ${stats.biggest_loss:.2f} |\n"

        if stats.current_positions:
            positions_str = ", ".join(stats.current_positions[:5])
            report += f"| **Current Positions** | {positions_str} |\n"

        report += f"| **Status** | {stats.status} |\n"
        report += "\n---\n\n"

    # Summary
    total_pnl = sum(s.realized_pnl for s in stats_list)
    total_trades = sum(s.total_trades for s in stats_list)

    report += f"""## Summary
| Metric | Value |
|--------|-------|
| **Total Bots Running** | {len(stats_list)} |
| **Combined Trades** | {total_trades} |
| **Combined P&L** | **${total_pnl:+.2f}** |

---
*Report generated by GridBot Chuck Report Generator*
"""

    return report


def find_latest_log(logs_dir: str, pattern: str) -> str:
    """Find the most recent log file matching pattern."""
    logs_path = Path(logs_dir)
    if not logs_path.exists():
        return None

    matching = list(logs_path.glob(pattern))
    if not matching:
        return None

    return str(max(matching, key=lambda p: p.stat().st_mtime))


def main():
    """Generate report for all bots."""
    base_dir = Path(__file__).parent
    logs_dir = base_dir / "logs"

    stats_list = []

    # Crosskiller - check temp output file first, fallback to ema_bot.log
    crosskiller_log = None
    temp_outputs = Path(r"C:\Users\splin\AppData\Local\Temp\claude\C--Users-splin\tasks")
    if temp_outputs.exists():
        # Find most recent b*.output file
        outputs = list(temp_outputs.glob("b*.output"))
        if outputs:
            latest = max(outputs, key=lambda p: p.stat().st_mtime)
            # Check if it's the EMA bot
            with open(latest, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = f.read(2000)
                if 'EMABot' in first_lines or 'EMA 9/20' in first_lines:
                    crosskiller_log = str(latest)

    if not crosskiller_log:
        crosskiller_log = str(base_dir / "ema_bot.log")

    if os.path.exists(crosskiller_log):
        stats_list.append(parse_crosskiller_log(crosskiller_log))

    # Chuck (BTC grid)
    chuck_log = find_latest_log(str(logs_dir), "bot_BTC_USD_LIVE*.log")
    if chuck_log:
        stats_list.append(parse_grid_bot_log(chuck_log, "Chuck", "BTC/USD"))

    # Growler (ADA grid)
    growler_log = find_latest_log(str(logs_dir), "bot_ADA_USD_LIVE*.log")
    if growler_log:
        stats_list.append(parse_grid_bot_log(growler_log, "Growler", "ADA/USD"))

    # Marketbot - check temp outputs
    marketbot_log = None
    if temp_outputs.exists():
        outputs = list(temp_outputs.glob("b*.output"))
        for output in sorted(outputs, key=lambda p: p.stat().st_mtime, reverse=True):
            with open(output, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = f.read(2000)
                if 'Stock Trading' in first_lines or 'mean reversion' in first_lines.lower():
                    marketbot_log = str(output)
                    break

    if marketbot_log:
        stats_list.append(parse_marketbot_log(marketbot_log))

    # Generate report
    report = generate_markdown_report(stats_list)

    # Save report
    report_file = base_dir / f"reports/daily_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(report)
    print(f"\nReport saved to: {report_file}")

    return report


if __name__ == "__main__":
    main()
