import streamlit as st
import pandas as pd
from utils import fetch_all_progress, calculate_metrics

st.title("Instructor Dashboard")

df = fetch_all_progress()

if df.empty:
    st.info("No student data yet.")
else:
    st.subheader("Overall Post-Editing Metrics")
    metrics_df = calculate_metrics(df)
    st.dataframe(metrics_df)

    st.subheader("PE Effort: Manual vs Automatic MT")
    pivot_time = df.pivot_table(index='username', columns='mt_type', values='duration', aggfunc='mean')
    st.bar_chart(pivot_time)

    st.subheader("Edit Distance Comparison")
    pivot_ed = df.pivot_table(index='username', columns='mt_type', values='edit_distance', aggfunc='mean')
    st.bar_chart(pivot_ed)

    st.subheader("Download Full Dataset")
    st.download_button("Download CSV", df.to_csv(index=False), file_name="student_pe_data.csv")
