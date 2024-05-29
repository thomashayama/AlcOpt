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
                        bottle_id int NOT NULL PRIMARY KEY,
                        bottle_number int,
                        mead_id
                     )""")

if st.session_state.page_state == 0:
    with st.form("my_form"):
        name = st.text_input("Name")
        mead_id = st.number_input("Mead ID", value=0, min_value=0, max_value=5, step=1)
        rating = st.slider("Overall Rating", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        bold = st.slider("Light to Bold", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        tannic = st.slider("Smooth to Tannic", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        sweet = st.slider("Dry to Sweet", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        acidic = st.slider("Soft to Acidic", value=3.0, min_value=1.0, max_value=5.0, step=.1)
        complexity = st.slider("Simple to Complex", value=3.0, min_value=1.0, max_value=5.0, step=.1)

        if st.form_submit_button('Submit'):
            with conn.session as s:
                s.execute(f"""INSERT INTO tasting VALUES (
                          {mead_id}, 
                          '{name}', 
                          {rating}, 
                          {bold}, 
                          {tannic}, 
                          {sweet}, 
                          {acidic}, 
                          {complexity});""")
                s.commit()
elif st.session_state.page_state == 1:
    st.markdown("Form Submitted")

    if st.button("Submit Another"):
        st.session_state.page_state = 0
        st.rerun()