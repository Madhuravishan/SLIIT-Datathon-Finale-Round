# test_env.py
import pandas as pd
import numpy as np
import joblib
import openpyxl
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import lightgbm as lgb
import xgboost as xgb

print("--> [1/4] Testing Data Structures & Excel...")
df = pd.DataFrame({"A": [1, 2, np.nan, 4], "B": ["x", "y", "x", "z"]})
df["A"] = df["A"].fillna(df["A"].median())
df.to_excel("temp_test.xlsx", index=False)
df_excel = pd.read_excel("temp_test.xlsx")
assert len(df_excel) == 4
print("    Data and Excel Engine: OK")

print("--> [2/4] Testing Machine Learning Pipelines...")
X, y = make_classification(n_samples=200, n_features=6, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Test LightGBM
clf_lgb = lgb.LGBMClassifier(verbosity=-1, random_state=42)
clf_lgb.fit(X_train, y_train)
pred_lgb = clf_lgb.predict(X_test)
print(f"    LightGBM Fit: OK (Accuracy: {accuracy_score(y_test, pred_lgb):.2f})")

# Test XGBoost
clf_xgb = xgb.XGBClassifier(eval_metric="logloss", random_state=42)
clf_xgb.fit(X_train, y_train)
pred_xgb = clf_xgb.predict(X_test)
print(f"    XGBoost Fit: OK (Accuracy: {accuracy_score(y_test, pred_xgb):.2f})")

print("--> [3/4] Testing Model Serialization (Joblib)...")
joblib.dump(clf_lgb, "temp_model.joblib")
loaded_model = joblib.load("temp_model.joblib")
assert loaded_model.predict(X_test).shape == y_test.shape
print("    Joblib Dump & Load: OK")

# Clean temporary test files
import os
os.remove("temp_test.xlsx")
os.remove("temp_model.joblib")

print("--> [4/4] Environment verification successful. System is ready.")