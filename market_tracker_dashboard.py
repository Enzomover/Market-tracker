import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# List of top 10 S&P 500 stocks by market capitalization
TOP_SP500_TICKERS = ["NVDA", "MSFT", "AAPL", "AMZN", "META", "GOOGL", "AVGO", "BRK.B", "TSLA", "JPM"]

def update_ticker_data(
    ticker,
    latest_only=False,
    log_errors=True,
    log_file="ticker_errors.log",
    retries=3,
    delay=5,
    period="30d",
    start_date=None,
    end_date=None
):
    """
    Fetch stock data for a ticker with optional retries and custom date ranges.
    """
    attempt = 0
    while attempt < retries:
        try:
            # Fetch data with either start/end or period
            if start_date and end_date:
                data = yf.download(ticker, start=start_date, end=end_date, interval="1d").reset_index()
            else:
                data = yf.download(ticker, period=period, interval="1d").reset_index()

            if data.empty:
                msg = f"No data found for ticker: {ticker}"
                if log_errors:
                    with open(log_file, "a") as f:
                        f.write(f"{datetime.now()} - {msg}\n")
                print(msg)
                return pd.DataFrame()

            # Keep only useful columns
            data = data[['Date', 'Open', 'Low', 'High', 'Close']].copy()

            # Calculate metrics
            data['Upward_Move'] = data['High'] - data['Low']
            data['Upward_Move_%'] = (data['Upward_Move'] / data['Low']).replace([float('inf'), -float('inf')], 0) * 100
            data['Daily_Range'] = data['Close'] - data['Open']

            if latest_only:
                data = data.iloc[[-1]].reset_index(drop=True)

            return data

        except Exception as e:
            attempt += 1
            msg = f"Attempt {attempt} failed for ticker {ticker}: {e}"
            if log_errors:
                with open(log_file, "a") as f:
                    f.write(f"{datetime.now()} - {msg}\n")
            print(msg)
            if attempt < retries:
                time.sleep(delay)
            else:
                return pd.DataFrame()

# Fetch data for all top S&P 500 tickers
def fetch_top_sp500_data(latest_only=False, period="30d", start_date=None, end_date=None):
    all_data = {}
    for ticker in TOP_SP500_TICKERS:
        df = update_ticker_data(ticker, latest_only=latest_only, period=period, start_date=start_date, end_date=end_date)
        if not df.empty:
            all_data[ticker] = df
    if not all_data:
        print("No data available for top S&P 500 tickers.")
        return pd.DataFrame()
    # Combine into single DataFrame
    combined_df = pd.concat(all_data, names=['Ticker', 'Row']).reset_index(level=1, drop=True).reset_index()
    return combined_df

# Example usage:
# Full 30-day data for all top S&P 500 stocks
full_data = fetch_top_sp500_data(latest_only=False)

# Only latest day for dashboard summary
latest_data = fetch_top_sp500_data(latest_only=True)

# Display results
print(latest_data)
