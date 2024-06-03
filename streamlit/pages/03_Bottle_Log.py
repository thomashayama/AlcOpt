import streamlit as st

st.set_page_config(
    page_title="Bottle Tracking",
)

# Create the SQL connection to pets_db as specified in your secrets file.
conn = st.connection('alcohol_db', type='sql')

if "page_state" not in st.session_state:
    st.session_state.page_state = 0

conn.session.execute("""CREATE TABLE IF NOT EXISTS bottle 
                     (
                        carboy_id int NOT NULL PRIMARY KEY,
                        bottle_id int,
                        mead_id int,
                        bottle_date date
                     )""")

if st.session_state.page_state == 0:
    with st.form("my_form"):
        name = st.text_input("Name")
        col_mead, carboy_carboy = st.columns((1, 1))
        mead_id = col_mead.number_input("Mead ID", value=0, min_value=0, max_value=8, step=1)
        carboy_id = carboy_carboy.number_input("Carboy ID", value=0, min_value=0, max_value=5, step=1)
        date = st.date_input("Bottling Date")

        if st.form_submit_button('Submit'):
            with conn.session as s:
                s.execute(f"""INSERT INTO tasting VALUES (
                          {carboy_id}, 
                          {mead_id}, 
                          {carboy_id}, 
                          {date});""")
                s.commit()
elif st.session_state.page_state == 1:
    st.markdown("Form Submitted")

    if st.button("Submit Another"):
        st.session_state.page_state = 0
        st.rerun()