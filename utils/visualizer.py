import plotly.express as px


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
        fig.update_layout(
            xaxis_tickangle=-45,
            title_font=dict(size=20),
            title_x=0.5,
            xaxis=dict(title_font=dict(size=16), tickfont=dict(size=12), showgrid=True, gridcolor='lightgray', gridwidth=0.5, showline=True, linecolor='black', linewidth=1, minor=dict(showgrid=False, gridcolor='rgba(200,200,200,0.2)')),
            yaxis=dict(title_font=dict(size=16), tickfont=dict(size=12), showgrid=True, gridcolor='lightgray', gridwidth=0.5, showline=True, linecolor='black', linewidth=1, minor=dict(showgrid=False, gridcolor='rgba(200,200,200,0.2)')),
            legend=dict(font=dict(size=12))
        )
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
        fig.update_layout(
            xaxis_tickangle=-45,
            title_font=dict(size=20),
            title_x=0.5,
            xaxis=dict(title_font=dict(size=16), tickfont=dict(size=12), showgrid=True, gridcolor='lightgray', gridwidth=0.5, showline=True, linecolor='black', linewidth=1, minor=dict(showgrid=False, gridcolor='rgba(200,200,200,0.2)')),
            yaxis=dict(title_font=dict(size=16), tickfont=dict(size=12), showgrid=True, gridcolor='lightgray', gridwidth=0.5, showline=True, linecolor='black', linewidth=1, minor=dict(showgrid=False, gridcolor='rgba(200,200,200,0.2)')),
            legend=dict(font=dict(size=12))
        )
        return fig
    return px.scatter(title="No bowling data found")


def plot_true_batting_stats(df):
    """Create scatter plot of true average vs true strike rate."""
    fig = px.scatter(
        df, 
        x='true_sr', 
        y='true_avg',
        hover_data=['batter', 'runs', 'matches_played'],
        title='True Average vs True Strike Rate (Top Run Scorers)',
        labels={
            'true_sr': 'True Strike Rate (%)',
            'true_avg': 'True Average (%)'
        }
    )

    # Add quadrant lines
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)

    # Add annotations for quadrants
    fig.add_annotation(x=20, y=20, text="High Avg & SR", showarrow=False, font=dict(color="green"))
    fig.add_annotation(x=-20, y=20, text="High Avg, Low SR", showarrow=False, font=dict(color="blue"))
    fig.add_annotation(x=20, y=-20, text="Low Avg, High SR", showarrow=False, font=dict(color="orange"))
    fig.add_annotation(x=-20, y=-20, text="Low Avg & SR", showarrow=False, font=dict(color="red"))

    fig.update_layout(
        width=800,
        height=600,
    showlegend=False,
    title_font=dict(size=20),
    title_x=0.5,
    xaxis=dict(title_font=dict(size=16), tickfont=dict(size=12), showgrid=True, gridcolor='lightgray', gridwidth=0.5, showline=True, linecolor='black', linewidth=1, minor=dict(showgrid=False, gridcolor='rgba(200,200,200,0.2)')),
    yaxis=dict(title_font=dict(size=16), tickfont=dict(size=12), showgrid=True, gridcolor='lightgray', gridwidth=0.5, showline=True, linecolor='black', linewidth=1, minor=dict(showgrid=False, gridcolor='rgba(200,200,200,0.2)'))
    )

    return fig


def plot_match_level_true_batting_stats(df):
    """Create scatter plot for match-level true batting stats."""
    # Color by team
    fig = px.scatter(
        df, 
        x='true_strike_rate', 
        y='true_average',
        color='team',
        size='runs',
        hover_data=['player', 'runs', 'balls', 'is_top6'],
        title='Match-Level True Average vs True Strike Rate',
        labels={
            'true_strike_rate': 'True Strike Rate (%)',
            'true_average': 'True Average (%)'
        }
    )

    # Add quadrant lines
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)

    # Add annotations for quadrants
    fig.add_annotation(x=10, y=10, text="Above Average", showarrow=False, font=dict(color="green"))
    fig.add_annotation(x=-10, y=10, text="Anchor Role", showarrow=False, font=dict(color="blue"))
    fig.add_annotation(x=10, y=-10, text="Aggressive", showarrow=False, font=dict(color="orange"))
    fig.add_annotation(x=-10, y=-10, text="Below Average", showarrow=False, font=dict(color="red"))

    # Add player names as text
    for _, row in df.iterrows():
        fig.add_annotation(
            x=row['true_strike_rate'],
            y=row['true_average'],
            text=row['player'].split()[-1],  # Last name only
            showarrow=False,
            font=dict(size=8),
            yshift=10
        )

    fig.update_layout(
        width=800,
        height=600,
        title_font=dict(size=20),
        title_x=0.5,
    xaxis=dict(title_font=dict(size=16), tickfont=dict(size=12), showgrid=True, gridcolor='lightgray', gridwidth=0.5, showline=True, linecolor='black', linewidth=1, minor=dict(showgrid=False, gridcolor='rgba(200,200,200,0.2)')),
    yaxis=dict(title_font=dict(size=16), tickfont=dict(size=12), showgrid=True, gridcolor='lightgray', gridwidth=0.5, showline=True, linecolor='black', linewidth=1, minor=dict(showgrid=False, gridcolor='rgba(200,200,200,0.2)')),
    legend=dict(font=dict(size=12))
    )

    return fig