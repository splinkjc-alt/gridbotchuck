import streamlit as st
import pandas as pd
from main import MarketScanner

# Page Config
st.set_page_config(page_title="AI Market Scanner", page_icon="🤖", layout="wide")

# Title
st.title("🤖 AI Market Scanner")
st.markdown("Scanning **AI Stocks** and **Crypto Assets** using 4 distinct strategies.")

# Sidebar Configuration
st.sidebar.header("Configuration")
currency = st.sidebar.selectbox("Currency", ["USD", "EUR", "GBP"], index=0)
scan_limit = st.sidebar.number_input(
    "Limit Assets (0 = No Limit)", min_value=0, value=20, step=5
)

# Run Button
if st.sidebar.button("Run Scanner", type="primary"):
    # Initialize Scanner with UI overrides
    scanner = MarketScanner()
    scanner.currency = currency
    scanner.scan_limit = scan_limit if scan_limit > 0 else None

    # 1. Fetch Assets
    with st.spinner("Fetching Asset Lists..."):
        stocks = scanner.get_ai_stocks()
        crypto = scanner.get_ai_crypto_pairs()

    # 2. Initialize Results
    results = {"Long-Term": [], "Strategic": [], "Risk": [], "Trading": []}

    # 3. Scan Logic
    progress_bar = st.progress(0)
    status_text = st.empty()

    total_assets = len(stocks) + len(crypto)
    processed = 0

    # Scan Stocks
    for ticker in stocks:
        status_text.text(f"Scanning Stock: {ticker}...")
        data = scanner.get_stock_data(ticker)
        analysis = scanner.analyze_asset(ticker, data)

        if analysis:
            for category, result in analysis.items():
                results[category].append(result)

        processed += 1
        progress_bar.progress(processed / total_assets)

    # Scan Crypto
    for ticker in crypto:
        status_text.text(f"Scanning Crypto: {ticker}...")
        data = scanner.get_crypto_data(ticker)
        analysis = scanner.analyze_asset(ticker, data)

        if analysis:
            for category, result in analysis.items():
                results[category].append(result)

        processed += 1
        progress_bar.progress(processed / total_assets)

    status_text.text("Scan Complete!")
    progress_bar.empty()

    # 4. Display Results
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📈 Long-Term", "🚀 Strategic", "🛡️ Risk", "💰 Trading"]
    )

    def display_table(category, description):
        st.subheader(f"{category} Investor")
        st.caption(description)

        if not results[category]:
            st.info("No data available.")
            return

        # Sort and Create DataFrame
        sorted_data = sorted(results[category], key=lambda x: x[1], reverse=True)
        df = pd.DataFrame(sorted_data, columns=["Asset", "Score"])

        # Filter out errors (-999)
        df = df[df["Score"] != -999]

        # Formatting
        st.dataframe(
            df.style.format({"Score": "{:.2f}"}).background_gradient(
                cmap="Greens", subset=["Score"]
            ),
            use_container_width=True,
        )

    with tab1:
        display_table("Long-Term", "Strongest Trend (Price vs 200 SMA)")

    with tab2:
        display_table("Strategic", "Best Momentum (1-Month Return)")

    with tab3:
        display_table("Risk", "Safest Assets (Lowest Volatility)")

    with tab4:
        display_table("Trading", "Best Dip Buy Opportunities (Lowest RSI)")

else:
    st.info("Click 'Run Scanner' in the sidebar to start.")
