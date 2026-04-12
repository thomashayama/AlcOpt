import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from alcopt.database.models import Review
from alcopt.database.queries import get_fermentation_leaderboard
from alcopt.database.utils import get_db
from alcopt.utils import (
    get_ratings_abv_data,
    get_ratings_rs_data,
    plot_correlation_heatmap,
    plot_sweetness_vs_rating,
    reviews_to_df,
)

st.title("AlcOpt")
st.caption("Track tastings, brews, and bottles. Optimize the next batch.")
st.page_link(
    "pages/01_Tasting_Form.py",
    label="Submit a tasting",
    icon=":material/rate_review:",
)

st.divider()
st.subheader("Fermentation Leaderboard")

with get_db() as db:
    leaderboard_df = get_fermentation_leaderboard(db)
    leaderboard_df.insert(0, "Rank", range(1, len(leaderboard_df) + 1))
    st.dataframe(
        leaderboard_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", width="small"),
            "Fermentation ID": st.column_config.NumberColumn(
                "Fermentation", width="small"
            ),
            "Average Rating": st.column_config.ProgressColumn(
                "Avg rating",
                help="Average overall rating across all reviews (out of 5)",
                format="%.2f",
                min_value=0,
                max_value=5,
            ),
            "# Ratings": st.column_config.NumberColumn("Reviews", width="small"),
        },
    )

    reviews = db.query(Review).all()
    reviews_df = reviews_to_df(reviews)

    st.pyplot(plot_correlation_heatmap(reviews_df))
    st.pyplot(plot_sweetness_vs_rating(reviews_df))

    ratings = [review.overall_rating for review in reviews]
    rating_hist = plt.figure(figsize=(8, 5))
    plt.hist(
        ratings,
        bins=np.arange(0.5, 6.5, 1),
        edgecolor="black",
        color="#4CAF50",
        alpha=0.8,
    )
    plt.xticks(range(1, 6))
    plt.xlabel("Rating", fontsize=12)
    plt.ylabel("# Reviews", fontsize=12)
    plt.title("Distribution of Overall Ratings", fontsize=14, fontweight="bold")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    st.pyplot(rating_hist)

    abv_data = get_ratings_abv_data()
    if abv_data:
        ratings, abvs = zip(*abv_data)
        m, b = np.polyfit(abvs, ratings, 1)
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(
            abvs,
            ratings,
            color="#1f77b4",
            edgecolor="black",
            alpha=0.8,
            label="Data Points",
        )
        x = np.array([min(abvs), max(abvs)])
        pred = m * x + b
        ax.plot(x, pred, color="red", linestyle="--", linewidth=2, label="Trend Line")
        ax.set_xlabel("ABV (%)", fontsize=12)
        ax.set_ylabel("Overall Rating", fontsize=12)
        ax.set_title("Overall Rating vs ABV", fontsize=14, fontweight="bold")
        ax.grid(axis="both", linestyle="--", alpha=0.7)
        ax.legend(loc="best", fontsize=10)
        st.pyplot(fig)

    rs_data = get_ratings_rs_data()
    if rs_data:
        ratings, rss = zip(*rs_data)
        m, b = np.polyfit(rss, ratings, 1)
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(
            rss,
            ratings,
            color="#ff7f0e",
            edgecolor="black",
            alpha=0.8,
            label="Data Points",
        )
        x = np.array([min(rss), max(rss)])
        pred = m * x + b
        ax.plot(x, pred, color="red", linestyle="--", linewidth=2, label="Trend Line")
        ax.set_xlabel("Residual Sugar (g/L)", fontsize=12)
        ax.set_ylabel("Overall Rating", fontsize=12)
        ax.set_title("Overall Rating vs Residual Sugar", fontsize=14, fontweight="bold")
        ax.grid(axis="both", linestyle="--", alpha=0.7)
        ax.legend(loc="best", fontsize=10)
        st.pyplot(fig)
