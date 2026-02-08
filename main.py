"""
Ichimoku Technical Analysis Scanner for NSE Stocks

Scans stocks for Tenkan-Kijun gap setups indicating potential momentum opportunities.
Identifies stocks where:
1. Tenkan-Kijun gap exceeds minimum threshold (indicates trend strength)
2. Price is near Tenkan line (potential entry point)
"""

import logging
from datetime import datetime
from typing import List, Tuple, Optional
import argparse

import pandas as pd
import yfinance as yf
import requests

# =====================
# CONFIGURATION
# =====================
TIMEFRAME: str = "1h"              # Options: 30m / 1h / 1d
PERIOD: str = "3mo"                # Historical data period
MIN_GAP_PCT: float = 3.0           # Minimum Tenkan-Kijun gap percentage
PRICE_NEAR_TENKAN_PCT: float = 0.4 # Maximum distance from Tenkan (%)
TENKAN_PERIOD: int = 9             # Tenkan-sen (Conversion Line) period
KIJUN_PERIOD: int = 26             # Kijun-sen (Base Line) period
MIN_DATA_POINTS: int = 30          # Minimum bars required for valid calculation

# =====================
# NSE STOCKS & INDICES
# =====================
def get_nifty_500_symbols() -> List[str]:
    """
    Fetch top 500 NSE stocks from Nifty 500 index constituents.
    Uses NSE API to get official index constituents.
    
    Returns:
        List of stock symbols with .NS suffix for yfinance
    """
    try:
        # NSE API endpoint for NIFTY 500 constituents
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract symbols from API response
        if 'data' in data:
            # Filter out 'NIFTY 500' index name itself (first element)
            symbols = [stock['symbol'] + '.NS' for stock in data['data'] 
                      if stock['symbol'].upper() not in ['NIFTY 500', 'NIFTY']]
            logger.info(f"Fetched {len(symbols)} symbols from NIFTY 500 index")
            return symbols
        else:
            raise ValueError("Unexpected API response format")
            
    except Exception as e:
        logger.error(f"Failed to fetch NIFTY 500 constituents: {e}")
        logger.warning("Using fallback hardcoded symbols")
        return [
            "^NSEI",        # NIFTY 50
            "^NSEBANK",     # BANKNIFTY
            "RELIANCE.NS",
            "TCS.NS",
            "INFY.NS",
            "HDFCBANK.NS",
            "ICICIBANK.NS",
            "SBIN.NS",
            "LT.NS",
            "AXISBANK.NS",
            "BAJFINANCE.NS"
        ]

