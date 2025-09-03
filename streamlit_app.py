import streamlit as st
import pandas as pd
import os
import json

from utils.data_loader import load_json_files, load_selected_dataset, get_match_info
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
DATA_FOLDER = "/home/sandeep/Desktop/cric_stats/ipl_male_json"  # Path to your JSON files
json_folder = DATA_FOLDER

try:
    # Load available files
    available_files = load_json_files(json_folder)
    if not available_files:
        st.error(f"No JSON files found in {json_folder}")
        st.stop()

    # Gather match info for dropdown and filters
    match_infos = []
    for f in available_files:
        try:
            info = get_match_info(os.path.join(json_folder, f))
            match_infos.append(info)
        except Exception as e:
            st.warning(f"Error loading file {f}: {str(e)}")
            continue

    if not match_infos:
        st.error("No valid match data found")
        st.stop()

# No longer needed as we calculate these values in the filters section

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

# Create sidebar filters with dependencies
if match_infos:
    st.sidebar.header("📊 Match Filters")
    
    # Tournament filter
    tournaments = sorted(list(set(m["tournament"] for m in match_infos if m["tournament"])))
    selected_tournament = st.sidebar.selectbox(
        "Select Tournament",
        ["All"] + tournaments
    )
    
    # Filter matches by tournament
    filtered_matches = match_infos
    if selected_tournament != "All":
        filtered_matches = [m for m in match_infos if m["tournament"] == selected_tournament]
    
    # Year filter (updates based on tournament)
    years = sorted(list(set(m["year"] for m in filtered_matches if m["year"])))
    selected_year = st.sidebar.selectbox(
        "Select Year",
        ["All"] + [str(y) for y in years]
    )
    
    # Further filter by year
    if selected_year != "All":
        filtered_matches = [m for m in filtered_matches if str(m["year"]) == selected_year]
    
    # Team filters (updates based on year and tournament)
    all_teams = sorted(list(set(
        team for m in filtered_matches for team in m["teams"]
    )))
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        team1 = st.selectbox("Team 1", ["All"] + all_teams)
    with col2:
        # Filter team2 options to exclude team1
        team2_options = ["All"] + [t for t in all_teams if t != team1]
        team2 = st.selectbox("Team 2", team2_options)
    
    # Filter matches by teams (in any order)
    if team1 != "All":
        filtered_matches = [m for m in filtered_matches if team1 in m["teams"]]
    if team2 != "All":
        filtered_matches = [m for m in filtered_matches if team2 in m["teams"]]
    
    # Date filter for matches (updates based on all previous filters)
    dates = sorted(list(set(m["date"] for m in filtered_matches if m["date"])))
    if dates:
        selected_date = st.sidebar.selectbox(
            "Select Date",
            ["All"] + dates
        )
        if selected_date != "All":
            filtered_matches = [m for m in filtered_matches if m["date"] == selected_date]
    
    # Final match selection (filtered by all criteria)
    if filtered_matches:
        match_options = [m["match_name"] for m in filtered_matches]
        selected_match = st.sidebar.selectbox("Select Match", match_options)
        
        # Get the full match info for the selected match
        selected_match_info = next(m for m in filtered_matches if m["match_name"] == selected_match)
        
        # Optional player filter
        player_filter = st.sidebar.text_input("Filter by Player (optional)")
    else:
        st.warning("No matches found with selected filters")

# Option to analyze true batting stats across all matches
analyze_true_stats = st.sidebar.checkbox("Show True Batting Stats (All Matches)")

if analyze_true_stats:
    # Load all filtered match data
    match_data_list = []
    for match in filtered_matches:
        try:
            with open(match["file_path"], "r") as f:
                match_data_list.append(json.load(f))
        except Exception as e:
            st.warning(f"Error loading {match['match_name']}: {str(e)}")
            continue
    
    if match_data_list:
        st.subheader("📊 True Batting Stats (Top Batters)")
        true_bat_df = compute_true_batting_stats(match_data_list, top_n=25)
        st.dataframe(true_bat_df)
        st.subheader("📈 True Average vs True Strike Rate (Scatter Plot)")
        st.plotly_chart(plot_true_batting_stats(true_bat_df), use_container_width=True)
    else:
        st.warning("No data available for selected filters")
else:
    # Show selected match
        if selected_match and filtered_matches:
            selected_match_info = next(m for m in filtered_matches if m["match_name"] == selected_match)
            try:
                dataset = load_selected_dataset(selected_match_info["file_path"])

                # Show match details
                st.subheader("🏏 Match Details")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Tournament:** {selected_match_info['tournament']}")
                    st.write(f"**Teams:** {selected_match_info['team1']} vs {selected_match_info['team2']}")
                    st.write(f"**Date:** {selected_match_info['date']}")
                with col2:
                    st.write(f"**Venue:** {selected_match_info['venue']}")
                    st.write(f"**City:** {selected_match_info['city']}")
                    st.write(f"**Result:** {selected_match_info['result']}")

                # Show raw preview
                st.subheader(f"📂 Data Preview")
                st.dataframe(pd.json_normalize(dataset).head())

                # -----------------------------
                # Process Stats
                # -----------------------------
                # Calculate stats for all teams if no specific team is selected
                if team1 == "All" and team2 == "All":
                    stats_df = compute_basic_stats(dataset, None, player_filter)
                else:
                    # If specific team(s) are selected, combine their stats
                    team1_stats = compute_basic_stats(dataset, team1 if team1 != "All" else None, player_filter)
                    team2_stats = compute_basic_stats(dataset, team2 if team2 != "All" else None, player_filter)
                    stats_df = pd.concat([team1_stats, team2_stats], ignore_index=True)

                st.subheader("📊 Processed Stats")
                st.dataframe(stats_df)

                # -----------------------------
                # Visualizations
                # -----------------------------
                st.subheader("📈 Visualizations")

                if not stats_df.empty:
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
                else:
                    st.info("No data available for selected filters.")
            except Exception as e:
                st.error(f"Error loading match data: {str(e)}")
