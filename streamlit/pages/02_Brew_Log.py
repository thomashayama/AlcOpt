import streamlit as st

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
                        bottle_num int NOT NULL,
                        ferment_date date,
                        rack_date date,
                        bottle_date date,
                        name varchar(255), 
                        water_mass float(2), 
                        honey_mass float(2),
                        init_specific_gravity float(4),
                        final_specific_gravity float(4),
                        notes varchar(255)
                     )""")

if st.session_state.page_state == 0:
    with st.form("my_form"):
        date = st.date_input("Tasting Date")
        date = st.date_input("Tasting Date")
        mead_id = st.number_input("Mead ID", value=0, min_value=0, max_value=5, step=1)
        rating = st.slider("Overall Rating", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        bold = st.slider("Light to Bold", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        tannic = st.slider("Smooth to Tannic", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        sweet = st.slider("Dry to Sweet", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        acidic = st.slider("Soft to Acidic", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        complexity = st.slider("Simple to Complex", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        notes = st.text_input("Additional Notes")

        if st.form_submit_button('Submit'):
            with conn.session as s:
                s.execute(f"INSERT INTO brew VALUES ({mead_id}, '{name}', {rating}, {bold}, {tannic}, {sweet}, {acidic}, {complexity});")
                s.commit()
elif st.session_state.page_state == 1:
    st.markdown("Form Submitted")

    if st.button("Submit Another"):
        st.session_state.page_state = 0
        st.rerun()