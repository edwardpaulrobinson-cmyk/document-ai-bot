import streamlit as st
import os
import time

st.set_page_config(page_title="Admin Uploads", page_icon="🛡️")

st.title("🛡️ Staff / Admin Portal")
st.markdown("Upload documents here. These will be added to the local knowledge base for users to ask questions about.")

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
    
st.success("Authenticated as Staff.")

st.subheader("1. Upload New Document(s)")
uploaded_files = st.file_uploader(
    "Choose files", type=["pdf", "png", "jpg", "jpeg", "doc", "docx"], accept_multiple_files=True
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        with st.spinner(f"Saving {uploaded_file.name}..."):
            file_path = os.path.join(KB_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ Successfully added **{uploaded_file.name}** to the knowledge base!")

st.markdown("---")
st.subheader("2. Current Knowledge Base")

files_in_kb = os.listdir(KB_DIR)

if not files_in_kb:
    st.info("No documents uploaded yet.")
else:
    for f_name in files_in_kb:
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.write(f"📄 {f_name}")
        with col2:
            if st.button("Delete", key=f"del_{f_name}"):
                os.remove(os.path.join(KB_DIR, f_name))
                st.rerun()
