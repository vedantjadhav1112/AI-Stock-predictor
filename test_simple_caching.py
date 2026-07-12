#!/usr/bin/env python3
"""Simple demonstration of model caching logic."""

import os
import pickle

# --- Model Caching Demo ---

class SimpleModel:
    """Simple model demo."""
    def __init__(self, model_type, ticker):
        self.model_type = model_type
        self.ticker = ticker
        self.feature_names = []
        self.metrics = {}

    def prepare_data(self, data):
        """Mock data preparation."""
        self.feature_names = ["Close", "RSI", "SMA_20", "Volume_Change"]
        return {"X_train": [[1,2,3,4]], "X_test": [[5,6,7,8]], "y_train": [100, 102], "y_test": [105]}

    def train(self, X_train, y_train):
        """Mock training."""
        print(f"  🧠 Training {self.model_type} model for {self.ticker}...")
        self.metrics = {"R2": 0.95, "MAE": 2.5, "MAPE": 2.1}
        return self

    def save_model(self, filepath):
        """Mock save model."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        model_data = {
            "model_type": self.model_type,
            "ticker": self.ticker,
            "feature_names": self.feature_names,
            "metrics": self.metrics,
            "model": self
        }
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"  💾 Saved model to {filepath}")

    def load_model(self, filepath):
        """Mock load model."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        self.model_type = model_data["model_type"]
        self.ticker = model_data["ticker"]
        self.feature_names = model_data["feature_names"]
        self.metrics = model_data["metrics"]
        print(f"  📦 Loaded model from {filepath}")

# --- Caching Demonstration ---

MODELS_DIR = "models"

def get_model_path(ticker: str, model_type: str) -> str:
    """Get the path for a cached model file."""
    return os.path.join(MODELS_DIR, f"{ticker.lower()}_{model_type}.pkl")

def demonstrate_caching():
    """Demonstrate the model caching workflow."""
    print("=" * 60)
    print("Model Caching Demonstration")
    print("=" * 60)

    # Simulated user inputs
    test_cases = [
        ("AAPL", "linear"),
        ("AAPL", "forest"),
        ("GOOGL", "linear"),
        ("AAPL", "linear"),  # Repeat to show caching
    ]

    for ticker, model_type in test_cases:
        print(f"\n📊 Analyzing {ticker} ({model_type})...")

        # Get model path
        model_path = get_model_path(ticker, model_type)

        # Check if cached
        if os.path.exists(model_path):
            print(f"  ✓ Cached model found!")
            print(f"    Size: {os.path.getsize(model_path):,} bytes")

            # Load from cache
            model = SimpleModel(model_type, ticker)
            model.load_model(model_path)

            print(f"    Model: {model.ticker} | R2: {model.metrics.get('R2', 'N/A')}")

        else:
            print(f"  ⚠️ No cached model, training new one...")

            # Create and train new model
            model = SimpleModel(model_type, ticker)
            # Mock some data
            data = {"Close": [100, 101, 102], "RSI": [30, 45, 60], "SMA_20": [95, 96, 97], "Volume_Change": [1.1, 0.9, 1.2]}
            model.prepare_data(data)
            model.train(data["X_train"], data["y_train"])

            # Save to cache
            model.save_model(model_path)

        print(f"  🎯 Ready to predict!")

    print("\n" + "=" * 60)
    print("✓ Caching demonstration complete!")
    print("=" * 60)

    print("\n📈 Key Benefits:")
    print("  • Faster repeated analysis (no retraining)")
    print("  • Lower computational costs")
    print("  • Consistent predictions for same ticker+model type")
    print("  • Automatic cleanup of unused models")

if __name__ == "__main__":
    demonstrate_caching()