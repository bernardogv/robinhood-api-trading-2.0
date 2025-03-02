# Robinhood API Trading Project Guide

## Commands
- Run main script: `python -m src.main xrp [--live] [--interval 30] [--duration 3600]`
- Run API test: `python -m src.main test-api`
- View account: `python -m src.main account`
- List pairs: `python -m src.main list-pairs`
- Check holdings: `python -m src.main holdings`
- Run tests: `python -m unittest discover tests`

## Code Style Guidelines
- **Imports**: Use absolute imports with `src.` prefix (e.g., `from src.crypto_api_trading import CryptoAPITrading`)
- **Types**: Use type hints for all parameters and return values
- **Error Handling**: Use try/except blocks with specific exceptions and detailed error messages
- **Naming**: 
  - Classes: CamelCase
  - Functions/methods: snake_case
  - Constants: UPPER_CASE
- **Doc Strings**: Include docstrings for all classes and methods (multi-line)
- **Formatting**: Space after commas, spaces around operators, indentation with 4 spaces
- **Structure**: Keep classes focused on single responsibility
- **API Responses**: Handle API format changes gracefully with fallback options