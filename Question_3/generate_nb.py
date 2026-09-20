import json

cells = []

def add_md(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": [text + "\n"]})

def add_code(text):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": [line + "\n" for line in text.split('\n')]})

add_md("# Question 3: Energy Transition Modeling and Future Emissions Forecasting\n\nThis notebook analyzes global energy-transition patterns using K-Means clustering and predicts future CO2 emissions (2026-2030) using deterministic Compound Growth Growth Rate (CAGR) modeling. All generated visualizations are displayed below their respective methodology sections.")

add_md("## Phase 1: Environment Setup and Data Loading\nImporting libraries and merging the Energy Mix and CO2 Datasets.")
add_code("""import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

os.makedirs('plots', exist_ok=True)
os.makedirs('output', exist_ok=True)

dataset_dir = '../Dataset' 
co2_df = pd.read_csv(os.path.join(dataset_dir, 'co2_emissions_yearly.csv'))
energy_df = pd.read_csv(os.path.join(dataset_dir, 'energy_mix_yearly.csv'))

merge_cols = ['year', 'country', 'iso3', 'region']
df = pd.merge(energy_df, co2_df, on=merge_cols, how='inner')
""")

add_md("## Phase 2: K-Means Clustering for Transition Archetypes (Q3.1)\nCalculating the 26-year 'Annualized Rate of Change' for renewable adoption for every country, then feeding it into a **K-Means Clustering model (k=3)**.")
add_code("""trend_data = []
for country, group in df.groupby('country'):
    group = group.sort_values('year')
    if len(group) > 1:
        start_year = group['year'].min()
        end_year = group['year'].max()
        start_ren = group[group['year'] == start_year]['renewables_total_pct'].values[0]
        end_ren = group[group['year'] == end_year]['renewables_total_pct'].values[0]
        start_co2 = group[group['year'] == start_year]['co2_per_capita_t'].values[0]
        end_co2 = group[group['year'] == end_year]['co2_per_capita_t'].values[0]
        
        years_span = end_year - start_year
        ren_annual_change = (end_ren - start_ren) / years_span if years_span > 0 else 0
        co2_annual_change = (end_co2 - start_co2) / years_span if years_span > 0 else 0
        
        trend_data.append({
            'country': country,
            'region': group['region'].iloc[0],
            'ren_annual_change': ren_annual_change,
            'co2_annual_change': co2_annual_change
        })

trend_df = pd.DataFrame(trend_data)
kmeans = KMeans(n_clusters=3, random_state=42)
trend_df['cluster'] = kmeans.fit_predict(trend_df[['ren_annual_change']])

cluster_centers = kmeans.cluster_centers_.flatten()
sorted_indices = np.argsort(cluster_centers)
label_map = {
    sorted_indices[0]: 'Business-as-Usual',
    sorted_indices[1]: 'Moderate Transition',
    sorted_indices[2]: 'Accelerated Transition'
}
trend_df['archetype'] = trend_df['cluster'].map(label_map)
df = df.merge(trend_df[['country', 'archetype']], on='country', how='left')
print(trend_df['archetype'].value_counts())
""")

add_md("### Visualization 2.1: Archetype Scatter Plot (Spatial Validation)\nPlotting Renewables % against CO2 per Capita to visually validate that our math successfully isolated the 'Accelerated' nations into a lower-carbon quadrant.")
add_code("""plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=df[df['year'] == df['year'].max()],
    x='renewables_total_pct', 
    y='co2_per_capita_t',
    hue='archetype',
    palette={'Business-as-Usual': '#E63946', 'Moderate Transition': '#F4A261', 'Accelerated Transition': '#2A9D8F'},
    s=100, alpha=0.8
)
plt.title(f'Energy Mix vs CO2 Initial Footprint (Year {df["year"].max()})')
plt.xlabel('Renewables Total %')
plt.legend(title='Transition Archetype')
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig('plots/energy_mix_vs_co2.png', dpi=300, bbox_inches='tight')
plt.close()
""")
add_md("![Scatter Plot: Archetype spatial validation](plots/energy_mix_vs_co2.png)")

add_md("### Visualization 2.2: Historical Timeline Trajectories\nTracking how representative countries from each archetype actually behaved from 2000 to today.")
add_code("""plt.figure(figsize=(12, 6))
rep_countries = []
for arch in ['Business-as-Usual', 'Moderate Transition', 'Accelerated Transition']:
    arch_df = trend_df[trend_df['archetype'] == arch]
    if not arch_df.empty:
        center_val = np.mean(arch_df['ren_annual_change'])
        rep_country = arch_df.iloc[(arch_df['ren_annual_change'] - center_val).abs().argsort()[:1]]['country'].values[0]
        rep_countries.append((arch, rep_country))

for arch, c in rep_countries:
    c_data = df[df['country'] == c].sort_values('year')
    plt.plot(c_data['year'], c_data['renewables_total_pct'], marker='o', label=f'{c} ({arch})')
    
plt.title('Renewables % Trajectories: Representative Countries by Archetype')
plt.xlabel('Year')
plt.ylabel('Renewables Total %')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig('plots/trajectory_examples.png', dpi=300, bbox_inches='tight')
plt.close()
""")
add_md("![Timeline Trajectory](plots/trajectory_examples.png)")

add_md("### Visualization 2.3: Dual-Axis Multi-Variable Stacked Bar Chart\nMapping the full energy supply against the CO2 output for the Top 15 massive global emitters.")
add_code("""df_top = df[df['year'] == df['year'].max()].nlargest(15, 'co2_emissions_mt').sort_values('co2_emissions_mt', ascending=False)
categories = df_top['country'].tolist()
fig, ax1 = plt.subplots(figsize=(14, 7))
colors = ['#333333', '#8B0000', '#D2691E', '#9370DB', '#2E8B57'] 
bar_width = 0.6
indices = np.arange(len(categories))

coal = df_top['coal_pct'].values
oil = df_top['oil_pct'].values
gas = df_top['gas_pct'].values
nuclear = df_top['nuclear_pct'].values
renewables = df_top['renewables_total_pct'].values
co2 = df_top['co2_per_capita_t'].values

ax1.bar(indices, coal, bar_width, label='Coal %', color=colors[0])
prev = coal
ax1.bar(indices, oil, bar_width, bottom=prev, label='Oil %', color=colors[1])
prev = prev + oil
ax1.bar(indices, gas, bar_width, bottom=prev, label='Gas %', color=colors[2])
prev = prev + gas
ax1.bar(indices, nuclear, bar_width, bottom=prev, label='Nuclear %', color=colors[3])
prev = prev + nuclear
ax1.bar(indices, renewables, bar_width, bottom=prev, label='Renewables %', color=colors[4])
ax1.set_xticks(indices)
ax1.set_xticklabels(categories, rotation=45, ha='right')

ax2 = ax1.twinx()
ax2.plot(indices, co2, color='blue', marker='o', linewidth=2.5, markersize=8, label='CO2 per Capita (t)')

plt.title('Global Energy Mix Breakdown vs CO2 Footprint (Top 15 Emitters)', fontsize=15, fontweight='bold')
plt.savefig('plots/energy_mix_all_vs_co2.png', dpi=300, bbox_inches='tight')
plt.close()
""")
add_md("![Dual Axis Stacked Bar Plot](plots/energy_mix_all_vs_co2.png)")

add_md("## Phase 3: Future Emissions Forecast (2026-2030) (Q3.2)\nUtilizing a deterministic Compound Growth Model building upon the 5-Year CAGR. We project 3 paths: BAU (0% mod), Moderate (-2% mod), and Accelerated (-5% mod).")
add_code("""forecast_years = list(range(2026, 2031))
forecast_results = []
for idx, row in trend_df.iterrows():
    c = row['country']
    c_data = df[df['country'] == c].sort_values('year')
    recent_5y = c_data[c_data['year'] >= 2021]
    
    if len(recent_5y) < 2: continue
    start_co2, end_co2 = max(recent_5y.iloc[0]['co2_emissions_mt'], 0.001), recent_5y.iloc[-1]['co2_emissions_mt']
    years_diff = recent_5y['year'].iloc[-1] - recent_5y['year'].iloc[0]
    
    co2_cagr = (end_co2 / start_co2)**(1/years_diff) - 1 if years_diff > 0 else 0
    bau_cagr = np.clip(co2_cagr, -0.15, 0.15)
    mod_cagr = np.clip(co2_cagr - 0.02, -0.20, 0.15) 
    acc_cagr = np.clip(co2_cagr - 0.05, -0.30, 0.15)
    last_co2 = c_data.iloc[-1]['co2_emissions_mt']
    
    for y, dy in enumerate(range(1, len(forecast_years) + 1)):
        forecast_results.append({
            'country': c, 'year': forecast_years[y],
            'BAU_MT': last_co2 * ((1 + bau_cagr) ** dy),
            'Moderate_MT': last_co2 * ((1 + mod_cagr) ** dy),
            'Accelerated_MT': last_co2 * ((1 + acc_cagr) ** dy)
        })

forecast_df = pd.DataFrame(forecast_results)
forecast_df.to_csv('output/forecasts_2026_2030.csv', index=False)
""")

add_md("### Visualization 3.1: Timeline Target Projections\nVisualizing the divergence in our CAGR projection for a top emitter to prove how the 'Accelerated' model forces emissions to hit 'Peak'.")
add_code("""top_emitters = df[df['year'] == df['year'].max()].nlargest(5, 'co2_emissions_mt')['country'].tolist()
plt.figure(figsize=(10, 6))
for c in top_emitters[:1]:
    hist_data = df[df['country'] == c].sort_values('year')
    f_data = forecast_df[forecast_df['country'] == c]
    
    plt.plot(hist_data['year'], hist_data['co2_emissions_mt'], label=f'{c} Historical', marker='.', color='black')
    plt.plot(f_data['year'], f_data['BAU_MT'], 'r--', label='BAU')
    plt.plot(f_data['year'], f_data['Moderate_MT'], 'C1--', label='Moderate')
    plt.plot(f_data['year'], f_data['Accelerated_MT'], 'g--', label='Accelerated')

plt.title('CO2 Emissions Potential Forecast Scenarios for Top Emitter')
plt.legend()
plt.savefig('plots/forecast_scenarios_example.png', dpi=300, bbox_inches='tight')
plt.close()
""")
add_md("![Forecast Scenarios Output](plots/forecast_scenarios_example.png)")

notebook = {
 "cells": cells,
 "metadata": {"language_info": {"name": "python", "version": "3"}},
 "nbformat": 4,
 "nbformat_minor": 4
}
with open('solution_q3.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1)
