"""Group Dynamics — Agreement, Controversy & Hot Takes."""

import math

import numpy as np
import streamlit as st

from utils.theme import (
    COLORS,
    MEMBER_COLORS,
    page_header,
    stat_card,
    award_card,
    metric_card_css,
    apply_plotly_theme,
)
from utils.calculations import (
    book_controversy,
    contrarian_index,
    hivemind_index,
    hot_takes,
    pairwise_correlation,
    attendance_by_book,
)
from utils.data_loader import MEMBERS
from utils import charts

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.markdown(metric_card_css(), unsafe_allow_html=True)
st.markdown(
    page_header("Group Dynamics", "Agreement, Controversy & Hot Takes"),
    unsafe_allow_html=True,
)

# ===================================================================
# 1. Consensus vs Controversy
# ===================================================================
st.markdown("---")
st.subheader("Consensus vs Controversy")
st.caption("Books ranked by rating standard deviation — green means agreement, red means war.")

controversy = book_controversy()

# Build a green-to-red color scale based on std_like
std_min = controversy["std_like"].min()
std_max = controversy["std_like"].max()


def _std_color(val):
    """Map std dev value to green->red hex color."""
    if std_max == std_min:
        return COLORS["success"]
    t = (val - std_min) / (std_max - std_min)
    # Green (#2A9D8F) -> Yellow (#E9C46A) -> Red (#E63946)
    if t < 0.5:
        t2 = t / 0.5
        r = int(0x2A + (0xE9 - 0x2A) * t2)
        g = int(0x9D + (0xC4 - 0x9D) * t2)
        b = int(0x8F + (0x6A - 0x8F) * t2)
    else:
        t2 = (t - 0.5) / 0.5
        r = int(0xE9 + (0xE6 - 0xE9) * t2)
        g = int(0xC4 + (0x39 - 0xC4) * t2)
        b = int(0x6A + (0x46 - 0x6A) * t2)
    return f"#{r:02X}{g:02X}{b:02X}"


controversy_sorted = controversy.sort_values("std_like", ascending=True)
bar_colors = [_std_color(v) for v in controversy_sorted["std_like"]]

import plotly.graph_objects as go

fig_controversy = go.Figure(
    go.Bar(
        y=controversy_sorted["Book"],
        x=controversy_sorted["std_like"],
        orientation="h",
        marker_color=bar_colors,
        hovertemplate="<b>%{y}</b><br>Std Dev: %{x:.2f}<extra></extra>",
    )
)
fig_controversy.update_layout(
    yaxis=dict(autorange="reversed"),
    xaxis_title="Rating Std Dev",
    height=max(400, len(controversy_sorted) * 28),
)
apply_plotly_theme(fig_controversy)
st.plotly_chart(fig_controversy, use_container_width=True)

# ===================================================================
# 2. Contrarian Index
# ===================================================================
st.markdown("---")
st.subheader("Contrarian Index")
st.caption("How often each member deviates more than 1 point from the group average.")

contrarian = contrarian_index()
fig_contrarian = charts.member_bar(
    contrarian, x="Member", y="contrarian_pct", member_col="Member",
    title="",
)
fig_contrarian.update_layout(
    yaxis_title="% of Ratings > 1pt from Avg",
    yaxis_tickformat=".0%",
    showlegend=False,
)
st.plotly_chart(fig_contrarian, use_container_width=True)

top_contrarian = contrarian.iloc[0]
st.markdown(
    award_card(
        "🤠", "Biggest Contrarian",
        top_contrarian["Member"],
        f"{top_contrarian['contrarian_pct']:.0%} of ratings deviate > 1 pt ({int(top_contrarian['contrarian_count'])} times)",
    ),
    unsafe_allow_html=True,
)

# ===================================================================
# 3. Hivemind Index
# ===================================================================
st.markdown("---")
st.subheader("Hivemind Index")
st.caption("Who tracks the group average closest — lower average deviation = more hivemind.")

hive = hivemind_index()
fig_hive = charts.member_bar(
    hive, x="Member", y="Avg Deviation", member_col="Member",
    title="",
)
fig_hive.update_layout(yaxis_title="Avg Deviation from Group Mean", showlegend=False)
st.plotly_chart(fig_hive, use_container_width=True)

