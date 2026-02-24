import streamlit as st
import os

st.set_page_config(
    page_title="System Hub",
    layout="wide"
)

pages = {
    "Hub": [
        st.Page("app.py", title="System Terminal", default=True)
    ],
    "Portals": [
        st.Page("pages/1_user_chat.py", title="Query Interface"),
        st.Page("pages/0_admin_upload.py", title="Data Ingestion")
    ]
}

pg = st.navigation(pages)
pg.run()

# --- Everything below only runs on the Home Page ---
if pg.url_path == "":
    st.title("SYSTEM HUB")
    st.markdown(
        "**STATUS: ONLINE**\n\n"
        "Welcome to the core interface. Use the sidebar to navigate.\n\n"
        "- **Data Ingestion:** Upload and parse knowledge base documents.\n"
        "- **Query Interface:** Access the GLM-4v large language model."
    )

    # We now store files locally again because OpenRouter doesn't have a Cloud Storage API
    KB_DIR = "knowledge_base"
    if not os.path.exists(KB_DIR):
        os.makedirs(KB_DIR)
