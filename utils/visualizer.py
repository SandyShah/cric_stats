import plotly.express as px


def plot_true_batting_stats(df):
    """
    Scatter plot of true average vs true strike rate for top batters.
    """
    fig = px.scatter(
        df,
        x="true_sr",
        y="true_avg",
        text="batter",
        size="runs",
        color="matches_played",
        labels={"true_sr": "True Strike Rate (%)", "true_avg": "True Average (%)"},
        title="True Average vs True Strike Rate (Top Batters)"
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(
        xaxis_title="True Strike Rate (%)",
        yaxis_title="True Average (%)",
        legend_title="Matches Played",
        height=600
    )
    return fig
