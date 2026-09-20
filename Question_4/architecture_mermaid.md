# CarbonPulse OS — Solution Architecture Diagram

This architecture diagram connects all multi-source datasets, feature engineering pipelines, trained machine learning models (Q1, Q2, Q3), and enterprise delivery interfaces.

```mermaid
flowchart TD
    %% Styling
    classDef ingestion fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#ffffff;
    classDef processing fill:#1e293b,stroke:#10b981,stroke-width:2px,color:#ffffff;
    classDef engine fill:#1e293b,stroke:#8b5cf6,stroke-width:2px,color:#ffffff;
    classDef api fill:#1e293b,stroke:#f59e0b,stroke-width:2px,color:#ffffff;
    classDef ui fill:#0f172a,stroke:#06b6d4,stroke-width:3px,color:#ffffff;

    subgraph L1["Layer 1: Real-Time Multi-Source Ingestion Engine"]
        D1["Daily Carbon Exchange Feeds<br/>(ICE, EEX, KRX, California ARB)"]:::ingestion
        D2["NOAA & GDACS Extreme Weather & Disaster APIs<br/>(Hurricanes, Floods, Heatwaves)"]:::ingestion
        D3["UNFCCC & Policy Milestones<br/>(COP Summits, Statutory ETS Reviews)"]:::ingestion
        D4["IEA & National Energy Mix Databases<br/>(Coal, Oil, Gas, Nuclear, Renewables)"]:::ingestion
    end

    subgraph L2["Layer 2: Event Harmonization & Feature Engineering Pipeline"]
        F1["Trading Calendar Smoothing<br/>(Weekend/Holiday Market Roll-Forward)"]:::processing
        F2["Event Proximity & Decay Engine<br/>(Days Until Policy, Shock Decay τ=7d/30d)"]:::processing
        F3["Stoichiometric Chemistry Transformer<br/>(Carbon Intensity & Fossil-GDP Interaction)"]:::processing
        F4["Jurisdiction Alignment Router<br/>(EU_ETS, California, RGGI, UK, China)"]:::processing
    end

    subgraph L3["Layer 3: Core AI & Econometric Analytics Engine"]
        M1["Module 1: 30-Day Autoregressive Forecaster<br/>(ARIMA Closed-Form Shock Dampener - Q1.1)"]:::engine
        M2["Module 2: Event Shock & Directional Classifier<br/>(LightGBM Event Shock Lift - Q2)"]:::engine
        M3["Module 3: Stoichiometric Emissions Simulator<br/>(Random Forest R²=0.945 - Q1.2)"]:::engine
        M4["Module 4: 2030 Transition Scenario Engine<br/>(K-Means Archetypes & CAGR Divergence - Q3)"]:::engine
    end

    subgraph L4["Layer 4: Enterprise Delivery & Presentation Layer"]
        API["High-Throughput API Gateway<br/>(REST & WebSockets / Bloomberg Connector)"]:::api
        UI1["CarbonPulse Executive Dashboard<br/>(Real-Time Forecasts & Confidence Bands)"]:::ui
        UI2["Shock Radar & Alert Center<br/>(Pre-COP Countdown & Disaster Volatility)"]:::ui
        UI3["Interactive Transition Simulator<br/>(Live Energy Mix Sliders & 2030 Compliance)"]:::ui
    end

    %% Data Flow Connections
    D1 --> F1
    D2 & D3 --> F1 & F2
    D4 --> F3
    F1 & F2 & F4 --> M1 & M2
    F3 --> M3 & M4

    M1 & M2 --> API
    M3 & M4 --> API

    API --> UI1
    API --> UI2
    API --> UI3
```

---

## How to Import into Draw.io in 3 Clicks:
1. Open [draw.io](https://app.diagrams.net) in your browser.
2. In the top navigation bar, click: **`Arrange`** $\longrightarrow$ **`Insert`** $\longrightarrow$ **`Advanced`** $\longrightarrow$ **`Mermaid`** (or **`XML`**).
3. Paste either the Mermaid code above or the contents of [`carbonpulse_architecture.drawio`](file:///e:/Documents/Projects/CodeFest/DAtathon%20finale/Question_4/carbonpulse_architecture.drawio) and click **`Insert`**!
