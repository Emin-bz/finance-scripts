from datetime import datetime
import fetchers

class Trader:
    def __init__(self, cash, fee_percent=0.001, stop_loss_percent=5.0, max_holding_days=30, reseed=1000, profit_perc_threshold=1):
        self.cash = cash
        self.fee_percent = fee_percent  # Platform fee in percentage
        self.holdings = 0  # Number of units (crypto coins)
        self.last_purchase_price = 0
        self.purchase_date = None
        self.stop_loss_percent = stop_loss_percent  # Maximum loss threshold
        self.max_holding_days = max_holding_days  # Max days to hold asset
        self.reseed = reseed
        self.reseed_count = 0
        self.profit_perc_threshold = profit_perc_threshold

    def buy(self, price, date):
        # Calculate how many units (crypto coins) can be bought with available cash
        units = self.cash / price
        fee = self.cash * self.fee_percent
        self.holdings = units
        self.last_purchase_price = price
        self.purchase_date = date
        self.cash -= (price * units + fee)
        print(f"Bought {units:.6f} units at {price:.2f} per unit on {date.strftime('%Y-%m-%d %H:%M:%S')}. Remaining cash: {self.cash:.2f}")

    def sell(self, price, date):
        # Sell all holdings
        revenue = price * self.holdings
        fee = revenue * self.fee_percent
        self.cash += (revenue - fee)
        print(f"Sold {self.holdings:.6f} units at {price:.2f} per unit on {date.strftime('%Y-%m-%d %H:%M:%S')}. Total cash: {self.cash:.2f}\n")
        self.holdings = 0
        self.last_purchase_price = 0
        self.purchase_date = None

    def should_sell(self, current_price, current_date):
        # Calculate price decrease from the purchase price (stop-loss trigger)
        price_decrease_percent = ((self.last_purchase_price - current_price) / self.last_purchase_price) * 100

        # Stop-loss check
        if price_decrease_percent >= self.stop_loss_percent:
            print(f"Stop-loss triggered! Price dropped by {price_decrease_percent:.2f}%. Selling on {current_date.strftime('%Y-%m-%d %H:%M:%S')}...")
            return True

        # Holding period check
        if self.purchase_date and (current_date - self.purchase_date).days >= self.max_holding_days:
            print(f"Max holding period reached ({self.max_holding_days} days). Selling on {current_date.strftime('%Y-%m-%d %H:%M:%S')}...")
            return True

        return False
    
    def seed(self, date, seeding_table):
        truncated_date = datetime(date.year, date.month, date.day)
        if date.day % 28 == 0 and truncated_date not in seeding_table:
            self.cash += self.reseed
            self.reseed_count += 1
            seeding_table[truncated_date] = 1
    
    def trade(self, data):
        chart_data = list(data.items())

        seeding_table = {}
        
        #TODO: Build in a mechanism which checks there were e.g. 5 consecutive stop losses and if so, stop trading for 2 months or something like that.

        for i in range(30, len(chart_data)):
            date = chart_data[i][0]
            price = chart_data[i][1]
            chart_range_data = chart_data[i-30:i]
            
            self.seed(date, seeding_table)

            if self.holdings == 0:
                self.buy(price, date)
            else:
                # Calculate price increase in percentage (net of platform fees)
                price_increase_percent = ((price - self.last_purchase_price) / self.last_purchase_price) * 100
                net_increase = price_increase_percent - self.fee_percent * 2

                # Sell if price has increased by at least 0.5% net or if safety checks are triggered
                if net_increase >= self.profit_perc_threshold:
                    self.sell(price, date)
                elif self.should_sell(price, date):
                    self.sell(price, date)

        self.sell(data[sorted(data.keys())[-1]], sorted(data.keys())[-1])


if __name__ == "__main__":

    class KEYS:
        CRYPTO = 'crypto'
        STOCK = 'stock'
        PROFIT_THRESHOLD = 'profit_perc_threshold'
        FETCHER_FUNC = 'fetcherFunc'
        SYMBOL = 'symbol'
        TYPE = 'type'

    modes = {
        KEYS.CRYPTO: {
            KEYS.FETCHER_FUNC: fetchers.fetch_crypto_data,
            KEYS.PROFIT_THRESHOLD: 1
        },
        KEYS.STOCK: {
            KEYS.FETCHER_FUNC: fetchers.fetch_stock_data_yahoo,
            KEYS.PROFIT_THRESHOLD: 2
        }
    }

    assets = {
        'bitcoin': {KEYS.SYMBOL: "BTCUSDT", KEYS.TYPE: KEYS.CRYPTO},
        'solana': {KEYS.SYMBOL: "SOLUSDT", KEYS.TYPE: KEYS.CRYPTO},
        'ethereum': {KEYS.SYMBOL: "ETHUSDT", KEYS.TYPE: KEYS.CRYPTO},
        'xrp': {KEYS.SYMBOL: "XRPUSDT", KEYS.TYPE: KEYS.CRYPTO},
        'cardano': {KEYS.SYMBOL: "ADAUSDT", KEYS.TYPE: KEYS.CRYPTO},
        'shiba': {KEYS.SYMBOL: "SHIBUSDT", KEYS.TYPE: KEYS.CRYPTO},
        'sp500': {KEYS.SYMBOL: "^GSPC", KEYS.TYPE: KEYS.STOCK},
        'nvda': {KEYS.SYMBOL: "NVDA", KEYS.TYPE: KEYS.STOCK}
    }

    # Choose the asset (Bitcoin or Solana)
    asset_choice = input("Enter asset choice: ").lower()
    if asset_choice not in assets:
        raise ValueError("Invalid asset choice.")
    
    symbol = assets[asset_choice]['symbol'].lower()
    initial_cash = 1000
    start_date = "2020-01-01"
    end_date = "2024-12-31"
    
    mode = assets[asset_choice]['type']

    # Initialize the trader for the chosen cryptocurrency
    trader = Trader(initial_cash, stop_loss_percent=75.0, max_holding_days=30, reseed=300, profit_perc_threshold=modes[mode]['profit_perc_threshold'])
    
    # Fetch daily data for the given period from CoinGecko
    data = modes[mode]['fetcherFunc'](symbol=symbol, start_date=start_date, end_date=end_date)

    # Simulate trading
    trader.trade(data)

    print()
    print(f"Started with initial cash: {initial_cash}")
    print(f"Final cash: {trader.cash:.2f}")
    print(f"Final holdings: {trader.holdings:.6f} units")
    print(f"Reseeded {trader.reseed_count} times with {trader.reseed}$ total reseed of {trader.reseed * trader.reseed_count}$")
    print(f"Total net profit: {(trader.cash - initial_cash - trader.reseed_count * trader.reseed):.2f}")
