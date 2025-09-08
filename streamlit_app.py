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
import numpy as np
import numpy as np
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
    # Death-over dismissals tracking
    player_do_dismissals = {}  # Number of times player was dismissed in death overs
    # Scoring milestone tracking (per-innings counts)
    player_30s = {}
    player_50s = {}
    player_100s = {}
    # Position-based stats: track stats by number of wickets already fallen when player came to bat
    # Structure: { player: { starting_wickets: { 'runs':int, 'balls':int, '4s':int, '6s':int, 'dismissals':int, 'innings':int } } }
    player_position_stats = {}
    
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

    # Batting position filter (0..9) - allow multiple selections
    position_options = [str(i) for i in range(0, 10)]
    selected_positions = st.sidebar.multiselect(
        "Select Batting Position(s)",
        options=position_options,
        default=[],
        help="Select one or more starting-wicket positions (0 means opened the innings). Leave empty to include all positions."
    )

    # Option: only show players who have actually batted in the selected positions
    filter_players_by_position = st.sidebar.checkbox(
        "Show only players who batted in selected positions",
        value=False,
        help="When checked, the player selector will only list players who have at least one innings that started at any of the selected positions."
    )

    # Option: restrict matches to those where the (sidebar) player filter played in the selected positions
    # The option to restrict matches to those where a selected player batted in selected positions
    # has been removed to simplify the UI and avoid confusing behavior.

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
            # st.markdown(f"**Total Matches:** {len(filtered_matches)}")
            st.markdown(f"**Tournament:** {selected_tournament if selected_tournament != 'All' else 'All Tournaments'}")

            # Helper: format consecutive numeric selections into ranges (works for years and positions)
            def _ordinal(n):
                try:
                    n = int(n)
                except Exception:
                    return str(n)
                if 10 <= n % 100 <= 20:
                    suf = 'th'
                else:
                    suf = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
                return f"{n}{suf}"

            def _format_ranges(items, use_ordinal=False, empty_label='All'):
                if not items:
                    return f"{empty_label}"
                try:
                    nums = sorted({int(x) for x in items})
                except Exception:
                    # fallback: join raw strings
                    return ', '.join(map(str, items))

                ranges = []
                start = prev = nums[0]
                for n in nums[1:]:
                    if n == prev + 1:
                        prev = n
                        continue
                    if start == prev:
                        ranges.append(_ordinal(start) if use_ordinal else str(start))
                    else:
                        a = _ordinal(start) if use_ordinal else str(start)
                        b = _ordinal(prev) if use_ordinal else str(prev)
                        ranges.append(f"{a}-{b}")
                    start = prev = n
                if start == prev:
                    ranges.append(_ordinal(start) if use_ordinal else str(start))
                else:
                    a = _ordinal(start) if use_ordinal else str(start)
                    b = _ordinal(prev) if use_ordinal else str(prev)
                    ranges.append(f"{a}-{b}")

                if len(ranges) == 1:
                    return ranges[0]
                if len(ranges) == 2:
                    return f"{ranges[0]} & {ranges[1]}"
                return f"{', '.join(ranges[:-1])} & {ranges[-1]}"

            # Years
            if selected_years:
                years_text = _format_ranges(selected_years, use_ordinal=False, empty_label='All Years')
                st.markdown(f"**Years:** {years_text}")
            else:
                st.markdown("**Years:** All Years")

            # Analysis summary line placed directly under selection details
            st.markdown(f"**Analysis based on {len(filtered_matches)} matches**")

            # Positions (show human-friendly ordinals/ranges)
            try:
                pos_text = _format_ranges(selected_positions, use_ordinal=True, empty_label='All positions')
            except Exception:
                pos_text = 'All positions'
            st.markdown(f"**Positions:** {pos_text}")
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
    # (previously there was an optional pre-scan here to restrict matches by player+position;
    # that feature has been removed to simplify the UI and avoid confusing match filtering)
        
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
                    # Track wickets in this innings to determine the 'came to bat after N wickets' position
                    current_wickets = 0
                    # Map of players to the starting wicket count for this innings (set when they face their first legal ball)
                    innings_player_start = {}
                    if 'overs' in innings:
                        # Track runs scored by each batter in this innings so we can detect 30/50/100 milestones
                        innings_runs = {}
                        for over in innings['overs']:
                            over_num = int(over.get('over', 0))
                            is_death_over = over_num >= 15  # Over numbers are 0-based, so 15 means 16th over
                            
                            if 'deliveries' in over:
                                for delivery in over['deliveries']:
                                    if 'batter' in delivery:
                                        batter = delivery['batter']
                                        runs = delivery.get('runs', {}).get('batter', 0)

                                        # We'll set the batter's innings start when they face their first legal ball (below)
                                        
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

                                                # If this wicket happened in death overs, increment death-over dismissals
                                                try:
                                                    if is_death_over:
                                                        player_do_dismissals[dismissed_player] = player_do_dismissals.get(dismissed_player, 0) + 1
                                                except Exception:
                                                    pass

                                                # If we know which position they started in this innings, increment position dismissals
                                                start_pos = innings_player_start.get(dismissed_player)
                                                if start_pos is not None:
                                                    pstats = player_position_stats.setdefault(dismissed_player, {}).setdefault(start_pos, {
                                                        'runs': 0, 'balls': 0, '4s': 0, '6s': 0, 'dismissals': 0, 'innings': 0
                                                    })
                                                    pstats['dismissals'] = pstats.get('dismissals', 0) + 1

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
                                                # Increase the innings-level wicket count for this delivery
                                                try:
                                                    current_wickets += 1
                                                except NameError:
                                                    # If for some reason current_wickets isn't defined, initialize it
                                                    current_wickets = 1

                                        # Count balls faced (excluding extras like wides and no-balls)
                                        if 'extras' not in delivery or not delivery['extras']:
                                            # If this is the first legal ball this batter faced in this innings, record their start position
                                            if batter not in innings_player_start:
                                                innings_player_start[batter] = current_wickets
                                                pos = innings_player_start[batter]
                                                pos_stats = player_position_stats.setdefault(batter, {}).setdefault(pos, {
                                                    'runs': 0, 'balls': 0, '4s': 0, '6s': 0, 'dismissals': 0, 'innings': 0
                                                })
                                                pos_stats['innings'] = pos_stats.get('innings', 0) + 1

                                            # Aggregate balls faced
                                            player_balls[batter] = player_balls.get(batter, 0) + 1
                                            if is_death_over:
                                                player_do_balls[batter] = player_do_balls.get(batter, 0) + 1

                                            # Track runs within this innings for milestone detection
                                            innings_runs[batter] = innings_runs.get(batter, 0) + runs

                                            # Count dot balls (run == 0)
                                            if runs == 0:
                                                player_dot_balls[batter] = player_dot_balls.get(batter, 0) + 1
                                                if is_death_over:
                                                    player_do_dot_balls[batter] = player_do_dot_balls.get(batter, 0) + 1

                                            # Also add to position-specific ball count
                                            start_pos = innings_player_start.get(batter)
                                            if start_pos is not None:
                                                pstats = player_position_stats.setdefault(batter, {}).setdefault(start_pos, {
                                                    'runs': 0, 'balls': 0, '4s': 0, '6s': 0, 'dismissals': 0, 'innings': 0,
                                                    '30s': 0, '50s': 0, '100s': 0
                                                })
                                                pstats['balls'] = pstats.get('balls', 0) + 1
                                        
                                        # Aggregate runs
                                        if batter:
                                            player_runs[batter] = player_runs.get(batter, 0) + runs
                                            if is_death_over:
                                                player_do_runs[batter] = player_do_runs.get(batter, 0) + runs
                                            # Also add to position-specific runs/boundaries
                                            start_pos = innings_player_start.get(batter)
                                            if start_pos is not None:
                                                pstats = player_position_stats.setdefault(batter, {}).setdefault(start_pos, {
                                                    'runs': 0, 'balls': 0, '4s': 0, '6s': 0, 'dismissals': 0, 'innings': 0,
                                                    '30s': 0, '50s': 0, '100s': 0
                                                })
                                                pstats['runs'] = pstats.get('runs', 0) + runs
                                                if runs == 4:
                                                    pstats['4s'] = pstats.get('4s', 0) + 1
                                                elif runs == 6:
                                                    pstats['6s'] = pstats.get('6s', 0) + 1
                                            
                                            # Count boundaries
                                            if runs == 4:
                                                player_fours[batter] = player_fours.get(batter, 0) + 1
                                                if is_death_over:
                                                    player_do_fours[batter] = player_do_fours.get(batter, 0) + 1
                                            elif runs == 6:
                                                player_sixes[batter] = player_sixes.get(batter, 0) + 1
                                                if is_death_over:
                                                    player_do_sixes[batter] = player_do_sixes.get(batter, 0) + 1
                                        # end delivery
                        # After finishing this innings, update milestone counters per player in this innings
                        for batter_name, runs_scored in innings_runs.items():
                            try:
                                start_pos = innings_player_start.get(batter_name)
                            except Exception:
                                start_pos = None

                            # Update global milestone counters
                            if runs_scored >= 30:
                                player_30s[batter_name] = player_30s.get(batter_name, 0) + 1
                            if runs_scored >= 50:
                                player_50s[batter_name] = player_50s.get(batter_name, 0) + 1
                            if runs_scored >= 100:
                                player_100s[batter_name] = player_100s.get(batter_name, 0) + 1

                            # Update position-specific milestone counters if we have the start position
                            if start_pos is not None:
                                pstats = player_position_stats.setdefault(batter_name, {}).setdefault(start_pos, {
                                    'runs': 0, 'balls': 0, '4s': 0, '6s': 0, 'dismissals': 0, 'innings': 0,
                                    '30s': 0, '50s': 0, '100s': 0
                                })
                                if runs_scored >= 30:
                                    pstats['30s'] = pstats.get('30s', 0) + 1
                                if runs_scored >= 50:
                                    pstats['50s'] = pstats.get('50s', 0) + 1
                                if runs_scored >= 100:
                                    pstats['100s'] = pstats.get('100s', 0) + 1
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
            col1, col2 = st.columns([8, 2])  # 80% main content, 20% selector
            
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

                # If user chose to filter players by selected positions, restrict the list
                if selected_positions and filter_players_by_position:
                    try:
                        sel_pos_ints = [int(p) for p in selected_positions]
                    except Exception:
                        sel_pos_ints = []

                    def has_played_in_positions(player_name):
                        pstats = player_position_stats.get(player_name, {})
                        for pos in sel_pos_ints:
                            if pstats.get(pos, {}).get('innings', 0) > 0:
                                return True
                        return False

                    filtered_players = [p for p in filtered_players if has_played_in_positions(p)]
                
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
                        
                        # Build row dict explicitly to avoid complex dict-unpacking issues
                        row = {
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
                            # Death-over dismissals (explicit column)
                            'DO_Dismissals': player_do_dismissals.get(player, 0),
                            # Use death-over dismissals to compute DO_Average
                            'DO_Average': float('inf') if player_do_dismissals.get(player, 0) == 0 else death_runs/player_do_dismissals.get(player, 1),  # Death overs runs / death-over dismissals
                            # Death overs balls per boundary (DO_BpB)
                            'DO_BpB': (round(death_balls / (player_do_fours.get(player, 0) + player_do_sixes.get(player, 0)), 2)
                                      if (player_do_fours.get(player, 0) + player_do_sixes.get(player, 0)) > 0 and death_balls > 0
                                      else '-'),
                            # Milestones
                            '30s': player_30s.get(player, 0),
                            '50s': player_50s.get(player, 0),
                            '100s': player_100s.get(player, 0)
                        }

                        # Position-based stats (0..9): came after p wickets fallen
                        for p in range(0, 10):
                            pst = player_position_stats.get(player, {}).get(p, {})
                            runs_p = pst.get('runs', 0)
                            balls_p = pst.get('balls', 0)
                            fours_p = pst.get('4s', 0)
                            sixes_p = pst.get('6s', 0)
                            dismissals_p = pst.get('dismissals', 0)

                            row[f"{p}_Runs"] = runs_p
                            row[f"{p}_Balls"] = balls_p
                            row[f"{p}_SR"] = round((runs_p / max(balls_p, 1)) * 100, 2) if balls_p > 0 else 0
                            row[f"{p}_Average"] = ('-' if dismissals_p == 0 else round(runs_p / dismissals_p, 2))
                            row[f"{p}_BpB"] = (round(balls_p / max((fours_p + sixes_p), 1), 2) if (fours_p + sixes_p) > 0 and balls_p > 0 else '-')
                            row[f"{p}_4s"] = fours_p
                            row[f"{p}_6s"] = sixes_p
                            # position milestone columns
                            row[f"{p}_30s"] = pst.get('30s', 0)
                            row[f"{p}_50s"] = pst.get('50s', 0)
                            row[f"{p}_100s"] = pst.get('100s', 0)

                        # Aggregated stats for selected positions (SelPos_*)
                        try:
                            sel_pos_ints = [int(p) for p in selected_positions] if selected_positions else None
                        except Exception:
                            sel_pos_ints = None

                        sel_runs = sel_balls = sel_4s = sel_6s = sel_innings = 0
                        sel_30s = sel_50s = sel_100s = 0
                        sel_dismissals = 0
                        pos_keys = range(0, 10) if not sel_pos_ints else sel_pos_ints
                        for pos in pos_keys:
                            pst = player_position_stats.get(player, {}).get(pos, {})
                            sel_runs += pst.get('runs', 0)
                            sel_balls += pst.get('balls', 0)
                            sel_4s += pst.get('4s', 0)
                            sel_6s += pst.get('6s', 0)
                            sel_innings += pst.get('innings', 0)
                            sel_30s += pst.get('30s', 0)
                            sel_50s += pst.get('50s', 0)
                            sel_100s += pst.get('100s', 0)
                            sel_dismissals += pst.get('dismissals', 0)

                        row['SelPos_Runs'] = sel_runs
                        row['SelPos_Balls'] = sel_balls
                        # Selected-position Strike Rate
                        row['SelPos_SR'] = round((sel_runs / max(sel_balls, 1)) * 100, 2) if sel_balls > 0 else 0
                        row['SelPos_4s'] = sel_4s
                        row['SelPos_6s'] = sel_6s
                        # Balls per boundary for selected positions
                        row['SelPos_BpB'] = (round(sel_balls / (sel_4s + sel_6s), 2)
                                             if (sel_4s + sel_6s) > 0 and sel_balls > 0
                                             else '-')
                        row['SelPos_Innings'] = sel_innings
                        row['SelPos_30s'] = sel_30s
                        row['SelPos_50s'] = sel_50s
                        row['SelPos_100s'] = sel_100s
                        # Selected-position dismissals and average
                        row['SelPos_Dismissals'] = sel_dismissals
                        row['SelPos_Average'] = ('-' if sel_dismissals == 0 else round(sel_runs / sel_dismissals, 2))

                        data.append(row)
                    
                    df = pd.DataFrame(data)

                    # Helper: coerce any numeric-like columns from strings (strip % and '-') to numeric types
                    def _coerce_numeric_columns(df_local):
                        for c in df_local.columns:
                            if c in ['Player']:
                                # leave player name as-is
                                continue
                            try:
                                ser = df_local[c].astype(str).str.strip()
                            except Exception:
                                continue
                            # Prepare a cleaned series by stripping percent signs and placeholder dashes
                            cleaned = ser.str.rstrip('%').replace({'-': ''})
                            # Attempt numeric conversion
                            conv = pd.to_numeric(cleaned.replace({'': pd.NA}), errors='coerce')
                            # If there is at least one numeric value, use the converted series and fill NaN/inf with 0
                            if conv.notna().sum() > 0:
                                conv = conv.fillna(0)
                                conv = conv.replace([pd.NA, None], 0)
                                try:
                                    conv = conv.replace([float('inf'), float('-inf')], 0)
                                except Exception:
                                    pass
                                df_local[c] = conv

                    _coerce_numeric_columns(df)

                    # Round float columns to 2 decimals for nicer display
                    for col in df.columns:
                        try:
                            if pd.api.types.is_float_dtype(df[col].dtype):
                                df[col] = df[col].round(2)
                        except Exception:
                            continue

                    # For Average columns, convert infinities/NaN to numeric and then replace non-finite with 0
                    for col in ['Average', 'DO_Average']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')

                    # Replace infinities and NaNs with 0 across the DataFrame to avoid sorting/plotting issues
                    try:
                        df = df.replace([float('inf'), float('-inf'), np.inf, -np.inf], 0).fillna(0)
                    except Exception:
                        df = df.fillna(0)

                    # Normalize dtypes: make integer-like columns Int64 and others floats
                    def _normalize_df_types(df_local):
                        for c in df_local.columns:
                            if c == 'Player':
                                continue
                            try:
                                ser = df_local[c]
                                # Work on stringified values to clean placeholders
                                s = ser.astype(str).str.strip()
                                cleaned = s.str.rstrip('%').replace({'-': '', '': pd.NA})
                                conv = pd.to_numeric(cleaned.replace({pd.NA: None}), errors='coerce')
                                if conv.notna().sum() == 0:
                                    continue
                                non_na = conv.dropna()
                                # If all values are integer-valued, use nullable Int64
                                if ((non_na % 1) == 0).all():
                                    df_local[c] = conv.astype('Int64')
                                else:
                                    df_local[c] = conv.astype(float).round(2)
                            except Exception:
                                continue

                    _normalize_df_types(df)
                    
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
                    # Determine which position columns to show: if user selected positions, show only those
                    try:
                        sel_pos_ints = [int(p) for p in selected_positions] if selected_positions else None
                    except Exception:
                        sel_pos_ints = None

                    preferred_position_columns = []
                    pos_range = sel_pos_ints if sel_pos_ints is not None else list(range(0,10))
                    for p in pos_range:
                        preferred_position_columns += [
                            f'{p}_Runs', f'{p}_Balls', f'{p}_SR', f'{p}_Average', f'{p}_BpB', f'{p}_4s', f'{p}_6s',
                            f'{p}_30s', f'{p}_50s', f'{p}_100s'
                        ]

                    preferred_order = [
                        'Sr.', 'Player', 'Matches', 'Innings', 'Not Outs', 'Dismissals',
                        'Runs', 'Balls', 'SR', 'Average', '4s', '6s', 'BpB', 'Dots', 'Dot_%',
                        # Aggregated selected-position summary (grouped)
                        'SelPos_Runs', 'SelPos_Balls', 'SelPos_SR', 'SelPos_Average', 'SelPos_Dismissals',
                        'SelPos_4s', 'SelPos_6s', 'SelPos_BpB', 'SelPos_Innings', 'SelPos_30s', 'SelPos_50s', 'SelPos_100s',
                        # Position stats (only selected positions if any)
                    ] + preferred_position_columns + [
                        'DO_Runs', 'DO_Balls', 'DO_SR', 'DO_Average', 'DO_4s', 'DO_6s', 'DO_BpB', 'DO_Dots', 'DO_Dot_%', 'DO_%'
                    ]
                    cols_in_order = [c for c in preferred_order if c in df.columns]
                    # Append any non-position columns not already in preferred_order; exclude
                    # position-specific columns for unselected positions so they don't appear at the end
                    extra_cols = []
                    for c in df.columns:
                        if c in cols_in_order:
                            continue
                        # If this looks like a position column (e.g., '6_Runs'), decide whether to include
                        parts = c.split('_', 1)
                        if len(parts) > 1 and parts[0].isdigit():
                            try:
                                pnum = int(parts[0])
                            except Exception:
                                extra_cols.append(c)
                                continue
                            # If user selected positions, only include columns for those positions
                            if sel_pos_ints is not None and pnum not in sel_pos_ints:
                                continue
                        # otherwise include the extra column
                        extra_cols.append(c)

                    cols_in_order += extra_cols
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
                        # Death-over dismissals column
                        "DO_Dismissals": player_do_dismissals.get(player, 0),
                        # Compute DO_Average using death-over dismissals where available; fall back to 0 if none
                        "DO_Average": (round(player_do_runs.get(player, 0) / player_do_dismissals.get(player, 1), 2)
                                        if player_do_dismissals.get(player, 0) > 0 else 0),
                        "DO_4s": player_do_fours.get(player, 0),
                        "DO_6s": player_do_sixes.get(player, 0),
                        "DO_%": f"{round((player_do_runs.get(player, 0) / max(player_runs.get(player, 1), 1)) * 100, 2)}%",
                        "DO_BpB": (round(player_do_balls.get(player, 0) / max((player_do_fours.get(player, 0) + player_do_sixes.get(player, 0)), 1), 2)
                                   if (player_do_fours.get(player, 0) + player_do_sixes.get(player, 0)) > 0 else '-'),
                        "Dots": player_dot_balls.get(player, 0),
                        "DO_Dots": player_do_dot_balls.get(player, 0),
                        "Dot_%": f"{round((player_dot_balls.get(player, 0) / max(player_balls.get(player, 1), 1)) * 100, 2)}%",
                        "DO_Dot_%": f"{round((player_do_dot_balls.get(player, 0) / max(player_do_balls.get(player, 1), 1)) * 100, 2)}%",
                        # Milestones
                        "30s": player_30s.get(player, 0),
                        "50s": player_50s.get(player, 0),
                        "100s": player_100s.get(player, 0)
                    }
                    for player in filtered_players
                }
                # Add aggregated selected-position columns (SelPos_*) to df_summary
                for player in list(data.keys()):
                    try:
                        sel_pos_ints = [int(p) for p in selected_positions] if selected_positions else None
                    except Exception:
                        sel_pos_ints = None

                    sel_runs = sel_balls = sel_4s = sel_6s = sel_innings = 0
                    sel_30s = sel_50s = sel_100s = 0
                    sel_dismissals = 0
                    pos_keys = range(0, 10) if not sel_pos_ints else sel_pos_ints
                    for pos in pos_keys:
                        pst = player_position_stats.get(player, {}).get(pos, {})
                        sel_runs += pst.get('runs', 0)
                        sel_balls += pst.get('balls', 0)
                        sel_4s += pst.get('4s', 0)
                        sel_6s += pst.get('6s', 0)
                        sel_innings += pst.get('innings', 0)

                        sel_30s += pst.get('30s', 0)
                        sel_50s += pst.get('50s', 0)
                        sel_100s += pst.get('100s', 0)
                        sel_dismissals += pst.get('dismissals', 0)

                    data[player]['SelPos_Runs'] = sel_runs
                    data[player]['SelPos_Balls'] = sel_balls
                    data[player]['SelPos_4s'] = sel_4s
                    data[player]['SelPos_6s'] = sel_6s
                    # SelPos balls-per-boundary
                    data[player]['SelPos_BpB'] = (round(sel_balls / max((sel_4s + sel_6s), 1), 2)
                                                   if (sel_4s + sel_6s) > 0 and sel_balls > 0 else '-')
                    # SelPos Strike Rate and Average
                    data[player]['SelPos_SR'] = round((sel_runs / max(sel_balls, 1)) * 100, 2) if sel_balls > 0 else 0
                    data[player]['SelPos_Innings'] = sel_innings
                    data[player]['SelPos_30s'] = sel_30s
                    data[player]['SelPos_50s'] = sel_50s
                    data[player]['SelPos_100s'] = sel_100s
                    data[player]['SelPos_Dismissals'] = sel_dismissals
                    data[player]['SelPos_Average'] = ('-' if sel_dismissals == 0 else round(sel_runs / sel_dismissals, 2))
                
                # Ensure percentage-like values are numeric (do not store as strings with %)
                for player_key, player_vals in data.items():
                    # DO_% was previously stored as a percent string; ensure numeric
                    if 'DO_%' in player_vals:
                        try:
                            # If it's a string with %, strip it
                            if isinstance(player_vals['DO_%'], str) and player_vals['DO_%'].endswith('%'):
                                player_vals['DO_%'] = float(player_vals['DO_%'].rstrip('%'))
                        except Exception:
                            try:
                                player_vals['DO_%'] = float(player_vals['DO_%'])
                            except Exception:
                                player_vals['DO_%'] = pd.NA
                    if 'Dot_%' in player_vals:
                        try:
                            if isinstance(player_vals['Dot_%'], str) and player_vals['Dot_%'].endswith('%'):
                                player_vals['Dot_%'] = float(player_vals['Dot_%'].rstrip('%'))
                        except Exception:
                            try:
                                player_vals['Dot_%'] = float(player_vals['Dot_%'])
                            except Exception:
                                player_vals['Dot_%'] = pd.NA
                    if 'DO_Dot_%' in player_vals:
                        try:
                            if isinstance(player_vals['DO_Dot_%'], str) and player_vals['DO_Dot_%'].endswith('%'):
                                player_vals['DO_Dot_%'] = float(player_vals['DO_Dot_%'].rstrip('%'))
                        except Exception:
                            try:
                                player_vals['DO_Dot_%'] = float(player_vals['DO_Dot_%'])
                            except Exception:
                                player_vals['DO_Dot_%'] = pd.NA

                df_summary = pd.DataFrame.from_dict(data, orient='index')

                # Coerce numeric-like columns in df_summary to proper numeric types so sorting works
                def _coerce_numeric_df_summary(df_local):
                    for c in df_local.columns:
                        try:
                            ser = df_local[c].astype(str).str.strip()
                        except Exception:
                            continue
                        cleaned = ser.str.rstrip('%').replace({'-': ''})
                        conv = pd.to_numeric(cleaned.replace({'': pd.NA}), errors='coerce')
                        if conv.notna().sum() > 0:
                            conv = conv.fillna(0)
                            conv = conv.replace([pd.NA, None], 0)
                            try:
                                conv = conv.replace([float('inf'), float('-inf')], 0)
                            except Exception:
                                pass
                            df_local[c] = conv

                _coerce_numeric_df_summary(df_summary)

                # Replace infinities and NaNs with 0 in df_summary so downstream plots/sorts work reliably
                try:
                    df_summary = df_summary.replace([float('inf'), float('-inf'), np.inf, -np.inf], 0).fillna(0)
                except Exception:
                    df_summary = df_summary.fillna(0)
                # Further normalize dtypes (ints vs floats)
                try:
                    def _normalize_df_summary_types(df_local):
                        for c in df_local.columns:
                            try:
                                s = df_local[c].astype(str).str.strip()
                                cleaned = s.str.rstrip('%').replace({'-': '', '': pd.NA})
                                conv = pd.to_numeric(cleaned.replace({pd.NA: None}), errors='coerce')
                                if conv.notna().sum() == 0:
                                    continue
                                non_na = conv.dropna()
                                if ((non_na % 1) == 0).all():
                                    df_local[c] = conv.astype('Int64')
                                else:
                                    df_local[c] = conv.astype(float).round(2)
                            except Exception:
                                continue
                    _normalize_df_summary_types(df_summary)
                except Exception:
                    pass

                # Add position-based columns (0 means player started the innings; 1 means after 1 wicket fell, ... up to 9)
                max_pos = 10  # track positions 0..9
                for player in df_summary.index:
                    pos_stats = player_position_stats.get(player, {})
                    for p in range(0, max_pos):
                        stats = pos_stats.get(p, {})
                        runs = stats.get('runs', 0)
                        balls = stats.get('balls', 0)
                        fours = stats.get('4s', 0)
                        sixes = stats.get('6s', 0)
                        dismissals = stats.get('dismissals', 0)

                        sr = round((runs / max(balls, 1)) * 100, 2) if balls > 0 else 0
                        avg = '-' if dismissals == 0 else round(runs / dismissals, 2)
                        bpb = (round(balls / max((fours + sixes), 1), 2) if (fours + sixes) > 0 and balls > 0 else '-')

                        df_summary.loc[player, f"{p}_Runs"] = runs
                        df_summary.loc[player, f"{p}_Balls"] = balls
                        df_summary.loc[player, f"{p}_SR"] = sr
                        df_summary.loc[player, f"{p}_Average"] = avg
                        df_summary.loc[player, f"{p}_BpB"] = bpb
                        df_summary.loc[player, f"{p}_4s"] = fours
                        df_summary.loc[player, f"{p}_6s"] = sixes
                        # milestones per position
                        df_summary.loc[player, f"{p}_30s"] = stats.get('30s', 0)
                        df_summary.loc[player, f"{p}_50s"] = stats.get('50s', 0)
                        df_summary.loc[player, f"{p}_100s"] = stats.get('100s', 0)
                
                # Sort by Total Runs in descending order
                df_summary = df_summary.sort_values(by="Total Runs", ascending=False)
                
                # Display summary of total matches
                st.markdown(f"**Analysis based on {len(filtered_matches)} matches**")

                # Helper to format selected positions into human-friendly ranges
                def _ordinal(n):
                    try:
                        n = int(n)
                    except Exception:
                        return str(n)
                    if 10 <= n % 100 <= 20:
                        suf = 'th'
                    else:
                        suf = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
                    return f"{n}{suf}"

                def _format_positions(sel_pos):
                    if not sel_pos:
                        return 'All positions'
                    # Convert to sorted unique ints
                    try:
                        nums = sorted({int(x) for x in sel_pos})
                    except Exception:
                        # fallback: join raw
                        return ', '.join(map(str, sel_pos))

                    ranges = []
                    start = prev = nums[0]
                    for n in nums[1:]:
                        if n == prev + 1:
                            prev = n
                            continue
                        # close range
                        if start == prev:
                            ranges.append(_ordinal(start))
                        else:
                            ranges.append(f"{_ordinal(start)}-{_ordinal(prev)}")
                        start = prev = n
                    # close final range
                    if start == prev:
                        ranges.append(_ordinal(start))
                    else:
                        ranges.append(f"{_ordinal(start)}-{_ordinal(prev)}")

                    # join with commas and an ampersand for the last item
                    if len(ranges) == 1:
                        return ranges[0]
                    if len(ranges) == 2:
                        return f"{ranges[0]} & {ranges[1]}"
                    return f"{', '.join(ranges[:-1])} & {ranges[-1]}"

                # Show selected positions (human-friendly)
                try:
                    pos_text = _format_positions(selected_positions) if 'selected_positions' in globals() or 'selected_positions' in locals() else 'All positions'
                except Exception:
                    pos_text = 'All positions'
                st.markdown(f"**Positions:** {pos_text}")
                
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
                    # Prefer showing columns in a friendly preferred order when available
                    stat_options = list(df_summary.columns)
                    try:
                        preferred_stat_names = [
                            'Matches', 'Innings', 'Not Outs', 'Dismissals',
                            'Total Runs', 'Total Balls', 'Strike Rate', 'Average',
                            '4s', '6s', 'BpB', 'Dots', 'Dot_%',
                            'SelPos_Runs', 'SelPos_Balls', 'SelPos_SR', 'SelPos_Average', 'SelPos_Dismissals', 'SelPos_4s', 'SelPos_6s', 'SelPos_BpB', 'SelPos_Innings', 'SelPos_30s', 'SelPos_50s', 'SelPos_100s',
                            'DO_Runs', 'DO_Balls', 'DO_SR', 'DO_Average', 'DO_4s', 'DO_6s', 'DO_%', 'DO_Dots', 'DO_Dot_%', 'DO_BpB'
                        ]
                        # Move any preferred names present in stat_options to the front, preserving their order
                        ordered = [s for s in preferred_stat_names if s in stat_options]
                        remaining = [s for s in stat_options if s not in ordered]
                        stat_options = ordered + remaining
                    except Exception:
                        pass

                    # Axis selectors and dynamic plot filters
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

                    # Ensure session state for dynamic plot filters
                    if 'plot_filters' not in st.session_state:
                        st.session_state['plot_filters'] = []

                    # Define operators used by filters
                    ops = ['>=', '<=', '>', '<', '==', '!=']

                    # Convert selected columns to numeric for plotting and for filtering
                    plot_df[x_col] = to_numeric_series(plot_df[x_col])
                    plot_df[y_col] = to_numeric_series(plot_df[y_col])

                    # Apply dynamic filters from session_state
                    for f in st.session_state.get('plot_filters', []):
                        col_name = f.get('col')
                        op = f.get('op')
                        raw_val = f.get('val')
                        if not col_name or raw_val is None or raw_val == '':
                            continue
                        try:
                            ser = to_numeric_series(plot_df[col_name])
                            val_str = str(raw_val).strip()
                            if val_str.endswith('%'):
                                val = float(val_str.rstrip('%'))
                            else:
                                val = float(val_str)
                            if op == '>=':
                                plot_df = plot_df[ser >= val]
                            elif op == '<=':
                                plot_df = plot_df[ser <= val]
                            elif op == '>':
                                plot_df = plot_df[ser > val]
                            elif op == '<':
                                plot_df = plot_df[ser < val]
                            elif op == '==':
                                plot_df = plot_df[ser == val]
                            elif op == '!=':
                                plot_df = plot_df[ser != val]
                        except Exception:
                            col_series = plot_df[col_name].astype(str)
                            if op == '==':
                                plot_df = plot_df[col_series == str(raw_val)]
                            elif op == '!=':
                                plot_df = plot_df[col_series != str(raw_val)]

                    # Create bubble plot in the main left column (col1) so it keeps its original width
                    # Filter out rows where selected x or y are not numeric/finite so scatter always has valid points
                    try:
                        x_ser = pd.to_numeric(plot_df[x_col], errors='coerce').fillna(0)
                        y_ser = pd.to_numeric(plot_df[y_col], errors='coerce').fillna(0)
                        try:
                            x_ser = x_ser.replace([float('inf'), float('-inf')], 0)
                            y_ser = y_ser.replace([float('inf'), float('-inf')], 0)
                        except Exception:
                            pass

                        # After filling NaN/inf with 0, all rows are valid; create a valid plotting df
                        plot_df_valid = plot_df.copy()
                        plot_df_valid[x_col] = x_ser
                        plot_df_valid[y_col] = y_ser

                        if plot_df_valid.empty:
                            st.warning(f"No valid numeric data points for the selected axes: {x_axis} vs {y_axis}")
                        else:
                            size_col = None
                            if "Total Runs" in plot_df_valid.columns and pd.api.types.is_numeric_dtype(plot_df_valid["Total Runs"]):
                                size_col = "Total Runs"

                            color_vals = plot_df_valid.index.astype(str).tolist() if not plot_df_valid.index.empty else None
                            text_vals = plot_df_valid.index.astype(str).tolist() if not plot_df_valid.index.empty else None

                            # Prepare a numeric size array for Plotly: convert, drop inf, and replace NaN with a small default
                            size_array = None
                            if "Total Runs" in plot_df_valid.columns:
                                s = pd.to_numeric(plot_df_valid["Total Runs"], errors='coerce').astype(float)
                                s = s.replace([np.inf, -np.inf], np.nan)
                                # If all sizes are NaN, fall back to a default small size; otherwise replace NaN with a small default
                                # default bubble size for missing values (reduced for smaller bubbles)
                                default_size = 4.0
                                if s.notna().sum() == 0:
                                    size_array = np.full(len(plot_df_valid), default_size)
                                else:
                                    s_filled = s.fillna(default_size)
                                    size_array = s_filled.to_numpy()

                            # Pass numeric arrays (or column names) to Plotly as recommended
                            fig = px.scatter(
                                plot_df_valid,
                                x=x_col,
                                y=y_col,
                                text=text_vals,
                                # size=size_array,
                                size=np.ones(len(plot_df_valid)) * 20,
                                size_max=20,
                                color=color_vals,
                                title=f"{y_axis} vs {x_axis}",
                                labels={x_col: x_axis, y_col: y_axis},
                                hover_data=[c for c in ["Total Runs", "Innings", "Strike Rate", "Average"] if c in plot_df_valid.columns]
                            )

                            fig.update_traces(textposition='top center', textfont=dict(size=12))
                            fig.update_layout(
                                showlegend=True,
                                height=600,
                                title_font=dict(size=18),
                                title_x=0.5,
                                xaxis=dict(title=x_axis, title_font=dict(size=20), tickfont=dict(size=18), showgrid=True, gridcolor='lightgray', gridwidth=0.5, showline=True, linecolor='black', linewidth=1, minor=dict(showgrid=False, gridcolor='rgba(200,200,200,0.2)')),
                                yaxis=dict(title=y_axis, title_font=dict(size=20), tickfont=dict(size=18), showgrid=True, gridcolor='lightgray', gridwidth=0.5, showline=True, linecolor='black', linewidth=1, minor=dict(showgrid=False, gridcolor='rgba(200,200,200,0.2)')),
                                legend=dict(font=dict(size=18))
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        import traceback
                        tb = traceback.format_exc()
                        st.error(f"Error creating plot: {e}")
                        st.text(tb)

                    # Render the plot filters directly below the plot (always visible)
                    st.markdown("#### Plot Filters")
                    st.caption("Add multiple filters to restrict plotted players (AND semantics)")
                    # Buttons to add/clear filters
                    add_cols = st.columns([1,1])
                    with add_cols[0]:
                        if st.button("Add filter", key="add_plot_filter"):
                            st.session_state['plot_filters'].append({'col': stat_options[0] if stat_options else '', 'op': '>=', 'val': ''})
                    with add_cols[1]:
                        if st.button("Clear", key="clear_plot_filters"):
                            st.session_state['plot_filters'] = []

                    # Render current filters as compact rows; allow removal
                    for i, f in list(enumerate(st.session_state.get('plot_filters', []))):
                        row_cols = st.columns([4,2,3,1])
                        try:
                            idx = stat_options.index(f.get('col')) if f.get('col') in stat_options else 0
                        except Exception:
                            idx = 0
                        with row_cols[0]:
                            col_sel = st.selectbox("Column", stat_options, index=idx, key=f"filter_col_{i}")
                        with row_cols[1]:
                            op_sel = st.selectbox("Operator", ops, index=ops.index(f.get('op')) if f.get('op') in ops else 0, key=f"filter_op_{i}")
                        with row_cols[2]:
                            val_in = st.text_input("Value", value=str(f.get('val', '')), key=f"filter_val_{i}")
                        with row_cols[3]:
                            remove = st.button("Remove", key=f"filter_remove_{i}")
                        st.session_state['plot_filters'][i] = {'col': col_sel, 'op': op_sel, 'val': val_in}
                        if remove:
                            st.session_state['plot_filters'].pop(i)
                            st.experimental_rerun()
                
                # Display the summary dataframe
                # Reorder summary stats rows into a logical order (keep any additional stats)
                preferred_stats_order = [
                    'Matches', 'Innings', 'Not Outs', 'Dismissals',
                    'Total Runs', 'Total Balls', 'Strike Rate', 'Average',
                    '4s', '6s', 'BpB', 'Dots', 'Dot_%',
                    # Aggregated selected-position summary (grouped)
                    'SelPos_Runs', 'SelPos_Balls', 'SelPos_SR', 'SelPos_Average', 'SelPos_Dismissals',
                    'SelPos_4s', 'SelPos_6s', 'SelPos_BpB', 'SelPos_Innings', 'SelPos_30s', 'SelPos_50s', 'SelPos_100s',
                    'DO_Runs', 'DO_Balls', 'DO_SR', 'DO_Average', 'DO_4s', 'DO_6s', 'DO_%', 'DO_Dots', 'DO_Dot_%', 'DO_BpB'
                ]

                # If the user selected specific positions, drop rows for unselected positions
                try:
                    sel_pos_ints = [int(p) for p in selected_positions] if selected_positions else None
                except Exception:
                    sel_pos_ints = None

                if sel_pos_ints is not None:
                    # Build a set of position-related row name prefixes to keep
                    keep_prefixes = set(str(p) + '_' for p in sel_pos_ints)
                    rows_to_drop = []
                    for idx in df_summary_transposed.index:
                        parts = idx.split('_', 1)
                        if len(parts) > 1 and parts[0].isdigit():
                            # position-specific row
                            if parts[0] not in [str(p) for p in sel_pos_ints]:
                                rows_to_drop.append(idx)
                    if rows_to_drop:
                        df_summary_transposed = df_summary_transposed.drop(rows_to_drop, errors='ignore')

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
