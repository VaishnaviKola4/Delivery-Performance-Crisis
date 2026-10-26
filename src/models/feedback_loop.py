"""
Continuous Learning and Feedback Loop Module.
Ingests newly completed delivery records, detects performance drift,
updates model weights with retraining, and tracks performance improvements over time.
"""

import os
import datetime
import pandas as pd
from src.models.delivery_model import DeliveryPerformanceModels

FEEDBACK_STORE_PATH = "data/feedback_stream.csv"
HISTORICAL_DATA_PATH = "data/delivery_orders.csv"

class OperationalFeedbackLoop:
    def __init__(self, models_instance: DeliveryPerformanceModels = None):
        self.models_instance = models_instance or DeliveryPerformanceModels.load("src/models")
        
    def record_feedback(self, new_orders: list) -> int:
        """
        Appends newly verified delivery outcomes to the feedback data store.
        """
        df_new = pd.DataFrame(new_orders)
        if "feedback_logged_at" not in df_new.columns:
            df_new["feedback_logged_at"] = datetime.datetime.now().isoformat()
            
        os.makedirs(os.path.dirname(FEEDBACK_STORE_PATH), exist_ok=True)
        if os.path.exists(FEEDBACK_STORE_PATH):
            df_new.to_csv(FEEDBACK_STORE_PATH, mode="a", header=False, index=False)
        else:
            df_new.to_csv(FEEDBACK_STORE_PATH, mode="w", header=True, index=False)
            
        return len(df_new)

    def trigger_retraining(self, min_feedback_threshold=50):
        """
        Retrains the model incorporating latest operational observations.
        """
        if not os.path.exists(FEEDBACK_STORE_PATH):
            return {"status": "SKIPPED", "reason": "No feedback data file found."}
            
        df_feedback = pd.read_csv(FEEDBACK_STORE_PATH)
        if len(df_feedback) < min_feedback_threshold:
            return {
                "status": "ACCUMULATING",
                "current_count": len(df_feedback),
                "threshold_required": min_feedback_threshold
            }
            
        df_base = pd.read_csv(HISTORICAL_DATA_PATH)
        df_combined = pd.concat([df_base, df_feedback.drop(columns=["feedback_logged_at"], errors="ignore")], ignore_index=True)
        df_combined.to_csv(HISTORICAL_DATA_PATH, index=False)
        
        # Clear feedback buffer after merge
        os.remove(FEEDBACK_STORE_PATH)
        
        # Retrain models
        new_metrics = self.models_instance.train_and_evaluate(HISTORICAL_DATA_PATH)
        self.models_instance.save("src/models")
        
        return {
            "status": "RETRAINED_SUCCESSFULLY",
            "combined_records": len(df_combined),
            "new_metrics": new_metrics
        }

