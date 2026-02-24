import streamlit as st
from google import genai
from google.genai import types
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Document AI Bot",
    page_icon="🤖",
    layout="wide"
)

# Initialize Gemini Client
@st.cache_resource
def get_client():
    # Try getting from environment first (local), then Streamlit secrets (cloud)
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

st.title("🤖 Multimodal Document Chatbot")
st.markdown("Upload a document (**PDF, PNG, JPG**) and chat with it! The AI will naturally converse about the text and images inside.")

if not client:
    st.error("Please set your `GEMINI_API_KEY` in the `.env` file (local) or in **Streamlit secrets** (deployed).")
    st.info("Get a free API key from [Google AI Studio](https://aistudio.google.com/).")
    st.stop()

# Sidebar for document upload
with st.sidebar:
    st.header("1. Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a file", type=["pdf", "png", "jpg", "jpeg"]
    )
    if uploaded_file:
        st.success(f"File uploaded: {uploaded_file.name}")
        
    st.markdown("---")
    st.markdown("### How it works")
    st.markdown("1. Upload a document on the left.")
    st.markdown("2. Type your question in the chat box.")
    st.markdown("3. The AI reads text AND sees images in the document to answer contextually.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize document reference
if "uploaded_doc_ref" not in st.session_state:
    st.session_state.uploaded_doc_ref = None
if "current_file_name" not in st.session_state:
    st.session_state.current_file_name = None

# Process newly uploaded file
if uploaded_file and uploaded_file.name != st.session_state.current_file_name:
    with st.spinner("Processing document for the AI..."):
        temp_file_path = f"temp_{uploaded_file.name}"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        try:
            # Upload to Gemini File API
            uploaded_doc = client.files.upload(file=temp_file_path)
            
            # Wait for processing if it's a PDF
            if temp_file_path.lower().endswith(".pdf"):
                while uploaded_doc.state.name == "PROCESSING":
                    time.sleep(2)
                    uploaded_doc = client.files.get(name=uploaded_doc.name)
            
            st.session_state.uploaded_doc_ref = uploaded_doc
            st.session_state.current_file_name = uploaded_file.name
            st.toast("Document processed and ready!")
            
            # Clear previous chat
            st.session_state.messages = []
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"I've read **{uploaded_file.name}**. What would you like to know about it?"
            })
            
        except Exception as e:
            st.error(f"Error processing file: {e}")
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about your document..."):
    # Add user message to UI
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Prepare contents
            contents = []
            
            # Always pass the document if it exists to maintain full context
            if st.session_state.uploaded_doc_ref:
                contents.append(st.session_state.uploaded_doc_ref)
                
            # Construct a conversation history string for the model to follow
            conversation_history = "Conversation History:\n"
            for msg in st.session_state.messages[:-1]: # exclude the current prompt
                role_label = "User" if msg["role"] == "user" else "Assistant"
                conversation_history += f"{role_label}: {msg['content']}\n"
                
            conversation_history += f"\nUser: {prompt}\n"
            
            # Ensure the model gives a natural, human-like response
            system_instruction = (
                "You are a helpful, conversational AI assistant analyzing a provided document. "
                "The user is asking questions about the document. "
                "Respond in a natural, human-like way. Be concise and directly answer their question. "
                "Do not summarize the entire document unprompted. Use markdown for formatting tables or lists if necessary."
            )
            
            contents.append(conversation_history)

            # Generate streaming content
            response = client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                )
            )

            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # Add assistant response to state
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
