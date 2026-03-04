import streamlit as st
import traceback

st.set_page_config(page_title="Streamlit Cloud Debugger", page_icon="🐛")
st.title("Streamlit Cloud Crash Debugger")
st.warning("Click these buttons strictly one-by-one to see which component crashes the deployed server!")

if st.button("1. Test Base Streamlit Dataframe Render"):
    try:
        import pandas as pd
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        st.dataframe(df)
        st.success("Pandas & Streamlit Base: OK")
    except Exception as e:
        st.error(f"Error: {e}")
        st.code(traceback.format_exc())

if st.button("2. Test Loading Local CSV"):
    try:
        import pandas as pd
        st.write("Reading tickers.csv...")
        df = pd.read_csv("tickers.csv")
        st.success(f"Loaded CSV successfully! {len(df)} tickers found.")
        st.write(df.head())
    except Exception as e:
        st.error(f"CSV Loading Error: {e}")
        st.code(traceback.format_exc())

if st.button("3. Test Importing yfinance"):
    try:
        st.write("Importing yfinance...")
        import yfinance as yf
        st.success(f"yfinance imported successfully: {yf.__version__}")
    except Exception as e:
        st.error(f"yfinance Import Error: {e}")
        st.code(traceback.format_exc())

if st.button("4. Test yfinance Data Fetching"):
    try:
        st.write("Importing and fetching aapl...")
        import yfinance as yf
        data = yf.Ticker("AAPL").history(period="1d")
        st.success("Fetched 1D of AAPL successfully.")
        st.dataframe(data)
    except Exception as e:
        st.error(f"yfinance Fetch Error: {e}")
        st.code(traceback.format_exc())

if st.button("5. Test Importing vaderSentiment"):
    try:
        st.write("Importing and initializing vaderSentiment...")
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        st.success("vaderSentiment imported and initialized completely.")
    except Exception as e:
        st.error(f"vaderSentiment Error: {e}")
        st.code(traceback.format_exc())
