"""
Data Preprocessing and Feature Engineering Module for Delivery Performance.
Handles:
- Missing value imputation
- Outlier filtering/clipping
- Categorical encoding & Standardization
- Operational delivery performance feature engineering
- Train / Validation / Test dataset splitting
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

NUMERICAL_FEATURES = [
    "package_weight_kg",
    "route_distance_km",
    "warehouse_load_pct",
    "promised_hours",
    "hour_of_day",
    "day_of_week",
    "is_weekend"
]

CATEGORICAL_FEATURES = [
    "warehouse_id",
    "product_category",
    "sla_tier",
    "weather_condition",
    "traffic_density",
    "courier_experience"
]

TARGET_CLASSIFICATION = "is_delayed"
TARGET_REGRESSION = "delay_hours"
TARGET_ROOT_CAUSE = "root_cause"

class DeliveryDataPreprocessor:
    def __init__(self):
        self.preprocessor = None
        self.feature_names = None
        
    def clean_and_engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans data, removes invalid records, and generates operational features.
        """
        df = df.copy()
        
        # Deduplication
        df = df.drop_duplicates(subset=["order_id"]) if "order_id" in df.columns else df.drop_duplicates()
        
        # Date & Temporal Features
        if "order_timestamp" in df.columns:
            df["order_timestamp"] = pd.to_datetime(df["order_timestamp"], errors="coerce")
            df["hour_of_day"] = df["order_timestamp"].dt.hour.fillna(12)
            df["day_of_week"] = df["order_timestamp"].dt.dayofweek.fillna(0)
            df["is_weekend"] = df["day_of_week"].apply(lambda x: 1 if x >= 5 else 0)
        else:
            df["hour_of_day"] = 12
            df["day_of_week"] = 0
            df["is_weekend"] = 0
            
        # Handle Missing Values in key columns
        df["package_weight_kg"] = df["package_weight_kg"].fillna(df["package_weight_kg"].median())
        df["route_distance_km"] = df["route_distance_km"].fillna(df["route_distance_km"].median())
        df["warehouse_load_pct"] = df["warehouse_load_pct"].fillna(75.0)
        df["promised_hours"] = df["promised_hours"].fillna(24.0)
        
        categorical_defaults = {
            "warehouse_id": "WH-CENTRAL-05",
            "product_category": "Electronics",
            "sla_tier": "Next-Day",
            "weather_condition": "Clear",
            "traffic_density": "Moderate",
            "courier_experience": "Mid"
        }
        for col, default_val in categorical_defaults.items():
            if col in df.columns:
                df[col] = df[col].fillna(default_val)
                
        # Outlier handling (clip extreme distance or weights)
        df["route_distance_km"] = np.clip(df["route_distance_km"], a_min=1.0, a_max=300.0)
        df["package_weight_kg"] = np.clip(df["package_weight_kg"], a_min=0.1, a_max=80.0)
        df["warehouse_load_pct"] = np.clip(df["warehouse_load_pct"], a_min=10.0, a_max=100.0)
        
        return df

    def fit_transform(self, df: pd.DataFrame):
        cleaned_df = self.clean_and_engineer_features(df)
        
        self.preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), NUMERICAL_FEATURES),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES)
            ]
        )
        
        X = cleaned_df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]
        X_transformed = self.preprocessor.fit_transform(X)
        
        # Extract feature names
        num_names = NUMERICAL_FEATURES
        cat_encoder = self.preprocessor.named_transformers_["cat"]
        cat_names = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
        self.feature_names = num_names + cat_names
        
        return X_transformed, cleaned_df

    def transform(self, df: pd.DataFrame):
        cleaned_df = self.clean_and_engineer_features(df)
        X = cleaned_df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]
        return self.preprocessor.transform(X), cleaned_df

    def split_dataset(self, df: pd.DataFrame, test_size=0.15, val_size=0.15, random_state=42):
        """
        Splits data into Train (70%), Validation (15%), and Test (15%) splits.
        """
        cleaned_df = self.clean_and_engineer_features(df)
        train_val_df, test_df = train_test_split(cleaned_df, test_size=test_size, random_state=random_state, stratify=cleaned_df[TARGET_CLASSIFICATION] if TARGET_CLASSIFICATION in cleaned_df else None)
        
        val_ratio = val_size / (1.0 - test_size)
        train_df, val_df = train_test_split(train_val_df, test_size=val_ratio, random_state=random_state, stratify=train_val_df[TARGET_CLASSIFICATION] if TARGET_CLASSIFICATION in train_val_df else None)
        
        return train_df, val_df, test_df

    def save(self, filepath="src/models/saved_preprocessor.joblib"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({"preprocessor": self.preprocessor, "feature_names": self.feature_names}, filepath)
        
    @classmethod
    def load(cls, filepath="src/models/saved_preprocessor.joblib"):
        instance = cls()
        data = joblib.load(filepath)
        instance.preprocessor = data["preprocessor"]
        instance.feature_names = data["feature_names"]
        return instance

