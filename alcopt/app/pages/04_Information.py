import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import warnings
import traceback
from unum import units


from alcopt.database.models import (
    Container,
    ContainerFermentationLog,
    Fermentation,
    SpecificGravityMeasurement,
    Review,
)
from alcopt.utils import sg_diff_to_abv, abv_to_sugar, get_sugar, BENCHMARK, mL
from alcopt.database.utils import (
    get_db,
    current_fermentation_log,
    latest_fermentation_log,
)
from alcopt.database.queries import get_fermentation_ingredient_additions


def display_fermentation_info(db, fermentation):
    """Displays fermentation info into streamlit"""
    st.subheader("Fermentation Details")
    st.write(f"**Fermentation ID:** {fermentation.id}")
    st.write(f"**Start Date:** {fermentation.start_date}")
    st.write(f"**End Date:** {fermentation.end_date}")

    st.subheader("Ingredients")
    # Only include additions that fell within a log window for this fermentation
    ingredients = get_fermentation_ingredient_additions(db, fermentation.id)
    if ingredients:
        ingredients_df = pd.DataFrame(
            [
                (
                    ing.ingredient.name,
                    ing.amount,
                    ing.unit,
                    (ing.added_at.date() - fermentation.start_date).days,
                    ing.ingredient.price,
                )
                for ing in ingredients
            ],
            columns=["Ingredient", "Amount", "Unit", "Days from Start", "Price"],
        )
        grouped_ingredients = (
            ingredients_df.groupby(["Ingredient", "Days from Start"])
            .agg({"Amount": "sum", "Unit": "first"})
            .reset_index()
        )
        st.dataframe(grouped_ingredients, hide_index=True)
    else:
        st.write("No ingredients added yet.")

    # Calculate yield from bottle logs
    all_logs = (
        db.query(ContainerFermentationLog)
        .filter_by(fermentation_id=fermentation.id)
        .all()
    )
    bottle_logs = [log for log in all_logs if log.stage == "bottled"]
    initial_volume = np.sum(
        [
            ing.amount
            for ing in ingredients
            if ing.ingredient.ingredient_type == "Liquid"
        ]
    )
    final_mass = np.sum(
        [
            b.amount
            - db.query(Container).filter_by(id=b.container_id).first().empty_mass
            for b in bottle_logs
            if b.unit == "g" and b.amount is not None
        ]
    )
    st.markdown(f"**Initial Volume (mL):** {initial_volume:.2f}")
    st.markdown(f"**Final Mass (g):** {final_mass:.2f}")

    # Calculate cost
    total_cost = 0.0
    for ing in ingredients:
        m = 1.0
        if ing.ingredient.ingredient_type == "Liquid":
            if ing.unit == "g":
                m = 0.001 * ing.ingredient.density
            else:
                m = 0.001
        elif ing.ingredient.ingredient_type == "Solute":
            if ing.unit == "g":
                m = 0.001
            elif ing.unit == "u":
                m = 1.0
            elif ing.unit == "tsp":
                m = 0.00492892
        else:
            warnings.warn(f"Unknown ingredient type: {ing.ingredient.ingredient_type}")
        total_cost += ing.ingredient.price * ing.amount * m
    st.markdown(f"**Total Cost:** ${total_cost:.2f}")
    if final_mass > 0:
        st.markdown(f"**Cost per kg:** ${1000 * total_cost / final_mass:.2f}")

    st.subheader("Specific Gravity Measurements")
    measurements = (
        db.query(SpecificGravityMeasurement)
        .filter_by(fermentation_id=fermentation.id)
        .all()
    )
    if measurements:
        initial_sg = measurements[0].specific_gravity
        final_sg = measurements[-1].specific_gravity
        abv = sg_diff_to_abv(initial_sg - final_sg)
        st.markdown(f"**~ABV (%)**: {abv:.2f}")
        if initial_volume > 0:
            initial_rs = get_sugar(ingredients) / (initial_volume * mL)
            rs_diff = abv_to_sugar(sg_diff_to_abv(initial_sg - final_sg))
            residual_sugar = initial_rs - rs_diff
            st.markdown(
                f"**~Residual Sugar (g/L)**: {residual_sugar.asUnit(units.g / units.L).asNumber():.2f}"
            )
        else:
            st.write("Cannot estimate residual sugar (no liquid ingredient volume).")

        measurements_df = pd.DataFrame(
            [
                (
                    m.measurement_date,
                    m.specific_gravity,
                    (m.measurement_date - fermentation.start_date).days,
                )
                for m in measurements
            ],
            columns=["Measurement Date", "Specific Gravity", "Days from Start"],
        )

        fig, ax1 = plt.subplots()

        ax1.set_xlabel("Days from Start")
        ax1.set_ylabel("Specific Gravity", color="tab:blue")

        ax1.axhline(y=initial_sg, color="gray", linestyle="--")
        ax1.text(
            0,
            initial_sg,
            f"Initial SG: {initial_sg:.3f}",
            color="gray",
            verticalalignment="bottom",
        )

        ax1.axhline(y=final_sg, color="black", linestyle="--")
        ax1.text(
            0,
            final_sg,
            f"Final SG: {final_sg:.3f} (~ABV: {abv:.2f}%)",
            color="black",
            verticalalignment="bottom",
        )

        ax1.plot(
            measurements_df["Days from Start"],
            measurements_df["Specific Gravity"],
            color="tab:blue",
            marker="o",
        )
        ax1.tick_params(axis="y", labelcolor="tab:blue")
        ylim1 = [0.995, max(measurements_df["Specific Gravity"]) + 0.01]
        ax1.set_ylim(*ylim1)

        ax2 = ax1.twinx()
        ax2.set_ylabel("Approximate ABV (%)", color="tab:red")
        ylim2 = [
            sg_diff_to_abv(initial_sg - ylim1[0]),
            sg_diff_to_abv(initial_sg - ylim1[1]),
        ]
        ax2.set_ylim(*ylim2)
        ax2.tick_params(axis="y", labelcolor="tab:red")

        for item in BENCHMARK:
            if item["abv"] is not None:
                abv = item["abv"]
                if abv <= ylim2[0] and abv >= ylim2[1]:
                    ax2.axhline(y=abv, color="green", linestyle="--")
                    ax2.text(
                        0,
                        abv,
                        f"{item['name']} {abv}%",
                        color="green",
                        verticalalignment="bottom",
                    )

        fig.tight_layout()
        st.pyplot(fig)
    else:
        st.write("No specific gravity measurements yet.")


