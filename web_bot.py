import streamlit as st
import yfinance as yf
import pandas as pd
from anthropic import Anthropic

st.set_page_config(page_title="AI Financial Market Bot", layout="centered")

st.title("AI Financial Market Analysis Bot")
st.caption("Stocks / ETFs analysis using Claude AI")

ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
MODEL = st.secrets.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

symbols = {
    "Apple": "AAPL",
    "Tesla": "TSLA",
    "Nvidia": "NVDA",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Meta": "META",
    "Google": "GOOGL",
    "S&P 500 ETF": "SPY",
    "Nasdaq ETF": "QQQ",
    "Dow Jones ETF": "DIA",
    "Gold ETF": "GLD",
    "Silver ETF": "SLV",
    "Oil ETF": "USO",
}

selected_name = st.selectbox("Choose Market Symbol", list(symbols.keys()))
symbol = symbols[selected_name]

period = st.selectbox("Analysis Period", ["5d", "1mo", "3mo", "6mo"], index=1)
interval = st.selectbox("Candle Interval", ["15m", "30m", "1h", "1d"], index=2)

strategy = st.selectbox(
    "Strategy Type",
    ["Intraday", "Swing Trade", "Short Term", "Long Term"],
    index=1
)
    st.write("DEBUG")
    st.write(type(latest))
    st.write(latest)
    st.write(type(latest["Close"]))
    st.write(latest["Close"])
    st.stop()
    def calculate_rsi(data, period=14):
    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_market_data(symbol, period, interval):
    df = yf.download(
        symbol,
        period=period,
        interval=interval,
        progress=False,
        auto_adjust=True
    )

    if df.empty:
        return None

    df = df.dropna()

    df["SMA_20"] = df["Close"].rolling(20).mean()
    df["SMA_50"] = df["Close"].rolling(50).mean()
    df["RSI"] = calculate_rsi(df)
    df["High_20"] = df["High"].rolling(20).max()
    df["Low_20"] = df["Low"].rolling(20).min()

    return df.dropna()

def ask_claude(symbol, selected_name, strategy, latest, recent_data):
    prompt = f"""
You are a financial market analysis assistant.

Analyze this market using only the data provided.

Symbol: {symbol}
Name: {selected_name}
Strategy: {strategy}

Latest Market Data:
Close Price: {latest['Close']}
RSI: {latest['RSI']}
SMA 20: {latest['SMA_20']}
SMA 50: {latest['SMA_50']}
20-period High: {latest['High_20']}
20-period Low: {latest['Low_20']}

Recent candles:
{recent_data}

Return ONLY this exact format:

Market Direction: Bullish / Bearish / Neutral
Best Entry Price: number or range
Take Profit Price: number
Stop Loss Price: number
AI Confidence: percentage
Brief Reason: one short sentence

Important:
- Do not give long explanation.
- Do not say "not financial advice".
- Be practical.
- If data is weak or unclear, say Neutral.
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        temperature=0.2,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text

if st.button("Analyze Market"):
    with st.spinner("Fetching market data and analyzing..."):
        df = get_market_data(symbol, period, interval)

        if df is None or df.empty:
            st.error("No market data found. Try another symbol, period, or interval.")
            st.stop()

        latest = df.iloc[-1]

        recent_data = df.tail(15)[
            ["Open", "High", "Low", "Close", "SMA_20", "SMA_50", "RSI"]
        ].round(2).to_string()

        result = ask_claude(symbol, selected_name, strategy, latest, recent_data)

        st.subheader(f"{selected_name} / {symbol}")
        current_price = float(latest["Close"])
        st.metric("Current Price", f"${current_price:.2f}")
        st.metric("RSI", f"{latest['RSI']:.2f}")

        st.divider()
        st.text(result)

        st.caption("Use this for analysis only. Always confirm with your own risk management.")
