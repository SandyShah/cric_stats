import os
import json


def load_json_files(data_folder: str):
    """Return list of JSON files in the folder."""
    return [f for f in os.listdir(data_folder) if f.endswith(".json")]

def get_match_info(file_path: str):
    """
    Extracts detailed match info for filters and display.
    Returns: dict with match details including date, teams, venue, etc.
    """
    with open(file_path, "r") as f:
        data = json.load(f)
    
    info = data.get("info", {})
    teams = info.get("teams", [])
    
    # Get first date from dates array
    dates = info.get("dates", [])
    match_date = dates[0] if dates else ""
    
    # Get year from season or date
    try:
        year = int(info.get("season", match_date[:4]))
    except (ValueError, TypeError):
        year = 0
        
    event = info.get("event", {})
    tournament = event.get("name", "")
    match_number = event.get("match_number", "")
    
    # Create a detailed match name
    match_name = f"{teams[0]} vs {teams[1]} - Match {match_number}"
    if match_date:
        match_name += f" ({match_date})"
        
    venue = info.get("venue", "")
    city = info.get("city", "")
    result = info.get("outcome", {}).get("winner", "No Result")
    
    return {
        "match_name": match_name,
        "year": year,
        "teams": teams,
        "team1": teams[0] if teams else "",
        "team2": teams[1] if len(teams) > 1 else "",
        "tournament": tournament,
        "match_number": match_number,
        "date": match_date,
        "venue": venue,
        "city": city,
        "result": result,
        "file_path": file_path
    }

def load_selected_dataset(file_path: str):
    """Load selected JSON dataset."""
    with open(file_path, "r") as f:
        data = json.load(f)
    return data
