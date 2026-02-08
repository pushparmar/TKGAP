"""
Flask web application for Ichimoku Technical Analysis Scanner
Provides a web UI to run scans on different timeframes and display results
"""

from flask import Flask, render_template, request, jsonify, send_file
import logging
from datetime import datetime
from typing import List, Tuple, Optional
import os
import pandas as pd
import yfinance as yf
import requests
import json
from pathlib import Path
from fpdf import FPDF
from io import BytesIO

# =====================
# CONFIGURATION
# =====================
TIMEFRAME_OPTIONS = {
    "30m": "30 Minutes",
    "1h": "1 Hour",
    "4h": "4 Hours",
    "1d": "1 Day"
}

PERIOD: str = "3mo"                # Historical data period
MIN_GAP_PCT: float = 3.0           # Minimum Tenkan-Kijun gap percentage
PRICE_NEAR_TENKAN_PCT: float = 0.4 # Maximum distance from Tenkan (%)
TENKAN_PERIOD: int = 9             # Tenkan-sen (Conversion Line) period
KIJUN_PERIOD: int = 26             # Kijun-sen (Base Line) period
MIN_DATA_POINTS: int = 30          # Minimum bars required for valid calculation
HISTORY_DIR: str = "scan_history"  # Directory to store scan history
MAX_HISTORY: int = 3               # Maximum number of scans to keep

# =====================
# SETUP
# =====================
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create history directory if it doesn't exist
Path(HISTORY_DIR).mkdir(exist_ok=True)


# =====================
# HISTORY MANAGEMENT
# =====================
def save_scan_history(scan_result: dict) -> str:
    """Save scan result to history (keeps last 3 scans)."""
    try:
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{HISTORY_DIR}/scan_{timestamp}.json"
        
        # Add id for reference
        scan_result['id'] = timestamp
        
        # Save to JSON file
        with open(filename, 'w') as f:
            json.dump(scan_result, f, indent=2)
        
        logger.info(f"Saved scan history: {filename}")
        
        # Clean up old scans, keep only last MAX_HISTORY
        history_files = sorted(Path(HISTORY_DIR).glob("scan_*.json"))
        if len(history_files) > MAX_HISTORY:
            for old_file in history_files[:-MAX_HISTORY]:
                old_file.unlink()
                logger.info(f"Deleted old scan: {old_file}")
        
        return timestamp
    
    except Exception as e:
        logger.error(f"Error saving scan history: {e}")
        return None


def load_scan_history() -> List[dict]:
    """Load all saved scans from history."""
    try:
        history_files = sorted(Path(HISTORY_DIR).glob("scan_*.json"), reverse=True)
        scans = []
        
        for file in history_files:
            try:
                with open(file, 'r') as f:
                    scan = json.load(f)
                    scans.append(scan)
            except Exception as e:
                logger.error(f"Error loading {file}: {e}")
                continue
        
        return scans
    
    except Exception as e:
        logger.error(f"Error loading scan history: {e}")
        return []


def generate_pdf(scan_result: dict) -> BytesIO:
    """Generate PDF report from scan result."""
    try:
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Ichimoku Technical Analysis Scan Report", ln=True, align='C')
        
        pdf.set_font("Arial", "", 10)
        pdf.ln(5)
        
        # Scan Details
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, "Scan Details", ln=True)
        pdf.set_font("Arial", "", 10)
        
        pdf.cell(40, 6, f"Scan Time: {scan_result.get('scan_time', 'N/A')}")
        pdf.cell(40, 6, f"Timeframe: {scan_result.get('timeframe', 'N/A')}")
        pdf.cell(40, 6, f"Min Gap: {scan_result.get('min_gap', 'N/A')}%")
        pdf.cell(0, 6, f"Symbols Scanned: {scan_result.get('symbols_scanned', 0)}", ln=True)
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 6, f"Matches Found: {scan_result.get('matches_found', 0)}", ln=True)
        
        pdf.ln(5)
        
        # Results Table
        if scan_result.get('results'):
            pdf.set_font("Arial", "B", 10)
            col_widths = [25, 20, 25, 25, 20, 25]
            headers = ['Symbol', 'Close', 'Tenkan', 'Kijun', 'Gap %', 'Signal']
            
            # Header
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 8, header, border=1, align='C')
            pdf.ln()
            
            # Rows
            pdf.set_font("Arial", "", 9)
            for result in scan_result['results'][:50]:  # Limit to first 50 for PDF
                pdf.cell(col_widths[0], 7, result[0], border=1)
                pdf.cell(col_widths[1], 7, str(result[1]), border=1, align='R')
                pdf.cell(col_widths[2], 7, str(result[2]), border=1, align='R')
                pdf.cell(col_widths[3], 7, str(result[3]), border=1, align='R')
                pdf.cell(col_widths[4], 7, str(result[4]), border=1, align='R')
                pdf.cell(col_widths[5], 7, result[5], border=1, align='C')
                pdf.ln()
        
        pdf.ln(5)
        pdf.set_font("Arial", "", 8)
        pdf.cell(0, 6, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align='C')
        
        # Return as bytes
        pdf_bytes = BytesIO()
        pdf_output = pdf.output(dest='S').encode('latin-1')
        pdf_bytes.write(pdf_output)
        pdf_bytes.seek(0)
        
        return pdf_bytes
    
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        return None


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
    """Calculate gap percentage and signal direction."""
    gap_percentage = abs(tenkan_value - kijun_value) / kijun_value * 100
    distance_from_tenkan_pct = abs(close_price - tenkan_value) / close_price * 100

    if tenkan_value > kijun_value:
        signal_direction = "Bullish"
    elif tenkan_value < kijun_value:
        signal_direction = "Bearish"
    else:
        signal_direction = "Neutral"

    return gap_percentage, distance_from_tenkan_pct, signal_direction


