import streamlit as st
import pandas as pd 

st.set_page_config(
    page_title="Mead Tracking",
)

# Create the SQL connection to pets_db as specified in your secrets file.
conn = st.connection('alcohol_db', type='sql')

if "page_state" not in st.session_state:
    st.session_state.page_state = 0

conn.session.execute("""CREATE TABLE IF NOT EXISTS brew 
                     (
                        mead_id int NOT NULL PRIMARY KEY, 
                        carboy_id int NOT NULL,
                        ferment_date date,
                        rack_date date,
                        bottle_date date,
                        water_mass float(2), 
                        other_liquid_name varchar(255),
                        other_liquid_mass float(2), 
                        honey_mass float(2),
                        init_specific_gravity float(4),
                        final_specific_gravity float(4),
                        notes varchar(255)
                     )""")

tab_form, tab_calc = st.tabs(["Form", "Calculator"])

with tab_form:
    if st.session_state.page_state == 0:
        with st.form("Brew Form"):
            mead_id = st.number_input("Mead ID", value=0, min_value=0, max_value=5, step=1)
            carboy_id = st.number_input("Carboy ID", value=0, min_value=0, max_value=6, step=1)
            ferment_date = st.date_input("Fermentation Start")
            rack_date = st.date_input("Rack Date")
            bottle_date = st.date_input("Bottle Date")
            carboy_id = st.number_input("Carboy ID", value=0, min_value=0, max_value=None, step=1)
            water_mass = st.number_input("Water Mass", value=0.0, min_value=0.0)
            other_liquid_name = st.text_input("Other Liquid Name")
            other_liquid_mass = st.number_input("Other Liquid Mass", value=0.0, min_value=0.0)
            honey_mass = st.number_input("Honey Mass", value=0.0, min_value=0.0)
            init_specific_gravity = st.number_input("Initial Specific Gravity", value=1.0, min_value=0.0)
            final_specific_gravity = st.number_input("Final Specific Gravity", value=0.0, min_value=0.0)
            notes = st.text_input("Additional Notes")

            if st.form_submit_button('Submit'):
                with conn.session as s:
                    s.execute(f"""INSERT INTO brew VALUES (
                            {mead_id}, 
                            {carboy_id}, 
                            {ferment_date}, 
                            {rack_date}, 
                            {bottle_date}, 
                            {water_mass}, 
                            {other_liquid_name}, 
                            {other_liquid_mass}, 
                            {honey_mass}, 
                            {init_specific_gravity},
                            {final_specific_gravity},
                            {notes});"""
                            )
                    s.commit()
    elif st.session_state.page_state == 1:
        st.markdown("Form Submitted")

        if st.button("Submit Another"):
            st.session_state.page_state = 0
            st.rerun()

    conn.reset()
    tasting_table = conn.query("SELECT * FROM tasting;")
    st.dataframe(tasting_table, use_container_width=True)

with tab_calc:
    max_volume = st.number_input(label="Total Volume (L)", value=1.750)

    col1, col2, col3 = st.columns((8, 1, 8))
    honey_sugar = col1.number_input(label="Honey Sugar (g)", value=17)
    col2.markdown("# /")
    honey_sugar = honey_sugar/col3.number_input(label="(L)", value=0.0147868)
    honey_density = st.number_input(label="Honey Density (g/L)", value=21/0.0147868)

    liquid_sugar = st.number_input(label="Liquid Sugar (g/L)", value=29/0.236588)
    liquid_density = st.number_input(label="Liquid Density (g/L)", value=1026)

    target_abv = st.number_input(label="Target ABV (%)", value=9) # in %
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