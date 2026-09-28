import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import time

# Page Configuration
st.set_page_config(page_title="OKX Pattern Scanner", layout="wide")
st.title("📈 OKX Multi-Timeframe Chart Pattern Scanner")

# OKX Exchange initialization
exchange = ccxt.okx({
    'enableRateLimit': True,
})

TIMEFRAMES = ['15m', '1h', '4h', '1d']

PATTERN_INFO = {
    "Double Top": "🔴 BEARISH Reversal (Price Neeche Ja Sakti Hai)",
    "Double Bottom": "🟢 BULLISH Reversal (Price Upar Ja Sakti Hai)",
    "Head & Shoulders": "🔴 BEARISH Reversal (Price Neeche Ja Sakti Hai)",
    "Inverse Head & Shoulders": "🟢 BULLISH Reversal (Price Upar Ja Sakti Hai)",
    "Ascending Triangle": "🟢 BULLISH Breakout (Upar Jaane Ke Chance)",
    "Descending Triangle": "🔴 BEARISH Breakout (Neeche Girne Ke Chance)",
    "Symmetrical Triangle": "🟡 NEUTRAL (Dono Taraf Breakout Ho Sakta Hai)",
    "Rising Wedge": "🔴 BEARISH Reversal (Neeche Girne Ke Chance)",
    "Falling Wedge": "🟢 BULLISH Reversal (Upar Jaane Ke Chance)",
    "Channel Up": "🟢 BULLISH Trend (Support Break Hone Par Bearish)",
    "Channel Down": "🔴 BEARISH Trend (Resistance Break Hone Par Bullish)"
}

@st.cache_data(ttl=300)
def get_okx_top_500_pairs():
    tickers = exchange.fetch_tickers()
    usdt_pairs = []
    for symbol, data in tickers.items():
        if symbol.endswith('/USDT') and data.get('quoteVolume') is not None:
            usdt_pairs.append({
                'symbol': symbol,
                'volume': data['quoteVolume'],
                'change': data.get('percentage', 0)
            })
    df = pd.DataFrame(usdt_pairs)
    df = df.sort_values(by='volume', ascending=False).head(500)
    return df['symbol'].tolist()

def detect_chart_patterns(df):
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

# Start Button
if st.button("Start Market Scan"):
    symbols = get_okx_top_500_pairs()
    st.write(f"🔍 Top {len(symbols)} coins scan ho rahe hain multi-timeframes par...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    table_placeholder = st.empty()
    
    results = []
    total_symbols = 50 # Speed testing ke liye top 50
    
    for idx, symbol in enumerate(symbols[:total_symbols]):
        status_text.text(f"Scanning ({idx+1}/{total_symbols}): {symbol}")
        progress_bar.progress((idx + 1) / total_symbols)
        
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
                        'Details / Signal': info
                    })
                    
                    # Real-time Table Update
                    table_placeholder.dataframe(pd.DataFrame(results), use_container_width=True)
                
                time.sleep(0.01)
            except Exception:
                continue

    st.success("✅ Scanning Complete!")
