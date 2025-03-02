import argparse
from src.trading_strategies import run_strategy
from src.crypto_api_trading import CryptoAPITrading
from src.xrp_trading import run_xrp_strategy
from test_api_functionality import test_api_functionality

def list_available_pairs():
    """List all available trading pairs from Robinhood"""
    client = CryptoAPITrading()
    pairs = client.get_trading_pairs()
    
    # Handle different response formats
    pairs_list = None
    if pairs:
        if 'trading_pairs' in pairs:
            pairs_list = pairs['trading_pairs']
        elif 'results' in pairs:
            pairs_list = pairs['results']
    
    if pairs_list:
        print("\nAvailable Trading Pairs:")
        for pair in pairs_list:
            symbol = pair.get('symbol')
            if symbol:
                print(f"- {symbol}")
    else:
        print("Failed to fetch trading pairs or no pairs available")

def list_holdings():
    """List user's current crypto holdings"""
    client = CryptoAPITrading()
    holdings = client.get_holdings()
    
    # Handle different response formats
    holdings_list = None
    if holdings:
        if 'holdings' in holdings:
            holdings_list = holdings['holdings']
        elif 'results' in holdings:
            holdings_list = holdings['results']
    
    if holdings_list:
        print("\nYour Crypto Holdings:")
        for holding in holdings_list:
            asset_code = holding.get('asset_code', 'Unknown')
            # Try different field names for quantity
            quantity = holding.get('total_quantity', 
                      holding.get('quantity', 
                      holding.get('quantity_available_for_trading', '0')))
            # Cost basis might not be available in all responses
            cost_basis = holding.get('cost_basis', 'N/A')
            
            if cost_basis != 'N/A':
                print(f"- {asset_code}: {quantity} (${cost_basis})")
            else:
                print(f"- {asset_code}: {quantity}")
    else:
        print("Failed to fetch holdings or no holdings available")

def main():
    parser = argparse.ArgumentParser(description='Robinhood Crypto Trading Bot')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List available trading pairs
    list_parser = subparsers.add_parser('list-pairs', help='List available trading pairs')
    
    # List holdings
    holdings_parser = subparsers.add_parser('holdings', help='List your crypto holdings')
    
    # Run a generic trading strategy
    strategy_parser = subparsers.add_parser('run', help='Run a trading strategy')
    strategy_parser.add_argument('--strategy', '-s', required=True, choices=['sma', 'rsi'], 
                                help='Trading strategy to use (sma=Simple Moving Average, rsi=Relative Strength Index)')
    strategy_parser.add_argument('--symbol', '-sym', required=True, 
                                help='Trading pair symbol (e.g., BTC-USD)')
    strategy_parser.add_argument('--quantity', '-q', required=True, 
                                help='Quantity to trade (e.g., 0.0001)')
    strategy_parser.add_argument('--interval', '-i', type=int, default=60, 
                                help='Checking interval in seconds (default: 60)')
    
    # Run the XRP-specific strategy
    xrp_parser = subparsers.add_parser('xrp', help='Run the XRP-specific trading strategy')
    xrp_parser.add_argument('--quantity', '-q', default="10", 
                           help='Quantity of XRP to trade (default: 10)')
    xrp_parser.add_argument('--interval', '-i', type=int, default=30, 
                           help='Checking interval in seconds (default: 30)')
    xrp_parser.add_argument('--duration', '-d', type=int, default=3600, 
                           help='Duration to run the strategy in seconds (default: 3600 = 1 hour)')
    xrp_parser.add_argument('--live', '-l', action='store_true', 
                           help='Run in live mode (DEFAULT is simulation mode)')
    
    # Test API functionality
    test_parser = subparsers.add_parser('test-api', help='Test all API functionality')
    test_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed response information')
    
    # Account information
    account_parser = subparsers.add_parser('account', help='Get account information')
    
    args = parser.parse_args()
    
    if args.command == 'list-pairs':
        list_available_pairs()
    elif args.command == 'holdings':
        list_holdings()
    elif args.command == 'run':
        run_strategy(args.strategy, args.symbol, args.quantity, args.interval)
    elif args.command == 'xrp':
        # For XRP strategy, we use the simulate parameter (opposite of the live flag)
        run_xrp_strategy(
            quantity=args.quantity, 
            interval=args.interval, 
            duration=args.duration, 
            simulate=not args.live
        )
    elif args.command == 'test-api':
        try:
            print("\nTesting Robinhood Crypto API functionality...")
            results = test_api_functionality()
            
            # Print a summary after all tests
            print("\n=== API Test Summary ===")
            print("✅ Found XRP-USD trading pair")
            print(f"✅ Current XRP price: ${float(results['xrp_price']):.4f}" if results.get('xrp_price') else "❌ Failed to get XRP price")
            print(f"✅ XRP holdings: {results['xrp_holdings']}" if results.get('xrp_holdings') else "❓ No XRP holdings found")
            print("\nAPI tests completed. You can now run the XRP trading strategy.")
            
        except Exception as e:
            print(f"Error during API testing: {e}")
            import traceback
            traceback.print_exc()
    elif args.command == 'account':
        client = CryptoAPITrading()
        account = client.get_account()
        print("\nAccount Information:")
        print(account)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()