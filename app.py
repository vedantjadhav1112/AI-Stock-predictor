# ============================================================
# app.py — The Streamlit Dashboard (Final Milestone)
# ============================================================
# This is the frontend of our application. It ties together
# all the backend modules we built in the 'src' directory.
#
# To run this:
#   streamlit run app.py
# ============================================================

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import joblib
import time

# Import our backend modules
from src.data_fetcher import get_stock_data, get_current_price
from src.preprocessor import preprocess_stock_data
from src.feature_engineer import add_features
from src.model import StockPredictor
from src.news_analyzer import get_full_analysis

# --- Model Caching Configuration ---
MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

def get_model_path(ticker: str, model_type: str) -> str:
    """Get the path for a cached model file."""
    return os.path.join(MODELS_DIR, f"{ticker.lower()}_{model_type}.pkl")

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Stock Research Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS Styling for a Premium Dark-Mode Look ---
st.markdown("""
<style>
    /* ---- Google Fonts ---- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ---- Global typography ---- */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ---- Glassmorphism metric cards ---- */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(30,58,95,0.55) 0%, rgba(15,32,56,0.65) 100%);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(99,179,237,0.18);
        padding: 18px 18px 18px 22px;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.25);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(59,130,246,0.22);
    }

    /* ---- Metric labels & values ---- */
    div[data-testid="metric-container"] label {
        color: rgba(148,163,184,0.9) !important;
        font-weight: 500 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-weight: 700 !important;
        color: #e2e8f0 !important;
    }

    /* ---- Gradient header banner ---- */
    .hero-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 40%, #2563eb 100%);
        border-radius: 18px;
        padding: 34px 40px;
        margin-bottom: 28px;
        border: 1px solid rgba(99,179,237,0.12);
        box-shadow: 0 4px 30px rgba(37,99,235,0.15);
    }
    .hero-header h1 {
        margin: 0 0 6px 0;
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(90deg, #e2e8f0, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }
    .hero-header p {
        margin: 0;
        color: rgba(148,163,184,0.85);
        font-size: 1rem;
        font-weight: 400;
    }

    /* ---- Section cards ---- */
    .glass-card {
        background: linear-gradient(135deg, rgba(30,58,95,0.35) 0%, rgba(15,32,56,0.45) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(99,179,237,0.12);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.18);
    }

    /* ---- Sidebar styling ---- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
        border-right: 1px solid rgba(99,179,237,0.1);
    }
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #60a5fa !important;
    }

    /* ---- Progress bars ---- */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #2563eb, #60a5fa) !important;
        border-radius: 6px;
    }

    /* ---- Smooth reveal animation ---- */
    @keyframes fadeSlideIn {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .stMetric, .element-container {
        animation: fadeSlideIn 0.45s ease-out;
    }

    /* ---- Divider ---- */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99,179,237,0.25), transparent);
        margin: 28px 0;
    }

    /* ---- Info boxes ---- */
    .stAlert {
        border-radius: 12px !important;
        border: 1px solid rgba(99,179,237,0.15) !important;
    }

    /* ---- Expander headers ---- */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        color: #94a3b8 !important;
    }

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 8px 20px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
        color: white !important;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Helper Functions
# ============================================================

def plot_stock_chart(df: pd.DataFrame, ticker: str):
    """Create an interactive candlestick chart using Plotly."""
    # We'll plot just the last 6 months to keep it readable
    plot_df = df.tail(126)  # ~126 trading days in 6 months
    
    fig = go.Figure(data=[go.Candlestick(
        x=plot_df.index,
        open=plot_df['Open'],
        high=plot_df['High'],
        low=plot_df['Low'],
        close=plot_df['Close'],
        name="Price",
        increasing_line_color='#22c55e',
        decreasing_line_color='#ef4444',
    )])
    
    # Add the 20-day Moving Average as a line
    fig.add_trace(go.Scatter(
        x=plot_df.index, 
        y=plot_df['SMA_20'], 
        line=dict(color='#60a5fa', width=2), 
        name='20-Day SMA'
    ))

    # Add the 5-day Moving Average as a line
    fig.add_trace(go.Scatter(
        x=plot_df.index,
        y=plot_df['SMA_5'],
        line=dict(color='#f59e0b', width=1.5, dash='dot'),
        name='5-Day SMA'
    ))

    fig.update_layout(
        title=dict(
            text=f"{ticker} — 6 Month Price History",
            font=dict(size=18, color='#e2e8f0', family='Inter'),
        ),
        yaxis_title="Price (USD)",
        xaxis_title="Date",
        template="plotly_dark",
        height=500,
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15,23,42,0.6)',
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=12, color='#94a3b8'),
        ),
        xaxis=dict(gridcolor='rgba(99,179,237,0.08)'),
        yaxis=dict(gridcolor='rgba(99,179,237,0.08)'),
    )
    return fig


def plot_rsi_chart(df: pd.DataFrame, ticker: str):
    """Create an RSI indicator chart."""
    plot_df = df.tail(126)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['RSI'],
        line=dict(color='#a78bfa', width=2),
        name='RSI (14)',
        fill='tozeroy',
        fillcolor='rgba(167,139,250,0.08)',
    ))

    # Overbought / Oversold lines
    fig.add_hline(y=70, line_dash="dash", line_color="rgba(239,68,68,0.5)",
                  annotation_text="Overbought (70)", annotation_position="bottom right")
    fig.add_hline(y=30, line_dash="dash", line_color="rgba(34,197,94,0.5)",
                  annotation_text="Oversold (30)", annotation_position="top right")

    fig.update_layout(
        title=dict(text=f"{ticker} — RSI Momentum", font=dict(size=16, color='#e2e8f0', family='Inter')),
        yaxis_title="RSI",
        template="plotly_dark",
        height=280,
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15,23,42,0.6)',
        yaxis=dict(range=[0, 100], gridcolor='rgba(99,179,237,0.08)'),
        xaxis=dict(gridcolor='rgba(99,179,237,0.08)'),
    )
    return fig


def plot_volume_chart(df: pd.DataFrame, ticker: str):
    """Create a volume bar chart."""
    plot_df = df.tail(60)

    colors = ['#22c55e' if row['Close'] >= row['Open'] else '#ef4444'
              for _, row in plot_df.iterrows()]

    fig = go.Figure(data=[go.Bar(
        x=plot_df.index, y=plot_df['Volume'],
        marker_color=colors, name='Volume',
    )])

    fig.update_layout(
        title=dict(text=f"{ticker} — Trading Volume (60 Days)", font=dict(size=16, color='#e2e8f0', family='Inter')),
        yaxis_title="Volume",
        template="plotly_dark",
        height=260,
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15,23,42,0.6)',
        yaxis=dict(gridcolor='rgba(99,179,237,0.08)'),
        xaxis=dict(gridcolor='rgba(99,179,237,0.08)'),
    )
    return fig


def run_analysis(ticker: str, model_type: str):
    """
    Run the full analysis pipeline for a given ticker and model type.
    Returns a dict with all results, or raises an exception.
    """
    results = {}

    # --- Always fetch current price & info ---
    current_info = get_current_price(ticker)
    results['current_info'] = current_info

    # --- Check for cached model ---
    model_path = get_model_path(ticker, model_type)
    predictor = StockPredictor(model_type=model_type)

    if os.path.exists(model_path):
        st.write(f"📦 Loading cached **{model_type}** model for **{ticker}**...")
        predictor.load_model(model_path)
        cached = True
    else:
        cached = False

    # --- We always need recent data for predictions & charts ---
    st.write("📡 Fetching historical data from Yahoo Finance...")
    raw_data = get_stock_data(ticker, period_years=2)
    clean_data = preprocess_stock_data(raw_data)
    featured_data = add_features(clean_data)
    results['featured_data'] = featured_data

    if not cached:
        # Train a fresh model
        st.write(f"🤖 Training **{model_type}** model on 2 years of history...")
        X_train, X_test, y_train, y_test = predictor.prepare_data(featured_data)
        predictor.train(X_train, y_train)

        # Evaluate the model so confidence is real
        st.write("📊 Evaluating model accuracy...")
        predictor.evaluate(X_test, y_test)

        # Save to cache
        st.write("💾 Saving model to cache...")
        predictor.save_model(model_path)
    else:
        # For cached models, if metrics are empty, run a quick evaluation
        if not predictor.metrics:
            st.write("📊 Evaluating cached model accuracy...")
            X_train, X_test, y_train, y_test = predictor.prepare_data(featured_data)
            predictor.evaluate(X_test, y_test)
            predictor.save_model(model_path)

    results['predictor'] = predictor
    results['cached'] = cached

    # --- Prediction ---
    latest_features = featured_data.iloc[[-1]]
    prediction = predictor.predict_next_day(latest_features)
    results['prediction'] = prediction

    # --- News & sentiment ---
    st.write("📰 Fetching news and running AI sentiment analysis...")
    nlp_results = get_full_analysis(ticker)
    results['nlp_results'] = nlp_results

    return results


# ============================================================
# Main Dashboard UI
# ============================================================

# --- Hero header ---
st.markdown("""
<div class="hero-header">
    <h1>📈 AI Stock Research Assistant</h1>
    <p>Machine learning price forecasting &amp; AI-powered news sentiment — all in one place.</p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar (User Inputs) ---
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    ticker = st.text_input(
        "Stock Ticker", value="AAPL",
        placeholder="e.g. AAPL, TSLA, MSFT"
    ).upper().strip()

    model_choice = st.selectbox(
        "ML Model",
        options=["Random Forest (Complex)", "Linear Regression (Fast)"],
    )
    model_type = "linear" if "Linear" in model_choice else "forest"

    analyze_button = st.button("🚀 Analyze Stock", use_container_width=True, type="primary")

    # --- Compare mode ---
    st.markdown("---")
    st.markdown("### 🔄 Compare Stocks")
    compare_enabled = st.checkbox("Enable comparison")
    compare_ticker = ""
    if compare_enabled:
        compare_ticker = st.text_input(
            "Compare with", value="MSFT",
            placeholder="e.g. GOOGL"
        ).upper().strip()

    # --- About section ---
    st.markdown("---")
    st.markdown("### 📋 About")
    st.markdown("""
    **v1.0** — AI Stock Research Assistant  
    
    **Models:** Linear Regression, Random Forest  
    **NLP:** FinBERT (financial sentiment)  
    **Data:** Yahoo Finance (real-time)
    
    *Built with Streamlit, scikit-learn & HuggingFace*
    """)

st.divider()

# ============================================================
# Analysis Execution
# ============================================================
if analyze_button:
    if not ticker:
        st.error("Please enter a valid stock ticker.")
        st.stop()

    try:
        with st.status(f"Analyzing {ticker}...", expanded=True) as status:
            results = run_analysis(ticker, model_type)

            if results['cached']:
                st.write("✅ Loaded model from cache")

            status.update(label="✅ Analysis Complete!", state="complete", expanded=False)

        # ============================================================
        # Render Results
        # ============================================================

        current_info = results['current_info']
        prediction = results['prediction']
        nlp_results = results['nlp_results']
        featured_data = results['featured_data']
        predictor = results['predictor']

        current_price = current_info['price']
        pred_price = prediction['predicted_price']
        price_diff = pred_price - current_price
        price_pct = (price_diff / current_price) * 100 if current_price else 0

        # --- Tabs ---
        tab_overview, tab_technical, tab_news, tab_compare = st.tabs([
            "📊 Overview", "📈 Technical Analysis", "📰 News & Sentiment", "🔄 Compare"
        ])

        # ============================
        # TAB 1: Overview
        # ============================
        with tab_overview:
            # --- Key Metrics ---
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Current Price", f"${current_price:,.2f}")
            with col2:
                st.metric(
                    "Predicted Price (Tomorrow)",
                    f"${pred_price:,.2f}",
                    f"{price_diff:>+,.2f} ({price_pct:>+.2f}%)"
                )
            with col3:
                st.metric("Model Confidence", f"{prediction['confidence']}%")
            with col4:
                sentiment = nlp_results['sentiment']['overall_sentiment']
                icon = "🟢" if sentiment == "Bullish" else "🔴" if sentiment == "Bearish" else "⚪"
                st.metric("News Sentiment", f"{icon} {sentiment}")

            st.markdown("<br>", unsafe_allow_html=True)

            # --- Additional Info Row ---
            col_mc, col_name, col_cur = st.columns(3)
            with col_mc:
                mc = current_info.get('market_cap', 0)
                if mc:
                    if mc >= 1e12:
                        mc_str = f"${mc/1e12:.2f}T"
                    elif mc >= 1e9:
                        mc_str = f"${mc/1e9:.2f}B"
                    elif mc >= 1e6:
                        mc_str = f"${mc/1e6:.2f}M"
                    else:
                        mc_str = f"${mc:,.0f}"
                    st.metric("Market Cap", mc_str)
            with col_name:
                st.metric("Company", current_info.get('name', ticker))
            with col_cur:
                st.metric("Currency", current_info.get('currency', 'USD'))

            st.markdown("<br>", unsafe_allow_html=True)

            # --- Price Chart ---
            st.subheader("📊 Price Chart")
            fig = plot_stock_chart(featured_data, ticker)
            st.plotly_chart(fig, use_container_width=True)

            # --- Model Performance ---
            st.subheader("🎯 Model Performance")
            metrics = predictor.metrics
            if metrics:
                perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
                with perf_col1:
                    st.metric("MAE", f"${metrics.get('MAE', 'N/A')}")
                with perf_col2:
                    st.metric("RMSE", f"${metrics.get('RMSE', 'N/A')}")
                with perf_col3:
                    r2 = metrics.get('R2', 0)
                    r2_pct = f"{r2 * 100:.1f}%" if isinstance(r2, (int, float)) else 'N/A'
                    st.metric("R² Score", r2_pct)
                with perf_col4:
                    st.metric("MAPE", f"{metrics.get('MAPE', 'N/A')}%")
            else:
                st.info("No evaluation metrics available. Retrain the model to see performance.")

            # --- Feature Importance ---
            st.subheader("🧠 Feature Importance")
            st.caption("What features drove this prediction?")
            importance = predictor.get_feature_importance()
            if importance:
                top_features = importance[:8]
                feat_names = [f[0] for f in top_features]
                feat_scores = [f[1] for f in top_features]

                # Normalize for display
                max_score = max(feat_scores) if feat_scores else 1
                for name, score in top_features:
                    display_score = min(score / max_score, 1.0) if max_score > 0 else 0
                    st.progress(display_score, text=f"{name}  ({score:.4f})")

        # ============================
        # TAB 2: Technical Analysis
        # ============================
        with tab_technical:
            st.subheader("📈 Technical Indicators")

            # RSI Chart
            fig_rsi = plot_rsi_chart(featured_data, ticker)
            st.plotly_chart(fig_rsi, use_container_width=True)

            # Volume Chart
            fig_vol = plot_volume_chart(featured_data, ticker)
            st.plotly_chart(fig_vol, use_container_width=True)

            # Key Technicals Summary
            st.subheader("📋 Key Technical Levels")
            latest = featured_data.iloc[-1]
            tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)

            with tech_col1:
                st.metric("RSI (14)", f"{latest['RSI']:.1f}")
            with tech_col2:
                st.metric("SMA 5", f"${latest['SMA_5']:.2f}")
            with tech_col3:
                st.metric("SMA 20", f"${latest['SMA_20']:.2f}")
            with tech_col4:
                vol_10 = latest['Volatility_10'] * 100
                st.metric("Volatility (10d)", f"{vol_10:.2f}%")

            st.markdown("<br>", unsafe_allow_html=True)

            # Interpretation
            rsi_val = latest['RSI']
            if rsi_val > 70:
                st.warning("⚠️ RSI is above 70 — the stock may be **overbought**. Watch for a potential pullback.")
            elif rsi_val < 30:
                st.success("🟢 RSI is below 30 — the stock may be **oversold**. A bounce could be coming.")
            else:
                st.info(f"ℹ️ RSI at {rsi_val:.1f} — the stock is in **neutral** momentum territory.")

            close_vs_sma20 = latest['Close_to_SMA20']
            if close_vs_sma20 > 1.02:
                st.success(f"🟢 Price is **{(close_vs_sma20 - 1)*100:.1f}% above** the 20-day SMA — short-term bullish trend.")
            elif close_vs_sma20 < 0.98:
                st.warning(f"⚠️ Price is **{(1 - close_vs_sma20)*100:.1f}% below** the 20-day SMA — short-term bearish trend.")
            else:
                st.info("ℹ️ Price is near the 20-day SMA — consolidating.")

        # ============================
        # TAB 3: News & Sentiment
        # ============================
        with tab_news:
            col_summary, col_breakdown = st.columns([2, 1])

            with col_summary:
                st.subheader("🧠 AI News Summary")
                st.info(nlp_results['summary'])

                st.subheader("📰 Recent Headlines")
                if not nlp_results['articles']:
                    st.write("No recent articles found.")
                else:
                    for i, article in enumerate(nlp_results['articles'][:8]):
                        # Get sentiment for this article
                        details = nlp_results['sentiment'].get('details', [])
                        if i < len(details):
                            sent = details[i]['sentiment']
                            conf = details[i]['confidence']
                            sent_icon = "🟢" if sent == "Bullish" else "🔴" if sent == "Bearish" else "⚪"
                            badge = f"{sent_icon} {sent} ({conf:.0%})"
                        else:
                            badge = ""

                        st.markdown(
                            f"**{badge}** — [{article['title']}]({article['link']})  \n"
                            f"*{article['publisher']}*"
                        )
                        if i < len(nlp_results['articles'][:8]) - 1:
                            st.markdown("---")

            with col_breakdown:
                st.subheader("📊 Sentiment Breakdown")

                pos_pct = nlp_results['sentiment']['positive_pct']
                neg_pct = nlp_results['sentiment']['negative_pct']
                neu_pct = nlp_results['sentiment']['neutral_pct']

                st.metric("Overall", f"{nlp_results['sentiment']['overall_sentiment']}")
                st.markdown("<br>", unsafe_allow_html=True)

                st.progress(pos_pct / 100, text=f"🟢 Bullish — {pos_pct:.0f}%")
                st.progress(neg_pct / 100, text=f"🔴 Bearish — {neg_pct:.0f}%")
                st.progress(neu_pct / 100, text=f"⚪ Neutral — {neu_pct:.0f}%")

                st.markdown("<br>", unsafe_allow_html=True)
                st.metric(
                    "Avg Confidence",
                    f"{nlp_results['sentiment']['confidence']:.0%}"
                )

        # ============================
        # TAB 4: Compare
        # ============================
        with tab_compare:
            if compare_enabled and compare_ticker and compare_ticker != ticker:
                st.subheader(f"🔄 {ticker} vs {compare_ticker}")

                try:
                    with st.status(f"Analyzing {compare_ticker}...", expanded=True) as cmp_status:
                        cmp_results = run_analysis(compare_ticker, model_type)
                        cmp_status.update(label=f"✅ {compare_ticker} analysis complete!", state="complete", expanded=False)

                    cmp_info = cmp_results['current_info']
                    cmp_pred = cmp_results['prediction']
                    cmp_nlp = cmp_results['nlp_results']

                    cmp_price = cmp_info['price']
                    cmp_pred_price = cmp_pred['predicted_price']
                    cmp_diff = cmp_pred_price - cmp_price
                    cmp_pct = (cmp_diff / cmp_price) * 100 if cmp_price else 0

                    # Side-by-side metrics
                    st.markdown("### Key Metrics Comparison")
                    compare_data = {
                        "Metric": ["Current Price", "Predicted Price", "Change (%)", "Confidence", "Sentiment", "Market Cap"],
                        ticker: [
                            f"${current_price:,.2f}",
                            f"${pred_price:,.2f}",
                            f"{price_pct:+.2f}%",
                            f"{prediction['confidence']}%",
                            sentiment,
                            current_info.get('name', ticker),
                        ],
                        compare_ticker: [
                            f"${cmp_price:,.2f}",
                            f"${cmp_pred_price:,.2f}",
                            f"{cmp_pct:+.2f}%",
                            f"{cmp_pred['confidence']}%",
                            cmp_nlp['sentiment']['overall_sentiment'],
                            cmp_info.get('name', compare_ticker),
                        ],
                    }
                    st.table(pd.DataFrame(compare_data).set_index("Metric"))

                    # Overlaid price chart
                    st.markdown("### Price History Overlay")
                    fig_cmp = go.Figure()

                    # Normalize both to percentage change from start
                    for t, fd, color, label in [
                        (ticker, featured_data, '#3b82f6', ticker),
                        (compare_ticker, cmp_results['featured_data'], '#f59e0b', compare_ticker),
                    ]:
                        tail_df = fd.tail(126)
                        base = tail_df['Close'].iloc[0]
                        pct_change = ((tail_df['Close'] - base) / base) * 100

                        fig_cmp.add_trace(go.Scatter(
                            x=tail_df.index, y=pct_change,
                            line=dict(color=color, width=2.5),
                            name=label,
                        ))

                    fig_cmp.update_layout(
                        title="6-Month % Change Comparison",
                        yaxis_title="% Change",
                        template="plotly_dark",
                        height=420,
                        margin=dict(l=0, r=0, t=50, b=0),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(15,23,42,0.6)',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        xaxis=dict(gridcolor='rgba(99,179,237,0.08)'),
                        yaxis=dict(gridcolor='rgba(99,179,237,0.08)'),
                    )
                    st.plotly_chart(fig_cmp, use_container_width=True)

                except Exception as e:
                    st.error(f"Could not analyze {compare_ticker}: {e}")
            else:
                if not compare_enabled:
                    st.info("👈 Enable **Compare Stocks** in the sidebar and enter a second ticker to see a side-by-side comparison.")
                elif compare_ticker == ticker:
                    st.warning("Please enter a different ticker to compare against.")
                else:
                    st.info("👈 Enter a comparison ticker in the sidebar.")

    except Exception as e:
        st.error(f"❌ An error occurred during analysis: {e}")
        with st.expander("🔍 Error Details"):
            st.exception(e)
else:
    # Shown before the user clicks analyze
    st.markdown("""
    <div class="glass-card" style="text-align:center; padding: 60px 40px;">
        <h2 style="color: #60a5fa; margin-bottom: 12px;">Welcome!</h2>
        <p style="color: #94a3b8; font-size: 1.1rem;">
            Enter a stock ticker in the sidebar and click <strong>Analyze Stock</strong> to get
            AI-powered predictions, technical analysis, and news sentiment.
        </p>
    </div>
    """, unsafe_allow_html=True)