# =====================
# LOGGING SETUP
# =====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =====================
# ICHIMOKU CALCULATION
# =====================
def calculate_ichimoku(
    dataframe: pd.DataFrame,
    tenkan_period: int = TENKAN_PERIOD,
    kijun_period: int = KIJUN_PERIOD
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Ichimoku Tenkan-sen and Kijun-sen lines.

    Tenkan-sen (Conversion Line) = (9-period high + 9-period low) / 2
    Kijun-sen (Base Line) = (26-period high + 26-period low) / 2

    Args:
        dataframe: OHLC price data with 'High' and 'Low' columns
        tenkan_period: Period for Tenkan-sen calculation (default: 9)
        kijun_period: Period for Kijun-sen calculation (default: 26)

    Returns:
        Tuple of (tenkan_series, kijun_series)

    Raises:
        ValueError: If required columns are missing from dataframe
    """
    if 'High' not in dataframe.columns or 'Low' not in dataframe.columns:
        raise ValueError("DataFrame must contain 'High' and 'Low' columns")

    tenkan_sen = (
        dataframe['High'].rolling(window=tenkan_period).max() +
        dataframe['Low'].rolling(window=tenkan_period).min()
    ) / 2

    kijun_sen = (
        dataframe['High'].rolling(window=kijun_period).max() +
        dataframe['Low'].rolling(window=kijun_period).min()
    ) / 2

    return tenkan_sen, kijun_sen


def calculate_signal_metrics(
    close_price: float,
    tenkan_value: float,
    kijun_value: float
) -> Tuple[float, float, str]:
    """
    Calculate gap percentage and signal direction.

    Args:
        close_price: Current close price
        tenkan_value: Tenkan-sen value
        kijun_value: Kijun-sen value

    Returns:
        Tuple of (gap_percentage, distance_from_tenkan_pct, signal_direction)
    """
    # Calculate Tenkan-Kijun gap as percentage of the gap relative to Kijun
    # This normalizes the gap size independent of absolute price levels
    gap_percentage = abs(tenkan_value - kijun_value) / kijun_value * 100

    # Calculate distance from Tenkan as percentage of close price
    distance_from_tenkan_pct = abs(close_price - tenkan_value) / close_price * 100

    # Determine signal direction
    if tenkan_value > kijun_value:
        signal_direction = "Bullish"
    elif tenkan_value < kijun_value:
        signal_direction = "Bearish"
    else:
        signal_direction = "Neutral"

    return gap_percentage, distance_from_tenkan_pct, signal_direction


def scan_symbol(symbol: str) -> Optional[List]:
    """
    Scan a single symbol for Ichimoku gap setup.

    Args:
        symbol: Stock symbol to scan (e.g., 'RELIANCE.NS')

    Returns:
        List of scan results if criteria met, None otherwise
    """
    try:
        # Download historical data
        dataframe = yf.download(
            symbol,
            interval=TIMEFRAME,
            period=PERIOD,
            progress=False
        )

        # Handle MultiIndex columns from yfinance
        # Columns are (OHLCV, symbol), so flatten to just OHLCV names
        if isinstance(dataframe.columns, pd.MultiIndex):
            dataframe.columns = dataframe.columns.get_level_values(0)
        
        # Validate sufficient data
        if len(dataframe) < MIN_DATA_POINTS:
            logger.warning(
                f"{symbol}: Insufficient data ({len(dataframe)} bars, need {MIN_DATA_POINTS})"
            )
            return None

        # Calculate Ichimoku indicators
        tenkan_series, kijun_series = calculate_ichimoku(dataframe)

        # Get latest values - use .values[-1] to extract scalar from Series
        close_price = float(dataframe['Close'].values[-1])
        tenkan_value = float(tenkan_series.values[-1])
        kijun_value = float(kijun_series.values[-1])

        # Check for NaN values (insufficient data for rolling calculations)
        if pd.isna(tenkan_value) or pd.isna(kijun_value) or pd.isna(close_price):
            logger.warning(f"{symbol}: NaN values in calculation (need more historical data)")
            return None

        # Calculate metrics
        gap_pct, distance_from_tenkan_pct, signal_direction = calculate_signal_metrics(
            close_price, tenkan_value, kijun_value
        )

        # Check if criteria are met
        if gap_pct >= MIN_GAP_PCT and distance_from_tenkan_pct <= PRICE_NEAR_TENKAN_PCT:
            logger.info(f"{symbol}: Match found - {signal_direction} setup")
            return [
                symbol,
                round(close_price, 2),
                round(tenkan_value, 2),
                round(kijun_value, 2),
                round(gap_pct, 2),
                signal_direction
            ]

        return None

    except Exception as error:
        logger.error(f"{symbol}: Error during scan - {error}")
        return None


def main() -> None:
    """Main execution function for stock scanning."""
    logger.info("Starting Ichimoku gap scan")
    logger.info(f"Timeframe: {TIMEFRAME} | Period: {PERIOD}")
    logger.info(f"Min Gap: {MIN_GAP_PCT}% | Max Distance from Tenkan: {PRICE_NEAR_TENKAN_PCT}%")

    # Fetch Nifty 500 constituents
    symbols = get_nifty_500_symbols()
    
    results: List[List] = []

    # Scan all symbols
    for symbol in symbols:
        result = scan_symbol(symbol)
        if result:
            results.append(result)

    # Sort results by gap percentage (descending)
    results.sort(key=lambda x: x[4], reverse=True)

    # Generate output DataFrame
    column_names = ["Symbol", "Close", "Tenkan", "Kijun", "TK Gap %", "Signal"]
    results_dataframe = pd.DataFrame(results, columns=column_names)

    # Save to CSV with timestamp
    date_string = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"wishlist_tk_gap_{date_string}.csv"

    results_dataframe.to_csv(filename, index=False)

    # Display results
    logger.info("=" * 60)
    logger.info("SCAN COMPLETE")
    logger.info(f"Matches found: {len(results)}")
    logger.info(f"Saved as: {filename}")
    logger.info("=" * 60)

    if len(results) > 0:
        print("\n" + results_dataframe.to_string(index=False))
    else:
        print("\nNo stocks matching criteria found.")


if __name__ == "__main__":
    main()
