import streamlit as st
import os

st.set_page_config(
    page_title="Document AI Hub",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Welcome to the AI Document Hub")
st.markdown("This is the main hub. From here, you can navigate to different parts of the application.")

st.markdown("### 🧑‍💻 For Users")
st.markdown("Click on **User Chat** in the sidebar to ask questions about the documents our staff have uploaded.")

st.markdown("---")
st.markdown("### 🛡️ For Staff")
st.markdown("Click on **Admin Upload** in the sidebar to manage the knowledge base.")

# Create the knowledge base directory if it doesn't exist
KB_DIR = "knowledge_base"
if not os.path.exists(KB_DIR):
    os.makedirs(KB_DIR)
