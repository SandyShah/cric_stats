def plot_runs_per_match(df):
    """Plot batting performance."""
    if not df.empty and 'role' in df and 'runs' in df:
        batting_df = df[df['role'] == 'batter'].sort_values('runs', ascending=False)
        fig = px.bar(batting_df,
                    x='player',
                    y='runs',
                    color='team',
                    title="Batting Performance",
                    labels={'player': 'Batsman', 'runs': 'Runs Scored'},
                    hover_data=['balls', 'fours', 'sixes', 'strike_rate'])
        fig.update_layout(xaxis_tickangle=-45)
        return fig
    return px.scatter(title="No batting data found")

def plot_top_players(df):
    """Plot bowling performance."""
    if not df.empty and 'role' in df and 'wickets' in df:
        bowling_df = df[df['role'] == 'bowler'].sort_values('wickets', ascending=False)
        fig = px.bar(bowling_df,
                    x='player',
                    y='wickets',
                    color='team',
                    title="Bowling Performance",
                    labels={'player': 'Bowler', 'wickets': 'Wickets Taken'},
                    hover_data=['overs', 'runs', 'economy'])
        fig.update_layout(xaxis_tickangle=-45)
        return fig
    return px.scatter(title="No bowling data found")
import plotly.express as px


def plot_true_batting_stats(df):
    """
    Scatter plot of true average vs true strike rate for top batters,
    exactly as shown in the article, with quadrant analysis.
    """
    # Create the scatter plot
    fig = px.scatter(
        df,
        x="true_sr",
        y="true_avg",
        text="batter",
        size="runs",
        color="avg_position",  # Color by batting position
        labels={
            "true_sr": "True Strike Rate (%)", 
            "true_avg": "True Average (%)",
            "avg_position": "Average Batting Position"
        },
        title="True Average vs True Strike Rate (Top Run Scorers)"
    )
    
    # Add quadrant lines at x=0 and y=0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Customize text position and appearance
    fig.update_traces(
        textposition="top center",
        textfont=dict(size=10),
        marker=dict(opacity=0.8)
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="True Strike Rate (%)",
        yaxis_title="True Average (%)",
        legend_title="Batting Position",
        height=700,
        width=1000,
        showlegend=True,
        # Add quadrant annotations
        annotations=[
            dict(x=50, y=50, text="Elite Performers<br>(High Avg & SR)", showarrow=False),
            dict(x=-50, y=50, text="Anchors<br>(High Avg, Low SR)", showarrow=False),
            dict(x=50, y=-50, text="Aggressive Players<br>(Low Avg, High SR)", showarrow=False),
            dict(x=-50, y=-50, text="Struggling Players<br>(Low Avg & SR)", showarrow=False),
        ]
    )
    
    return fig
