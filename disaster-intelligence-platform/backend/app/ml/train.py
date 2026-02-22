"""
ML Training Script for XGBoost Risk Calibration Model
Generates training data from historical events + ward characteristics
Outputs: trained model, evaluation metrics (ROC-AUC, F1), model file
"""
import os
import pickle
import logging
from typing import Dict, List, Tuple
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)

try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import (
        roc_auc_score, f1_score, precision_score, recall_score,
        confusion_matrix, classification_report
    )
    HAS_ML_DEPS = True
except ImportError:
    HAS_ML_DEPS = False
    logger.warning("ML dependencies not installed. Training will fail.")

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


# Feature names (must match model.py)
FEATURE_NAMES = [
    "rainfall_intensity",
    "cumulative_rainfall_48h",
    "elevation_m",
    "mean_slope",
    "population_density",
    "infrastructure_density",
    "historical_frequency",
    "drainage_index",
    "impervious_surface_pct",
    "low_lying_index",
    "elderly_ratio",
]


def generate_training_data(wards: list, n_samples_per_ward: int = 50) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate training data from ward characteristics and historical patterns.
    
    Strategy:
    - For each ward, generate multiple weather scenarios
    - Label as flood=1 if weather + vulnerability exceed thresholds
    - Uses real ward properties (elevation, drainage, history) as features
    - Weather scenarios drawn from realistic Pune monsoon distributions
    """
    X = []
    y_flood = []

    for ward in wards:
        for _ in range(n_samples_per_ward):
            # Draw weather conditions from realistic Pune distributions
            # Monsoon: mean 15mm/h, can reach 100+mm/h during cloudbursts
            is_monsoon = np.random.random() < 0.4  # 40% monsoon samples
            
            if is_monsoon:
                rainfall = np.random.exponential(20) + np.random.uniform(5, 30)
                cumulative = rainfall * np.random.uniform(6, 48)
            else:
                rainfall = max(0, np.random.exponential(3) - 1)
                cumulative = rainfall * np.random.uniform(1, 24)

            elevation = ward.elevation_m or 560
            slope = ward.mean_slope or 2.0
            density = ward.population_density or 10000
            infra = ward.infrastructure_density or 3.0
            hist_freq = ward.historical_flood_frequency or 0.5
            drainage = ward.drainage_index or 0.5
            impervious = (ward.impervious_surface_pct or 50) / 100
            low_lying = ward.low_lying_index or 0.5
            elderly = ward.elderly_ratio or 0.1

            features = [
                rainfall,
                cumulative,
                elevation,
                slope,
                density,
                infra,
                hist_freq,
                drainage,
                impervious,
                low_lying,
                elderly,
            ]

            # Label: flood occurrence based on physics-informed rules
            flood_probability = 0.0
            
            # Heavy rainfall is the primary driver
            if rainfall > 50:
                flood_probability += 0.45
            elif rainfall > 25:
                flood_probability += 0.25
            elif rainfall > 10:
                flood_probability += 0.10
            
            # Cumulative rainfall
            if cumulative > 200:
                flood_probability += 0.20
            elif cumulative > 100:
                flood_probability += 0.10
            
            # Low elevation more vulnerable
            flood_probability += max(0, (580 - elevation) / 200) * 0.10
            
            # Poor drainage
            flood_probability += (1 - drainage) * 0.10
            
            # High impervious surface
            flood_probability += impervious * 0.05
            
            # Low-lying areas
            flood_probability += low_lying * 0.05
            
            # Historical precedent
            flood_probability += min(0.05, hist_freq * 0.03)
            
            # Add noise
            flood_probability += np.random.normal(0, 0.05)
            flood_probability = max(0, min(1, flood_probability))
            
            # Binary label
            label = 1 if flood_probability > 0.4 else 0

            X.append(features)
            y_flood.append(label)

    return np.array(X), np.array(y_flood)


def generate_heat_training_data(wards: list, n_samples_per_ward: int = 50) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate training data for heat risk model.

    Key insight: the 11-feature vector does NOT include temperature directly.
    So the model must learn which ward characteristics correlate with heat
    vulnerability.  We simulate diverse weather scenarios (some hot/dry,
    some mild/wet) and only label EXTREME combinations as heat=1.

    The training regime ensures:
    - Only ~25-35 % positive rate (not 60 %+)
    - Dry weather alone is NOT sufficient — ward must also be vulnerable
    - Ward-specific features (density, impervious, elderly) create spread
    """
    X = []
    y_heat = []

    for ward in wards:
        for _ in range(n_samples_per_ward):
            # ---------- Synthetic weather scenario ----------
            season_roll = np.random.random()
            if season_roll < 0.25:
                # Hot summer scenario — dry, intense heat
                rainfall = max(0, np.random.exponential(1.5) - 1)
                cumulative = rainfall * np.random.uniform(0.5, 6)
                temp_factor = 1.0  # full heat signal
            elif season_roll < 0.55:
                # Mild / winter — cool or moderate
                rainfall = max(0, np.random.exponential(4))
                cumulative = rainfall * np.random.uniform(2, 18)
                temp_factor = 0.0  # no heat signal
            else:
                # Monsoon — wet, moderate temps
                rainfall = np.random.exponential(15) + np.random.uniform(3, 25)
                cumulative = rainfall * np.random.uniform(6, 48)
                temp_factor = 0.0  # rain suppresses heat

            # ---------- Ward characteristics ----------
            elevation = ward.elevation_m or 560
            slope = ward.mean_slope or 2.0
            density = ward.population_density or 10000
            infra = ward.infrastructure_density or 3.0
            hist_freq = ward.historical_flood_frequency or 0.5
            drainage = ward.drainage_index or 0.5
            impervious = (ward.impervious_surface_pct or 50) / 100
            low_lying = ward.low_lying_index or 0.5
            elderly = ward.elderly_ratio or 0.1

            features = [
                rainfall, cumulative, elevation, slope, density,
                infra, hist_freq, drainage, impervious, low_lying, elderly,
            ]

            # ---------- Labeling (physics-informed) ----------
            heat_probability = 0.0

            # Temperature factor is the PRIMARY gate — only summer heat
            # contributes significantly.  Without it, ward characteristics
            # alone should NOT push a ward above the threshold.
            heat_probability += temp_factor * 0.35

            # Ward vulnerability adds to risk only during hot weather
            # (scaled by temp_factor so they're suppressed in cool weather)
            vuln_score = 0.0

            # Elderly vulnerability
            vuln_score += min(0.15, (elderly / 0.20) * 0.12)

            # Population density → urban heat island
            vuln_score += min(0.10, (density / 35000) * 0.08)

            # Impervious surface → heat absorption
            vuln_score += min(0.10, impervious * 0.08)

            # Poor drainage → correlates with poor infrastructure
            vuln_score += (1 - drainage) * 0.04

            # Low elevation → core urban area, hotter
            vuln_score += max(0, (580 - elevation) / 200) * 0.04

            # Historical heatwave days
            hw_days = ward.historical_heatwave_days or 12
            vuln_score += min(0.06, hw_days / 25 * 0.05)

            # Vulnerability only contributes meaningfully when it's hot
            heat_probability += vuln_score * (0.3 + 0.7 * temp_factor)

            # Dry conditions provide a small boost (not the dominant driver)
            if rainfall < 1.0 and cumulative < 3.0:
                heat_probability += 0.05 * temp_factor
            elif rainfall < 3.0:
                heat_probability += 0.02 * temp_factor

            # Add noise
            heat_probability += np.random.normal(0, 0.05)
            heat_probability = max(0, min(1, heat_probability))

            # Higher threshold — only truly hot + vulnerable combos are positive
            label = 1 if heat_probability > 0.50 else 0
            X.append(features)
            y_heat.append(label)

    return np.array(X), np.array(y_heat)


