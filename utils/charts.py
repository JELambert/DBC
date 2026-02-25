"""Reusable Plotly chart builders with DBC wine theme."""

import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from utils.theme import COLORS, MEMBER_COLORS, PLOTLY_LAYOUT, apply_plotly_theme


def horizontal_bar(df, x, y, title="", color=None, color_discrete_map=None):
    """Horizontal bar chart."""
    fig = px.bar(
        df, x=x, y=y, orientation="h", title=title,
        color=color, color_discrete_map=color_discrete_map or {},
    )
    if not color:
        fig.update_traces(marker_color=COLORS["primary"])
    apply_plotly_theme(fig)
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return fig


def grouped_bar(df, x, y_cols, names=None, title="", barmode="group"):
    """Grouped bar chart with multiple y columns."""
    fig = go.Figure()
    colors = [COLORS["primary"], COLORS["secondary"], COLORS["accent"]]
    for i, col in enumerate(y_cols):
        fig.add_trace(go.Bar(
            x=df[x], y=df[col],
            name=names[i] if names else col,
            marker_color=colors[i % len(colors)],
        ))
    fig.update_layout(barmode=barmode, title=title)
    apply_plotly_theme(fig)
    return fig


def member_bar(df, x, y, member_col="Member", title=""):
    """Bar chart colored by member."""
    fig = px.bar(
        df, x=x, y=y, color=member_col, title=title,
        color_discrete_map=MEMBER_COLORS,
    )
    apply_plotly_theme(fig)
    return fig


def scatter_plot(df, x, y, title="", color=None, size=None, text=None,
                 color_discrete_map=None, trendline=None, hover_data=None):
    """Scatter plot with optional trendline."""
    fig = px.scatter(
        df, x=x, y=y, title=title, color=color, size=size, text=text,
        color_discrete_map=color_discrete_map or {},
        trendline=trendline, hover_data=hover_data,
    )
    apply_plotly_theme(fig)
    return fig


def radar_chart(categories, values, name="", fill=True):
    """Single-series radar chart."""
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],  # close the polygon
        theta=categories + [categories[0]],
        fill="toself" if fill else None,
        name=name,
        line=dict(color=COLORS["primary"]),
        fillcolor=f"rgba(114, 47, 55, 0.3)",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 5], gridcolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        ),
    )
    apply_plotly_theme(fig)
    return fig


def multi_radar(categories, series_dict, title=""):
    """Multi-series radar chart. series_dict = {name: values}."""
    fig = go.Figure()
    colors = list(MEMBER_COLORS.values())
    for i, (name, values) in enumerate(series_dict.items()):
        color = MEMBER_COLORS.get(name, colors[i % len(colors)])
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=name,
            line=dict(color=color),
            fillcolor=f"rgba({int(color[1:3], 16)},{int(color[3:5], 16)},{int(color[5:7], 16)},0.15)",
        ))
    fig.update_layout(
        title=title,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 5], gridcolor="rgba(255,255,255,0.1)"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        ),
    )
    apply_plotly_theme(fig)
    return fig


def donut_chart(df, values, names, title=""):
    """Donut chart (pie with hole)."""
    fig = px.pie(
        df, values=values, names=names, title=title, hole=0.4,
        color_discrete_sequence=[COLORS["primary"], COLORS["secondary"],
                                 COLORS["accent"], "#E63946", "#2A9D8F",
                                 "#E9C46A", "#F4A261"],
    )
    fig.update_traces(textfont_color=COLORS["text"])
    apply_plotly_theme(fig)
    return fig


def line_chart(df, x, y_cols, names=None, title="", dash_cols=None):
    """Line chart with multiple series. dash_cols is a list of column names to render dashed."""
    fig = go.Figure()
    colors = [COLORS["primary"], COLORS["secondary"], COLORS["accent"],
              COLORS["danger"], COLORS["success"]]
    dash_cols = dash_cols or []
    for i, col in enumerate(y_cols):
        dash = "dash" if col in dash_cols else "solid"
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col],
            mode="lines+markers",
            name=names[i] if names else col,
            line=dict(color=colors[i % len(colors)], dash=dash),
            marker=dict(size=6),
        ))
    fig.update_layout(title=title)
    apply_plotly_theme(fig)
    return fig


def member_line_chart(df, x, y, member_col="Member", title=""):
    """Line chart colored by member."""
    fig = px.line(
        df, x=x, y=y, color=member_col, title=title,
        color_discrete_map=MEMBER_COLORS, markers=True,
    )
    apply_plotly_theme(fig)
    return fig


