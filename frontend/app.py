import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import sys

# Configure page
st.set_page_config(
    page_title="NEPSE Pump & Dump Detector",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API URL
API_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
    <style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("📈 NEPSE Pump & Dump Detection System")
st.markdown("*Detecting suspicious trading patterns in Nepal Stock Exchange*")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Dashboard", "🔍 Stock Analysis", "⚠️ Alerts", "📊 Suspicious Stocks", "ℹ️ About"])

# Helper function to make API calls
def api_call(endpoint, method="GET", data=None):
    try:
        url = f"{API_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Make sure the backend server is running on port 8000!")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Page: Dashboard
if page == "🏠 Dashboard":
    st.header("Market Overview")
    
    # Get market data
    market_data = api_call("/api/market-overview")
    
    if market_data and "error" not in market_data:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="NEPSE Index",
                value=f"{market_data.get('index_value', 0):.2f}",
                delta=f"{market_data.get('change_percent', 0):.2f}%"
            )
        
        with col2:
            st.metric(
                label="Change",
                value=f"{market_data.get('change', 0):.2f}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Date",
                value=market_data.get('date', 'N/A'),
                delta=None
            )
        
        with col4:
            st.metric(
                label="Turnover",
                value=f"Rs. {market_data.get('volume', 0):,.0f}",
                delta=None
            )
    else:
        st.warning("Unable to fetch market data. Please check your internet connection.")
    
    st.divider()
    
    # Top movers section
    st.subheader("📊 Today's Trading Activity")
    
    stocks_data = api_call("/api/stocks/today")
    
    if stocks_data and stocks_data.get('stocks'):
        stocks = stocks_data['stocks']
        
        # Create DataFrame
        df = pd.DataFrame(stocks)
        
        # Select relevant columns
        if not df.empty:
            display_columns = ['symbol', 'lastTradedPrice', 'percentageChange', 'totalTradeQuantity', 'highPrice', 'lowPrice']
            available_columns = [col for col in display_columns if col in df.columns]
            
            if available_columns:
                df_display = df[available_columns].head(20)
                
                # Rename columns for better display
                column_mapping = {
                    'symbol': 'Symbol',
                    'lastTradedPrice': 'LTP',
                    'percentageChange': 'Change %',
                    'totalTradeQuantity': 'Volume',
                    'highPrice': 'High',
                    'lowPrice': 'Low'
                }
                df_display = df_display.rename(columns=column_mapping)
                
                # Format numbers
                if 'Change %' in df_display.columns:
                    df_display['Change %'] = df_display['Change %'].round(2)
                
                # Color code based on change
                def color_change(val):
                    if isinstance(val, (int, float)):
                        color = 'green' if val > 0 else 'red' if val < 0 else 'black'
                        return f'color: {color}'
                    return ''
                
                if 'Change %' in df_display.columns:
                    styled_df = df_display.style.applymap(color_change, subset=['Change %'])
                    st.dataframe(styled_df, use_container_width=True, height=400)
                else:
                    st.dataframe(df_display, use_container_width=True, height=400)
            else:
                st.info("No stock data available to display")
        else:
            st.info("No stock data available")
    else:
        st.warning("Unable to fetch stock data")

# Page: Stock Analysis
elif page == "🔍 Stock Analysis":
    st.header("Individual Stock Analysis")
    
    # Input for stock symbol
    col1, col2 = st.columns([3, 1])
    
    with col1:
        stock_symbol = st.text_input("Enter Stock Symbol (e.g., NABIL, NICA, ADBL)", "").upper()
    
    with col2:
        st.write("")
        st.write("")
        analyze_button = st.button("🔍 Analyze", type="primary")
    
    if analyze_button and stock_symbol:
        with st.spinner(f"Analyzing {stock_symbol}..."):
            analysis = api_call(f"/api/analyze/{stock_symbol}")
            
            if analysis:
                st.success(f"Analysis complete for {stock_symbol}")
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Current Price", f"Rs. {analysis['current_price']:.2f}")
                
                with col2:
                    st.metric("Price Change", f"{analysis['price_change_percent']:.2f}%")
                
                with col3:
                    st.metric("Volume", f"{analysis['volume']:,.0f}")
                
                with col4:
                    # Risk score with color
                    risk_color = "🔴" if analysis['risk_level'] == "High" else "🟡" if analysis['risk_level'] == "Medium" else "🟢"
                    st.metric("Risk Level", f"{risk_color} {analysis['risk_level']}")
                
                # Risk score progress bar
                st.subheader("Risk Score")
                st.progress(analysis['risk_score'] / 100)
                st.write(f"**Score: {analysis['risk_score']}/100**")
                
                # Signals detected
                st.subheader("🚨 Detection Signals")
                
                if analysis['signals']:
                    for signal in analysis['signals']:
                        if "No suspicious" in signal:
                            st.success(f"✅ {signal}")
                        elif "High" in signal or "Unusual" in signal:
                            st.error(f"⚠️ {signal}")
                        else:
                            st.warning(f"⚡ {signal}")
                else:
                    st.info("No signals detected")
                
                # Recommendation
                st.subheader("💡 Recommendation")
                
                if analysis['risk_level'] == "High":
                    st.error("⚠️ **HIGH RISK**: This stock shows strong pump-and-dump indicators. Exercise extreme caution!")
                elif analysis['risk_level'] == "Medium":
                    st.warning("⚡ **MEDIUM RISK**: This stock shows some suspicious patterns. Monitor closely before trading.")
                else:
                    st.success("✅ **LOW RISK**: This stock appears to be trading normally.")
    
    elif analyze_button:
        st.warning("Please enter a stock symbol")

