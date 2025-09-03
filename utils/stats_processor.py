import pandas as pd


def compute_true_batting_stats(match_data_list, top_n=25):
    """
    Compute true average and true strike rate for all batters across matches.
    match_data_list: list of match dicts (from JSON)
    Returns: DataFrame with batter, true_avg, true_sr, matches_played, runs, balls, outs
    """
    from collections import defaultdict
    bat_stats = defaultdict(lambda: {"runs": 0, "balls": 0, "outs": 0, "matches": 0, "true_avg_sum": 0, "true_sr_sum": 0})

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
