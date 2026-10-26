"""
Synthetic Data Generator for E-Commerce Delivery Performance.
Simulates realistic operations across Warehouses, Delivery Routes, Staffing, and Historical Delivery Performance.
Calibrated to represent an authentic delivery performance crisis (~18-25% delayed shipments).
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

WAREHOUSE_METRICS = [
    {"warehouse_id": "WH-NORTH-01", "name": "North Metro Hub", "location_city": "Chicago", "latitude": 41.8781, "longitude": -87.6298, "max_capacity": 15000, "staff_headcount": 45},
    {"warehouse_id": "WH-SOUTH-02", "name": "South Regional Depot", "location_city": "Dallas", "latitude": 32.7767, "longitude": -96.7970, "max_capacity": 12000, "staff_headcount": 35},
    {"warehouse_id": "WH-EAST-03", "name": "East Coast Mega Center", "location_city": "Newark", "latitude": 40.7357, "longitude": -74.1724, "max_capacity": 22000, "staff_headcount": 70},
    {"warehouse_id": "WH-WEST-04", "name": "Pacific Coast Gateway", "location_city": "Los Angeles", "latitude": 34.0522, "longitude": -118.2437, "max_capacity": 18000, "staff_headcount": 55},
    {"warehouse_id": "WH-CENTRAL-05", "name": "Midwest Fulfillment Hub", "location_city": "Kansas City", "latitude": 39.0997, "longitude": -94.5786, "max_capacity": 10000, "staff_headcount": 30}
]

PRODUCT_CATEGORIES = [
    {"category": "Electronics", "fragile": True, "avg_weight_kg": 3.8, "base_prep_mins": 45},
    {"category": "Apparel", "fragile": False, "avg_weight_kg": 0.9, "base_prep_mins": 20},
    {"category": "Home & Kitchen", "fragile": True, "avg_weight_kg": 5.4, "base_prep_mins": 50},
    {"category": "Books & Stationery", "fragile": False, "avg_weight_kg": 1.2, "base_prep_mins": 15},
    {"category": "Groceries & FMCG", "fragile": False, "avg_weight_kg": 4.1, "base_prep_mins": 30},
    {"category": "Heavy Appliances", "fragile": True, "avg_weight_kg": 28.5, "base_prep_mins": 90}
]

WEATHER_CONDITIONS = ["Clear", "Rain", "Snow", "Fog", "Thunderstorm"]
TRAFFIC_LEVELS = ["Low", "Moderate", "High", "Congested"]
DELIVERY_PERSONNEL_EXPERIENCE = ["Junior", "Mid", "Senior"]

def generate_warehouse_data(output_dir="data"):
    wh_df = pd.DataFrame(WAREHOUSE_METRICS)
    # Warehouse load stress levels
    wh_df["current_inventory_load"] = [int(cap * np.random.uniform(0.75, 0.98)) for cap in wh_df["max_capacity"]]
    wh_df["utilization_pct"] = np.round((wh_df["current_inventory_load"] / wh_df["max_capacity"]) * 100, 2)
    os.makedirs(output_dir, exist_ok=True)
    wh_df.to_csv(os.path.join(output_dir, "warehouses.csv"), index=False)
    return wh_df

def generate_staffing_data(wh_df, output_dir="data", days=30):
    records = []
    start_date = datetime.now() - timedelta(days=days)
    shifts = ["Morning", "Afternoon", "Night"]
    
    for day in range(days):
        current_date = (start_date + timedelta(days=day)).date()
        is_weekend = (start_date + timedelta(days=day)).weekday() >= 5
        
        for _, wh in wh_df.iterrows():
            for shift in shifts:
                baseline = wh["staff_headcount"] // 3
                if shift == "Night":
                    scheduled = int(baseline * 0.7)
                elif shift == "Morning":
                    scheduled = int(baseline * 1.2)
                else:
                    scheduled = baseline
                
                absenteeism_rate = np.random.uniform(0.05, 0.35 if is_weekend else 0.22)
                actual_present = max(1, int(scheduled * (1 - absenteeism_rate)))
                overtime_hours = 0
                if actual_present < scheduled:
                    overtime_hours = round(np.random.uniform(1.0, 5.0) * (scheduled - actual_present), 1)
                
                records.append({
                    "date": str(current_date),
                    "warehouse_id": wh["warehouse_id"],
                    "shift": shift,
                    "scheduled_personnel": scheduled,
                    "active_personnel": actual_present,
                    "staff_shortage": scheduled - actual_present,
                    "overtime_hours": overtime_hours
                })
    staff_df = pd.DataFrame(records)
    staff_df.to_csv(os.path.join(output_dir, "staffing.csv"), index=False)
    return staff_df

def generate_delivery_dataset(num_records=6000, output_dir="data", days=30):
    wh_df = generate_warehouse_data(output_dir)
    staff_df = generate_staffing_data(wh_df, output_dir, days=days)
    
    orders = []
    base_time = datetime.now() - timedelta(days=days)
    
    for i in range(1, num_records + 1):
        order_id = f"ORD-{20260000 + i}"
        order_offset_seconds = random.randint(0, days * 24 * 3600)
        order_timestamp = base_time + timedelta(seconds=order_offset_seconds)
        
        wh = wh_df.sample(1).iloc[0]
        cat = random.choice(PRODUCT_CATEGORIES)
        
        # Priority SLA
        # For realistic e-commerce, promised hours are strictly monitored
        sla_tier = np.random.choice(["Same-Day", "Next-Day", "Standard 2-Day"], p=[0.25, 0.50, 0.25])
        promised_hours = 4.0 if sla_tier == "Same-Day" else (16.0 if sla_tier == "Next-Day" else 36.0)
        
        # Route parameters
        if sla_tier == "Same-Day":
            route_distance_km = round(np.random.uniform(5.0, 45.0), 1)
        elif sla_tier == "Next-Day":
            route_distance_km = round(np.random.uniform(10.0, 120.0), 1)
        else:
            route_distance_km = round(np.random.uniform(25.0, 260.0), 1)
            
        weather = np.random.choice(WEATHER_CONDITIONS, p=[0.50, 0.22, 0.12, 0.09, 0.07])
        traffic = np.random.choice(TRAFFIC_LEVELS, p=[0.20, 0.35, 0.30, 0.15])
        courier_exp = np.random.choice(DELIVERY_PERSONNEL_EXPERIENCE, p=[0.35, 0.45, 0.20])
        
        # Warehouse fulfillment delay calculation
        wh_capacity_stress = (wh["current_inventory_load"] / wh["max_capacity"])
        base_dispatch_delay = cat["base_prep_mins"] / 60.0 # hours
        
        # Dispatch latency influenced by warehouse stress
        wh_delay_noise = np.random.exponential(scale=1.2 if wh_capacity_stress > 0.88 else 0.5)
        wh_processing_time = (base_dispatch_delay * 1.5) + (wh_capacity_stress * 2.5) + wh_delay_noise
        
        # Transit speed
        base_speed_kmh = 36.0
        if traffic == "Moderate":
            base_speed_kmh *= 0.75
        elif traffic == "High":
            base_speed_kmh *= 0.50
        elif traffic == "Congested":
            base_speed_kmh *= 0.32
            
        if weather == "Rain":
            base_speed_kmh *= 0.80
        elif weather == "Snow":
            base_speed_kmh *= 0.52
        elif weather == "Thunderstorm":
            base_speed_kmh *= 0.45
            
        if courier_exp == "Junior":
            base_speed_kmh *= 0.82
        elif courier_exp == "Senior":
            base_speed_kmh *= 1.15
            
        transit_time_hours = route_distance_km / max(base_speed_kmh, 4.0)
        transit_noise = np.random.exponential(scale=0.8)
        total_transit_hours = transit_time_hours + transit_noise
        
        # Additional operational delay shocks (vehicle breakdowns, dispatch queue, dock waiting)
        operational_shock = 0.0
        if np.random.random() < 0.12:
            operational_shock = np.random.uniform(2.0, 7.0)
            
        total_delivery_time_hours = round(wh_processing_time + total_transit_hours + operational_shock, 2)
        
        delay_hours = round(max(0.0, total_delivery_time_hours - promised_hours), 2)
        is_delayed = 1 if total_delivery_time_hours > promised_hours else 0
        
        # Accurate Root Cause Assignment
        if not is_delayed:
            primary_root_cause = "On-Time / Optimal"
        else:
            if weather in ["Snow", "Thunderstorm"] and (weather == "Snow" or np.random.rand() > 0.3):
                primary_root_cause = "Adverse Weather Disruptions"
            elif traffic in ["High", "Congested"] and (total_transit_hours > wh_processing_time):
                primary_root_cause = "Severe Traffic Congestion"
            elif wh_capacity_stress >= 0.88 or wh_processing_time > (promised_hours * 0.5):
                primary_root_cause = "Warehouse Bottleneck / High Utilization"
            elif courier_exp == "Junior" and route_distance_km > 35:
                primary_root_cause = "Courier Route Navigation Inefficiency"
            elif operational_shock > 0:
                primary_root_cause = "Understaffing / Dispatch Lag"
            else:
                primary_root_cause = "Peak Demand Capacity Overload"
                
        # Customer satisfaction score (1 to 5)
        if not is_delayed:
            csat = random.choices([4, 5], weights=[0.20, 0.80])[0]
        else:
            if delay_hours < 2:
                csat = random.choices([3, 4], weights=[0.60, 0.40])[0]
            elif delay_hours < 5:
                csat = random.choices([2, 3], weights=[0.70, 0.30])[0]
            else:
                csat = 1
                
        orders.append({
            "order_id": order_id,
            "order_timestamp": order_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "warehouse_id": wh["warehouse_id"],
            "warehouse_name": wh["name"],
            "product_category": cat["category"],
            "package_weight_kg": round(float(np.random.normal(cat["avg_weight_kg"], 0.4)), 2),
            "is_fragile": int(cat["fragile"]),
            "sla_tier": sla_tier,
            "promised_hours": promised_hours,
            "route_distance_km": route_distance_km,
            "weather_condition": weather,
            "traffic_density": traffic,
            "courier_experience": courier_exp,
            "warehouse_load_pct": wh["utilization_pct"],
            "wh_processing_time_hours": round(wh_processing_time, 2),
            "transit_time_hours": round(total_transit_hours, 2),
            "actual_delivery_time_hours": total_delivery_time_hours,
            "delay_hours": delay_hours,
            "is_delayed": is_delayed,
            "root_cause": primary_root_cause,
            "customer_satisfaction": csat,
            "delivery_cost_usd": round(10.0 + route_distance_km * 0.55 + (15.0 if is_delayed else 0.0), 2)
        })
        
    df = pd.DataFrame(orders)
    csv_path = os.path.join(output_dir, "delivery_orders.csv")
    df.to_csv(csv_path, index=False)
    print(f"Generated {len(df)} orders. Delayed rate: {df['is_delayed'].mean():.2%}")
    return df

if __name__ == "__main__":
    generate_delivery_dataset(num_records=6000)
