"""Training pipeline for primary and meta models."""
from __future__ import annotations

import logging
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml_models.validation import purged_kfold

logger = logging.getLogger(__name__)


def _cross_validate_pipeline(
    pipeline_builder,
    features: pd.DataFrame,
    labels: pd.Series,
    timestamps: pd.Series | None,
    n_splits: int,
    embargo_pct: float,
    model_label: str,
) -> None:
    if timestamps is None:
        logger.warning(
            "%s training received no timestamps; skipping purged_kfold cross-validation.", model_label
        )
        return

    ts_index = pd.Series(timestamps).reset_index(drop=True)
    splits = purged_kfold(n_splits=n_splits, timestamps=ts_index, embargo_pct=embargo_pct)
    logger.info(
        "%s cross-validation using purged_kfold with %d splits and embargo_pct=%.3f",
        model_label,
        n_splits,
        embargo_pct,
    )

    accuracies = []
    pnl_proxies = []
    for fold_idx, (train_ts, val_ts) in enumerate(splits, start=1):
        train_mask = ts_index.isin(train_ts)
        val_mask = ts_index.isin(val_ts)

        X_train, X_val = features.loc[train_mask], features.loc[val_mask]
        y_train, y_val = labels.loc[train_mask], labels.loc[val_mask]

        pipeline = pipeline_builder()
        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_val)

        acc = accuracy_score(y_val, preds)
        accuracies.append(acc)

        pnl_proxy = (preds * y_val).mean() if set(y_val.unique()) <= {-1, 1} else float("nan")
        pnl_proxies.append(pnl_proxy)

        logger.info(
            "%s fold %d (purged_kfold): accuracy=%.3f, pnl_proxy=%.3f",
            model_label,
            fold_idx,
            acc,
            pnl_proxy,
        )

    if accuracies:
        logger.info(
            "%s purged_kfold CV accuracy mean=%.3f std=%.3f; pnl_proxy mean=%.3f",
            model_label,
            pd.Series(accuracies).mean(),
            pd.Series(accuracies).std(),
            pd.Series(pnl_proxies).mean(),
        )


def train_primary_model(
    features: pd.DataFrame,
    labels: pd.Series,
    timestamps: pd.Series | None = None,
    *,
    n_splits: int = 5,
    embargo_pct: float = 0.01,
) -> Pipeline:
    """Train a classifier as the primary signal model using Purged K-Fold CV.

    Implements López de Prado's Purged K-Fold with embargo to reduce leakage and
    overfitting. If ``timestamps`` are not provided, falls back to a single fit
    without cross-validation.
    """

    def _build_pipeline() -> Pipeline:
        return Pipeline([
            ("scaler", StandardScaler()),
            ("rf", RandomForestClassifier(n_estimators=200, random_state=42)),
        ])

    _cross_validate_pipeline(
        _build_pipeline, features, labels, timestamps, n_splits, embargo_pct, "Primary model"
    )

    final_pipeline = _build_pipeline()
    final_pipeline.fit(features, labels)
    logger.info("Primary model trained on full dataset after purged_kfold evaluation.")
    return final_pipeline


def train_meta_model(
    features: pd.DataFrame,
    meta_labels: pd.Series,
    timestamps: pd.Series | None = None,
    *,
    n_splits: int = 5,
    embargo_pct: float = 0.01,
) -> Pipeline:
    """Train meta-model to filter primary signals using Purged K-Fold CV.

    Implements López de Prado's Purged K-Fold with embargo to guard against
    leakage. If ``timestamps`` are omitted, the model trains without CV as a
    backward-compatible fallback.
    """

    def _build_pipeline() -> Pipeline:
        return Pipeline([
            ("scaler", StandardScaler()),
            ("rf", RandomForestClassifier(n_estimators=100, random_state=24)),
        ])

    _cross_validate_pipeline(
        _build_pipeline, features, meta_labels, timestamps, n_splits, embargo_pct, "Meta model"
    )

    final_pipeline = _build_pipeline()
    final_pipeline.fit(features, meta_labels)
    logger.info("Meta model trained on full dataset after purged_kfold evaluation.")
    return final_pipeline


def save_model(model: Pipeline, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    logger.info("Model saved to %s", path)


def load_model(path: str | Path) -> Pipeline:
    return joblib.load(path)
