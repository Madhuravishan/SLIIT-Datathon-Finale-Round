# Executive Summary: Question 3 Analysis
**Renewable Energy Transition Scenario Modelling**

## 3.1 Energy Mix to CO2 Relationship

Based on the datasets (2000-2026), each country's progress was analyzed via K-Means Clustering on their annualized rate of renewable energy adoption. 

The countries group cleanly into 3 Archetypes:

- **Business-as-Usual (BAU) (19 Countries)**: Continues current minimal or static trend in renewables adoption.
- **Moderate Transition (18 Countries)**: Steady positive improvement replacing fossil fuels. 
- **Accelerated Transition (13 Countries)**: Highly aggressive deployment of renewables significantly outpacing standard adoption curves.

*(Visualizations saved in the `plots/` directory: energy_mix_vs_co2.png and trajectory_examples.png)*

## 3.2 Forecasting Future Emissions (2026-2030)

Forecasting used simple compounding growth models built on the country's past 5-year CAGR of CO2 emissions. 

**Model Drivers and Parameter Choices:**
1. **BAU Model**: Projects CO2 emissions growing/shrinking strictly at the recent 5-year CAGR.
2. **Moderate Transition Model**: Adjusts the CO2 CAGR downward by **-2%** points annually compared to BAU, capturing the steady offset provided by increased renewables. 
3. **Accelerated Transition Model**: Adjusts the CO2 CAGR downward by **-5%** points annually compared to BAU, indicating a much starker deployment (equivalent to a rapid Net-Zero styled transition). 

Forecast data is available in `output/forecasts_2026_2030.csv`.

## 3.3 Key Insights

1. **Uneven Transition**: A vast majority of the emissions profile relies heavily on the 'Accelerated' transitions of a few key developed or aggressively progressing nations, while many developing regions remain locked in the BAU archetype due to immediate industrialization scaling.
2. **Emissions Elasticity**: There is a lag in CO2 decoupling; a single percentage point rise in renewables does not immediately trigger an equal drop in emissions if absolute energy demand is still scaling exponentially.
3. **Optimistic Trajectories**: In an Accelerated Scenario, we see peak emissions reached by several current top-emitters before 2030, reversing historical upward trends. 
