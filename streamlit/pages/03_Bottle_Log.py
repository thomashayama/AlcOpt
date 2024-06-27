import streamlit as st

st.set_page_config(
    page_title="Bottle Tracking",
)

# Create the SQL connection to pets_db as specified in your secrets file.
conn = st.connection('alcohol_db', type='sql')

if "page_state" not in st.session_state:
    st.session_state.page_state = 0
if "last_data" not in st.session_state:
    st.session_state.last_data = {}

conn.session.execute("""CREATE TABLE IF NOT EXISTS bottle 
                     (
                        carboy_id int NOT NULL,
                        mead_id int,
                        bottle_id int NOT NULL,
                        bottle_date date NOT NULL,
                        CHECK (FirstIdentifier IS NOT NULL OR SecondIdentifier IS NOT NULL),
                        PRIMARY KEY (bottle_id, bottle_date)
                     )""")

if st.session_state.page_state == 0:
    with st.form("my_form"):
        col_mead, carboy_carboy = st.columns((1, 1))
        mead_id = col_mead.number_input("Mead ID", value=st.session_state.last_data.get("mead_id", -1), min_value=-1, max_value=8, step=1)
        carboy_id = carboy_carboy.number_input("Carboy ID", value=st.session_state.last_data.get("carboy_id", -1), min_value=-1, max_value=5, step=1)
        bottle_id = st.number_input("Carboy ID", value=st.session_state.last_data.get("carboy_id", -1), min_value=-1, max_value=5, step=1)
        date = st.date_input("Bottling Date")

        if st.form_submit_button('Submit'):
            # Check if valid


            with conn.session as s:
                s.execute(f"""INSERT INTO tasting VALUES (
                          {carboy_id}, 
                          {mead_id}, 
                          {bottle_id}, 
                          {date});""")
                s.commit()
            st.session_state.page_state = 1
            st.session_state.last_data["mead_id"] = mead_id
            st.session_state.last_data["carboy_id"] = carboy_id
elif st.session_state.page_state == 1:
    st.markdown("Form Submitted")

    if st.button("Submit Another"):
        st.session_state.page_state = 0
        st.rerun()