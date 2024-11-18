import streamlit as st
import pandas as pd 
from datetime import datetime
import cv2
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from unum import units

# SQL
from sqlalchemy import asc

from alcopt.database.models import Fermentation, SpecificGravityMeasurement, FermentationIngredient, Ingredient, Vessel, FermentationVesselLog, Bottle, BottleLog
from alcopt.streamlit_utils import all_ferm_ingredients_info, all_vessel_log_info, all_measurement_info, all_bottle_info
from alcopt.database.utils import get_db
from alcopt.utils import sugar_to_abv, abv_to_sugar, BENCHMARK, mL, str2unit, unit2str, VOLUME_UNITS, MASS_UNITS

st.set_page_config(
    page_title="Brew Tracking",
    page_icon="🍷",
)
if "new_ingredients" not in st.session_state:
    st.session_state.new_ingredients = []


def add_new_ingredient(db):
    with st.form("Add New Ingredient"):
        ingredient_name = st.text_input("New Ingredient Name")
        sugar_content = st.number_input("Sugar Content (g/L or g)", value=0.0)
        ingredient_type = st.radio("Type", ["Liquid", "Solute", "Solid"])
        density = st.number_input("Density (g/mL)", value=1.0)
        price = st.number_input("Price ($/L or kg)", value=0.00)
        notes = st.text_input("Additional Notes")
        if st.form_submit_button('Add'):
            if ingredient_name is not None and ingredient_name != "":
                try:
                    new_ingredient = Ingredient(name=ingredient_name, sugar_content=sugar_content, ingredient_type=ingredient_type, density=density, price=price, notes=notes)
                    db.add(new_ingredient)
                    db.commit()
                except Exception as e:
                    # st.error("Ingredient already in table!!")
                    st.error(e)


def add_fermentation_ingredient(ingredient_name=None):
    """Add Ingredient to a fermentation"""
    with st.form("Add Ingredient"):
        with get_db() as db:
            vessel_id = st.number_input("Vessel ID", value=1, min_value=1, step=1)
            if ingredient_name is None:
                ingredient_name = st.text_input("Ingredient Name")
            date = st.date_input("Date")
            col_start, col_end = st.columns([1, 1])
            start_amount = col_start.number_input("Starting Amount", value=0.0, min_value=0.0)
            end_amount = col_end.number_input("Ending Amount", value=0.0, min_value=0.0)
            amount = end_amount - start_amount
            unit = st.text_input("Units", "g")
            if st.form_submit_button('Add'):
                try:
                    vessel = db.query(Vessel).filter_by(id=vessel_id).first()
                    if vessel is None:
                        st.error(f"Vessel {vessel_id} not found")
                    else:
                        fermentation_id = vessel.fermentation_id
                        if fermentation_id is None:
                            new_fermentation = Fermentation(start_date=date)
                            db.add(new_fermentation)
                            db.commit()
                            fermentation_id = new_fermentation.id
                            st.success(f"Created New Fermentation <{fermentation_id}>")

                            vessel_log = FermentationVesselLog(
                                fermentation_id=fermentation_id,
                                vessel_id=vessel_id,
                                start_date=date
                            )
                            db.add(vessel_log)
                            db.commit()
                            st.success(f"Created New Fermentation Vessel Log <{vessel_log.id}>")

                            # Update the fermentation_id of the vessel
                            vessel.fermentation_id = fermentation_id
                            db.commit()
                            st.success(f"Fermentation ID updated successfully for Vessel ID: {vessel_id}")
                        ingredient_id = db.query(Ingredient).filter_by(name=ingredient_name).first().id
                        new_ferm_ingredient = FermentationIngredient(
                            fermentation_id=fermentation_id, 
                            ingredient_id=ingredient_id, 
                            amount=amount, 
                            unit=unit,
                            added_at=date)
                        db.add(new_ferm_ingredient)
                        db.commit()
                        st.success(f"Created New Fermentation Ingredient <{new_ferm_ingredient.id}>")
                except Exception as e:
                    st.error(f"Error {e}")


def add_measurement_form(db):
    st.title("Add Specific Gravity Measurement")

    with st.form(key='measurement_form'):
        vessel_id = st.number_input("Vessel ID", value=1, min_value=1, step=1)
        measurement_date = st.date_input("Measurement Date", value=datetime.now())
        specific_gravity = st.number_input("Specific Gravity", value=.999, min_value=0.0, step=0.001, format="%.3f")

        submit_button = st.form_submit_button(label='Add Measurement')

    if submit_button:
        try:
            vessel = db.query(Vessel).filter_by(id=vessel_id).first()
            if vessel is None:
                st.error(f"Vessel {vessel_id} not found")
            else:
                if vessel.fermentation_id is None:
                    st.error(f"Vessel {vessel_id} doesn't have a fermentation")
                else:
                    # Add new specific gravity measurement
                    new_measurement = SpecificGravityMeasurement(
                        fermentation_id=vessel.fermentation_id,
                        measurement_date=measurement_date,
                        specific_gravity=specific_gravity
                    )
                    db.add(new_measurement)
                    db.commit()
                    st.success(f"Measurement added successfully for Fermentation ID: {vessel.fermentation_id}")
        except Exception as e:
            st.error(f"An error occurred: {e}")
            db.rollback()


