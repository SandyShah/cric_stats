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
from utils.visualizer import (
    plot_runs_per_match,
    plot_top_players,
    plot_true_batting_stats
)

st.markdown('</div></div>', unsafe_allow_html=True)

# Sidebar navigation

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
                    st.write(f"**File:** {os.path.basename(selected_match_info['file_path'])}")
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

    # Initialize stats tracking
    player_runs = {}
    player_do_runs = {}  # Death overs runs (16-20)
    player_balls = {}    # Total balls faced
    player_do_balls = {} # Death overs balls faced
    player_fours = {}    # Total fours
    player_do_fours = {} # Death overs fours
    player_sixes = {}    # Total sixes
    player_do_sixes = {} # Death overs sixes
    player_matches = {}  # Total matches in playing XI
    player_innings = {}  # Innings where player batted
    player_dismissals = {}  # Number of times player got out
    # Dot ball tracking
    player_dot_balls = {}   # Total dot balls faced
    player_do_dot_balls = {}# Death overs dot balls faced
    
    # Track which players are processed for each match to avoid double counting
    processed_players = set()

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

    # Get all available years and sort in descending order (most recent first)
    years = sorted(list(set(m["year"] for m in filtered_matches if m["year"])), reverse=True)
    # Convert years to strings for selection
    year_options = [str(y) for y in years]
    # Allow multiple year selection
    selected_years = st.sidebar.multiselect(
        "Select Year(s)",
        options=year_options,
        default=[],
        help="Select multiple years by clicking. Leave empty to see all years."
    )
    # Filter matches if years are selected
    if selected_years:
        filtered_matches = [m for m in filtered_matches if str(m["year"]) in selected_years]

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
        st.markdown("### Match Selection Details")
        st.markdown(f"**Selected Matches:** {len(selected_matches)}")
    else:
        st.markdown("### Match Selection Details")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Total Matches:** {len(filtered_matches)}")
            st.markdown(f"**Tournament:** {selected_tournament if selected_tournament != 'All' else 'All Tournaments'}")
            if selected_years:
                st.markdown(f"**Years:** {', '.join(selected_years)}")
            else:
                st.markdown("**Years:** All Years")
        with col2:
            if selected_venue != "All":
                st.markdown(f"**Venue:** {selected_venue}")
            if team1 != "All":
                st.markdown(f"**Team 1:** {team1}")
            if team2 != "All":
                st.markdown(f"**Team 2:** {team2}")
            if selected_date != "All":
                st.markdown(f"**Date:** {selected_date}")
    
    player_filter = st.sidebar.text_input("Filter by Player (optional)")

    # Load and aggregate data for selected matches
    player_runs = {}
    player_do_runs = {}   # Death overs runs (16-20)
    player_balls = {}     # Total balls faced
    player_do_balls = {}  # Death overs balls faced
    player_fours = {}     # Total fours
    player_do_fours = {}  # Death overs fours
    player_sixes = {}     # Total sixes
    player_do_sixes = {}  # Death overs sixes
    player_matches = {}   # Total matches in playing XI (counted from team sheets)
    player_innings = {}   # Innings where player batted (counted from actual batting)
    
    if filtered_matches:
        for match in filtered_matches:
            try:
                dataset = load_selected_dataset(match["file_path"])
                # Process innings data for batting stats
                innings_data = []
                if 'innings' in dataset:
                    innings_data = dataset['innings']
                
                # Reset processed players set for this match
                processed_players.clear()
                
                # Get teams and their players for this match
                teams_info = dataset.get('info', {}).get('players', {})
                if teams_info:  # Only process if we have valid team information
                    for team_name, team_players in teams_info.items():
                        for player in team_players:
                            # Skip if we've already processed this player (in case they appear in both teams somehow)
                            if player in processed_players:
                                continue
                                
                            # Apply player filter if it exists
                            if player_filter and player_filter.lower() not in player.lower():
                                continue
                                
                            # Mark as processed and increment matches (they were in playing XI)
                            processed_players.add(player)
                            player_matches[player] = player_matches.get(player, 0) + 1
                
                for innings in innings_data:
                    if 'overs' in innings:
                        for over in innings['overs']:
                            over_num = int(over.get('over', 0))
                            is_death_over = over_num >= 15  # Over numbers are 0-based, so 15 means 16th over
                            
                            if 'deliveries' in over:
                                for delivery in over['deliveries']:
                                    if 'batter' in delivery:
                                        batter = delivery['batter']
                                        runs = delivery.get('runs', {}).get('batter', 0)
                                        
                                        # Apply player filter if set
                                        if player_filter and player_filter.lower() not in batter.lower():
                                            continue
                                            
                                        # Initialize player data structures if needed
                                        if batter not in player_innings:
                                            player_innings[batter] = {
                                                'count': 0,
                                                'matches': set()  # Set to track unique matches
                                            }
                                        
                                        # Track innings (only once per match per player)
                                        match_id = match["file_path"]
                                        if match_id not in player_innings[batter]['matches']:
                                            player_innings[batter]['matches'].add(match_id)
                                            player_innings[batter]['count'] += 1
                                        
                                        # Check for dismissal in this delivery
                                        if 'wickets' in delivery:
                                            for wicket in delivery['wickets']:
                                                dismissed_player = wicket.get('player_out')
                                                # Initialize dismissals count and details if needed for dismissed player
                                                if dismissed_player not in player_dismissals:
                                                    player_dismissals[dismissed_player] = {
                                                        'count': 0,
                                                        'details': []  # Track dismissal details
                                                    }
                                                
                                                # Increment dismissal count for the dismissed player
                                                player_dismissals[dismissed_player]['count'] += 1
                                                
                                                # Store dismissal details
                                                dismissal_info = {
                                                    'kind': wicket.get('kind', 'unknown'),
                                                    'fielders': [f.get('name') for f in wicket.get('fielders', [])] if 'fielders' in wicket else [],
                                                    'bowler': delivery.get('bowler'),
                                                    'over': over.get('over'),
                                                    'batter_on_strike': batter,
                                                    'non_striker': delivery.get('non_striker'),
                                                    'score': f"{innings.get('team')} {sum(d.get('runs', {}).get('total', 0) for o in innings['overs'][:over.get('over', 0)+1] for d in o.get('deliveries', []))}-{len([w for o in innings['overs'][:over.get('over', 0)+1] for d in o.get('deliveries', []) for w in d.get('wickets', [])])}", 
                                                    'match': match.get('match_name', os.path.basename(match["file_path"])),
                                                    'file': os.path.basename(match["file_path"])
                                                }
                                                player_dismissals[dismissed_player]['details'].append(dismissal_info)
                                                
                                                # Also mark this delivery for tracking innings
                                                if dismissed_player not in player_innings:
                                                    player_innings[dismissed_player] = {
                                                        'count': 0,
                                                        'matches': set()  # Set to track unique matches
                                                    }
                                                if match_id not in player_innings[dismissed_player]['matches']:
                                                    player_innings[dismissed_player]['matches'].add(match_id)
                                                    player_innings[dismissed_player]['count'] += 1

                                        # Count balls faced (excluding extras like wides and no-balls)
                                        if 'extras' not in delivery or not delivery['extras']:
                                            # Aggregate balls faced
                                            player_balls[batter] = player_balls.get(batter, 0) + 1
                                            if is_death_over:
                                                player_do_balls[batter] = player_do_balls.get(batter, 0) + 1
                                            # Count dot balls (run == 0)
                                            if runs == 0:
                                                player_dot_balls[batter] = player_dot_balls.get(batter, 0) + 1
                                                if is_death_over:
                                                    player_do_dot_balls[batter] = player_do_dot_balls.get(batter, 0) + 1
                                        
                                        # Aggregate runs
                                        if batter:
                                            player_runs[batter] = player_runs.get(batter, 0) + runs
                                            if is_death_over:
                                                player_do_runs[batter] = player_do_runs.get(batter, 0) + runs
                                            
                                            # Count boundaries
                                            if runs == 4:
                                                player_fours[batter] = player_fours.get(batter, 0) + 1
                                                if is_death_over:
                                                    player_do_fours[batter] = player_do_fours.get(batter, 0) + 1
                                            elif runs == 6:
                                                player_sixes[batter] = player_sixes.get(batter, 0) + 1
                                                if is_death_over:
                                                    player_do_sixes[batter] = player_do_sixes.get(batter, 0) + 1

            except Exception as e:
                st.warning(f"Error loading {match['match_name']}: {str(e)}")
                st.error(f"Detailed error: {str(e)}")
                continue

        # Prepare table: columns = players, rows = stats
        if player_runs:
            # We'll use the player_matches that was already calculated from playing XI information
            # No need to recalculate matches here as it's already done when processing the playing XI
            
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
                        total_runs = player_runs.get(player, 0)
                        death_runs = player_do_runs.get(player, 0)
                        total_balls = player_balls.get(player, 0)
                        death_balls = player_do_balls.get(player, 0)
                        
                        # Calculate strike rates
                        total_sr = (total_runs / max(total_balls, 1)) * 100
                        death_sr = (death_runs / max(death_balls, 1)) * 100
                        
                        # Get number of matches and innings
                        total_matches = player_matches.get(player, 0)  # Total matches in squad
                        innings_played = player_innings.get(player, {}).get('count', 0)  # Times actually batted
                        
                        # Calculate total boundaries and balls per boundary
                        total_boundaries = player_fours.get(player, 0) + player_sixes.get(player, 0)
                        balls_per_boundary = total_balls / total_boundaries if total_boundaries > 0 else float('inf')
                        
                        data.append({
                            'Player': player,
                            'Matches': total_matches,
                            'Innings': innings_played,
                            'Runs': total_runs,
                            'Balls': total_balls,
                            '4s': player_fours.get(player, 0),
                            '6s': player_sixes.get(player, 0),
                            'BpB': round(balls_per_boundary, 2) if balls_per_boundary != float('inf') else '-',  # Balls per Boundary
                            'SR': total_sr,
                            'Dismissals': player_dismissals.get(player, {}).get('count', 0),
                            'Not Outs': player_innings.get(player, {}).get('count', 0) - player_dismissals.get(player, {}).get('count', 0),
                            'Average': float('inf') if player_dismissals.get(player, {}).get('count', 0) == 0 else total_runs/player_dismissals.get(player, {}).get('count', 1),  # Total runs/Dismissals
                            'DO_Runs': death_runs,
                            'DO_4s': player_do_fours.get(player, 0),
                            'DO_6s': player_do_sixes.get(player, 0),
                            'DO_%': (death_runs/total_runs*100) if total_runs > 0 else 0,
                            'Dots': player_dot_balls.get(player, 0),
                            'DO_Dots': player_do_dot_balls.get(player, 0),
                            'Dot_%': (player_dot_balls.get(player, 0)/total_balls*100) if total_balls > 0 else 0,
                            'DO_Dot_%': (player_do_dot_balls.get(player, 0)/max(death_balls,1)*100) if death_balls > 0 else 0,
                            'DO_SR': death_sr,
                            'DO_Average': float('inf') if player_dismissals.get(player, {}).get('count', 0) == 0 else death_runs/player_dismissals.get(player, {}).get('count', 1),  # Death overs runs/Dismissals
                            # Death overs balls per boundary (DO_BpB)
                            'DO_BpB': (round(death_balls / (player_do_fours.get(player, 0) + player_do_sixes.get(player, 0)), 2)
                                      if (player_do_fours.get(player, 0) + player_do_sixes.get(player, 0)) > 0 and death_balls > 0
                                      else '-'),
                        })
                    
                    df = pd.DataFrame(data)
                    
                    # Format numeric columns
                    numeric_columns = ['SR', 'DO_%', 'DO_SR']
                    for col in numeric_columns:
                        df[col] = df[col].round(2)
                    
                    # Format average columns to show "-" for not-out cases with no dismissals
                    for col in ['Average', 'DO_Average']:
                        df[col] = df[col].apply(lambda x: "-" if x == float('inf') else round(x, 2))
                        
                    # Add % symbol to DO_%
                    df['DO_%'] = df['DO_%'].astype(str) + '%'
                    # Add Dot % and DO Dot % as percentage strings
                    if 'Dot_%' in df.columns:
                        df['Dot_%'] = df['Dot_%'].round(2).astype(str) + '%'
                    if 'DO_Dot_%' in df.columns:
                        df['DO_Dot_%'] = df['DO_Dot_%'].round(2).astype(str) + '%'
                    
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
                    
                    # Reorder columns into a logical batting-stats order while keeping any new columns
                    preferred_order = [
                        'Sr.', 'Player', 'Matches', 'Innings', 'Not Outs', 'Dismissals',
                        'Runs', 'Balls', 'SR', 'Average', '4s', '6s', 'BpB', 'Dots', 'Dot_%',
                        'DO_Runs', 'DO_Balls', 'DO_SR', 'DO_Average', 'DO_4s', 'DO_6s', 'DO_BpB', 'DO_Dots', 'DO_Dot_%', 'DO_%'
                    ]
                    cols_in_order = [c for c in preferred_order if c in df.columns]
                    # Append any columns not in preferred_order (keeps future additions)
                    cols_in_order += [c for c in df.columns if c not in cols_in_order]
                    df = df[cols_in_order]

                    st.dataframe(
                        df.set_index(['Sr.', 'Player']),  # Multi-index with Sr. and Player
                        use_container_width=True,
                        height=min(len(filtered_players) * 35 + 38, 400)  # Adjust height based on number of rows
                    )
            
            with col1:
                # Filter data for selected players
                # Create a summary DataFrame with all stats
                data = {
                    player: {
                        "Matches": player_matches.get(player, 0),
                        "Innings": player_innings.get(player, {}).get('count', 0),
                        "Not Outs": player_innings.get(player, {}).get('count', 0) - player_dismissals.get(player, {}).get('count', 0),
                        "Dismissals": player_dismissals.get(player, {}).get('count', 0),
                        "Total Runs": player_runs.get(player, 0),
                        "Total Balls": player_balls.get(player, 0),
                        "BpB": (round(player_balls.get(player, 0) / max((player_fours.get(player, 0) + player_sixes.get(player, 0)), 1), 2)
                                if (player_fours.get(player, 0) + player_sixes.get(player, 0)) > 0 else '-'),
                        "Strike Rate": round((player_runs.get(player, 0) / max(player_balls.get(player, 1), 1)) * 100, 2),
                        "Average": float('inf') if player_dismissals.get(player, {}).get('count', 0) == 0 else round(player_runs.get(player, 0) / player_dismissals.get(player, {}).get('count', 1), 2),
                        "4s": player_fours.get(player, 0),
                        "6s": player_sixes.get(player, 0),
                        "DO_Runs": player_do_runs.get(player, 0),
                        "DO_Balls": player_do_balls.get(player, 0),
                        "DO_SR": round((player_do_runs.get(player, 0) / max(player_do_balls.get(player, 1), 1)) * 100, 2),
                        "DO_Average": round(player_do_runs.get(player, 0) / max(player_innings.get(player, {}).get('count', 1), 1), 2),
                        "DO_4s": player_do_fours.get(player, 0),
                        "DO_6s": player_do_sixes.get(player, 0),
                        "DO_%": f"{round((player_do_runs.get(player, 0) / max(player_runs.get(player, 1), 1)) * 100, 2)}%",
                        "DO_BpB": (round(player_do_balls.get(player, 0) / max((player_do_fours.get(player, 0) + player_do_sixes.get(player, 0)), 1), 2)
                                   if (player_do_fours.get(player, 0) + player_do_sixes.get(player, 0)) > 0 else '-'),
                        "Dots": player_dot_balls.get(player, 0),
                        "DO_Dots": player_do_dot_balls.get(player, 0),
                        "Dot_%": f"{round((player_dot_balls.get(player, 0) / max(player_balls.get(player, 1), 1)) * 100, 2)}%",
                        "DO_Dot_%": f"{round((player_do_dot_balls.get(player, 0) / max(player_do_balls.get(player, 1), 1)) * 100, 2)}%"
                    }
                    for player in filtered_players
                }
                
                df_summary = pd.DataFrame.from_dict(data, orient='index')
                
                # Sort by Total Runs in descending order
                df_summary = df_summary.sort_values(by="Total Runs", ascending=False)
                
                # Display summary of total matches
                st.markdown(f"**Analysis based on {len(filtered_matches)} matches**")
                
                # Display the table with custom formatting
                st.subheader("Batting Stats Summary")
                
                # Transpose the DataFrame and sort columns (players) by Total Runs
                df_summary_sorted = df_summary.sort_values(by="Total Runs", ascending=False)
                df_summary_transposed = df_summary_sorted.T
                # Normalize any rows that are stored as percent-strings (e.g., 'DO_%', 'Dot_%', 'DO_Dot_%')
                for idx in df_summary_transposed.index:
                    try:
                        row = df_summary_transposed.loc[idx].astype(str)
                    except Exception:
                        continue
                    if row.str.contains('%').any():
                        # Strip %, convert to float where possible, round and re-append '%'
                        new_vals = []
                        for v in row:
                            if isinstance(v, str) and v.endswith('%'):
                                try:
                                    num = float(v.rstrip('%'))
                                    new_vals.append(f"{round(num,2)}%")
                                except Exception:
                                    new_vals.append(v)
                            else:
                                new_vals.append(v)
                        df_summary_transposed.loc[idx] = new_vals

                # Create scatter plot if we have players
                if filtered_players and len(filtered_players) > 0:
                    st.markdown("### Player Comparison Plot")

                    # Add axis selection for scatter plot
                    # Use the exact column names from the summary DataFrame so select options match the table
                    stat_options = list(df_summary.columns)

                    col_plot1, col_plot2 = st.columns(2)
                    with col_plot1:
                        x_axis = st.selectbox("X-Axis", stat_options, index=0)
                    with col_plot2:
                        # default to a sensible second choice (prefer Strike Rate if present)
                        default_y = 0
                        if "Strike Rate" in stat_options:
                            default_y = stat_options.index("Strike Rate")
                        y_axis = st.selectbox("Y-Axis", stat_options, index=default_y)

                    # Use the selected axis values (column names from df_summary)
                    x_col = x_axis
                    y_col = y_axis

                    # Create scatter plot using plotly
                    import plotly.express as px

                    # Prepare data for plotting (work on a copy)
                    plot_df = df_summary.copy()

                    # Helper: convert column to numeric, handling percent strings and non-numeric placeholders
                    def to_numeric_series(s):
                        # Convert everything to string first
                        ser = s.astype(str)
                        # If any value ends with '%', strip and convert
                        if ser.str.endswith('%').any():
                            return ser.str.rstrip('%').replace({'nan': None}).astype(float)
                        # Otherwise coerce to numeric, converting non-numeric to NaN
                        return pd.to_numeric(ser.replace({'nan': None}), errors='coerce')

                    # Convert selected columns to numeric for plotting
                    plot_df[x_col] = to_numeric_series(plot_df[x_col])
                    plot_df[y_col] = to_numeric_series(plot_df[y_col])

                    # Create bubble plot
                    fig = px.scatter(
                        plot_df,
                        x=x_col,
                        y=y_col,
                        text=plot_df.index,  # Player names
                        size="Total Runs" if "Total Runs" in plot_df.columns else None,    # Bubble size based on total runs when available
                        color=plot_df.index if not plot_df.index.empty else None,  # Different color for each player
                        title=f"{y_axis} vs {x_axis}",
                        labels={
                            x_col: x_axis,
                            y_col: y_axis
                        },
                        hover_data=[c for c in ["Total Runs", "Innings", "Strike Rate", "Average"] if c in plot_df.columns]  # Additional info on hover
                    )
                    # Update layout
                    fig.update_traces(
                        textposition='top center',
                        marker=dict(size=20),
                        textfont=dict(size=10)
                    )
                    fig.update_layout(
                        showlegend=True,
                        height=600,
                        xaxis_title=x_axis,
                        yaxis_title=y_axis
                    )

                    # Display the plot
                    st.plotly_chart(fig, use_container_width=True)
                
                # Display the summary dataframe
                # Reorder summary stats rows into a logical order (keep any additional stats)
                preferred_stats_order = [
                    'Matches', 'Innings', 'Not Outs', 'Dismissals',
                    'Total Runs', 'Total Balls', 'Strike Rate', 'Average',
                    '4s', '6s', 'BpB', 'Dots', 'Dot %',
                    'DO Runs', 'DO Balls', 'DO Strike Rate', 'DO Average', 'DO 4s', 'DO 6s', 'DO %', 'DO Dots', 'DO Dot %', 'DO_BpB'
                ]
                rows_in_order = [r for r in preferred_stats_order if r in df_summary_transposed.index]
                rows_in_order += [r for r in df_summary_transposed.index if r not in rows_in_order]
                df_summary_transposed = df_summary_transposed.reindex(rows_in_order)

                st.dataframe(
                    df_summary_transposed,
                    use_container_width=True,
                    height=500  # Fixed height for better readability of all stats
                )
                # st.dataframe(data)
                
                # Add a summary of matches included
                st.markdown("---")
                # Display matches included
                st.markdown("**Matches included in analysis:**")
                for match in filtered_matches:
                    st.markdown(f"- {match['match_name']} ({match['date']})")

                # Add a section for dismissal details
                if 'Dismissal Details' in df_summary_transposed.index:
                    st.markdown("---")
                    st.markdown("**Dismissal Details:**")
                    for player, details in df_summary.iterrows():
                        dismissals = details.get('Dismissal Details', [])
                        if dismissals:
                            st.markdown(f"**{player}**")
                            for d in dismissals:
                                # Format fielders if any
                                fielder_text = f" by {', '.join(d['fielders'])}" if d['fielders'] else ""
                                # Format bowler if available
                                bowler_text = f" (bowler: {d['bowler']})" if d['bowler'] else ""
                                # Construct dismissal string
                                # Format bowler info
                                bowler_text = f" (bowled by {d['bowler']})" if d['bowler'] and d['kind'] != "run out" else ""
                                
                                # Format score and match info
                                score_text = f" at {d['score']}" if 'score' in d else ""
                                match_text = f" - {d['match']}" if 'match' in d else f" [{d['file']}]"
                                
                                # Add batting position context for run outs
                                position_text = ""
                                if d['kind'] == "run out":
                                    if d.get('batter_on_strike') == player:
                                        position_text = " (on strike)"
                                    elif d.get('non_striker') == player:
                                        position_text = " (at non-striker's end)"
                                        
                                st.markdown(f"- {d['kind']}{position_text}{fielder_text}{bowler_text} in over {d['over']}{score_text}{match_text}")
        else:
            st.info("No batting data available for selected filters.")
    else:
        st.info("No matches selected.")