def train_model(wards: list, output_dir: str = None) -> Dict:
    """
    Train XGBoost flood prediction model
    Returns: evaluation metrics
    """
    if not HAS_ML_DEPS:
        return {"error": "ML dependencies not installed. Run: pip install xgboost scikit-learn shap"}

    output_dir = output_dir or os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Generating training data from {len(wards)} wards...")
    X, y = generate_training_data(wards, n_samples_per_ward=100)

    logger.info(f"Training set: {X.shape[0]} samples, {X.shape[1]} features")
    logger.info(f"Class balance: {np.sum(y == 1)}/{len(y)} positive ({100*np.mean(y):.1f}%)")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train XGBoost
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="auc",
        use_label_encoder=False,
        random_state=42,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # Evaluate
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
        "f1": round(f1_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred), 4),
        "recall": round(recall_score(y_test, y_pred), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "positive_rate": round(float(np.mean(y)), 4),
    }

    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="roc_auc")
    metrics["cv_auc_mean"] = round(float(np.mean(cv_scores)), 4)
    metrics["cv_auc_std"] = round(float(np.std(cv_scores)), 4)

    # Feature importance
    importance = dict(zip(FEATURE_NAMES, model.feature_importances_.tolist()))
    metrics["feature_importance"] = {k: round(v, 4) for k, v in
                                       sorted(importance.items(), key=lambda x: x[1], reverse=True)}

    # SHAP
    if HAS_SHAP:
        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_test[:100])
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            metrics["shap_importance"] = {
                FEATURE_NAMES[i]: round(float(mean_abs_shap[i]), 4)
                for i in range(len(FEATURE_NAMES))
            }
        except Exception as e:
            logger.warning(f"SHAP computation failed: {e}")

    # Save model
    flood_path = os.path.join(output_dir, "model_flood.pkl")
    with open(flood_path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Flood model saved to {flood_path}")

    # ---- Train Heat Model ----
    logger.info("Training heat risk model...")
    X_heat, y_heat = generate_heat_training_data(wards, n_samples_per_ward=100)
    logger.info(f"Heat training set: {X_heat.shape[0]} samples, positive rate: {100*np.mean(y_heat):.1f}%")

    X_train_h, X_test_h, y_train_h, y_test_h = train_test_split(
        X_heat, y_heat, test_size=0.2, random_state=42, stratify=y_heat
    )

    heat_model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="auc",
        use_label_encoder=False,
        random_state=42,
    )

    heat_model.fit(
        X_train_h, y_train_h,
        eval_set=[(X_test_h, y_test_h)],
        verbose=False,
    )

    y_pred_h = heat_model.predict(X_test_h)
    y_prob_h = heat_model.predict_proba(X_test_h)[:, 1]

    heat_metrics = {
        "roc_auc": round(roc_auc_score(y_test_h, y_prob_h), 4),
        "f1": round(f1_score(y_test_h, y_pred_h), 4),
        "precision": round(precision_score(y_test_h, y_pred_h), 4),
        "recall": round(recall_score(y_test_h, y_pred_h), 4),
    }
    metrics["heat_model"] = heat_metrics

    heat_path = os.path.join(output_dir, "model_heat.pkl")
    with open(heat_path, "wb") as f:
        pickle.dump(heat_model, f)
    logger.info(f"Heat model saved to {heat_path}")
    logger.info(f"Heat metrics: ROC-AUC={heat_metrics['roc_auc']}, F1={heat_metrics['f1']}")

    # Save metrics
    import json
    metrics_path = os.path.join(output_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)

    logger.info(f"Flood metrics: ROC-AUC={metrics['roc_auc']}, F1={metrics['f1']}, CV-AUC={metrics['cv_auc_mean']}±{metrics['cv_auc_std']}")

    return metrics


if __name__ == "__main__":
    """
    Run standalone training:
    python -m app.ml.train
    """
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    from app.db.database import SessionLocal
    from app.models.ward import Ward
    from app.services.ward_data_service import initialize_wards

    logging.basicConfig(level=logging.INFO)

    db = SessionLocal()
    try:
        initialize_wards(db)
        wards = db.query(Ward).all()

        if not wards:
            logger.error("No wards found. Initialize database first.")
            sys.exit(1)

        metrics = train_model(wards)

        if "error" in metrics:
            print(f"Error: {metrics['error']}")
            sys.exit(1)

        print("\n=== Training Results ===")
        print(f"ROC-AUC: {metrics['roc_auc']}")
        print(f"F1 Score: {metrics['f1']}")
        print(f"Precision: {metrics['precision']}")
        print(f"Recall: {metrics['recall']}")
        print(f"CV AUC: {metrics['cv_auc_mean']} ± {metrics['cv_auc_std']}")
        print(f"\nFeature Importance:")
        for feat, imp in metrics['feature_importance'].items():
            print(f"  {feat}: {imp}")

    finally:
        db.close()
