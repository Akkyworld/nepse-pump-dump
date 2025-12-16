import streamlit as st
import requests
import pandas as pd

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="NEPSE Pump & Dump Detector",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- BACKEND API --------------------
API_URL = "http://localhost:8000"

# -------------------- CUSTOM CSS --------------------
st.markdown("""
<style>
/* BODY */
body, .main {
    background-color: #121212;  /* Dark minimal background */
    color: #e0e0e0;             /* Light text */
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* MAIN HEADER */
.main-header {
    background: linear-gradient(135deg, #4f46e5, #6366f1);
    padding: 2rem;
    border-radius: 12px;
    color: #ffffff;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 6px 15px rgba(0,0,0,0.3);
}

/* METRIC CARDS */
.metric-card {
    background-color: #1f1f2e;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    border-left: 4px solid #4f46e5;
    margin: 1rem 0;
}

/* STOCK CARDS */
.stock-card {
    background-color: #1f1f2e;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.25);
    margin: 0.5rem 0;
}

/* RISK BADGES */
.risk-high {
    background-color: #e53935;
    color: #ffffff;
    padding: 0.3rem 0.8rem;
    border-radius: 12px;
    font-weight: bold;
}
.risk-medium {
    background-color: #ffb300;
    color: #ffffff;
    padding: 0.3rem 0.8rem;
    border-radius: 12px;
    font-weight: bold;
}
.risk-low {
    background-color: #43a047;
    color: #ffffff;
    padding: 0.3rem 0.8rem;
    border-radius: 12px;
    font-weight: bold;
}

/* TABLES */
[data-testid="stDataFrameContainer"] {
    background-color: #1f1f2e !important;
    color: #e0e0e0 !important;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background-color: #1b1b24;
    color: #e0e0e0;
}

/* HIDE STREAMLIT MENU & FOOTER */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# -------------------- API CALL --------------------
def api_call(endpoint):
    try:
        response = requests.get(f"{API_URL}{endpoint}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend! Make sure it's running on port 8000")
        return None

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown("## 📈 NEPSE Detector")
    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "🔍 Stock Analysis", "⚠️ Suspicious Stocks"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### Quick Stats")

    stats = api_call("/stats")
    if stats:
        st.metric("Total Stocks", stats.get("total_stocks", 0))
        st.metric("High Risk", stats.get("high_risk", 0))
        st.metric("Medium Risk", stats.get("medium_risk", 0))

# -------------------- DASHBOARD --------------------
if page == "🏠 Dashboard":
    st.markdown("""
    <div class="main-header">
        <h1>📈 NEPSE Pump & Dump Detection System</h1>
        <p>Real-time monitoring of Nepal Stock Exchange</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📊 Today's Trading Activity")

    tab1, tab2 = st.tabs(["All Stocks", "Suspicious Only"])

    # -------- ALL STOCKS --------
    with tab1:
        stocks_data = api_call("/stocks")
        if stocks_data:
            df = pd.DataFrame(stocks_data)

            col1, col2, col3 = st.columns(3)

            with col1:
                risk_filter = st.selectbox(
                    "Filter by Risk",
                    ["All", "HIGH", "MEDIUM", "LOW"]
                )

            with col2:
                search = st.text_input("🔍 Search Symbol").upper()

            with col3:
                sort_by = st.selectbox(
                    "Sort by",
                    ["volume_spike", "price_change_percent", "volume"]
                )

            # Filtering
            if risk_filter != "All":
                df = df[df["risk_level"] == risk_filter]

            if search:
                df = df[df["symbol"].str.contains(search, case=False)]

            # Safe Sorting (NO MORE KeyError)
            if sort_by in df.columns:
                df = df.sort_values(by=sort_by, ascending=False)

            st.dataframe(
                df[
                    [
                        "symbol",
                        "current_price",
                        "price_change_percent",
                        "volume",
                        "volume_spike",
                        "risk_level",
                        "pattern",
                        "reason",
                    ]
                ],
                use_container_width=True,
                height=600,
            )

    # -------- SUSPICIOUS ONLY --------
    with tab2:
        suspicious_data = api_call("/stocks/suspicious")
        if suspicious_data:
            for stock in suspicious_data:
                risk_class = f"risk-{stock['risk_level'].lower()}"
                st.markdown(f"""
                <div class="stock-card">
                    <h3>{stock['symbol']}
                        <span class="{risk_class}">
                            {stock['risk_level']} Risk
                        </span>
                    </h3>
                    <p>
                        Price: Rs. {stock['current_price']:.2f} |
                        Change: {stock['price_change_percent']:.2f}% |
                        Volume: {stock['volume']} |
                        Spike: {stock['volume_spike']}x
                    </p>
                    <p>{stock['pattern']} - {stock['reason']}</p>
                </div>
                """, unsafe_allow_html=True)

# -------------------- STOCK ANALYSIS --------------------
elif page == "🔍 Stock Analysis":
    st.title("🔍 Individual Stock Analysis")

    stock_symbol = st.text_input(
        "Stock Symbol",
        placeholder="e.g. NABIL, NICA, ADBL"
    ).upper()

    if st.button("Analyze") and stock_symbol:
        analysis = api_call(f"/stocks/{stock_symbol}")
        if analysis:
            risk_class = f"risk-{analysis['risk_level'].lower()}"
            st.markdown(f"""
            <div class="stock-card">
                <h2>
                    {analysis['symbol']}
                    <span class="{risk_class}">
                        {analysis['risk_level']}
                    </span>
                </h2>
                <p>Price: Rs. {analysis['current_price']:.2f}</p>
                <p>Change: {analysis['price_change_percent']:.2f}%</p>
                <p>Volume: {analysis['volume']}</p>
                <p>Volume Spike: {analysis['volume_spike']}x</p>
                <p>{analysis['reason']}</p>
            </div>
            """, unsafe_allow_html=True)

# -------------------- SUSPICIOUS STOCKS --------------------
elif page == "⚠️ Suspicious Stocks":
    st.title("⚠️ Potentially Suspicious Stocks")

    suspicious_data = api_call("/stocks/suspicious")
    if suspicious_data:
        for stock in suspicious_data:
            risk_class = f"risk-{stock['risk_level'].lower()}"
            st.markdown(f"""
            <div class="stock-card">
                <h3>
                    {stock['symbol']}
                    <span class="{risk_class}">
                        {stock['risk_level']} Risk
                    </span>
                </h3>
                <p>
                    Price: Rs. {stock['current_price']:.2f} |
                    Change: {stock['price_change_percent']:.2f}% |
                    Volume: {stock['volume']}
                </p>
                <p>{stock['pattern']} - {stock['reason']}</p>
            </div>
            """, unsafe_allow_html=True)

# -------------------- FOOTER --------------------
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#888;'>NEPSE Pump & Dump Detection System | 2024</div>",
    unsafe_allow_html=True,
)

