"""Ratings Analytics -- Statistical Deep-Dive into DBC ratings."""

import numpy as np
import streamlit as st

from utils.data_loader import get_book_summary, get_member_book_matrix, get_ratings_long
from utils.calculations import rating_trends, taste_similarity_matrix
from utils.theme import COLORS, page_header, metric_card_css
from utils import charts

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.markdown(page_header("Ratings Analytics", subtitle="Statistical Deep-Dive"), unsafe_allow_html=True)
st.markdown(metric_card_css(), unsafe_allow_html=True)

summary = get_book_summary()
ratings = get_ratings_long()

# ---------------------------------------------------------------------------
# 1. Key Metrics Row
# ---------------------------------------------------------------------------
overall_like = ratings["Likeability"].mean()
overall_imp = ratings["Importance"].mean()
most_agreed = summary.loc[summary["std_like"].idxmin()]
most_polarizing = summary.loc[summary["std_like"].idxmax()]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Overall Mean Likeability", f"{overall_like:.2f}")
c2.metric("Overall Mean Importance", f"{overall_imp:.2f}")
c3.metric("Most Agreed-Upon Book", most_agreed["Book"], delta=f"std {most_agreed['std_like']:.2f}")
c4.metric("Most Polarizing Book", most_polarizing["Book"], delta=f"std {most_polarizing['std_like']:.2f}")

st.divider()

# ---------------------------------------------------------------------------
# 2. Likeability vs Importance Scatter
# ---------------------------------------------------------------------------
st.subheader("Likeability vs Importance")

summary["Year"] = summary["Date"].dt.year.astype(str)

fig_scatter = charts.scatter_plot(
    summary,
    x="avg_like",
    y="avg_imp",
    size="num_raters",
    color="Year",
    text="Book",
    title="Likeability vs Importance (size = # raters)",
    trendline="ols",
    hover_data=["Proposer"],
)
fig_scatter.update_traces(textposition="top center", textfont_size=9)

# Axis ranges for quadrant lines
x_mid = summary["avg_like"].mean()
y_mid = summary["avg_imp"].mean()
x_range = [summary["avg_like"].min() - 0.3, summary["avg_like"].max() + 0.3]
y_range = [summary["avg_imp"].min() - 0.3, summary["avg_imp"].max() + 0.3]

fig_scatter.add_hline(y=y_mid, line_dash="dot", line_color="rgba(255,255,255,0.2)")
fig_scatter.add_vline(x=x_mid, line_dash="dot", line_color="rgba(255,255,255,0.2)")

quadrants = [
    (x_range[1], y_range[1], "Loved & Important", "bottom left"),
    (x_range[0], y_range[1], "Tough but Important", "bottom right"),
    (x_range[1], y_range[0], "Loved but Fluffy", "top left"),
    (x_range[0], y_range[0], "Skip It", "top right"),
]
for qx, qy, label, anchor in quadrants:
    fig_scatter.add_annotation(
        x=qx, y=qy, text=label, showarrow=False,
        font=dict(size=11, color=COLORS["text_muted"]),
        xanchor=anchor.split()[1], yanchor=anchor.split()[0],
    )

fig_scatter.update_layout(xaxis_title="Avg Likeability", yaxis_title="Avg Importance")
st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# 3. Rating Trends Over Time
# ---------------------------------------------------------------------------
st.subheader("Rating Trends Over Time")

use_rolling = st.toggle("3-book rolling average", value=False)
trends = rating_trends()

if use_rolling:
    y_cols = ["rolling_like_3", "rolling_imp_3"]
    names = ["Likeability (3-book avg)", "Importance (3-book avg)"]
    dash_cols = []
else:
    y_cols = ["avg_like", "avg_imp"]
    names = ["Avg Likeability", "Avg Importance"]
    dash_cols = []

fig_trends = charts.line_chart(
    trends, x="Date", y_cols=y_cols, names=names,
    title="Group Avg Ratings Over Time", dash_cols=dash_cols,
)
st.plotly_chart(fig_trends, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# 4. Distribution -- Violin Plot
# ---------------------------------------------------------------------------
st.subheader("Likeability Distribution")

fig_violin = charts.violin_plot(
    ratings, y="Likeability", title="Distribution of All Individual Likeability Ratings",
)
st.plotly_chart(fig_violin, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# 5. THE HEATMAP -- Members x Books, colored by Likeability
# ---------------------------------------------------------------------------
st.subheader("The Heatmap")
st.caption("Members (rows) x Books (columns), colored by Likeability. Gray cells = member did not rate.")

matrix = get_member_book_matrix("Likeability")

# Build z-values; NaN will be handled via a custom colorscale
z_values = matrix.values.tolist()
book_labels = matrix.columns.tolist()
member_labels = matrix.index.tolist()

# Create custom text for hover -- show value or "Absent"
hover_text = []
for row in matrix.values:
    hover_row = []
    for val in row:
        hover_row.append(f"{val:.1f}" if not np.isnan(val) else "Absent")
    hover_text.append(hover_row)

import plotly.graph_objects as go

fig_heat = go.Figure(data=go.Heatmap(
    z=matrix.values,
    x=book_labels,
    y=member_labels,
    colorscale=[
        [0, "#E63946"],
        [0.25, "#F4A261"],
        [0.5, "#E9C46A"],
        [0.75, "#2A9D8F"],
        [1, "#2A9D8F"],
    ],
    zmin=1, zmax=5,
    hoverongaps=False,
    xgap=2, ygap=2,
    text=hover_text,
    hovertemplate="Book: %{x}<br>Member: %{y}<br>Rating: %{text}<extra></extra>",
))

# Overlay gray rectangles for NaN cells
for i, member in enumerate(member_labels):
    for j, book in enumerate(book_labels):
        if np.isnan(matrix.values[i, j]):
            fig_heat.add_shape(
                type="rect",
                x0=j - 0.5, x1=j + 0.5,
                y0=i - 0.5, y1=i + 0.5,
                fillcolor="#2A2A3E",
                line=dict(width=0),
                layer="above",
            )

fig_heat.update_layout(
    title="Member x Book Likeability Heatmap",
    xaxis=dict(tickangle=45, dtick=1),
    height=400,
)
from utils.theme import apply_plotly_theme
apply_plotly_theme(fig_heat)
st.plotly_chart(fig_heat, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# 6. Correlation Matrix -- Pairwise Member Taste Similarity
# ---------------------------------------------------------------------------
st.subheader("Taste Similarity (Member Correlation)")

corr = taste_similarity_matrix()
fig_corr = charts.correlation_heatmap(corr, title="Pairwise Member Taste Correlation")
st.plotly_chart(fig_corr, use_container_width=True)
