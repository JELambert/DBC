"""Book Explorer -- deep dive into any single book."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.charts import radar_chart, scatter_plot
from utils.data_loader import (
    get_all_books,
    get_book_enrichment,
    get_book_summary,
    get_ratings_long,
    load_raw_data,
)
from utils.theme import (
    COLORS,
    MEMBER_COLORS,
    apply_plotly_theme,
    metric_card_css,
    page_header,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.markdown(metric_card_css(), unsafe_allow_html=True)
st.markdown(page_header("Book Explorer", "Deep-dive into any book the club has read"), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Book selector
# ---------------------------------------------------------------------------
all_books = get_all_books()
selected_book = st.selectbox("Choose a book", all_books, index=len(all_books) - 1)

# ---------------------------------------------------------------------------
# Load data for the selected book
# ---------------------------------------------------------------------------
raw = load_raw_data()
book_row = raw[raw["Book"] == selected_book].iloc[0]
enrichment = get_book_enrichment(selected_book)
ratings = get_ratings_long()
book_ratings = ratings[ratings["Book"] == selected_book]
summary = get_book_summary()
book_summary = summary[summary["Book"] == selected_book]

# ---------------------------------------------------------------------------
# Header section
# ---------------------------------------------------------------------------
col_img, col_info = st.columns([1, 3])

with col_img:
    cover_url = enrichment.get("cover_url", "")
    if cover_url:
        st.image(cover_url, width=200)
    else:
        st.markdown(
            f"""<div style="width:200px;height:300px;background:{COLORS['bg_card']};
            border:1px solid {COLORS['primary']};border-radius:8px;display:flex;
            align-items:center;justify-content:center;color:{COLORS['text_muted']};
            font-family:Georgia,serif;font-size:1.1rem;text-align:center;padding:1rem;">
            {selected_book}</div>""",
            unsafe_allow_html=True,
        )

with col_info:
    author = enrichment.get("author", book_row.get("Author", "Unknown"))
    year = enrichment.get("year_published", "")
    page_count = enrichment.get("page_count", "")

    st.markdown(
        f'<h2 style="font-family:Georgia,serif;color:{COLORS["text"]};margin-bottom:0;">{selected_book}</h2>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="color:{COLORS["text_muted"]};font-size:1rem;margin-top:4px;">'
        f'by <strong style="color:{COLORS["secondary"]}">{author}</strong>'
        f'{f" &middot; {year}" if year else ""}'
        f'{f" &middot; {page_count} pages" if page_count else ""}'
        f"</p>",
        unsafe_allow_html=True,
    )

    # Genre pills
    genres = enrichment.get("genres", [])
    if genres:
        pills_html = " ".join(
            f'<span style="background:{COLORS["accent"]};color:{COLORS["text"]};'
            f'padding:4px 12px;border-radius:20px;font-size:0.8rem;margin-right:6px;'
            f'display:inline-block;margin-bottom:4px;">{g}</span>'
            for g in genres
        )
        st.markdown(pills_html, unsafe_allow_html=True)

    # Proposer badge & discussion date
    proposer = book_row["Proposer"]
    discussion_date = book_row["Date"].strftime("%B %d, %Y")
    p_color = MEMBER_COLORS.get(proposer, COLORS["secondary"])
    st.markdown(
        f'<p style="margin-top:8px;color:{COLORS["text_muted"]};font-size:0.9rem;">'
        f'Proposed by <span style="background:{p_color};color:#fff;padding:3px 10px;'
        f'border-radius:12px;font-size:0.8rem;">{proposer}</span>'
        f" &middot; Discussed {discussion_date}</p>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Plot Summary
# ---------------------------------------------------------------------------
plot_summary = enrichment.get("plot_summary", "")
if plot_summary:
    with st.expander("Plot Summary"):
        st.write(plot_summary)

# ---------------------------------------------------------------------------
# Ratings Breakdown
# ---------------------------------------------------------------------------
st.markdown(f'<h3 style="color:{COLORS["secondary"]};font-family:Georgia,serif;">Ratings Breakdown</h3>', unsafe_allow_html=True)

if not book_ratings.empty:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=book_ratings["Member"],
        y=book_ratings["Likeability"],
        name="Likeability",
        marker_color=[MEMBER_COLORS.get(m, COLORS["primary"]) for m in book_ratings["Member"]],
        opacity=0.9,
    ))
    fig.add_trace(go.Bar(
        x=book_ratings["Member"],
        y=book_ratings["Importance"],
        name="Importance",
        marker_color=[MEMBER_COLORS.get(m, COLORS["primary"]) for m in book_ratings["Member"]],
        opacity=0.5,
    ))
    fig.update_layout(barmode="group", title="Likeability & Importance by Member")
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No individual ratings available for this book.")

# ---------------------------------------------------------------------------
# Radar Chart -- Book Profile
# ---------------------------------------------------------------------------
st.markdown(f'<h3 style="color:{COLORS["secondary"]};font-family:Georgia,serif;">Book Profile</h3>', unsafe_allow_html=True)

if not book_summary.empty:
    bs = book_summary.iloc[0]
    avg_like = bs["avg_like"]
    avg_imp = bs["avg_imp"]

    # Attendance rate scaled to 0-5
    num_raters = bs["num_raters"]
    total_members = len(MEMBER_COLORS)
    attendance_scaled = (num_raters / total_members) * 5

    # Agreement: inverse of std_like, scaled 0-5 (lower std = higher agreement)
    std_like = bs["std_like"]
    agreement = max(0, 5 - std_like * 2.5) if std_like > 0 else 5.0

    # Proposer track record: avg likeability of the proposer's other books
    proposer_books = summary[summary["Proposer"] == proposer]
    if len(proposer_books) > 1:
        other_books = proposer_books[proposer_books["Book"] != selected_book]
        proposer_track = other_books["avg_like"].mean()
    else:
        proposer_track = avg_like  # only book, use own score

    categories = ["Avg Likeability", "Avg Importance", "Attendance", "Agreement", "Proposer Track"]
    values = [
        round(avg_like, 2),
        round(avg_imp, 2),
        round(attendance_scaled, 2),
        round(agreement, 2),
        round(proposer_track, 2),
    ]

    fig = radar_chart(categories, values, name=selected_book)
    fig.update_layout(title="")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# How This Book Compares -- scatter of all books
# ---------------------------------------------------------------------------
st.markdown(f'<h3 style="color:{COLORS["secondary"]};font-family:Georgia,serif;">How This Book Compares</h3>', unsafe_allow_html=True)

if not summary.empty:
    plot_df = summary.copy()
    plot_df["selected"] = plot_df["Book"] == selected_book
    plot_df["marker_size"] = plot_df["selected"].map({True: 18, False: 8})

    fig = go.Figure()

    # Other books
    others = plot_df[~plot_df["selected"]]
    fig.add_trace(go.Scatter(
        x=others["avg_like"],
        y=others["avg_imp"],
        mode="markers",
        marker=dict(size=8, color=COLORS["text_muted"], opacity=0.5),
        text=others["Book"],
        hovertemplate="<b>%{text}</b><br>Likeability: %{x:.2f}<br>Importance: %{y:.2f}<extra></extra>",
        name="Other Books",
    ))

    # Selected book
    sel = plot_df[plot_df["selected"]]
    fig.add_trace(go.Scatter(
        x=sel["avg_like"],
        y=sel["avg_imp"],
        mode="markers+text",
        marker=dict(size=18, color=COLORS["primary"], line=dict(width=2, color=COLORS["secondary"])),
        text=sel["Book"],
        textposition="top center",
        textfont=dict(color=COLORS["secondary"], size=12),
        hovertemplate="<b>%{text}</b><br>Likeability: %{x:.2f}<br>Importance: %{y:.2f}<extra></extra>",
        name=selected_book,
    ))

    fig.update_layout(
        xaxis_title="Avg Likeability",
        yaxis_title="Avg Importance",
        title="All Books: Likeability vs Importance",
    )
    apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Fun Facts & Awards (from enrichment)
# ---------------------------------------------------------------------------
fun_facts = enrichment.get("fun_facts", [])
awards = enrichment.get("awards", [])

if fun_facts or awards:
    st.markdown(f'<h3 style="color:{COLORS["secondary"]};font-family:Georgia,serif;">Fun Facts & Awards</h3>', unsafe_allow_html=True)

    if awards:
        for award in awards:
            st.markdown(
                f'<div style="background:{COLORS["bg_card"]};border-left:4px solid {COLORS["secondary"]};'
                f'border-radius:8px;padding:12px 16px;margin-bottom:8px;">'
                f'<span style="color:{COLORS["secondary"]};">&#9733;</span> '
                f'<span style="color:{COLORS["text"]};">{award}</span></div>',
                unsafe_allow_html=True,
            )

    if fun_facts:
        for fact in fun_facts:
            st.markdown(
                f'<div style="background:{COLORS["bg_card"]};border-left:4px solid {COLORS["accent"]};'
                f'border-radius:8px;padding:12px 16px;margin-bottom:8px;">'
                f'<span style="color:{COLORS["text"]};">{fact}</span></div>',
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------------------
# Themes (from enrichment)
# ---------------------------------------------------------------------------
themes = enrichment.get("themes", [])
if themes:
    st.markdown(f'<h3 style="color:{COLORS["secondary"]};font-family:Georgia,serif;">Themes</h3>', unsafe_allow_html=True)
    theme_colors = [COLORS["primary"], COLORS["accent"], COLORS["success"], COLORS["warning"], COLORS["danger"], "#7B2D8E", "#457B9D"]
    pills = " ".join(
        f'<span style="background:{theme_colors[i % len(theme_colors)]};color:{COLORS["text"]};'
        f'padding:5px 14px;border-radius:20px;font-size:0.85rem;margin-right:6px;'
        f'display:inline-block;margin-bottom:6px;">{t}</span>'
        for i, t in enumerate(themes)
    )
    st.markdown(pills, unsafe_allow_html=True)
