# run_pipeline.py
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score
import lightgbm as lgb
import joblib

def build_and_train_pipeline(df: pd.DataFrame, target_col: str, model_save_path: str = "models/model.joblib"):
    os.makedirs("models", exist_ok=True)
    
    # 1. Separate features and target
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # 2. Identify column types
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
    
    # 3. Build transformers
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, num_cols),
            ('cat', categorical_transformer, cat_cols)
        ]
    )
    
    # 4. Define model pipeline
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', lgb.LGBMClassifier(n_estimators=100, learning_rate=0.05, random_state=42, verbosity=-1))
    ])
    
    # 5. Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 6. Fit pipeline
    pipeline.fit(X_train, y_train)
    
    # 7. Evaluate
    preds = pipeline.predict(X_test)
    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds, average='weighted')
    print(f"[PIPELINE TRAINED] Test Accuracy: {acc:.4f} | Weighted F1: {f1:.4f}")
    
    # 8. Save artifact
    joblib.dump(pipeline, model_save_path)
    print(f"[SAVED] Pipeline saved to: {model_save_path}")
    return pipeline

if __name__ == "__main__":
    # Synthetic verification run
    sample_df = pd.DataFrame({
        'age': [25, 45, np.nan, 35, 50, 23, 40, 60],
        'income': [50000, 80000, 60000, np.nan, 120000, 45000, 75000, 110000],
        'gender': ['M', 'F', 'F', 'M', 'F', 'M', 'M', 'F'],
        'city': ['Colombo', 'Kandy', 'Colombo', 'Galle', 'Kandy', 'Colombo', 'Galle', 'Colombo'],
        'target': [0, 1, 0, 1, 1, 0, 1, 1]
    })
    build_and_train_pipeline(sample_df, target_col='target')