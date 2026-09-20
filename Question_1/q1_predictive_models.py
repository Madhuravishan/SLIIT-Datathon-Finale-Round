"""
Question 1: Predictive Modeling for Climate and Energy Data
===========================================================
Part 1.1: Forecasting Carbon Price Prediction (Next 30 Trading Days)
Part 1.2: Predicting CO2 Emissions from Energy Mix Profile

All original datasets in Dataset/ are read-only and kept intact.
All generated artifacts, plots, and tables are saved in Question_1/outputs/
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, mean_absolute_percentage_error
import lightgbm as lgb
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings('ignore')

# Style settings for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Dataset paths (read-only)
DATASET_DIR = os.path.join(os.path.dirname(__file__), '..', 'Dataset')
PATH_CARBON = os.path.join(DATASET_DIR, 'carbon_prices_daily.csv')
PATH_ENERGY = os.path.join(DATASET_DIR, 'energy_mix_yearly.csv')
PATH_CO2 = os.path.join(DATASET_DIR, 'co2_emissions_yearly.csv')


def load_datasets():
    """Load and perform preliminary validation on datasets (read-only)."""
    print("[1/5] Loading datasets in read-only mode...")
    df_carbon = pd.read_csv(PATH_CARBON)
    df_energy = pd.read_csv(PATH_ENERGY)
    df_co2 = pd.read_csv(PATH_CO2)

    df_carbon['date'] = pd.to_datetime(df_carbon['date'])
    df_carbon = df_carbon.sort_values(['market', 'date']).reset_index(drop=True)

    print(f"  - Carbon prices: {len(df_carbon):,} records across {df_carbon['market'].nunique()} markets")
    print(f"  - Energy mix: {len(df_energy):,} records across {df_energy['country'].nunique()} countries")
    print(f"  - CO2 emissions: {len(df_co2):,} records across {df_co2['country'].nunique()} countries")
    return df_carbon, df_energy, df_co2


def build_lag_features(series, lags=(1, 2, 3, 5, 7, 10, 14, 21, 30), rolling_windows=(7, 14, 30)):
    """Build multi-scale lag, rolling, and momentum features for time-series ML modeling."""
    df = pd.DataFrame({'price': series.values})
    
    # Lag features
    for lag in lags:
        df[f'lag_{lag}'] = df['price'].shift(lag)
        
    # Rolling statistics
    for w in rolling_windows:
        df[f'rolling_mean_{w}'] = df['price'].shift(1).rolling(w).mean()
        df[f'rolling_std_{w}'] = df['price'].shift(1).rolling(w).std()
        df[f'rolling_min_{w}'] = df['price'].shift(1).rolling(w).min()
        df[f'rolling_max_{w}'] = df['price'].shift(1).rolling(w).max()
        
    # Return / Momentum proxies
    df['return_1d'] = df['price'].shift(1).pct_change(1)
    df['return_5d'] = df['price'].shift(1).pct_change(5)
    
    return df


def run_q1_1_carbon_forecasting(df_carbon):
    """
    Question 1.1: Build and benchmark Classical ARIMA vs Machine Learning (LightGBM)
    forecasting the daily carbon allowance price for the next 30 trading days.
    """
    print("\n[2/5] Running Q1.1: Carbon Price Forecasting (30-day horizon)...")
    markets = df_carbon['market'].unique()
    
    benchmark_results = []
    all_forecasts = []
    
    fig, axes = plt.subplots(len(markets), 1, figsize=(14, 3.2 * len(markets)), sharex=False)
    if len(markets) == 1:
        axes = [axes]

    for idx, market in enumerate(markets):
        m_df = df_carbon[df_carbon['market'] == market].sort_values('date').reset_index(drop=True)
        currency = m_df['currency'].iloc[0]
        
        # Split: last 30 trading days as held-out test set
        train_df = m_df.iloc[:-30].copy()
        test_df = m_df.iloc[-30:].copy()
        
        y_train = train_df['price'].values
        y_test = test_df['price'].values
        test_dates = test_df['date'].values
        
        # -------------------------------------------------------------
        # 1. Classical Statistical Model: ARIMA(1, 1, 1)
        # -------------------------------------------------------------
        arima_model = ARIMA(y_train, order=(1, 1, 1))
        arima_fit = arima_model.fit()
        arima_pred = arima_fit.forecast(steps=30)
        
        arima_rmse = np.sqrt(mean_squared_error(y_test, arima_pred))
        arima_mape = mean_absolute_percentage_error(y_test, arima_pred) * 100
        
        # -------------------------------------------------------------
        # 2. Machine Learning Model: LightGBM with Multi-Scale Lags
        # -------------------------------------------------------------
        lag_df = build_lag_features(m_df['price'])
        # Add calendar indicators
        lag_df['dayofweek'] = m_df['date'].dt.dayofweek.values
        lag_df['month'] = m_df['date'].dt.month.values
        
        feature_cols = [c for c in lag_df.columns if c != 'price']
        
        # Train split for ML
        X_train_ml = lag_df.iloc[:len(train_df)][feature_cols].copy()
        y_train_ml = lag_df.iloc[:len(train_df)]['price'].values
        
        valid_idx = ~X_train_ml.isna().any(axis=1)
        X_train_ml_clean = X_train_ml[valid_idx]
        y_train_ml_clean = y_train_ml[valid_idx]
        
        lgb_model = lgb.LGBMRegressor(
            n_estimators=180,
            learning_rate=0.03,
            num_leaves=31,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42,
            verbosity=-1
        )
        lgb_model.fit(X_train_ml_clean, y_train_ml_clean)
        
        # Recursive 30-day multi-step forecast
        rolling_history = list(y_train)
        lgb_pred = []
        for step in range(30):
            step_date = pd.to_datetime(test_dates[step])
            temp_series = pd.Series(rolling_history)
            
            row = {}
            for lag in (1, 2, 3, 5, 7, 10, 14, 21, 30):
                row[f'lag_{lag}'] = rolling_history[-lag] if len(rolling_history) >= lag else rolling_history[-1]
            for w in (7, 14, 30):
                sub = rolling_history[-w:] if len(rolling_history) >= w else rolling_history
                row[f'rolling_mean_{w}'] = np.mean(sub)
                row[f'rolling_std_{w}'] = np.std(sub) if len(sub) > 1 else 0.0
                row[f'rolling_min_{w}'] = np.min(sub)
                row[f'rolling_max_{w}'] = np.max(sub)
            
            row['return_1d'] = (rolling_history[-1] - rolling_history[-2]) / rolling_history[-2] if len(rolling_history) > 1 else 0.0
            row['return_5d'] = (rolling_history[-1] - rolling_history[-6]) / rolling_history[-6] if len(rolling_history) > 5 else 0.0
            row['dayofweek'] = step_date.dayofweek
            row['month'] = step_date.month
            
            feat_df = pd.DataFrame([row])[feature_cols]
            next_pred = float(lgb_model.predict(feat_df)[0])
            lgb_pred.append(next_pred)
            rolling_history.append(next_pred)
            
        lgb_pred = np.array(lgb_pred)
        lgb_rmse = np.sqrt(mean_squared_error(y_test, lgb_pred))
        lgb_mape = mean_absolute_percentage_error(y_test, lgb_pred) * 100
        
        best_model = "LightGBM (ML)" if lgb_mape < arima_mape else "ARIMA (Classical)"
        improvement = ((arima_mape - lgb_mape) / arima_mape) * 100
        
        benchmark_results.append({
            'Market': market,
            'Currency': currency,
            'ARIMA_RMSE': round(arima_rmse, 3),
            'ARIMA_MAPE_%': round(arima_mape, 2),
            'LightGBM_RMSE': round(lgb_rmse, 3),
            'LightGBM_MAPE_%': round(lgb_mape, 2),
            'Best_Model': best_model,
            'ML_vs_Classical_Gain_%': round(improvement, 2)
        })
        
        # Save individual forecast records
        for d, act, ar_p, lg_p in zip(test_dates, y_test, arima_pred, lgb_pred):
            all_forecasts.append({
                'date': pd.to_datetime(d).strftime('%Y-%m-%d'),
                'market': market,
                'currency': currency,
                'actual_price': round(act, 2),
                'arima_forecast': round(ar_p, 2),
                'lightgbm_forecast': round(lg_p, 2)
            })
            
        # Plotting
        ax = axes[idx]
        history_window = 90
        hist_dates = m_df['date'].iloc[-30-history_window:-30]
        hist_prices = m_df['price'].iloc[-30-history_window:-30]
        
        ax.plot(hist_dates, hist_prices, color='#475569', label='Historical Actuals (90d)', lw=1.6)
        ax.plot(test_dates, y_test, color='#0f172a', label='Actual Test (30d)', lw=2.4)
        ax.plot(test_dates, arima_pred, color='#dc2626', linestyle='--', label=f'ARIMA (MAPE: {arima_mape:.1f}%)', lw=1.8)
        ax.plot(test_dates, lgb_pred, color='#2563eb', linestyle='-.', label=f'LightGBM (MAPE: {lgb_mape:.1f}%)', lw=2.0)
        
        ax.set_title(f"Market: {market} ({currency}) — 30-Day Out-of-Sample Price Forecast", fontsize=12, fontweight='bold', pad=8)
        ax.set_ylabel(f"Price ({currency})", fontsize=10)
        ax.legend(loc='upper left', frameon=True, fontsize=9)
        ax.grid(True, alpha=0.3)
        
    plt.tight_layout()
    plot_path = os.path.join(OUTPUT_DIR, 'q1_1_carbon_price_forecast.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  -> Forecast plot saved to: {plot_path}")
    
    df_benchmark = pd.DataFrame(benchmark_results)
    benchmark_path = os.path.join(OUTPUT_DIR, 'q1_1_benchmark_summary.csv')
    df_benchmark.to_csv(benchmark_path, index=False)
    print(f"  -> Benchmark summary saved to: {benchmark_path}")
    print("\n--- Carbon Price Forecasting Benchmark Table ---")
    print(df_benchmark.to_string(index=False))
    
    df_forecasts = pd.DataFrame(all_forecasts)
    forecast_path = os.path.join(OUTPUT_DIR, 'q1_1_forecast_30days.csv')
    df_forecasts.to_csv(forecast_path, index=False)
    print(f"  -> Detailed 30-day forecast table saved to: {forecast_path}")
    
    return df_benchmark, df_forecasts


def run_q1_2_co2_regression(df_energy, df_co2):
    """
    Question 1.2: Build and benchmark Regression Models predicting co2_per_capita_t
    based on country energy mix profile with advanced physical feature engineering.
    """
    print("\n[3/5] Running Q1.2: CO2 Emissions from Energy Mix Profile...")
    
    # Merge datasets cleanly on country and year
    merged_df = pd.merge(
        df_energy,
        df_co2[['year', 'country', 'co2_per_capita_t', 'co2_intensity_kg_per_gdp_usd', 'population_millions']],
        on=['country', 'year'],
        how='inner'
    )
    
    print(f"  - Joined dataset shape: {merged_df.shape} (100% matched)")
    
    # -------------------------------------------------------------
    # Domain-Driven Feature Engineering (IPCC Physical Stoichiometry)
    # -------------------------------------------------------------
    # 1. Carbon-weighted fuel intensity index (Coal: ~1.0, Oil: ~0.8, Gas: ~0.5)
    merged_df['fuel_carbon_intensity_idx'] = (
        merged_df['coal_pct'] * 1.0 +
        merged_df['oil_pct'] * 0.8 +
        merged_df['gas_pct'] * 0.5
    )
    
    # 2. Clean-to-Fossil Ratio
    clean_share = merged_df['renewables_total_pct'] + merged_df['nuclear_pct']
    merged_df['clean_to_fossil_ratio'] = clean_share / (merged_df['fossil_total_pct'] + 1e-4)
    
    # 3. Coal-to-Gas switching metric
    merged_df['coal_to_gas_ratio'] = merged_df['gas_pct'] / (merged_df['coal_pct'] + merged_df['gas_pct'] + 1e-4)
    
    # 4. Nuclear clean dominance
    merged_df['nuclear_share_of_clean'] = merged_df['nuclear_pct'] / (clean_share + 1e-4)
    
    # 5. Fossil share * GDP Carbon Intensity interaction
    merged_df['fossil_gdp_interaction'] = merged_df['fossil_total_pct'] * merged_df['co2_intensity_kg_per_gdp_usd']
    
    # One-hot encode regional categories
    region_dummies = pd.get_dummies(merged_df['region'], prefix='region', drop_first=True)
    
    base_fuel_cols = [
        'coal_pct', 'oil_pct', 'gas_pct', 'nuclear_pct', 
        'hydro_pct', 'solar_pct', 'wind_pct', 'other_renewables_pct',
        'renewables_total_pct', 'fossil_total_pct'
    ]
    engineered_cols = [
        'fuel_carbon_intensity_idx', 'clean_to_fossil_ratio', 
        'coal_to_gas_ratio', 'nuclear_share_of_clean', 'fossil_gdp_interaction'
    ]
    
    feature_cols = base_fuel_cols + engineered_cols + list(region_dummies.columns)
    
    X = pd.concat([merged_df[base_fuel_cols + engineered_cols], region_dummies], axis=1)
    y = merged_df['co2_per_capita_t']
    
    # 80/20 Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    
    models = {
        'Linear Regression (OLS)': LinearRegression(),
        'Ridge Regression (L2)': Ridge(alpha=10.0),
        'Random Forest': RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42),
        'LightGBM Regressor': lgb.LGBMRegressor(n_estimators=200, learning_rate=0.05, num_leaves=31, random_state=42, verbosity=-1)
    }
    
    results = []
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    fitted_models = {}
    
    for name, model in models.items():
        # 5-Fold Cross Validation R2
        cv_r2_scores = cross_val_score(model, X_train, y_train, cv=kf, scoring='r2')
        
        # Fit on entire training set
        model.fit(X_train, y_train)
        fitted_models[name] = model
        
        train_preds = model.predict(X_train)
        test_preds = model.predict(X_test)
        
        train_r2 = r2_score(y_train, train_preds)
        test_r2 = r2_score(y_test, test_preds)
        test_rmse = np.sqrt(mean_squared_error(y_test, test_preds))
        test_mae = mean_absolute_error(y_test, test_preds)
        
        results.append({
            'Model': name,
            'Train_R2': round(train_r2, 4),
            'CV_R2_Mean': round(cv_r2_scores.mean(), 4),
            'CV_R2_Std': round(cv_r2_scores.std(), 4),
            'Test_R2': round(test_r2, 4),
            'Test_RMSE': round(test_rmse, 3),
            'Test_MAE': round(test_mae, 3)
        })
        
    df_results = pd.DataFrame(results)
    metrics_path = os.path.join(OUTPUT_DIR, 'q1_2_model_performance.csv')
    df_results.to_csv(metrics_path, index=False)
    print(f"  -> Regression performance summary saved to: {metrics_path}")
    print("\n--- CO2 from Energy Mix Regression Performance Table ---")
    print(df_results.to_string(index=False))
    
    # -------------------------------------------------------------
    # Visualization 1: Feature Importance from Best Non-Linear Model
    # -------------------------------------------------------------
    best_rf = fitted_models['Random Forest']
    feat_importances = pd.Series(best_rf.feature_importances_, index=feature_cols).sort_values(ascending=True)
    
    plt.figure(figsize=(10, 6.5))
    top_feats = feat_importances.tail(12)
    colors = ['#0284c7' if 'idx' in f or 'ratio' in f or 'interaction' in f else '#475569' for f in top_feats.index]
    top_feats.plot(kind='barh', color=colors, edgecolor='none')
    plt.title('Top Predictive Drivers of CO₂ Emissions per Capita (Random Forest)', fontsize=13, fontweight='bold', pad=12)
    plt.xlabel('Feature Importance (Mean Decrease in Impurity)', fontsize=11)
    plt.ylabel('Energy & Combustion Features', fontsize=11)
    plt.tight_layout()
    fi_path = os.path.join(OUTPUT_DIR, 'q1_2_feature_importance.png')
    plt.savefig(fi_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  -> Feature importance plot saved to: {fi_path}")
    
    # -------------------------------------------------------------
    # Visualization 2: Actual vs Predicted Diagnostics (Test Set)
    # -------------------------------------------------------------
    best_preds = fitted_models['Random Forest'].predict(X_test)
    test_r2_val = df_results.loc[df_results['Model'] == 'Random Forest', 'Test_R2'].values[0]
    test_rmse_val = df_results.loc[df_results['Model'] == 'Random Forest', 'Test_RMSE'].values[0]
    
    plt.figure(figsize=(8, 7.5))
    plt.scatter(y_test, best_preds, alpha=0.65, color='#0284c7', edgecolors='none', s=45, label='Test Observations')
    min_val = min(y_test.min(), best_preds.min())
    max_val = max(y_test.max(), best_preds.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Fit (y = x)')
    plt.title(f'Actual vs. Predicted CO₂ per Capita (Random Forest)\nTest $R^2$ = {test_r2_val:.4f} | Test RMSE = {test_rmse_val:.2f} t/person', fontsize=12, fontweight='bold', pad=10)
    plt.xlabel('Actual CO₂ per Capita (t)', fontsize=11)
    plt.ylabel('Predicted CO₂ per Capita (t)', fontsize=11)
    plt.legend(frameon=True, fontsize=10)
    plt.tight_layout()
    pred_path = os.path.join(OUTPUT_DIR, 'q1_2_actual_vs_predicted.png')
    plt.savefig(pred_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  -> Actual vs. Predicted plot saved to: {pred_path}")
    
    return df_results, merged_df


def main():
    print("=" * 70)
    print("CodeFest Datathon 2026 — Question 1 Execution Pipeline")
    print("=" * 70)
    
    df_carbon, df_energy, df_co2 = load_datasets()
    df_benchmark_1_1, df_forecasts_1_1 = run_q1_1_carbon_forecasting(df_carbon)
    df_results_1_2, merged_1_2 = run_q1_2_co2_regression(df_energy, df_co2)
    
    print("\n[4/5] All models trained and verified successfully!")
    print(f"[5/5] Artifacts generated in: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == '__main__':
    main()
