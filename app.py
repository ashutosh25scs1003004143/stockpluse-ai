import os
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import google.generativeai as genai

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM CSS INJECTION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="StockPulse AI - Indian Stock Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with proper Streamlit string wrapping to prevent SyntaxError
st.markdown("""
<style>
    /* Dark Theme Custom Colors */
    .stApp {
        background-color: #0B0F19;
        color: #F8FAFC;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0B0F19;
    }
    ::-webkit-scrollbar-thumb {
        background: #263244;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #3B82F6;
    }

    /* Metric Cards Custom Styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. GEMINI API SETUP & SECRETS MANAGEMENT
# -----------------------------------------------------------------------------
# Safely fetch API Key from st.secrets or environment variable
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# -----------------------------------------------------------------------------
# 3. MOCK DATASETS (INDIAN EQUITIES & INDICES)
# -----------------------------------------------------------------------------
MOCK_STOCKS = [
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd.", "exchange": "NSE", "sector": "Energy", "price": 2945.50, "change": 34.20, "changePercent": 1.17, "pe": 28.4, "roe": "9.8%", "high52w": 3024.90, "low52w": 2220.30, "rsi": 58.4},
    {"symbol": "TCS", "name": "Tata Consultancy Services", "exchange": "NSE", "sector": "IT", "price": 4120.10, "change": -28.40, "changePercent": -0.68, "pe": 32.1, "roe": "48.2%", "high52w": 4254.75, "low52w": 3313.00, "rsi": 44.2},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Limited", "exchange": "NSE", "sector": "Banking", "price": 1682.30, "change": 18.90, "changePercent": 1.14, "pe": 19.4, "roe": "16.5%", "high52w": 1757.50, "low52w": 1363.55, "rsi": 62.1},
    {"symbol": "INFY", "name": "Infosys Limited", "exchange": "NSE", "sector": "IT", "price": 1785.40, "change": 42.10, "changePercent": 2.41, "pe": 29.8, "roe": "31.8%", "high52w": 1847.00, "low52w": 1355.00, "rsi": 68.9},
    {"symbol": "TATAMOTORS", "name": "Tata Motors Limited", "exchange": "NSE", "sector": "Automobile", "price": 980.60, "change": -34.50, "changePercent": -3.40, "pe": 10.4, "roe": "32.4%", "high52w": 1179.00, "low52w": 615.00, "rsi": 38.2},
    {"symbol": "ITC", "name": "ITC Limited", "exchange": "BSE", "sector": "FMCG", "price": 492.20, "change": 6.80, "changePercent": 1.40, "pe": 28.9, "roe": "29.2%", "high52w": 510.60, "low52w": 399.30, "rsi": 55.4}
]

# Helper to generate candlestick dummy historical data
def get_historical_df(base_price):
    dates = pd.date_range(end=pd.Timestamp.today(), periods=30, freq='B')
    np.random.seed(42)
    returns = np.random.normal(0, 0.015, size=len(dates))
    price_series = base_price * (1 + returns).cumprod()
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': price_series * (1 - np.random.uniform(0, 0.005, size=len(dates))),
        'High': price_series * (1 + np.random.uniform(0.001, 0.01, size=len(dates))),
        'Low': price_series * (1 - np.random.uniform(0.001, 0.01, size=len(dates))),
        'Close': price_series,
        'Volume': np.random.randint(100000, 5000000, size=len(dates))
    })
    df['MA20'] = df['Close'].rolling(window=5, min_periods=1).mean()
    return df

# -----------------------------------------------------------------------------
# 4. SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if 'virtual_balance' not in st.session_state:
    st.session_state.virtual_balance = 100000.00
if 'paper_trades' not in st.session_state:
    st.session_state.paper_trades = []
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ['RELIANCE', 'TCS', 'HDFCBANK']

# -----------------------------------------------------------------------------
# 5. SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("📈 StockPulse AI")
    st.caption("Understand Markets. Invest Smarter.")
    st.divider()

    menu = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Markets & Explorer",
            "AI Stock Analyst",
            "Virtual Trading",
            "Watchlist & Settings"
        ],
        icon="📊"
    )
    
    st.divider()
    # Market Status Indicator
    st.sidebar.success("● Market Open (NSE/BSE Live)")

# -----------------------------------------------------------------------------
# MENU 1: DASHBOARD
# -----------------------------------------------------------------------------
if menu == "Dashboard":
    st.header("Indian Benchmark Indices")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("NIFTY 50", "24,586.70", "+164.25 (0.67%)")
    col2.metric("SENSEX", "80,716.55", "+522.30 (0.65%)")
    col3.metric("BANK NIFTY", "52,280.40", "+485.10 (0.94%)")
    col4.metric("NIFTY IT", "41,850.15", "-120.40 (-0.29%)", delta_color="inverse")
    
    st.divider()
    st.subheader("Top Gainers & Losers (NSE LargeCap)")
    
    df_stocks = pd.DataFrame(MOCK_STOCKS)
    c1, c2 = st.columns(2)
    
    with c1:
        st.write("🟢 **Top Gainers**")
        gainers = df_stocks.sort_values(by="changePercent", ascending=False).head(3)
        st.dataframe(gainers[['symbol', 'name', 'price', 'changePercent']], use_container_width=True, hide_index=True)
        
    with c2:
        st.write("🔴 **Top Losers**")
        losers = df_stocks.sort_values(by="changePercent", ascending=True).head(3)
        st.dataframe(losers[['symbol', 'name', 'price', 'changePercent']], use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# MENU 2: MARKETS & EXPLORER
# -----------------------------------------------------------------------------
elif menu == "Markets & Explorer":
    st.header("Stock Explorer & Interactive Charting")
    
    selected_sym = st.selectbox("Select Stock Ticker", [s['symbol'] for s in MOCK_STOCKS])
    stock = next(s for s in MOCK_STOCKS if s['symbol'] == selected_sym)
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Current Price", f"₹{stock['price']}", f"{stock['changePercent']}%")
    col_b.metric("P/E Ratio", stock['pe'])
    col_c.metric("52-Wk Range", f"₹{stock['low52w']} - ₹{stock['high52w']}")
    
    # Render Candlestick Chart via Plotly
    df_chart = get_historical_df(stock['price'])
    fig = go.Figure(data=[go.Candlestick(
        x=df_chart['Date'],
        open=df_chart['Open'],
        high=df_chart['High'],
        low=df_chart['Low'],
        close=df_chart['Close'],
        name="OHLC"
    )])
    fig.add_trace(go.Scatter(x=df_chart['Date'], y=df_chart['MA20'], mode='lines', name='MA (20)', line=dict(color='#3B82F6')))
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=20, r=20, t=30, b=20))
    
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# MENU 3: AI STOCK ANALYST (GEMINI API)
# -----------------------------------------------------------------------------
elif menu == "AI Stock Analyst":
    st.header("🤖 AI Stock Analyst (Powered by Gemini)")
    st.caption("Detailed fundamental analysis and risk evaluation powered by Gemini AI.")
    
    target_sym = st.selectbox("Select Company for Analysis", [s['symbol'] for s in MOCK_STOCKS], key="ai_sym")
    stock_info = next(s for s in MOCK_STOCKS if s['symbol'] == target_sym)
    
    if st.button("Generate AI Intelligence Report", type="primary"):
        if not GEMINI_KEY:
            st.warning("⚠️ Google Gemini API Key is missing. Please configure it in `.streamlit/secrets.toml` or Settings tab.")
        else:
            with st.spinner(f"Analyzing {stock_info['name']} using Google Gemini..."):
                try:
                    # Initialize Gemini Model
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = f"""
                    Act as a senior Indian stock analyst. Produce a structured research report for {stock_info['name']} ({stock_info['symbol']}).
                    Verified Data: Price=₹{stock_info['price']}, PE={stock_info['pe']}, ROE={stock_info['roe']}, RSI={stock_info['rsi']}.
                    Include these sections:
                    1. Business Model Overview
                    2. Fundamental & Valuation Summary
                    3. Technical Trend & RSI Interpretation
                    4. Potential Risks
                    5. Bullish vs Bearish Outlook
                    """
                    response = model.generate_content(prompt)
                    
                    st.success("Analysis Complete!")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Error calling Gemini API: {str(e)}")

# -----------------------------------------------------------------------------
# MENU 4: VIRTUAL TRADING
# -----------------------------------------------------------------------------
elif menu == "Virtual Trading":
    st.header("📝 Virtual Paper Trading Simulator")
    
    c_bal, c_ord = st.columns(2)
    c_bal.metric("Virtual Cash Balance", f"₹{st.session_state.virtual_balance:,.2f}")
    c_ord.metric("Executed Trades", len(st.session_state.paper_trades))
    
    st.divider()
    t_sym = st.selectbox("Select Asset to Trade", [s['symbol'] for s in MOCK_STOCKS], key="vt_sym")
    t_stock = next(s for s in MOCK_STOCKS if s['symbol'] == t_sym)
    
    qty = st.number_input("Quantity", min_value=1, value=10)
    total_val = qty * t_stock['price']
    st.info(f"Estimated Order Value: **₹{total_val:,.2f}**")
    
    btn_buy, btn_sell = st.columns(2)
    if btn_buy.button("BUY (Paper)", type="primary", use_container_width=True):
        if total_val > st.session_state.virtual_balance:
            st.error("Insufficient Virtual Balance!")
        else:
            st.session_state.virtual_balance -= total_val
            st.session_state.paper_trades.append({
                "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "Symbol": t_sym,
                "Type": "BUY",
                "Qty": qty,
                "Price": t_stock['price'],
                "Total": total_val
            })
            st.success(f"Executed BUY order for {qty} shares of {t_sym}!")
            st.rerun()

# -----------------------------------------------------------------------------
# MENU 5: WATCHLIST & SETTINGS
# -----------------------------------------------------------------------------
elif menu == "Watchlist & Settings":
    st.header("⚙️ App Settings & API Key Verification")
    
    st.subheader("Gemini API Status")
    if GEMINI_KEY:
        st.success("✅ Google Gemini API Key detected and loaded securely.")
    else:
        st.error("❌ Google Gemini API Key not found!")
        
    st.markdown("""
    ### How to configure API key:
    1. Create `.streamlit/secrets.toml` in project root.
    2. Add: `GEMINI_API_KEY = "YOUR_KEY_HERE"`
    """)
