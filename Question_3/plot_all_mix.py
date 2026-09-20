import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load Data
dataset_dir = '../Dataset' 
co2_df = pd.read_csv(os.path.join(dataset_dir, 'co2_emissions_yearly.csv'))
energy_df = pd.read_csv(os.path.join(dataset_dir, 'energy_mix_yearly.csv'))

# Merge Data 
merge_cols = ['year', 'country', 'iso3', 'region']
df = pd.merge(energy_df, co2_df, on=merge_cols, how='inner')

# Get latest year data
latest_year = df['year'].max()
df_latest = df[df['year'] == latest_year].copy()

# Select the top 15 highest total CO2 emitters for focus
df_top = df_latest.nlargest(15, 'co2_emissions_mt').sort_values('co2_emissions_mt', ascending=False)

# Prepare categories
categories = df_top['country'].tolist()
coal = df_top['coal_pct'].values
oil = df_top['oil_pct'].values
gas = df_top['gas_pct'].values
nuclear = df_top['nuclear_pct'].values
renewables = df_top['renewables_total_pct'].values

co2_per_capita = df_top['co2_per_capita_t'].values

# Create plot
fig, ax1 = plt.subplots(figsize=(14, 7))

# Define colors
colors = ['#333333', '#8B0000', '#D2691E', '#9370DB', '#2E8B57'] # Coal, Oil, Gas, Nuclear, Renewables

# Stacked Bar Chart
bar_width = 0.6
indices = np.arange(len(categories))

ax1.bar(indices, coal, bar_width, label='Coal %', color=colors[0])
prev = coal
ax1.bar(indices, oil, bar_width, bottom=prev, label='Oil %', color=colors[1])
prev = prev + oil
ax1.bar(indices, gas, bar_width, bottom=prev, label='Gas %', color=colors[2])
prev = prev + gas
ax1.bar(indices, nuclear, bar_width, bottom=prev, label='Nuclear %', color=colors[3])
prev = prev + nuclear
ax1.bar(indices, renewables, bar_width, bottom=prev, label='Renewables %', color=colors[4])

ax1.set_xlabel('Top 15 CO2 Emitters (Sorted by Total Mass)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Energy Mix Share (%)', fontsize=12, fontweight='bold')
ax1.set_xticks(indices)
ax1.set_xticklabels(categories, rotation=45, ha='right')
ax1.set_ylim(0, 100)

# Secondary Axis for CO2 Per Capita
ax2 = ax1.twinx()
ax2.plot(indices, co2_per_capita, color='blue', marker='o', linewidth=2.5, markersize=8, label='CO2 per Capita (t)')
ax2.set_ylabel('CO2 Emissions per Capita (t)', color='blue', fontsize=12, fontweight='bold')
ax2.tick_params(axis='y', labelcolor='blue')

# Title and Layout
plt.title(f'Global Energy Mix Breakdown vs CO2 Footprint (Top 15 Emitters, {latest_year})', fontsize=15, fontweight='bold')

# Combine legends
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=11)

plt.grid(axis='y', linestyle='--', alpha=0.3)
plt.tight_layout()

# Save
os.makedirs('plots', exist_ok=True)
plt.savefig('plots/energy_mix_all_vs_co2.png', dpi=300, bbox_inches='tight')
print("Multi-variable visualization saved to plots/energy_mix_all_vs_co2.png")
