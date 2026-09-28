import ccxt
import pandas as pd
import numpy as np
import time

# OKX Exchange initialization
exchange = ccxt.okx({
    'enableRateLimit': True,
})

# Aapke bataye gaye Multi-Timeframes
TIMEFRAMES = ['15m', '1h', '4h', '1d']

# 10 Patterns aur unki details (Bullish/Bearish)
PATTERN_INFO = {
    "Double Top": "BEARISH Reversal (Price Neeche Ja Sakti Hai)",
    "Double Bottom": "BULLISH Reversal (Price Upar Ja Sakti Hai)",
    "Head & Shoulders": "BEARISH Reversal (Price Neeche Ja Sakti Hai)",
    "Inverse Head & Shoulders": "BULLISH Reversal (Price Upar Ja Sakti Hai)",
    "Ascending Triangle": "BULLISH Continuation/Breakout (Upar Jaane Ke Chance)",
    "Descending Triangle": "BEARISH Continuation/Breakout (Neeche Girne Ke Chance)",
    "Symmetrical Triangle": "NEUTRAL (Dono Taraf Breakout Ho Sakta Hai)",
    "Rising Wedge": "BEARISH Reversal (Neeche Girne Ke Chance)",
    "Falling Wedge": "BULLISH Reversal (Upar Jaane Ke Chance)",
    "Channel Up": "BULLISH Trend (Support Break Hone Par Bearish)",
    "Channel Down": "BEARISH Trend (Resistance Break Hone Par Bullish)"
}

def get_okx_top_500_pairs():
    """OKX se Top 500 USDT pairs fetch karta hai (Gainers + Losers)"""
    print("OKX Market Data Fetch Ho Raha Hai...")
    tickers = exchange.fetch_tickers()
    
    usdt_pairs = []
    for symbol, data in tickers.items():
        if symbol.endswith('/USDT') and data.get('quoteVolume') is not None:
            usdt_pairs.append({
                'symbol': symbol,
                'volume': data['quoteVolume'],
                'change': data.get('percentage', 0)
            })
    
    # Volume ke hisab se top 500 filter karta hai
    df = pd.DataFrame(usdt_pairs)
    df = df.sort_values(by='volume', ascending=False).head(500)
    return df['symbol'].tolist()

def detect_chart_patterns(df):
    """10 Main Chart Patterns detect karne ka logic"""
    patterns_found = []
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    
    if len(close) < 50:
        return patterns_found

    recent_highs = high[-20:]
    recent_lows = low[-20:]
    
    # 1. Double Top
    if abs(recent_highs[-1] - recent_highs[-10]) / recent_highs[-1] < 0.005 and close[-1] < recent_highs[-1]:
        patterns_found.append("Double Top")
        
    # 2. Double Bottom
    if abs(recent_lows[-1] - recent_lows[-10]) / recent_lows[-1] < 0.005 and close[-1] > recent_lows[-1]:
        patterns_found.append("Double Bottom")

    # 3. Ascending Triangle
    if abs(max(recent_highs) - recent_highs[-1]) / recent_highs[-1] < 0.008 and recent_lows[-1] > recent_lows[-10]:
        patterns_found.append("Ascending Triangle")

    # 4. Descending Triangle
    if abs(min(recent_lows) - recent_lows[-1]) / recent_lows[-1] < 0.008 and recent_highs[-1] < recent_highs[-10]:
        patterns_found.append("Descending Triangle")

    # 5. Symmetrical Triangle
    if recent_highs[-1] < recent_highs[-10] and recent_lows[-1] > recent_lows[-10]:
        patterns_found.append("Symmetrical Triangle")

    # 6. Rising Wedge
    if recent_highs[-1] > recent_highs[-5] and recent_lows[-1] > recent_lows[-5] and (recent_highs[-1] - recent_lows[-1]) < (recent_highs[-10] - recent_lows[-10]):
        patterns_found.append("Rising Wedge")

    # 7. Falling Wedge
    if recent_highs[-1] < recent_highs[-5] and recent_lows[-1] < recent_lows[-5] and (recent_highs[-1] - recent_lows[-1]) < (recent_highs[-10] - recent_lows[-10]):
        patterns_found.append("Falling Wedge")

    # 8. Channel Up
    if recent_highs[-1] > recent_highs[-10] and recent_lows[-1] > recent_lows[-10]:
        patterns_found.append("Channel Up")

    # 9. Channel Down
    if recent_highs[-1] < recent_highs[-10] and recent_lows[-1] < recent_lows[-10]:
        patterns_found.append("Channel Down")

    # 10. Head & Shoulders / Inverse Head & Shoulders
    if len(high) >= 30:
        head = high[-15]
        if head > high[-25] and head > high[-5]:
            patterns_found.append("Head & Shoulders")
        
        head_inv = low[-15]
        if head_inv < low[-25] and head_inv < low[-5]:
            patterns_found.append("Inverse Head & Shoulders")

    return list(set(patterns_found))

def run_scanner():
    symbols = get_okx_top_500_pairs()
    print(f"Total {len(symbols)} coins scan hone ja rahe hain...\n")
    
    results = []
    
    # Fast testing ke liye starting me pehle 50 pairs scan karega (Aap 500 tak badha sakte hain)
    for symbol in symbols[:50]:
        for tf in TIMEFRAMES:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=100)
                df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
                
                patterns = detect_chart_patterns(df)
                for p in patterns:
                    info = PATTERN_INFO.get(p, "N/A")
                    results.append({
                        'Symbol': symbol,
                        'Timeframe': tf,
                        'Pattern': p,
                        'Details/Bias': info
                    })
                    print(f"[FOUND] {symbol} | TF: {tf} | Pattern: {p} --> {info}")
                
                time.sleep(0.02) # API Rate Limit ke liye
            except Exception as e:
                continue

    # Summary Output
    if results:
        res_df = pd.DataFrame(results)
        print("\n================ FINAL SCAN RESULTS ================")
        print(res_df.to_string(index=False))
    else:
        print("\nKoi pattern filhal match nahi hua.")

if __name__ == "__main__":
    run_scanner()
  
