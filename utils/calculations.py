"""Derived metrics and statistical calculations for DBC dashboard."""

import numpy as np
import pandas as pd
from scipy import stats

from utils.data_loader import (
    get_ratings_long,
    get_book_summary,
    get_member_book_matrix,
    MEMBERS,
)


def member_stats() -> pd.DataFrame:
    """Per-member statistics: avg ratings, std dev, attendance, etc."""
    ratings = get_ratings_long()
    total_books = ratings["Book"].nunique()

    rows = []
    for member in MEMBERS:
        mr = ratings[ratings["Member"] == member]
        if mr.empty:
            continue
        rows.append({
            "Member": member,
            "Books Rated": len(mr),
            "Attendance Rate": len(mr) / total_books,
            "Avg Likeability Given": mr["Likeability"].mean(),
            "Avg Importance Given": mr["Importance"].mean(),
            "Std Likeability": mr["Likeability"].std(),
            "Std Importance": mr["Importance"].std(),
            "Min Likeability": mr["Likeability"].min(),
            "Max Likeability": mr["Likeability"].max(),
            "Range Likeability": mr["Likeability"].max() - mr["Likeability"].min(),
        })
    return pd.DataFrame(rows)


def agreement_score() -> pd.DataFrame:
    """Mean absolute deviation from group average per member.

    Lower = more agreeable with the group.
    """
    ratings = get_ratings_long()
    book_avgs = ratings.groupby("Book")["Likeability"].mean().rename("book_avg")
    merged = ratings.merge(book_avgs, on="Book")
    merged["deviation"] = (merged["Likeability"] - merged["book_avg"]).abs()

    result = merged.groupby("Member")["deviation"].mean().reset_index()
    result.columns = ["Member", "Avg Deviation"]
    return result.sort_values("Avg Deviation")


def pairwise_correlation() -> pd.DataFrame:
    """Pearson correlation between each member pair on shared books."""
    matrix = get_member_book_matrix("Likeability")
    members = matrix.index.tolist()
    rows = []
    for i, m1 in enumerate(members):
        for j, m2 in enumerate(members):
            if i >= j:
                continue
            shared = matrix.loc[[m1, m2]].dropna(axis=1)
            if shared.shape[1] < 3:
                continue
            r, p = stats.pearsonr(shared.loc[m1], shared.loc[m2])
            rows.append({
                "Member 1": m1,
                "Member 2": m2,
                "Correlation": round(r, 3),
                "P-value": round(p, 4),
                "Shared Books": shared.shape[1],
            })
    return pd.DataFrame(rows).sort_values("Correlation", ascending=False)


def taste_similarity_matrix() -> pd.DataFrame:
    """Full correlation matrix for clustering/heatmap."""
    matrix = get_member_book_matrix("Likeability")
    return matrix.T.corr()


def hot_takes(threshold: float = 1.5) -> pd.DataFrame:
    """Ratings deviating > threshold from group average."""
    ratings = get_ratings_long()
    book_avgs = ratings.groupby("Book")["Likeability"].mean().rename("book_avg")
    merged = ratings.merge(book_avgs, on="Book")
    merged["deviation"] = merged["Likeability"] - merged["book_avg"]
    merged["abs_deviation"] = merged["deviation"].abs()

    hot = merged[merged["abs_deviation"] > threshold].sort_values(
        "abs_deviation", ascending=False
    )
    return hot[["Book", "Member", "Likeability", "book_avg", "deviation", "abs_deviation"]]


def book_controversy() -> pd.DataFrame:
    """Standard deviation per book — higher = more polarizing."""
    summary = get_book_summary()
    return summary[["Book", "book_index", "std_like", "avg_like", "num_raters"]].sort_values(
        "std_like", ascending=False
    )


def proposer_performance() -> pd.DataFrame:
    """Average group rating for books each member proposed."""
    summary = get_book_summary()
    result = summary.groupby("Proposer").agg(
        books_proposed=("Book", "count"),
        avg_like=("avg_like", "mean"),
        avg_imp=("avg_imp", "mean"),
    ).reset_index()
    return result.sort_values("avg_like", ascending=False)


