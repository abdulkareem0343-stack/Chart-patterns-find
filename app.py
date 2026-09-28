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

PATTERN_INFO = {
    "Double Top": {"signal": "🔴 BEARISH Reversal", "detail": "Neckline (Support) break hone par sell/short karein."},
    "Double Bottom": {"signal": "🟢 BULLISH Reversal", "detail": "Neckline (Resistance) break hone par buy/long karein."},
    "Head & Shoulders": {"signal": "🔴 BEARISH Reversal", "detail": "Neckline break hone par strong downward move expected."},
    "Inverse Head & Shoulders": {"signal": "🟢 BULLISH Reversal", "detail": "Neckline break hone par strong upward pump expected."},
    "Ascending Triangle": {"signal": "🟢 BULLISH Breakout", "detail": "Flat Resistance level break hone par buy karein."},
    "Descending Triangle": {"signal": "🔴 BEARISH Breakout", "detail": "Flat Support level break hone par sell karein."},
    "Symmetrical Triangle": {"signal": "🟡 NEUTRAL", "detail": "Key price level break hone ka wait karein."},
    "Rising Wedge": {"signal": "🔴 BEARISH Reversal", "detail": "Lower Support line toot-te hi drop aa sakta hai."},
    "Falling Wedge": {"signal": "🟢 BULLISH Reversal", "detail": "Upper Resistance break hote hi pump ho sakta hai."},
    "Channel Up": {"signal": "🟢 BULLISH Trend", "detail": "Lower Support line tootne par trend reversal hoga."},
    "Channel Down": {"signal": "🔴 BEARISH Trend", "detail": "Upper Resistance line tootne par bullish move aayega."}
}

# Controls
st.subheader("⚙️ Scanner Settings")

selected_tf = st.multiselect(
    "Timeframe select karein:",
    options=['15m', '1h', '4h', '1d'],
    default=['15m', '1h']
)

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
    current_price = close[-1]
    
    # Double Top (Neckline = Minimum Low between tops)
    if abs(recent_highs[-1] - recent_highs[-10]) / recent_highs[-1] < 0.005 and close[-1] < recent_highs[-1]:
        neckline_price = round(float(min(recent_lows[-10:])), 4)
        patterns_found.append(("Double Top", neckline_price, "Neckline Price"))
        
    # Double Bottom (Neckline = Maximum High between bottoms)
    if abs(recent_lows[-1] - recent_lows[-10]) / recent_lows[-1] < 0.005 and close[-1] > recent_lows[-1]:
        neckline_price = round(float(max(recent_highs[-10:])), 4)
        patterns_found.append(("Double Bottom", neckline_price, "Neckline Price"))

    # Ascending Triangle (Flat Resistance Level)
    if abs(max(recent_highs) - recent_highs[-1]) / recent_highs[-1] < 0.008 and recent_lows[-1] > recent_lows[-10]:
        res_price = round(float(max(recent_highs)), 4)
        patterns_found.append(("Ascending Triangle", res_price, "Resistance Price"))

    # Descending Triangle (Flat Support Level)
    if abs(min(recent_lows) - recent_lows[-1]) / recent_lows[-1] < 0.008 and recent_highs[-1] < recent_highs[-10]:
        sup_price = round(float(min(recent_lows)), 4)
        patterns_found.append(("Descending Triangle", sup_price, "Support Price"))

    # Symmetrical Triangle
    if recent_highs[-1] < recent_highs[-10] and recent_lows[-1] > recent_lows[-10]:
        key_price = round(float((recent_highs[-1] + recent_lows[-1]) / 2), 4)
        patterns_found.append(("Symmetrical Triangle", key_price, "Key Range Level"))

    # Head & Shoulders (Neckline = Support Level of Shoulders)
    if len(high) >= 30:
        if high[-15] > high[-25] and high[-15] > high[-5]:
            neckline_price = round(float(min(low[-25:-5])), 4)
            patterns_found.append(("Head & Shoulders", neckline_price, "Neckline Price"))
            
        if low[-15] < low[-25] and low[-15] < low[-5]:
            neckline_price = round(float(max(high[-25:-5])), 4)
            patterns_found.append(("Inverse Head & Shoulders", neckline_price, "Neckline Price"))

    # Wedge & Channel Patterns
    if recent_highs[-1] > recent_highs[-5] and recent_lows[-1] > recent_lows[-5] and (recent_highs[-1] - recent_lows[-1]) < (recent_highs[-10] - recent_lows[-10]):
        patterns_found.append(("Rising Wedge", round(float(recent_lows[-1]), 4), "Support Price"))

    if recent_highs[-1] < recent_highs[-5] and recent_lows[-1] < recent_lows[-5] and (recent_highs[-1] - recent_lows[-1]) < (recent_highs[-10] - recent_lows[-10]):
        patterns_found.append(("Falling Wedge", round(float(recent_highs[-1]), 4), "Resistance Price"))

    if recent_highs[-1] > recent_highs[-10] and recent_lows[-1] > recent_lows[-10]:
        patterns_found.append(("Channel Up", round(float(recent_lows[-1]), 4), "Support Level"))

    if recent_highs[-1] < recent_highs[-10] and recent_lows[-1] < recent_lows[-10]:
        patterns_found.append(("Channel Down", round(float(recent_highs[-1]), 4), "Resistance Level"))

    return patterns_found

# --- SCAN BUTTON ---
if st.button("🚀 Start Pattern Scan", use_container_width=True):
    if not selected_tf:
        st.error("Baraye mehrbani kam az kam ek Timeframe select karein!")
    else:
        symbols = get_okx_pairs(coin_limit)
        st.info(f"🔍 Top {len(symbols)} coins scan ho rahe hain selected timeframes par...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_steps = len(symbols)
        found_coins = set()
        
        for idx, symbol in enumerate(symbols):
            status_text.text(f"Scanning ({idx+1}/{total_steps}): {symbol}")
            progress_bar.progress((idx + 1) / total_steps)
            
            if symbol in found_coins:
                continue

            for tf in selected_tf:
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=100)
                    df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
                    current_price = round(float(df['close'].iloc[-1]), 4)
                    
                    patterns = detect_chart_patterns(df)
                    if patterns and symbol not in found_coins:
                        p_name, level_price, level_label = patterns[0]
                        info = PATTERN_INFO.get(p_name, {"signal": "N/A", "detail": ""})
                        
                        clean_symbol = symbol.replace("/", "")
                        tv_url = f"https://www.tradingview.com/chart/?symbol=OKX%3A{clean_symbol}"
                        
                        # Mobile Card Display with Neckline Price
                        with st.container():
                            st.markdown(f"""
                            ---
                            ### 📌 **{symbol}**
                            * **Current Price:** `${current_price}`
                            * **Timeframe:** `{tf}`
                            * **Pattern:** **{p_name}**
                            * **🎯 {level_label}:** `${level_price}`
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
