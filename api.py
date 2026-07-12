# ============================================================
# api.py — FastAPI REST Backend for AI Stock Predictor
# ============================================================
# This exposes the existing ML pipeline as HTTP endpoints
# so the Flutter mobile app can consume the data via JSON.
#
# To run:
#   uvicorn api:app --host 0.0.0.0 --port 8000 --reload
# ============================================================

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import traceback

# Import our existing backend modules — NO changes needed!
from src.data_fetcher import get_stock_data, get_current_price
from src.preprocessor import preprocess_stock_data
from src.feature_engineer import add_features
from src.model import StockPredictor
from src.news_analyzer import get_full_analysis

import os
import numpy as np
import pandas as pd

# --- App Setup ---
app = FastAPI(
    title="AI Stock Predictor API",
    description="ML-powered stock price prediction and news sentiment analysis",
    version="1.0.0",
)

# --- CORS (allow Flutter app to call this API from any origin) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Model caching config ---
MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)


def get_model_path(ticker: str, model_type: str) -> str:
    return os.path.join(MODELS_DIR, f"{ticker.lower()}_{model_type}.pkl")


# ============================================================
# Helper: Run the full analysis pipeline (reused from app.py)
# ============================================================
def _run_analysis(ticker: str, model_type: str = "forest") -> dict:
    """
    Run the full ML pipeline for a ticker.
    Returns a dict with all results.
    """
    results = {}

    # Current price & info
    current_info = get_current_price(ticker)
    results["current_info"] = current_info

    # Check for cached model
    model_path = get_model_path(ticker, model_type)
    predictor = StockPredictor(model_type=model_type)

    if os.path.exists(model_path):
        predictor.load_model(model_path)
        cached = True
    else:
        cached = False

    # Always fetch recent data for predictions & charts
    raw_data = get_stock_data(ticker, period_years=2)
    clean_data = preprocess_stock_data(raw_data)
    featured_data = add_features(clean_data)
    results["featured_data"] = featured_data

    if not cached:
        X_train, X_test, y_train, y_test = predictor.prepare_data(featured_data)
        predictor.train(X_train, y_train)
        predictor.evaluate(X_test, y_test)
        predictor.save_model(model_path)
    else:
        if not predictor.metrics:
            X_train, X_test, y_train, y_test = predictor.prepare_data(featured_data)
            predictor.evaluate(X_test, y_test)
            predictor.save_model(model_path)

    results["predictor"] = predictor
    results["cached"] = cached

    # Prediction
    latest_features = featured_data.iloc[[-1]]
    prediction = predictor.predict_next_day(latest_features)
    results["prediction"] = prediction

    # News & sentiment
    nlp_results = get_full_analysis(ticker)
    results["nlp_results"] = nlp_results

    return results


def _serialize_featured_data(df: pd.DataFrame, tail: int = 126) -> list:
    """Convert a DataFrame tail to a JSON-serializable list of dicts."""
    plot_df = df.tail(tail).copy()
    plot_df.index = plot_df.index.strftime("%Y-%m-%d")
    records = []
    for date, row in plot_df.iterrows():
        record = {"date": date}
        for col in row.index:
            val = row[col]
            # Convert numpy types to native Python types
            if isinstance(val, (np.integer,)):
                record[col] = int(val)
            elif isinstance(val, (np.floating,)):
                record[col] = round(float(val), 4)
            else:
                record[col] = val
        records.append(record)
    return records


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Stock Predictor API"}


