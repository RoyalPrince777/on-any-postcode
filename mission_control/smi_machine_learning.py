"""Small, readable implementations of the algorithms named in the source video.

These classes favour auditability and deterministic behaviour over performance.
They intentionally expose a compact scikit-learn-like ``fit``/``predict`` API.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _features(X: np.ndarray) -> np.ndarray:
    value = np.asarray(X, dtype=float)
    if value.ndim == 1:
        value = value.reshape(-1, 1)
    if value.ndim != 2 or value.shape[0] == 0:
        raise ValueError("X must be a non-empty 2D feature matrix")
    if not np.isfinite(value).all():
        raise ValueError("X contains NaN or infinite values")
    return value


def _target(y: np.ndarray, n: int, *, numeric: bool = False) -> np.ndarray:
    value = np.asarray(y, dtype=float if numeric else None).reshape(-1)
    if len(value) != n:
        raise ValueError("X and y must contain the same number of rows")
    if numeric and not np.isfinite(value).all():
        raise ValueError("y contains NaN or infinite values")
    return value


class StandardScaler:
    def fit(self, X: np.ndarray) -> StandardScaler:
        X = _features(X)
        self.mean_ = X.mean(axis=0)
        self.scale_ = X.std(axis=0)
        self.scale_[self.scale_ == 0] = 1.0
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        return (_features(X) - self.mean_) / self.scale_

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)


class LinearRegression:
    """Ordinary least squares using a stable pseudo-inverse."""

    def fit(self, X: np.ndarray, y: np.ndarray) -> LinearRegression:
        X = _features(X)
        y = _target(y, len(X), numeric=True)
        design = np.column_stack((np.ones(len(X)), X))
        coefficients = np.linalg.pinv(design) @ y
        self.intercept_ = float(coefficients[0])
        self.coef_ = coefficients[1:]
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return _features(X) @ self.coef_ + self.intercept_


class LogisticRegression:
    """Binary logistic regression trained by full-batch gradient descent."""

    def __init__(self, learning_rate: float = 0.1, epochs: int = 1500, l2: float = 0.0):
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.l2 = l2

    @staticmethod
    def _sigmoid(z: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-np.clip(z, -40, 40)))

    def fit(self, X: np.ndarray, y: np.ndarray) -> LogisticRegression:
        X = _features(X)
        y_raw = _target(y, len(X))
        self.classes_ = np.unique(y_raw)
        if len(self.classes_) != 2:
            raise ValueError("logistic regression requires exactly two classes")
        target = (y_raw == self.classes_[1]).astype(float)
        self.scaler_ = StandardScaler()
        scaled = self.scaler_.fit_transform(X)
        self.coef_ = np.zeros(scaled.shape[1])
        self.intercept_ = 0.0
        for _ in range(self.epochs):
            probabilities = self._sigmoid(scaled @ self.coef_ + self.intercept_)
            error = probabilities - target
            gradient = scaled.T @ error / len(scaled) + self.l2 * self.coef_
            self.coef_ -= self.learning_rate * gradient
            self.intercept_ -= self.learning_rate * float(error.mean())
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        scaled = self.scaler_.transform(X)
        positive = self._sigmoid(scaled @ self.coef_ + self.intercept_)
        return np.column_stack((1.0 - positive, positive))

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.classes_[(self.predict_proba(X)[:, 1] >= 0.5).astype(int)]


@dataclass
class _ClassificationNode:
    prediction: object
    feature: int | None = None
    threshold: float | None = None
    left: _ClassificationNode | None = None
    right: _ClassificationNode | None = None


class DecisionTreeClassifier:
    """CART-style classification tree using Gini impurity."""

    def __init__(self, max_depth: int = 5, min_samples_split: int = 2, max_features: int | None = None, random_state: int = 0):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.max_features = max_features
        self.random_state = random_state

    @staticmethod
    def _majority(y: np.ndarray):
        values, counts = np.unique(y, return_counts=True)
        return values[np.argmax(counts)]

    @staticmethod
    def _gini(y: np.ndarray) -> float:
        if len(y) == 0:
            return 0.0
        _, counts = np.unique(y, return_counts=True)
        probabilities = counts / len(y)
        return float(1.0 - np.sum(probabilities**2))

    def fit(self, X: np.ndarray, y: np.ndarray) -> DecisionTreeClassifier:
        X = _features(X)
        y = _target(y, len(X))
        self.classes_ = np.unique(y)
        self._rng = np.random.default_rng(self.random_state)
        self.root_ = self._grow(X, y, 0)
        return self

    def _grow(self, X: np.ndarray, y: np.ndarray, depth: int) -> _ClassificationNode:
        node = _ClassificationNode(prediction=self._majority(y))
        if depth >= self.max_depth or len(y) < self.min_samples_split or len(np.unique(y)) == 1:
            return node
        feature_count = X.shape[1]
        take = feature_count if self.max_features is None else min(self.max_features, feature_count)
        feature_indices = self._rng.choice(feature_count, take, replace=False)
        best = None
        best_score = self._gini(y)
        for feature in feature_indices:
            values = np.unique(X[:, feature])
            if len(values) < 2:
                continue
            thresholds = (values[:-1] + values[1:]) / 2.0
            for threshold in thresholds:
                left = X[:, feature] <= threshold
                if left.all() or (~left).all():
                    continue
                score = (left.sum() * self._gini(y[left]) + (~left).sum() * self._gini(y[~left])) / len(y)
                if score < best_score - 1e-12:
                    best_score = score
                    best = (feature, float(threshold), left)
        if best is None:
            return node
        feature, threshold, left = best
        node.feature, node.threshold = feature, threshold
        node.left = self._grow(X[left], y[left], depth + 1)
        node.right = self._grow(X[~left], y[~left], depth + 1)
        return node

    def _predict_row(self, row: np.ndarray):
        node = self.root_
        while node.feature is not None:
            node = node.left if row[node.feature] <= node.threshold else node.right
        return node.prediction

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.asarray([self._predict_row(row) for row in _features(X)])


class RandomForestClassifier:
    """Bootstrap aggregation of randomised decision trees."""

    def __init__(self, n_estimators: int = 25, max_depth: int = 6, max_features: int | None = None, random_state: int = 0):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.max_features = max_features
        self.random_state = random_state

    def fit(self, X: np.ndarray, y: np.ndarray) -> RandomForestClassifier:
        X = _features(X)
        y = _target(y, len(X))
        self.classes_ = np.unique(y)
        rng = np.random.default_rng(self.random_state)
        features = self.max_features or max(1, int(np.sqrt(X.shape[1])))
        self.trees_ = []
        for seed in rng.integers(0, 2**31 - 1, size=self.n_estimators):
            indices = rng.integers(0, len(X), size=len(X))
            tree = DecisionTreeClassifier(self.max_depth, max_features=features, random_state=int(seed))
            self.trees_.append(tree.fit(X[indices], y[indices]))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        votes = np.asarray([tree.predict(X) for tree in self.trees_])
        output = []
        for column in votes.T:
            values, counts = np.unique(column, return_counts=True)
            output.append(values[np.argmax(counts)])
        return np.asarray(output)


@dataclass
class _RegressionNode:
    value: float
    feature: int | None = None
    threshold: float | None = None
    left: _RegressionNode | None = None
    right: _RegressionNode | None = None


class _RegressionTree:
    def __init__(self, max_depth: int = 2, min_samples_split: int = 2):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split

    def fit(self, X: np.ndarray, y: np.ndarray) -> _RegressionTree:
        self.root_ = self._grow(_features(X), np.asarray(y, dtype=float), 0)
        return self

    def _grow(self, X: np.ndarray, y: np.ndarray, depth: int) -> _RegressionNode:
        node = _RegressionNode(float(y.mean()))
        if depth >= self.max_depth or len(y) < self.min_samples_split:
            return node
        best, best_loss = None, float(np.sum((y - y.mean()) ** 2))
        for feature in range(X.shape[1]):
            values = np.unique(X[:, feature])
            for threshold in (values[:-1] + values[1:]) / 2.0:
                left = X[:, feature] <= threshold
                if left.all() or (~left).all():
                    continue
                loss = np.sum((y[left] - y[left].mean()) ** 2) + np.sum((y[~left] - y[~left].mean()) ** 2)
                if loss < best_loss - 1e-12:
                    best_loss, best = float(loss), (feature, float(threshold), left)
        if best is None:
            return node
        feature, threshold, left = best
        node.feature, node.threshold = feature, threshold
        node.left = self._grow(X[left], y[left], depth + 1)
        node.right = self._grow(X[~left], y[~left], depth + 1)
        return node

    def _row(self, row: np.ndarray) -> float:
        node = self.root_
        while node.feature is not None:
            node = node.left if row[node.feature] <= node.threshold else node.right
        return node.value

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.asarray([self._row(row) for row in _features(X)])


class GradientBoostingRegressor:
    """Squared-error gradient boosting with shallow regression trees."""

    def __init__(self, n_estimators: int = 40, learning_rate: float = 0.1, max_depth: int = 2):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth

    def fit(self, X: np.ndarray, y: np.ndarray) -> GradientBoostingRegressor:
        X = _features(X)
        y = _target(y, len(X), numeric=True)
        self.initial_ = float(y.mean())
        prediction = np.full(len(y), self.initial_)
        self.trees_ = []
        for _ in range(self.n_estimators):
            tree = _RegressionTree(self.max_depth).fit(X, y - prediction)
            prediction += self.learning_rate * tree.predict(X)
            self.trees_.append(tree)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = _features(X)
        prediction = np.full(len(X), self.initial_)
        for tree in self.trees_:
            prediction += self.learning_rate * tree.predict(X)
        return prediction


class KNearestNeighborsClassifier:
    """Majority vote among the k closest Euclidean neighbours."""

    def __init__(self, n_neighbors: int = 5):
        if n_neighbors < 1:
            raise ValueError("n_neighbors must be positive")
        self.n_neighbors = n_neighbors

    def fit(self, X: np.ndarray, y: np.ndarray) -> KNearestNeighborsClassifier:
        X = _features(X)
        self.y_ = _target(y, len(X))
        self.scaler_ = StandardScaler()
        self.X_ = self.scaler_.fit_transform(X)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        queries = self.scaler_.transform(X)
        result = []
        for row in queries:
            distances = np.sum((self.X_ - row) ** 2, axis=1)
            neighbours = self.y_[np.argsort(distances)[: min(self.n_neighbors, len(self.X_))]]
            values, counts = np.unique(neighbours, return_counts=True)
            result.append(values[np.argmax(counts)])
        return np.asarray(result)


class KMeans:
    """Unsupervised k-means clustering with k-means++ initialisation."""

    def __init__(self, n_clusters: int = 3, max_iter: int = 200, tolerance: float = 1e-5, random_state: int = 0):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.tolerance = tolerance
        self.random_state = random_state

    def fit(self, X: np.ndarray) -> KMeans:
        X = _features(X)
        if self.n_clusters < 1 or self.n_clusters > len(X):
            raise ValueError("n_clusters must be between 1 and the number of rows")
        rng = np.random.default_rng(self.random_state)
        centres = [X[rng.integers(len(X))]]
        while len(centres) < self.n_clusters:
            distance = np.min(np.sum((X[:, None, :] - np.asarray(centres)[None, :, :]) ** 2, axis=2), axis=1)
            total = float(distance.sum())
            probabilities = distance / total if total else np.full(len(X), 1 / len(X))
            centres.append(X[rng.choice(len(X), p=probabilities)])
        centres = np.asarray(centres, dtype=float)
        for iteration in range(1, self.max_iter + 1):
            labels = np.argmin(np.sum((X[:, None, :] - centres[None, :, :]) ** 2, axis=2), axis=1)
            updated = np.asarray([X[labels == index].mean(axis=0) if np.any(labels == index) else centres[index] for index in range(self.n_clusters)])
            if np.max(np.abs(updated - centres)) <= self.tolerance:
                centres = updated
                break
            centres = updated
        self.cluster_centers_ = centres
        self.labels_ = self.predict(X)
        self.n_iter_ = iteration
        self.inertia_ = float(np.sum((X - centres[self.labels_]) ** 2))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = _features(X)
        return np.argmin(np.sum((X[:, None, :] - self.cluster_centers_[None, :, :]) ** 2, axis=2), axis=1)

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).labels_


class NeuralNetworkClassifier:
    """A configurable multilayer binary neural network trained by backpropagation."""

    def __init__(self, hidden_units: int | tuple[int, ...] = (8, 8), learning_rate: float = 0.1, epochs: int = 2500, random_state: int = 0):
        self.hidden_layers = (hidden_units,) if isinstance(hidden_units, int) else tuple(hidden_units)
        if not self.hidden_layers or any(width < 1 for width in self.hidden_layers):
            raise ValueError("at least one positive hidden-layer width is required")
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.random_state = random_state

    @staticmethod
    def _sigmoid(value: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-np.clip(value, -40, 40)))

    def fit(self, X: np.ndarray, y: np.ndarray) -> NeuralNetworkClassifier:
        X = _features(X)
        raw = _target(y, len(X))
        self.classes_ = np.unique(raw)
        if len(self.classes_) != 2:
            raise ValueError("neural network currently requires exactly two classes")
        target = (raw == self.classes_[1]).astype(float).reshape(-1, 1)
        self.scaler_ = StandardScaler()
        scaled = self.scaler_.fit_transform(X)
        rng = np.random.default_rng(self.random_state)
        widths = (scaled.shape[1],) + self.hidden_layers + (1,)
        self.weights_ = [rng.normal(0, np.sqrt(2 / widths[index]), (widths[index], widths[index + 1])) for index in range(len(widths) - 1)]
        self.biases_ = [np.zeros((1, width)) for width in widths[1:]]
        for _ in range(self.epochs):
            activations = [scaled]
            for weights, bias in zip(self.weights_[:-1], self.biases_[:-1]):
                activations.append(np.tanh(activations[-1] @ weights + bias))
            output = self._sigmoid(activations[-1] @ self.weights_[-1] + self.biases_[-1])
            delta = (output - target) / len(scaled)
            weight_gradients = [np.empty(0)] * len(self.weights_)
            bias_gradients = [np.empty(0)] * len(self.biases_)
            weight_gradients[-1] = activations[-1].T @ delta
            bias_gradients[-1] = delta.sum(axis=0, keepdims=True)
            for layer in range(len(self.weights_) - 2, -1, -1):
                delta = (delta @ self.weights_[layer + 1].T) * (1 - activations[layer + 1] ** 2)
                weight_gradients[layer] = activations[layer].T @ delta
                bias_gradients[layer] = delta.sum(axis=0, keepdims=True)
            for layer in range(len(self.weights_)):
                self.weights_[layer] -= self.learning_rate * weight_gradients[layer]
                self.biases_[layer] -= self.learning_rate * bias_gradients[layer]
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        scaled = self.scaler_.transform(X)
        activation = scaled
        for weights, bias in zip(self.weights_[:-1], self.biases_[:-1]):
            activation = np.tanh(activation @ weights + bias)
        positive = self._sigmoid(activation @ self.weights_[-1] + self.biases_[-1]).reshape(-1)
        return np.column_stack((1 - positive, positive))

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.classes_[(self.predict_proba(X)[:, 1] >= 0.5).astype(int)]
