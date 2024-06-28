import streamlit as st
import pandas as pd 
import datetime
import cv2
import numpy as np
import streamlit as st

# SQL
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy_models import Fermentation, Bottle, Review

st.set_page_config(
    page_title="Mead Tracking",
)
if "new_ingredients" not in st.session_state:
    st.session_state.new_ingredients = []


def insert_row(conn, table_name, *args, verbose=False):
    def process_col_val(col):
        if col is None:
            return 'NULL'
        if isinstance(col, str) or isinstance(col, datetime.date):
            return f"'{col}'"
        else:
            return str(col)
    columns = ', '.join([process_col_val(col) for col in args])
    with conn.session as s:
        sql_command = f"INSERT INTO {table_name} VALUES ({columns});"
        if verbose: print(sql_command)
        s.execute(sql_command)
        s.commit()

# Create the SQL connection to pets_db as specified in your secrets file.
# conn = st.connection('alcohol_db', type='sql')
engine = create_engine('sqlite:///wine_mead.db')
Session = sessionmaker(bind=engine)

if "page_state" not in st.session_state:
    st.session_state.page_state = 0

tab_new_form, tab_update, tab_calc = st.tabs(["New Form", "Update", "Calculator"])

with tab_update:
    if st.session_state.page_state == 0:
        # Select Action
        

        if carboy_state == "Primary Fermentation":
            # image = st.camera_input("Show QR code")
            # if image is not None:
            #     bytes_data = image.getvalue()
            #     cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

            #     detector = cv2.QRCodeDetector()

            #     data, bbox, straight_qrcode = detector.detectAndDecode(cv2_img)

            #     st.write(data)

            col_carboy, col_mead = st.columns((1, 1))
            carboy_id = col_carboy.number_input("Carboy ID", value=0, min_value=0, max_value=6, step=1)
            carboy_history_table = conn.query(f"SELECT * FROM carboy WHERE carboy_id = {carboy_id} ORDER BY date_added;")
            
            mead_id = col_mead.number_input("Mead ID", value=None, min_value=0, max_value=5, step=1)
            
            # Query and choose ingredient added
            ingredients_history_table = conn.query(f"SELECT name FROM ingredient")
            options = list(ingredients_history_table.loc[:, "name"]) + st.session_state.new_ingredients + ["*New Ingredient"]
            ingredient_name = st.selectbox("Ingredient Added", options=options)

            # Create text input for user entry
            if ingredient_name == "*New Ingredient": 
                with st.form("Add New Ingredient"):
                    ingredient_name = st.text_input("New Ingredient Name")
                    sugar_content = st.text_input("Sugar Content (g/L)")
                    density = st.text_input("Density (kg/L)")
                    notes = st.text_input("Additional Notes")
                    if st.form_submit_button('Add'):
                        if ingredient_name is not None and ingredient_name != "":
                            try:
                                insert_row(conn, "ingredient", ingredient_name, sugar_content, density, notes)
                                st.session_state.new_ingredients.append(ingredient_name)
                            except:
                                st.error("Ingredient already in table!!")
            
            with st.form("Add Ingredient"):
                date = st.date_input("Date")
                col_start, col_end = st.columns([1, 1])
                start_mass = col_start.number_input("Starting Mass", value=0.0, min_value=0.0)
                end_mass = col_end.number_input("Ending Mass", value=0.0, min_value=0.0)
                ingredient_mass = end_mass - start_mass
                notes = st.text_input("Ingredient Add Notes")

                if st.form_submit_button('Submit Action'):
                    insert_row(conn, "brew", mead_id, carboy_id, date, ingredient_name, ingredient_mass, notes)


            specific_gravity = st.number_input("Specific Gravity", value=1.010, min_value=.990, step=.001)
            notes = st.text_input("Brew Notes")
            if st.button("Finish"):
                insert_row(conn, "brew", mead_id, carboy_id, date, specific_gravity, notes)
        elif carboy_state == "Secondary Fermentation": 
            pass
        elif carboy_state == "Rack/Age": 
            if final_specific_gravity is not None:
                st.markdown(f"~ABV: {(init_specific_gravity - final_specific_gravity) * 131.25}")
                final_brix = 143.254 * final_specific_gravity**3 - 648.670 * final_specific_gravity**2 + 1125.805 * final_specific_gravity - 620.389
                st.markdown(f"~Brix: {final_brix}")
                st.markdown(f"~RS: {98*final_brix}") 
                # st.markdown(f"~g/L: {98*final_brix/(water_mass+other_liquid_mass+)}")
        elif carboy_state == "Bottle": 
            pass
        elif carboy_state == "Empty": 
            pass

        st.dataframe(carboy_history_table)
    elif st.session_state.page_state == 1:
        st.markdown("Form Submitted")

        if st.button("Submit Another"):
            st.session_state.page_state = 0
            st.rerun()


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