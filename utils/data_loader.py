"""Load and transform DBC data from CSV and enrichment JSON."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "DrunkBookClub - Sheet1.csv"
ENRICHMENT_PATH = DATA_DIR / "book_enrichment.json"

MEMBERS = ["Willy", "Bartel", "Josh", "Faulkner", "Ryan", "John", "Christian"]

# Nickname mapping for the Proposer column
PROPOSER_NICKNAMES = {
    "Johnny": "John",
    "Wilson": "Willy",
}


@st.cache_data
def load_raw_data() -> pd.DataFrame:
    """Load the raw CSV and clean it up."""
    df = pd.read_csv(CSV_PATH)
    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y")
    df["Proposer"] = df["Proposer"].replace(PROPOSER_NICKNAMES)
    df["Book"] = df["Book"].str.strip()
    df["book_index"] = range(1, len(df) + 1)
    return df


@st.cache_data
def load_enrichment() -> dict:
    """Load book enrichment JSON metadata."""
    if ENRICHMENT_PATH.exists():
        with open(ENRICHMENT_PATH) as f:
            return json.load(f)
    return {}


@st.cache_data
def get_ratings_long() -> pd.DataFrame:
    """Transform wide-format CSV into long-format ratings DataFrame.

    Returns DataFrame with columns:
        Book, Date, Proposer, book_index, Member, Likeability, Importance
    One row per member-book rating (only where ratings exist).
    """
    df = load_raw_data()
    rows = []
    for _, book_row in df.iterrows():
        for member in MEMBERS:
            like_col = f"{member} - Likeability"
            imp_col = f"{member} - Importance"
            if like_col in df.columns and imp_col in df.columns:
                like_val = book_row.get(like_col)
                imp_val = book_row.get(imp_col)
                # Skip if both are missing
                if pd.notna(like_val) and pd.notna(imp_val):
                    rows.append({
                        "Book": book_row["Book"],
                        "Date": book_row["Date"],
                        "Proposer": book_row["Proposer"],
                        "book_index": book_row["book_index"],
                        "Member": member,
                        "Likeability": float(like_val),
                        "Importance": float(imp_val),
                    })
    return pd.DataFrame(rows)


@st.cache_data
def get_book_summary() -> pd.DataFrame:
    """Get per-book summary stats.

    Returns DataFrame with columns:
        Book, Date, Proposer, book_index, Avg Likeability, Avg Importance,
        Std Likeability, Num Raters
    """
    ratings = get_ratings_long()
    raw = load_raw_data()

    summary = ratings.groupby("Book").agg(
        avg_like=("Likeability", "mean"),
        avg_imp=("Importance", "mean"),
        std_like=("Likeability", "std"),
        std_imp=("Importance", "std"),
        num_raters=("Member", "count"),
    ).reset_index()

    # Merge back book metadata
    meta = raw[["Book", "Date", "Proposer", "book_index"]].drop_duplicates()
    summary = summary.merge(meta, on="Book")
    summary = summary.sort_values("book_index").reset_index(drop=True)
    # Fill NaN std (single-rater books) with 0
    summary["std_like"] = summary["std_like"].fillna(0)
    summary["std_imp"] = summary["std_imp"].fillna(0)
    return summary


@st.cache_data
def get_member_book_matrix(metric: str = "Likeability") -> pd.DataFrame:
    """Get a Member x Book matrix for the given metric.

    Returns a pivot table with members as rows, books as columns (in chronological order).
    Missing ratings are NaN.
    """
    ratings = get_ratings_long()
    raw = load_raw_data()
    book_order = raw.sort_values("Date")["Book"].tolist()

    matrix = ratings.pivot_table(
        index="Member",
        columns="Book",
        values=metric,
        aggfunc="first",
    )
    # Reorder columns chronologically
    matrix = matrix[[b for b in book_order if b in matrix.columns]]
    return matrix


@st.cache_data
def get_enriched_books() -> dict:
    """Get enrichment data merged with book keys matching CSV names."""
    return load_enrichment()


def get_book_enrichment(book_name: str) -> dict:
    """Get enrichment data for a specific book."""
    enrichment = get_enriched_books()
    return enrichment.get(book_name, {})


@st.cache_data
def get_all_books() -> list[str]:
    """Get list of all book names in chronological order."""
    df = load_raw_data()
    return df.sort_values("Date")["Book"].tolist()


@st.cache_data
def get_all_proposers() -> list[str]:
    """Get unique proposers."""
    df = load_raw_data()
    return sorted(df["Proposer"].unique().tolist())
