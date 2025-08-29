import streamlit as st
import pandas as pd
from datetime import datetime
import yfinance as yf
import time
from concurrent.futures import ThreadPoolExecutor

# --- Top S&P 500 tickers ---
TOP_SP500_TICKERS = ["NVDA", "MSFT", "AAPL", "AMZN", "META", "GOOGL", "AVGO", "BRK.B", "TSLA", "JPM"]

# --- Fetch ticker data with proper numeric handling ---
def update_ticker_data(
    ticker,
    latest_only=False,
    retries=3,
    delay=5,
    period="30d",
    start_date=None,
    end_date=None
):
    attempt = 0
    while attempt < retries:
        try:
            # Fetch data
            if start_date and end_date:
                data = yf.download(ticker, start=start_date, end=end_date, interval="1d")
            else:
                data = yf.download(ticker, period=period, interval="1d")

            if data.empty:
                st.warning(f"No data found for ticker: {ticker}")
                return pd.DataFrame()

            # Keep only essential columns
            data = data.reset_index()
            data = data[['Date', 'Open', 'Low', 'High', 'Close']].copy()

            # Ensure numeric types
            for col in ['Open', 'Low', 'High', 'Close']:
                data[col] = pd.to_numeric(data[col], errors='coerce')

            # Drop rows with missing values
            data = data.dropna(subset=['Open', 'Low', 'High', 'Close'])

            # Calculate metrics
            data['Upward_Move'] = data['High'] - data['Low']
            data['Upward_Move_%'] = (data['Upward_Move'] / data['Low']) * 100
            data['Daily_Range'] = data['Close'] - data['Open']

            if latest_only:
                data = data.iloc[[-1]].reset_index(drop=True)

            return data

        except Exception as e:
            attempt += 1
            st.warning(f"Attempt {attempt} failed for ticker {ticker}: {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                return pd.DataFrame()

# --- Multithreaded fetch for latest day ---
def fetch_all_latest(top_tickers):
    all_data = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = {executor.submit(update_ticker_data, t, True): t for t in top_tickers}
        for future in results:
            ticker = results[future]
            df = future.result()
            if not df.empty:
                all_data[ticker] = df
    if all_data:
        combined_df = pd.concat(all_data, names=['Ticker', 'Row']).reset_index(level=1, drop=True).reset_index()
        return combined_df
    else:
        return pd.DataFrame()

# --- Streamlit caching ---
@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_latest_data():
    return fetch_all_latest(TOP_SP500_TICKERS)

# --- Streamlit app ---
st.title("Top S&P 500 Stocks Dashboard")
st.write("Fetching latest data for top S&P 500 stocks...")

latest_data = get_latest_data()

if latest_data.empty:
    st.warning("No data available.")
else:
    st.subheader("Latest Day Metrics")
    st.dataframe(latest_data)

    st.subheader("Top Movers by Upward Move %")
    top_movers = latest_data.sort_values("Upward_Move_%", ascending=False)
    st.dataframe(top_movers[['Ticker', 'Date', 'Upward_Move', 'Upward_Move_%', 'Daily_Range']].head(10))

# --- Full 30-day data on demand ---
if st.checkbox("Show full 30-day historical data"):
    st.info("Fetching full 30-day data (may take a few seconds)...")
    full_data_list = []
    for ticker in TOP_SP500_TICKERS:
        df = update_ticker_data(ticker, latest_only=False)
        if not df.empty:
            df['Ticker'] = ticker
            full_data_list.append(df)
    if full_data_list:
        full_data = pd.concat(full_data_list).reset_index(drop=True)
        st.subheader("Full 30-Day Data")
        st.dataframe(full_data)
    else:
        st.warning("No historical data available.")
