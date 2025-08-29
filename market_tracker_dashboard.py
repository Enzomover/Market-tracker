import yfinance as yf
import pandas as pd

def update_ticker_data(ticker):
    try:
        # Download last 30 days of daily data
        data = yf.download(ticker, period="30d", interval="1d").reset_index()

        # If no data is returned
        if data.empty:
            print(f"No data found for ticker: {ticker}")
            return pd.DataFrame()  # Return empty DataFrame

        # Keep only useful columns
        data = data[['Date', 'Open', 'Low', 'High', 'Close']].copy()

        # Calculate upward move and percentage
        data['Upward_Move'] = data['High'] - data['Low']
        data['Upward_Move_%'] = (data['Upward_Move'] / data['Low']).replace([float('inf'), -float('inf')], 0) * 100

        # Calculate daily range (Close - Open)
        data['Daily_Range'] = data['Close'] - data['Open']

        return data

    except Exception as e:
        print(f"Error updating ticker data for {ticker}: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error
