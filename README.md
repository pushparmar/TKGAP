# Ichimoku Technical Analysis Scanner - Web UI

A real-time technical analysis scanner for NSE Nifty 500 stocks using the Ichimoku indicator to identify Tenkan-Kijun gap trading setups.

## 📊 Features

- **Dynamic Timeframe Selection**: Choose between 30-minute, 1-hour, and 1-day intervals
- **Real-time NSE Data**: Automatically fetches Nifty 500 constituents from NSE API
- **Ichimoku Indicator Analysis**: Calculates Tenkan-sen and Kijun-sen lines
- **Gap Detection**: Identifies stocks with Tenkan-Kijun gaps exceeding 1.5%
- **Signal Classification**: Categorizes setups as Bullish or Bearish
- **Beautiful Web Dashboard**: Interactive table-based UI with modern design
- **CSV Export**: Automatically saves results for further analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Virtual environment (recommended)

### Installation

1. **Navigate to project directory**:
```bash
cd /workspaces/TKGAP
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

### Running the Web Server

```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Using the Web Dashboard

1. **Select Timeframe**: Choose 30m, 1h, or 1d
2. **Click "Run Scan"**: Initiates scan of all Nifty 500 stocks
3. **View Results**: Results displayed in table format, sorted by gap strength
4. **Analyze**: Review Signal (Bullish/Bearish), prices, and gap percentages

## 📁 File Structure

```
/workspaces/TKGAP/
├── app.py                    # Flask backend application
├── main.py                   # CLI scanner (original)
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── templates/
│   └── index.html            # Web UI dashboard
└── wishlist_tk_gap_*.csv     # Results (auto-generated)
```

## ⚙️ Configuration

Edit these constants in `app.py` to customize:

```python
PERIOD = "3mo"                  # Historical data period
MIN_GAP_PCT = 3.0              # Minimum Tenkan-Kijun gap %
PRICE_NEAR_TENKAN_PCT = 0.4   # Max distance from Tenkan
TENKAN_PERIOD = 9              # Tenkan-sen period
KIJUN_PERIOD = 26              # Kijun-sen period
MIN_DATA_POINTS = 30           # Minimum bars required
```

## 📈 Trading Setup Explanation

### Tenkan-Kijun Gap (Ichimoku)

- **Tenkan-sen** = (9-period high + 9-period low) / 2
- **Kijun-sen** = (26-period high + 26-period low) / 2
- **Gap** = |Tenkan - Kijun| / Kijun × 100%

### Bullish Setup
- Tenkan > Kijun (uptrend)
- Price near Tenkan line (support)
- Large gap indicates strong momentum

### Bearish Setup
- Tenkan < Kijun (downtrend)
- Price near Tenkan line (resistance)
- Large gap indicates strong momentum

## 🔧 API Endpoints

### `GET /`
Returns the main dashboard HTML

### `POST /api/scan`
Executes scan with specified timeframe

**Request:**
```json
{
  "timeframe": "1h"
}
```

**Response:**
```json
{
  "timeframe": "1h",
  "scan_time": "2026-02-08 14:29:16",
  "symbols_scanned": 500,
  "matches_found": 38,
  "results": [
    ["TRITURBINE.NS", 502.75, 501.0, 520.8, 3.8, "Bearish"],
    ...
  ]
}
```

### `GET /api/status`
Health check endpoint

## 📊 Result Interpretation

| Column | Meaning |
|--------|---------|
| Symbol | Stock ticker with .NS suffix |
| Close Price | Current closing price |
| Tenkan | Conversion line value |
| Kijun | Base line value |
| TK Gap % | Tenkan-Kijun gap percentage |
| Signal | Bullish or Bearish setup |

## 🎯 Usage Examples

### CLI Scanner (Original)
```bash
python main.py
```

### Web Dashboard
1. Open browser to `http://localhost:5000`
2. Select timeframe (defaults to 1h)
3. Click "Run Scan"
4. Wait for results (2-3 minutes for Nifty 500)
5. View and analyze results

## ⚠️ Notes

- **First Scan**: Takes 2-3 minutes to scan all 500 stocks
- **Data Source**: yfinance for OHLC data, NSE API for constituents
- **Real-time Updates**: Re-run scan to get latest data
- **CSV Format**: Results auto-save to `wishlist_tk_gap_*.csv`

## 🔍 Troubleshooting

**Port 5000 already in use?**
```bash
# Find process using port 5000
lsof -i :5000

# Kill it
kill -9 <PID>
```

**API limit errors?**
- yfinance has rate limits; wait a few minutes before re-scanning
- NSE API requires valid User-Agent header (included in code)

**No results found?**
- Try different timeframes (1d may have fewer matches than 1h)
- Adjust `MIN_GAP_PCT` to lower threshold or `PRICE_NEAR_TENKAN_PCT` to be more/less restrictive

## 📝 License

This project analyzes NSE stock data for educational and research purposes.

## 🤝 Contributing

Suggestions and improvements welcome! Areas for enhancement:
- Email alerts for new matches
- Scheduled automatic scans
- Historical result tracking
- Additional Ichimoku indicators
- Support for other indices (Nifty 50, etc.)

---

**Disclaimer**: This scanner is for educational purposes. Always conduct proper due diligence before trading decisions.