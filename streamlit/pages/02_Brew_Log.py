import streamlit as st
import pandas as pd 
from datetime import datetime
import cv2
import numpy as np
import streamlit as st

# SQL
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy_models import Fermentation, SpecificGravityMeasurement, FermentationIngredient, Ingredient, Vessel, FermentationVesselLog

st.set_page_config(
    page_title="Brew Tracking",
)
if "new_ingredients" not in st.session_state:
    st.session_state.new_ingredients = []


def add_new_ingredient():
    with st.form("Add New Ingredient"):
        ingredient_name = st.text_input("New Ingredient Name")
        sugar_content = st.number_input("Sugar Content (g/L)", value=0.0)
        ingredient_type = st.radio("Type", ["Liquid", "Solvent", "Solid"])
        density = st.number_input("Density (kg/L)", value=1.0)
        price = st.number_input("Price ($)", value=0.00)
        notes = st.text_input("Additional Notes")
        if st.form_submit_button('Add'):
            if ingredient_name is not None and ingredient_name != "":
                try:
                    session = Session()
                    new_ingredient = Ingredient(name=ingredient_name, sugar_content=sugar_content, ingredient_type=ingredient_type, density=density, price=price, notes=notes)
                    session.add(new_ingredient)
                    session.commit()
                    session.close()
                except Exception as e:
                    # st.error("Ingredient already in table!!")
                    st.error(e)


def add_fermentation():
    with st.form("Add Ingredient"):
        if st.form_submit_button('Add'):
            try:
                session = Session()
                new_fermentation = Fermentation(start_date=datetime.now(), initial_specific_gravity=1.080)
                session.add(new_fermentation)
                session.commit()
                print("Fermentation added successfully with ID:", new_fermentation.id)
                session.close()
                return new_fermentation.id
            except Exception as e:
                st.error(f"Error {e}")


def add_fermentation_vessel_log(vessel_id, fermentation_id):
    with st.form("Add Ingredient"):
        if st.form_submit_button('Add'):
            try:
                session = Session()
                vessel_log = FermentationVesselLog(
                    fermentation_id=fermentation_id,
                    vessel_id=vessel_id,
                    start_date=datetime.now()
                )
                session.add(vessel_log)
                session.commit()
                print("Fermentation Vessel Log added successfully with ID:", vessel_log.id)
                session.close()
                return vessel_log.id
            except Exception as e:
                st.error(f"Error {e}")


def add_fermentation_ingredient(ingredient_name=None):
    """Add Ingredient to a fermentation"""
    with st.form("Add Ingredient"):
        session = Session()
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
                vessel = session.query(Vessel).filter_by(id=vessel_id).first()
                if vessel is None:
                    st.error(f"Vessel {vessel_id} not found")
                else:
                    fermentation_id = vessel.fermentation_id
                    if fermentation_id is None:
                        new_fermentation = Fermentation(start_date=date)
                        session.add(new_fermentation)
                        session.commit()
                        fermentation_id = new_fermentation.id
                        st.success(f"Created New Fermentation <{fermentation_id}>")

                        vessel_log = FermentationVesselLog(
                            fermentation_id=fermentation_id,
                            vessel_id=vessel_id,
                            start_date=date
                        )
                        session.add(vessel_log)
                        session.commit()
                        st.success(f"Created New Fermentation Vessel Log <{vessel_log.id}>")

                        # Update the fermentation_id of the vessel
                        vessel.fermentation_id = fermentation_id
                        session.commit()
                        st.success(f"Fermentation ID updated successfully for Vessel ID: {vessel_id}")
                    ingredient_id = session.query(Ingredient).filter_by(name=ingredient_name).first().id
                    new_ferm_ingredient = FermentationIngredient(
                        fermentation_id=fermentation_id, 
                        ingredient_id=ingredient_id, 
                        amount=amount, 
                        unit=unit,
                        added_at=date)
                    session.add(new_ferm_ingredient)
                    session.commit()
                    st.success(f"Created New Fermentation Ingredient <{new_ferm_ingredient.id}>")
                    return new_fermentation.id
            except Exception as e:
                st.error(f"Error {e}")
        session.close()

def add_measurement_form():
    st.title("Add Specific Gravity Measurement")

    with st.form(key='measurement_form'):
        fermentation_id = st.number_input("Fermentation ID", min_value=1, step=1)
        measurement_date = st.date_input("Measurement Date", value=datetime.now())
        specific_gravity = st.number_input("Specific Gravity", value=.999, min_value=0.0, step=0.001, format="%.3f")

        submit_button = st.form_submit_button(label='Add Measurement')

    if submit_button:
        try:
            # Add new specific gravity measurement
            new_measurement = SpecificGravityMeasurement(
                fermentation_id=fermentation_id,
                measurement_date=measurement_date,
                specific_gravity=specific_gravity
            )
            session.add(new_measurement)
            session.commit()
            st.success(f"Measurement added successfully for Fermentation ID: {fermentation_id}")
        except Exception as e:
            st.error(f"An error occurred: {e}")
            session.rollback()
        finally:
            session.close()

