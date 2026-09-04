"""Local-first OAP ISAC spatial-intelligence pipeline.

This module implements the software path needed to turn authorised 5G SRS/CSI-like
radio measurements into privacy-reduced Matrix RF events. It deliberately does not
claim a live radio testbed, licensed spectrum, centimetre accuracy or a trained
production model unless real calibration/radio evidence is supplied.

Raw I/Q stays inside the local service call. Public/Matrix-facing outputs contain
only bounded spatial abstractions, confidence, provenance and freshness metadata.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

FEATURE_DIMENSIONS = 32
MAX_SUBCARRIERS = 256
MAX_ANTENNAS = 16
MIN_CALIBRATION_POINTS = 3
DEFAULT_COLLISION_DISTANCE_M = 1.0


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _finite(value: object, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    mean = _mean(values)
    return _mean(tuple((item - mean) ** 2 for item in values))


def _quantile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(max(int(round((len(ordered) - 1) * fraction)), 0), len(ordered) - 1)
    return ordered[index]


def _vector_distance(left: Sequence[float], right: Sequence[float]) -> float:
    width = min(len(left), len(right))
    if width == 0:
        return float("inf")
    return math.sqrt(sum((left[index] - right[index]) ** 2 for index in range(width)))


def _normalise(values: Sequence[float]) -> tuple[float, ...]:
    if not values:
        return ()
    scale = max(max(abs(item) for item in values), 1e-9)
    return tuple(item / scale for item in values)


def _phase(i_value: float, q_value: float) -> float:
    return math.atan2(q_value, i_value)


def _inverse_dft_magnitudes(samples: Sequence[complex]) -> tuple[float, ...]:
    """Return bounded CIR magnitudes without requiring NumPy.

    The transform is intentionally capped because this is the deterministic fallback
    path. A hardware/GPU adapter may replace it later without changing the contract.
    """

    bounded = tuple(samples[:MAX_SUBCARRIERS])
    count = len(bounded)
    if count == 0:
        return ()
    output: list[float] = []
    for time_index in range(count):
        total = 0j
        for frequency_index, sample in enumerate(bounded):
            angle = 2.0 * math.pi * frequency_index * time_index / count
            total += sample * complex(math.cos(angle), math.sin(angle))
        output.append(abs(total / count))
    return tuple(output)


@dataclass(frozen=True)
class SRSFrame:
    """One authorised lower-layer radio measurement frame."""

    source: str
    device_ref: str
    cell_ref: str
    antenna_iq: tuple[tuple[tuple[float, float], ...], ...]
    timestamp: str = field(default_factory=_utc_iso)
    noise_power: float = 0.0
    sequence: int = 0
    source_kind: str = "srs_iq"
    authorised: bool = False

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> "SRSFrame":
        raw_antennas = payload.get("antenna_iq") or payload.get("antennas") or ()
        antennas: list[tuple[tuple[float, float], ...]] = []
        if isinstance(raw_antennas, Sequence) and not isinstance(raw_antennas, (str, bytes)):
            for raw_antenna in raw_antennas[:MAX_ANTENNAS]:
                samples: list[tuple[float, float]] = []
                if isinstance(raw_antenna, Sequence) and not isinstance(raw_antenna, (str, bytes)):
                    for raw_sample in raw_antenna[:MAX_SUBCARRIERS]:
                        if isinstance(raw_sample, Mapping):
                            samples.append(
                                (
                                    _finite(raw_sample.get("i")),
                                    _finite(raw_sample.get("q")),
                                )
                            )
                        elif (
                            isinstance(raw_sample, Sequence)
                            and not isinstance(raw_sample, (str, bytes))
                            and len(raw_sample) >= 2
                        ):
                            samples.append((_finite(raw_sample[0]), _finite(raw_sample[1])))
                if samples:
                    antennas.append(tuple(samples))
        return cls(
            source=str(payload.get("source") or "unknown")[:80],
            device_ref=str(payload.get("device_ref") or payload.get("ue_ref") or "anonymous-device")[:96],
            cell_ref=str(payload.get("cell_ref") or payload.get("gnb_ref") or "unknown-cell")[:96],
            antenna_iq=tuple(antennas),
            timestamp=str(payload.get("timestamp") or _utc_iso())[:64],
            noise_power=max(_finite(payload.get("noise_power")), 0.0),
            sequence=max(int(_finite(payload.get("sequence"))), 0),
            source_kind=str(payload.get("source_kind") or "srs_iq")[:40],
            authorised=bool(payload.get("authorised")),
        )

    @property
    def sample_count(self) -> int:
        return sum(len(antenna) for antenna in self.antenna_iq)


@dataclass(frozen=True)
class CalibrationPoint:
    label: str
    x_m: float
    y_m: float
    z_m: float
    zone: str
    features: tuple[float, ...]


@dataclass(frozen=True)
class PositionEstimate:
    device_ref: str
    x_m: float | None
    y_m: float | None
    z_m: float | None
    zone: str | None
    confidence: float
    model: str
    calibrated: bool
    timestamp: str
    provenance: str


@dataclass(frozen=True)
class MatrixRFEvent:
    event_type: str
    device_ref: str
    zone: str | None
    x_m: float | None
    y_m: float | None
    z_m: float | None
    confidence: float
    timestamp: str
    source: str
    source_kind: str
    raw_rf_included: bool = False
    biometric_identity: bool = False
    hidden_emotion_inference: bool = False


def extract_spatial_features(frame: SRSFrame) -> tuple[float, ...]:
    """Convert authorised SRS I/Q into a fixed 32-dimensional local feature vector."""

    if not frame.antenna_iq:
        return (0.0,) * FEATURE_DIMENSIONS

    antenna_power: list[float] = []
    antenna_phase_mean: list[float] = []
    cir_peaks: list[float] = []
    cir_centroids: list[float] = []
    cir_spreads: list[float] = []
    all_magnitudes: list[float] = []
    all_phases: list[float] = []

    for antenna in frame.antenna_iq:
        complex_samples = tuple(complex(i_value, q_value) for i_value, q_value in antenna)
        magnitudes = tuple(abs(sample) for sample in complex_samples)
        phases = tuple(_phase(sample.real, sample.imag) for sample in complex_samples)
        cir = _inverse_dft_magnitudes(complex_samples)
        power = _mean(tuple(item * item for item in magnitudes))
        antenna_power.append(power)
        antenna_phase_mean.append(_mean(phases))
        all_magnitudes.extend(magnitudes)
        all_phases.extend(phases)
        if cir:
            peak = max(cir)
            cir_peaks.append(peak)
            total = sum(cir) or 1.0
            centroid = sum(index * value for index, value in enumerate(cir)) / total
            spread = math.sqrt(
                sum(((index - centroid) ** 2) * value for index, value in enumerate(cir))
                / total
            )
            cir_centroids.append(centroid / max(len(cir), 1))
            cir_spreads.append(spread / max(len(cir), 1))

    magnitude_norm = _normalise(all_magnitudes)
    power_norm = _normalise(antenna_power)
    features = [
        _mean(magnitude_norm),
        math.sqrt(_variance(magnitude_norm)),
        min(magnitude_norm, default=0.0),
        max(magnitude_norm, default=0.0),
        _quantile(magnitude_norm, 0.25),
        _quantile(magnitude_norm, 0.50),
        _quantile(magnitude_norm, 0.75),
        _mean(all_phases) / math.pi,
        math.sqrt(_variance(all_phases)) / math.pi,
        _mean(power_norm),
        math.sqrt(_variance(power_norm)),
        min(power_norm, default=0.0),
        max(power_norm, default=0.0),
        _mean(_normalise(cir_peaks)),
        math.sqrt(_variance(_normalise(cir_peaks))),
        _mean(cir_centroids),
        math.sqrt(_variance(cir_centroids)),
        _mean(cir_spreads),
        math.sqrt(_variance(cir_spreads)),
        min(cir_centroids, default=0.0),
        max(cir_centroids, default=0.0),
        min(cir_spreads, default=0.0),
        max(cir_spreads, default=0.0),
        min(len(frame.antenna_iq) / MAX_ANTENNAS, 1.0),
        min(frame.sample_count / (MAX_ANTENNAS * MAX_SUBCARRIERS), 1.0),
        min(frame.noise_power, 1.0),
        _mean(tuple(abs(item) for item in antenna_phase_mean)) / math.pi,
        math.sqrt(_variance(antenna_phase_mean)) / math.pi,
    ]
    for index in range(4):
        features.append(power_norm[index] if index < len(power_norm) else 0.0)
    return tuple(_finite(item) for item in features[:FEATURE_DIMENSIONS])


class LocalPositioningModel:
    """Deterministic local calibration model with no external provider dependency."""

    def __init__(self) -> None:
        self._points: list[CalibrationPoint] = []

    @property
    def calibration_count(self) -> int:
        return len(self._points)

    @property
    def trained(self) -> bool:
        return self.calibration_count >= MIN_CALIBRATION_POINTS

    def add_calibration(
        self,
        *,
        label: str,
        x_m: float,
        y_m: float,
        z_m: float = 0.0,
        zone: str = "",
        features: Iterable[float],
    ) -> CalibrationPoint:
        point = CalibrationPoint(
            label=str(label)[:80],
            x_m=_finite(x_m),
            y_m=_finite(y_m),
            z_m=_finite(z_m),
            zone=str(zone)[:80],
            features=tuple(_finite(item) for item in features)[:FEATURE_DIMENSIONS],
        )
        if len(point.features) != FEATURE_DIMENSIONS:
            raise ValueError("calibration_feature_dimension_mismatch")
        self._points.append(point)
        return point

    def predict(self, frame: SRSFrame, features: Sequence[float]) -> PositionEstimate:
        if not self.trained:
            return PositionEstimate(
                device_ref=frame.device_ref,
                x_m=None,
                y_m=None,
                z_m=None,
                zone=None,
                confidence=0.0,
                model="local_knn_calibration_v1",
                calibrated=False,
                timestamp=frame.timestamp,
                provenance=frame.source,
            )
        ranked = sorted(
            ((_vector_distance(features, point.features), point) for point in self._points),
            key=lambda item: item[0],
        )[: min(3, len(self._points))]
        weights = tuple(1.0 / max(distance, 1e-6) for distance, _point in ranked)
        total_weight = sum(weights) or 1.0
        x_m = sum(weight * point.x_m for weight, (_distance, point) in zip(weights, ranked)) / total_weight
        y_m = sum(weight * point.y_m for weight, (_distance, point) in zip(weights, ranked)) / total_weight
        z_m = sum(weight * point.z_m for weight, (_distance, point) in zip(weights, ranked)) / total_weight
        nearest_distance, nearest = ranked[0]
        confidence = max(0.0, min(1.0, 1.0 / (1.0 + nearest_distance)))
        return PositionEstimate(
            device_ref=frame.device_ref,
            x_m=round(x_m, 3),
            y_m=round(y_m, 3),
            z_m=round(z_m, 3),
            zone=nearest.zone or nearest.label,
            confidence=round(confidence, 4),
            model="local_knn_calibration_v1",
            calibrated=True,
            timestamp=frame.timestamp,
            provenance=frame.source,
        )


class ISACSpatialService:
    """Governed end-to-end ISAC software service for Matrix RF."""

    def __init__(self) -> None:
        self.model = LocalPositioningModel()
        self._last_features: dict[str, tuple[float, ...]] = {}
        self._last_estimates: dict[str, PositionEstimate] = {}
        self._events: list[MatrixRFEvent] = []
        self._zone_counts: dict[str, int] = {}

    def add_calibration_from_frame(
        self,
        frame: SRSFrame,
        *,
        label: str,
        x_m: float,
        y_m: float,
        z_m: float = 0.0,
        zone: str = "",
    ) -> CalibrationPoint:
        if not frame.authorised:
            raise PermissionError("rf_measurement_not_authorised")
        return self.model.add_calibration(
            label=label,
            x_m=x_m,
            y_m=y_m,
            z_m=z_m,
            zone=zone,
            features=extract_spatial_features(frame),
        )

    def ingest(self, frame: SRSFrame) -> dict[str, object]:
        if not frame.authorised:
            raise PermissionError("rf_measurement_not_authorised")
        if frame.sample_count == 0:
            raise ValueError("rf_measurement_empty")
        features = extract_spatial_features(frame)
        previous = self._last_features.get(frame.device_ref)
        change_score = 0.0
        if previous is not None:
            change_score = min(_vector_distance(features, previous) / math.sqrt(FEATURE_DIMENSIONS), 1.0)
        estimate = self.model.predict(frame, features)
        self._last_features[frame.device_ref] = features
        self._last_estimates[frame.device_ref] = estimate
        event = MatrixRFEvent(
            event_type="position_estimate" if estimate.calibrated else "rf_spatial_observation",
            device_ref=frame.device_ref,
            zone=estimate.zone,
            x_m=estimate.x_m,
            y_m=estimate.y_m,
            z_m=estimate.z_m,
            confidence=estimate.confidence,
            timestamp=frame.timestamp,
            source=frame.source,
            source_kind=frame.source_kind,
        )
        self._events.append(event)
        self._events = self._events[-100:]
        if estimate.zone:
            self._zone_counts[estimate.zone] = self._zone_counts.get(estimate.zone, 0) + 1
        return {
            "matrix_event": event,
            "estimate": estimate,
            "feature_dimension": len(features),
            "change_score": round(change_score, 4),
            "object_or_environment_change_detected": change_score >= 0.20,
            "raw_rf_retained_in_event": False,
            "guardian_rf_passed": True,
        }

    def collision_risks(self, threshold_m: float = DEFAULT_COLLISION_DISTANCE_M) -> tuple[dict[str, object], ...]:
        located = [item for item in self._last_estimates.values() if item.calibrated]
        risks: list[dict[str, object]] = []
        for index, left in enumerate(located):
            for right in located[index + 1 :]:
                if left.x_m is None or left.y_m is None or right.x_m is None or right.y_m is None:
                    continue
                distance = math.hypot(left.x_m - right.x_m, left.y_m - right.y_m)
                if distance <= threshold_m:
                    risks.append(
                        {
                            "left_device_ref": left.device_ref,
                            "right_device_ref": right.device_ref,
                            "distance_m": round(distance, 3),
                            "threshold_m": threshold_m,
                            "confidence": round(min(left.confidence, right.confidence), 4),
                        }
                    )
        return tuple(risks)

    def snapshot(self) -> dict[str, object]:
        estimates = tuple(
            {
                "device_ref": item.device_ref,
                "x_m": item.x_m,
                "y_m": item.y_m,
                "z_m": item.z_m,
                "zone": item.zone,
                "confidence": item.confidence,
                "calibrated": item.calibrated,
                "timestamp": item.timestamp,
            }
            for item in self._last_estimates.values()
        )
        events = tuple(
            {
                "event_type": item.event_type,
                "device_ref": item.device_ref,
                "zone": item.zone,
                "x_m": item.x_m,
                "y_m": item.y_m,
                "z_m": item.z_m,
                "confidence": item.confidence,
                "timestamp": item.timestamp,
                "source": item.source,
                "source_kind": item.source_kind,
                "raw_rf_included": item.raw_rf_included,
            }
            for item in self._events[-20:]
        )
        return {
            "software_ready": True,
            "feature_dimensions": FEATURE_DIMENSIONS,
            "calibration_points": self.model.calibration_count,
            "model_trained": self.model.trained,
            "active_device_count": len(self._last_estimates),
            "estimates": estimates,
            "occupancy_heatmap": dict(sorted(self._zone_counts.items())),
            "collision_risks": self.collision_risks(),
            "recent_events": events,
            "raw_rf_in_matrix": False,
            "biometric_identity": False,
            "covert_person_tracking": False,
            "human_authority_final": True,
        }
