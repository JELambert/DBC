"""Home overview page for the DBC dashboard."""

import random

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_loader import (
    load_raw_data,
    get_book_summary,
    get_enriched_books,
    get_book_enrichment,
    MEMBERS,
)
from utils.theme import COLORS, metric_card_css, page_header, stat_card
from utils import charts

st.set_page_config(page_title="DBC - Home", page_icon="🍷", layout="wide")

# -- Header ------------------------------------------------------------------
st.markdown(page_header("Drunk Book Club", "Dashboard home — a data-driven look at our reading journey"), unsafe_allow_html=True)

# -- Load data ----------------------------------------------------------------
raw = load_raw_data()
summary = get_book_summary()
enrichment = get_enriched_books()

# -- Hero metrics row ---------------------------------------------------------
st.markdown(metric_card_css(), unsafe_allow_html=True)

total_books = len(raw)
active_members = len(MEMBERS)
first_date = raw["Date"].min()
last_date = raw["Date"].max()
months_active = max(1, (last_date.year - first_date.year) * 12 + last_date.month - first_date.month)
avg_club_rating = round(summary["avg_like"].mean(), 2)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Books", total_books)
c2.metric("Active Members", active_members)
c3.metric("Months Active", months_active)
c4.metric("Avg Club Rating", avg_club_rating)

st.divider()

# -- Most Recent Book ---------------------------------------------------------
st.subheader("Most Recent Read")

most_recent = raw.sort_values("Date").iloc[-1]
recent_title = most_recent["Book"]
recent_author = ""
recent_cover = None

book_enrich = get_book_enrichment(recent_title)
if book_enrich:
    recent_author = book_enrich.get("author", "")
    recent_cover = book_enrich.get("cover_url")

# Get ratings for this book from summary
recent_summary = summary[summary["Book"] == recent_title]
recent_avg = round(recent_summary["avg_like"].values[0], 2) if len(recent_summary) > 0 else "N/A"

col_cover, col_info = st.columns([1, 3])

with col_cover:
    if recent_cover:
        st.image(recent_cover, width=160)
    else:
        st.markdown(
            f"""<div style="width:140px;height:200px;background:{COLORS['bg_card']};
            border:1px solid {COLORS['primary']};border-radius:8px;display:flex;
            align-items:center;justify-content:center;color:{COLORS['text_muted']};
            font-family:Georgia,serif;text-align:center;padding:12px;">
            {recent_title}</div>""",
            unsafe_allow_html=True,
        )

with col_info:
    st.markdown(
        f"""<div style="font-family:Georgia,serif;">
        <h3 style="color:{COLORS['secondary']};margin-bottom:4px;">{recent_title}</h3>
        <p style="color:{COLORS['text_muted']};margin-top:0;">
            {f'by {recent_author} — ' if recent_author else ''}Proposed by {most_recent['Proposer']}
            — {most_recent['Date'].strftime('%B %Y')}</p>
        <p style="color:{COLORS['text']};font-size:1.1rem;">Avg Likeability: <b>{recent_avg}</b> / 5</p>
        </div>""",
        unsafe_allow_html=True,
    )

st.divider()

# -- Hall of Fame / Hall of Shame ---------------------------------------------
st.subheader("Hall of Fame & Hall of Shame")
col_fame, col_shame = st.columns(2)

sorted_books = summary.sort_values("avg_like", ascending=False)

with col_fame:
    top5 = sorted_books.head(5).sort_values("avg_like", ascending=True)
    fig_top = charts.horizontal_bar(
        top5, x="avg_like", y="Book", title="Top 5 — Highest Rated",
    )
    fig_top.update_traces(marker_color=COLORS["success"])
    fig_top.update_layout(xaxis_range=[0, 5])
    st.plotly_chart(fig_top, use_container_width=True)

with col_shame:
    bot5 = sorted_books.tail(5).sort_values("avg_like", ascending=True)
    fig_bot = charts.horizontal_bar(
        bot5, x="avg_like", y="Book", title="Bottom 5 — Lowest Rated",
    )
    fig_bot.update_traces(marker_color=COLORS["danger"])
    fig_bot.update_layout(xaxis_range=[0, 5])
    st.plotly_chart(fig_bot, use_container_width=True)

st.divider()

# -- Books per Year -----------------------------------------------------------
col_year, col_proposer = st.columns(2)

with col_year:
    st.subheader("Books per Year")
    books_year = raw.copy()
    books_year["Year"] = books_year["Date"].dt.year
    year_counts = books_year.groupby("Year").size().reset_index(name="Books")
    year_counts["Year"] = year_counts["Year"].astype(str)

    fig_year = px.bar(
        year_counts, x="Year", y="Books", title="Books Read per Year",
        text="Books",
    )
    fig_year.update_traces(marker_color=COLORS["primary"], textposition="outside")
    charts.apply_plotly_theme(fig_year)
    st.plotly_chart(fig_year, use_container_width=True)

# -- Proposer Distribution ----------------------------------------------------
with col_proposer:
    st.subheader("Proposer Distribution")
    proposer_counts = raw.groupby("Proposer").size().reset_index(name="Books Proposed")
    fig_proposer = charts.donut_chart(
        proposer_counts, values="Books Proposed", names="Proposer",
        title="Who Proposed How Many Books?",
    )
    st.plotly_chart(fig_proposer, use_container_width=True)

st.divider()

# -- Random Fun Fact ----------------------------------------------------------
st.subheader("Random Fun Fact")

fun_facts = [
    f"The club has been running for **{months_active} months** and counting.",
    f"**{sorted_books.iloc[0]['Book']}** holds the all-time highest rating at **{sorted_books.iloc[0]['avg_like']:.2f}**.",
    f"**{sorted_books.iloc[-1]['Book']}** is the lowest-rated book at **{sorted_books.iloc[-1]['avg_like']:.2f}**.",
    f"On average, each book gets **{summary['num_raters'].mean():.1f} raters** per session.",
    f"Josh has proposed the most books — a true literary engine.",
    f"The club averages **{total_books / max(1, months_active / 12):.1f} books per year**.",
    f"Prophet Song and The Safekeep both cracked a **4.0+** rating — elite company.",
    f"Ghost Fleet scored a dismal **{summary[summary['Book'] == 'Ghost Fleet']['avg_like'].values[0]:.2f}** — the DBC basement dweller.",
    f"The first book ever discussed was **{raw.sort_values('Date').iloc[0]['Book']}** back in **{raw.sort_values('Date').iloc[0]['Date'].strftime('%B %Y')}**.",
    f"Freedom achieved a remarkable **{summary[summary['Book'] == 'Freedom']['avg_like'].values[0]:.2f}** average rating.",
    f"The club has **{active_members} active members** contributing their hot takes.",
    f"Project Hail Mary ratings ranged wildly — Ryan gave it a **-0.5** (yes, negative).",
]

fact = random.choice(fun_facts)
st.markdown(
    stat_card("DBC Trivia", fact, color=COLORS["secondary"]),
    unsafe_allow_html=True,
)
