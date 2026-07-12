# ============================================================
# src/model.py — Machine Learning Model Layer
# ============================================================
# Responsibility: Train ML models, make predictions, evaluate
# performance, and save/load trained models.
#
# This module implements:
#   1. Train/test split (time-series aware — no data leakage!)
#   2. Feature scaling (StandardScaler)
#   3. Linear Regression (simple, interpretable baseline)
#   4. Random Forest (powerful, handles non-linear patterns)
#   5. Model evaluation metrics
#   6. Save/load trained models to disk
# ============================================================

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    mean_absolute_error,      # MAE: average error in dollars
    mean_squared_error,       # MSE: penalizes large errors more
    r2_score,                 # R²: how well the model explains variance
)
import joblib
import os


class StockPredictor:
    """
    A class that wraps the entire ML pipeline:
    data splitting, scaling, training, prediction, and evaluation.

    Why a class instead of loose functions?
    ----------------------------------------
    The scaler and model need to be used TOGETHER — the scaler
    that was fit on training data MUST be the same scaler used
    on new predictions. A class bundles them together so they
    can't get separated. This is called "encapsulation."

    Attributes
    ----------
    model : sklearn estimator
        The trained ML model (LinearRegression or RandomForest).
    scaler : StandardScaler
        The fitted scaler (transforms features to zero mean, unit variance).
    feature_names : list
        Names of the features the model was trained on.
    metrics : dict
        Evaluation metrics from the test set.
    """

    def __init__(self, model_type: str = "forest"):
        """
        Initialize the predictor.

        Parameters
        ----------
        model_type : str
            Which algorithm to use:
            - "linear" : Linear Regression (simple, fast, interpretable)
            - "forest" : Random Forest (powerful, handles non-linear patterns)
        """
        if model_type not in ("linear", "forest"):
            raise ValueError(f"model_type must be 'linear' or 'forest', got '{model_type}'")
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.metrics = {}

    def prepare_data(
        self, df: pd.DataFrame, target_col: str = "Target", test_size: float = 0.2
    ) -> tuple:
        """
        Split data into training and testing sets (time-series aware).

        IMPORTANT: For time-series data, we do NOT use random splitting!
        Random splitting would let the model "peek" at future data during
        training — this is called "data leakage" and inflates accuracy.

        Instead, we use the EARLIEST 80% for training and the LATEST 20%
        for testing. This simulates real-world usage: we train on the past
        and predict the future.

        Parameters
        ----------
        df : pd.DataFrame
            Feature-engineered DataFrame with a Target column.
        target_col : str
            Name of the column to predict. Default is "Target".
        test_size : float
            Fraction of data to use for testing. Default is 0.2 (20%).

        Returns
        -------
        tuple : (X_train, X_test, y_train, y_test)
            X = features (inputs), y = target (what we predict).
        """
        # --- Separate features (X) and target (y) ---
        # X = everything the model uses to make predictions
        # y = the correct answer (what we're trying to predict)
        self.feature_names = [col for col in df.columns if col != target_col]
        X = df[self.feature_names].values  # .values converts to numpy array
        y = df[target_col].values

        # --- Time-series split ---
        # Calculate where to cut: 80% train, 20% test
        split_index = int(len(X) * (1 - test_size))

        X_train = X[:split_index]   # First 80% of rows
        X_test = X[split_index:]    # Last 20% of rows
        y_train = y[:split_index]
        y_test = y[split_index:]

        print(f"[MODEL] Data split:")
        print(f"  Training set: {len(X_train)} rows (oldest data)")
        print(f"  Testing set:  {len(X_test)} rows (most recent data)")

        # --- Scale the features ---
        # StandardScaler transforms each feature to have:
        #   mean = 0, standard deviation = 1
        #
        # Formula: scaled_value = (value - mean) / std
        #
        # CRITICAL: We .fit_transform() on TRAINING data only,
        # then .transform() on test data using the SAME parameters.
        # If we fit on test data too, we'd leak test statistics
        # into the model — another form of data leakage!
        X_train = self.scaler.fit_transform(X_train)
        X_test = self.scaler.transform(X_test)  # NOT fit_transform!

        return X_train, X_test, y_train, y_test

    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """
        Train the selected ML model.

        Supports two algorithms:
        - Linear Regression: Finds the best straight line/hyperplane.
        - Random Forest: Builds 100 decision trees that each vote.

        Parameters
        ----------
        X_train : np.ndarray
            Scaled training features (2D array: rows x features).
        y_train : np.ndarray
            Training target values (1D array: correct answers).
        """
        if self.model_type == "linear":
            print("[MODEL] Training Linear Regression...")
            self.model = LinearRegression()
        else:
            print("[MODEL] Training Random Forest (100 trees)...")
            # Random Forest parameters explained:
            #   n_estimators=100   → Build 100 decision trees
            #   max_depth=15       → Each tree can be at most 15 levels deep
            #                        (prevents overfitting by limiting complexity)
            #   min_samples_split=5 → A node must have at least 5 samples to split
            #                        (prevents trees from memorizing noise)
            #   random_state=42    → Makes results reproducible (same "random" every time)
            #   n_jobs=-1          → Use all CPU cores for parallel training
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1,
            )

        # .fit() is where the actual LEARNING happens.
        self.model.fit(X_train, y_train)
        print("[MODEL] Training complete!")

        # Show what the model learned
        self._print_feature_importance()

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using the trained model.

        Parameters
        ----------
        X : np.ndarray
            Scaled feature array (can be one row or many rows).

        Returns
        -------
        np.ndarray
            Predicted values (next-day close prices).
        """
        if self.model is None:
            raise RuntimeError("Model not trained yet! Call .train() first.")
        return self.model.predict(X)

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """
        Evaluate the model on the test set and return metrics.

        Metrics explained:
        - MAE (Mean Absolute Error): Average error in dollars.
          "On average, the prediction is off by $X."

        - RMSE (Root Mean Squared Error): Like MAE but penalizes
          large errors more. Useful for catching outlier predictions.

        - R² Score: How much of the variance the model explains.
          1.0 = perfect, 0.0 = no better than guessing the average.

        - MAPE (Mean Absolute Percentage Error): Error as a percentage.
          "On average, the prediction is off by X%."

        Parameters
        ----------
        X_test : np.ndarray
            Scaled test features.
        y_test : np.ndarray
            Actual test target values (the correct answers).

        Returns
        -------
        dict
            Dictionary of evaluation metrics.
        """
        predictions = self.predict(X_test)

        # Calculate metrics
        mae = mean_absolute_error(y_test, predictions)
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        r2 = r2_score(y_test, predictions)
        mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100

        self.metrics = {
            "MAE": round(mae, 2),
            "RMSE": round(rmse, 2),
            "R2": round(r2, 4),
            "MAPE": round(mape, 2),
        }

        # Print a readable report
        print("\n" + "=" * 50)
        print("MODEL EVALUATION REPORT")
        print("=" * 50)
        print(f"  MAE  (Mean Absolute Error):    ${mae:.2f}")
        print(f"  RMSE (Root Mean Squared Error): ${rmse:.2f}")
        print(f"  R2   (R-Squared Score):         {r2:.4f}")
        print(f"  MAPE (Mean Abs % Error):        {mape:.2f}%")
        print("=" * 50)

        # Interpretation
        if r2 > 0.9:
            print("  Interpretation: Excellent fit!")
        elif r2 > 0.7:
            print("  Interpretation: Good fit.")
        elif r2 > 0.5:
            print("  Interpretation: Moderate fit — room for improvement.")
        else:
            print("  Interpretation: Poor fit — consider more features or a different model.")

        # Show some sample predictions vs actuals
        print(f"\n  Sample Predictions vs Actual (last 5 test rows):")
        print(f"  {'Actual':>10s}  {'Predicted':>10s}  {'Error':>10s}")
        print(f"  {'-'*10}  {'-'*10}  {'-'*10}")
        for actual, pred in zip(y_test[-5:], predictions[-5:]):
            error = pred - actual
            print(f"  ${actual:>9.2f}  ${pred:>9.2f}  ${error:>+9.2f}")

        return self.metrics

    def predict_next_day(self, latest_features: pd.DataFrame) -> dict:
        """
        Predict the next trading day's close price.

        This is the function the Streamlit dashboard will call
        to show the user the predicted price.

        Parameters
        ----------
        latest_features : pd.DataFrame
            A single-row DataFrame with the most recent day's features.

        Returns
        -------
        dict
            Contains 'predicted_price', 'confidence', and 'model_type'.
        """
        if self.model is None:
            raise RuntimeError("Model not trained yet!")

        # Scale the features using the same scaler from training
        feature_values = latest_features[self.feature_names].values
        scaled_features = self.scaler.transform(feature_values)

        # Make prediction
        predicted_price = self.model.predict(scaled_features)[0]

        # Calculate a simple confidence score based on model metrics
        # This uses MAPE — lower error = higher confidence
        mape = self.metrics.get("MAPE", 10)
        confidence = max(0, min(100, 100 - mape))  # Clamp between 0-100

        return {
            "predicted_price": round(predicted_price, 2),
            "confidence": round(confidence, 1),
            "model_type": self.model_type,
        }

    # ==============================================================
    # Feature Importance — What did the model learn?
    # ==============================================================

    def _print_feature_importance(self) -> None:
        """Print the top features the model relies on."""
        importance = self.get_feature_importance()
        print(f"  Top 5 most important features:")
        for name, score in importance[:5]:
            print(f"    - {name}: {score:.4f}")

    def get_feature_importance(self) -> list:
        """
        Get feature importances ranked by magnitude.

        For Linear Regression: uses absolute coefficient values.
        For Random Forest: uses built-in feature_importances_
            (measures how much each feature reduces prediction error).

        Returns
        -------
        list of (name, importance) tuples, sorted descending.
        """
        if self.model is None:
            return []

        if self.model_type == "linear":
            # Linear Regression: importance = absolute weight value
            importances = np.abs(self.model.coef_)
        else:
            # Random Forest: has a built-in .feature_importances_ attribute
            # This measures how much each feature reduces the prediction
            # error across all 100 trees. Higher = more important.
            importances = self.model.feature_importances_

        # Pair names with importances and sort
        paired = list(zip(self.feature_names, importances))
        paired.sort(key=lambda x: x[1], reverse=True)
        return paired

    # ==============================================================
    # Save & Load — Persist trained models to disk
    # ==============================================================

    def save_model(self, filepath: str = "models/stock_predictor.pkl") -> None:
        """
        Save the trained model, scaler, and metadata to disk.

        We use joblib (not pickle) because it's optimized for
        large numpy arrays — scikit-learn models contain many.

        What gets saved:
        - The trained model (weights/trees)
        - The fitted scaler (mean/std statistics)
        - Feature names (so we know which columns to expect)
        - Evaluation metrics
        - Model type identifier

        Parameters
        ----------
        filepath : str
            Path to save the .pkl file.
        """
        if self.model is None:
            raise RuntimeError("No trained model to save!")

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Bundle everything into a single dictionary
        bundle = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "metrics": self.metrics,
            "model_type": self.model_type,
        }

        # joblib.dump() serializes the Python object to a file
        joblib.dump(bundle, filepath)
        print(f"[MODEL] Saved to {filepath}")

    def load_model(self, filepath: str = "models/stock_predictor.pkl") -> None:
        """
        Load a previously saved model from disk.

        Parameters
        ----------
        filepath : str
            Path to the .pkl file.

        Raises
        ------
        FileNotFoundError
            If the model file doesn't exist.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"No saved model found at '{filepath}'")

        # joblib.load() deserializes the file back into Python objects
        bundle = joblib.load(filepath)

        self.model = bundle["model"]
        self.scaler = bundle["scaler"]
        self.feature_names = bundle["feature_names"]
        self.metrics = bundle["metrics"]
        self.model_type = bundle["model_type"]

        print(f"[MODEL] Loaded {self.model_type} model from {filepath}")
        print(f"  Features: {len(self.feature_names)}")
        print(f"  Metrics: R2={self.metrics.get('R2', 'N/A')}, "
              f"MAE=${self.metrics.get('MAE', 'N/A')}")