def rack_form(db):
    with st.form(key='rack_form'):
        col_from, col_to = st.columns((1, 1))
        from_vessel_id = col_from.number_input("From Vessel ID", value=1, min_value=1, step=1)
        to_vessel_id = col_to.number_input("To Vessel ID", value=1, min_value=1, step=1)
        date = st.date_input("Date")
        submit_button = st.form_submit_button(label='Add Action')

    if submit_button:
        try:
            from_vessel = db.query(Vessel).filter_by(id=from_vessel_id).first()
            to_vessel = db.query(Vessel).filter_by(id=to_vessel_id).first()
            vessel_log = FermentationVesselLog(
                fermentation_id=from_vessel.fermentation_id,
                vessel_id=to_vessel.id,
                start_date=date
            )
            db.add(vessel_log)
            db.commit()
            to_vessel.fermentation_id = from_vessel.fermentation_id
            from_vessel.fermentation_id = None
            db.commit()
            st.success(f"Racked from {from_vessel.id} to {to_vessel.id}")
        except Exception as e:
            st.error(f"An error occurred: {e}")


def bottle_form(db):
    with st.form(key='bottle_form'):
        vessel_id = st.number_input("Vessel ID", value=1, min_value=1, step=1)
        bottle_id = st.number_input("Bottle ID", value=1, min_value=1, step=1)
        date = st.date_input("Date")
        col_start, col_end = st.columns([1, 1])
        start_amount = col_start.number_input("Starting Amount", value=0.0, min_value=0.0)
        end_amount = col_end.number_input("Ending Amount", value=0.0, min_value=0.0)
        amount = end_amount - start_amount
        unit = st.text_input("Units", "g")
        submit_button = st.form_submit_button(label='Add Action')

    if submit_button:
        try:
            vessel = db.query(Vessel).filter_by(id=vessel_id).first()
            bottle = db.query(Bottle).filter_by(id=bottle_id).first()
            bottle_log = BottleLog(
                fermentation_id=vessel.fermentation_id,
                bottle_id=bottle.id,
                vessel_id=vessel_id,
                bottling_date=date,
                amount=amount,
                unit=unit,
            )
            db.add(bottle_log)
            db.commit()
            st.success(f"Created New Bottle Log <{bottle_log.id}>")

            bottle.fermentation_id = vessel.fermentation_id
            bottle.bottling_date = date
            db.commit()
            st.success(f"Bottled from Vessel {vessel.id} into Bottle {bottle.id}")
        except Exception as e:
            st.error(f"An error occurred: {e}")

    if st.button("Vessel Empty"):
        vessel = db.query(Vessel).filter_by(id=vessel_id).first()
        vessel.fermentation_id = None
        db.commit()
        st.success(f"Vessel {vessel.id} Emptied")


def get_volume(ingredients):
    volume = 0*mL

    for ingredient in ingredients:
        ingredient_type = ingredient['ingredient_type'].lower()
        if ingredient_type in ["liquid", "solvent"]:
            print("is_liq")
            unit = unit2str(ingredient['amount'])
            if unit in VOLUME_UNITS:
                volume += ingredient['amount']
            elif unit in MASS_UNITS:
                volume += ingredient['amount'] / ingredient['density']
            else:
                raise Exception(f"{unit} Not Implemented")

    return volume


def get_sugar(ingredients):
    sugar = 0*units.g

    for ingredient in ingredients:
        ingredient_type = ingredient['ingredient_type'].lower()
        if ingredient['sugar_content'] is not None:
            if ingredient_type in ["liquid", "solvent"]:
                unit = unit2str(ingredient['amount'])
                print(ingredient_type, unit)
                if unit in VOLUME_UNITS:
                    sugar += ingredient['amount'] * ingredient['sugar_content']
                elif unit in MASS_UNITS:
                    sugar += ingredient['amount'] * ingredient['sugar_content'] / ingredient['density']
                else:
                    raise Exception(f"{unit} Not Implemented")
            elif ingredient_type in ["solid", "solute"]:
                sugar += ingredient['amount'] * ingredient['sugar_content']
    
    return sugar


def calculate_max_potential_abv(ingredients):
    # Constants for calculation
    total_sugar = get_sugar(ingredients)
    fermentation_volume = get_volume(ingredients)
    
    print(total_sugar)
    print(fermentation_volume)
    if fermentation_volume > 0*mL:
        max_potential_abv = sugar_to_abv(total_sugar / fermentation_volume)
        return max_potential_abv, total_sugar / fermentation_volume, fermentation_volume  # Return max ABV, sugar content in g/L, and total volume
    else:
        return 0, 0, fermentation_volume  # Avoid division by zero


