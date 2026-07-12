# AI Stock Research Assistant 🤖📈

An AI-powered stock research tool that combines **machine learning price forecasting** with **news sentiment analysis** to help you make informed investment decisions.

## Features

- 📊 Interactive candlestick charts with technical overlays (SMA 5, SMA 20)
- 🤖 Next-day price prediction using ML models (Linear Regression & Random Forest)
- 📰 AI-powered news summarization via FinBERT
- 💹 Sentiment analysis (Bullish / Bearish / Neutral) with confidence scores
- 📈 Technical indicators — RSI, volatility, volume analysis
- 🔄 Multi-stock comparison with normalized % change overlay
- 💾 Model caching — trained models are saved and reused automatically
- 🎨 Premium dark-mode UI with glassmorphism styling

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit |
| Data | yfinance (Yahoo Finance) |
| ML | scikit-learn (Linear Regression, Random Forest) |
| NLP | Hugging Face Transformers (FinBERT) |
| Charts | Plotly |
| Styling | Custom CSS (glassmorphism, Inter font) |

## Setup

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd ai-stock-predictor

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. (Optional) Copy the environment template
cp .env.example .env

# 6. Run the app
streamlit run app.py
```

> **Note:** The first run will download the FinBERT model (~500MB) from Hugging Face.  
> After that, the model is cached locally in `~/.cache/huggingface/`.

## Project Structure

```
├── app.py                  # Streamlit dashboard (main entry point)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── src/                    # Backend source code
│   ├── __init__.py         # Package initializer
│   ├── data_fetcher.py     # Fetch stock data & current prices
│   ├── preprocessor.py     # Clean and validate data
│   ├── feature_engineer.py # Create ML features (SMA, RSI, etc.)
│   ├── model.py            # Train, predict, evaluate, save/load
│   └── news_analyzer.py    # Fetch news, sentiment, summarize
├── models/                 # Saved trained models (.pkl)
├── notebooks/              # Jupyter notebooks for experimentation
├── test_caching.py         # Model caching integration test
└── test_simple_caching.py  # Caching logic demo
```

## How It Works

1. **Data Ingestion** — Fetches 2 years of historical OHLCV data from Yahoo Finance
2. **Preprocessing** — Cleans data: removes duplicates, fills gaps, validates types
3. **Feature Engineering** — Creates 15+ ML features: moving averages, RSI, volatility, lag features, day-of-week, etc.
4. **ML Training** — Trains a model (Linear Regression or Random Forest) with time-series-aware splitting (no data leakage)
5. **Prediction** — Predicts tomorrow's close price with a confidence score based on model accuracy
6. **News Analysis** — Fetches latest news via yfinance, classifies sentiment with FinBERT, generates a summary
7. **Dashboard** — Renders everything in a premium Streamlit UI with interactive charts

## Known Limitations

- **Not financial advice** — This is a research/educational tool. ML models cannot reliably predict stock prices.
- **Data source** — Relies on Yahoo Finance, which may have delays or outages.
- **NLP model** — FinBERT is trained on financial text but may misclassify ambiguous headlines.
- **Caching** — Cached models become stale over time. Delete `models/*.pkl` to force retraining.
- **GPU not required** — All models run on CPU. Larger transformer models would benefit from GPU acceleration.

## License

MIT
