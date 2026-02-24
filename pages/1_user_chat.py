import streamlit as st
from openai import OpenAI
import os
import sys

# Add parent directory to path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import get_all_kb_text

st.set_page_config(page_title="Query Interface", layout="wide")

st.title("QUERY INTERFACE")
st.markdown("Engine: `meta-llama/llama-3.3-70b-instruct` | State: **Ready**")

KB_DIR = "knowledge_base"

# Initialize OpenRouter Client
@st.cache_resource
def get_client():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["OPENROUTER_API_KEY"]
        except (FileNotFoundError, KeyError):
            return None
    if not api_key:
        return None
        
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

client = get_client()
if not client:
    st.error("Admin error: Please set OPENROUTER_API_KEY in Streamlit Secrets.")
    st.info("You can get a free key from [OpenRouter.ai](https://openrouter.ai/).")
    st.stop()

# Helper function to get KB text
@st.cache_data(show_spinner="Reading knowledge base documents...")
def prep_knowledge_base():
    return get_all_kb_text(KB_DIR)

# Load KB into memory
kb_text = prep_knowledge_base()
if not kb_text.strip():
    st.info("The staff has not uploaded any documents yet. Please check back later!")
    st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Hello! I've read the available knowledge base. What would you like to know?"
    })

# Display chat messages
for message in st.session_state.messages:
    if message["role"] != "system": # Don't show the massive context dump to the user
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about the documents..."):
    # Add user message to UI
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Reconstruct the conversation for OpenAI format
            # We inject the massive KB text as the system prompt
            api_messages = [
                {
                    "role": "system", 
                    "content": (
                        "You are a friendly, empathetic, and highly capable AI assistant securely analyzing documents for staff and users. "
                        "When users ask questions, respond warmly and conversationally as if you were a real, helpful colleague. "
                        "CRITICAL RULES:\n"
                        "1. If the answer is NOT explicitly stated in the provided text, politely explain: 'I'm sorry, but I don't see that information in the documents I've been provided.'\n"
                        "2. Do NOT make things up or guess. Rely ONLY on the provided documents.\n"
                        "3. Do not sound like a robot listing rules; weave the factual answers smoothly into a kind, human response.\n\n"
                        f"=== KNOWLEDGE BASE DOCUMENTS ===\n{kb_text}\n================================="
                    )
                }
            ]
            
            # Add historical messages (ignoring our intro message)
            for msg in st.session_state.messages[1:]:
                api_messages.append({"role": msg["role"], "content": msg["content"]})
                
            message_placeholder.markdown("*(Analyzing...)*")
            
            # Call OpenRouter API
            response = client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=api_messages,
                stream=True,
                temperature=0.7
            )

            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # Add assistant response to state
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            if "401" in str(e):
                st.error("OpenRouter API Key is invalid.")
            elif "429" in str(e):
                st.error("Rate Limit Reached (though very rare on OpenRouter!). Try again in a minute.")
            else:
                st.error(f"An unexpected error occurred: {e}")
            st.session_state.messages.pop() # Remove failed prompt
