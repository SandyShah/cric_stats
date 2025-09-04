import pandas as pd
from collections import defaultdict


def compute_basic_stats(dataset, team_filter=None, player_filter=None):
    """
    Convert JSON dataset to DataFrame and compute basic stats.
    Processes innings data and computes batting/bowling stats.
    """
    # Extract match info
    info = dataset.get('info', {})
    innings_data = dataset.get('innings', [])

    # Process innings data
    innings_stats = []

    for inning in innings_data:
        team = inning.get('team', '')
        overs = inning.get('overs', [])

        # Initialize stats for this innings
        batters_stats = {}
        bowlers_stats = {}

        # Process each over
        for over in overs:
            for delivery in over.get('deliveries', []):
                batter = delivery.get('batter', '')
                bowler = delivery.get('bowler', '')
                runs = delivery.get('runs', {})
                batter_runs = runs.get('batter', 0)
                extras = runs.get('extras', 0)
                total = runs.get('total', 0)

                # Update batter stats
                if batter not in batters_stats:
                    batters_stats[batter] = {'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0}
                batters_stats[batter]['runs'] += batter_runs
                batters_stats[batter]['balls'] += 1
                if batter_runs == 4:
                    batters_stats[batter]['fours'] += 1
                elif batter_runs == 6:
                    batters_stats[batter]['sixes'] += 1

                # Update bowler stats
                if bowler not in bowlers_stats:
                    bowlers_stats[bowler] = {'runs': 0, 'balls': 0, 'wickets': 0}
                bowlers_stats[bowler]['runs'] += total
                bowlers_stats[bowler]['balls'] += 1
                if 'wickets' in delivery:
                    bowlers_stats[bowler]['wickets'] += len(delivery['wickets'])

        # Convert stats to DataFrame records
        for batter, stats in batters_stats.items():
            innings_stats.append({
                'team': team,
                'player': batter,
                'role': 'batter',
                'runs': stats['runs'],
                'balls': stats['balls'],
                'fours': stats['fours'],
                'sixes': stats['sixes'],
                'strike_rate': (stats['runs'] / stats['balls'] * 100) if stats['balls'] > 0 else 0
            })

        for bowler, stats in bowlers_stats.items():
            overs = stats['balls'] // 6 + (stats['balls'] % 6) / 10
            innings_stats.append({
                'team': team,
                'player': bowler,
                'role': 'bowler',
                'overs': overs,
                'runs': stats['runs'],
                'wickets': stats['wickets'],
                'economy': stats['runs'] / overs if overs > 0 else 0
            })

    # Create DataFrame
    df = pd.DataFrame(innings_stats)

    # Apply filters
    if team_filter:
        df = df[df['team'] == team_filter]
    if player_filter:
        df = df[df['player'].str.contains(player_filter, case=False, na=False)]

    return df


def compute_match_level_true_batting_stats(dataset):
    """
    Compute true batting stats at match level.
    True average = ((player_avg / top6_avg) - 1) * 100
    True strike rate = ((player_sr / top6_sr) - 1) * 100

    Args:
        dataset: Single match JSON data
    Returns:
        DataFrame with player-level true batting stats for this match
    """
    innings_data = dataset.get('innings', [])
    match_info = dataset.get('info', {})

    # Get players for each team (assume first 6 are top-order)
    team_players = {}
    for team, players in match_info.get('players', {}).items():
        team_players[team] = players[:6]  # Top 6 batters

    # Track stats for each player in this match
    player_stats = defaultdict(lambda: {
        'runs': 0, 'balls': 0, 'outs': 0, 'team': ''
    })

    # Process each innings
    for inning in innings_data:
        team = inning.get('team', '')

        # Process deliveries to collect stats
        for over in inning.get('overs', []):
            for delivery in over.get('deliveries', []):
                batter = delivery.get('batter', '')
                runs = delivery.get('runs', {}).get('batter', 0)

                player_stats[batter]['runs'] += runs
                player_stats[batter]['balls'] += 1
                player_stats[batter]['team'] = team

                # Check for wickets
                if 'wickets' in delivery:
                    for wicket in delivery['wickets']:
                        if wicket.get('player_out') == batter:
                            player_stats[batter]['outs'] += 1

    # Calculate top 6 aggregate stats for each team
    team_top6_stats = {}
    for team, top6_players in team_players.items():
        total_runs = sum(player_stats[p]['runs'] for p in top6_players if p in player_stats)
        total_balls = sum(player_stats[p]['balls'] for p in top6_players if p in player_stats)
        total_outs = sum(player_stats[p]['outs'] for p in top6_players if p in player_stats)

        team_top6_stats[team] = {
            'avg': total_runs / total_outs if total_outs > 0 else 0,
            'sr': (total_runs / total_balls * 100) if total_balls > 0 else 0
        }

    # Calculate true stats for each player
    results = []
    for player, stats in player_stats.items():
        if stats['balls'] > 0:  # Only include players who faced balls
            team = stats['team']
            player_avg = stats['runs'] / stats['outs'] if stats['outs'] > 0 else stats['runs']  # If not out, use runs
            player_sr = (stats['runs'] / stats['balls']) * 100

            # Get team's top 6 benchmarks
            top6_avg = team_top6_stats.get(team, {}).get('avg', 0)
            top6_sr = team_top6_stats.get(team, {}).get('sr', 0)

            # Calculate true stats
            true_avg = ((player_avg / top6_avg) - 1) * 100 if top6_avg > 0 else 0
            true_sr = ((player_sr / top6_sr) - 1) * 100 if top6_sr > 0 else 0

            results.append({
                'player': player,
                'team': team,
                'runs': stats['runs'],
                'balls': stats['balls'],
                'outs': stats['outs'],
                'average': player_avg,
                'strike_rate': player_sr,
                'true_average': true_avg,
                'true_strike_rate': true_sr,
                'is_top6': player in team_players.get(team, [])
            })

    return pd.DataFrame(results)


def compute_true_batting_stats(match_data_list, top_n=25):
    """
    Compute true average and true strike rate as per the article:
    True average = ((player_avg / top6_avg) - 1) * 100
    True strike rate = ((player_sr / top6_sr) - 1) * 100

    Args:
        match_data_list: list of match dicts (from JSON)
        top_n: number of top run scorers to return
    Returns:
        DataFrame with batter stats including true_avg and true_sr
    """
    from collections import defaultdict

    # Track stats for each batter across all matches
    bat_stats = defaultdict(lambda: {
        "runs": 0,          # Total runs
        "balls": 0,         # Total balls
        "outs": 0,         # Total dismissals
        "matches": 0,       # Number of matches
        "true_avg_sum": 0,  # Sum of true averages (for calculating mean)
        "true_sr_sum": 0,   # Sum of true strike rates (for calculating mean)
        "position_sum": 0,  # Sum of batting positions (for calculating mean)
    })

    for match in match_data_list:
        # Get top 6 batters for each team (assume first 6 in players list)
        innings = match.get("innings", [])
        top6_stats = []
        for inn in innings:
            team = inn.get("team")
            players = match["info"]["players"].get(team, [])[:6]
            # Collect runs and outs for top 6
            runs = defaultdict(int)
            balls = defaultdict(int)
            outs = defaultdict(int)
            for over in inn.get("overs", []):
                for delivery in over.get("deliveries", []):
                    batter = delivery.get("batter")
                    runs[batter] += delivery["runs"]["batter"]
                    balls[batter] += 1
                    if "wickets" in delivery:
                        for w in delivery["wickets"]:
                            if w.get("player_out") == batter:
                                outs[batter] += 1
            # Only consider top 6
            top6_runs = sum(runs[p] for p in players)
            top6_outs = sum(outs[p] for p in players)
            top6_balls = sum(balls[p] for p in players)
            top6_stats.append({"runs": top6_runs, "outs": top6_outs, "balls": top6_balls, "players": players})

        # For each batter in match, calculate true stats
        for inn, top6 in zip(innings, top6_stats):
            for over in inn.get("overs", []):
                for delivery in over.get("deliveries", []):
                    batter = delivery.get("batter")
                    bat_stats[batter]["runs"] += delivery["runs"]["batter"]
                    bat_stats[batter]["balls"] += 1
                    if "wickets" in delivery:
                        for w in delivery["wickets"]:
                            if w.get("player_out") == batter:
                                bat_stats[batter]["outs"] += 1
                    # True stats for this match
                    # True average: (batter_avg / top6_avg - 1) * 100
                    # True strike rate: (batter_sr / top6_sr - 1) * 100
            # Compute batter's match stats
            for p in top6["players"]:
                runs = bat_stats[p]["runs"]
                balls = bat_stats[p]["balls"]
                outs = bat_stats[p]["outs"]
                # Avoid div by zero
                batter_avg = runs / outs if outs else 0
                top6_avg = top6["runs"] / top6["outs"] if top6["outs"] else 0
                batter_sr = (runs / balls) * 100 if balls else 0
                top6_sr = (top6["runs"] / top6["balls"] * 100) if top6["balls"] else 0
                true_avg = ((batter_avg / top6_avg) - 1) * 100 if top6_avg else 0
                true_sr = ((batter_sr / top6_sr) - 1) * 100 if top6_sr else 0
                bat_stats[p]["true_avg_sum"] += true_avg
                bat_stats[p]["true_sr_sum"] += true_sr
                bat_stats[p]["matches"] += 1

    # Prepare DataFrame
    rows = []
    for batter, stats in bat_stats.items():
        matches = stats["matches"]
        if matches > 0:
            rows.append({
                "batter": batter,
                "true_avg": stats["true_avg_sum"] / matches,
                "true_sr": stats["true_sr_sum"] / matches,
                "matches_played": matches,
                "runs": stats["runs"],
                "balls": stats["balls"],
                "outs": stats["outs"]
            })
    df = pd.DataFrame(rows)
    df = df.sort_values(by="runs", ascending=False).head(top_n)
    return df