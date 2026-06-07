"""
MACD (Weekly) and RSI (Daily) Signal Calculator

Calculates:
  - Weekly MACD: Using weekly-resampled price data.
  - Daily RSI: Using daily price data.

Uses Yahoo Finance for price data.
"""

import sys
import yfinance as yf
import pandas as pd


def calculate_macd(df, fast=12, slow=26, signal=9):
    """Calculate MACD, Signal line, and Histogram from a DataFrame with a 'Close' column."""
    ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    df["MACD"] = macd_line
    df["Signal"] = signal_line
    df["Histogram"] = histogram
    return df


def calculate_rsi(df, window=14):
    """Calculate the Relative Strength Index (RSI)."""
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Use Wilder's smoothing (exponential moving average with alpha = 1/window)
    avg_gain = gain.ewm(alpha=1/window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/window, adjust=False).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def resample_to_weekly(df):
    """Resample daily OHLC data to weekly OHLC data."""
    # Ensure index is datetime
    df.index = pd.to_datetime(df.index)
    
    # Resample to weekly (end of week, Sunday 'W' or Monday 'W-MON')
    # Using 'W-FRI' often makes sense for market data
    weekly = df.resample('W-FRI').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })
    return weekly.dropna()


def interpret_macd(row):
    """Return a simple Buy/Sell/Hold interpretation based on MACD vs Signal."""
    if row["MACD"] > row["Signal"] and row["Histogram"] > 0:
        return "📈 BULLISH"
    elif row["MACD"] < row["Signal"] and row["Histogram"] < 0:
        return "📉 BEARISH"
    else:
        return "➡️  NEUTRAL"


def interpret_rsi(val):
    """Interpret RSI value."""
    if val >= 60:
        return "🔥 OVERBOUGHT"
    elif val <= 40:
        return "❄️  OVERSOLD"
    else:
        return "✅ NEUTRAL"


def get_analysis(ticker):
    """Fetch data and return analysis results for a given ticker."""
    try:
        # Fetch 2 years of daily data to have enough weeks for Weekly MACD
        data_daily = yf.download(ticker, period="2y", interval="1d", progress=False)

        if data_daily.empty:
            return None

        # Flatten multi-level columns if present
        if isinstance(data_daily.columns, pd.MultiIndex):
            data_daily.columns = data_daily.columns.get_level_values(0)

        # 1. Calculate Daily RSI
        data_daily = calculate_rsi(data_daily)
        
        # 2. Resample to Weekly and calculate Weekly MACD
        data_weekly = resample_to_weekly(data_daily.copy())
        if data_weekly.empty:
            return None
        data_weekly = calculate_macd(data_weekly)

        # Latest Values
        latest_daily = data_daily.iloc[-1]
        latest_weekly = data_weekly.iloc[-1]

        return {
            "ticker": ticker,
            "date_daily": latest_daily.name.strftime('%Y-%m-%d'),
            "close": latest_daily['Close'],
            "rsi": latest_daily['RSI'],
            "rsi_trend": interpret_rsi(latest_daily['RSI']),
            "date_weekly": latest_weekly.name.strftime('%Y-%m-%d'),
            "macd": latest_weekly['MACD'],
            "signal": latest_weekly['Signal'],
            "histogram": latest_weekly['Histogram'],
            "weekly_trend": interpret_macd(latest_weekly)
        }
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None


def main():
    ticker = input("Enter stock ticker symbol (e.g. AAPL, RELIANCE.NS): ").strip().upper()
    if not ticker:
        print("No ticker entered. Exiting.")
        sys.exit(1)

    print(f"\nFetching data for {ticker}...")
    results = get_analysis(ticker)

    if not results:
        print(f"Error: No data found for ticker '{ticker}'.")
        return

    # Output Results
    print(f"\n{'='*60}")
    print(f"  Technical Analysis for {ticker}")
    print(f"{'='*60}")
    
    print(f"\n[DAILY TIMEFRAME]")
    print(f"  Date         : {results['date_daily']}")
    print(f"  Close        : {results['close']:.2f}")
    print(f"  RSI (14)     : {results['rsi']:.2f} ({results['rsi_trend']})")

    print(f"\n[WEEKLY TIMEFRAME]")
    print(f"  Week Ending  : {results['date_weekly']}")
    print(f"  MACD Line    : {results['macd']:.4f}")
    print(f"  Signal Line  : {results['signal']:.4f}")
    print(f"  Histogram    : {results['histogram']:.4f}")
    print(f"  MACD Bias    : {results['weekly_trend']}")
    
    print(f"\n{'─'*60}")
    print(f"  SUMMARY: Weekly trend is {results['weekly_trend']}")
    print(f"           Daily momentum is {results['rsi_trend']}")
    print(f"{'─'*60}\n")


if __name__ == "__main__":
    main()
