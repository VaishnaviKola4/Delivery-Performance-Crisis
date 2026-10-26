# How to Use: Delivery Performance Crisis AI

## 1. Quick Start Guide

### Step 1: Environment Setup
Ensure Python 3.9+ is installed. Clone the repository and install required dependencies:
```bash
git clone <repository_url>
cd DeliveryPerformanceAI
pip install -r requirements.txt
```

### Step 2: Generate or Ingest Logistics Data
To generate a comprehensive simulated dataset mimicking real-world e-commerce delivery crisis scenarios:
```bash
python src/data_generator.py
```
This produces three synthetic operational datasets in the `/data` directory:
- `data/delivery_orders.csv` (6,000 order transactions with transit times, delays, costs, and root causes)
- `data/warehouses.csv` (Warehouse capacity, locations, and inventory stress metrics)
- `data/staffing.csv` (Shift-level scheduled vs actual headcount and overtime)

### Step 3: Train the Machine Learning Models
Execute the end-to-end model training and validation pipeline:
```bash
python src/models/delivery_model.py
```
This trains:
1. **Delay Classifier:** `RandomForestClassifier` (Delay Probability & Binary Prediction)
2. **Delay Regressor:** `RandomForestRegressor` (Delay Magnitude in Hours)
3. **Root Cause Classifier:** `GradientBoostingClassifier` (Tactical Delay Attribution)

Trained artifacts are stored in `src/models/delivery_models.joblib` and `src/models/saved_preprocessor.joblib`.

### Step 4: Launch the Interactive Dashboard
Launch the Streamlit web application:
```bash
streamlit run src/ui/app.py
```
Open your browser at `http://localhost:8501`.

---

## 2. Navigating the UI Dashboard

1. **🚨 Crisis Executive Overview:**
   - Review high-level network performance, on-time delivery rates, root-cause distribution charts, and SLA tier vulnerability.
2. **🔍 Single-Order Diagnostic & Dispatch:**
   - Input specific order details (Warehouse, Category, Weight, Traffic, Weather, Distance, SLA).
   - Click **Run AI Delay Diagnostic** to get instant delay predictions and operational action plans.
3. **🧪 What-If Digital Twin Simulator:**
   - Contrast baseline risky delivery conditions against potential interventions (rerouting, courier seniority upgrade, warehouse load-shedding).
   - Observe real-time risk reduction and SLA rescue metrics.
4. **🏭 Warehouse & Fleet Bottlenecks:**
   - Inspect warehouse utilization versus delay rates.
   - Analyze staffing shortages across morning, afternoon, and night shifts.
5. **🔄 Model Health & Continuous Feedback:**
   - Examine global feature importances.
   - Ingest newly verified delivery feedback into the stream buffer and trigger online model retraining.

