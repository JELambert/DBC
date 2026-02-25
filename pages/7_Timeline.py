"""Timeline page for the DBC dashboard."""

import pandas as pd
import streamlit as st

from utils.data_loader import get_book_summary, load_raw_data
from utils.theme import COLORS, MEMBER_COLORS, metric_card_css, page_header, stat_card
from utils import charts

st.set_page_config(page_title="DBC - Timeline", page_icon="🍷", layout="wide")

# -- Header ------------------------------------------------------------------
st.markdown(
    page_header("Timeline", "Our Reading Journey"),
    unsafe_allow_html=True,
)

# -- Load data ----------------------------------------------------------------
summary = get_book_summary()
raw = load_raw_data()

# =============================================================================
# 1. Interactive Timeline — scatter plot
# =============================================================================
st.subheader("Interactive Timeline")

fig_timeline = charts.timeline_scatter(
    summary,
    x="Date",
    y="avg_like",
    size="num_raters",
    color="Proposer",
    title="Books Over Time",
    color_discrete_map=MEMBER_COLORS,
    hover_data={"Book": True, "avg_like": ":.2f", "num_raters": True, "Proposer": True},
)
fig_timeline.update_layout(
    xaxis_title="Date",
    yaxis_title="Avg Likeability",
    yaxis_range=[0, 5],
)
st.plotly_chart(fig_timeline, use_container_width=True)

st.divider()

# =============================================================================
# 2. Era Cards
# =============================================================================
st.subheader("Eras of the Club")

era_defs = [
    {
        "name": "The Early Days",
        "start": "2023-10-01",
        "end": "2024-01-31",
        "desc": "Founding members, first reads, finding our groove.",
    },
    {
        "name": "The Expansion",
        "start": "2024-02-01",
        "end": "2024-09-30",
        "desc": "Growth period — new members, wider genres.",
    },
    {
        "name": "The Golden Age",
        "start": "2024-10-01",
        "end": "2099-12-31",
        "desc": "Most active era — peak engagement and bold picks.",
    },
]

era_cols = st.columns(3)

for col, era in zip(era_cols, era_defs):
    start = pd.Timestamp(era["start"])
    end = pd.Timestamp(era["end"])
    era_books = summary[(summary["Date"] >= start) & (summary["Date"] <= end)]
    book_count = len(era_books)
    avg_rating = round(era_books["avg_like"].mean(), 2) if book_count > 0 else "N/A"

    if book_count > 0:
        best = era_books.loc[era_books["avg_like"].idxmax()]
        standout = f"{best['Book']} ({best['avg_like']:.2f})"
    else:
        standout = "—"

    # Date range label
    end_label = "present" if era["end"] > "2026-01-01" else pd.Timestamp(era["end"]).strftime("%b %Y")
    date_range = f"{start.strftime('%b %Y')} – {end_label}"

    with col:
        st.markdown(
            f"""<div style="background:{COLORS['bg_card']};border:1px solid {COLORS['primary']};
            border-radius:12px;padding:20px;margin-bottom:12px;
            box-shadow:0 4px 12px rgba(114,47,55,0.15);">
            <h3 style="color:{COLORS['secondary']};font-family:Georgia,serif;margin:0 0 4px 0;">
                {era['name']}</h3>
            <p style="color:{COLORS['text_muted']};font-size:0.85rem;margin:0 0 12px 0;">
                {era['desc']}</p>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown(stat_card("Date Range", date_range), unsafe_allow_html=True)
        st.markdown(stat_card("Books Read", str(book_count)), unsafe_allow_html=True)
        st.markdown(stat_card("Avg Rating", str(avg_rating)), unsafe_allow_html=True)
        st.markdown(stat_card("Standout Book", standout, color=COLORS["secondary"]), unsafe_allow_html=True)

st.divider()

# =============================================================================
# 3. Reading Pace — days between consecutive meetings
# =============================================================================
st.subheader("Reading Pace")

sorted_dates = raw.sort_values("Date")
dates = sorted_dates["Date"].values
books = sorted_dates["Book"].values

pace_rows = []
for i in range(1, len(dates)):
    gap = (pd.Timestamp(dates[i]) - pd.Timestamp(dates[i - 1])).days
    pace_rows.append({"Book": books[i], "Days Since Previous": gap})

pace_df = pd.DataFrame(pace_rows)

fig_pace = charts.horizontal_bar(
    pace_df.sort_values("Days Since Previous", ascending=True),
    x="Days Since Previous",
    y="Book",
    title="Days Between Consecutive Meetings",
)
fig_pace.update_traces(marker_color=COLORS["accent"])
fig_pace.update_layout(height=max(400, len(pace_df) * 28))
st.plotly_chart(fig_pace, use_container_width=True)

avg_gap = round(pace_df["Days Since Previous"].mean(), 1)
max_gap_row = pace_df.loc[pace_df["Days Since Previous"].idxmax()]
min_gap_row = pace_df.loc[pace_df["Days Since Previous"].idxmin()]

p1, p2, p3 = st.columns(3)
p1.markdown(stat_card("Avg Days Between Reads", f"{avg_gap} days"), unsafe_allow_html=True)
p2.markdown(stat_card("Longest Gap", f"{int(max_gap_row['Days Since Previous'])} days — {max_gap_row['Book']}"), unsafe_allow_html=True)
p3.markdown(stat_card("Shortest Gap", f"{int(min_gap_row['Days Since Previous'])} days — {min_gap_row['Book']}"), unsafe_allow_html=True)

st.divider()

# =============================================================================
# 4. Cumulative Stats — area chart
# =============================================================================
st.subheader("Cumulative Stats")

cumulative = summary.sort_values("Date").copy()
cumulative["Cumulative Books"] = range(1, len(cumulative) + 1)
cumulative["Running Avg Rating"] = cumulative["avg_like"].expanding().mean().round(2)

fig_cumul = charts.area_chart(
    cumulative,
    x="Date",
    y_cols=["Cumulative Books", "Running Avg Rating"],
    names=["Cumulative Books Read", "Running Avg Rating"],
    title="Cumulative Books & Running Average Rating Over Time",
)
fig_cumul.update_layout(
    yaxis_title="Count / Rating",
    xaxis_title="Date",
)
st.plotly_chart(fig_cumul, use_container_width=True)