# ============================================================
# Test: Compare Linear Regression vs Random Forest
# ============================================================
if __name__ == "__main__":
    from data_fetcher import get_stock_data
    from preprocessor import preprocess_stock_data
    from feature_engineer import add_features

    # --- Prepare data (shared by both models) ---
    print("=" * 60)
    print("MODEL COMPARISON: Linear Regression vs Random Forest")
    print("=" * 60)

    raw = get_stock_data("AAPL", period_years=2)
    clean = preprocess_stock_data(raw)
    featured = add_features(clean)

    # --- Test 1: Linear Regression ---
    print("\n" + "#" * 60)
    print("# MODEL 1: LINEAR REGRESSION")
    print("#" * 60)
    lr_predictor = StockPredictor(model_type="linear")
    X_train, X_test, y_train, y_test = lr_predictor.prepare_data(featured)
    lr_predictor.train(X_train, y_train)
    lr_metrics = lr_predictor.evaluate(X_test, y_test)

    # --- Test 2: Random Forest ---
    print("\n" + "#" * 60)
    print("# MODEL 2: RANDOM FOREST")
    print("#" * 60)
    rf_predictor = StockPredictor(model_type="forest")
    X_train, X_test, y_train, y_test = rf_predictor.prepare_data(featured)
    rf_predictor.train(X_train, y_train)
    rf_metrics = rf_predictor.evaluate(X_test, y_test)

    # --- Side-by-side comparison ---
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"  {'Metric':<10s}  {'Linear Reg':>12s}  {'Random Forest':>14s}  {'Winner':>10s}")
    print(f"  {'-'*10}  {'-'*12}  {'-'*14}  {'-'*10}")
    for metric in ["MAE", "RMSE", "R2", "MAPE"]:
        lr_val = lr_metrics[metric]
        rf_val = rf_metrics[metric]
        # For R2, higher is better. For everything else, lower is better.
        if metric == "R2":
            winner = "Forest" if rf_val > lr_val else "Linear"
        else:
            winner = "Forest" if rf_val < lr_val else "Linear"
        print(f"  {metric:<10s}  {lr_val:>12}  {rf_val:>14}  {winner:>10}")

    # --- Save the better model ---
    best = lr_predictor if lr_metrics["R2"] >= rf_metrics["R2"] else rf_predictor
    print(f"\n  Saving the winner ({best.model_type}) to disk...")
    best.save_model("models/stock_predictor.pkl")

    # --- Test loading ---
    print("\n--- Testing model load ---")
    loaded = StockPredictor()
    loaded.load_model("models/stock_predictor.pkl")

    # Predict with the loaded model
    latest = featured.iloc[[-1]]
    result = loaded.predict_next_day(latest)
    print(f"\n[PREDICTION] Next day predicted close: ${result['predicted_price']}")
    print(f"[PREDICTION] Confidence: {result['confidence']}%")
    print(f"[PREDICTION] Model used: {result['model_type']}")
