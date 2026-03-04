import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize Sentiment Analyzer
analyzer = SentimentIntensityAnalyzer()

# Set page config for a more dynamic look
st.set_page_config(page_title="Stock View", page_icon="📈", layout="wide")

# Custom CSS for a modern look
st.markdown("""
<style>
    /* Dark theme overrides and generic modern UI touches */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .stTextInput>div>div>input {
        background-color: #161b22;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
    }
    .stDateInput>div>div>input {
        background-color: #161b22;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
    }
    h1, h2, h3 {
        color: #58a6ff !important;
        font-family: 'Inter', sans-serif;
    }
    .st-bb {
        background-color: transparent !important;
    }
    /* Fix transparent dropdown background */
    div[role="listbox"] ul {
        background-color: #161b22 !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #161b22 !important;
    }
    /* Simple glassmorphism card for the main content area */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("Dynamic Stock Viewer 📈")
st.markdown("A simple, beautiful way to view historical market data using `yfinance`.")

try:
    # Sidebar for inputs
    with st.sidebar:
        st.header("Parameters")
        
        # Initialize ticker history in session state
        if "ticker_history" not in st.session_state:
            st.session_state["ticker_history"] = ["AAPL"]
            
        if "current_ticker" not in st.session_state:
            st.session_state["current_ticker"] = "AAPL"
            
        # Autocomplete ticker list setup
        @st.cache_data(ttl=timedelta(days=7))
        def fetch_tickers():
            try:
                # Read from bundled static CSV to prevent cloud firewalls from blocking FTP startup requests
                df = pd.read_csv("tickers.csv")
                tickers = df['Symbol'].dropna().astype(str).tolist()
                return sorted(list(set(tickers)))
            except Exception:
                # Fallback tiny list if fetching fails
                return ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "META", "NVDA", "BRK-B", "SPY", "SOXL"]

        available_tickers = fetch_tickers()
        
        # Ensure current_ticker is always in the available list so the selectbox doesn't crash on load
        if st.session_state["current_ticker"] not in available_tickers:
            available_tickers.insert(0, st.session_state["current_ticker"])

        def add_to_history():
            new_ticker = st.session_state["ticker_input_widget"].upper().strip()
            if new_ticker:
                st.session_state["current_ticker"] = new_ticker
                # Add to history if not exists, and keep it deduplicated and limited to 5
                hist = st.session_state["ticker_history"]
                if new_ticker in hist:
                    hist.remove(new_ticker)
                hist.insert(0, new_ticker)
                st.session_state["ticker_history"] = hist[:5]
                
        def set_ticker(t):
            st.session_state["current_ticker"] = t
            # Also bump to top of history
            hist = st.session_state["ticker_history"]
            if t in hist:
                hist.remove(t)
            hist.insert(0, t)
            st.session_state["ticker_history"] = hist[:5]

        # Use a selectbox for predictive search typing
        # index maps to the current_ticker's dynamic position in the list
        idx = available_tickers.index(st.session_state["current_ticker"])
        st.selectbox("Search Ticker Symbol", 
                     options=available_tickers, 
                     index=idx, 
                     key="ticker_input_widget", 
                     on_change=add_to_history)
                     
        ticker = st.session_state["current_ticker"]
        
        compare_tickers = st.multiselect("Compare With", 
                                         options=available_tickers, 
                                         default=[],
                                         help="Select additional tickers to compare percentage returns.")
        
        # Display Ticker History
        hist = st.session_state["ticker_history"]
        if len(hist) > 1:
            st.markdown("**Recent History**")
            pcols = st.columns(len(hist) if len(hist) < 5 else 5)
            for i, t in enumerate(hist):
                if i < 5:
                    with pcols[i]:
                        if st.button(t, key=f"hist_{t}"):
                            set_ticker(t)
                            st.rerun()
        
        st.markdown("---")
        
        # Session state for managing dates
        if "end_date" not in st.session_state:
            st.session_state["end_date"] = datetime.today().date()
        if "start_date" not in st.session_state:
            st.session_state["start_date"] = st.session_state["end_date"] - timedelta(days=365)
            
        def set_date_range(days):
            st.session_state["end_date"] = datetime.today().date()
            st.session_state["start_date"] = st.session_state["end_date"] - timedelta(days=days)

        # Quick date range buttons MUST be before the inputs they modify
        st.markdown("**Quick Ranges**")
        bcol1, bcol2, bcol3, bcol4, bcol5 = st.columns(5)
        with bcol1:
            if st.button("1D"): set_date_range(1)
        with bcol2:
            if st.button("1W"): set_date_range(7)
        with bcol3:
            if st.button("1M"): set_date_range(30)
        with bcol4:
            if st.button("1Y"): set_date_range(365)
        with bcol5:
            if st.button("5Y"): set_date_range(365 * 5)

        col1, col2 = st.columns(2)
        with col1:
            st.date_input("Start Date", key="start_date")
        with col2:
            st.date_input("End Date", key="end_date")
            
        # Read finalized dates back out for use
        start_date_input = st.session_state["start_date"]
        end_date_input = st.session_state["end_date"]

    # Main content area

    # Streamlit-native caching for history to prevent rate limiting
    @st.cache_data(ttl=timedelta(minutes=15))
    def get_cached_history(ticker_sym, start, end, interval="1d"):
        return yf.Ticker(ticker_sym).history(start=start, end=end, interval=interval)
        
    @st.cache_data(ttl=timedelta(minutes=15))
    def get_cached_info(ticker_sym):
        return yf.Ticker(ticker_sym).info
        
    @st.cache_data(ttl=timedelta(minutes=15))
    def get_cached_news(ticker_sym):
        return yf.Ticker(ticker_sym).news

    if ticker:
        # Determine optimal interval for the selected date range
        date_diff = (end_date_input - start_date_input).days
        days_from_today = (datetime.today().date() - start_date_input).days

        interval = "1d"
        # yfinance limits intraday data: <60d for 5m/15m, <730d for 1h
        if date_diff <= 3 and days_from_today < 60:
            interval = "5m"
        elif date_diff <= 14 and days_from_today < 60:
            interval = "15m"
        elif date_diff <= 60 and days_from_today < 730:
            interval = "1h"

        try:
            with st.spinner(f"Fetching data for {ticker}..."):
                # Get historical data via Streamlit Cache
                hist_data = get_cached_history(ticker, start_date_input, end_date_input, interval)
                
                if not hist_data.empty:
                    # Get company info if available (Cached)
                    info = get_cached_info(ticker)
                    company_name = info.get('longName', ticker)
                    current_price = info.get('currentPrice', 'N/A')
                    currency = info.get('currency', 'USD')
                    
                    # Display Header
                    st.subheader(f"{company_name} ({ticker})")
                    
                    if current_price != 'N/A':
                        st.metric(label="Current Price", value=f"{current_price} {currency}")
                    
                    # Display Chart
                    if not compare_tickers:
                        st.markdown(f"### Closing Price History ({interval.upper()} Interval)")
                        # Streamlit's native line chart is clean and responsive
                        st.line_chart(hist_data['Close'], use_container_width=True)
                    else:
                        st.markdown(f"### Comparison Price History (% Change, {interval.upper()} Interval)")
                        # Build a combined dataframe normalized to standard percentage return
                        chart_df = pd.DataFrame()
                        chart_df[ticker] = (hist_data['Close'] / hist_data['Close'].iloc[0] - 1) * 100
                        
                        for comp_tick in compare_tickers:
                            try:
                                # Use cached history pull for comparisons too
                                c_data = get_cached_history(comp_tick, start_date_input, end_date_input, interval)
                                if not c_data.empty:
                                    chart_df[comp_tick] = (c_data['Close'] / c_data['Close'].iloc[0] - 1) * 100
                            except Exception:
                                st.warning(f"Could not fetch comparison data for {comp_tick}")
                        
                        st.line_chart(chart_df, use_container_width=True)
                    
                    # --- PREDICTION MODEL ---
                    st.markdown("### 🔮 Near Future Prediction Model")
                    st.markdown("*Note: This is a basic algorithmic forecast combining Technical Analysis and News Sentiment. It is NOT financial advice.*")
                    
                    # 1. Technical Indicator: Moving Average Crossover (20-day vs 50-day)
                    try:
                        # Get last 90 days to ensure we have enough data for 50-day SMA securely from cache
                        pred_data = get_cached_history(ticker, datetime.today().date() - timedelta(days=90), datetime.today().date())
                        if len(pred_data) >= 50:
                            sma_20 = pred_data['Close'].rolling(window=20).mean().iloc[-1]
                            sma_50 = pred_data['Close'].rolling(window=50).mean().iloc[-1]
                            current_close = pred_data['Close'].iloc[-1]
                            
                            tech_signal = 0 # 1 for Bullish, -1 for Bearish, 0 for Neutral
                            tech_text = "⚪ Neutral"
                            
                            if sma_20 > sma_50:
                                tech_signal = 1
                                tech_text = "🟢 Bullish (Short-term trend > Long-term trend)"
                            elif sma_20 < sma_50:
                                tech_signal = -1
                                tech_text = "🔴 Bearish (Short-term trend < Long-term trend)"
                        else:
                            tech_signal = 0
                            tech_text = "⚪ Neutral (Not enough data for 50-day SMA)"
                    except Exception:
                        tech_signal = 0
                        tech_text = "⚪ Neutral (Error calculating MAs)"

                    # 2. News Sentiment Aggregation
                    agg_sentiment = 0.0
                    news_count = 0
                    try:
                        news_items = get_cached_news(ticker)
                        if news_items:
                            for item in news_items[:10]:
                                article = item.get('content', item)
                                title = article.get('title', '')
                                if title:
                                    agg_sentiment += analyzer.polarity_scores(title)['compound']
                                    news_count += 1
                    except Exception:
                        pass
                    
                    avg_sentiment = agg_sentiment / news_count if news_count > 0 else 0
                    sent_signal = 0
                    sent_text = "⚪ Neutral"
                    
                    if avg_sentiment >= 0.15:
                        sent_signal = 1
                        sent_text = f"🟢 Positive (Avg Score: {avg_sentiment:.2f})"
                    elif avg_sentiment <= -0.15:
                        sent_signal = -1
                        sent_text = f"🔴 Negative (Avg Score: {avg_sentiment:.2f})"
                    else:
                        sent_text = f"⚪ Neutral (Avg Score: {avg_sentiment:.2f})"

                    # 3. Final Combined Prediction
                    total_signal = tech_signal + sent_signal
                    if total_signal >= 1:
                        final_pred = "📈 LIKELY UPWARD TREND"
                        pred_color = "#3fb950"
                    elif total_signal <= -1:
                        final_pred = "📉 LIKELY DOWNWARD TREND"
                        pred_color = "#f85149"
                    else:
                        final_pred = "➖ LIKELY SIDEWAYS / MIXED"
                        pred_color = "#d2a8ff"

                    # Display Model Results
                    colA, colB, colC = st.columns(3)
                    with colA:
                        st.metric("Technical Signal (SMA 20/50)", tech_text.split(' ')[0])
                        st.caption(tech_text)
                    with colB:
                        st.metric("Sentiment Signal (News)", sent_text.split(' ')[0])
                        st.caption(sent_text)
                    with colC:
                        st.markdown(f"<div style='background-color: #161b22; padding: 1rem; border: 1px solid #30363d; border-radius: 6px; text-align: center;'>"
                                    f"<span style='font-size: 0.9rem; color: #8b949e;'>Combined Forecast</span><br>"
                                    f"<strong style='font-size: 1.2rem; color: {pred_color};'>{final_pred}</strong></div>", 
                                    unsafe_allow_html=True)
                    
                    st.markdown("---")

                    # Expandable raw data section
                    with st.expander("View Raw Data"):
                        st.dataframe(
                            hist_data.style.format("{:.2f}"), 
                            use_container_width=True
                        )
                    
                    # --- RECENT NEWS SECTION ---
                    try:
                        news = get_cached_news(ticker)
                        if news:
                            st.markdown("---")
                            st.markdown("### 📰 Recent News")
                            for item in news[:10]:
                                # yfinance news sometimes uses a nested 'content' dict
                                article = item.get('content', item)
                                title = article.get('title', 'No Title')
                                
                                provider = article.get('provider', {})
                                publisher = provider.get('displayName', 'Unknown Publisher')
                                
                                # Safely extract the link
                                click_through = article.get('clickThroughUrl')
                                canonical = article.get('canonicalUrl')
                                
                                link = '#'
                                if click_through and isinstance(click_through, dict):
                                    link = click_through.get('url', '#')
                                elif canonical and isinstance(canonical, dict):
                                    link = canonical.get('url', '#')
                                    
                                # Extract publish time
                                pub_date = article.get('pubDate', '')
                                time_str = ""
                                if pub_date:
                                    try:
                                        # Example format: 2026-03-02T21:12:24Z
                                        dt = datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%SZ")
                                        time_str = f" • *{dt.strftime('%b %d, %Y %I:%M %p')}*"
                                    except Exception:
                                        time_str = f" • *{pub_date}*"
                                        
                                # Sentiment Analysis prediction on Title
                                scores = analyzer.polarity_scores(title)
                                compound = scores['compound']
                                
                                # Determine prediction Good/Bad/Neutral
                                if compound >= 0.05:
                                    sentiment = "🟢 Good News"
                                elif compound <= -0.05:
                                    sentiment = "🔴 Bad News"
                                else:
                                    sentiment = "⚪ Neutral"
                                    
                                st.markdown(f"**[{title}]({link})**  \n*{publisher}*{time_str}  \n**Prediction:** {sentiment} *(Score: {compound:.2f})*")
                    except Exception as e:
                        pass
                else:
                    st.warning(f"No data found for {ticker} in the selected date range. Is it a valid symbol?")
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            st.info("Check if the ticker symbol is correct or if there are network issues.")
    else:
        st.info("Please enter a ticker symbol in the sidebar.")
except Exception as e:
    import traceback
    st.error(f"FATAL APP ERROR: {e}")
    st.code(traceback.format_exc())
