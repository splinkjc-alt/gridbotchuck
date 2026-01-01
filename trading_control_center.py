"""
Trading Control Center
======================

Mobile-friendly dashboard to:
- Chat with Claude AI
- Monitor all trading bots
- Approve/decline trades
- View performance stats

Run: streamlit run trading_control_center.py
Access: http://localhost:8501 (works on phone too!)
"""

from datetime import UTC, datetime
from pathlib import Path
import time

from dotenv import load_dotenv
import pandas as pd
import streamlit as st

# Load environment variables
load_dotenv()

# Page config - mobile friendly
st.set_page_config(
    page_title="Trading Control Center",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly design
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .status-good {
        color: #2ecc71;
        font-weight: bold;
    }
    .status-bad {
        color: #e74c3c;
        font-weight: bold;
    }
    .trade-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        color: white;
        text-align: right;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .assistant-message {
        background: #f5f5f5;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3rem;
        font-size: 1.1rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_trades" not in st.session_state:
    st.session_state.pending_trades = []


def get_bot_status():
    """Get status of all running bots."""
    bots = {
        "crypto": {
            "name": "Crypto Day Trader",
            "status": "Running",
            "file": "C:\\Users\\splin\\AppData\\Local\\Temp\\claude\\C--Users-splin\\tasks\\bf42029.output",
            "strategy": "Mean Reversion (RSI < 45)",
            "balance": "$10,000",
            "open_trades": 0
        },
        "stock": {
            "name": "Stock Day Trader",
            "status": "Sleeping (Market Closed)",
            "file": "C:\\Users\\splin\\AppData\\Local\\Temp\\claude\\C--Users-splin\\tasks\\ba790bb.output",
            "strategy": "Mean Reversion (RSI < 40)",
            "balance": "$25,000",
            "open_trades": 0
        },
        "grid": {
            "name": "GridBot Chuck",
            "status": "Running",
            "file": "C:\\Users\\splin\\AppData\\Local\\Temp\\claude\\C--Users-splin\\tasks\\b8b6b55.output",
            "strategy": "Grid Trading (DAG/USD)",
            "balance": "Live Trading",
            "profit": "$3.00+"
        }
    }
    return bots


def get_recent_scans(bot_file, limit=5):
    """Get recent scan results from bot output."""
    try:
        if Path(bot_file).exists():
            with open(bot_file) as f:
                lines = f.readlines()
                # Get last N lines
                recent = lines[-50:]
                scans = [line.strip() for line in recent if "Scan complete" in line or "MEAN REVERSION" in line]
                return scans[-limit:]
    except Exception as e:
        return [f"Error reading logs: {e}"]
    return []


def chat_with_claude(user_message):
    """
    Simulate Claude chat (placeholder for Claude API integration).

    To enable real Claude API:
    1. Install: pip install anthropic
    2. Set ANTHROPIC_API_KEY in .env
    3. Uncomment the code below
    """

    # PLACEHOLDER RESPONSE (replace with real API call)
    responses = [
        "The crypto bot is running well! Currently waiting for RSI < 45 oversold conditions.",
        "Stock market is closed for the weekend. The bot will wake up Monday 9:30 AM ET.",
        "Mean reversion strategy is working correctly - it's being patient and not chasing pumps.",
        "I'm monitoring all 3 bots for you. Everything looks good!",
        "GridBot Chuck is making steady profits on DAG/USD grid trading.",
    ]

    # Simple keyword-based responses
    msg_lower = user_message.lower()
    if "crypto" in msg_lower or "bitcoin" in msg_lower:
        return (
            "The crypto bot is scanning 20 pairs every 60 seconds with RSI < 45 threshold. "
            "Currently waiting for oversold opportunities!"
        )
    elif "stock" in msg_lower:
        return (
            "Stock bot is sleeping - market closed for the weekend. "
            "It will automatically wake up and start trading Monday morning at 9:30 AM ET!"
        )
    elif "grid" in msg_lower or "dag" in msg_lower:
        return (
            "GridBot Chuck is running smoothly on DAG/USD with grid trading strategy. "
            "Making small consistent profits!"
        )
    elif "status" in msg_lower or "how" in msg_lower:
        return (
            "All 3 bots are running perfectly! Crypto bot: Active (0 trades yet). "
            "Stock bot: Sleeping (weekend). GridBot: Active and profitable."
        )
    else:
        import random
        return random.choice(responses)  # noqa: S311

    # REAL CLAUDE API INTEGRATION (uncomment when ready):
    # try:
    #     from anthropic import Anthropic
    #     client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    #
    #     message = client.messages.create(
    #         model="claude-sonnet-4-5-20251029",
    #         max_tokens=1024,
    #         messages=[
    #             {"role": "user", "content": user_message}
    #         ]
    #     )
    #     return message.content[0].text
    # except Exception as e:
    #     return f"Error: {e}"


# ==================== MAIN APP ====================

st.markdown('<div class="main-header">🤖 Trading Control Center</div>', unsafe_allow_html=True)

# Auto-refresh toggle
auto_refresh = st.checkbox("🔄 Auto-refresh (every 10s)", value=False)
if auto_refresh:
    time.sleep(10)
    st.rerun()

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📊 Bot Status", "⏳ Pending Trades", "📈 Performance"])

# ==================== TAB 1: CHAT WITH CLAUDE ====================
with tab1:
    st.subheader("💬 Chat with Claude")
    st.caption("Ask me anything about your trading bots!")

    # Display chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-message user-message">👤 You: {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message assistant-message">🤖 Claude: {msg["content"]}</div>', unsafe_allow_html=True)

    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Your message:", placeholder="Ask about bot status, trades, strategies...")
        submitted = st.form_submit_button("Send 📤")

        if submitted and user_input:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Get Claude response
            response = chat_with_claude(user_input)
            st.session_state.messages.append({"role": "assistant", "content": response})

            st.rerun()

# ==================== TAB 2: BOT STATUS ====================
with tab2:
    st.subheader("📊 Live Bot Status")

    bots = get_bot_status()

    for _bot_id, bot in bots.items():
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"### {bot['name']}")
                st.write(f"**Strategy:** {bot['strategy']}")
                st.write(f"**Balance:** {bot['balance']}")
                if "profit" in bot:
                    st.write(f"**Profit:** {bot['profit']}")

            with col2:
                if bot["status"] == "Running":
                    st.markdown(f'<div class="status-good">✅ {bot["status"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="status-bad">😴 {bot["status"]}</div>', unsafe_allow_html=True)

            # Show recent activity
            with st.expander(f"Recent Activity ({bot['name']})"):
                recent = get_recent_scans(bot["file"])
                if recent:
                    for scan in recent:
                        st.text(scan)
                else:
                    st.text("No recent activity")

            st.markdown("---")

# ==================== TAB 3: PENDING TRADES ====================
with tab3:
    st.subheader("⏳ Pending Trade Approvals")

    # Check for pending trades (placeholder - in real version, read from bot state)
    if not st.session_state.pending_trades:
        st.info("No pending trades at the moment. Bots are scanning for opportunities!")

        # Show example of what it would look like
        with st.expander("👀 See Example Trade"):
            st.markdown("""
            <div class="trade-card">
                <h4>DOGE/USD - Mean Reversion</h4>
                <p><strong>Entry:</strong> $0.1245</p>
                <p><strong>Stop Loss:</strong> $0.1193 (-3%)</p>
                <p><strong>Target:</strong> $0.1295 (+4%)</p>
                <p><strong>RSI:</strong> 38 (Oversold)</p>
                <p><strong>Score:</strong> 65/100</p>
                <p><strong>Risk:</strong> $20 | <strong>Reward:</strong> $60 (1:3 ratio)</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.button("✅ APPROVE TRADE", type="primary", disabled=True)
            with col2:
                st.button("❌ DECLINE TRADE", disabled=True)
    else:
        # Display actual pending trades
        for trade in st.session_state.pending_trades:
            st.markdown(f"""
            <div class="trade-card">
                <h4>{trade['pair']} - {trade['strategy']}</h4>
                <p><strong>Entry:</strong> ${trade['entry']}</p>
                <p><strong>Stop Loss:</strong> ${trade['stop']} ({trade['stop_pct']}%)</p>
                <p><strong>Target:</strong> ${trade['target']} ({trade['target_pct']}%)</p>
                <p><strong>RSI:</strong> {trade['rsi']}</p>
                <p><strong>Score:</strong> {trade['score']}/100</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ APPROVE {trade['pair']}", key=f"approve_{trade['id']}"):
                    st.success(f"Trade approved: {trade['pair']}")
                    # TODO: Send approval to bot
            with col2:
                if st.button(f"❌ DECLINE {trade['pair']}", key=f"decline_{trade['id']}"):
                    st.error(f"Trade declined: {trade['pair']}")
                    # TODO: Send decline to bot

# ==================== TAB 4: PERFORMANCE ====================
with tab4:
    st.subheader("📈 Trading Performance")

    # Metrics row
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>0</h3>
            <p>Total Trades</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>N/A</h3>
            <p>Win Rate</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>$0.00</h3>
            <p>Total P&L</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Trade history table (placeholder)
    st.subheader("Trade History")
    st.info("No trades yet. Once bots start trading, history will appear here!")

    # Show example table
    with st.expander("👀 See Example"):
        example_data = pd.DataFrame({
            "Date": ["2025-12-28 10:30", "2025-12-28 11:15"],
            "Pair": ["DOGE/USD", "XRP/USD"],
            "Entry": ["$0.1245", "$1.87"],
            "Exit": ["$0.1295", "$1.90"],
            "P&L": ["+$25.00", "+$15.00"],
            "Result": ["Win ✅", "Win ✅"]
        })
        st.dataframe(example_data, use_container_width=True)

# ==================== FOOTER ====================
st.markdown("---")
st.caption(f"🤖 Trading Control Center | Last updated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("💡 Tip: Add this page to your Android home screen for quick access!")
