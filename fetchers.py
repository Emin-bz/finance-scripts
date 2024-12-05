import requests
import os
import json
import pickle
from datetime import datetime, timedelta
import yfinance as yf

CACHE_DIR = "./cache"  # Directory to store cached data
os.makedirs(CACHE_DIR, exist_ok=True)

def load_cache(file_name):
    """Load cached data from a file."""
    cache_path = os.path.join(CACHE_DIR, file_name)
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    return {}

def save_cache(file_name, data):
    """Save data to a cache file."""
    cache_path = os.path.join(CACHE_DIR, file_name)
    with open(cache_path, 'wb') as f:
        pickle.dump(data, f)

def fetch_crypto_data(symbol, start_date, end_date):
    """
    Fetch multi-year historical crypto data using Binance API with caching.

    Args:
        symbol (str): The trading pair symbol (e.g., "BTCUSDT").
        start_date (str): Start date in "YYYY-MM-DD" format.
        end_date (str): End date in "YYYY-MM-DD" format.

    Returns:
        dict: Historical price data in the format {datetime: price}.
    """
    cache_file = f"{symbol}_crypto.pkl"
    price_data = load_cache(cache_file)

    # Determine the range to fetch based on the cache
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    cached_dates = set(price_data.keys())
    fetch_start = max(cached_dates) if cached_dates else start_dt
    fetch_end = end_dt

    if fetch_start < fetch_end:
        base_url = "https://api.binance.com/api/v3/klines"
        interval = "4h"  # 1-minute data
        max_candles = 1000  # Binance's maximum candles per request

        current_start = fetch_start
        while current_start < fetch_end:
            current_end = current_start + timedelta(hours=4 * max_candles - 1)
            if current_end > fetch_end:
                current_end = fetch_end

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

            current_start = current_end + timedelta(minutes=1)

    save_cache(cache_file, price_data)
    return price_data


def fetch_stock_data_yahoo(symbol, start_date, end_date):
    """
    Fetch historical stock data using Yahoo Finance with caching.

    Args:
        symbol (str): The stock ticker symbol (e.g., "AAPL").
        start_date (str): Start date in "YYYY-MM-DD" format.
        end_date (str): End date in "YYYY-MM-DD" format.

    Returns:
        dict: Historical price data in the format {datetime: price}.
    """
    cache_file = f"{symbol}_stock.pkl"
    price_data = load_cache(cache_file)

    # Determine the range to fetch based on the cache
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    cached_dates = set(price_data.keys())
    fetch_start = max(cached_dates) if cached_dates else start_dt
    fetch_end = end_dt

    if fetch_start < fetch_end:
        # Fetch data using yfinance
        stock_data = yf.download(symbol, start=fetch_start.strftime("%Y-%m-%d"), end=fetch_end.strftime("%Y-%m-%d"))

        # Parse the data into a dictionary
        for index, row in stock_data.iterrows():
            date = index.to_pydatetime()  # Ensure `datetime` object
            price_data[date] = row['Close']

    save_cache(cache_file, price_data)
    return price_data
