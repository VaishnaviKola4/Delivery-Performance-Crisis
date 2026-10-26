# API & Interface Guide

This document describes programmatic interfaces, function contracts, and data models for integrating the Delivery Performance AI System into existing Warehouse Management Systems (WMS) and Transportation Management Systems (TMS).

---

## 1. Data Models

### Input Shipment Schema (`dict` or `pandas.DataFrame`)
```json
{
  "order_id": "ORD-20261001",
  "warehouse_id": "WH-NORTH-01",
  "product_category": "Electronics",
  "package_weight_kg": 4.5,
  "sla_tier": "Same-Day",
  "promised_hours": 4.0,
  "route_distance_km": 35.0,
  "weather_condition": "Rain",
  "traffic_density": "High",
  "courier_experience": "Junior",
  "warehouse_load_pct": 88.0,
  "hour_of_day": 14,
  "day_of_week": 2,
  "is_weekend": 0
}
```

### Prediction Output Schema
```json
{
  "is_delayed_prediction": 1,
  "delay_probability": 0.84,
  "predicted_delay_hours": 1.75,
  "predicted_root_cause": "Severe Traffic Congestion"
}
```

---

## 2. Python Core Interface

### `DeliveryPerformanceModels`
Located at `src.models.delivery_model.DeliveryPerformanceModels`.

#### `load(model_dir: str = "src/models") -> DeliveryPerformanceModels`
Loads trained preprocessor and model estimators from disk.

#### `predict(single_order_dict_or_df) -> List[Dict[str, Any]]`
Infers delay probability, delay duration, and root cause diagnosis for one or many shipments.

```python
from src.models.delivery_model import DeliveryPerformanceModels

model = DeliveryPerformanceModels.load("src/models")
predictions = model.predict({
    "warehouse_id": "WH-NORTH-01",
    "product_category": "Electronics",
    "package_weight_kg": 4.2,
    "sla_tier": "Same-Day",
    "promised_hours": 4.0,
    "route_distance_km": 28.0,
    "weather_condition": "Clear",
    "traffic_density": "Moderate",
    "courier_experience": "Mid",
    "warehouse_load_pct": 75.0,
    "hour_of_day": 10,
    "day_of_week": 1,
    "is_weekend": 0
})
print(predictions)
```

---

## 3. Recommendation Engine Interface

### `OperationalRecommendationEngine`
Located at `src.models.recommendation_engine.OperationalRecommendationEngine`.

#### `analyze_order_and_recommend(order_dict: Dict, prediction_result: Dict) -> Dict`
Maps model output to prescriptive operational interventions across routing, staffing, and inventory.

#### `simulate_what_if_scenario(base_order: Dict, adjustments: Dict) -> Dict`
Evaluates simulated interventions against baseline risk metrics.
```python
sim_impact = recommender.simulate_what_if_scenario(
    base_order=order_payload,
    adjustments={"traffic_density": "Moderate", "warehouse_load_pct": 70.0}
)
print(sim_impact["impact"]["risk_reduction_pct"])
```

---

## 4. Feedback & Retraining Interface

### `OperationalFeedbackLoop`
Located at `src.models.feedback_loop.OperationalFeedbackLoop`.

#### `record_feedback(new_orders: list) -> int`
Buffers verified ground-truth delivery records.

#### `trigger_retraining(min_feedback_threshold: int = 50) -> Dict`
Merges buffered delivery feedback into historical records and retrains all models.

