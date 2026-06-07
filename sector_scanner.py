import pandas as pd
from macd_signal import get_analysis
import sys

def main():
    # Use command line argument if provided, otherwise default to nifty50.csv
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "nifty50.csv"

    try:
        df_stocks = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: {csv_file} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
        sys.exit(1)

    if "Symbol" not in df_stocks.columns:
        print(f"Error: {csv_file} must contain a 'Symbol' column.")
        sys.exit(1)

    tickers = df_stocks["Symbol"].tolist()
    results = []

    print(f"Scanning {len(tickers)} stocks from {csv_file}... This may take a minute.")

    for ticker in tickers:
        print(f"Analyzing {ticker}...", end="\r")
        res = get_analysis(ticker)
        if res:
            results.append({
                "Scrip": ticker.replace(".NS", ""),
                "Weekly Trend": res["weekly_trend"],
                "Daily Trend": res["rsi_trend"]
            })
    
    print("\nScan complete.\n")

    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    if not results_df.empty:
        results_df = results_df.sort_values(by="Scrip")

    # Print results in specific tables
    def print_table(title, subset_df):
        print(f"\n### {title} ({len(subset_df)} stocks)")
        if subset_df.empty:
            print("No stocks found in this category.")
        else:
            try:
                print(subset_df.to_markdown(index=False))
            except ImportError:
                print(subset_df.to_string(index=False))

    # 1. Strong Bullish: Bullish MACD + Overbought RSI
    strong_bullish = results_df[
        (results_df["Weekly Trend"] == "📈 BULLISH") & 
        (results_df["Daily Trend"] == "🔥 OVERBOUGHT")
    ]
    
    # 2. Strong Bearish: Bearish MACD + Oversold RSI
    strong_bearish = results_df[
        (results_df["Weekly Trend"] == "📉 BEARISH") & 
        (results_df["Daily Trend"] == "❄️  OVERSOLD")
    ]

    # 3. Mild Bullish: Bullish MACD + Neutral RSI
    mild_bullish = results_df[
        (results_df["Weekly Trend"] == "📈 BULLISH") & 
        (results_df["Daily Trend"] == "✅ NEUTRAL")
    ]

    # 4. Mild Bearish: Bearish MACD + Neutral RSI
    mild_bearish = results_df[
        (results_df["Weekly Trend"] == "📉 BEARISH") & 
        (results_df["Daily Trend"] == "✅ NEUTRAL")
    ]

    print_table("🚀 STRONG BULLISH (Weekly Bullish + Daily Overbought)", strong_bullish)
    print_table("🐻 STRONG BEARISH (Weekly Bearish + Daily Oversold)", strong_bearish)
    print_table("📈 MILD BULLISH (Weekly Bullish + Daily Neutral)", mild_bullish)
    print_table("📉 MILD BEARISH (Weekly Bearish + Daily Neutral)", mild_bearish)

if __name__ == "__main__":
    main()
