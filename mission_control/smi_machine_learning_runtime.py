"""Governed local machine-learning facade for the canonical SMI runtime.

Training is memory-only and bounded. This module does not publish, deploy,
spend credits, or claim that synthetic acceptance proves production fitness.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .smi_machine_learning import (
    DecisionTreeClassifier,
    GradientBoostingRegressor,
    KMeans,
    KNearestNeighborsClassifier,
    LinearRegression,
    LogisticRegression,
    NeuralNetworkClassifier,
    RandomForestClassifier,
)

MAX_ROWS = 2000
MAX_FEATURES = 64
MAX_PREDICTIONS_RETURNED = 100

SUPERVISED_MODELS = {
    "linear": LinearRegression,
    "logistic": LogisticRegression,
    "decision_tree": DecisionTreeClassifier,
    "random_forest": RandomForestClassifier,
    "gradient_boosting": GradientBoostingRegressor,
    "knn": KNearestNeighborsClassifier,
    "neural_network": NeuralNetworkClassifier,
}


def status() -> dict[str, Any]:
    return {
        "engine": "oap_smi_machine_learning",
        "algorithms": [*SUPERVISED_MODELS, "kmeans"],
        "algorithm_count": 8,
        "local_only": True,
        "external_api_calls": False,
        "production_fitness": "unknown",
        "redmi_a5_runtime": "unknown",
        "publication_granted": False,
        "founder_final": False,
    }


def _matrix(raw: object) -> np.ndarray:
    value = np.asarray(raw, dtype=float)
    if value.ndim != 2 or not 1 <= len(value) <= MAX_ROWS:
        raise ValueError("feature_matrix_invalid")
    if not 1 <= value.shape[1] <= MAX_FEATURES:
        raise ValueError("feature_count_invalid")
    if not np.isfinite(value).all():
        raise ValueError("features_non_finite")
    return value


def _labels(raw: object, rows: int) -> np.ndarray:
    value = np.asarray(raw).reshape(-1)
    if len(value) != rows:
        raise ValueError("target_length_invalid")
    return value


def evaluate(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("json_object_required")
    model_name = str(payload.get("model") or "").strip().lower()
    X = _matrix(payload.get("features"))
    if model_name == "kmeans":
        clusters = int(payload.get("clusters", 3))
        model = KMeans(n_clusters=clusters).fit(X)
        return {
            "model": model_name,
            "rows": len(X),
            "feature_count": X.shape[1],
            "metric": {"inertia": model.inertia_},
            "predictions": model.labels_[:MAX_PREDICTIONS_RETURNED].tolist(),
            "prediction_count": min(len(X), MAX_PREDICTIONS_RETURNED),
            "training_only": True,
            "production_fitness": "unknown",
            "publication_granted": False,
        }
    factory = SUPERVISED_MODELS.get(model_name)
    if factory is None:
        raise ValueError("model_unknown")
    y = _labels(payload.get("target"), len(X))
    model = factory().fit(X, y)
    predicted = model.predict(X)
    regression = model_name in {"linear", "gradient_boosting"}
    if regression:
        expected = y.astype(float)
        metric = {"training_rmse": float(np.sqrt(np.mean((predicted - expected) ** 2)))}
    else:
        metric = {"training_accuracy": float(np.mean(predicted == y))}
    return {
        "model": model_name,
        "rows": len(X),
        "feature_count": X.shape[1],
        "metric": metric,
        "predictions": predicted[:MAX_PREDICTIONS_RETURNED].tolist(),
        "prediction_count": min(len(X), MAX_PREDICTIONS_RETURNED),
        "training_only": True,
        "production_fitness": "unknown",
        "publication_granted": False,
    }


def synthetic_acceptance() -> dict[str, Any]:
    rng = np.random.default_rng(25)
    X = rng.normal(size=(140, 2))
    linear_y = 3.0 + 2.0 * X[:, 0] - X[:, 1]
    class_y = ((X[:, 0] * X[:, 1] > 0.1) | (X[:, 0] > 1.0)).astype(int)
    simple_y = (X[:, 0] - X[:, 1] > 0).astype(int)
    clusters = np.vstack((X[:45] - 5, X[45:90] + 5, X[90:] + (5, -5)))

    def accuracy(actual, predicted) -> float:
        return float(np.mean(np.asarray(actual) == np.asarray(predicted)))

    def rmse(actual, predicted) -> float:
        return float(np.sqrt(np.mean((np.asarray(actual) - np.asarray(predicted)) ** 2)))

    checks = {
        "linear": rmse(linear_y, LinearRegression().fit(X, linear_y).predict(X)) <= 1e-8,
        "logistic": accuracy(simple_y, LogisticRegression().fit(X, simple_y).predict(X)) >= 0.95,
        "decision_tree": accuracy(class_y, DecisionTreeClassifier(max_depth=6).fit(X, class_y).predict(X)) >= 0.95,
        "random_forest": accuracy(class_y, RandomForestClassifier(25, max_depth=6).fit(X, class_y).predict(X)) >= 0.94,
        "gradient_boosting": rmse(np.sin(X[:, 0]) + X[:, 1] ** 2, GradientBoostingRegressor(60).fit(X, np.sin(X[:, 0]) + X[:, 1] ** 2).predict(X)) <= 0.22,
        "knn": accuracy(class_y, KNearestNeighborsClassifier(5).fit(X, class_y).predict(X)) >= 0.90,
        "kmeans": len(np.unique(KMeans(3, random_state=2).fit_predict(clusters))) == 3,
        "neural_network": accuracy(class_y, NeuralNetworkClassifier((10, 6), epochs=3000, random_state=2).fit(X, class_y).predict(X)) >= 0.91,
    }
    return {
        "scope": "deterministic_synthetic_acceptance_only",
        "checks": checks,
        "passed": all(checks.values()),
        "production_fitness": "unknown",
        "redmi_a5_runtime": "unknown",
        "publication_granted": False,
    }
