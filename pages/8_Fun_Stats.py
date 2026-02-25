"""Fun Stats page — quirky trivia and deep cuts from DBC data."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import (
    load_raw_data,
    get_ratings_long,
    get_book_summary,
    get_enriched_books,
    MEMBERS,
)
from utils.calculations import (
    member_stats,
    proposer_bias,
    genre_distribution,
    seasonal_ratings,
    cosine_similarity_books,
    taste_similarity_matrix,
    proposer_performance,
)
from utils.theme import (
    COLORS,
    MEMBER_COLORS,
    metric_card_css,
    page_header,
    stat_card,
    award_card,
)
from utils import charts

st.set_page_config(page_title="DBC - Fun Stats", page_icon="🍷", layout="wide")

# -- Header ------------------------------------------------------------------
st.markdown(
    page_header("Fun Stats", "Quirky Trivia & Deep Cuts"),
    unsafe_allow_html=True,
)
st.markdown(metric_card_css(), unsafe_allow_html=True)

# -- Load data ----------------------------------------------------------------
ratings = get_ratings_long()
summary = get_book_summary()
enrichment = get_enriched_books()

# =============================================================================
# 1. The Ryan Scale
# =============================================================================
st.subheader("The Ryan Scale")
st.caption(
    "Ryan uses fractional ratings like 2.3333 and 3.7 while everyone else "
    "sticks to whole numbers. Here's how his precision compares."
)

ryan_ratings = ratings[ratings["Member"] == "Ryan"]["Likeability"]
others_ratings = ratings[ratings["Member"] != "Ryan"]["Likeability"]

col_ryan1, col_ryan2 = st.columns(2)

with col_ryan1:
    fig_ryan = px.histogram(
        ryan_ratings,
        nbins=20,
        title="Ryan's Ratings Distribution",
        labels={"value": "Likeability", "count": "Count"},
    )
    fig_ryan.update_traces(marker_color=MEMBER_COLORS["Ryan"], marker_line_width=1,
                           marker_line_color=COLORS["bg_dark"])
    charts.apply_plotly_theme(fig_ryan)
    fig_ryan.update_layout(showlegend=False, xaxis_range=[-1, 5.5])
    st.plotly_chart(fig_ryan, use_container_width=True)

with col_ryan2:
    fig_others = px.histogram(
        others_ratings,
        nbins=12,
        title="Everyone Else's Ratings Distribution",
        labels={"value": "Likeability", "count": "Count"},
    )
    fig_others.update_traces(marker_color=COLORS["primary"], marker_line_width=1,
                             marker_line_color=COLORS["bg_dark"])
    charts.apply_plotly_theme(fig_others)
    fig_others.update_layout(showlegend=False, xaxis_range=[-1, 5.5])
    st.plotly_chart(fig_others, use_container_width=True)

# Precision stats
ryan_frac = ryan_ratings.apply(lambda x: x != int(x)).mean() * 100
others_frac = others_ratings.apply(lambda x: x != int(x)).mean() * 100

c1, c2 = st.columns(2)
c1.markdown(
    stat_card("Ryan's Fractional Ratings", f"{ryan_frac:.0f}%", color=MEMBER_COLORS["Ryan"]),
    unsafe_allow_html=True,
)
c2.markdown(
    stat_card("Everyone Else's Fractional Ratings", f"{others_frac:.0f}%", color=COLORS["primary"]),
    unsafe_allow_html=True,
)

st.divider()

# =============================================================================
# 2. The Project Hail Mary Incident
# =============================================================================
st.subheader("The Project Hail Mary Incident")

# Find the negative rating
neg = ratings[ratings["Likeability"] < 0]
if not neg.empty:
    row = neg.iloc[0]
    st.markdown(
        award_card(
            "🚨",
            "Only Negative Rating in Club History",
            f"{row['Member']} gave {row['Book']}",
            f"Likeability: {row['Likeability']} — yes, that's a negative number.",
        ),
        unsafe_allow_html=True,
    )
else:
    st.info("No negative ratings found.")

st.divider()

# =============================================================================
# 3. Proposer's Curse
# =============================================================================
st.subheader("Proposer's Curse")
st.caption("Do proposers rate their own picks higher than the group average?")

bias_df = proposer_bias()
if not bias_df.empty:
    fig_bias = charts.grouped_bar(
        bias_df,
        x="Member",
        y_cols=["own_rating", "group_avg"],
        names=["Proposer's Own Rating", "Group Average"],
        title="Proposer's Rating vs Group Average for Their Picks",
    )
    fig_bias.update_layout(yaxis_range=[0, 5])
    st.plotly_chart(fig_bias, use_container_width=True)

    # Show bias summary
    cols_bias = st.columns(len(bias_df))
    for i, (_, r) in enumerate(bias_df.iterrows()):
        sign = "+" if r["bias"] >= 0 else ""
        cols_bias[i].markdown(
            stat_card(r["Member"], f"{sign}{r['bias']:.2f} bias"),
            unsafe_allow_html=True,
        )

st.divider()

# =============================================================================
# 4. Genre Roulette
# =============================================================================
st.subheader("Genre Roulette")
st.caption("What genres has the club been reading?")

genre_df = genre_distribution()
if not genre_df.empty:
    fig_genre = charts.donut_chart(
        genre_df.head(12),
        values="Count",
        names="Genre",
        title="Top Genres Read",
    )
    st.plotly_chart(fig_genre, use_container_width=True)
else:
    st.info("No genre data available in enrichment.")

st.divider()

# =============================================================================
# 5. Page Turner Index
# =============================================================================
st.subheader("Page Turner Index")
st.caption("Total estimated pages consumed by the club.")

total_pages = 0
books_with_pages = 0
for book_name, book_data in enrichment.items():
    pages = book_data.get("pages")
    if pages:
        book_summary_row = summary[summary["Book"] == book_name]
        if not book_summary_row.empty:
            num_raters = book_summary_row["num_raters"].values[0]
            total_pages += pages * num_raters
            books_with_pages += 1

c1, c2 = st.columns(2)
c1.markdown(
    stat_card("Total Pages Read (Club-wide)", f"{total_pages:,}", color=COLORS["secondary"]),
    unsafe_allow_html=True,
)
c2.markdown(
    stat_card("Books with Page Data", f"{books_with_pages}", color=COLORS["accent"]),
    unsafe_allow_html=True,
)

st.divider()

# =============================================================================
# 6. Seasonal Tastes
# =============================================================================
st.subheader("Seasonal Tastes")
st.caption("Do certain months produce better reads?")

seasonal_df = seasonal_ratings()
if not seasonal_df.empty:
    fig_season = px.bar(
        seasonal_df,
        x="Month Name",
        y="avg_like",
        title="Average Rating by Month",
        text=seasonal_df["avg_like"].round(2),
        hover_data={"count": True},
    )
    fig_season.update_traces(
        marker_color=COLORS["primary"],
        textposition="outside",
        marker_line_width=1,
        marker_line_color=COLORS["bg_dark"],
    )
    charts.apply_plotly_theme(fig_season)
    fig_season.update_layout(yaxis_range=[0, 5], xaxis_title="Month", yaxis_title="Avg Likeability")
    st.plotly_chart(fig_season, use_container_width=True)

st.divider()

# =============================================================================
# 7. "If You Liked X..."
# =============================================================================
st.subheader('"If You Liked X..."')
st.caption("Most similar book pairs based on rating patterns (cosine similarity).")

sim_df = cosine_similarity_books()
if not sim_df.empty:
    top_pairs = sim_df.head(5)
    for _, pair in top_pairs.iterrows():
        c1, c2, c3 = st.columns([3, 1, 3])
        c1.markdown(
            stat_card("Book", pair["Book 1"], color=COLORS["success"]),
            unsafe_allow_html=True,
        )
        c2.markdown(
            f"""<div style="text-align:center; padding-top:20px; color:{COLORS['secondary']};
                font-family:Georgia,serif; font-size:1.2rem;">
                {pair['Similarity']:.3f}
            </div>""",
            unsafe_allow_html=True,
        )
        c3.markdown(
            stat_card("Book", pair["Book 2"], color=COLORS["success"]),
            unsafe_allow_html=True,
        )

st.divider()

# =============================================================================
# 8. Taste Twins Matrix
# =============================================================================
st.subheader("Taste Twins Matrix")
st.caption("Correlation heatmap showing which members have the most similar taste.")

corr_matrix = taste_similarity_matrix()
fig_corr = charts.correlation_heatmap(corr_matrix, title="Member Taste Similarity")
st.plotly_chart(fig_corr, use_container_width=True)

st.divider()

# =============================================================================
# 9. Attendance Trophy
# =============================================================================
st.subheader("Attendance Trophy")
st.caption("Who has rated the most books?")

mstats = member_stats()
mstats_sorted = mstats.sort_values("Books Rated", ascending=True)

fig_attend = px.bar(
    mstats_sorted,
    x="Books Rated",
    y="Member",
    orientation="h",
    title="Books Rated per Member",
    color="Member",
    color_discrete_map=MEMBER_COLORS,
    text="Books Rated",
)
fig_attend.update_traces(textposition="outside")
charts.apply_plotly_theme(fig_attend)
fig_attend.update_layout(showlegend=False)
st.plotly_chart(fig_attend, use_container_width=True)

st.divider()

# =============================================================================
# 10. DBC School GPA
# =============================================================================
st.subheader("DBC School GPA")
st.caption(
    "Converting average likeability to GPA: 5=A (4.0), 4=B (3.0), 3=C (2.0), "
    "2=D (1.0), 1=F (0.0)."
)


def like_to_gpa(like: float) -> float:
    """Convert likeability (1-5) to GPA (0-4)."""
    return max(0.0, like - 1.0)


perf = proposer_performance()
if not perf.empty:
    perf["GPA"] = perf["avg_like"].apply(like_to_gpa).round(2)

    def gpa_letter(gpa: float) -> str:
        if gpa >= 3.7:
            return "A"
        if gpa >= 3.0:
            return "B+"
        if gpa >= 2.7:
            return "B"
        if gpa >= 2.0:
            return "C+"
        if gpa >= 1.7:
            return "C"
        if gpa >= 1.0:
            return "D"
        return "F"

    perf["Letter"] = perf["GPA"].apply(gpa_letter)
    perf_sorted = perf.sort_values("GPA", ascending=False)

    cols_gpa = st.columns(len(perf_sorted))
    for i, (_, r) in enumerate(perf_sorted.iterrows()):
        cols_gpa[i].markdown(
            award_card(
                "🎓",
                r["Proposer"],
                f"{r['Letter']} ({r['GPA']:.2f})",
                f"Avg Likeability: {r['avg_like']:.2f} across {r['books_proposed']} books",
            ),
            unsafe_allow_html=True,
        )

st.divider()

# =============================================================================
# 11. Prediction Corner — Best Genres
# =============================================================================
st.subheader("Prediction Corner")
st.caption("Which genres should the club read more of? Average rating by genre.")

# Build genre-rating mapping from enrichment + summary
genre_ratings: dict[str, list[float]] = {}
for book_name, book_data in enrichment.items():
    genres = book_data.get("genres", [])
    book_row = summary[summary["Book"] == book_name]
    if book_row.empty or not genres:
        continue
    avg = book_row["avg_like"].values[0]
    for g in genres:
        genre_ratings.setdefault(g, []).append(avg)

if genre_ratings:
    genre_avg_df = pd.DataFrame([
        {"Genre": g, "Avg Rating": np.mean(vals), "Books": len(vals)}
        for g, vals in genre_ratings.items()
    ]).sort_values("Avg Rating", ascending=False)

    fig_genre_rec = px.bar(
        genre_avg_df.head(15),
        x="Genre",
        y="Avg Rating",
        title="Average Club Rating by Genre",
        text=genre_avg_df.head(15)["Avg Rating"].round(2),
        hover_data={"Books": True},
        color="Avg Rating",
        color_continuous_scale=["#E63946", "#E9C46A", "#2A9D8F"],
    )
    fig_genre_rec.update_traces(textposition="outside")
    charts.apply_plotly_theme(fig_genre_rec)
    fig_genre_rec.update_layout(yaxis_range=[0, 5], xaxis_tickangle=-45)
    st.plotly_chart(fig_genre_rec, use_container_width=True)
else:
    st.info("No genre enrichment data available.")
