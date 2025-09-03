import streamlit as st
import pandas as pd
import os
import json

from utils.data_loader import load_json_files, load_selected_dataset
from utils.stats_processor import compute_basic_stats, compute_true_batting_stats
from utils.visualizer import plot_runs_per_match, plot_top_players, plot_true_batting_stats

# -----------------------------
# Streamlit Page Config
# -----------------------------
st.set_page_config(
    page_title="Cricket Stats Analysis",
    page_icon="🏏",
    layout="wide"
)

st.title("🏏 Cricket Stats Analysis App")


# -----------------------------
# Load Data
# -----------------------------
DATA_FOLDER = "data"
json_folder = DATA_FOLDER
available_files = load_json_files(json_folder)

selected_file = st.sidebar.selectbox("Select Tournament/Series", available_files)

# Option to analyze true batting stats across all matches
analyze_true_stats = st.sidebar.checkbox("Show True Batting Stats (All Matches)")

if analyze_true_stats:
    # Load all JSON files in folder
    match_data_list = []
    for fname in available_files:
        fpath = os.path.join(json_folder, fname)
        with open(fpath, "r") as f:
            match_data_list.append(json.load(f))
    st.subheader("📊 True Batting Stats (Top Batters)")
    true_bat_df = compute_true_batting_stats(match_data_list, top_n=25)
    st.dataframe(true_bat_df)
    st.subheader("📈 True Average vs True Strike Rate (Scatter Plot)")
    st.plotly_chart(plot_true_batting_stats(true_bat_df), use_container_width=True)
else:
    if selected_file:
        dataset = load_selected_dataset(os.path.join(json_folder, selected_file))

        # Show raw preview
        st.subheader(f"📂 Data Preview - {selected_file}")
        st.dataframe(pd.json_normalize(dataset).head())

        # -----------------------------
        # Filters
        # -----------------------------
        st.sidebar.header("Filters")
        team_filter = st.sidebar.text_input("Filter by Team (optional)")
        player_filter = st.sidebar.text_input("Filter by Player (optional)")

        # -----------------------------
        # Process Stats
        # -----------------------------
        stats_df = compute_basic_stats(dataset, team_filter, player_filter)

        st.subheader("📊 Processed Stats")
        st.dataframe(stats_df)

        # -----------------------------
        # Visualizations
        # -----------------------------
        st.subheader("📈 Visualizations")

        st.plotly_chart(plot_runs_per_match(stats_df), use_container_width=True)
        st.plotly_chart(plot_top_players(stats_df), use_container_width=True)

        # -----------------------------
        # Download Option
        # -----------------------------
        csv = stats_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="cricket_stats.csv",
            mime="text/csv"
        )
