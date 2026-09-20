# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import joblib
import os

st.set_page_config(page_title="SLIIT Datathon AI Engine", layout="wide")

st.title("📊 Multi-Source Analytics & Predictive Dashboard")
st.markdown("Automated Tabular Data Processor and Model Inference Engine")

# Sidebar: Controls
st.sidebar.header("Data Control Center")
uploaded_file = st.sidebar.file_uploader("Upload Competition Dataset (CSV)", type=["csv"])

@st.cache_data
def load_data(file):
    return pd.read_csv(file)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    tabs = st.tabs(["📋 Data Overview", "📈 EDA & Visuals", "🔮 Prediction & Model"])
    
    with tabs[0]:
        st.subheader("Dataset Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", df.shape[0])
        col2.metric("Columns", df.shape[1])
        col3.metric("Missing Values", int(df.isna().sum().sum()))
        
        st.dataframe(df.head(10), use_container_width=True)
        
        st.subheader("Statistical Profile")
        st.write(df.describe())
        
    with tabs[1]:
        st.subheader("Exploratory Visualizations")
        num_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        if num_cols:
            col_x = st.selectbox("Select X Axis Feature", num_cols, index=0)
            col_y = st.selectbox("Select Y Axis Feature", num_cols, index=min(1, len(num_cols)-1))
            
            fig = px.scatter(df, x=col_x, y=col_y, title=f"{col_x} vs {col_y}", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No numeric columns found for plotting.")
            
    with tabs[2]:
        st.subheader("Model Inference")
        if os.path.exists("models/model.joblib"):
            pipeline = joblib.load("models/model.joblib")
            st.success("Trained pipeline successfully loaded from `models/model.joblib`.")
            
            if st.button("Generate Predictions on Uploaded Data"):
                try:
                    preds = pipeline.predict(df)
                    df_out = df.copy()
                    df_out["Prediction"] = preds
                    st.dataframe(df_out.head(15), use_container_width=True)
                    
                    csv_export = df_out.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Predictions CSV", csv_export, "predictions.csv", "text/csv")
                except Exception as e:
                    st.error(f"Inference error: Ensure columns match trained model! Details: {e}")
        else:
            st.info("No model found in `models/model.joblib`. Train a model via `run_pipeline.py` first.")
else:
    st.info("Awaiting dataset upload. Please upload a CSV from the sidebar.")