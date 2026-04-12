import streamlit as st

from alcopt.auth import is_admin, show_login_status
from alcopt.database.models import Container
from alcopt.database.utils import get_db
from alcopt.labels import DEFAULT_BASE_URL, generate_label_pdf

st.set_page_config(
    page_title="Container Labels",
    page_icon="🍷",
)

token = show_login_status()
if not token:
    st.warning("Please log in to access this page.")
    st.stop()
if not is_admin():
    st.warning("Admin access required.")
    st.stop()

st.title("Container Labels")
st.caption(
    "Generate a printable PDF of QR-code labels. Each QR links to the "
    "container's Information page."
)

with get_db() as db:
    containers = (
        db.query(Container).order_by(Container.container_type, Container.id).all()
    )

if not containers:
    st.info("No containers in the database yet.")
    st.stop()

option_labels = {
    f"#{c.id} — {c.container_type} ({c.volume_liters} L)": c.id for c in containers
}

selected = st.multiselect(
    "Containers to print",
    options=list(option_labels.keys()),
    default=list(option_labels.keys()),
)
selected_ids = [option_labels[label] for label in selected]

base_url = st.text_input(
    "Base URL",
    value=DEFAULT_BASE_URL,
    help="Override only if you're testing against a different deployment.",
)

st.caption(f"{len(selected_ids)} labels selected · 12 per page")

if st.button("Generate PDF", type="primary", disabled=not selected_ids):
    pdf_bytes = generate_label_pdf(selected_ids, base_url=base_url)
    st.session_state["labels_pdf"] = pdf_bytes

if "labels_pdf" in st.session_state:
    st.download_button(
        "Download container_labels.pdf",
        data=st.session_state["labels_pdf"],
        file_name="container_labels.pdf",
        mime="application/pdf",
    )
