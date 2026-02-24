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
    # Check for documents
    KB_DIR = "knowledge_base"
    if not os.path.exists(KB_DIR):
        os.makedirs(KB_DIR)
    
    docs = [f for f in os.listdir(KB_DIR) if os.path.isfile(os.path.join(KB_DIR, f))]
    doc_count = len(docs)
    status_color = "green" if doc_count > 0 else "red"
    
    st.markdown(
        f"**STATUS: <span style='color:{status_color}'>{'ONLINE' if doc_count > 0 else 'EMPTY'}</span>**\n\n"
        f"Currently Indexing: **{doc_count} Documents**\n\n"
        "Welcome to the core interface. Use the sidebar to navigate.\n\n"
        "- **Data Ingestion:** Upload and parse knowledge base documents.\n"
        "- **Query Interface:** Access the dynamic Multi-API Waterfall Router."
    , unsafe_allow_html=True)

    # We now store files locally again because the previous Cloud Storage API had persistence issues
    KB_DIR = "knowledge_base"
    if not os.path.exists(KB_DIR):
        os.makedirs(KB_DIR)
