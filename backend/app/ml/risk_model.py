import pickle
from pathlib import Path
from typing import Dict, Optional
import numpy as np

MODEL_PATH = Path("models/risk_model.pkl")
SCALER_PATH = Path("models/risk_scaler.pkl")


_model = None
_scaler = None


def load_risk_model():
    """Load the pre-trained XGBoost risk model and scaler (cached)."""
    global _model, _scaler
    if _model is not None and _scaler is not None:
        return _model, _scaler

    if not MODEL_PATH.exists() or not SCALER_PATH.exists():
        return None, None
    
    try:
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
        with open(SCALER_PATH, "rb") as f:
            _scaler = pickle.load(f)
        return _model, _scaler
    except Exception:
        return None, None


def predict_risk(features: Dict) -> Optional[Dict]:
    """
    Predict cancer risk score from extracted report features.
    Returns probability and risk level.
    """
    model, scaler = load_risk_model()
    if model is None:
        return {"error": "Risk model not trained yet. Run the training notebook first."}

    try:
        # Convert features to array (model expects 30 UCI breast cancer features)
        feature_values = np.array(list(features.values())).reshape(1, -1)
        scaled = scaler.transform(feature_values)
        probability = model.predict_proba(scaled)[0]

        return {
            "risk_score": round(float(probability[1]) * 100, 1),
            "risk_level": "High" if probability[1] > 0.7 else "Medium" if probability[1] > 0.4 else "Low",
            "confidence": round(float(max(probability)) * 100, 1)
        }
    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}
