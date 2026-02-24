import streamlit as st
import os

st.set_page_config(
    page_title="Document AI Hub",
    page_icon="🤖",
    layout="wide"
)

pages = {
    "Hub": [
        st.Page("app.py", title="Home", icon="🏠", default=True)
    ],
    "Portals": [
        st.Page("pages/1_user_chat.py", title="User Chat", icon="💬"),
        st.Page("pages/0_admin_upload.py", title="Admin Upload", icon="🛡️")
    ]
}

pg = st.navigation(pages)
pg.run()

# --- Everything below only runs on the Home Page ---
if pg.url_path == "":
    st.title("🤖 Welcome to the AI Document Hub")
    st.markdown("This is the main hub. From here, you can navigate to different parts of the application using the sidebar on the left.")

    # Create the knowledge base directory if it doesn't exist
    KB_DIR = "knowledge_base"
    if not os.path.exists(KB_DIR):
        os.makedirs(KB_DIR)
