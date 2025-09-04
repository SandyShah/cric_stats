# -----------------------------
# Streamlit Page Config
# -----------------------------
import streamlit as st
st.set_page_config(
    page_title="Cricket Stats Analysis",
    page_icon="🏏",
    layout="wide"
)

import pandas as pd
import os
import json
from utils.data_loader import load_json_files, load_selected_dataset, get_match_info
from utils.stats_processor import compute_basic_stats, compute_true_batting_stats, compute_match_level_true_batting_stats
from utils.visualizer import plot_runs_per_match, plot_top_players, plot_true_batting_stats, plot_match_level_true_batting_stats

# Sidebar navigation for multipage
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Match Stats", "Batting Stats"])

if page == "Match Stats":
    st.title("🏏 Cricket Stats Analysis App")



# -----------------------------

    DATA_FOLDER = "data"  # Path to your JSON files
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
        if 'selected_match' in locals() and filtered_matches:
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
                # Match-level True Batting Stats
                # -----------------------------
                st.subheader("🎯 True Batting Stats (This Match)")
                st.info("True stats compare each player's performance to the average of top 6 batsmen in this match")
                try:
                    true_match_stats = compute_match_level_true_batting_stats(dataset)
                    if not true_match_stats.empty:
                        # Display stats with formatting
                        display_cols = ['player', 'team', 'runs', 'balls', 'average', 'strike_rate', 
                                      'true_average', 'true_strike_rate', 'is_top6']
                        formatted_stats = true_match_stats[display_cols].copy()
                        # Round numeric columns
                        for col in ['average', 'strike_rate', 'true_average', 'true_strike_rate']:
                            formatted_stats[col] = formatted_stats[col].round(2)
                        st.dataframe(formatted_stats, use_container_width=True)
                        # Show interpretation
                        st.markdown("""
                        **How to read True Stats:**
                        - **True Average > 0**: Player performed better than top 6 average
                        - **True Strike Rate > 0**: Player struck faster than top 6 average
                        - **Negative values**: Player performed below top 6 benchmark
                        """)
                        # Visualization for match-level true stats
                        st.plotly_chart(plot_match_level_true_batting_stats(true_match_stats), use_container_width=True)
                    else:
                        st.warning("No batting data available for true stats calculation")
                except Exception as e:
                    st.error(f"Error calculating true batting stats: {str(e)}")
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

