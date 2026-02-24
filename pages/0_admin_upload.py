import streamlit as st
import os
import time

st.set_page_config(page_title="Data Ingestion")

st.title("DATA INGESTION")
st.markdown("Upload documents here to index them into the local knowledge base.")

KB_DIR = "knowledge_base"
if not os.path.exists(KB_DIR):
    os.makedirs(KB_DIR)

# Basic password protection
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.warning("Please enter the admin password to upload files.")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if pwd == "admin123":
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()
    
st.success("Authentication successful.")

st.subheader("1. Ingest New Documents")
uploaded_files = st.file_uploader(
    "Select files", type=["pdf", "png", "jpg", "jpeg", "doc", "docx"], accept_multiple_files=True
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        with st.spinner(f"Ingesting {uploaded_file.name}..."):
            file_path = os.path.join(KB_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Indexed: {uploaded_file.name}")

st.markdown("---")
st.subheader("2. Active Knowledge Base")

files_in_kb = os.listdir(KB_DIR)

if not files_in_kb:
    st.info("Knowledge base is empty.")
else:
    for f_name in files_in_kb:
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.write(f"{f_name}")
        with col2:
            if st.button("Delete", key=f"del_{f_name}"):
                os.remove(os.path.join(KB_DIR, f_name))
                st.rerun()
