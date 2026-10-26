"""
Machine Learning Model Architectures for Delivery Performance Crisis Management.
Includes:
1. Delay Classifier (RandomForest / GradientBoosting): Predicts whether an order will be delayed.
2. Delay Hours Regressor (RandomForestRegressor): Predicts the exact duration of delay.
3. Root Cause Classifier: Classifies the operational culprit behind delays.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_squared_error, mean_absolute_error, r2_score, classification_report
)
from src.preprocessing.data_preprocessor import (
    DeliveryDataPreprocessor, TARGET_CLASSIFICATION, TARGET_REGRESSION, TARGET_ROOT_CAUSE
)

class DeliveryPerformanceModels:
    def __init__(self):
        self.preprocessor = DeliveryDataPreprocessor()
        # 1. Classification: Delay probability
        self.delay_classifier = RandomForestClassifier(
            n_estimators=100, max_depth=12, random_state=42, n_jobs=-1
        )
        # 2. Regression: Delay duration in hours
        self.delay_regressor = RandomForestRegressor(
            n_estimators=100, max_depth=12, random_state=42, n_jobs=-1
        )
        # 3. Root Cause Diagnostic Classifier
        self.root_cause_classifier = GradientBoostingClassifier(
            n_estimators=80, max_depth=6, random_state=42
        )
        self.is_trained = False
        self.evaluation_metrics = {}

    def train_and_evaluate(self, raw_data_path="data/delivery_orders.csv"):
        print(f"Loading data from {raw_data_path}...")
        df = pd.read_csv(raw_data_path)
        
        train_df, val_df, test_df = self.preprocessor.split_dataset(df)
        print(f"Dataset split: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
        
        # Fit preprocessor on training data
        X_train, clean_train = self.preprocessor.fit_transform(train_df)
        X_val, clean_val = self.preprocessor.transform(val_df)
        X_test, clean_test = self.preprocessor.transform(test_df)
        
        # ----------------------------------------------------
        # 1. Train Delay Classifier (is_delayed)
        # ----------------------------------------------------
        y_train_cls = clean_train[TARGET_CLASSIFICATION]
        y_val_cls = clean_val[TARGET_CLASSIFICATION]
        y_test_cls = clean_test[TARGET_CLASSIFICATION]
        
        print("Training Delay Classifier...")
        self.delay_classifier.fit(X_train, y_train_cls)
        y_pred_cls = self.delay_classifier.predict(X_test)
        y_prob_cls = self.delay_classifier.predict_proba(X_test)[:, 1]
        
        cls_metrics = {
            "accuracy": round(float(accuracy_score(y_test_cls, y_pred_cls)), 4),
            "precision": round(float(precision_score(y_test_cls, y_pred_cls, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test_cls, y_pred_cls, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_test_cls, y_pred_cls, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test_cls, y_prob_cls)), 4)
        }
        
        # ----------------------------------------------------
        # 2. Train Delay Regressor (delay_hours for delayed shipments)
        # ----------------------------------------------------
        print("Training Delay Hours Regressor...")
        y_train_reg = clean_train[TARGET_REGRESSION]
        y_test_reg = clean_test[TARGET_REGRESSION]
        self.delay_regressor.fit(X_train, y_train_reg)
        y_pred_reg = self.delay_regressor.predict(X_test)
        
        reg_metrics = {
            "mae_hours": round(float(mean_absolute_error(y_test_reg, y_pred_reg)), 4),
            "rmse_hours": round(float(np.sqrt(mean_squared_error(y_test_reg, y_pred_reg))), 4),
            "r2_score": round(float(r2_score(y_test_reg, y_pred_reg)), 4)
        }
        
        # ----------------------------------------------------
        # 3. Train Root Cause Classifier
        # ----------------------------------------------------
        print("Training Root Cause Diagnostics Classifier...")
        y_train_cause = clean_train[TARGET_ROOT_CAUSE]
        y_test_cause = clean_test[TARGET_ROOT_CAUSE]
        self.root_cause_classifier.fit(X_train, y_train_cause)
        y_pred_cause = self.root_cause_classifier.predict(X_test)
        
        root_cause_metrics = {
            "accuracy": round(float(accuracy_score(y_test_cause, y_pred_cause)), 4),
            "weighted_f1": round(float(f1_score(y_test_cause, y_pred_cause, average="weighted", zero_division=0)), 4)
        }
        
        # Calculate feature importances
        feature_importance = pd.DataFrame({
            "feature": self.preprocessor.feature_names,
            "importance": self.delay_classifier.feature_importances_
        }).sort_values("importance", ascending=False).to_dict(orient="records")
        
        self.evaluation_metrics = {
            "delay_classifier": cls_metrics,
            "delay_regressor": reg_metrics,
            "root_cause_classifier": root_cause_metrics,
            "top_feature_importance": feature_importance[:10]
        }
        self.is_trained = True
        return self.evaluation_metrics

    def predict(self, single_order_dict_or_df):
        if not self.is_trained:
            raise RuntimeError("Model is not trained yet. Call train_and_evaluate or load().")
            
        if isinstance(single_order_dict_or_df, dict):
            df = pd.DataFrame([single_order_dict_or_df])
        else:
            df = single_order_dict_or_df.copy()
            
        X, cleaned_df = self.preprocessor.transform(df)
        
        delay_prob = self.delay_classifier.predict_proba(X)[:, 1]
        is_delayed_pred = (delay_prob >= 0.5).astype(int)
        delay_hours_pred = np.maximum(0.0, self.delay_regressor.predict(X))
        root_cause_pred = self.root_cause_classifier.predict(X)
        
        results = []
        for i in range(len(df)):
            results.append({
                "is_delayed_prediction": int(is_delayed_pred[i]),
                "delay_probability": round(float(delay_prob[i]), 3),
                "predicted_delay_hours": round(float(delay_hours_pred[i]), 2) if is_delayed_pred[i] else 0.0,
                "predicted_root_cause": str(root_cause_pred[i]) if is_delayed_pred[i] else "On-Time Fulfillment"
            })
        return results

    def save(self, model_dir="src/models"):
        os.makedirs(model_dir, exist_ok=True)
        self.preprocessor.save(os.path.join(model_dir, "saved_preprocessor.joblib"))
        model_payload = {
            "delay_classifier": self.delay_classifier,
            "delay_regressor": self.delay_regressor,
            "root_cause_classifier": self.root_cause_classifier,
            "evaluation_metrics": self.evaluation_metrics,
            "is_trained": self.is_trained
        }
        joblib.dump(model_payload, os.path.join(model_dir, "delivery_models.joblib"))
        print(f"Models successfully saved to {model_dir}/delivery_models.joblib")

    @classmethod
    def load(cls, model_dir="src/models"):
        instance = cls()
        instance.preprocessor = DeliveryDataPreprocessor.load(os.path.join(model_dir, "saved_preprocessor.joblib"))
        model_payload = joblib.load(os.path.join(model_dir, "delivery_models.joblib"))
        instance.delay_classifier = model_payload["delay_classifier"]
        instance.delay_regressor = model_payload["delay_regressor"]
        instance.root_cause_classifier = model_payload["root_cause_classifier"]
        instance.evaluation_metrics = model_payload["evaluation_metrics"]
        instance.is_trained = model_payload["is_trained"]
        return instance

if __name__ == "__main__":
    ai_system = DeliveryPerformanceModels()
    metrics = ai_system.train_and_evaluate("data/delivery_orders.csv")
    ai_system.save("src/models")
    print("Training Metrics Summary:")
    print(metrics)

