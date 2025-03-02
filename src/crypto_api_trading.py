import base64
import datetime
import json
from typing import Any, Dict, Optional
import uuid
import requests
from nacl.signing import SigningKey
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE64_PRIVATE_KEY = os.getenv("BASE64_PRIVATE_KEY")



class CryptoAPITrading:
    def __init__(self):
        self.api_key = API_KEY
        private_key_seed = base64.b64decode(BASE64_PRIVATE_KEY)
        self.private_key = SigningKey(private_key_seed)
        self.base_url = "https://trading.robinhood.com"

    @staticmethod
    def _get_current_timestamp() -> int:
        return int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())

    @staticmethod
    def get_query_params(key: str, *args: Optional[str]) -> str:
        if not args:
            return ""

        params = []
        for arg in args:
            params.append(f"{key}={arg}")

        return "?" + "&".join(params)

    def make_api_request(self, method: str, path: str, body: str = "") -> Any:
        timestamp = self._get_current_timestamp()
        headers = self.get_authorization_header(method, path, body, timestamp)
        url = self.base_url + path

        print(f"Making {method} request to {url}")
        
        try:
            response = {}
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=json.loads(body) if body else {}, timeout=10)
            
            # Print response details for debugging
            print(f"Response status code: {response.status_code}")
            if response.status_code != 200:
                print(f"Error response text: {response.text}")
            
            # Check if we can parse the response as JSON
            try:
                return response.json()
            except json.JSONDecodeError as json_err:
                print(f"Failed to decode JSON: {json_err}")
                print(f"Response text: {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"Error making API request: {e}")
            return None

    def get_authorization_header(
            self, method: str, path: str, body: str, timestamp: int
    ) -> Dict[str, str]:
        message_to_sign = f"{self.api_key}{timestamp}{path}{method}{body}"
        signed = self.private_key.sign(message_to_sign.encode("utf-8"))

        return {
            "x-api-key": self.api_key,
            "x-signature": base64.b64encode(signed.signature).decode("utf-8"),
            "x-timestamp": str(timestamp),
        }

    def get_account(self) -> Any:
        path = "/api/v1/crypto/trading/accounts/"
        return self.make_api_request("GET", path)

    # The symbols argument must be formatted in trading pairs, e.g "BTC-USD", "ETH-USD". If no symbols are provided,
    # all supported symbols will be returned
    def get_trading_pairs(self, *symbols: Optional[str]) -> Any:
        query_params = self.get_query_params("symbol", *symbols)
        path = f"/api/v1/crypto/trading/trading_pairs/{query_params}"
        return self.make_api_request("GET", path)

    # The asset_codes argument must be formatted as the short form name for a crypto, e.g "BTC", "ETH". If no asset
    # codes are provided, all crypto holdings will be returned
    def get_holdings(self, *asset_codes: Optional[str]) -> Any:
        query_params = self.get_query_params("asset_code", *asset_codes)
        path = f"/api/v1/crypto/trading/holdings/{query_params}"
        return self.make_api_request("GET", path)

    # The symbols argument must be formatted in trading pairs, e.g "BTC-USD", "ETH-USD". If no symbols are provided,
    # the best bid and ask for all supported symbols will be returned
    def get_best_bid_ask(self, *symbols: Optional[str]) -> Any:
        query_params = self.get_query_params("symbol", *symbols)
        
        # Try with the original path
        path = f"/api/v1/crypto/marketdata/best_bid_ask/{query_params}"
        print(f"Attempting to get best bid/ask with path: {path}")
        result = self.make_api_request("GET", path)
        
        # Check if the result has the format we're seeing now: {'results': [{...}]}
        if result and isinstance(result, dict) and 'results' in result and result['results']:
            print("Found 'results' key in response, adapting to expected format...")
            
            # Convert to the expected format that our code uses
            best_bid_ask_items = []
            
            for item in result['results']:
                # Create a mapping from the new format to our expected format
                adapted_item = {}
                
                if 'symbol' in item:
                    adapted_item['symbol'] = item['symbol']
                
                # Map the new price fields to our expected format
                if 'bid_inclusive_of_sell_spread' in item:
                    adapted_item['bid_price'] = item['bid_inclusive_of_sell_spread']
                elif 'bid_price' in item:
                    adapted_item['bid_price'] = item['bid_price']
                
                if 'ask_inclusive_of_buy_spread' in item:
                    adapted_item['ask_price'] = item['ask_inclusive_of_buy_spread']
                elif 'ask_price' in item:
                    adapted_item['ask_price'] = item['ask_price']
                
                # If we only have a single price, use it for both bid and ask
                if 'price' in item and (not 'bid_price' in adapted_item or not 'ask_price' in adapted_item):
                    if not 'bid_price' in adapted_item:
                        adapted_item['bid_price'] = item['price']
                    if not 'ask_price' in adapted_item:
                        adapted_item['ask_price'] = item['price']
                
                # Add timestamp if available
                if 'timestamp' in item:
                    adapted_item['timestamp'] = item['timestamp']
                
                best_bid_ask_items.append(adapted_item)
            
            return {'best_bid_ask': best_bid_ask_items}
        
        # If that format isn't found, try some alternative endpoints
        if not result or (isinstance(result, dict) and 'best_bid_ask' not in result):
            print("First attempt failed, trying alternative endpoint...")
            
            # Try alternative endpoints
            alt_paths = [
                f"/api/v1/crypto/quotes/{query_params}",
                f"/api/v1/crypto/marketdata/quotes/{query_params}"
            ]
            
            for alt_path in alt_paths:
                print(f"Trying alternative path: {alt_path}")
                alt_result = self.make_api_request("GET", alt_path)
                
                # If we get a valid-looking response, process it
                if alt_result and isinstance(alt_result, dict) and not alt_result.get('error'):
                    print(f"Alternative path {alt_path} returned: {alt_result.keys() if isinstance(alt_result, dict) else 'Not a dictionary'}")
                    
                    # Check for different response formats
                    if 'quotes' in alt_result:
                        return {'best_bid_ask': alt_result['quotes']}
                    elif 'data' in alt_result:
                        return {'best_bid_ask': alt_result['data']}
                    elif 'results' in alt_result and alt_result['results']:
                        # Process as above
                        best_bid_ask_items = []
                        for item in alt_result['results']:
                            adapted_item = {}
                            if 'symbol' in item:
                                adapted_item['symbol'] = item['symbol']
                            if 'bid_inclusive_of_sell_spread' in item:
                                adapted_item['bid_price'] = item['bid_inclusive_of_sell_spread']
                            elif 'bid_price' in item:
                                adapted_item['bid_price'] = item['bid_price']
                            if 'ask_inclusive_of_buy_spread' in item:
                                adapted_item['ask_price'] = item['ask_inclusive_of_buy_spread']
                            elif 'ask_price' in item:
                                adapted_item['ask_price'] = item['ask_price']
                            if 'price' in item and (not 'bid_price' in adapted_item or not 'ask_price' in adapted_item):
                                if not 'bid_price' in adapted_item:
                                    adapted_item['bid_price'] = item['price']
                                if not 'ask_price' in adapted_item:
                                    adapted_item['ask_price'] = item['price']
                            if 'timestamp' in item:
                                adapted_item['timestamp'] = item['timestamp']
                            best_bid_ask_items.append(adapted_item)
                        return {'best_bid_ask': best_bid_ask_items}
                    
                    # If we can't adapt the format, just return it
                    return alt_result
        
        return result

    # The symbol argument must be formatted in a trading pair, e.g "BTC-USD", "ETH-USD"
    # The side argument must be "bid", "ask", or "both".
    # Multiple quantities can be specified in the quantity argument, e.g. "0.1,1,1.999".
    def get_estimated_price(self, symbol: str, side: str, quantity: str) -> Any:
        # Original path
        path = f"/api/v1/crypto/marketdata/estimated_price/?symbol={symbol}&side={side}&quantity={quantity}"
        print(f"Attempting to get estimated price with path: {path}")
        result = self.make_api_request("GET", path)
        
        # Check if the response has the new format with 'results' key
        if result and isinstance(result, dict) and 'results' in result and result['results']:
            print("Found 'results' key in estimated price response, adapting format...")
            
            # Create a standardized format response
            estimated_prices = []
            
            for item in result['results']:
                price_item = {}
                
                # Include all original fields for reference
                price_item.update(item)
                
                # Make sure we have a standardized 'price' field
                if 'price' not in price_item and 'bid_inclusive_of_sell_spread' in item and 'ask_inclusive_of_buy_spread' in item:
                    # For 'both' side, calculate the midpoint
                    bid = float(item['bid_inclusive_of_sell_spread'])
                    ask = float(item['ask_inclusive_of_buy_spread'])
                    price_item['price'] = str((bid + ask) / 2)
                
                estimated_prices.append(price_item)
            
            return {
                'estimated_price': estimated_prices[0]['price'] if side != 'both' else None,
                'bid_price': next((item['price'] for item in estimated_prices if item.get('side') == 'bid'), None),
                'ask_price': next((item['price'] for item in estimated_prices if item.get('side') == 'ask'), None),
                'prices': estimated_prices  # Keep the full details for reference
            }
            
        # If we didn't find the expected format, try some alternative endpoints
        if not result or (isinstance(result, dict) and ('estimated_price' not in result and 'price' not in result and 'results' not in result)):
            print("First attempt failed, trying alternative endpoint...")
            
            # Try alternative endpoints
            alt_paths = [
                f"/api/v1/crypto/price_estimates/?symbol={symbol}&side={side}&quantity={quantity}",
                f"/api/v1/crypto/marketdata/price_estimates/?symbol={symbol}&side={side}&quantity={quantity}"
            ]
            
            for alt_path in alt_paths:
                print(f"Trying alternative path: {alt_path}")
                alt_result = self.make_api_request("GET", alt_path)
                
                # If we get a valid-looking response, return it
                if alt_result and isinstance(alt_result, dict) and not alt_result.get('error'):
                    print(f"Alternative path {alt_path} returned: {alt_result.keys() if isinstance(alt_result, dict) else 'Not a dictionary'}")
                    return alt_result
        
        return result

    def place_order(
            self,
            client_order_id: str,
            side: str,
            order_type: str,
            symbol: str,
            order_config: Dict[str, str],
    ) -> Any:
        body = {
            "client_order_id": client_order_id,
            "side": side,
            "type": order_type,
            "symbol": symbol,
            f"{order_type}_order_config": order_config,
        }
        path = "/api/v1/crypto/trading/orders/"
        return self.make_api_request("POST", path, json.dumps(body))

    def cancel_order(self, order_id: str) -> Any:
        path = f"/api/v1/crypto/trading/orders/{order_id}/cancel/"
        return self.make_api_request("POST", path)

    def get_order(self, order_id: str) -> Any:
        path = f"/api/v1/crypto/trading/orders/{order_id}/"
        return self.make_api_request("GET", path)

    def get_orders(self) -> Any:
        path = "/api/v1/crypto/trading/orders/"
        return self.make_api_request("GET", path)


def main():
    api_trading_client = CryptoAPITrading()
    print(api_trading_client.get_account())

    """
    BUILD YOUR TRADING STRATEGY HERE

    order = api_trading_client.place_order(
          str(uuid.uuid4()),
          "buy",
          "market",
          "BTC-USD",
          {"asset_quantity": "0.0001"}
    )
    """


if __name__ == "__main__":
    main()