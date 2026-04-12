import streamlit as st

from alcopt.auth import require_admin
from alcopt.labels import DEFAULT_BASE_URL, generate_label_pdf

require_admin()

st.title("Container Labels")
st.caption(
    "Generate a printable PDF of QR-code labels for an inclusive range of "
    "container IDs. Each QR links to the container's Information page."
)

min_col, max_col = st.columns(2)
with min_col:
    min_id = st.number_input("Min container ID", min_value=1, value=1, step=1)
with max_col:
    max_id = st.number_input("Max container ID", min_value=1, value=12, step=1)

base_url = st.text_input(
    "Base URL",
    value=DEFAULT_BASE_URL,
    help="Override only if you're testing against a different deployment.",
)

if max_id < min_id:
    st.error("Max ID must be greater than or equal to Min ID.")
    st.stop()

container_ids = list(range(int(min_id), int(max_id) + 1))
st.caption(f"{len(container_ids)} labels · 12 per page")

if st.button("Generate PDF", type="primary"):
    st.session_state["labels_pdf"] = generate_label_pdf(
        container_ids, base_url=base_url
    )

if "labels_pdf" in st.session_state:
    st.download_button(
        "Download container_labels.pdf",
        data=st.session_state["labels_pdf"],
        file_name="container_labels.pdf",
        mime="application/pdf",
    )
