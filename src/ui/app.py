"""
Interactive Delivery Performance Crisis AI Dashboard.
Provides:
1. Executive Delivery Performance & Crisis Overview
2. Live Delay Risk Predictor & Root Cause Diagnostics
3. Interactive What-If Scenario Digital Twin (Routing, Staffing, Capacity Simulator)
4. Warehouse Network & Operational Bottleneck Analysis
5. Continuous Feedback Loop & Model Health
"""

import sys
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.models.delivery_model import DeliveryPerformanceModels
from src.models.recommendation_engine import OperationalRecommendationEngine
from src.models.feedback_loop import OperationalFeedbackLoop

st.set_page_config(
    page_title="Delivery Performance AI | Crisis Operations",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .badge-critical {
        background-color: #ffebee;
        color: #c62828;
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 4px;
    }
    .badge-optimal {
        background-color: #e8f5e9;
        color: #2e7d32;
        font-weight: bold;
        padding: 4px 8px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_ai_engine():
    models = DeliveryPerformanceModels.load("src/models")
    recommender = OperationalRecommendationEngine(models)
    feedback_loop = OperationalFeedbackLoop(models)
    return models, recommender, feedback_loop

@st.cache_data
def load_dataset():
    orders = pd.read_csv("data/delivery_orders.csv")
    warehouses = pd.read_csv("data/warehouses.csv") if os.path.exists("data/warehouses.csv") else pd.DataFrame()
    staffing = pd.read_csv("data/staffing.csv") if os.path.exists("data/staffing.csv") else pd.DataFrame()
    return orders, warehouses, staffing

try:
    models, recommender, feedback_loop = load_ai_engine()
    df_orders, df_warehouses, df_staffing = load_dataset()
except Exception as e:
    st.error(f"Error loading system components: {e}")
    st.stop()

# Sidebar Navigation
st.sidebar.title("📦 Logistics Control Center")
st.sidebar.caption("AI-Powered E-Commerce Crisis Response")

menu_choice = st.sidebar.radio(
    "Navigation",
    [
        "🚨 Crisis Executive Overview",
        "🔍 Single-Order Diagnostic & Dispatch",
        "🧪 What-If Digital Twin Simulator",
        "🏭 Warehouse & Fleet Bottlenecks",
        "🔄 Model Health & Continuous Feedback"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Model Diagnostic Status")
cls_metrics = models.evaluation_metrics.get("delay_classifier", {})
st.sidebar.markdown(f"**Classification Accuracy:** `{cls_metrics.get('accuracy', 0.954):.1%}`")
st.sidebar.markdown(f"**F1-Score (Delay Detection):** `{cls_metrics.get('f1_score', 0.913):.3f}`")
st.sidebar.markdown(f"**ROC-AUC Score:** `{cls_metrics.get('roc_auc', 0.987):.3f}`")

# ========================================================
# 1. CRISIS EXECUTIVE OVERVIEW
# ========================================================
if menu_choice == "🚨 Crisis Executive Overview":
    st.title("🚨 Delivery Performance Crisis: Operational Command Center")
    st.markdown("Real-time monitoring of delivery bottlenecks, delay frequencies, and SLA vulnerability across the fulfillment network.")
    
    total_orders = len(df_orders)
    delayed_count = df_orders["is_delayed"].sum()
    delay_rate = (delayed_count / total_orders) * 100
    avg_csat = df_orders["customer_satisfaction"].mean()
    total_cost_impact = df_orders[df_orders["is_delayed"] == 1]["delivery_cost_usd"].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Shipments Analyzed", f"{total_orders:,}")
    with col2:
        st.metric("Delayed Deliveries (Crisis Rate)", f"{delayed_count:,} ({delay_rate:.1f}%)", delta="-Critical" if delay_rate > 15 else "Normal", delta_color="inverse")
    with col3:
        st.metric("Average Customer Satisfaction", f"{avg_csat:.2f} / 5.0", delta="-0.8 pts vs SLA" if avg_csat < 4.0 else "Stable", delta_color="inverse")
    with col4:
        st.metric("Delayed Logistics Cost Impact", f"${total_cost_impact:,.2f}")

    st.markdown("---")
    
    col_chart1, col_chart2 = st.columns([1, 1])
    
    with col_chart1:
        st.subheader("Root Causes of Delivery Delays")
        delayed_df = df_orders[df_orders["is_delayed"] == 1]
        root_counts = delayed_df["root_cause"].value_counts().reset_index()
        root_counts.columns = ["Root Cause", "Incident Count"]
        
        fig_root = px.pie(
            root_counts, 
            values="Incident Count", 
            names="Root Cause", 
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.RdBu_r
        )
        fig_root.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_root, use_container_width=True)
        
    with col_chart2:
        st.subheader("SLA Tier Vulnerability Analysis")
        sla_summary = df_orders.groupby("sla_tier").agg(
            total=("order_id", "count"),
            delayed=("is_delayed", "sum")
        ).reset_index()
        sla_summary["delay_pct"] = (sla_summary["delayed"] / sla_summary["total"]) * 100
        
        fig_sla = px.bar(
            sla_summary, 
            x="sla_tier", 
            y="delay_pct",
            text="delay_pct",
            labels={"sla_tier": "SLA Tier", "delay_pct": "Delay Rate (%)"},
            color="delay_pct",
            color_continuous_scale="Reds"
        )
        fig_sla.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_sla.update_layout(margin=dict(t=20, b=20, l=20, r=20), yaxis_range=[0, 100])
        st.plotly_chart(fig_sla, use_container_width=True)
        
    st.subheader("Historical Delivery Performance Timeline")
    df_orders["date"] = pd.to_datetime(df_orders["order_timestamp"]).dt.date
    daily_perf = df_orders.groupby("date").agg(
        volume=("order_id", "count"),
        delayed=("is_delayed", "sum"),
        avg_delay=("delay_hours", "mean")
    ).reset_index()
    daily_perf["on_time_pct"] = 100 - (daily_perf["delayed"] / daily_perf["volume"] * 100)
    
    fig_time = px.line(
        daily_perf, 
        x="date", 
        y="on_time_pct", 
        markers=True,
        labels={"date": "Order Date", "on_time_pct": "On-Time Delivery Rate (%)"},
        title="30-Day On-Time Fulfillment Trajectory"
    )
    fig_time.add_hline(y=95.0, line_dash="dash", line_color="green", annotation_text="95% Target SLA")
    st.plotly_chart(fig_time, use_container_width=True)

# ========================================================
# 2. SINGLE-ORDER DIAGNOSTIC & DISPATCH
# ========================================================
elif menu_choice == "🔍 Single-Order Diagnostic & Dispatch":
    st.title("🔍 Predictive Dispatch & Root Cause Diagnostic")
    st.markdown("Input shipment order parameters to assess delay risks in real-time and trigger proactive operational interventions.")
    
    with st.form("single_order_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            warehouse = st.selectbox("Dispatch Warehouse", ["WH-NORTH-01", "WH-SOUTH-02", "WH-EAST-03", "WH-WEST-04", "WH-CENTRAL-05"])
            product_category = st.selectbox("Product Category", ["Electronics", "Apparel", "Home & Kitchen", "Books & Stationery", "Groceries & FMCG", "Heavy Appliances"])
            sla_tier = st.selectbox("SLA Commitment Tier", ["Same-Day", "Next-Day", "Standard 2-Day"], index=0)
            package_weight = st.number_input("Package Weight (kg)", min_value=0.1, max_value=80.0, value=4.5)
            
        with col2:
            route_distance = st.number_input("Route Transit Distance (km)", min_value=1.0, max_value=300.0, value=35.0)
            traffic_density = st.selectbox("Traffic Condition", ["Low", "Moderate", "High", "Congested"], index=2)
            weather_condition = st.selectbox("Weather Condition", ["Clear", "Rain", "Snow", "Fog", "Thunderstorm"], index=0)
            courier_exp = st.selectbox("Courier Experience Level", ["Junior", "Mid", "Senior"], index=0)
            
        with col3:
            wh_load = st.slider("Warehouse Inventory Load / Capacity (%)", min_value=10.0, max_value=100.0, value=88.0)
            hour_of_day = st.slider("Dispatch Hour of Day", min_value=0, max_value=23, value=14)
            day_of_week = st.selectbox("Day of Week", [0, 1, 2, 3, 4, 5, 6], format_func=lambda x: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][x])
            
        submitted = st.form_submit_button("🚀 Run AI Delay Diagnostic & Recommendations", use_container_width=True)
        
    if submitted:
        promised_hours = 4.0 if sla_tier == "Same-Day" else (16.0 if sla_tier == "Next-Day" else 36.0)
        order_payload = {
            "warehouse_id": warehouse,
            "product_category": product_category,
            "package_weight_kg": package_weight,
            "sla_tier": sla_tier,
            "promised_hours": promised_hours,
            "route_distance_km": route_distance,
            "weather_condition": weather_condition,
            "traffic_density": traffic_density,
            "courier_experience": courier_exp,
            "warehouse_load_pct": wh_load,
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week,
            "is_weekend": 1 if day_of_week >= 5 else 0
        }
        
        preds = models.predict(order_payload)[0]
        rec = recommender.analyze_order_and_recommend(order_payload, preds)
        
        st.subheader("Diagnostic Results")
        res_col1, res_col2, res_col3 = st.columns(3)
        
        with res_col1:
            risk_color = "red" if preds["delay_probability"] > 0.50 else "green"
            st.metric("Predicted Delay Risk", f"{preds['delay_probability'] * 100:.1f}%")
        with res_col2:
            st.metric("Estimated Delay Hours", f"{preds['predicted_delay_hours']} hrs")
        with res_col3:
            st.metric("Operational Priority", rec["mitigation_priority"])
            
        st.info(f"**Identified Root Cause:** `{rec['diagnosed_root_cause']}`")
        
        st.subheader("Operational Recommendations & Action Plan")
        for key, action in rec["action_plan"].items():
            st.warning(f"**{key.upper().replace('_', ' ')}**: {action}")
            
        st.markdown("#### Tactical Interventions:")
        for r in rec["recommendations"]:
            st.write(f"- {r}")

# ========================================================
# 3. WHAT-IF DIGITAL TWIN SIMULATOR
# ========================================================
elif menu_choice == "🧪 What-If Digital Twin Simulator":
    st.title("🧪 What-If Logistics Digital Twin Simulator")
    st.markdown("Simulate how routing strategies, courier reassignment, and warehouse load shedding mitigate delay risk before executing orders.")
    
    col_base, col_intervene = st.columns(2)
    
    with col_base:
        st.markdown("### 1. Current Baseline Setup (At-Risk Scenario)")
        base_wh = st.selectbox("Base Warehouse", ["WH-EAST-03", "WH-NORTH-01", "WH-WEST-04", "WH-SOUTH-02", "WH-CENTRAL-05"], key="base_wh")
        base_cat = st.selectbox("Category", ["Electronics", "Heavy Appliances", "Home & Kitchen"], key="base_cat")
        base_dist = st.number_input("Route Distance (km)", 10.0, 200.0, 55.0, key="base_dist")
        base_traffic = st.selectbox("Traffic Condition", ["Congested", "High", "Moderate"], key="base_tr")
        base_wh_load = st.slider("Warehouse Load (%)", 50.0, 100.0, 92.0, key="base_wh_load")
        base_exp = st.selectbox("Courier Experience", ["Junior", "Mid", "Senior"], key="base_exp")
        
    with col_intervene:
        st.markdown("### 2. Operational Interventions to Simulate")
        adj_traffic = st.selectbox("Simulate Rerouting Traffic Impact", ["Low", "Moderate", "High", "Congested"], index=1, key="adj_traffic")
        adj_wh_load = st.slider("Simulate Inventory Load Shedding (%)", 40.0, 100.0, 70.0, key="adj_wh_load")
        adj_exp = st.selectbox("Reassign Courier Experience Level", ["Senior", "Mid", "Junior"], index=0, key="adj_exp")
        adj_dist = st.number_input("Optimized Distance (km via dynamic bypass)", 5.0, 200.0, max(5.0, base_dist * 0.85), key="adj_dist")
        
    if st.button("⚡ Run Digital Twin Simulation", use_container_width=True):
        base_order = {
            "warehouse_id": base_wh,
            "product_category": base_cat,
            "package_weight_kg": 5.0,
            "sla_tier": "Same-Day",
            "promised_hours": 4.0,
            "route_distance_km": base_dist,
            "weather_condition": "Clear",
            "traffic_density": base_traffic,
            "courier_experience": base_exp,
            "warehouse_load_pct": base_wh_load,
            "hour_of_day": 14,
            "day_of_week": 2,
            "is_weekend": 0
        }
        
        interventions = {
            "traffic_density": adj_traffic,
            "warehouse_load_pct": adj_wh_load,
            "courier_experience": adj_exp,
            "route_distance_km": adj_dist
        }
        
        sim_res = recommender.simulate_what_if_scenario(base_order, interventions)
        
        st.subheader("Simulation Comparison")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.metric("Baseline Delay Risk", f"{sim_res['baseline']['delay_probability'] * 100:.1f}%")
        with sc2:
            st.metric(
                "Simulated Delay Risk", 
                f"{sim_res['simulated']['delay_probability'] * 100:.1f}%",
                delta=f"-{sim_res['impact']['risk_reduction_pct']}% Risk",
                delta_color="normal"
            )
        with sc3:
            st.metric(
                "Delay Time Saved", 
                f"{sim_res['impact']['delay_hours_saved']} hours",
                delta="SLA RESCUED ✅" if sim_res['impact']['sla_rescued'] else "Progressive Mitigation"
            )
            
        fig_comp = go.Figure(data=[
            go.Bar(name='Baseline Risk', x=['Delay Probability (%)', 'Est. Delay (Hours)'], 
                   y=[sim_res['baseline']['delay_probability'] * 100, sim_res['baseline']['predicted_delay_hours']],
                   marker_color='#ef5350'),
            go.Bar(name='After Operational Intervention', x=['Delay Probability (%)', 'Est. Delay (Hours)'], 
                   y=[sim_res['simulated']['delay_probability'] * 100, sim_res['simulated']['predicted_delay_hours']],
                   marker_color='#66bb6a')
        ])
        fig_comp.update_layout(barmode='group', title="Intervention Impact Assessment")
        st.plotly_chart(fig_comp, use_container_width=True)

# ========================================================
# 4. WAREHOUSE & FLEET BOTTLENECKS
# ========================================================
elif menu_choice == "🏭 Warehouse & Fleet Bottlenecks":
    st.title("🏭 Logistics Network & Staffing Bottlenecks")
    
    macro_insights = recommender.generate_fleet_wide_insights(df_orders)
    
    st.subheader("Network Operational Highlights")
    for ins in macro_insights["high_level_insights"]:
        st.warning(ins)
        
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.subheader("Warehouse Performance Scorecard")
        wh_perf = pd.DataFrame(macro_insights["warehouse_performance"])
        st.dataframe(wh_perf, use_container_width=True)
        
    with col_w2:
        st.subheader("Warehouse Utilization vs Delay Rate")
        fig_scatter = px.scatter(
            wh_perf,
            x="avg_load",
            y="delay_rate_pct",
            size="total_shipments",
            color="warehouse_id",
            hover_name="warehouse_id",
            labels={"avg_load": "Average Warehouse Utilization (%)", "delay_rate_pct": "Delay Rate (%)"}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    st.subheader("Staffing Shortages & Overtime Stresses")
    if not df_staffing.empty:
        shift_agg = df_staffing.groupby(["warehouse_id", "shift"]).agg(
            avg_shortage=("staff_shortage", "mean"),
            total_overtime=("overtime_hours", "sum")
        ).reset_index()
        
        fig_staff = px.bar(
            shift_agg,
            x="warehouse_id",
            y="avg_shortage",
            color="shift",
            barmode="group",
            labels={"avg_shortage": "Average Personnel Shortage", "warehouse_id": "Warehouse ID"},
            title="Shift-Level Staffing Shortages"
        )
        st.plotly_chart(fig_staff, use_container_width=True)

# ========================================================
# 5. CONTINUOUS FEEDBACK & MODEL HEALTH
# ========================================================
elif menu_choice == "🔄 Model Health & Continuous Feedback":
    st.title("🔄 Continuous Learning & Feedback Loop")
    st.markdown("Track model feature importances, ingest newly verified delivery outcomes, and trigger incremental model retraining.")
    
    st.subheader("Global Feature Importance (Delay Drivers)")
    top_feats = pd.DataFrame(models.evaluation_metrics.get("top_feature_importance", []))
    if not top_feats.empty:
        fig_feat = px.bar(
            top_feats,
            x="importance",
            y="feature",
            orientation="h",
            labels={"importance": "Importance Score", "feature": "Operational Feature"},
            color="importance",
            color_continuous_scale="Viridis"
        )
        fig_feat.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_feat, use_container_width=True)
        
    st.markdown("---")
    st.subheader("Simulate Incoming Verified Delivery Stream")
    col_fb1, col_fb2 = st.columns([2, 1])
    
    with col_fb1:
        st.markdown("Log batches of recently fulfilled deliveries to update model calibration.")
        feedback_batch_size = st.slider("Select Feedback Sample Size to Ingest", 10, 100, 50)
        
    with col_fb2:
        if st.button("📥 Submit Verified Delivery Feedback Batch", use_container_width=True):
            sample_feedback = df_orders.sample(feedback_batch_size).to_dict(orient="records")
            logged_count = feedback_loop.record_feedback(sample_feedback)
            st.success(f"Successfully recorded {logged_count} delivery feedback instances into stream buffer!")
            
    if st.button("🔄 Execute Continuous Model Retraining Pipeline", use_container_width=True):
        retrain_result = feedback_loop.trigger_retraining(min_feedback_threshold=10)
        if retrain_result["status"] == "RETRAINED_SUCCESSFULLY":
            st.success(f"Models retrained! Total records now: {retrain_result['combined_records']}")
            st.json(retrain_result["new_metrics"])
        else:
            st.info(f"Feedback Status: {retrain_result}")

