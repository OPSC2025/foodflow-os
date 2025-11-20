"""
Anomaly detection ML service for sensor data.

Uses statistical methods and machine learning to detect anomalies in real-time sensor readings.
"""

import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src.contexts.plant_ops.domain.schemas import SensorReadingCreate


class AnomalyDetector:
    """
    Real-time anomaly detection for sensor data.
    
    Uses multiple detection methods:
    - Statistical thresholds (mean ± 3 std dev)
    - Isolation Forest for multivariate anomalies
    - Rate of change detection
    - Historical pattern comparison
    """
    
    def __init__(
        self,
        window_size: int = 100,
        contamination: float = 0.01,
        std_threshold: float = 3.0,
        rate_threshold: float = 5.0,
    ):
        """
        Initialize anomaly detector.
        
        Args:
            window_size: Number of readings to keep in memory for analysis
            contamination: Expected proportion of outliers (for Isolation Forest)
            std_threshold: Number of standard deviations for statistical detection
            rate_threshold: Maximum allowed rate of change per second
        """
        self.window_size = window_size
        self.contamination = contamination
        self.std_threshold = std_threshold
        self.rate_threshold = rate_threshold
        
        # Per-sensor data windows
        self._windows: Dict[UUID, List[Tuple[datetime, float]]] = {}
        
        # Per-sensor models
        self._models: Dict[UUID, IsolationForest] = {}
        self._scalers: Dict[UUID, StandardScaler] = {}
        
        # Per-sensor statistics
        self._stats: Dict[UUID, Dict[str, float]] = {}
    
    def detect(
        self,
        sensor_id: UUID,
        timestamp: datetime,
        value: float,
        sensor_min: Optional[float] = None,
        sensor_max: Optional[float] = None,
    ) -> Tuple[bool, float, str]:
        """
        Detect if a sensor reading is anomalous.
        
        Args:
            sensor_id: Sensor ID
            timestamp: Reading timestamp
            value: Sensor value
            sensor_min: Minimum expected value for sensor
            sensor_max: Maximum expected value for sensor
            
        Returns:
            Tuple of (is_anomaly, anomaly_score, reason)
        """
        # Initialize window if needed
        if sensor_id not in self._windows:
            self._windows[sensor_id] = []
        
        window = self._windows[sensor_id]
        
        # Check hard limits first
        if sensor_min is not None and value < sensor_min:
            return True, 1.0, f"Below minimum threshold ({sensor_min})"
        
        if sensor_max is not None and value > sensor_max:
            return True, 1.0, f"Above maximum threshold ({sensor_max})"
        
        # Need at least 10 readings for statistical analysis
        if len(window) < 10:
            window.append((timestamp, value))
            return False, 0.0, "Insufficient data"
        
        # Check rate of change
        if len(window) > 0:
            last_time, last_value = window[-1]
            time_diff = (timestamp - last_time).total_seconds()
            if time_diff > 0:
                rate = abs(value - last_value) / time_diff
                if rate > self.rate_threshold:
                    window.append((timestamp, value))
                    self._trim_window(sensor_id)
                    return True, 0.8, f"Excessive rate of change ({rate:.2f}/s)"
        
        # Statistical detection (mean ± 3 std dev)
        values = [v for _, v in window]
        mean = np.mean(values)
        std = np.std(values)
        
        if std > 0:
            z_score = abs(value - mean) / std
            if z_score > self.std_threshold:
                window.append((timestamp, value))
                self._trim_window(sensor_id)
                return True, min(z_score / 10, 1.0), f"Statistical outlier (z={z_score:.2f})"
        
        # Machine learning detection (if enough data)
        if len(window) >= 50:
            is_anomaly, score = self._ml_detect(sensor_id, value)
            if is_anomaly:
                window.append((timestamp, value))
                self._trim_window(sensor_id)
                return True, score, "ML model detected anomaly"
        
        # Add to window
        window.append((timestamp, value))
        self._trim_window(sensor_id)
        
        return False, 0.0, "Normal"
    
    def _ml_detect(self, sensor_id: UUID, value: float) -> Tuple[bool, float]:
        """
        Use Isolation Forest for anomaly detection.
        
        Args:
            sensor_id: Sensor ID
            value: Current value
            
        Returns:
            Tuple of (is_anomaly, score)
        """
        # Get or create model
        if sensor_id not in self._models:
            self._models[sensor_id] = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100,
            )
            self._scalers[sensor_id] = StandardScaler()
            
            # Train on historical data
            window = self._windows[sensor_id]
            values = np.array([[v] for _, v in window])
            
            # Scale and fit
            scaled = self._scalers[sensor_id].fit_transform(values)
            self._models[sensor_id].fit(scaled)
        
        # Predict
        model = self._models[sensor_id]
        scaler = self._scalers[sensor_id]
        
        scaled_value = scaler.transform([[value]])
        prediction = model.predict(scaled_value)[0]
        score = model.score_samples(scaled_value)[0]
        
        # Prediction is -1 for anomaly, 1 for normal
        is_anomaly = prediction == -1
        
        # Convert score to 0-1 range (more negative = more anomalous)
        anomaly_score = max(0, min(1, -score))
        
        return is_anomaly, anomaly_score
    
    def _trim_window(self, sensor_id: UUID) -> None:
        """Trim window to maximum size."""
        window = self._windows[sensor_id]
        if len(window) > self.window_size:
            self._windows[sensor_id] = window[-self.window_size:]
    
    def update_stats(self, sensor_id: UUID) -> Dict[str, float]:
        """
        Calculate and update statistics for a sensor.
        
        Args:
            sensor_id: Sensor ID
            
        Returns:
            Dictionary of statistics
        """
        if sensor_id not in self._windows or len(self._windows[sensor_id]) < 2:
            return {}
        
        values = [v for _, v in self._windows[sensor_id]]
        
        stats = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "median": float(np.median(values)),
            "q25": float(np.percentile(values, 25)),
            "q75": float(np.percentile(values, 75)),
            "count": len(values),
        }
        
        self._stats[sensor_id] = stats
        return stats
    
    def get_stats(self, sensor_id: UUID) -> Dict[str, float]:
        """Get cached statistics for a sensor."""
        return self._stats.get(sensor_id, {})
    
    def retrain(self, sensor_id: UUID) -> None:
        """
        Retrain ML model for a sensor.
        
        Useful after sensor recalibration or significant process changes.
        """
        if sensor_id in self._models:
            del self._models[sensor_id]
            del self._scalers[sensor_id]
    
    def save(self, path: Path) -> None:
        """
        Save detector state to disk.
        
        Args:
            path: Directory to save models
        """
        path.mkdir(parents=True, exist_ok=True)
        
        # Save models
        for sensor_id, model in self._models.items():
            model_path = path / f"{sensor_id}_model.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(model, f)
        
        # Save scalers
        for sensor_id, scaler in self._scalers.items():
            scaler_path = path / f"{sensor_id}_scaler.pkl"
            with open(scaler_path, "wb") as f:
                pickle.dump(scaler, f)
        
        # Save stats
        stats_path = path / "stats.pkl"
        with open(stats_path, "wb") as f:
            pickle.dump(self._stats, f)
    
    def load(self, path: Path) -> None:
        """
        Load detector state from disk.
        
        Args:
            path: Directory containing saved models
        """
        if not path.exists():
            return
        
        # Load models
        for model_path in path.glob("*_model.pkl"):
            sensor_id = UUID(model_path.stem.replace("_model", ""))
            with open(model_path, "rb") as f:
                self._models[sensor_id] = pickle.load(f)
        
        # Load scalers
        for scaler_path in path.glob("*_scaler.pkl"):
            sensor_id = UUID(scaler_path.stem.replace("_scaler", ""))
            with open(scaler_path, "rb") as f:
                self._scalers[sensor_id] = pickle.load(f)
        
        # Load stats
        stats_path = path / "stats.pkl"
        if stats_path.exists():
            with open(stats_path, "rb") as f:
                self._stats = pickle.load(f)


