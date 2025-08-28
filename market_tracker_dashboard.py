import yfinance as yf
import pandas as pd
import streamlit as st
import os

# -------------------------
# SETTINGS
# -------------------------
tickers = ["AAPL", "MSFT", "TSLA"]  # Add or change tickers here
interval = "1d"
output_folder = "market_data"
os.makedirs(output_folder, exist_ok=True)

st.title("📈 Market Tracker: Daily Lows & Upward Moves")
st.write("Tracks daily lows and upward price movements from the low to close.")

# -------------------------
# FUNCTION TO UPDATE DATA
# -------------------------
def update_ticker_data(ticker):
    csv_file = os.path.join(output_folder, f"{ticker}_market_data.csv")
    
    # Load existing data if present
    if os.path.exists(csv_file):
        existing_data = pd.read_csv(csv_file, index_col=0, parse_dates=True)
        start_date = existing_data.index[-1] + pd.Timedelta(days=1)
    else:
        existing_data = pd.DataFrame()
        start_date = None
    
    # Download new data
    new_data = yf.download(ticker, start=start_date, interval=interval)
    if new_data.empty:
        return existing_data  # nothing new
    
    # Calculate metrics
    new_data['Daily_Low'] = new_data['Low']
    new_data['Upward_Move'] = new_data['Close'] - new_data['Low']
    new_data['Upward_Move_%'] = (new_data['Upward_Move'] / new_data['Low']) * 100
    
    # Combine with existing data
    if not existing_data.empty:
        data = pd.concat([existing_data, new_data])
    else:
        data = new_data
    
    # Save updated CSV
    data.to_csv(csv_file)
    return data

# -------------------------
# UPDATE DATA AND DISPLAY
# -------------------------
for ticker in tickers:
    st.subheader(f"{ticker}")
    data = update_ticker_data(ticker)
    
    if data.empty:
        st.warning(f"No data available for {ticker}")
        continue
    
    # Summary stats
    avg_upward = data['Upward_Move'].mean()
    avg_upward_pct = data['Upward_Move_%'].mean()
    
    st.write(f"**Average Upward Move from Low to Close:** {avg_upward:.2f} (${avg_upward_pct:.2f}%)")
    st.write(f"**Latest Daily Low:** {data['Daily_Low'][-1]:.2f}")
    st.write(f"**Latest Upward Move:** {data['Upward_Move'][-1]:.2f} (${data['Upward_Move_%'][-1]:.2f}%)")
    
    # Display table
    st.dataframe(data[['Open','High','Daily_Low','Close','Upward_Move','Upward_Move_%']])
    
    # Plot chart (Upward movement trend)
    st.line_chart(data[['Upward_Move','Upward_Move_%']])
