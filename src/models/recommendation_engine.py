"""
Operational Recommendation Engine for Delivery Performance Crisis Mitigation.
Analyzes model predictions, feature attribution, and logistical metrics to generate:
- Routing Strategies (dynamic rerouting, buffer adjustments)
- Staffing Schedule adjustments (overtime allocation, shift re-balancing)
- Inventory & Fulfillment re-allocation (load balancing across warehouses)
- Interactive What-If Scenario Simulations
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np

class OperationalRecommendationEngine:
    def __init__(self, models_instance=None):
        self.models_instance = models_instance

    def analyze_order_and_recommend(self, order_dict: Dict[str, Any], prediction_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates tactical operational recommendations for an individual shipment.
        """
        is_delayed = prediction_result.get("is_delayed_prediction", 0)
        delay_prob = prediction_result.get("delay_probability", 0.0)
        predicted_hours = prediction_result.get("predicted_delay_hours", 0.0)
        root_cause = prediction_result.get("predicted_root_cause", "")
        
        recommendations = []
        mitigation_priority = "LOW"
        suggested_actions = {}
        
        if is_delayed or delay_prob > 0.40:
            if delay_prob > 0.70 or predicted_hours > 3.0:
                mitigation_priority = "CRITICAL"
            else:
                mitigation_priority = "MEDIUM"
                
            # Operational Rule 1: Severe Traffic Congestion
            if "Traffic" in root_cause or order_dict.get("traffic_density") in ["High", "Congested"]:
                suggested_actions["routing"] = (
                    "REROUTE TO SECONDARY CORRIDOR: Shift dispatch away from arterial highways. "
                    "Incorporate dynamic micro-hub staging or off-peak delivery dispatch (+1.5h buffer)."
                )
                recommendations.append("Apply dynamic GPS waypoint bypass avoiding congestion bottlenecks.")
                
            # Operational Rule 2: Adverse Weather Disruptions
            if "Weather" in root_cause or order_dict.get("weather_condition") in ["Snow", "Thunderstorm", "Rain"]:
                suggested_actions["weather_protocol"] = (
                    "TRIGGER CONTINGENCY COLD-CHAIN / WEATHER SLA: Proactively message customer with "
                    "updated weather ETA (+2 to 4 hrs) and reassign to 4WD equipped fleet or localized delivery hubs."
                )
                recommendations.append("Switch SLA tier notification to 'Weather-Shield Alert' to preserve CSAT.")
                
            # Operational Rule 3: Warehouse Bottlenecks
            if "Warehouse" in root_cause or float(order_dict.get("warehouse_load_pct", 0)) > 85.0:
                suggested_actions["warehouse_ops"] = (
                    f"INVENTORY LOAD BALANCING: Warehouse load is critical ({order_dict.get('warehouse_load_pct')}%. "
                    "Re-route fulfillment wave to adjacent lower-stress facility or enable fast-track cross-docking."
                )
                recommendations.append("Route high-velocity SKU picking to dedicated priority packing stations.")
                
            # Operational Rule 4: Staffing and Dispatch Lag
            if "Understaffing" in root_cause or "Dispatch" in root_cause:
                suggested_actions["staffing"] = (
                    "ACTIVATE ON-CALL SHIFT & PEAK OVERTIME: Dispatch queue is exceeding threshold. "
                    "Authorize 2 hours of overtime for fulfillment pickers and third-party 3PL overflow couriers."
                )
                recommendations.append("Deploy 3PL gig courier surge capacity to absorb dispatch queue.")
                
            # Operational Rule 5: Courier Route Inefficiency
            if "Courier" in root_cause or order_dict.get("courier_experience") == "Junior":
                suggested_actions["courier_ops"] = (
                    "PAIRING WITH SENIOR COURIER OR CO-PILOT AI: Route distance exceeds junior threshold. "
                    "Provide turn-by-turn clustered geofence drop-offs to prevent turnaround delays."
                )
                recommendations.append("Cluster delivery orders into compact geofenced micro-routes.")
        else:
            suggested_actions["status"] = "Normal Execution: On-track for standard SLA commitment."
            recommendations.append("Maintain baseline standard operating procedure.")
            
        return {
            "order_id": order_dict.get("order_id", "N/A"),
            "mitigation_priority": mitigation_priority,
            "delay_probability": delay_prob,
            "predicted_delay_hours": predicted_hours,
            "diagnosed_root_cause": root_cause,
            "action_plan": suggested_actions,
            "recommendations": recommendations
        }

    def simulate_what_if_scenario(self, base_order: Dict[str, Any], adjustments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs a What-If digital twin simulation comparing baseline scenario vs operational intervention.
        """
        if not self.models_instance:
            raise ValueError("Models instance is required to run simulations.")
            
        modified_order = base_order.copy()
        for k, v in adjustments.items():
            modified_order[k] = v
            
        base_pred = self.models_instance.predict(base_order)[0]
        sim_pred = self.models_instance.predict(modified_order)[0]
        
        prob_reduction = round(base_pred["delay_probability"] - sim_pred["delay_probability"], 3)
        hours_saved = round(base_pred["predicted_delay_hours"] - sim_pred["predicted_delay_hours"], 2)
        
        return {
            "baseline": {
                "delay_probability": base_pred["delay_probability"],
                "predicted_delay_hours": base_pred["predicted_delay_hours"],
                "root_cause": base_pred["predicted_root_cause"]
            },
            "simulated": {
                "delay_probability": sim_pred["delay_probability"],
                "predicted_delay_hours": sim_pred["predicted_delay_hours"],
                "root_cause": sim_pred["predicted_root_cause"]
            },
            "impact": {
                "risk_reduction_pct": round(prob_reduction * 100, 1),
                "delay_hours_saved": max(0.0, hours_saved),
                "sla_rescued": bool(base_pred["is_delayed_prediction"] == 1 and sim_pred["is_delayed_prediction"] == 0)
            }
        }

    def generate_fleet_wide_insights(self, orders_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generates macro operational crisis insights across warehouse networks and delivery personnel.
        """
        total_orders = len(orders_df)
        delayed_orders = orders_df[orders_df["is_delayed"] == 1]
        delay_rate = (len(delayed_orders) / total_orders) * 100 if total_orders > 0 else 0
        
        # Breakdown by root cause
        root_cause_breakdown = orders_df["root_cause"].value_counts().to_dict()
        
        # Warehouse performance ranking
        wh_summary = orders_df.groupby("warehouse_id").agg(
            total_shipments=("order_id", "count"),
            delayed_shipments=("is_delayed", "sum"),
            avg_delay_hours=("delay_hours", "mean"),
            avg_csat=("customer_satisfaction", "mean"),
            avg_load=("warehouse_load_pct", "mean")
        ).reset_index()
        wh_summary["delay_rate_pct"] = np.round((wh_summary["delayed_shipments"] / wh_summary["total_shipments"]) * 100, 1)
        wh_summary = wh_summary.sort_values(by="delay_rate_pct", ascending=False)
        
        # Top operational bottlenecks
        insights = []
        highest_wh = wh_summary.iloc[0]
        insights.append(f"Warehouse {highest_wh['warehouse_id']} is experiencing the highest delay rate ({highest_wh['delay_rate_pct']}%) with an average utilization of {highest_wh['avg_load']:.1f}%.")
        
        traffic_delays = orders_df[orders_df["traffic_density"].isin(["High", "Congested"])]["is_delayed"].mean() * 100
        insights.append(f"Congested & High traffic corridors drive a {traffic_delays:.1f}% delay probability. Dynamic route re-dispatch is advised.")
        
        return {
            "total_orders_evaluated": total_orders,
            "overall_delay_rate_pct": round(delay_rate, 2),
            "root_cause_distribution": root_cause_breakdown,
            "warehouse_performance": wh_summary.to_dict(orient="records"),
            "high_level_insights": insights
        }

