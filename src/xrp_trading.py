import time
import uuid
from datetime import datetime
from typing import List, Dict, Any
from src.crypto_api_trading import CryptoAPITrading

class XRPTradingStrategy:
    """
    An advanced trading strategy specifically for XRP cryptocurrency.
    Uses a combination of technical indicators including RSI, MACD, Bollinger Bands,
    and volume analysis to make more profitable trading decisions.
    """
    def __init__(self, client: CryptoAPITrading, symbol: str = "XRP-USD", quantity: str = "10"):
        self.client = client
        self.symbol = symbol
        self.quantity = quantity
        self.price_history: List[float] = []
        self.time_history: List[datetime] = []
        self.volume_history: List[float] = []  # Track trading volumes if available
        
        # RSI settings
        self.rsi_period = 14
        self.rsi_values: List[float] = []
        self.overbought_threshold = 70  # RSI value considered overbought
        self.oversold_threshold = 30    # RSI value considered oversold
        
        # MACD settings
        self.macd_fast = 12             # Fast EMA period
        self.macd_slow = 26             # Slow EMA period
        self.macd_signal = 9            # Signal line period
        self.macd_values: List[float] = []
        self.macd_signal_values: List[float] = []
        self.macd_histogram: List[float] = []
        
        # Bollinger Bands settings
        self.bb_period = 20             # Bollinger Bands period
        self.bb_std_dev = 2             # Number of standard deviations
        self.bb_upper: List[float] = []
        self.bb_middle: List[float] = []
        self.bb_lower: List[float] = []
        
        # Other technical indicators
        self.volatility_window = 20     # Window to calculate volatility
        self.ema_short = 9              # Short exponential moving average
        self.ema_medium = 21            # Medium exponential moving average
        self.ema_long = 50              # Long exponential moving average
        self.ema_short_values: List[float] = []
        self.ema_medium_values: List[float] = []
        self.ema_long_values: List[float] = []
        
        # Trading parameters
        self.min_data_points = max(self.rsi_period, self.bb_period, self.macd_slow + self.macd_signal, self.volatility_window, self.ema_long) + 1
        self.profit_target = 0.03       # 3% profit target
        self.stop_loss = 0.02           # 2% stop loss
        self.max_position_size = 20     # Maximum XRP units to trade at once
        
        # Trade tracking
        self.last_buy_price = 0
        self.last_sell_price = 0
        self.position_size = 0
        self.trade_history = []
        self.profit_loss = 0            # Track P&L
        
    def collect_price_data(self) -> float:
        """Collect the current price data for XRP"""
        # Try multiple methods to get price data in case some API endpoints are unavailable
        
        # Method 1: Try get_best_bid_ask
        result = self.client.get_best_bid_ask(self.symbol)
        
        # Our adapter should now convert all responses to a standardized format with 'best_bid_ask' key
        if result and 'best_bid_ask' in result and result['best_bid_ask'] and len(result['best_bid_ask']) > 0:
            try:
                item = result['best_bid_ask'][0]
                
                # Use the midpoint of bid and ask as the current price
                if 'bid_price' in item and 'ask_price' in item:
                    bid_price = float(item['bid_price'])
                    ask_price = float(item['ask_price'])
                    current_price = (bid_price + ask_price) / 2
                    print(f"Got price from bid_price/ask_price: {current_price}")
                    
                # If we only have a 'price' field
                elif 'price' in item:
                    current_price = float(item['price'])
                    print(f"Got price from price field: {current_price}")
                    
                # If we have different field names
                elif 'bid_inclusive_of_sell_spread' in item and 'ask_inclusive_of_buy_spread' in item:
                    bid_price = float(item['bid_inclusive_of_sell_spread'])
                    ask_price = float(item['ask_inclusive_of_buy_spread'])
                    current_price = (bid_price + ask_price) / 2
                    print(f"Got price from bid/ask_inclusive_of_spread: {current_price}")
                    
                else:
                    print(f"Could not extract price from item: {item}")
                    raise KeyError("No price fields found in response")
                
                # Add to our price history
                self.price_history.append(current_price)
                self.time_history.append(datetime.now())
                
                # Keep only the data we need for our calculations
                if len(self.price_history) > self.min_data_points:
                    self.price_history.pop(0)
                    self.time_history.pop(0)
                    
                return current_price
            except (KeyError, ValueError, TypeError, IndexError) as e:
                print(f"Error parsing best_bid_ask response: {e}")
                print(f"Response structure: {result}")
                # Continue to try other methods
        
        # Method 2: Try get_estimated_price
        print("Trying to get price from estimated_price endpoint...")
        try:
            est_result = self.client.get_estimated_price(self.symbol, "both", "1.0")
            
            if est_result:
                print(f"Estimated price response: {est_result}")
                
                # Try different possible response formats
                if 'estimated_price' in est_result:
                    current_price = float(est_result['estimated_price'])
                elif 'price' in est_result:
                    current_price = float(est_result['price'])
                elif 'data' in est_result and est_result['data']:
                    # Might be structured as data[0]['price']
                    if isinstance(est_result['data'], list) and est_result['data'][0].get('price'):
                        current_price = float(est_result['data'][0]['price'])
                    else:
                        return 0
                else:
                    return 0
                
                print(f"Got price from estimated_price: {current_price}")
                
                # Add to our price history
                self.price_history.append(current_price)
                self.time_history.append(datetime.now())
                
                # Keep only the data we need for our calculations
                if len(self.price_history) > self.min_data_points:
                    self.price_history.pop(0)
                    self.time_history.pop(0)
                    
                return current_price
        except Exception as e:
            print(f"Error getting estimated_price: {e}")
        
        # Method 3: If nothing else works, try a synthetic price generation for testing
        # This is only for simulation purposes when API is unavailable
        if self.price_history:
            # Generate a slightly modified price based on last price
            import random
            last_price = self.price_history[-1]
            fluctuation = last_price * random.uniform(-0.005, 0.005)  # Random 0.5% change
            synthetic_price = last_price + fluctuation
            
            print(f"Warning: Using synthetic price generation: {synthetic_price}")
            
            self.price_history.append(synthetic_price)
            self.time_history.append(datetime.now())
            
            if len(self.price_history) > self.min_data_points:
                self.price_history.pop(0)
                self.time_history.pop(0)
                
            return synthetic_price
        else:
            # First price - use a reasonable placeholder for XRP
            synthetic_price = 0.50  # Example XRP price in USD
            print(f"Warning: Using placeholder price for first data point: {synthetic_price}")
            self.price_history.append(synthetic_price)
            self.time_history.append(datetime.now())
            return synthetic_price
    
    def calculate_rsi(self) -> float:
        """
        Calculate the Relative Strength Index (RSI) based on price history
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss
        """
        if len(self.price_history) < self.rsi_period + 1:
            return 50  # Default to neutral RSI if we don't have enough data
        
        # Calculate price changes
        price_changes = [self.price_history[i] - self.price_history[i-1] 
                         for i in range(1, len(self.price_history))]
        
        # Use the most recent price_changes based on rsi_period
        price_changes = price_changes[-self.rsi_period:]
        
        # Separate gains and losses
        gains = [change if change > 0 else 0 for change in price_changes]
        losses = [abs(change) if change < 0 else 0 for change in price_changes]
        
        # Calculate average gain and average loss
        avg_gain = sum(gains) / self.rsi_period if gains else 0
        avg_loss = sum(losses) / self.rsi_period if losses else 0
        
        # Calculate RS and RSI
        if avg_loss == 0:
            # Avoid division by zero
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # Store RSI value
        self.rsi_values.append(rsi)
        if len(self.rsi_values) > self.rsi_period:
            self.rsi_values.pop(0)
            
        return rsi
    
    def calculate_ema(self, period: int, prices: List[float]) -> float:
        """
        Calculate the Exponential Moving Average
        EMA = Price(t) * k + EMA(y) * (1 - k)
        where k = 2/(period + 1), t = today, y = yesterday
        """
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        # Start with a simple moving average for the first value
        sma = sum(prices[:period]) / period
        
        # Calculate the multiplier
        multiplier = 2 / (period + 1)
        
        # Calculate EMA
        ema = sma
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
            
        return ema
    
    def calculate_macd(self) -> Dict[str, float]:
        """
        Calculate the Moving Average Convergence Divergence
        MACD = 12-day EMA - 26-day EMA
        Signal Line = 9-day EMA of MACD
        Histogram = MACD - Signal Line
        """
        if len(self.price_history) < self.macd_slow + self.macd_signal:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        # Calculate the fast and slow EMAs
        fast_ema = self.calculate_ema(self.macd_fast, self.price_history)
        slow_ema = self.calculate_ema(self.macd_slow, self.price_history)
        
        # Calculate MACD
        macd = fast_ema - slow_ema
        
        # Update MACD values history
        self.macd_values.append(macd)
        if len(self.macd_values) > self.macd_slow:
            self.macd_values.pop(0)
        
        # Calculate the MACD signal line (9-day EMA of MACD)
        if len(self.macd_values) < self.macd_signal:
            signal = macd
        else:
            signal = self.calculate_ema(self.macd_signal, self.macd_values)
        
        # Update Signal values history
        self.macd_signal_values.append(signal)
        if len(self.macd_signal_values) > self.macd_signal:
            self.macd_signal_values.pop(0)
        
        # Calculate the MACD histogram
        histogram = macd - signal
        
        # Update Histogram values history
        self.macd_histogram.append(histogram)
        if len(self.macd_histogram) > self.macd_signal:
            self.macd_histogram.pop(0)
        
        return {"macd": macd, "signal": signal, "histogram": histogram}
    
    def calculate_bollinger_bands(self) -> Dict[str, float]:
        """
        Calculate Bollinger Bands
        Middle Band = 20-day simple moving average (SMA)
        Upper Band = Middle Band + (20-day standard deviation * 2)
        Lower Band = Middle Band - (20-day standard deviation * 2)
        """
        if len(self.price_history) < self.bb_period:
            middle = self.price_history[-1] if self.price_history else 0
            return {"upper": middle, "middle": middle, "lower": middle}
        
        # Get the last n prices
        prices = self.price_history[-self.bb_period:]
        
        # Calculate the middle band (SMA)
        middle = sum(prices) / len(prices)
        
        # Calculate the standard deviation
        variance = sum((price - middle) ** 2 for price in prices) / len(prices)
        std_dev = variance ** 0.5
        
        # Calculate the upper and lower bands
        upper = middle + (std_dev * self.bb_std_dev)
        lower = middle - (std_dev * self.bb_std_dev)
        
        # Update Bollinger Bands history
        self.bb_middle.append(middle)
        self.bb_upper.append(upper)
        self.bb_lower.append(lower)
        
        # Maintain list length
        if len(self.bb_middle) > self.bb_period:
            self.bb_middle.pop(0)
            self.bb_upper.pop(0)
            self.bb_lower.pop(0)
        
        return {"upper": upper, "middle": middle, "lower": lower}
    
    def calculate_emas(self) -> Dict[str, float]:
        """Calculate various EMAs for trend identification"""
        short_ema = self.calculate_ema(self.ema_short, self.price_history)
        medium_ema = self.calculate_ema(self.ema_medium, self.price_history)
        long_ema = self.calculate_ema(self.ema_long, self.price_history)
        
        # Update EMA history
        self.ema_short_values.append(short_ema)
        self.ema_medium_values.append(medium_ema)
        self.ema_long_values.append(long_ema)
        
        # Maintain list length
        if len(self.ema_short_values) > self.ema_short:
            self.ema_short_values.pop(0)
        if len(self.ema_medium_values) > self.ema_medium:
            self.ema_medium_values.pop(0)
        if len(self.ema_long_values) > self.ema_long:
            self.ema_long_values.pop(0)
        
        return {"short": short_ema, "medium": medium_ema, "long": long_ema}
    
    def calculate_volatility(self) -> float:
        """
        Calculate price volatility as the standard deviation of percentage price changes
        over the volatility window.
        """
        if len(self.price_history) < self.volatility_window + 1:
            return 0  # Return 0 volatility if we don't have enough data
        
        # Calculate percentage price changes
        prices = self.price_history[-self.volatility_window:]
        pct_changes = [(prices[i] - prices[i-1]) / prices[i-1] * 100
                       for i in range(1, len(prices))]
        
        # Calculate standard deviation
        mean = sum(pct_changes) / len(pct_changes)
        variance = sum((x - mean) ** 2 for x in pct_changes) / len(pct_changes)
        volatility = variance ** 0.5  # square root of variance = standard deviation
        
        return volatility
        
    def detect_trend(self) -> str:
        """
        Detect the current market trend using EMA relationships
        Return: "uptrend", "downtrend", or "sideways"
        """
        if len(self.price_history) < self.ema_long:
            return "unknown"  # Not enough data
            
        # Calculate EMAs if not already done
        emas = self.calculate_emas()
        
        # Check EMA alignment for trend detection
        if emas["short"] > emas["medium"] > emas["long"]:
            return "uptrend"
        elif emas["short"] < emas["medium"] < emas["long"]:
            return "downtrend"
        else:
            return "sideways"

    def check_support_resistance(self, current_price: float) -> Dict[str, Any]:
        """
        Check if price is near support or resistance levels using Bollinger Bands
        """
        bb = self.calculate_bollinger_bands()
        
        # Calculate percentage distance from bands
        upper_distance = ((bb["upper"] - current_price) / current_price) * 100
        lower_distance = ((current_price - bb["lower"]) / current_price) * 100
        
        # Define thresholds for "near" support/resistance
        threshold = 1.0  # 1% from band is considered "near"
        
        result = {
            "at_support": lower_distance < threshold,
            "at_resistance": upper_distance < threshold,
            "upper_band": bb["upper"],
            "lower_band": bb["lower"],
            "middle_band": bb["middle"]
        }
        
        return result
    
    def analyze_market(self) -> Dict[str, Any]:
        """
        Analyze the market conditions and generate trading signals using multiple indicators
        Returns a dictionary with analysis results and trading signals
        """
        current_price = self.collect_price_data()
        
        if current_price == 0 or len(self.price_history) < self.min_data_points:
            return {
                "price": current_price,
                "indicators": {},
                "signal": "insufficient_data",
                "reason": "Not enough data points collected",
                "confidence": 0
            }
        
        # Calculate all technical indicators
        rsi = self.calculate_rsi()
        macd = self.calculate_macd()
        bb = self.calculate_bollinger_bands()
        emas = self.calculate_emas()
        volatility = self.calculate_volatility()
        trend = self.detect_trend()
        sr_levels = self.check_support_resistance(current_price)
        
        # Store all indicators for reporting
        indicators = {
            "rsi": rsi,
            "macd": macd,
            "bollinger_bands": bb,
            "emas": emas,
            "volatility": volatility,
            "trend": trend,
            "support_resistance": sr_levels
        }
        
        # Initialize signal components
        signal = "hold"  # Default to hold
        reasons = []
        confidence = 0.0
        
        # === BUY SIGNAL ANALYSIS ===
        buy_signals = 0
        buy_confidence = 0.0
        
        # RSI buy signals (oversold condition)
        if rsi < self.oversold_threshold:
            buy_signals += 1
            buy_confidence += 0.2
            reasons.append(f"RSI ({rsi:.2f}) indicates oversold condition")
        elif rsi < 40:  # Approaching oversold
            buy_signals += 0.5
            buy_confidence += 0.1
        
        # MACD buy signals (bullish crossover or histogram turning positive)
        if len(self.macd_histogram) > 2:
            # Histogram turning positive is bullish
            if self.macd_histogram[-2] < 0 and self.macd_histogram[-1] > 0:
                buy_signals += 1
                buy_confidence += 0.2
                reasons.append("MACD bullish crossover detected")
            # Histogram becoming less negative is bullish momentum
            elif self.macd_histogram[-2] < self.macd_histogram[-1] < 0:
                buy_signals += 0.5
                buy_confidence += 0.1
        
        # Bollinger Bands buy signals (price at or below lower band)
        if current_price <= bb["lower"] * 1.01:  # Within 1% of lower band
            buy_signals += 1
            buy_confidence += 0.15
            reasons.append("Price at lower Bollinger Band (support level)")
        
        # Trend-based buy signals
        if trend == "uptrend":
            buy_signals += 0.5
            buy_confidence += 0.1
            # Add to reasons only if it's a strong signal overall
            if buy_signals > 1.5:  
                reasons.append("Confirmed uptrend provides favorable buying conditions")
        
        # === SELL SIGNAL ANALYSIS ===
        sell_signals = 0
        sell_confidence = 0.0
        
        # RSI sell signals (overbought condition)
        if rsi > self.overbought_threshold:
            sell_signals += 1
            sell_confidence += 0.2
            reasons.append(f"RSI ({rsi:.2f}) indicates overbought condition")
        elif rsi > 60:  # Approaching overbought
            sell_signals += 0.5
            sell_confidence += 0.1
        
        # MACD sell signals (bearish crossover or histogram turning negative)
        if len(self.macd_histogram) > 2:
            # Histogram turning negative is bearish
            if self.macd_histogram[-2] > 0 and self.macd_histogram[-1] < 0:
                sell_signals += 1
                sell_confidence += 0.2
                reasons.append("MACD bearish crossover detected")
            # Histogram becoming less positive is bearish momentum
            elif self.macd_histogram[-2] > self.macd_histogram[-1] > 0:
                sell_signals += 0.5
                sell_confidence += 0.1
        
        # Bollinger Bands sell signals (price at or above upper band)
        if current_price >= bb["upper"] * 0.99:  # Within 1% of upper band
            sell_signals += 1
            sell_confidence += 0.15
            reasons.append("Price at upper Bollinger Band (resistance level)")
        
        # Trend-based sell signals
        if trend == "downtrend":
            sell_signals += 0.5
            sell_confidence += 0.1
            # Add to reasons only if it's a strong signal overall
            if sell_signals > 1.5:
                reasons.append("Confirmed downtrend suggests selling")
        
        # High volatility might be a reason to sell to reduce risk
        if volatility > 3.0:  # Very high volatility
            sell_signals += 0.5
            sell_confidence += 0.1
            reasons.append(f"Extremely high volatility ({volatility:.2f}%)")
        
        # === DETERMINE FINAL SIGNAL ===
        
        # Check for profit taking or stop loss if we're in a position
        if self.last_buy_price > 0 and self.position_size > 0:
            # Calculate current profit/loss percentage
            profit_pct = ((current_price - self.last_buy_price) / self.last_buy_price) * 100
            
            # Profit target hit
            if profit_pct >= self.profit_target * 100:
                sell_signals += 2
                sell_confidence += 0.4
                reasons.append(f"Profit target reached: {profit_pct:.2f}%")
            
            # Stop loss hit
            elif profit_pct <= -self.stop_loss * 100:
                sell_signals += 2
                sell_confidence += 0.3
                reasons.append(f"Stop loss triggered: {profit_pct:.2f}%")
        
        # Make final decision based on signal counts and confidence
        if buy_signals > sell_signals and buy_signals >= 1.5:
            signal = "buy"
            confidence = min(1.0, buy_confidence)  # Cap at 1.0 (100%)
            
            # If we already have a position, we may want to add to it or hold
            if self.position_size > 0:
                # Check if position is already large
                if self.position_size >= self.max_position_size:
                    signal = "hold"
                    reasons.append(f"Maximum position size reached ({self.position_size})")
                else:
                    # Add to position, but note this
                    reasons.insert(0, f"Adding to existing position of {self.position_size} XRP")
                    
        elif sell_signals > buy_signals and sell_signals >= 1.5:
            signal = "sell"
            confidence = min(1.0, sell_confidence)  # Cap at 1.0 (100%)
            
            # If we have no position or already sold everything, change to hold
            if self.position_size <= 0:
                signal = "hold"
                reasons = ["No position to sell"]
        else:
            signal = "hold"
            confidence = max(0.5, 1.0 - (buy_confidence + sell_confidence))
            if not reasons:
                reasons.append("No strong signals detected")
        
        # Format reason string
        reason = " | ".join(reasons) if reasons else "Market analysis inconclusive"
        
        return {
            "price": current_price,
            "indicators": indicators,
            "signal": signal,
            "reason": reason,
            "confidence": confidence,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals
        }
    
    def place_buy_order(self) -> Dict:
        """Place a buy order for XRP"""
        print(f"Placing buy order for {self.quantity} of {self.symbol}")
        
        # First check account balance to ensure we have enough funds
        account = self.client.get_account()
        
        # Determine available buying power
        buying_power = 0
        if account and 'buying_power' in account:
            buying_power = float(account['buying_power'])
            print(f"Available buying power: ${buying_power}")
        elif account and account.get('results'):
            # Try alternate format
            buying_power = float(account['results'][0].get('buying_power', 0))
            print(f"Available buying power: ${buying_power}")
        
        # Check if we have enough funds
        current_price = self.collect_price_data()
        order_cost = float(self.quantity) * current_price
        
        if order_cost > buying_power:
            print(f"Warning: Insufficient funds for order (Need ${order_cost:.2f}, have ${buying_power:.2f})")
            # Adjust quantity if needed
            adjusted_quantity = str(int(float(self.quantity) * (buying_power / order_cost) * 0.95))  # 5% buffer
            if float(adjusted_quantity) < 1:
                print("Cannot place order: Insufficient funds even for minimum quantity")
                return {"status": "failed", "reason": "insufficient_funds"}
            
            print(f"Adjusting quantity from {self.quantity} to {adjusted_quantity}")
            self.quantity = adjusted_quantity
        
        try:
            order = self.client.place_order(
                str(uuid.uuid4()),
                "buy",
                "market",
                self.symbol,
                {"asset_quantity": self.quantity}
            )
            
            # Update position tracking
            order_quantity = float(self.quantity)
            self.position_size += order_quantity
            self.last_buy_price = current_price
            
            # Record the trade in history
            trade_record = {
                "time": datetime.now(),
                "type": "buy",
                "price": current_price,
                "quantity": order_quantity,
                "total": current_price * order_quantity
            }
            self.trade_history.append(trade_record)
            
            print(f"Buy order placed: {order}")
            return order
            
        except Exception as e:
            print(f"Error placing buy order: {e}")
            return {"status": "failed", "reason": str(e)}
    
    def place_sell_order(self) -> Dict:
        """Place a sell order for XRP"""
        print(f"Placing sell order for {self.quantity} of {self.symbol}")
        
        # First check holdings to ensure we have enough XRP
        holdings = self.client.get_holdings("XRP")
        
        # Determine available holdings
        available_xrp = 0
        if holdings and 'holdings' in holdings and holdings['holdings']:
            available_xrp = float(holdings['holdings'][0].get('quantity', 0))
            print(f"Available XRP: {available_xrp}")
        elif holdings and 'results' in holdings:
            # Try alternate format - look for XRP in results
            xrp_holdings = [h for h in holdings['results'] if h.get('asset_code') == 'XRP']
            if xrp_holdings:
                # Try different field names
                available_xrp = float(xrp_holdings[0].get('total_quantity', 
                               xrp_holdings[0].get('quantity', 
                               xrp_holdings[0].get('quantity_available_for_trading', 0))))
                print(f"Available XRP: {available_xrp}")
        
        # Check if we have enough XRP
        if float(self.quantity) > available_xrp:
            print(f"Warning: Insufficient XRP for order (Need {self.quantity}, have {available_xrp})")
            # Adjust quantity if needed
            if available_xrp <= 0:
                print("Cannot place order: No XRP holdings")
                return {"status": "failed", "reason": "no_holdings"}
            
            adjusted_quantity = str(int(available_xrp * 0.99))  # 1% buffer for safety
            print(f"Adjusting quantity from {self.quantity} to {adjusted_quantity}")
            self.quantity = adjusted_quantity
        
        try:
            order = self.client.place_order(
                str(uuid.uuid4()),
                "sell",
                "market",
                self.symbol,
                {"asset_quantity": self.quantity}
            )
            
            # Update position tracking
            current_price = self.collect_price_data()
            order_quantity = float(self.quantity)
            
            # Calculate profit/loss if we have a last buy price
            if self.last_buy_price > 0:
                profit = (current_price - self.last_buy_price) * order_quantity
                profit_pct = ((current_price - self.last_buy_price) / self.last_buy_price) * 100
                self.profit_loss += profit
                print(f"Trade P&L: ${profit:.2f} ({profit_pct:.2f}%)")
                print(f"Total P&L: ${self.profit_loss:.2f}")
            
            # Update position size
            self.position_size = max(0, self.position_size - order_quantity)
            self.last_sell_price = current_price
            
            # Record the trade in history
            trade_record = {
                "time": datetime.now(),
                "type": "sell",
                "price": current_price,
                "quantity": order_quantity,
                "total": current_price * order_quantity,
                "profit": profit if self.last_buy_price > 0 else None,
                "profit_pct": profit_pct if self.last_buy_price > 0 else None
            }
            self.trade_history.append(trade_record)
            
            print(f"Sell order placed: {order}")
            return order
            
        except Exception as e:
            print(f"Error placing sell order: {e}")
            return {"status": "failed", "reason": str(e)}
    
    def execute(self, simulate: bool = True) -> None:
        """
        Execute the XRP trading strategy based on advanced market analysis
        
        Args:
            simulate: If True, only simulate orders without actually placing them
        """
        print(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        
        try:
            # Attempt to perform market analysis with all indicators
            analysis = self.analyze_market()
            
            # Display current price
            if analysis['price'] > 0:
                print(f"Current XRP price: ${analysis['price']:.4f}")
            else:
                print("Warning: Unable to get reliable price data")
                return  # Skip this execution cycle if we don't have price data
            
            # Display summary of position and P&L if we have a position
            if self.position_size > 0:
                unrealized_pl = (analysis['price'] - self.last_buy_price) * self.position_size
                unrealized_pl_pct = ((analysis['price'] - self.last_buy_price) / self.last_buy_price) * 100
                print(f"Current position: {self.position_size} XRP @ ${self.last_buy_price:.4f}")
                print(f"Unrealized P&L: ${unrealized_pl:.2f} ({unrealized_pl_pct:.2f}%)")
            
            # Display analysis and generate signals if we have enough data
            if 'indicators' in analysis and analysis['indicators']:
                indicators = analysis['indicators']
                
                # Display key indicators
                if 'rsi' in indicators:
                    print(f"RSI: {indicators['rsi']:.2f}")
                
                if 'macd' in indicators:
                    print(f"MACD: {indicators['macd']['macd']:.4f}, Signal: {indicators['macd']['signal']:.4f}, Histogram: {indicators['macd']['histogram']:.4f}")
                
                if 'bollinger_bands' in indicators:
                    bb = indicators['bollinger_bands']
                    print(f"Bollinger Bands: Upper: ${bb['upper']:.4f}, Middle: ${bb['middle']:.4f}, Lower: ${bb['lower']:.4f}")
                
                if 'trend' in indicators:
                    print(f"Trend: {indicators['trend']}")
                
                if 'volatility' in indicators:
                    print(f"Volatility: {indicators['volatility']:.2f}%")
                
                # Display trading signal with confidence
                print(f"Signal: {analysis['signal']} (Confidence: {analysis['confidence']:.2f})")
                print(f"Buy signals: {analysis.get('buy_signals', 0)}, Sell signals: {analysis.get('sell_signals', 0)}")
                print(f"Reason: {analysis['reason']}")
                
                # Execute orders based on the signal and confidence
                if analysis['signal'] == 'buy' and analysis['confidence'] >= 0.6:  # Require higher confidence for buys
                    if simulate:
                        print("[SIMULATION] Would place buy order now")
                    else:
                        try:
                            order_result = self.place_buy_order()
                            if order_result.get('status') == 'failed':
                                print(f"Buy order failed: {order_result.get('reason')}")
                        except Exception as e:
                            print(f"Error placing buy order: {e}")
                
                elif analysis['signal'] == 'sell' and analysis['confidence'] >= 0.5:  # Lower threshold for sells (risk management)
                    if simulate:
                        print("[SIMULATION] Would place sell order now")
                    else:
                        try:
                            order_result = self.place_sell_order()
                            if order_result.get('status') == 'failed':
                                print(f"Sell order failed: {order_result.get('reason')}")
                        except Exception as e:
                            print(f"Error placing sell order: {e}")
                
                else:
                    print("Holding position - signal not strong enough")
                    
                # Additional features for simulation mode
                if simulate and self.position_size > 0:
                    # Update simulated P&L for tracking performance
                    current_price = analysis['price']
                    if self.last_buy_price > 0:
                        unrealized_pl = (current_price - self.last_buy_price) * self.position_size
                        unrealized_pl_pct = ((current_price - self.last_buy_price) / self.last_buy_price) * 100
                        
                        # Check for simulated stop loss or profit taking
                        if unrealized_pl_pct <= -self.stop_loss * 100:
                            print(f"[SIMULATION] Stop loss triggered at ${current_price:.4f} (-{abs(unrealized_pl_pct):.2f}%)")
                            print(f"[SIMULATION] Would sell {self.position_size} XRP for ${unrealized_pl:.2f} loss")
                            self.profit_loss += unrealized_pl
                            self.position_size = 0
                        elif unrealized_pl_pct >= self.profit_target * 100:
                            print(f"[SIMULATION] Profit target reached at ${current_price:.4f} (+{unrealized_pl_pct:.2f}%)")
                            print(f"[SIMULATION] Would sell {self.position_size} XRP for ${unrealized_pl:.2f} profit")
                            self.profit_loss += unrealized_pl
                            self.position_size = 0
            else:
                print("Collecting initial data, no signals generated yet")
                
        except Exception as e:
            print(f"Error during strategy execution: {e}")
            import traceback
            traceback.print_exc()
            print("Continuing to next cycle...")


def run_xrp_strategy(quantity: str = "10", interval: int = 60, duration: int = 3600, simulate: bool = True):
    """
    Run the XRP trading strategy for a specified duration
    
    Args:
        quantity: Amount of XRP to trade
        interval: Seconds between each strategy execution
        duration: Total running time in seconds (default: 1 hour)
        simulate: If True, only simulate orders without actually placing them
    """
    client = CryptoAPITrading()
    
    # First, check API connectivity
    print("\nVerifying API connectivity and available trading pairs...")
    
    # Check if we can get account information (basic authentication test)
    account_info = client.get_account()
    if not account_info:
        print("⚠️ Failed to get account information. API authentication may be incorrect.")
        print("Please check that your API_KEY and BASE64_PRIVATE_KEY are set correctly in the .env file.")
        return
    
    # Check if XRP-USD is available
    pairs = client.get_trading_pairs()
    
    if not pairs:
        print("⚠️ Failed to retrieve trading pairs.")
        print("Continuing with XRP strategy, but watch for errors...")
        xrp_verified = False
    else:
        # Check for different response formats
        pairs_list = None
        
        if 'trading_pairs' in pairs:
            pairs_list = pairs['trading_pairs']
        elif 'results' in pairs:
            pairs_list = pairs['results']
        
        if not pairs_list:
            print(f"⚠️ Unexpected response format from trading pairs endpoint: {pairs.keys() if isinstance(pairs, dict) else 'Not a dictionary'}")
            print("Continuing with XRP strategy, but watch for errors...")
            xrp_verified = False
        else:
            # Find XRP in the pairs list - check both formats for symbol field
            xrp_pairs = [pair for pair in pairs_list if pair.get('symbol') == 'XRP-USD']
            
            if not xrp_pairs:
                print("⚠️ Warning: XRP-USD trading pair not found in the available pairs.")
                print("Available pairs may include:", [p.get('symbol') for p in pairs_list[:5]], "...")
                print("Continuing anyway, but API calls may fail...")
                xrp_verified = False
            else:
                print(f"✅ XRP-USD trading pair is available: {xrp_pairs[0]}")
                xrp_verified = True
    
    # Create the strategy instance
    strategy = XRPTradingStrategy(client, "XRP-USD", quantity)
    
    # Get initial XRP price for performance comparison
    initial_price = 0
    try:
        price_response = client.get_best_bid_ask("XRP-USD")
        if price_response and 'best_bid_ask' in price_response and price_response['best_bid_ask']:
            best_bid_ask = price_response['best_bid_ask'][0]
            if 'bid_price' in best_bid_ask and 'ask_price' in best_bid_ask:
                bid = float(best_bid_ask['bid_price'])
                ask = float(best_bid_ask['ask_price'])
                initial_price = (bid + ask) / 2
                print(f"Initial XRP price: ${initial_price:.4f}")
    except Exception as e:
        print(f"Error getting initial price: {e}")
    
    print(f"\nStarting XRP trading strategy with quantity {quantity}")
    print(f"Checking at {interval} second intervals")
    print(f"Strategy will run for {duration // 60} minutes")
    if simulate:
        print("SIMULATION MODE: No actual orders will be placed")
    else:
        print("⚠️ LIVE TRADING MODE: Real orders will be placed!")
        
        # Extra confirmation for live trading
        if not xrp_verified:
            print("\n⚠️ WARNING: Running in live mode with unverified XRP trading pair!")
            confirmation = input("Are you sure you want to continue with live trading? (yes/no): ")
            if confirmation.lower() != 'yes':
                print("Exiting at user request.")
                return
    
    print("Press Ctrl+C to stop")
    
    # Record start time for calculating performance
    start_time = time.time()
    execution_count = 0
    
    try:
        while time.time() - start_time < duration:
            strategy.execute(simulate)
            execution_count += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStrategy execution stopped by user")
    
    # Calculate final performance
    runtime = time.time() - start_time
    runtime_minutes = runtime / 60
    
    # Get final XRP price
    final_price = 0
    try:
        price_response = client.get_best_bid_ask("XRP-USD")
        if price_response and 'best_bid_ask' in price_response and price_response['best_bid_ask']:
            best_bid_ask = price_response['best_bid_ask'][0]
            if 'bid_price' in best_bid_ask and 'ask_price' in best_bid_ask:
                bid = float(best_bid_ask['bid_price'])
                ask = float(best_bid_ask['ask_price'])
                final_price = (bid + ask) / 2
    except Exception as e:
        print(f"Error getting final price: {e}")
    
    # Print performance summary
    print("\n" + "="*50)
    print("XRP TRADING STRATEGY PERFORMANCE SUMMARY")
    print("="*50)
    print(f"Runtime: {runtime_minutes:.2f} minutes ({execution_count} strategy executions)")
    
    if initial_price > 0 and final_price > 0:
        market_change_pct = ((final_price - initial_price) / initial_price) * 100
        print(f"Initial XRP price: ${initial_price:.4f}")
        print(f"Final XRP price: ${final_price:.4f}")
        print(f"Market change: {market_change_pct:.2f}%")
    
    if strategy.profit_loss != 0:
        print(f"Strategy P&L: ${strategy.profit_loss:.2f}")
        
        # Calculate annualized return
        if runtime_minutes > 0:
            annual_minutes = 365 * 24 * 60  # minutes in a year
            annualized_return = (strategy.profit_loss / float(quantity)) * (annual_minutes / runtime_minutes)
            print(f"Annualized return: {annualized_return:.2f}%")
    
    # Print trade history summary
    if strategy.trade_history:
        print("\nTrade History:")
        print(f"Total trades: {len(strategy.trade_history)}")
        
        buy_trades = [t for t in strategy.trade_history if t['type'] == 'buy']
        sell_trades = [t for t in strategy.trade_history if t['type'] == 'sell']
        
        print(f"Buy trades: {len(buy_trades)}")
        print(f"Sell trades: {len(sell_trades)}")
        
        # Calculate win rate if we have profits/losses
        profitable_trades = [t for t in strategy.trade_history if t.get('profit', 0) and t.get('profit') > 0]
        losing_trades = [t for t in strategy.trade_history if t.get('profit', 0) and t.get('profit') < 0]
        
        if profitable_trades or losing_trades:
            win_rate = len(profitable_trades) / (len(profitable_trades) + len(losing_trades)) * 100 if (len(profitable_trades) + len(losing_trades)) > 0 else 0
            print(f"Win rate: {win_rate:.2f}%")
            
            if profitable_trades:
                avg_profit = sum(t['profit'] for t in profitable_trades) / len(profitable_trades)
                print(f"Average profit per winning trade: ${avg_profit:.2f}")
            
            if losing_trades:
                avg_loss = sum(t['profit'] for t in losing_trades) / len(losing_trades)
                print(f"Average loss per losing trade: ${avg_loss:.2f}")
    
    # If we have current position, show unrealized P&L
    if strategy.position_size > 0 and final_price > 0 and strategy.last_buy_price > 0:
        unrealized_pl = (final_price - strategy.last_buy_price) * strategy.position_size
        unrealized_pl_pct = ((final_price - strategy.last_buy_price) / strategy.last_buy_price) * 100
        print(f"\nCurrent position: {strategy.position_size} XRP @ ${strategy.last_buy_price:.4f}")
        print(f"Unrealized P&L: ${unrealized_pl:.2f} ({unrealized_pl_pct:.2f}%)")
    
    print("="*50)
    print("\nXRP trading strategy completed")


if __name__ == "__main__":
    # Run the strategy in simulation mode by default
    run_xrp_strategy(quantity="10", interval=30, duration=3600, simulate=True)