import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import time

# Mobile Friendly Layout
st.set_page_config(page_title="OKX Pattern Scanner", layout="centered")

st.title("📲 OKX Chart Pattern Scanner")

# OKX Exchange
exchange = ccxt.okx({
    'enableRateLimit': True,
})

# Pattern Details & Signal Info
PATTERN_INFO = {
    "Double Top": {"signal": "🔴 BEARISH Reversal", "detail": "Price M-Shape bana kar resistance se rejection le rahi hai, neeche gir sakti hai."},
    "Double Bottom": {"signal": "🟢 BULLISH Reversal", "detail": "Price W-Shape bana kar support se bounce ho rahi hai, upar ja sakti hai."},
    "Head & Shoulders": {"signal": "🔴 BEARISH Reversal", "detail": "Neckline break hone par strong downward move aa sakta hai."},
    "Inverse Head & Shoulders": {"signal": "🟢 BULLISH Reversal", "detail": "Neckline break hone par strong upward pump aa sakta hai."},
    "Ascending Triangle": {"signal": "🟢 BULLISH Breakout", "detail": "Flat resistance breakout par upar jaane ke high chances hain."},
    "Descending Triangle": {"signal": "🔴 BEARISH Breakout", "detail": "Flat support break hone par neeche girne ke chances hain."},
    "Symmetrical Triangle": {"signal": "🟡 NEUTRAL", "detail": "Dono taraf breakout ho sakta hai, direction confirm hone ka wait karein."},
    "Rising Wedge": {"signal": "🔴 BEARISH Reversal", "detail": "Range narrow ho rahi hai, support toot-te hi drop aa sakta hai."},
    "Falling Wedge": {"signal": "🟢 BULLISH Reversal", "detail": "Range narrow ho rahi hai, resistance break hote hi pump ho sakta hai."},
    "Channel Up": {"signal": "🟢 BULLISH Trend", "detail": "Price upper channel mein hai, lower line break hone par trend badal sakta hai."},
    "Channel Down": {"signal": "🔴 BEARISH Trend", "detail": "Price lower channel mein hai, upper line break hone par bullish reversal aa sakta hai."}
}

# Mobile Controls Section
st.subheader("⚙️ Scanner Settings")

# 1. Custom Timeframe Selection
selected_tf = st.multiselect(
    "Timeframe select karein:",
    options=['15m', '1h', '4h', '1d'],
    default=['15m', '1h']
)

# 2. Custom Coin Count (Up to 500)
coin_limit = st.slider("Kitne Coins scan karne hain?", min_value=10, max_value=500, value=50, step=10)

@st.cache_data(ttl=300)
def get_okx_pairs(limit):
    tickers = exchange.fetch_tickers()
    usdt_pairs = []
    for symbol, data in tickers.items():
        if symbol.endswith('/USDT') and data.get('quoteVolume') is not None:
            usdt_pairs.append({
                'symbol': symbol,
                'volume': data['quoteVolume']
            })
    df = pd.DataFrame(usdt_pairs)
    df = df.sort_values(by='volume', ascending=False).head(limit)
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
    
    # 10 Chart Patterns Logic
    if abs(recent_highs[-1] - recent_highs[-10]) / recent_highs[-1] < 0.005 and close[-1] < recent_highs[-1]:
        patterns_found.append("Double Top")
        
    if abs(recent_lows[-1] - recent_lows[-10]) / recent_lows[-1] < 0.005 and close[-1] > recent_lows[-1]:
        patterns_found.append("Double Bottom")

    if abs(max(recent_highs) - recent_highs[-1]) / recent_highs[-1] < 0.008 and recent_lows[-1] > recent_lows[-10]:
        patterns_found.append("Ascending Triangle")

    if abs(min(recent_lows) - recent_lows[-1]) / recent_lows[-1] < 0.008 and recent_highs[-1] < recent_highs[-10]:
        patterns_found.append("Descending Triangle")

    if recent_highs[-1] < recent_highs[-10] and recent_lows[-1] > recent_lows[-10]:
        patterns_found.append("Symmetrical Triangle")

    if recent_highs[-1] > recent_highs[-5] and recent_lows[-1] > recent_lows[-5] and (recent_highs[-1] - recent_lows[-1]) < (recent_highs[-10] - recent_lows[-10]):
        patterns_found.append("Rising Wedge")

    if recent_highs[-1] < recent_highs[-5] and recent_lows[-1] < recent_lows[-5] and (recent_highs[-1] - recent_lows[-1]) < (recent_highs[-10] - recent_lows[-10]):
        patterns_found.append("Falling Wedge")

    if recent_highs[-1] > recent_highs[-10] and recent_lows[-1] > recent_lows[-10]:
        patterns_found.append("Channel Up")

    if recent_highs[-1] < recent_highs[-10] and recent_lows[-1] < recent_lows[-10]:
        patterns_found.append("Channel Down")

    if len(high) >= 30:
        if high[-15] > high[-25] and high[-15] > high[-5]:
            patterns_found.append("Head & Shoulders")
        if low[-15] < low[-25] and low[-15] < low[-5]:
            patterns_found.append("Inverse Head & Shoulders")

    return list(set(patterns_found))

# --- SCAN BUTTON ---
if st.button("🚀 Start Pattern Scan", use_container_width=True):
    if not selected_tf:
        st.error("Khabardar: Kam az kam ek Timeframe select karein!")
    else:
        symbols = get_okx_pairs(coin_limit)
        st.info(f"🔍 Top {len(symbols)} coins scan ho rahe hain selected timeframes par...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_steps = len(symbols)
        found_coins = set() # Har coin ka ek hi result lene ke liye
        
        for idx, symbol in enumerate(symbols):
            status_text.text(f"Scanning ({idx+1}/{total_steps}): {symbol}")
            progress_bar.progress((idx + 1) / total_steps)
            
            # Agar coin pehle detect ho gaya hai toh skip karein
            if symbol in found_coins:
                continue

            for tf in selected_tf:
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=100)
                    df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
                    
                    patterns = detect_chart_patterns(df)
                    if patterns and symbol not in found_coins:
                        p = patterns[0] # Ek coin ka sirf EK pattern
                        info = PATTERN_INFO.get(p, {"signal": "N/A", "detail": ""})
                        
                        # OKX TradingView Direct Link
                        clean_symbol = symbol.replace("/", "")
                        tv_url = f"https://www.tradingview.com/chart/?symbol=OKX%3A{clean_symbol}"
                        
                        # Mobile Card Display
                        with st.container():
                            st.markdown(f"""
                            ---
                            ### 📌 **{symbol}**
                            * **Timeframe:** `{tf}`
                            * **Pattern:** **{p}**
                            * **Signal:** {info['signal']}
                            * **Detail:** {info['detail']}
                            """)
                            st.link_button(f"🔗 Open {symbol} Chart on TradingView", tv_url)
                        
                        found_coins.add(symbol)
                        break
                        
                    time.sleep(0.01)
                except Exception:
                    continue

        st.success("✅ Scan Complete!")