def display_ingredient_calculator():
    st.title("Fermentation Ingredient Calculator")

    # Select vessel ID to load vessel information
    vessel_id = st.number_input("Vessel ID", min_value=1, step=1)

    with get_db() as db:
        vessel = db.query(Vessel).filter_by(id=vessel_id).first()
        if not vessel:
            st.error("No vessel found with the given ID.")
            return

        max_vessel_volume = vessel.volume_liters*units.L

        ingredients = db.query(Ingredient).all()

    st.write(f"Maximum Vessel Volume: {round(max_vessel_volume.asNumber(units.L), 3)} L")

    # Select ingredients
    ingredient_options = {ingredient.name: ingredient for ingredient in ingredients}
    selected_ingredient_names = st.multiselect("Select Ingredients", list(ingredient_options.keys()))

    selected_ingredients = []
    for name in selected_ingredient_names:
        ingredient = ingredient_options[name]
        col_unit, col_amount = st.columns([1, 3])
        unit = col_unit.selectbox(f"Unit for {ingredient.name}", options=["g", "mL"], key=f"{ingredient.id}_unit")
        
        amount = col_amount.number_input(f"Amount of {ingredient.name} ({unit})", min_value=0.0, step=1.0, key=f"{ingredient.id}_amount")
        selected_ingredients.append({
            'id': ingredient.id,
            'name': ingredient.name,
            'sugar_content': ingredient.sugar_content * (1.0 if ingredient.ingredient_type in ["Solute", "Solid"] else units.g/units.L),
            'amount': amount * str2unit[unit],
            'ingredient_type': ingredient.ingredient_type,
            'density': ingredient.density * units.kg/units.L,
        })

    # Calculate fermentation volume automatically from added ingredients
    if selected_ingredients:
        max_abv, max_sugar_content, fermentation_volume = calculate_max_potential_abv(selected_ingredients)

        # Display current volume taken up by added ingredients
        st.write(f"Current Total Volume: {fermentation_volume.asNumber(units.L)} liters")

        # Check if the maximum volume is exceeded
        if fermentation_volume > max_vessel_volume * 1000:
            st.error("Error: Total volume exceeds the maximum vessel volume!")
        elif fermentation_volume > 0.9 * max_vessel_volume * 1000:
            st.warning("Warning: Total volume is above 90% of the maximum vessel volume!")

        # Handle case where max_abv and max_sugar_content are both 0
        if max_abv == 0:
            st.error("No valid ingredients added to calculate ABV and sugar content.")
            return

        # Slider for the desired ABV
        desired_abv = st.slider("Desired ABV (%)", min_value=0.0, max_value=float(max_abv), step=0.1, key="desired_abv")

        # Calculate and display the resulting sugar content based on the desired ABV
        resulting_sugar_content = max_sugar_content - abv_to_sugar(desired_abv)
        st.write(f"**Resulting Sugar Content:** {resulting_sugar_content.asNumber(units.g/units.L):.2f} g/L")

        # Display maximum potential ABV and corresponding sugar content
        st.write(f"**Maximum Potential ABV:** {max_abv.asNumber():.2f}%")
        st.write(f"**Maximum Sugar Content:** {max_sugar_content.asNumber(units.g/units.L):.2f} g/L")

        fig, ax = plt.subplots()
        for item in BENCHMARK:
            if item['abv'] is None:
                ax.axhline(item['rs'].asNumber())
                ax.text(0, item['rs'].asNumber(), f"{item['name']}", color='black', verticalalignment='bottom')
            else:
                print(item['abv'], item['rs'].asNumber())
                ax.scatter(item['abv'], item['rs'].asNumber(), c='blue')
                ax.text(item['abv'], item['rs'].asNumber(), f"{item['name']}", color='black', verticalalignment='bottom')
        ax.scatter(desired_abv, resulting_sugar_content.asNumber(), c='green')
        ax.text(desired_abv, resulting_sugar_content.asNumber(), "Calculation", color='green', verticalalignment='bottom')
        ax.plot([0, max_abv], [max_sugar_content.asNumber(), 0], color='green', linestyle='--')
        ax.set_ylabel("Residual Sugar (g/L)")
        ax.set_xlabel("ABV (%)")
        ax.set_xlim([0, None])
        st.pyplot(fig)


tab_ingredient, tab_measurement, tab_rack, tab_bottle, tab_calc = st.tabs(["Ingredient", "Measurement", "Rack", "Bottle", "Calculator"])

with get_db() as db:
    with tab_ingredient:
        # Query and choose ingredient added
        ingredient_names = [i.name for i in db.query(Ingredient).order_by(asc(Ingredient.name)).all()]

        options = ingredient_names + ["*New Ingredient"]
        ingredient_name = st.selectbox("Ingredient Added", options=options)

        # Create text input for user entry
        if ingredient_name == "*New Ingredient": 
            add_new_ingredient(db)
        
        add_fermentation_ingredient(ingredient_name=ingredient_name)

        st.dataframe(all_ferm_ingredients_info(db)[::-1], hide_index=True)


    with tab_measurement:
        add_measurement_form(db)
        st.dataframe(all_measurement_info(db)[::-1], hide_index=True)

    with tab_rack:
        rack_form(db)
        st.dataframe(all_vessel_log_info(db)[::-1], hide_index=True)

    with tab_bottle:
        bottle_form(db)
        st.dataframe(all_bottle_info(db), hide_index=True)

    with tab_calc:
        display_ingredient_calculator()