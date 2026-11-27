"""Acceptance and security boundaries for SMI machine learning."""

from pathlib import Path

import numpy as np
import pytest

from mission_control import smi_machine_learning_runtime as runtime


def test_all_video_algorithms_pass_synthetic_acceptance():
    receipt = runtime.synthetic_acceptance()
    assert receipt["passed"] is True
    assert len(receipt["checks"]) == 8
    assert all(receipt["checks"].values())
    assert receipt["production_fitness"] == "unknown"
    assert receipt["publication_granted"] is False


def test_bounded_local_evaluation_keeps_production_unknown():
    result = runtime.evaluate({
        "model": "linear",
        "features": [[0, 0], [1, 0], [0, 1], [1, 1]],
        "target": [2, 5, 1, 4],
    })
    assert result["metric"]["training_rmse"] < 1e-8
    assert result["production_fitness"] == "unknown"
    assert result["publication_granted"] is False


@pytest.mark.parametrize("payload", [
    {"model": "unknown", "features": [[1]], "target": [1]},
    {"model": "linear", "features": [[float("nan")]], "target": [1]},
    {"model": "linear", "features": [[1], [2]], "target": [1]},
])
def test_invalid_or_unbounded_requests_fail_closed(payload):
    with pytest.raises(ValueError):
        runtime.evaluate(payload)


def test_kmeans_is_unsupervised_and_bounded():
    points = np.vstack((np.zeros((5, 2)), np.ones((5, 2)) * 10))
    result = runtime.evaluate({"model": "kmeans", "features": points.tolist(), "clusters": 2})
    assert len(set(result["predictions"])) == 2
    assert result["training_only"] is True


def test_routes_are_founder_only_and_mutation_is_csrf_guarded():
    source = Path("mission_control/smi_machine_learning_views.py").read_text(
        encoding="utf-8"
    )
    assert source.count("founder_only=True") == 3
    assert '@bp.post("/ml/evaluate")' in source
    assert "web_security.csrf_valid(request)" in source
