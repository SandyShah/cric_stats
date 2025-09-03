import os
import json

def load_json_files(data_folder: str):
    """Return list of JSON files in the folder."""
    return [f for f in os.listdir(data_folder) if f.endswith(".json")]

def load_selected_dataset(file_path: str):
    """Load selected JSON dataset."""
    with open(file_path, "r") as f:
        data = json.load(f)
    return data
