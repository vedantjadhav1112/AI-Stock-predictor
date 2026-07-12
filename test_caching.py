#!/usr/bin/env python3
"""Test script to verify model caching functionality."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.model import StockPredictor
from src.data_fetcher import get_stock_data, get_current_price
from src.preprocessor import preprocess_stock_data
from src.feature_engineer import add_features

MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

def get_model_path(ticker: str, model_type: str) -> str:
    """Get the path for a cached model file."""
    return os.path.join(MODELS_DIR, f"{ticker.lower()}_{model_type}.pkl")

def test_caching():
    """Test the model caching workflow."""
    ticker = "AAPL"
    model_type = "linear"
    model_path = get_model_path(ticker, model_type)

    print("=" * 60)
    print(f"Testing Model Caching for {ticker} ({model_type})")
    print("=" * 60)

    # Check if model exists
    if os.path.exists(model_path):
        print(f"\n✓ Cached model found at: {model_path}")
        print(f"  Size: {os.path.getsize(model_path) / 1024:.2f} KB")
    else:
        print(f"\n✗ No cached model found at: {model_path}")
        print("  Training a new model and saving to cache...")

        # Fetch and process data
        raw_data = get_stock_data(ticker, period_years=2)
        clean_data = preprocess_stock_data(raw_data)
        featured_data = add_features(clean_data)

        # Train and save
        predictor = StockPredictor(model_type=model_type)
        X_train, X_test, y_train, y_test = predictor.prepare_data(featured_data)
        predictor.train(X_train, y_train)
        predictor.save_model(model_path)
        print(f"\n✓ Model saved to: {model_path}")

    # Load and verify
    print("\n--- Loading cached model ---")
    predictor = StockPredictor(model_type=model_type)
    predictor.load_model(model_path)
    print(f"✓ Model loaded successfully")
    print(f"  Features: {len(predictor.feature_names)}")
    print(f"  Model type: {predictor.model_type}")

    # Test prediction
    print("\n--- Testing prediction ---")
    raw_data = get_stock_data(ticker, period_years=2)
    clean_data = preprocess_stock_data(raw_data)
    featured_data = add_features(clean_data)
    latest_features = featured_data.iloc[[-1]]
    result = predictor.predict_next_day(latest_features)
    print(f"✓ Prediction: ${result['predicted_price']:.2f}")
    print(f"  Confidence: {result['confidence']:.1f}%")
    print(f"  Model: {result['model_type']}")

    print("\n" + "=" * 60)
    print("✓ All caching tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    test_caching()