top_hive = hive.iloc[0]
st.markdown(
    award_card(
        "🐝", "Hivemind Champion",
        top_hive["Member"],
        f"Average deviation of only {top_hive['Avg Deviation']:.2f} points",
    ),
    unsafe_allow_html=True,
)

# ===================================================================
# 4. Hot Takes Wall
# ===================================================================
st.markdown("---")
st.subheader("Hot Takes Wall")
st.caption("The 10 biggest single-rating deviations from the group average.")

takes = hot_takes(threshold=0.0)  # Get all, then take top 10
takes_top = takes.head(10)

for _, row in takes_top.iterrows():
    direction = "above" if row["deviation"] > 0 else "below"
    arrow = "⬆️" if row["deviation"] > 0 else "⬇️"
    color = MEMBER_COLORS.get(row["Member"], COLORS["secondary"])
    st.markdown(
        f"""
        <div style="background: {COLORS['bg_card']}; border-left: 4px solid {color};
                    border-radius: 8px; padding: 14px 20px; margin-bottom: 10px;
                    display: flex; align-items: center; gap: 16px;">
            <div style="font-size: 1.8rem;">{arrow}</div>
            <div style="flex: 1;">
                <div style="color: {COLORS['text']}; font-family: Georgia, serif; font-weight: bold;">
                    {row['Member']} on <em>{row['Book']}</em>
                </div>
                <div style="color: {COLORS['text_muted']}; font-size: 0.85rem; margin-top: 2px;">
                    Rated <b>{row['Likeability']:.1f}</b> vs group avg <b>{row['book_avg']:.1f}</b>
                    &mdash; {abs(row['deviation']):.1f} pts {direction}
                </div>
            </div>
            <div style="font-family: Georgia, serif; font-size: 1.6rem; font-weight: bold;
                        color: {'#E63946' if row['deviation'] < 0 else '#2A9D8F'};">
                {row['deviation']:+.1f}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ===================================================================
# 5. Agreement Network
# ===================================================================
st.markdown("---")
st.subheader("Agreement Network")
st.caption("Nodes = members, edges = rating correlation. Thicker lines mean more similar taste.")

corr = pairwise_correlation()

# Position nodes in a circle
n = len(MEMBERS)
nodes = []
for i, member in enumerate(MEMBERS):
    angle = 2 * math.pi * i / n - math.pi / 2
    nodes.append({
        "name": member,
        "x": math.cos(angle),
        "y": math.sin(angle),
    })

# Normalize correlation to 0-1 for edge weight
if not corr.empty:
    corr_min = corr["Correlation"].min()
    corr_max = corr["Correlation"].max()
    corr_range = corr_max - corr_min if corr_max != corr_min else 1.0

    edges = []
    for _, row in corr.iterrows():
        weight = (row["Correlation"] - corr_min) / corr_range
        edges.append({
            "source": row["Member 1"],
            "target": row["Member 2"],
            "weight": weight,
        })

    fig_network = charts.network_graph(nodes, edges, title="")
    fig_network.update_layout(height=550)
    st.plotly_chart(fig_network, use_container_width=True)
else:
    st.info("Not enough shared ratings to compute correlations.")

# ===================================================================
# 6. Attendance Patterns
# ===================================================================
st.markdown("---")
st.subheader("Attendance Patterns")
st.caption("Who rated each book — showing participation across the club's history.")

attendance = attendance_by_book()
# Pivot: Book x Member with 1/0 for stacked bar
att_pivot = attendance.pivot_table(index="Book", columns="Member", values="Rated", aggfunc="first")
# Maintain book order
book_order = attendance.drop_duplicates("Book")["Book"].tolist()
att_pivot = att_pivot.loc[[b for b in book_order if b in att_pivot.index]]

fig_attend = go.Figure()
for member in MEMBERS:
    if member in att_pivot.columns:
        fig_attend.add_trace(go.Bar(
            x=att_pivot.index,
            y=att_pivot[member].astype(int),
            name=member,
            marker_color=MEMBER_COLORS.get(member, COLORS["secondary"]),
        ))

fig_attend.update_layout(
    barmode="stack",
    yaxis_title="Raters",
    xaxis_tickangle=-45,
    height=500,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
)
apply_plotly_theme(fig_attend)
st.plotly_chart(fig_attend, use_container_width=True)