def heatmap(z, x_labels, y_labels, title="", colorscale=None, zmin=None, zmax=None):
    """Heatmap chart."""
    if colorscale is None:
        colorscale = [
            [0, "#E63946"],    # red (low)
            [0.25, "#F4A261"], # orange
            [0.5, "#E9C46A"],  # yellow
            [0.75, "#2A9D8F"], # teal
            [1, "#2A9D8F"],    # green (high)
        ]
    fig = go.Figure(data=go.Heatmap(
        z=z, x=x_labels, y=y_labels,
        colorscale=colorscale,
        zmin=zmin, zmax=zmax,
        hoverongaps=False,
        xgap=2, ygap=2,
    ))
    fig.update_layout(title=title)
    apply_plotly_theme(fig)
    return fig


def violin_plot(df, y, x=None, title="", color=None, color_discrete_map=None):
    """Violin plot."""
    fig = px.violin(
        df, y=y, x=x, title=title, color=color,
        color_discrete_map=color_discrete_map or {},
        box=True, points="all",
    )
    apply_plotly_theme(fig)
    return fig


def histogram(df, x, title="", nbins=10, color=None):
    """Histogram."""
    fig = px.histogram(
        df, x=x, title=title, nbins=nbins, color=color,
        color_discrete_map=MEMBER_COLORS if color else {},
    )
    fig.update_traces(marker_line_width=1, marker_line_color=COLORS["bg_dark"])
    if not color:
        fig.update_traces(marker_color=COLORS["primary"])
    apply_plotly_theme(fig)
    return fig


def timeline_scatter(df, x, y, size=None, color=None, text=None, title="",
                     color_discrete_map=None, hover_data=None):
    """Timeline scatter plot."""
    fig = px.scatter(
        df, x=x, y=y, size=size, color=color, text=text,
        title=title, color_discrete_map=color_discrete_map or MEMBER_COLORS,
        hover_data=hover_data,
    )
    fig.update_traces(textposition="top center")
    apply_plotly_theme(fig)
    return fig


def area_chart(df, x, y_cols, names=None, title=""):
    """Stacked area chart."""
    fig = go.Figure()
    colors = [COLORS["primary"], COLORS["secondary"], COLORS["accent"]]
    for i, col in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col],
            mode="lines",
            name=names[i] if names else col,
            fill="tozeroy" if i == 0 else "tonexty",
            line=dict(color=colors[i % len(colors)]),
        ))
    fig.update_layout(title=title)
    apply_plotly_theme(fig)
    return fig


def correlation_heatmap(corr_matrix, title="Taste Similarity Matrix"):
    """Correlation matrix heatmap."""
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns.tolist(),
        y=corr_matrix.index.tolist(),
        colorscale=[
            [0, "#E63946"],
            [0.5, "#1A1A2E"],
            [1, "#2A9D8F"],
        ],
        zmin=-1, zmax=1,
        text=np.round(corr_matrix.values, 2),
        texttemplate="%{text}",
        xgap=2, ygap=2,
    ))
    fig.update_layout(title=title)
    apply_plotly_theme(fig)
    return fig


def network_graph(nodes, edges, title=""):
    """Simple network graph using Plotly scatter.

    nodes: list of dicts with 'name', 'x', 'y'
    edges: list of dicts with 'source', 'target', 'weight'
    """
    fig = go.Figure()

    # Draw edges
    for edge in edges:
        src = next(n for n in nodes if n["name"] == edge["source"])
        tgt = next(n for n in nodes if n["name"] == edge["target"])
        width = max(1, edge["weight"] * 5)
        opacity = min(1.0, 0.3 + edge["weight"] * 0.7)
        fig.add_trace(go.Scatter(
            x=[src["x"], tgt["x"]], y=[src["y"], tgt["y"]],
            mode="lines",
            line=dict(width=width, color=f"rgba(201,169,110,{opacity})"),
            showlegend=False, hoverinfo="none",
        ))

    # Draw nodes
    for node in nodes:
        color = MEMBER_COLORS.get(node["name"], COLORS["secondary"])
        fig.add_trace(go.Scatter(
            x=[node["x"]], y=[node["y"]],
            mode="markers+text",
            marker=dict(size=30, color=color, line=dict(width=2, color=COLORS["text"])),
            text=[node["name"]], textposition="top center",
            textfont=dict(color=COLORS["text"], size=12),
            showlegend=False,
        ))

    fig.update_layout(
        title=title,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    apply_plotly_theme(fig)
    return fig