def get_container_info(container_id):
    with get_db() as db:
        try:
            container = db.query(Container).filter_by(id=container_id).first()

            if not container:
                st.error(f"No container found with ID: {container_id}")
                return

            st.title(
                f"Container Information for {container.container_type.title()} ID: {container_id}"
            )

            st.subheader("Container Details")
            st.write(f"**Type:** {container.container_type}")
            st.write(f"**Volume (liters):** {container.volume_liters}")
            st.write(f"**Material:** {container.material}")
            st.write(f"**Empty Mass:** {container.empty_mass}")
            st.write(f"**Date Added:** {container.date_added}")

            # Resolve fermentation from log
            log = current_fermentation_log(db, container_id)
            if log is None:
                log = latest_fermentation_log(db, container_id)

            if log:
                fermentation = (
                    db.query(Fermentation).filter_by(id=log.fermentation_id).first()
                )
                if fermentation:
                    display_fermentation_info(db, fermentation)
            else:
                st.write("This container has no fermentation history.")

            st.subheader("Reviews")
            reviews = db.query(Review).filter_by(container_id=container_id).all()
            if reviews:
                reviews_df = pd.DataFrame(
                    [
                        (
                            r.overall_rating,
                            r.boldness,
                            r.tannicity,
                            r.sweetness,
                            r.acidity,
                            r.complexity,
                            r.review_date,
                        )
                        for r in reviews
                    ],
                    columns=[
                        "Overall Rating",
                        "Boldness",
                        "Tannicity",
                        "Sweetness",
                        "Acidity",
                        "Complexity",
                        "Review Date",
                    ],
                )
                st.dataframe(reviews_df, hide_index=True)
            else:
                st.write("No reviews for this container yet.")
        except Exception as e:
            traceback.print_exc()
            st.error(f"An error occurred: {e}")


BOTTLE_ID_OFFSET = 18


def container_info_form():
    st.title("Retrieve Container Information")
    st.info(
        f"Vessels and bottles are now unified as **containers**. If you're "
        f"looking up a bottle by its old bottle ID, add **+{BOTTLE_ID_OFFSET}** "
        f"to get its container ID (e.g. old bottle #5 is container "
        f"#{5 + BOTTLE_ID_OFFSET}).",
        icon=":material/info:",
    )

    with st.form(key="container_info_form"):
        id_input = st.number_input("Container ID", min_value=1, step=1)
        submit_button = st.form_submit_button(label="Get Information")

    if submit_button:
        get_container_info(id_input)


# Deep link from a QR-code label: /Information?container_id=42
deep_link_id = st.query_params.get("container_id")
if deep_link_id is not None:
    try:
        get_container_info(int(deep_link_id))
    except (TypeError, ValueError):
        st.error(f"Invalid container_id in URL: {deep_link_id!r}")
    st.divider()

container_info_form()