def rack_form():
    with st.form(key='rack_form'):
        col_from, col_to = st.columns((1, 1))
        from_vessel_id = col_from.number_input("From Vessel ID", value=1, min_value=1, step=1)
        to_vessel_id = col_to.number_input("To Vessel ID", value=1, min_value=1, step=1)
        date = st.date_input("Date")
        submit_button = st.form_submit_button(label='Add Action')

    if submit_button:
        try:
            from_vessel = session.query(Vessel).filter_by(id=from_vessel_id).first()
            to_vessel = session.query(Vessel).filter_by(id=to_vessel_id).first()
            vessel_log = FermentationVesselLog(
                fermentation_id=from_vessel.fermentation_id,
                vessel_id=to_vessel.id,
                start_date=date
            )
            session.add(vessel_log)
            session.commit()
            to_vessel.fermentation_id = from_vessel.fermentation_id
            from_vessel.fermentation_id = None
            session.commit()
            st.success(f"Racked from {from_vessel.id} to {to_vessel.id}")
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            session.close()


engine = create_engine('sqlite:///wine_mead.db')
Session = sessionmaker(bind=engine)
session = Session()

fermentation_ingredients = session.query(FermentationIngredient).all()
fermentation_ingredients_list = [
    {
    "ID": fermentation_ingredient.id,
    "Amount": fermentation_ingredient.amount,
    "Unit": fermentation_ingredient.unit,
    "Date Added": fermentation_ingredient.added_at,
    "Fermentation ID": fermentation_ingredient.fermentation_id
    }
    for fermentation_ingredient in fermentation_ingredients
]
fermentation_ingredients = pd.DataFrame(fermentation_ingredients_list)

tab_ingredient, tab_measurement, tab_rack, tab_calc = st.tabs(["Ingredient", "Measurement", "Rack", "Calculator"])

with tab_ingredient:
    session = Session()

    # Query and choose ingredient added
    ingredient_names = [i.name for i in session.query(Ingredient).order_by(asc(Ingredient.name)).all()]

    options = ingredient_names + ["*New Ingredient"]
    ingredient_name = st.selectbox("Ingredient Added", options=options)

    # Create text input for user entry
    if ingredient_name == "*New Ingredient": 
        add_new_ingredient()
    
    add_fermentation_ingredient(ingredient_name=ingredient_name)

    st.dataframe(fermentation_ingredients[::-1], use_container_width=True, hide_index=True)

#             specific_gravity = st.number_input("Specific Gravity", value=1.010, min_value=.990, step=.001)
#             notes = st.text_input("Brew Notes")
#             if st.button("Finish"):
#                 insert_row(conn, "brew", mead_id, carboy_id, date, specific_gravity, notes)
#         elif carboy_state == "Secondary Fermentation": 
#             pass
#         elif carboy_state == "Rack/Age": 
#             if final_specific_gravity is not None:
#                 st.markdown(f"~ABV: {(init_specific_gravity - final_specific_gravity) * 131.25}")
#                 final_brix = 143.254 * final_specific_gravity**3 - 648.670 * final_specific_gravity**2 + 1125.805 * final_specific_gravity - 620.389
#                 st.markdown(f"~Brix: {final_brix}")
#                 st.markdown(f"~RS: {98*final_brix}") 
#                 # st.markdown(f"~g/L: {98*final_brix/(water_mass+other_liquid_mass+)}")

#         st.dataframe(carboy_history)
    # elif st.session_state.page_state == 1:
    #     st.markdown("Form Submitted")

    #     if st.button("Submit Another"):
    #         st.session_state.page_state = 0
    #         st.rerun()
with tab_measurement:
    add_measurement_form()

with tab_rack:
    rack_form()

with tab_calc:
    max_volume = st.number_input(label="Total Volume (L)", value=1.750)

    col1, col2, col3 = st.columns((8, 1, 8))
    honey_sugar = col1.number_input(label="Honey Sugar (g)", value=17)
    col2.markdown("# /")
    honey_sugar = honey_sugar/col3.number_input(label="(L)", value=0.0147868, step=0.00001)
    honey_density = st.number_input(label="Honey Density (g/L)", value=21/0.0147868)

    col1, col2, col3 = st.columns((8, 1, 8))
    liquid_sugar = col1.number_input(label="Liquid Sugar (g)", value=29)
    col2.markdown("# /")
    liquid_sugar = liquid_sugar/col3.number_input(label="(L)", value=0.236588, step=0.00001)
    liquid_density = st.number_input(label="Liquid Density (g/L)", value=1026)

    target_abv = st.number_input(label="Target ABV (%)", value=12, help="Beer 5, Moscato 5-6, Riesling 8-8.5, Champagne 11, Pinot Noir 11.5-13.5") # in %
    sugar_per_abv = st.number_input(label="Sugar/ABV", value=17)

    target_sugar = target_abv * sugar_per_abv * max_volume

    honey_vol = (target_sugar-max_volume*liquid_sugar)/(honey_sugar-liquid_sugar)
    liquid_vol = max_volume - honey_vol

    printout_data = [
        {"Parameter": "max_volume", "Value": max_volume}, 
        {"Parameter": "honey_sugar", "Value": honey_sugar}, 
        {"Parameter": "honey_density", "Value": honey_density}, 
        {"Parameter": "liquid_sugar", "Value": liquid_sugar}, 
        {"Parameter": "liquid_density", "Value": liquid_density}, 
        {"Parameter": "target_abv", "Value": target_abv}, 
        {"Parameter": "sugar_per_abv", "Value": sugar_per_abv}, 
        {"Parameter": "target_sugar", "Value": target_sugar}, 
        {"Parameter": "L Liquid", "Value": liquid_vol}, 
        {"Parameter": "g Liquid", "Value": liquid_vol * liquid_density}, 
        {"Parameter": "L Honey", "Value": honey_vol}, 
        {"Parameter": "g Honey", "Value": honey_vol * honey_density}, 
        ]

    printout = pd.DataFrame(printout_data)
    st.dataframe(printout, hide_index=True)