@app.get("/api/stock/{ticker}/price")
def get_price(ticker: str):
    """
    Get the current stock price and company info.
    Fast endpoint — no ML involved.
    """
    ticker = ticker.upper().strip()
    try:
        info = get_current_price(ticker)
        return {
            "ticker": ticker,
            "price": info["price"],
            "name": info["name"],
            "currency": info["currency"],
            "market_cap": info["market_cap"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/stock/{ticker}/analysis")
def get_analysis(
    ticker: str,
    model_type: str = Query("forest", regex="^(linear|forest)$"),
):
    """
    Full analysis: prediction, model metrics, technical indicators,
    news sentiment, and chart data. This is the main endpoint.
    """
    ticker = ticker.upper().strip()
    try:
        results = _run_analysis(ticker, model_type)

        current_info = results["current_info"]
        prediction = results["prediction"]
        nlp_results = results["nlp_results"]
        featured_data = results["featured_data"]
        predictor = results["predictor"]

        current_price = current_info["price"]
        pred_price = prediction["predicted_price"]
        price_diff = pred_price - current_price
        price_pct = (price_diff / current_price) * 100 if current_price else 0

        # Latest technical indicators
        latest = featured_data.iloc[-1]

        # Feature importance
        importance = predictor.get_feature_importance()
        top_features = [
            {"name": name, "score": round(float(score), 4)}
            for name, score in importance[:8]
        ]

        return {
            "ticker": ticker,
            "current_price": current_price,
            "predicted_price": pred_price,
            "price_change": round(price_diff, 2),
            "price_change_pct": round(price_pct, 2),
            "confidence": prediction["confidence"],
            "model_type": model_type,
            "cached_model": results["cached"],
            "company": {
                "name": current_info["name"],
                "currency": current_info["currency"],
                "market_cap": current_info["market_cap"],
            },
            "metrics": predictor.metrics,
            "technical": {
                "rsi": round(float(latest["RSI"]), 2),
                "sma_5": round(float(latest["SMA_5"]), 2),
                "sma_20": round(float(latest["SMA_20"]), 2),
                "volatility_10": round(float(latest["Volatility_10"]) * 100, 2),
                "close_to_sma20": round(float(latest["Close_to_SMA20"]), 4),
                "daily_return": round(float(latest["Daily_Return"]) * 100, 2),
                "volume": int(latest["Volume"]),
            },
            "feature_importance": top_features,
            "sentiment": nlp_results["sentiment"],
            "news_summary": nlp_results["summary"],
            "articles": nlp_results["articles"],
            "chart_data": _serialize_featured_data(featured_data, tail=126),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/stock/{ticker}/news")
def get_news(ticker: str):
    """
    Get news headlines and sentiment analysis.
    Lighter endpoint — no ML model training, just NLP.
    """
    ticker = ticker.upper().strip()
    try:
        nlp_results = get_full_analysis(ticker)
        return {
            "ticker": ticker,
            "sentiment": nlp_results["sentiment"],
            "summary": nlp_results["summary"],
            "articles": nlp_results["articles"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{ticker}/history")
def get_history(
    ticker: str,
    period_years: int = Query(2, ge=1, le=5),
    tail: int = Query(126, ge=10, le=500),
):
    """
    Get historical OHLCV data + features for charting.
    """
    ticker = ticker.upper().strip()
    try:
        raw_data = get_stock_data(ticker, period_years=period_years)
        clean_data = preprocess_stock_data(raw_data)
        featured_data = add_features(clean_data)

        return {
            "ticker": ticker,
            "total_rows": len(featured_data),
            "data": _serialize_featured_data(featured_data, tail=tail),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stock/{ticker}/compare/{other_ticker}")
def compare_stocks(
    ticker: str,
    other_ticker: str,
    model_type: str = Query("forest", regex="^(linear|forest)$"),
):
    """
    Compare two stocks side-by-side with predictions and sentiment.
    """
    ticker = ticker.upper().strip()
    other_ticker = other_ticker.upper().strip()

    if ticker == other_ticker:
        raise HTTPException(status_code=400, detail="Cannot compare a stock with itself")

    try:
        results_a = _run_analysis(ticker, model_type)
        results_b = _run_analysis(other_ticker, model_type)

        def _stock_summary(t, res):
            cp = res["current_info"]["price"]
            pp = res["prediction"]["predicted_price"]
            diff = pp - cp
            pct = (diff / cp) * 100 if cp else 0
            return {
                "ticker": t,
                "current_price": cp,
                "predicted_price": pp,
                "price_change": round(diff, 2),
                "price_change_pct": round(pct, 2),
                "confidence": res["prediction"]["confidence"],
                "sentiment": res["nlp_results"]["sentiment"]["overall_sentiment"],
                "name": res["current_info"]["name"],
                "market_cap": res["current_info"]["market_cap"],
                "metrics": res["predictor"].metrics,
            }

        # Normalized % change data for overlay chart
        def _pct_change_series(fd, tail=126):
            tail_df = fd.tail(tail)
            base = float(tail_df["Close"].iloc[0])
            records = []
            for date, row in tail_df.iterrows():
                pct = ((float(row["Close"]) - base) / base) * 100
                records.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "pct_change": round(pct, 2),
                })
            return records

        return {
            "stock_a": _stock_summary(ticker, results_a),
            "stock_b": _stock_summary(other_ticker, results_b),
            "chart_a": _pct_change_series(results_a["featured_data"]),
            "chart_b": _pct_change_series(results_b["featured_data"]),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
