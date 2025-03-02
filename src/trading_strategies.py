import time
import uuid
from src.crypto_api_trading import CryptoAPITrading

class SimpleMovingAverageStrategy:
    def __init__(self, client: CryptoAPITrading, symbol: str, quantity: str):
        self.client = client
        self.symbol = symbol
        self.quantity = quantity
        self.price_history = []
        self.ma_period = 5  # 5-point moving average
        
    def collect_price_data(self):
        """Collect price data for the moving average calculation"""
        # In a real strategy, you'd collect historical data
        # For this example, we'll just get the current price
        result = self.client.get_best_bid_ask(self.symbol)
        if result and 'best_bid_ask' in result and len(result['best_bid_ask']) > 0:
            current_price = float(result['best_bid_ask'][0]['ask_price'])
            self.price_history.append(current_price)
            
            # Keep only the most recent prices for our moving average
            if len(self.price_history) > self.ma_period:
                self.price_history.pop(0)
                
            return current_price
        return None
    
    def calculate_moving_average(self):
        """Calculate the moving average from collected price data"""
        if len(self.price_history) < self.ma_period:
            return None
        return sum(self.price_history) / len(self.price_history)
    
    def execute(self):
        """Execute the trading strategy"""
        current_price = self.collect_price_data()
        moving_avg = self.calculate_moving_average()
        
        if not current_price or not moving_avg:
            print("Not enough data to execute strategy")
            return
        
        print(f"Current price: {current_price}, Moving Average: {moving_avg}")
        
        # Simple strategy: Buy if price is below MA, Sell if price is above MA
        if current_price < moving_avg * 0.98:  # Price is 2% below MA - potential buy
            print(f"Buy signal: Price ({current_price}) is below MA ({moving_avg})")
            # Uncomment to execute real trades
            # self._place_buy_order()
        elif current_price > moving_avg * 1.02:  # Price is 2% above MA - potential sell
            print(f"Sell signal: Price ({current_price}) is above MA ({moving_avg})")
            # Uncomment to execute real trades
            # self._place_sell_order()
        else:
            print("No trading signal")
    
    def _place_buy_order(self):
        """Place a buy order"""
        print(f"Placing buy order for {self.quantity} of {self.symbol}")
        order = self.client.place_order(
            str(uuid.uuid4()),
            "buy",
            "market",
            self.symbol,
            {"asset_quantity": self.quantity}
        )
        print(f"Buy order placed: {order}")
        return order
    
    def _place_sell_order(self):
        """Place a sell order"""
        print(f"Placing sell order for {self.quantity} of {self.symbol}")
        order = self.client.place_order(
            str(uuid.uuid4()),
            "sell",
            "market",
            self.symbol,
            {"asset_quantity": self.quantity}
        )
        print(f"Sell order placed: {order}")
        return order


class RSIStrategy:
    """A simple Relative Strength Index (RSI) strategy"""
    def __init__(self, client: CryptoAPITrading, symbol: str, quantity: str):
        self.client = client
        self.symbol = symbol
        self.quantity = quantity
        self.price_history = []
        self.rsi_period = 14
        self.overbought_threshold = 70
        self.oversold_threshold = 30
        
    # Implementation of RSI calculation and trading logic would go here
    # For brevity, this is just a placeholder
    
    def execute(self):
        print("RSI Strategy not fully implemented yet")


def run_strategy(strategy_name: str, symbol: str, quantity: str, interval: int = 60):
    """Run a trading strategy at specified intervals"""
    client = CryptoAPITrading()
    
    # Select strategy
    if strategy_name.lower() == "sma":
        strategy = SimpleMovingAverageStrategy(client, symbol, quantity)
    elif strategy_name.lower() == "rsi":
        strategy = RSIStrategy(client, symbol, quantity)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    print(f"Starting {strategy_name} strategy for {symbol} with quantity {quantity}")
    print(f"Checking at {interval} second intervals")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            print(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
            strategy.execute()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStrategy execution stopped by user")