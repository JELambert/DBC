"""Leaderboards & Awards page for the DBC dashboard."""

import streamlit as st

from utils.data_loader import get_book_summary
from utils.calculations import (
    book_controversy,
    member_stats,
    proposer_performance,
    agreement_score,
    contrarian_index,
)
from utils.theme import page_header, award_card

st.set_page_config(page_title="DBC - Leaderboards", page_icon="🏆", layout="wide")

st.markdown(page_header("Leaderboards", "Awards & Rankings"), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
summary = get_book_summary()
controversy = book_controversy()
m_stats = member_stats()
prop_perf = proposer_performance()
agree = agreement_score()
contrar = contrarian_index()

# ===================================================================
# BOOK AWARDS
# ===================================================================
st.subheader("Book Awards")

# Most Loved — highest avg likeability
most_loved = summary.sort_values("avg_like", ascending=False).iloc[0]

# Most Important — highest avg importance
most_important = summary.sort_values("avg_imp", ascending=False).iloc[0]

# Best Overall — highest combined (avg_like + avg_imp) / 2
summary["overall"] = (summary["avg_like"] + summary["avg_imp"]) / 2
best_overall = summary.sort_values("overall", ascending=False).iloc[0]

# Most Polarizing — highest std_like
most_polarizing = controversy.iloc[0]  # already sorted desc by std_like

# Most Unanimously Loved — high avg_like + low std_like
summary["unanimous"] = summary["avg_like"] - summary["std_like"]
most_unanimous = summary.sort_values("unanimous", ascending=False).iloc[0]

# Sleeper Hit — highest importance/likeability ratio
summary["sleeper"] = summary["avg_imp"] / summary["avg_like"].replace(0, float("nan"))
sleeper_hit = summary.sort_values("sleeper", ascending=False).iloc[0]

# Guilty Pleasure — highest likeability with lowest importance (like - imp)
summary["guilty"] = summary["avg_like"] - summary["avg_imp"]
guilty_pleasure = summary.sort_values("guilty", ascending=False).iloc[0]

# Ghost Fleet Award — lowest rated book
lowest_rated = summary.sort_values("avg_like", ascending=True).iloc[0]

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(award_card(
        "❤️", "Most Loved", most_loved["Book"],
        f"Avg Likeability: {most_loved['avg_like']:.2f}",
    ), unsafe_allow_html=True)
with col2:
    st.markdown(award_card(
        "📚", "Most Important", most_important["Book"],
        f"Avg Importance: {most_important['avg_imp']:.2f}",
    ), unsafe_allow_html=True)
with col3:
    st.markdown(award_card(
        "🏆", "Best Overall", best_overall["Book"],
        f"Combined Score: {best_overall['overall']:.2f}",
    ), unsafe_allow_html=True)

st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)
with col4:
    st.markdown(award_card(
        "🔥", "Most Polarizing", most_polarizing["Book"],
        f"Std Dev: {most_polarizing['std_like']:.2f}",
    ), unsafe_allow_html=True)
with col5:
    st.markdown(award_card(
        "🤝", "Most Unanimously Loved", most_unanimous["Book"],
        f"Avg {most_unanimous['avg_like']:.2f} | Std {most_unanimous['std_like']:.2f}",
    ), unsafe_allow_html=True)
with col6:
    st.markdown(award_card(
        "💤", "Sleeper Hit", sleeper_hit["Book"],
        f"Importance/Likeability: {sleeper_hit['sleeper']:.2f}",
    ), unsafe_allow_html=True)

st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

col7, col8, col9 = st.columns(3)
with col7:
    st.markdown(award_card(
        "🍬", "Guilty Pleasure", guilty_pleasure["Book"],
        f"Like {guilty_pleasure['avg_like']:.2f} | Imp {guilty_pleasure['avg_imp']:.2f}",
    ), unsafe_allow_html=True)
with col8:
    st.markdown(award_card(
        "👻", "Ghost Fleet Award", lowest_rated["Book"],
        f"Avg Likeability: {lowest_rated['avg_like']:.2f}",
    ), unsafe_allow_html=True)

st.divider()

# ===================================================================
# MEMBER AWARDS
# ===================================================================
st.subheader("Member Awards")

# MVP Proposer — highest avg rating of proposed books
mvp_proposer = prop_perf.iloc[0]  # already sorted desc by avg_like

# The Generous One — highest avg likeability given
generous = m_stats.sort_values("Avg Likeability Given", ascending=False).iloc[0]

# The Critic — lowest avg likeability given
critic = m_stats.sort_values("Avg Likeability Given", ascending=True).iloc[0]

# Iron Liver — most books rated
iron_liver = m_stats.sort_values("Books Rated", ascending=False).iloc[0]

# The Contrarian — highest contrarian percentage
top_contrarian = contrar.iloc[0]  # already sorted desc by contrarian_pct

# The Hivemind — lowest avg deviation
hivemind = agree.iloc[0]  # already sorted asc by Avg Deviation

# Range King — highest range in likeability scores
range_king = m_stats.sort_values("Range Likeability", ascending=False).iloc[0]

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(award_card(
        "🎯", "MVP Proposer", mvp_proposer["Proposer"],
        f"Avg Rating of Picks: {mvp_proposer['avg_like']:.2f}",
    ), unsafe_allow_html=True)
with col2:
    st.markdown(award_card(
        "🌟", "The Generous One", generous["Member"],
        f"Avg Likeability Given: {generous['Avg Likeability Given']:.2f}",
    ), unsafe_allow_html=True)
with col3:
    st.markdown(award_card(
        "🧐", "The Critic", critic["Member"],
        f"Avg Likeability Given: {critic['Avg Likeability Given']:.2f}",
    ), unsafe_allow_html=True)

st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)
with col4:
    st.markdown(award_card(
        "💪", "Iron Liver", iron_liver["Member"],
        f"Books Rated: {int(iron_liver['Books Rated'])}",
    ), unsafe_allow_html=True)
with col5:
    st.markdown(award_card(
        "🤠", "The Contrarian", top_contrarian["Member"],
        f"Contrarian Rate: {top_contrarian['contrarian_pct']:.0%}",
    ), unsafe_allow_html=True)
with col6:
    st.markdown(award_card(
        "🐝", "The Hivemind", hivemind["Member"],
        f"Avg Deviation: {hivemind['Avg Deviation']:.2f}",
    ), unsafe_allow_html=True)

st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

col7, col8, col9 = st.columns(3)
with col7:
    st.markdown(award_card(
        "📏", "Range King", range_king["Member"],
        f"Rating Range: {range_king['Range Likeability']:.1f}",
    ), unsafe_allow_html=True)

st.divider()

# ===================================================================
# YEARLY AWARDS
# ===================================================================
st.subheader("Yearly Awards")

summary["Year"] = summary["Date"].dt.year
years = sorted(summary["Year"].unique())

# Build yearly best books
yearly_awards = []
for year in years:
    year_books = summary[summary["Year"] == year]
    best = year_books.sort_values("avg_like", ascending=False).iloc[0]
    yearly_awards.append((year, best))

cols = st.columns(3)
for i, (year, best) in enumerate(yearly_awards):
    with cols[i % 3]:
        st.markdown(award_card(
            "📅", f"Book of the Year {year}", best["Book"],
            f"Avg Likeability: {best['avg_like']:.2f}",
        ), unsafe_allow_html=True)
