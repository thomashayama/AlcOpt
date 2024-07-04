import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
from sqlalchemy_models import Vessel, Fermentation, FermentationIngredient, SpecificGravityMeasurement, Bottle, Review


st.set_page_config(
    page_title="Information",
    # page_icon="🍷",
)

engine = create_engine('sqlite:///wine_mead.db')
Session = sessionmaker(bind=engine)
session = Session()

def sg_diff_to_abv(sg_diff):
    return sg_diff * 131.25

def display_fermentation_info(fermentation):
    st.subheader("Fermentation Details")
    st.write(f"**Fermentation ID:** {fermentation.id}")
    st.write(f"**Start Date:** {fermentation.start_date}")
    st.write(f"**End Date:** {fermentation.end_date}")

    st.subheader("Ingredients")
    ingredients = session.query(FermentationIngredient).filter_by(fermentation_id=fermentation.id).all()
    if ingredients: 
        ingredients_df = pd.DataFrame([(ing.ingredient.name, ing.amount, ing.unit, (ing.added_at - fermentation.start_date).days) for ing in ingredients], columns=["Ingredient", "Amount", "Unit", "Days from Start"])
        grouped_ingredients = ingredients_df.groupby(["Ingredient", "Days from Start"]).agg({"Amount": "sum", "Unit": "first"}).reset_index()
        st.dataframe(grouped_ingredients, hide_index=True)
    else:
        st.write("No ingredients added yet.")

    st.subheader("Specific Gravity Measurements")
    measurements = session.query(SpecificGravityMeasurement).filter_by(fermentation_id=fermentation.id).all()
    if measurements:
        initial_sg = measurements[0].specific_gravity
        final_sg = measurements[-1].specific_gravity
        abv = sg_diff_to_abv(initial_sg - final_sg)
        st.markdown(f"**~ABV (%)**: {abv:.2f}")
        measurements_df = pd.DataFrame([(m.measurement_date, m.specific_gravity, (m.measurement_date - fermentation.start_date).days) for m in measurements], columns=["Measurement Date", "Specific Gravity", "Days from Start"])

        fig, ax1 = plt.subplots()

        ax1.set_xlabel('Days from Start')
        ax1.set_ylabel('Specific Gravity', color='tab:blue')

        # Plot initial and final SG as horizontal lines with labels
        ax1.axhline(y=initial_sg, color='gray', linestyle='--')
        ax1.text(0, initial_sg, f'Initial SG: {initial_sg:.3f}', color='gray', verticalalignment='bottom')

        ax1.axhline(y=final_sg, color='black', linestyle='--')
        ax1.text(0, final_sg, f'Final SG: {final_sg:.3f} (~ABV: {abv:.2f}%)', color='black', verticalalignment='bottom')
        
        ax1.plot(measurements_df['Days from Start'], measurements_df['Specific Gravity'], color='tab:blue', marker='o')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        ylim1 = [0.995, max(measurements_df['Specific Gravity']) + 0.01]
        ax1.set_ylim(*ylim1)

        ax2 = ax1.twinx()
        ax2.set_ylabel('Approximate ABV (%)', color='tab:red')
        ylim2 = [sg_diff_to_abv(initial_sg - ylim1[0]), sg_diff_to_abv(initial_sg - ylim1[1])]
        ax2.set_ylim(*ylim2)
        ax2.tick_params(axis='y', labelcolor='tab:red')

        benchmark_abv = {
            'Beer': 5.0,
            'Moscato': 7.0,
            'Riesling': 9.0,
            'Cabernet Sauvignon': 12.0,
            'Zinfandel': 15.0,
            'Port': 20.0,
        }

        for wine, abv in benchmark_abv.items():
            if abv <= ylim2[0] and abv >= ylim2[1]:
                ax2.axhline(y=abv, color='green', linestyle='--')
                ax2.text(0, abv, f'{wine} {abv}%', color='green', verticalalignment='bottom')

        fig.tight_layout()
        st.pyplot(fig)
    else:
        st.write("No specific gravity measurements yet.")

def get_vessel_info(vessel_id):
    try:
        vessel = session.query(Vessel).filter_by(id=vessel_id).first()

        if not vessel:
            st.error(f"No vessel found with ID: {vessel_id}")
            return

        fermentation = session.query(Fermentation).filter_by(id=vessel.fermentation_id).first() if vessel.fermentation_id else None

        st.title(f"Vessel Information for Vessel ID: {vessel_id}")

        st.subheader("Vessel Details")
        st.write(f"**Volume (liters):** {vessel.volume_liters}")
        st.write(f"**Material:** {vessel.material}")
        st.write(f"**Empty Mass:** {vessel.empty_mass}")
        st.write(f"**Date Added:** {vessel.date_added}")

        if fermentation:
            display_fermentation_info(fermentation)
        else:
            st.write("This vessel is not currently used in any fermentation.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        session.close()

def get_bottle_info(bottle_id):
    try:
        bottle = session.query(Bottle).filter_by(id=bottle_id).first()

        if not bottle:
            st.error(f"No bottle found with ID: {bottle_id}")
            return

        fermentation = session.query(Fermentation).filter_by(id=bottle.fermentation_id).first() if bottle.fermentation_id else None

        st.title(f"Bottle Information for Bottle ID: {bottle_id}")

        st.subheader("Bottle Details")
        st.write(f"**Volume (liters):** {bottle.volume_liters}")
        st.write(f"**Empty Mass:** {bottle.empty_mass}")
        st.write(f"**Date Added:** {bottle.date_added}")
        st.write(f"**Bottling Date:** {bottle.bottling_date}")

        if fermentation:
            display_fermentation_info(fermentation)

        st.subheader("Reviews")
        reviews = session.query(Review).filter_by(bottle_id=bottle_id).all()
        if reviews:
            reviews_df = pd.DataFrame([(r.overall_rating, r.boldness, r.tannicity, r.sweetness, r.acidity, r.complexity, r.review_date) for r in reviews], columns=["Overall Rating", "Boldness", "Tannicity", "Sweetness", "Acidity", "Complexity", "Review Date"])
            st.dataframe(reviews_df, hide_index=True)
        else:
            st.write("No reviews for this bottle yet.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        session.close()

def vessel_info_form():
    st.title("Retrieve Vessel or Bottle Information")

    with st.form(key='vessel_info_form'):
        retrieval_type = st.radio("Select the type of information to retrieve:", ("Vessel", "Bottle"))
        id_input = st.number_input("ID", min_value=1, step=1)
        
        submit_button = st.form_submit_button(label='Get Information')

    if submit_button:
        if retrieval_type == "Vessel":
            get_vessel_info(id_input)
        else:
            get_bottle_info(id_input)

vessel_info_form()