elif page == "Batting Stats":
    st.title("Batting Stats")

    # Load available files and match info
    DATA_FOLDER = "data"
    json_folder = DATA_FOLDER
    try:
        available_files = load_json_files(json_folder)
        if not available_files:
            st.error(f"No JSON files found in {json_folder}")
            st.stop()
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
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

    # Sidebar filters (copied and adapted from Match Stats)
    st.sidebar.header("Batting Stats Filters")
    tournaments = sorted(list(set(m["tournament"] for m in match_infos if m["tournament"])))
    selected_tournament = st.sidebar.selectbox("Select Tournament", ["All"] + tournaments)
    filtered_matches = match_infos
    if selected_tournament != "All":
        filtered_matches = [m for m in filtered_matches if m["tournament"] == selected_tournament]

    years = sorted(list(set(m["year"] for m in filtered_matches if m["year"])))
    selected_year = st.sidebar.selectbox("Select Year", ["All"] + [str(y) for y in years])
    if selected_year != "All":
        filtered_matches = [m for m in filtered_matches if str(m["year"]) == selected_year]

    all_teams = sorted(list(set(team for m in filtered_matches for team in m["teams"])))
    col1, col2 = st.sidebar.columns(2)
    with col1:
        team1 = st.selectbox("Team 1", ["All"] + all_teams)
    with col2:
        team2_options = ["All"] + [t for t in all_teams if t != team1]
        team2 = st.selectbox("Team 2", team2_options)
    if team1 != "All":
        filtered_matches = [m for m in filtered_matches if team1 in m["teams"]]
    if team2 != "All":
        filtered_matches = [m for m in filtered_matches if team2 in m["teams"]]

    venues = sorted(list(set(m["venue"] for m in filtered_matches if m["venue"])))
    selected_venue = st.sidebar.selectbox("Select Venue", ["All"] + venues)
    if selected_venue != "All":
        filtered_matches = [m for m in filtered_matches if m["venue"] == selected_venue]

    dates = sorted(list(set(m["date"] for m in filtered_matches if m["date"])))
    selected_date = st.sidebar.selectbox("Select Date", ["All"] + dates)
    if selected_date != "All":
        filtered_matches = [m for m in filtered_matches if m["date"] == selected_date]

    match_options = [m["match_name"] for m in filtered_matches]
    selected_matches = st.sidebar.multiselect("Select Match(es)", match_options)
    
    # If specific matches are selected, filter to just those matches
    if selected_matches:
        filtered_matches = [m for m in filtered_matches if m["match_name"] in selected_matches]
        st.markdown(f"**Showing stats for selected {len(selected_matches)} matches**")
    else:
        st.markdown(f"**Showing aggregated stats for all {len(filtered_matches)} matches matching filters**")
    
    player_filter = st.sidebar.text_input("Filter by Player (optional)")

    # Load and aggregate data for selected matches
    player_runs = {}
    if filtered_matches:
        for match in filtered_matches:
            try:
                dataset = load_selected_dataset(match["file_path"])
                # Process innings data for batting stats
                innings_data = []
                if 'innings' in dataset:
                    innings_data = dataset['innings']
                
                for innings in innings_data:
                    if 'overs' in innings:
                        for over in innings['overs']:
                            if 'deliveries' in over:
                                for delivery in over['deliveries']:
                                    if 'batter' in delivery:
                                        batter = delivery['batter']
                                        runs = delivery.get('runs', {}).get('batter', 0)
                                        
                                        # Apply player filter if set
                                        if player_filter and player_filter.lower() not in batter.lower():
                                            continue
                                            
                                        # Aggregate runs
                                        if batter:
                                            player_runs[batter] = player_runs.get(batter, 0) + runs

            except Exception as e:
                st.warning(f"Error loading {match['match_name']}: {str(e)}")
                st.error(f"Detailed error: {str(e)}")
                continue

        # Prepare table: columns = players, rows = stats
        if player_runs:
            # Track matches played by each player
            player_matches = {}
            
            # Process each match to count player appearances
            for match in filtered_matches:
                try:
                    dataset = load_selected_dataset(match["file_path"])
                    if 'innings' in dataset:
                        match_players = set()  # Track unique players in this match
                        for innings in dataset['innings']:
                            if 'overs' in innings:
                                for over in innings['overs']:
                                    if 'deliveries' in over:
                                        for delivery in over['deliveries']:
                                            if 'batter' in delivery:
                                                batter = delivery['batter']
                                                match_players.add(batter)
                        
                        # Update match count for each player who appeared
                        for player in match_players:
                            player_matches[player] = player_matches.get(player, 0) + 1
                                                
                except Exception as e:
                    st.warning(f"Error processing match count for {match['match_name']}: {str(e)}")
            
            # Create DataFrame with players as columns
            all_players = sorted(player_runs.keys())  # Alphabetically sorted players
            
            # Create columns for main content and player selector
            col1, col2 = st.columns([7, 3])  # 70% main content, 30% selector
            
            with col2:
                # Add custom CSS for fixed positioning and scrolling
                st.markdown("""
                    <style>
                        /* Container styling */
                        .player-selector-wrapper {
                            position: fixed;
                            right: 2rem;
                            top: 100px;
                            width: 22%;
                            background: white;
                            z-index: 1000;
                            border-radius: 4px;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
                        }
                        
                        .player-selector {
                            border: 1px solid #e0e0e0;
                            border-radius: 4px;
                            background-color: white;
                        }
                        
                        /* Search box styling */
                        .search-box {
                            padding: 8px;
                            border-bottom: 1px solid #e0e0e0;
                        }
                        
                        .search-box input {
                            width: 100%;
                            padding: 5px;
                            border: 1px solid #ddd;
                            border-radius: 4px;
                        }
                        
                        /* Header styling */
                        .selector-header {
                            padding: 8px 12px;
                            background-color: #f8f9fa;
                            border-bottom: 1px solid #e0e0e0;
                            font-weight: bold;
                            font-size: 14px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        }
                        
                        .select-all-option {
                            position: sticky;
                            top: 0;
                            background: white;
                            padding: 8px 12px;
                            border-bottom: 1px solid #e0e0e0;
                            z-index: 1;
                        }
                    </style>
                """, unsafe_allow_html=True)

                # Start the fixed position container
                st.markdown('<div class="player-selector-wrapper">', unsafe_allow_html=True)
                st.markdown('<div class="player-selector">', unsafe_allow_html=True)
                
                # Header with title
                st.markdown('<div class="selector-header">Player Selection</div>', unsafe_allow_html=True)
                
                # Search box
                st.markdown('<div class="search-box">', unsafe_allow_html=True)
                player_search = st.text_input("", placeholder="Search players...", label_visibility="collapsed")
                st.markdown('</div>', unsafe_allow_html=True)
                
                                # Process comma-separated search and filter players
                filtered_players = []
                if player_search:
                    # Split search terms by comma and strip whitespace
                    search_names = [name.strip() for name in player_search.split(',')]
                    
                    # Create a case-insensitive map of player names
                    player_map = {p.lower(): p for p in all_players}
                    
                    # Find exact matches first, then partial matches for each search term
                    for search_name in search_names:
                        search_lower = search_name.lower()
                        # Try exact match first
                        exact_matches = [
                            player_map[name] for name in player_map
                            if search_lower == name
                        ]
                        # Then try partial matches if no exact match found
                        if not exact_matches:
                            matches = [
                                player_map[name] for name in player_map
                                if search_lower in name
                            ]
                            filtered_players.extend(matches)
                        else:
                            filtered_players.extend(exact_matches)
                else:
                    filtered_players = sorted(all_players)
                
                # Remove duplicates while preserving order
                filtered_players = list(dict.fromkeys(filtered_players))
                
                st.markdown('</div></div>', unsafe_allow_html=True)

            with col1:
                if filtered_players:
                    # Create DataFrame with players as rows and stats as columns
                    data = []
                    for player in filtered_players:
                        data.append({
                            'Player': player,
                            'Matches': player_matches.get(player, 0),
                            'Runs': player_runs.get(player, 0),
                            'Average': player_runs.get(player, 0) / max(player_matches.get(player, 1), 1),  # Runs per match
                        })
                    
                    df = pd.DataFrame(data)
                    
                    # Format the Average column
                    df['Average'] = df['Average'].round(2)
                    
                    # Sort by Runs in descending order if no specific search, otherwise keep search order
                    if not player_search:
                        df = df.sort_values('Runs', ascending=False)
                    
                    # Add serial number
                    df.insert(0, 'Sr.', range(1, len(df) + 1))
                    
                    # Display the table with custom formatting
                    st.markdown("""
                        <style>
                            .dataframe {
                                font-size: 14px;
                                text-align: left;
                            }
                            .dataframe thead tr th {
                                text-align: left;
                                background-color: #f8f9fa;
                                padding: 8px !important;
                            }
                            .dataframe tbody tr td {
                                text-align: left;
                                padding: 8px !important;
                            }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    st.dataframe(
                        df.set_index(['Sr.', 'Player']),  # Multi-index with Sr. and Player
                        use_container_width=True,
                        height=min(len(filtered_players) * 35 + 38, 400)  # Adjust height based on number of rows
                    )
            
            with col1:
                # Filter data for selected players
                data = {
                    player: [
                        player_matches.get(player, 0),  # Matches played
                        player_runs[player]  # Runs
                    ]
                    for player in filtered_players
                }
                
                df = pd.DataFrame(data, index=["Matches Played", "Runs Scored"])
                
                # Transpose for sorting
                df_sorted = df.T
                df_sorted = df_sorted.sort_values(by="Runs Scored", ascending=False)
                df = df_sorted.T
                
                # Display summary of total matches
                st.markdown(f"**Analysis based on {len(filtered_matches)} matches**")
                
                # Display the table
                st.subheader("Batting Stats Table")
                st.dataframe(df)
                
                # Add a summary of matches included
                st.markdown("---")
                st.markdown("**Matches included in analysis:**")
                for match in filtered_matches:
                    st.markdown(f"- {match['match_name']} ({match['date']})")
        else:
            st.info("No batting data available for selected filters.")
    else:
        st.info("No matches selected.")