class AnomalyDetectionService:
    """
    Service for managing anomaly detection across all sensors.
    
    Provides high-level API for anomaly detection with persistence.
    """
    
    def __init__(self, model_dir: Optional[Path] = None):
        """
        Initialize anomaly detection service.
        
        Args:
            model_dir: Directory for saving/loading models
        """
        self.model_dir = model_dir or Path("/tmp/anomaly_models")
        self.detector = AnomalyDetector()
        
        # Load existing models
        if self.model_dir.exists():
            self.detector.load(self.model_dir)
    
    def check_reading(
        self,
        reading: SensorReadingCreate,
        sensor_min: Optional[float] = None,
        sensor_max: Optional[float] = None,
    ) -> SensorReadingCreate:
        """
        Check if a reading is anomalous and update it.
        
        Args:
            reading: Sensor reading to check
            sensor_min: Minimum expected value
            sensor_max: Maximum expected value
            
        Returns:
            Updated reading with anomaly information
        """
        is_anomaly, score, reason = self.detector.detect(
            reading.sensor_id,
            reading.timestamp,
            reading.value,
            sensor_min,
            sensor_max,
        )
        
        # Update reading
        reading.is_anomaly = is_anomaly
        reading.anomaly_score = score if is_anomaly else None
        
        # Add reason to metadata
        if reading.metadata is None:
            reading.metadata = {}
        reading.metadata["anomaly_reason"] = reason
        
        return reading
    
    def check_batch(
        self,
        readings: List[SensorReadingCreate],
        sensor_configs: Dict[UUID, Dict[str, Optional[float]]],
    ) -> List[SensorReadingCreate]:
        """
        Check a batch of readings for anomalies.
        
        Args:
            readings: List of sensor readings
            sensor_configs: Dictionary mapping sensor_id to {min, max} config
            
        Returns:
            Updated readings with anomaly information
        """
        updated = []
        
        for reading in readings:
            config = sensor_configs.get(reading.sensor_id, {})
            updated_reading = self.check_reading(
                reading,
                sensor_min=config.get("min"),
                sensor_max=config.get("max"),
            )
            updated.append(updated_reading)
        
        return updated
    
    def get_sensor_stats(self, sensor_id: UUID) -> Dict[str, float]:
        """Get statistics for a sensor."""
        return self.detector.get_stats(sensor_id)
    
    def update_sensor_stats(self, sensor_id: UUID) -> Dict[str, float]:
        """Update and get statistics for a sensor."""
        return self.detector.update_stats(sensor_id)
    
    def retrain_sensor(self, sensor_id: UUID) -> None:
        """Retrain model for a sensor."""
        self.detector.retrain(sensor_id)
    
    def save_models(self) -> None:
        """Save all models to disk."""
        self.detector.save(self.model_dir)
    
    def get_anomaly_summary(self) -> Dict[str, int]:
        """
        Get summary of anomaly detection across all sensors.
        
        Returns:
            Dictionary with counts and statistics
        """
        total_sensors = len(self.detector._windows)
        trained_models = len(self.detector._models)
        
        return {
            "total_sensors": total_sensors,
            "trained_models": trained_models,
            "window_size": self.detector.window_size,
        }


# Global service instance
_service: Optional[AnomalyDetectionService] = None


def get_anomaly_service() -> AnomalyDetectionService:
    """Get global anomaly detection service instance."""
    global _service
    if _service is None:
        _service = AnomalyDetectionService()
    return _service