def proposer_bias() -> pd.DataFrame:
    """Do proposers rate their own picks higher than the group average?

    Returns per-proposer: their rating of own picks vs group avg of own picks.
    """
    ratings = get_ratings_long()
    own = ratings[ratings["Member"] == ratings["Proposer"]]
    if own.empty:
        return pd.DataFrame()

    book_avgs = ratings.groupby("Book")["Likeability"].mean().rename("book_avg")
    own = own.merge(book_avgs, on="Book")

    result = own.groupby("Member").agg(
        own_rating=("Likeability", "mean"),
        group_avg=("book_avg", "mean"),
        books=("Book", "count"),
    ).reset_index()
    result["bias"] = result["own_rating"] - result["group_avg"]
    return result.sort_values("bias", ascending=False)


def member_deviation_per_book() -> pd.DataFrame:
    """Per-member deviation from group average for each book."""
    ratings = get_ratings_long()
    book_avgs = ratings.groupby("Book")["Likeability"].mean().rename("book_avg")
    merged = ratings.merge(book_avgs, on="Book")
    merged["deviation"] = merged["Likeability"] - merged["book_avg"]
    return merged


def rating_trends() -> pd.DataFrame:
    """Group average ratings over time with rolling averages."""
    summary = get_book_summary()
    summary = summary.sort_values("Date")
    summary["rolling_like_3"] = summary["avg_like"].rolling(3, min_periods=1).mean()
    summary["rolling_imp_3"] = summary["avg_imp"].rolling(3, min_periods=1).mean()
    return summary


def contrarian_index() -> pd.DataFrame:
    """Count how often each member deviates > 1 point from group avg."""
    ratings = get_ratings_long()
    book_avgs = ratings.groupby("Book")["Likeability"].mean().rename("book_avg")
    merged = ratings.merge(book_avgs, on="Book")
    merged["big_deviation"] = (merged["Likeability"] - merged["book_avg"]).abs() > 1.0

    result = merged.groupby("Member").agg(
        contrarian_count=("big_deviation", "sum"),
        total_rated=("Book", "count"),
    ).reset_index()
    result["contrarian_pct"] = result["contrarian_count"] / result["total_rated"]
    return result.sort_values("contrarian_pct", ascending=False)


def hivemind_index() -> pd.DataFrame:
    """Who tracks the group average closest (lowest avg deviation)."""
    return agreement_score()  # Same calculation, lower = more hivemind


def genre_distribution() -> pd.DataFrame:
    """Genre counts from enrichment data."""
    from utils.data_loader import get_enriched_books
    enrichment = get_enriched_books()
    genres = {}
    for book_data in enrichment.values():
        for genre in book_data.get("genres", []):
            genres[genre] = genres.get(genre, 0) + 1
    df = pd.DataFrame(list(genres.items()), columns=["Genre", "Count"])
    return df.sort_values("Count", ascending=False)


def seasonal_ratings() -> pd.DataFrame:
    """Average ratings by month."""
    summary = get_book_summary()
    summary["Month"] = summary["Date"].dt.month
    summary["Month Name"] = summary["Date"].dt.strftime("%B")
    return summary.groupby(["Month", "Month Name"]).agg(
        avg_like=("avg_like", "mean"),
        count=("Book", "count"),
    ).reset_index().sort_values("Month")


def cosine_similarity_books() -> pd.DataFrame:
    """Cosine similarity between books based on member ratings."""
    matrix = get_member_book_matrix("Likeability")
    # Transpose: books as rows, members as columns
    bm = matrix.T
    # Fill NaN with column mean for similarity calc
    bm_filled = bm.apply(lambda col: col.fillna(col.mean()), axis=0)

    from numpy.linalg import norm
    books = bm_filled.index.tolist()
    rows = []
    for i, b1 in enumerate(books):
        for j, b2 in enumerate(books):
            if i >= j:
                continue
            v1 = bm_filled.loc[b1].values
            v2 = bm_filled.loc[b2].values
            n1, n2 = norm(v1), norm(v2)
            if n1 == 0 or n2 == 0:
                continue
            sim = np.dot(v1, v2) / (n1 * n2)
            rows.append({"Book 1": b1, "Book 2": b2, "Similarity": round(sim, 3)})
    return pd.DataFrame(rows).sort_values("Similarity", ascending=False)


def attendance_by_book() -> pd.DataFrame:
    """Which members rated each book."""
    ratings = get_ratings_long()
    raw_data = get_book_summary()
    book_order = raw_data.sort_values("book_index")["Book"].tolist()

    result = []
    for book in book_order:
        book_ratings = ratings[ratings["Book"] == book]
        for member in MEMBERS:
            rated = member in book_ratings["Member"].values
            result.append({"Book": book, "Member": member, "Rated": rated})
    return pd.DataFrame(result)
