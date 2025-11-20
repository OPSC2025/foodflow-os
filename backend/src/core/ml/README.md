# FoodFlow OS - Machine Learning Module

This module provides ML capabilities for the FoodFlow OS platform, starting with real-time anomaly detection for sensor data.

## Anomaly Detection

The anomaly detection system uses multiple methods to identify unusual sensor readings in real-time:

### Detection Methods

1. **Hard Limit Checking**
   - Compares readings against configured min/max thresholds
   - Immediate detection with 100% confidence
   - Configured per sensor in the database

2. **Statistical Analysis**
   - Uses mean ± 3 standard deviations (z-score)
   - Requires at least 10 historical readings
   - Adapts to normal operating ranges automatically

3. **Rate of Change Detection**
   - Monitors how quickly values change over time
   - Detects sudden spikes or drops
   - Configurable threshold (default: 5 units/second)

4. **Machine Learning (Isolation Forest)**
   - Unsupervised learning for multivariate anomalies
   - Trains automatically on historical data
   - Requires at least 50 readings for training
   - Updates continuously as new data arrives

### Usage

#### Basic Usage

```python
from src.core.ml.anomaly_detection import get_anomaly_service
from src.contexts.plant_ops.domain.schemas import SensorReadingCreate
from datetime import datetime
from uuid import uuid4

# Get service instance
service = get_anomaly_service()

# Create a reading
reading = SensorReadingCreate(
    sensor_id=uuid4(),
    timestamp=datetime.utcnow(),
    value=75.5,
    batch_id=None,
)

# Check for anomalies
updated_reading = service.check_reading(
    reading,
    sensor_min=0.0,
    sensor_max=100.0,
)

if updated_reading.is_anomaly:
    print(f"Anomaly detected! Score: {updated_reading.anomaly_score}")
    print(f"Reason: {updated_reading.metadata['anomaly_reason']}")
```

#### Bulk Processing

```python
# Check multiple readings at once
readings = [...]  # List of SensorReadingCreate objects

sensor_configs = {
    sensor_id_1: {"min": 0.0, "max": 100.0},
    sensor_id_2: {"min": 10.0, "max": 50.0},
}

updated_readings = service.check_batch(readings, sensor_configs)

anomalies = [r for r in updated_readings if r.is_anomaly]
print(f"Found {len(anomalies)} anomalies in batch")
```

#### Get Sensor Statistics

```python
# Get real-time statistics for a sensor
stats = service.update_sensor_stats(sensor_id)

print(f"Mean: {stats['mean']:.2f}")
print(f"Std Dev: {stats['std']:.2f}")
print(f"Min: {stats['min']:.2f}")
print(f"Max: {stats['max']:.2f}")
print(f"Median: {stats['median']:.2f}")
```

#### Retrain Model

```python
# Retrain after sensor recalibration or process changes
service.retrain_sensor(sensor_id)
```

### Integration with PlantOps

The anomaly detection is automatically integrated into the sensor service:

```python
from src.contexts.plant_ops.application.services import SensorService

# Service automatically checks for anomalies
reading_id = await sensor_service.record_reading(tenant_id, reading)

# Bulk ingestion also includes anomaly detection
count = await sensor_service.record_readings_bulk(tenant_id, readings)
```

### Configuration

The anomaly detector can be configured with these parameters:

```python
from src.core.ml.anomaly_detection import AnomalyDetector

detector = AnomalyDetector(
    window_size=100,        # Number of readings to keep in memory
    contamination=0.01,     # Expected proportion of outliers (1%)
    std_threshold=3.0,      # Z-score threshold for statistical detection
    rate_threshold=5.0,     # Maximum rate of change per second
)
```

### Model Persistence

Models are automatically saved and loaded:

```python
# Models are saved to /tmp/anomaly_models by default
service = AnomalyDetectionService(model_dir=Path("/opt/foodflow/models"))

# Save models manually
service.save_models()

# Models are automatically loaded on initialization
```

### Performance

- **Latency**: < 1ms per reading (statistical methods)
- **Latency**: < 5ms per reading (with ML)
- **Throughput**: > 10,000 readings/second
- **Memory**: ~1MB per sensor (100 reading window)
- **Training**: Automatic, incremental

### Events Published

The system publishes domain events for anomalies:

```python
{
    "event_type": "SensorAnomalyDetected",
    "tenant_id": "...",
    "sensor_id": "...",
    "reading_id": "...",
    "value": 85.5,
    "anomaly_score": 0.87,
    "timestamp": "2024-11-20T10:30:00Z"
}
```

## Future ML Capabilities

### Planned Features

1. **Predictive Maintenance**
   - Predict equipment failures before they occur
   - Analyze vibration, temperature, and performance trends
   - Recommend maintenance schedules

2. **Quality Prediction**
   - Predict batch quality from process parameters
   - Early warning for quality issues
   - Optimize process parameters for quality

3. **Demand Forecasting**
   - Time-series forecasting for production planning
   - Seasonal pattern detection
   - Multi-horizon predictions

4. **Root Cause Analysis**
   - Automated correlation analysis
   - Identify factors contributing to defects
   - Suggest corrective actions

5. **Process Optimization**
   - Reinforcement learning for parameter tuning
   - Multi-objective optimization
   - Energy efficiency improvements

## Development

### Running Tests

```bash
pytest tests/ml/ -v
```

### Adding New Models

1. Create model class in `src/core/ml/`
2. Implement training and inference methods
3. Add service wrapper for integration
4. Update documentation

### Dependencies

- **scikit-learn**: Core ML algorithms
- **numpy**: Numerical operations
- **pandas**: Data manipulation (future)
- **xgboost**: Gradient boosting (future)
- **prophet**: Time-series forecasting (future)

## References

- [Isolation Forest Paper](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf)
- [Anomaly Detection Best Practices](https://scikit-learn.org/stable/modules/outlier_detection.html)
- [Time Series Anomaly Detection](https://arxiv.org/abs/2009.13807)
