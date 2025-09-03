---
title: "Cricket Stats Explorer"
emoji: 🏏
colorFrom: yellow
colorTo: green
sdk: docker
python_version: "3.10"
app_file: streamlit_app.py
pinned: false
---

# Cricket Stats Explorer 🏏

This is a Streamlit app deployed on HuggingFace Spaces to explore cricket statistics with
True Average and True Strike Rate visualizations.

# 📊 Cricket Stats Analysis App – Requirements

## 🎯 Project Idea

The goal of this project is to build a **Streamlit-based Cricket Stats Analysis app** that allows users to explore, filter, and visualize cricket data (from multiple JSON files containing match/series/season data such as IPL).

The app should dynamically load JSON files from a specified folder (e.g., containing data from multiple years or tournaments), allow the user to select which dataset to analyze via a **dropdown**, and then generate processed outputs such as tables, charts, and insights.

This project will serve as a foundation, with **LLM/NLP integration planned in Phase 2** (e.g., querying stats in natural language).

---

## 📂 Inputs

1. **Data Files (JSON)**
   * All raw cricket data will be stored in a single folder.
   * Files may belong to different years/tournaments (e.g., IPL 2020, IPL 2021, World Cup).
   * Each file contains structured data like players, matches, scores, stats.

2. **User Selections (Streamlit UI)**
   * **Tournament/Series**: Dropdown (fetched dynamically from available JSON files in folder).
   * **Filter options**: (Phase 1) basic filters like team, year, match, player.
   * (Phase 2) additional filters like venue, batting/bowling performance, etc.

---

## 📤 Outputs

1. **Processed Data Display**
   * Show loaded JSON data in a **clean tabular format** (pandas DataFrame).
   * Highlight key stats such as runs, wickets, strike rate, economy.

2. **Visualizations** (using `matplotlib` or `plotly`)
   * Runs per match (line/bar chart).
   * Player performance comparison (bar/heatmap).
   * Team win/loss stats (pie or stacked bar).

3. **Summary Section**
   * Key insights such as:
     * Top run scorers
     * Best bowlers (most wickets, best economy)
     * Team standings

4. **Download Option**
   * Option to download filtered/processed stats as CSV.

---

## 🖥️ Streamlit UI Layout

* **Sidebar**
  * Dropdown for tournament/series (list of JSON files).
  * Filter options (team, player, year).
  * Checkbox for selecting type of visualization.

* **Main Page**
  * Title + Description of selected dataset.
  * Data Preview (DataFrame).
  * Charts & Visuals.
  * Key Insights/Summaries.
  * Download button.

---

## 🚀 Tech Stack

* **Backend/Data**: Python (pandas, json).
* **Frontend/UI**: Streamlit.
* **Visualization**: matplotlib / plotly.
* **File Handling**: os, glob (to fetch all JSON files in folder).
* (Future) **LLM Integration**: OpenAI API or local model for natural language queries.

---

## ✅ Phase 1 Scope

* Load all JSON files from `data/` folder.
* Display dropdown for selecting one dataset (file).
* Display raw + processed stats.
* Add filtering (team, player).
* Generate basic charts.
* Provide CSV download.

---

## 🔮 Phase 2 (Later)

* Extend filters (venue, year, match type).
* Add comparison views (e.g., player vs player, team vs team).
* Integrate LLM for natural-language questions:
  * “Who was the top scorer for MI in 2021?”
  * “Show me RCB’s win/loss ratio across years.”
