"""Training pipeline for primary and meta models."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


def train_primary_model(features: pd.DataFrame, labels: pd.Series) -> Pipeline:
    """Train a simple classifier as the primary signal model."""

    X_train, X_val, y_train, y_val = train_test_split(features, labels, test_size=0.2, shuffle=False)
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("rf", RandomForestClassifier(n_estimators=200, random_state=42)),
    ])
    pipeline.fit(X_train, y_train)
    score = pipeline.score(X_val, y_val)
    logger.info("Primary model validation accuracy: %.3f", score)
    return pipeline


def train_meta_model(features: pd.DataFrame, meta_labels: pd.Series) -> Pipeline:
    """Train meta-model to filter primary signals."""

    X_train, X_val, y_train, y_val = train_test_split(features, meta_labels, test_size=0.2, shuffle=False)
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("rf", RandomForestClassifier(n_estimators=100, random_state=24)),
    ])
    pipeline.fit(X_train, y_train)
    score = pipeline.score(X_val, y_val)
    logger.info("Meta model validation accuracy: %.3f", score)
    return pipeline


def save_model(model: Pipeline, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    logger.info("Model saved to %s", path)


def load_model(path: str | Path) -> Pipeline:
    return joblib.load(path)
