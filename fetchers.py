import requests
from datetime import datetime, timedelta
import yfinance as yf

def fetch_crypto_data(symbol, start_date, end_date):
    """
    Fetch multi-year historical crypto data using Binance API.

    Args:
        symbol (str): The trading pair symbol (e.g., "BTCUSDT").
        start_date (str): Start date in "YYYY-MM-DD" format.
        end_date (str): End date in "YYYY-MM-DD" format.

    Returns:
        dict: Historical price data in the format {datetime: price}.
    """
    base_url = "https://api.binance.com/api/v3/klines"
    interval = "1d"  # Daily data
    max_candles = 1000  # Binance's maximum candles per request
    price_data = {}

    # Convert start and end dates to datetime objects
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    current_start = start_dt

    while current_start < end_dt:
        # Calculate the end of the current chunk
        current_end = current_start + timedelta(days=max_candles - 1)
        if current_end > end_dt:
            current_end = end_dt

        # Convert dates to milliseconds
        start_timestamp = int(current_start.timestamp() * 1000)
        end_timestamp = int(current_end.timestamp() * 1000)

        # Fetch data for the current chunk
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'startTime': start_timestamp,
            'endTime': end_timestamp,
            'limit': max_candles,
        }
        response = requests.get(base_url, params=params)
        data = response.json()

        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code} - {response.text}")
            break

        # Parse and store prices
        for entry in data:
            date = datetime.fromtimestamp(entry[0] / 1000)  # Convert milliseconds to datetime
            close_price = float(entry[4])  # Close price
            price_data[date] = close_price

        # Move to the next chunk
        current_start = current_end + timedelta(days=1)

    return price_data
    
def fetch_stock_data_yahoo(symbol, start_date, end_date):
    """
    Fetch historical stock data using Yahoo Finance and parse it into
    a dictionary format: {datetime: price}
    """
    # Fetch data using yfinance
    stock_data = yf.download(symbol, start=start_date, end=end_date)

    # Parse the data into a dictionary {datetime: price}
    price_data = {}
    for index, row in stock_data.iterrows():
        # Ensure the index is converted to a Python datetime object
        date = datetime.strptime(str(index.date()), "%Y-%m-%d")
        # Use the closing price for each day
        price_data[date] = row['Close']

    return price_data