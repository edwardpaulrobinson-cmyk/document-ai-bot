import streamlit as st
from google import genai
import os
import time
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Admin Uploads", page_icon="🛡️")

st.title("🛡️ Staff / Admin Portal")
st.markdown("Upload documents here. These will be securely stored in the Gemini cloud for users to ask questions about.")

# Initialize Gemini Client
@st.cache_resource
def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except (FileNotFoundError, KeyError):
            return None
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

client = get_client()

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
    
if not client:
    st.error("API Key not found!")
    st.stop()

st.success("Authenticated as Staff.")

st.subheader("1. Upload New Document(s)")
uploaded_files = st.file_uploader(
    "Choose files", type=["pdf", "png", "jpg", "jpeg", "doc", "docx"], accept_multiple_files=True
)

if uploaded_files:
    for uploaded_file in uploaded_files:
        with st.spinner(f"Uploading {uploaded_file.name} to Gemini..."):
            # Save to temporary file first
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            try:
                # Upload to Gemini File API
                uploaded_doc = client.files.upload(file=temp_path, config={"display_name": uploaded_file.name})
                st.success(f"✅ Successfully added **{uploaded_file.name}** to the knowledge base!")
            except Exception as e:
                st.error(f"Failed to upload {uploaded_file.name}: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

st.markdown("---")
st.subheader("2. Current Knowledge Base")

with st.spinner("Fetching documents from Gemini..."):
    # List all files currently stored in Gemini
    gemini_files = []
    try:
        gemini_files = list(client.files.list())
    except Exception as e:
        if "400" in str(e) or "API_KEY_INVALID" in str(e) or "expired" in str(e).lower():
            st.error("Your new API key is invalid or hasn't activated yet. Please check Google AI Studio.")
        elif "429" in str(e):
            st.error("Rate Limit Reached: Cannot fetch documents right now. Please wait 1 minute.")
        else:
            st.error(f"Error fetching documents: {e}")

if not gemini_files:
    st.info("No documents uploaded yet.")
else:
    for g_file in gemini_files:
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.write(f"📄 {g_file.display_name or g_file.name}")
        with col2:
            if st.button("Delete", key=f"del_{g_file.name}"):
                client.files.delete(name=g_file.name)
                st.rerun()