# Page: Alerts
elif page == "⚠️ Alerts":
    st.header("Alert Management")
    
    # Get existing alerts
    alerts = api_call("/api/alerts")
    
    # Add new alert section
    with st.expander("➕ Create New Alert"):
        with st.form("alert_form"):
            alert_symbol = st.text_input("Stock Symbol")
            alert_type = st.selectbox("Alert Type", ["Price Spike", "Volume Surge", "Volatility", "Custom"])
            alert_message = st.text_area("Alert Message")
            alert_risk = st.selectbox("Risk Level", ["Low", "Medium", "High"])
            
            submit_alert = st.form_submit_button("Create Alert")
            
            if submit_alert:
                if alert_symbol and alert_message:
                    new_alert = {
                        "stock_symbol": alert_symbol.upper(),
                        "alert_type": alert_type.lower().replace(" ", "_"),
                        "message": alert_message,
                        "risk_level": alert_risk
                    }
                    
                    result = api_call("/api/alerts", method="POST", data=new_alert)
                    
                    if result:
                        st.success("✅ Alert created successfully!")
                        st.rerun()
                else:
                    st.error("Please fill in all fields")
    
    st.divider()
    
    # Display alerts
    st.subheader("📋 Active Alerts")
    
    if alerts and len(alerts) > 0:
        for alert in reversed(alerts):  # Show newest first
            risk_color = "🔴" if alert['risk_level'] == "High" else "🟡" if alert['risk_level'] == "Medium" else "🟢"
            
            col1, col2 = st.columns([5, 1])
            
            with col1:
                st.markdown(f"### {risk_color} {alert['stock_symbol']} - {alert['alert_type'].replace('_', ' ').title()}")
                st.write(alert['message'])
                st.caption(f"Created: {alert['timestamp']}")
            
            with col2:
                if st.button("🗑️", key=f"delete_{alert['id']}"):
                    api_call(f"/api/alerts/{alert['id']}", method="DELETE")
                    st.rerun()
            
            st.divider()
    else:
        st.info("No active alerts. Create one above to get started!")

# Page: Suspicious Stocks
elif page == "📊 Suspicious Stocks":
    st.header("Potentially Suspicious Stocks")
    st.write("Stocks showing unusual trading patterns")
    
    if st.button("🔄 Refresh Data"):
        st.rerun()
    
    suspicious_data = api_call("/api/suspicious-stocks")
    
    if suspicious_data and suspicious_data.get('suspicious_stocks'):
        st.success(f"Found {suspicious_data['total']} suspicious stocks")
        
        stocks = suspicious_data['suspicious_stocks']
        
        # Display as cards
        for i in range(0, len(stocks), 3):
            cols = st.columns(3)
            
            for j in range(3):
                if i + j < len(stocks):
                    stock = stocks[i + j]
                    
                    with cols[j]:
                        risk_color = "🔴" if stock['risk_indicator'] == "High" else "🟡"
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3>{risk_color} {stock['symbol']}</h3>
                            <p><strong>LTP:</strong> Rs. {stock['ltp']:.2f}</p>
                            <p><strong>Change:</strong> {stock['change_percent']:.2f}%</p>
                            <p><strong>Volume:</strong> {stock['volume']:,.0f}</p>
                            <p><strong>Risk:</strong> {stock['risk_indicator']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"Analyze {stock['symbol']}", key=f"analyze_{stock['symbol']}"):
                            st.session_state['analyze_symbol'] = stock['symbol']
                            # Switch to analysis page
                            st.info(f"Go to Stock Analysis page and enter: {stock['symbol']}")
    else:
        st.info("No suspicious stocks detected at the moment.")

# Page: About
elif page == "ℹ️ About":
    st.header("About This Project")
    
    st.markdown("""
    ## 📈 NEPSE Pump & Dump Detection System
    
    This project is designed to detect potential pump-and-dump schemes in the Nepal Stock Exchange (NEPSE).
    
    ### 🎯 What is Pump and Dump?
    
    A **pump-and-dump** is a form of securities fraud that involves artificially inflating the price of a stock 
    through false and misleading positive statements, in order to sell the cheaply purchased stock at a higher price.
    
    ### 🔍 Detection Methods
    
    Our system analyzes the following indicators:
    
    1. **Unusual Price Spikes** - Sudden increases in stock price (>5% or >10%)
    2. **High Trading Volume** - Abnormally high trading activity
    3. **Price Volatility** - Large differences between high and low prices
    
    ### 🛠️ Technology Stack
    
    - **Backend**: FastAPI (Python)
    - **Frontend**: Streamlit (Python)
    - **Data Source**: NepaliPaisa API
    - **Analysis**: Simple rule-based machine learning
    
    ### 👥 Project Team
    
    - Student 1: [Your Name]
    - Student 2: [Partner Name]
    - Course: Introduction to Python
    
    ### ⚠️ Disclaimer
    
    This is an educational project. The detection system uses simplified algorithms and should NOT be used 
    for actual investment decisions. Always consult with financial advisors before making investment choices.
    
    ### 📚 Features
    
    - Real-time NEPSE market data
    - Individual stock analysis
    - Alert management system
    - Suspicious stock monitoring
    - Simple risk scoring algorithm
    
    ---
    
    **Made with ❤️ for learning Python**
    """)
    
    # System status
    st.subheader("🔧 System Status")
    
    status = api_call("/")
    
    if status:
        st.success("✅ Backend is running")
        st.json(status)
    else:
        st.error("❌ Backend is not responding")

# Footer
st.divider()
st.caption("NEPSE Pump & Dump Detection System | Educational Project | 2025")