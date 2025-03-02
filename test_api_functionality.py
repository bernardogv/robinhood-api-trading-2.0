import time
import uuid
import requests
from src.crypto_api_trading import CryptoAPITrading

def check_api_connectivity():
    """
    Check if we can connect to the Robinhood API server
    This helps determine if the issue is authentication, network, or endpoint related
    """
    print("\n===== CHECKING API CONNECTIVITY =====\n")
    
    base_url = "https://trading.robinhood.com"
    
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"Base API connectivity: Status code {response.status_code}")
        return response.status_code < 400
    except requests.RequestException as e:
        print(f"Failed to connect to API server: {e}")
        print("Please check your internet connection or if the API domain is correct")
        return False

def test_api_functionality():
    """
    Test all the Robinhood API functionality to ensure it's working properly
    before implementing XRP-specific trading.
    """
    # First check basic connectivity
    connectivity = check_api_connectivity()
    if not connectivity:
        print("⚠️ Warning: Could not connect to the API server. Tests may fail.")
    
    client = CryptoAPITrading()
    print("\n===== TESTING API AUTHENTICATION & ENDPOINTS =====\n")
    
    # Test 1: Get Account Information
    print("Test 1: Get Account Information")
    account_info = client.get_account()
    print(f"Account Info Response: {account_info}")
    if account_info:
        print("✅ Account info retrieval successful")
    else:
        print("❌ Failed to retrieve account info")
    
    # Test 2: Get Trading Pairs
    print("\nTest 2: Get Trading Pairs")
    pairs = client.get_trading_pairs()
    print(f"Trading pairs response structure: {pairs.keys() if isinstance(pairs, dict) else 'Not a dictionary'}")
    
    # Analyze the response structure
    if pairs:
        print("Got response from trading pairs endpoint")
        
        # Check for different possible response formats
        pairs_list = None
        if 'trading_pairs' in pairs:
            pairs_list = pairs['trading_pairs']
            print("Found 'trading_pairs' key in response")
        elif 'results' in pairs:
            pairs_list = pairs['results']
            print("Found 'results' key in response (new API format)")
        
        if pairs_list:
            print(f"First few trading pairs: {pairs_list[:3]}")
            print("✅ Trading pairs retrieval successful")
            
            # Check if XRP is available
            xrp_pairs = [pair for pair in pairs_list if 'XRP-' in pair.get('symbol', '')]
            if xrp_pairs:
                print(f"Found XRP pairs: {[pair.get('symbol') for pair in xrp_pairs]}")
            else:
                print("No XRP trading pairs found")
        else:
            print(f"❌ Response has no tradable pairs. Response keys: {pairs.keys() if isinstance(pairs, dict) else 'Not a dictionary'}")
    else:
        print("❌ Failed to retrieve trading pairs - null response")
    
    # Test 3: Get Holdings
    print("\nTest 3: Get Holdings")
    holdings = client.get_holdings()
    print(f"Holdings response structure: {holdings.keys() if isinstance(holdings, dict) else 'Not a dictionary'}")
    
    if holdings:
        # Check for different response formats
        holdings_list = None
        if 'holdings' in holdings:
            # Old format
            holdings_list = holdings['holdings']
            print("Found 'holdings' key in response")
        elif 'results' in holdings:
            # New format
            holdings_list = holdings['results']
            print("Found 'results' key in response (new API format)")
        
        if holdings_list:
            print(f"Holdings found: {len(holdings_list)} assets")
            for holding in holdings_list[:2]:  # Show first 2 for brevity
                asset_code = holding.get('asset_code')
                quantity = holding.get('total_quantity', holding.get('quantity', 'unknown'))
                print(f"  - {asset_code}: {quantity}")
            
            # Check if there are any XRP holdings
            xrp_holdings = [h for h in holdings_list if h.get('asset_code') == 'XRP']
            if xrp_holdings:
                print(f"Found XRP holdings: {xrp_holdings[0].get('total_quantity', xrp_holdings[0].get('quantity', 'unknown'))} XRP")
            else:
                print("No XRP holdings found")
                
            print("✅ Holdings retrieval successful")
        else:
            print("✅ Holdings retrieval successful (no assets found)")
    else:
        print("❌ Failed to retrieve holdings")
    
    # Test 4: Get Best Bid/Ask for Bitcoin
    print("\nTest 4: Get Best Bid/Ask (BTC-USD)")
    btc_bid_ask = client.get_best_bid_ask("BTC-USD")
    print(f"BTC-USD Bid/Ask response: {btc_bid_ask}")
    
    if btc_bid_ask:
        print(f"Response keys: {btc_bid_ask.keys() if isinstance(btc_bid_ask, dict) else 'Not a dictionary'}")
        
        # Check different possible response formats
        if 'best_bid_ask' in btc_bid_ask and btc_bid_ask['best_bid_ask']:
            print("✅ Best bid/ask retrieval successful")
            print(f"Best bid/ask data (after adaptation): {btc_bid_ask['best_bid_ask'][:1]}")
            
            # Example for using the data
            if btc_bid_ask['best_bid_ask'][0].get('bid_price') and btc_bid_ask['best_bid_ask'][0].get('ask_price'):
                bid = float(btc_bid_ask['best_bid_ask'][0]['bid_price'])
                ask = float(btc_bid_ask['best_bid_ask'][0]['ask_price'])
                print(f"BTC-USD Bid: ${bid}, Ask: ${ask}, Spread: ${ask-bid}")
        
        # Check for error messages in the response
        elif isinstance(btc_bid_ask, dict) and 'error' in btc_bid_ask:
            print(f"❌ API returned an error: {btc_bid_ask['error']}")
        elif isinstance(btc_bid_ask, dict) and 'message' in btc_bid_ask:
            print(f"❌ API returned message: {btc_bid_ask['message']}")
        else:
            print("❌ Failed to retrieve best bid/ask - unexpected response format")
    else:
        print("❌ Failed to retrieve best bid/ask - null response")
    
    # Test 5: Get Estimated Price for Bitcoin
    print("\nTest 5: Get Estimated Price (BTC-USD)")
    btc_est_price = client.get_estimated_price("BTC-USD", "both", "0.0001")
    print(f"BTC-USD Estimated Price response: {btc_est_price}")
    
    if btc_est_price:
        print(f"Response keys: {btc_est_price.keys() if isinstance(btc_est_price, dict) else 'Not a dictionary'}")
        
        # Check for success patterns in the response - multiple possible formats now
        if isinstance(btc_est_price, dict):
            if 'estimated_price' in btc_est_price:
                print("✅ Estimated price retrieval successful")
                print(f"Estimated price: ${btc_est_price['estimated_price']}")
                
                if 'bid_price' in btc_est_price and 'ask_price' in btc_est_price:
                    print(f"Bid price: ${btc_est_price['bid_price']}")
                    print(f"Ask price: ${btc_est_price['ask_price']}")
                    
            elif 'price' in btc_est_price:
                print("✅ Estimated price retrieval successful")
                print(f"Price: ${btc_est_price['price']}")
                
            elif 'prices' in btc_est_price:
                print("✅ Estimated price retrieval successful")
                print(f"First price entry: {btc_est_price['prices'][0] if btc_est_price['prices'] else 'No prices available'}")
                
            # If none of those keys exist but we have other data we can use
            elif 'results' in btc_est_price and btc_est_price['results']:
                print("✅ Estimated price retrieval successful (raw format)")
                
                # Try to extract usable price information
                if 'price' in btc_est_price['results'][0]:
                    print(f"Price from results: ${btc_est_price['results'][0]['price']}")
                elif 'bid_inclusive_of_sell_spread' in btc_est_price['results'][0] and 'ask_inclusive_of_buy_spread' in btc_est_price['results'][0]:
                    bid = float(btc_est_price['results'][0]['bid_inclusive_of_sell_spread'])
                    ask = float(btc_est_price['results'][0]['ask_inclusive_of_buy_spread'])
                    print(f"Bid price: ${bid}")
                    print(f"Ask price: ${ask}")
                    print(f"Midpoint: ${(bid + ask) / 2}")
                    
            # Check for error messages
            elif 'error' in btc_est_price:
                print(f"❌ API returned an error: {btc_est_price['error']}")
            elif 'message' in btc_est_price:
                print(f"❌ API returned message: {btc_est_price['message']}")
            else:
                print(f"❌ Failed to retrieve estimated price - unexpected response keys: {btc_est_price.keys()}")
        else:
            print("❌ Failed to retrieve estimated price - response is not a dictionary")
    else:
        print("❌ Failed to retrieve estimated price - null response")
    
    # Test 6: Get Best Bid/Ask for XRP 
    print("\nTest 6: Get Best Bid/Ask for XRP-USD (if available)")
    try:
        # Let's try with a different pair if XRP-USD specifically is not available
        potential_pairs = ["XRP-USD", "XRP/USD", "XRP-USDT", "XRP-USDC"]
        
        for pair in potential_pairs:
            print(f"Trying {pair}...")
            xrp_bid_ask = client.get_best_bid_ask(pair)
            print(f"{pair} Bid/Ask response: {xrp_bid_ask}")
            
            if xrp_bid_ask:
                if 'best_bid_ask' in xrp_bid_ask and xrp_bid_ask['best_bid_ask']:
                    print(f"✅ {pair} best bid/ask retrieval successful")
                    print(f"Response data: {xrp_bid_ask['best_bid_ask']}")
                    break
                elif isinstance(xrp_bid_ask, dict) and ('error' in xrp_bid_ask or 'message' in xrp_bid_ask):
                    error_msg = xrp_bid_ask.get('error', xrp_bid_ask.get('message', 'Unknown error'))
                    print(f"❌ API error for {pair}: {error_msg}")
                else:
                    print(f"❌ Unexpected response format for {pair}")
            else:
                print(f"❌ Null response for {pair}")
                
    except Exception as e:
        print(f"❌ Error retrieving XRP bid/ask: {e}")
    
    # Test 7: Get Orders
    print("\nTest 7: Get Orders")
    orders = client.get_orders()
    print(f"Orders: {orders}")
    if orders:
        print("✅ Orders retrieval successful")
    else:
        print("❌ Failed to retrieve orders")

    # Collect results for summary
    results = {
        "account_info": account_info,
        "trading_pairs": pairs,
        "holdings": holdings,
        "xrp_holdings": None,
        "xrp_price": None
    }
    
    # Extract XRP holdings if available
    if holdings:
        holdings_list = None
        if 'results' in holdings:
            holdings_list = holdings['results']
        elif 'holdings' in holdings:
            holdings_list = holdings['holdings']
            
        if holdings_list:
            xrp_holdings = [h for h in holdings_list if h.get('asset_code') == 'XRP']
            if xrp_holdings:
                # Try different field names for quantity
                quantity = xrp_holdings[0].get('total_quantity', 
                            xrp_holdings[0].get('quantity', 
                            xrp_holdings[0].get('quantity_available_for_trading', '0')))
                results['xrp_holdings'] = quantity
    
    # Extract the XRP price if available
    if 'best_bid_ask' in xrp_bid_ask and xrp_bid_ask['best_bid_ask']:
        best_bid_ask = xrp_bid_ask['best_bid_ask'][0]
        # Try different formats for price
        if 'price' in best_bid_ask:
            results['xrp_price'] = best_bid_ask['price']
        elif 'bid_price' in best_bid_ask and 'ask_price' in best_bid_ask:
            bid_price = float(best_bid_ask['bid_price'])
            ask_price = float(best_bid_ask['ask_price'])
            results['xrp_price'] = str((bid_price + ask_price) / 2)
    
    print("\n===== API FUNCTIONALITY TESTING COMPLETE =====\n")
    return results  # Return results for further use

if __name__ == "__main__":
    test_results = test_api_functionality()
    
    # Print a simple summary if run directly
    if test_results.get('xrp_price'):
        print(f"\nCurrent XRP price: ${float(test_results['xrp_price']):.4f}")
    if test_results.get('xrp_holdings'):
        print(f"Your XRP holdings: {test_results['xrp_holdings']}")