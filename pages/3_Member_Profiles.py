"""Member Profiles — individual deep-dives and head-to-head comparison."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from utils.data_loader import (
    MEMBERS,
    get_ratings_long,
    get_book_summary,
    load_raw_data,
    get_enriched_books,
)
from utils.calculations import (
    member_stats,
    agreement_score,
    pairwise_correlation,
    member_deviation_per_book,
)
from utils.charts import (
    radar_chart,
    multi_radar,
    histogram,
    apply_plotly_theme,
)
from utils.theme import (
    COLORS,
    MEMBER_COLORS,
    page_header,
    metric_card_css,
    stat_card,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.markdown(page_header("Member Profiles", "Deep-dive into individual reading tastes"), unsafe_allow_html=True)
st.markdown(metric_card_css(), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
raw = load_raw_data()
ratings = get_ratings_long()
summary = get_book_summary()
stats = member_stats()
agree = agreement_score()
enrichment = get_enriched_books()

# ---------------------------------------------------------------------------
# Mode toggle & member selector
# ---------------------------------------------------------------------------
compare_mode = st.toggle("Compare Mode")

if compare_mode:
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        member_a = st.selectbox("Member A", MEMBERS, index=0)
    with col_sel2:
        member_b = st.selectbox("Member B", MEMBERS, index=1)
    selected_members = [member_a, member_b]
else:
    member_a = st.selectbox("Select Member", MEMBERS, index=0)
    selected_members = [member_a]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _member_color(name: str) -> str:
    return MEMBER_COLORS.get(name, COLORS["primary"])


def _genre_diversity(member: str) -> float:
    """Count distinct genres across books the member rated (0-5 scale)."""
    member_books = ratings[ratings["Member"] == member]["Book"].unique()
    genres = set()
    for book in member_books:
        info = enrichment.get(book, {})
        for g in info.get("genres", []):
            genres.add(g)
    # Scale: cap at 20 genres -> 5
    return min(len(genres) / 4.0, 5.0)


def _taste_profile(member: str) -> list[float]:
    """Return 6-dimension taste profile scaled 0-5."""
    row = stats[stats["Member"] == member]
    if row.empty:
        return [0] * 6
    row = row.iloc[0]
    agree_row = agree[agree["Member"] == member]
    avg_dev = agree_row.iloc[0]["Avg Deviation"] if not agree_row.empty else 1.0

    avg_like = float(row["Avg Likeability Given"])  # already 0-5ish
    avg_imp = float(row["Avg Importance Given"])
    consistency = max(0, 5 - float(row["Std Likeability"]))  # inverse std
    agreement = max(0, 5 - avg_dev * 3)  # inverse deviation scaled
    attendance = float(row["Attendance Rate"]) * 5
    genre_div = _genre_diversity(member)

    return [
        round(avg_like, 2),
        round(avg_imp, 2),
        round(consistency, 2),
        round(agreement, 2),
        round(attendance, 2),
        round(genre_div, 2),
    ]


RADAR_CATEGORIES = [
    "Avg Likeability",
    "Avg Importance",
    "Consistency",
    "Agreement",
    "Attendance",
    "Genre Diversity",
]


def _member_card(member: str):
    """Render metric cards for a single member."""
    row = stats[stats["Member"] == member]
    if row.empty:
        st.warning(f"No data for {member}")
        return
    row = row.iloc[0]
    books_proposed = int(raw[raw["Proposer"] == member].shape[0])
    first_book_date = ratings[ratings["Member"] == member]["Date"].min()
    first_str = first_book_date.strftime("%b %Y") if pd.notna(first_book_date) else "N/A"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Books Proposed", books_proposed)
    c2.metric("Books Rated", int(row["Books Rated"]))
    c3.metric("Attendance", f"{row['Attendance Rate']:.0%}")
    c4.metric("First Rating", first_str)


def _rating_history_fig(members: list[str]):
    """Line chart of likeability over time with group avg."""
    book_avgs = ratings.groupby(["Book", "Date"]).agg(
        group_avg=("Likeability", "mean")
    ).reset_index().sort_values("Date")

    fig = go.Figure()
    # Group average dashed
    fig.add_trace(go.Scatter(
        x=book_avgs["Date"], y=book_avgs["group_avg"],
        mode="lines",
        name="Group Avg",
        line=dict(color=COLORS["text_muted"], dash="dash", width=2),
    ))
    for m in members:
        mr = ratings[ratings["Member"] == m].sort_values("Date")
        fig.add_trace(go.Scatter(
            x=mr["Date"], y=mr["Likeability"],
            mode="lines+markers",
            name=m,
            line=dict(color=_member_color(m)),
            marker=dict(size=6),
        ))
    fig.update_layout(
        title="Rating History (Likeability)",
        xaxis_title="Date",
        yaxis_title="Likeability",
        yaxis=dict(range=[0, 5.5]),
    )
    apply_plotly_theme(fig)
    return fig


def _deviation_fig(members: list[str]):
    """Bar chart of per-book deviation from group mean."""
    dev = member_deviation_per_book()
    fig = go.Figure()
    for m in members:
        md = dev[dev["Member"] == m].sort_values("Date")
        fig.add_trace(go.Bar(
            x=md["Book"], y=md["deviation"],
            name=m,
            marker_color=_member_color(m),
        ))
    fig.update_layout(
        title="Harsh or Generous? (Deviation from Group Mean)",
        xaxis_title="Book",
        yaxis_title="Deviation",
        barmode="group",
    )
    apply_plotly_theme(fig)
    return fig


def _proposed_books_table(member: str) -> pd.DataFrame:
    """Table of books proposed by this member with group avg ratings."""
    proposed = summary[summary["Proposer"] == member][
        ["Book", "Date", "avg_like", "avg_imp", "num_raters"]
    ].copy()
    proposed.columns = ["Book", "Date", "Avg Likeability", "Avg Importance", "Raters"]
    proposed["Date"] = proposed["Date"].dt.strftime("%Y-%m-%d")
    return proposed.sort_values("Date").reset_index(drop=True)


def _taste_alignment(member: str) -> pd.DataFrame:
    """Pairwise correlations for this member, ranked."""
    pw = pairwise_correlation()
    rows = pw[(pw["Member 1"] == member) | (pw["Member 2"] == member)].copy()
    rows["Other"] = rows.apply(
        lambda r: r["Member 2"] if r["Member 1"] == member else r["Member 1"], axis=1
    )
    return rows[["Other", "Correlation", "Shared Books"]].sort_values(
        "Correlation", ascending=False
    ).reset_index(drop=True)


def _head_to_head_table(m1: str, m2: str) -> pd.DataFrame:
    """Table comparing two members on shared books."""
    r1 = ratings[ratings["Member"] == m1][["Book", "Date", "Likeability"]].rename(
        columns={"Likeability": f"{m1} Rating"}
    )
    r2 = ratings[ratings["Member"] == m2][["Book", "Likeability"]].rename(
        columns={"Likeability": f"{m2} Rating"}
    )
    merged = r1.merge(r2, on="Book").sort_values("Date")
    merged["Diff"] = merged[f"{m1} Rating"] - merged[f"{m2} Rating"]
    merged["Date"] = merged["Date"].dt.strftime("%Y-%m-%d")
    return merged.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

if compare_mode:
    # --- Compare Mode ---
    st.subheader(f"{member_a} vs {member_b}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"### <span style='color:{_member_color(member_a)}'>{member_a}</span>",
            unsafe_allow_html=True,
        )
        _member_card(member_a)
    with col2:
        st.markdown(
            f"### <span style='color:{_member_color(member_b)}'>{member_b}</span>",
            unsafe_allow_html=True,
        )
        _member_card(member_b)

    # Overlaid radar
    st.subheader("Taste Profile")
    series = {
        member_a: _taste_profile(member_a),
        member_b: _taste_profile(member_b),
    }
    st.plotly_chart(multi_radar(RADAR_CATEGORIES, series, title="Taste Profile Comparison"), use_container_width=True)

    # Overlaid rating history
    st.subheader("Rating History")
    st.plotly_chart(_rating_history_fig(selected_members), use_container_width=True)

    # Rating distributions side by side
    st.subheader("Rating Distribution")
    dc1, dc2 = st.columns(2)
    with dc1:
        m_data = ratings[ratings["Member"] == member_a]
        st.plotly_chart(histogram(m_data, "Likeability", title=f"{member_a}", nbins=10), use_container_width=True)
    with dc2:
        m_data = ratings[ratings["Member"] == member_b]
        st.plotly_chart(histogram(m_data, "Likeability", title=f"{member_b}", nbins=10), use_container_width=True)

    # Harsh or generous
    st.subheader("Harsh or Generous?")
    st.plotly_chart(_deviation_fig(selected_members), use_container_width=True)

    # Head to head table
    st.subheader("Head-to-Head")
    h2h = _head_to_head_table(member_a, member_b)
    if not h2h.empty:
        avg_diff = h2h["Diff"].mean()
        label = "higher" if avg_diff > 0 else "lower"
        st.markdown(
            stat_card(
                "Average Rating Difference",
                f"{member_a} rates {abs(avg_diff):.2f} pts {label} than {member_b}",
            ),
            unsafe_allow_html=True,
        )
        st.dataframe(h2h, use_container_width=True, hide_index=True)
    else:
        st.info("No shared books to compare.")

    # Taste alignment side by side
    st.subheader("Taste Alignment")
    ta1, ta2 = st.columns(2)
    with ta1:
        st.markdown(f"**{member_a}**")
        st.dataframe(_taste_alignment(member_a), use_container_width=True, hide_index=True)
    with ta2:
        st.markdown(f"**{member_b}**")
        st.dataframe(_taste_alignment(member_b), use_container_width=True, hide_index=True)

else:
    # --- Single Member Mode ---
    st.markdown(
        f"### <span style='color:{_member_color(member_a)}'>{member_a}</span>",
        unsafe_allow_html=True,
    )
    _member_card(member_a)

    # Taste profile radar
    st.subheader("Taste Profile")
    profile = _taste_profile(member_a)
    fig_radar = radar_chart(RADAR_CATEGORIES, profile, name=member_a)
    fig_radar.update_traces(
        line=dict(color=_member_color(member_a)),
        fillcolor=f"rgba({int(_member_color(member_a)[1:3],16)},{int(_member_color(member_a)[3:5],16)},{int(_member_color(member_a)[5:7],16)},0.3)",
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Rating history
    st.subheader("Rating History")
    st.plotly_chart(_rating_history_fig(selected_members), use_container_width=True)

    # Rating distribution
    st.subheader("Rating Distribution")
    m_data = ratings[ratings["Member"] == member_a]
    st.plotly_chart(histogram(m_data, "Likeability", title=f"{member_a} — Likeability Scores", nbins=10), use_container_width=True)

    # Harsh or generous
    st.subheader("Harsh or Generous?")
    agree_row = agree[agree["Member"] == member_a]
    if not agree_row.empty:
        dev_val = agree_row.iloc[0]["Avg Deviation"]
        dev_data = member_deviation_per_book()
        member_dev = dev_data[dev_data["Member"] == member_a]
        avg_signed = member_dev["deviation"].mean()
        label = "generous" if avg_signed > 0 else "harsh"
        st.markdown(
            stat_card(
                "Average Signed Deviation",
                f"{avg_signed:+.2f} ({label} rater)",
                color=COLORS["success"] if avg_signed > 0 else COLORS["danger"],
            ),
            unsafe_allow_html=True,
        )
    st.plotly_chart(_deviation_fig(selected_members), use_container_width=True)

    # Proposed books
    st.subheader("Their Proposed Books")
    proposed = _proposed_books_table(member_a)
    if proposed.empty:
        st.info(f"{member_a} hasn't proposed any books yet.")
    else:
        st.dataframe(proposed, use_container_width=True, hide_index=True)

    # Taste alignment
    st.subheader("Taste Alignment")
    alignment = _taste_alignment(member_a)
    if alignment.empty:
        st.info("Not enough shared books for correlation.")
    else:
        st.dataframe(alignment, use_container_width=True, hide_index=True)
