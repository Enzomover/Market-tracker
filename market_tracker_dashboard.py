import streamlit as st
import pandas as pd
import yfinance as yf
import time
from concurrent.futures import ThreadPoolExecutor

# --- Top S&P 500 tickers ---
TOP_SP500_TICKERS = ["NVDA", "MSFT", "AAPL", "AMZN", "META", "GOOGL", "AVGO", "BRK.B", "TSLA", "JPM"]

# --- Safe ticker data fetch ---
def update_ticker_data(ticker, latest_only=False, retries=3, delay=2, period="30d"):
    for attempt in range(retries):
        try:
            # Download data
            data = yf.download(ticker, period=period, interval="1d")
            if data.empty:
                continue  # retry

            # Reset index and select only necessary columns
            data = data.reset_index()
            required_cols = ['Date', 'Open', 'High', 'Low', 'Close']
            data = data[[col for col in required_cols if col in data.columns]]

            # Ensure numeric
            for col in ['Open','High','Low','Close']:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')

            # Drop rows with NaNs
            data = data.dropna(subset=['Open','High','Low','Close'])
            if data.empty:
                continue  # retry

            # Calculate metrics safely
            data['Upward_Move'] = data['High'] - data['Low']
            data['Upward_Move_%'] = (data['Upward_Move'] / data['Low']).replace([float('inf'), -float('inf')], 0).fillna(0) * 100
            data['Daily_Range'] = data['Close'] - data['Open']

            if latest_only:
                data = data.iloc[[-1]].reset_index(drop=True)

            return data

        except Exception as e:
            st.warning(f"{ticker} attempt {attempt+1} failed: {e}")
            time.sleep(delay)

    st.warning(f"{ticker} failed after {retries} attempts")
    return pd.DataFrame()

# --- Multithreaded latest-day fetch ---
def fetch_all_latest(top_tickers):
    all_data = {}

    def fetch(ticker):
        return update_ticker_data(ticker, latest_only=True)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch, t): t for t in top_tickers}
        for future in futures:
            ticker = futures[future]
            df = future.result()
            if not df.empty:
                all_data[ticker] = df

    if all_data:
        combined_df = pd.concat(all_data, names=['Ticker','Row']).reset_index(level=1, drop=True).reset_index()
        return combined_df
    else:
        return pd.DataFrame()

# --- Streamlit caching ---
@st.cache_data(ttl=600)
def get_latest_data():
    return fetch_all_latest(TOP_SP500_TICKERS)

# --- Streamlit app ---
st.title("Top S&P 500 Stocks Dashboard")
st.write("Fetching latest data for top S&P 500 stocks...")

latest_data = get_latest_data()

if latest_data.empty:
    st.warning("No data available. Please try again later.")
else:
    st.subheader("Latest Day Metrics")
    st.dataframe(latest_data)

    st.subheader("Top Movers by Upward Move %")
    top_movers = latest_data.sort_values("Upward_Move_%", ascending=False)
    st.dataframe(top_movers[['Ticker','Date','Upward_Move','Upward_Move_%','Daily_Range']].head(10))

# --- Optional full 30-day fetch ---
if st.checkbox("Show full 30-day historical data"):
    st.info("Fetching full 30-day data (may take a few seconds)...")
    full_data_list = []

    def fetch_full(ticker):
        df = update_ticker_data(ticker, latest_only=False)
        if not df.empty:
            df['Ticker'] = ticker
        return df

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch_full, t): t for t in TOP_SP500_TICKERS}
        for future in futures:
            df = future.result()
            if df is not None and not df.empty:
                full_data_list.append(df)

    if full_data_list:
        full_data = pd.concat(full_data_list).reset_index(drop=True)
        st.subheader("Full 30-Day Data")
        st.dataframe(full_data)
    else:
        st.warning("No historical data available.")