def get_nifty_500_symbols() -> List[str]:
    """Fetch top 500 NSE stocks from Nifty 500 index constituents."""
    try:
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
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
            "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
            "SBIN.NS", "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS"
        ]


def scan_symbol(symbol: str, timeframe: str, min_gap: float = MIN_GAP_PCT) -> Optional[List]:
    """Scan a single symbol for Ichimoku gap setup."""
    try:
        dataframe = yf.download(
            symbol,
            interval=timeframe,
            period=PERIOD,
            progress=False
        )

        # Handle MultiIndex columns from yfinance
        if isinstance(dataframe.columns, pd.MultiIndex):
            dataframe.columns = dataframe.columns.get_level_values(0)
        
        if len(dataframe) < MIN_DATA_POINTS:
            return None

        tenkan_series, kijun_series = calculate_ichimoku(dataframe)

        close_price = float(dataframe['Close'].values[-1])
        tenkan_value = float(tenkan_series.values[-1])
        kijun_value = float(kijun_series.values[-1])

        if pd.isna(tenkan_value) or pd.isna(kijun_value) or pd.isna(close_price):
            return None

        gap_pct, distance_from_tenkan_pct, signal_direction = calculate_signal_metrics(
            close_price, tenkan_value, kijun_value
        )

        # Check both gap percentage and distance from Tenkan
        if gap_pct >= min_gap and distance_from_tenkan_pct <= PRICE_NEAR_TENKAN_PCT:
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


def run_scan(timeframe: str, min_gap: float = MIN_GAP_PCT) -> dict:
    """Execute scan and return results as dictionary."""
    logger.info(f"Starting scan with timeframe: {timeframe}, min_gap: {min_gap}%")
    
    symbols = get_nifty_500_symbols()
    results = []
    
    for idx, symbol in enumerate(symbols):
        try:
            result = scan_symbol(symbol, timeframe, min_gap)
            if result:
                results.append(result)
            
            # Log progress every 50 stocks
            if (idx + 1) % 50 == 0:
                logger.info(f"Scanned {idx + 1}/{len(symbols)} symbols...")
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            continue
    
    # Sort by gap percentage (descending)
    results.sort(key=lambda x: x[4], reverse=True)
    
    return {
        "timeframe": timeframe,
        "min_gap": min_gap,
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbols_scanned": len(symbols),
        "matches_found": len(results),
        "results": results
    }


# =====================
# ROUTES
# =====================
@app.route('/')
def index():
    """Render main dashboard page."""
    return render_template('index.html', timeframes=TIMEFRAME_OPTIONS)


@app.route('/api/scan', methods=['POST'])
def api_scan():
    """API endpoint to run scan."""
    try:
        data = request.get_json()
        timeframe = data.get('timeframe', '1h')
        min_gap = float(data.get('min_gap', MIN_GAP_PCT))
        
        if timeframe not in TIMEFRAME_OPTIONS:
            return jsonify({"error": "Invalid timeframe"}), 400
        
        if min_gap < 0 or min_gap > 100:
            return jsonify({"error": "Minimum gap must be between 0 and 100"}), 400
        
        logger.info(f"Received scan request for timeframe: {timeframe}, min_gap: {min_gap}%")
        scan_result = run_scan(timeframe, min_gap)
        
        # Save to history
        history_id = save_scan_history(scan_result)
        scan_result['history_id'] = history_id
        
        return jsonify(scan_result)
    
    except ValueError:
        return jsonify({"error": "Invalid minimum gap value"}), 400
    except Exception as e:
        logger.error(f"Scan error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/status', methods=['GET'])
def api_status():
    """Health check endpoint."""
    return jsonify({"status": "OK", "message": "Ichimoku Scanner is running"})


@app.route('/api/history', methods=['GET'])
def api_history():
    """Get all saved scan history."""
    try:
        scans = load_scan_history()
        # Prepare response with summary info
        history_summary = []
        for scan in scans:
            history_summary.append({
                "id": scan.get('id'),
                "scan_time": scan.get('scan_time'),
                "timeframe": scan.get('timeframe'),
                "min_gap": scan.get('min_gap'),
                "symbols_scanned": scan.get('symbols_scanned'),
                "matches_found": scan.get('matches_found')
            })
        return jsonify({"history": history_summary})
    
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/history/<scan_id>', methods=['GET'])
def api_history_detail(scan_id: str):
    """Get detailed scan result from history."""
    try:
        filename = f"{HISTORY_DIR}/scan_{scan_id}.json"
        if Path(filename).exists():
            with open(filename, 'r') as f:
                scan_result = json.load(f)
            return jsonify(scan_result)
        else:
            return jsonify({"error": "Scan not found"}), 404
    
    except Exception as e:
        logger.error(f"Error retrieving scan detail: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/download-pdf', methods=['POST'])
def api_download_pdf():
    """Download scan result as PDF."""
    try:
        data = request.get_json()
        scan_id = data.get('scan_id')
        
        # If scan_id provided, load from history; otherwise use current results
        if scan_id:
            filename = f"{HISTORY_DIR}/scan_{scan_id}.json"
            if Path(filename).exists():
                with open(filename, 'r') as f:
                    scan_result = json.load(f)
            else:
                return jsonify({"error": "Scan not found"}), 404
        else:
            # Use the data from request (current scan)
            scan_result = data.get('scan_result')
            if not scan_result:
                return jsonify({"error": "No scan data provided"}), 400
        
        pdf_bytes = generate_pdf(scan_result)
        if pdf_bytes:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ichimoku_scan_{timestamp}.pdf"
            return send_file(
                pdf_bytes,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({"error": "Failed to generate PDF"}), 500
    
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting Ichimoku Scanner Web UI")
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)
