import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError
import os
import time
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="User Chat", page_icon="💬", layout="wide")

st.title("💬 Ask the Document Bot")
st.markdown("I can answer questions based on the documents uploaded by the staff.")

KB_DIR = "knowledge_base"

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
if not client:
    st.error("Admin error: API Key is not set in secrets.")
    st.stop()

# Helper function to upload KB files to Gemini if they haven't been already
@st.cache_data(show_spinner="Syncing knowledge base with AI...")
def prep_knowledge_base():
    if not os.path.exists(KB_DIR):
        return []
    
    files = os.listdir(KB_DIR)
    gemini_file_refs = []
    
    for filename in files:
        filepath = os.path.join(KB_DIR, filename)
        # Upload to Gemini Storage
        try:
            uploaded_doc = client.files.upload(file=filepath)
            
            # Wait for processing if PDF
            if filepath.lower().endswith(".pdf"):
                while uploaded_doc.state.name == "PROCESSING":
                    time.sleep(2)
                    uploaded_doc = client.files.get(name=uploaded_doc.name)
                    
            gemini_file_refs.append(uploaded_doc)
        except APIError as e:
            if "429" in str(e):
                st.error("Failed to load documents: The AI is currently overloaded with requests (Rate Limit). Please tell the admin or wait 1 minute.")
                st.stop()
            else:
                st.error(f"Error loading {filename}: {e}")
                
    return gemini_file_refs

# Load KB into memory
kb_files = prep_knowledge_base()
if not kb_files:
    st.info("The staff has not uploaded any documents yet. Please check back later!")
    st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Hello! I am ready to answer questions about the **{len(kb_files)} document(s)** the staff has provided. What would you like to know?"
    })

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about the documents..."):
    # Add user message to UI
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # We must pass the documents + the chat history
            contents = []
            contents.extend(kb_files) # All the uploaded files!
            
            # Construct a conversation history string for the model to follow
            conversation_history = "Conversation History:\n"
            for msg in st.session_state.messages[:-1]: # exclude the current prompt
                role_label = "User" if msg["role"] == "user" else "Assistant"
                conversation_history += f"{role_label}: {msg['content']}\n"
                
            conversation_history += f"\nUser: {prompt}\n"
            
            system_instruction = (
                "You are an expert factual assistant. Your ONLY source of truth is the provided documents and images.\n\n"
                "CRITICAL RULES:\n"
                "1. If the answer is NOT explicitly stated in the provided text or images, you MUST reply: 'I cannot answer this because the information is not in the provided documents.'\n"
                "2. Do NOT make things up, guess, or use outside knowledge.\n"
                "3. Intelligently connect text and images within the documents to provide a comprehensive answer, but ONLY based on facts shown.\n"
                "4. Be concise and human-like in your delivery.\n"
            )
            
            contents.append(conversation_history)

            # Generate streaming content
            message_placeholder.markdown("*(Thinking...)*")
            
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
            
        except APIError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                error_msg = "**Whoops! The AI is currently overloaded with requests.**\n\nGoogle's free tier only allows 15 questions per minute. Please wait about 60 seconds and try your question again."
                message_placeholder.error(error_msg)
                # Remove the user's prompt since it failed
                st.session_state.messages.pop()
            else:
                st.error(f"An error occurred: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
