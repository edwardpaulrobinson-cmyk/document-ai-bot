import streamlit as st
from openai import OpenAI
from google import genai
from google.genai import types
import os
import sys

# Add parent directory to path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import get_all_kb_text

st.set_page_config(page_title="Query Interface", layout="wide")

st.title("QUERY INTERFACE")
st.markdown("Engine: `Waterfall Router (Cerebras → Groq → SambaNova → OpenRouter → Gemini)` | State: **Ready**")

KB_DIR = "knowledge_base"

# Initialize ALL available clients
@st.cache_resource
def get_clients():
    def get_key(name):
        val = os.getenv(name)
        if not val:
            try:
                val = st.secrets[name]
            except Exception:
                pass
        return val

    clients = {}
    
    # 1. Cerebras (1M tokens/day free, insanely fast Llama 3.1)
    ck = get_key("CEREBRAS_API_KEY")
    if ck:
        clients["Cerebras"] = {"client": OpenAI(base_url="https://api.cerebras.ai/v1", api_key=ck), "model": "llama3.1-8b"}
        
    # 2. Groq (14.4k requests/day free, insanely fast)
    gk = get_key("GROQ_API_KEY")
    if gk:
        clients["Groq"] = {"client": OpenAI(base_url="https://api.groq.com/openai/v1", api_key=gk), "model": "llama-3.3-70b-versatile"}
        
    # 3. SambaNova (Massive free tier)
    sk = get_key("SAMBANOVA_API_KEY")
    if sk:
        clients["SambaNova"] = {"client": OpenAI(base_url="https://api.sambanova.ai/v1", api_key=sk), "model": "Meta-Llama-3.1-8B-Instruct"}

    # 4. OpenRouter (200 requests/day free Llama 3.3)
    ok = get_key("OPENROUTER_API_KEY")
    if ok:
        clients["OpenRouter"] = {"client": OpenAI(base_url="https://openrouter.ai/api/v1", api_key=ok), "model": "meta-llama/llama-3.3-70b-instruct:free"}
        
    # 5. Gemini (1500 requests/day free)
    gmk = get_key("GEMINI_API_KEY")
    if gmk:
        clients["Gemini"] = {"client": genai.Client(api_key=gmk), "model": "gemini-2.5-flash"}

    return clients

available_clients = get_clients()
if not available_clients:
    st.error("Admin error: No API Keys found in Streamlit Secrets.")
    st.info("Please set at least one of: CEREBRAS_API_KEY, GROQ_API_KEY, SAMBANOVA_API_KEY, OPENROUTER_API_KEY, or GEMINI_API_KEY.")
    st.stop()

# Helper function to get KB text
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
        "role": "model", # Using 'model' internally to support Gemini's strict schema
        "content": "Hello! I've read the available knowledge base. What would you like to know?"
    })

# Display chat messages
for message in st.session_state.messages:
    if message["role"] != "system":
        # Map 'model' to 'assistant' just for the UI rendering icon
        role_label = "assistant" if message["role"] == "model" else message["role"]
        with st.chat_message(role_label):
            st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a question about the documents..."):
    # Add user message to UI
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        system_instruction = (
            "You are an advanced, intelligent, and empathetic AI assistant securely analyzing documents for staff. "
            "You MUST format your responses to be highly readable, beautiful, and structured exactly like a professional software manual.\n\n"
            "CRITICAL FORMATTING RULES:\n"
            "1. ALWAYS use large Bold Headers (e.g. '### Common Issues & Solutions:', '### Step-by-Step Process:').\n"
            "2. Break down complex answers into numbered lists and bullet points.\n"
            "3. Use bold text to highlight key terms, buttons, or navigation paths (e.g. **Finance → Payables**).\n"
            "4. Include direct quotes or notes from the document italicized (e.g. *Document note: 'xyz'*).\n"
            "5. Never output a giant wall of text. Use spacing and structure.\n\n"
            "CRITICAL BEHAVIOR RULES:\n"
            "1. Be smart: Connect different pieces of information across the documents to give a comprehensive, intelligent answer.\n"
            "2. Be human: Sound conversational but professional. Do not sound like a robotic rule-follower.\n"
            "3. BE FACTUAL: If the answer is NOT explicitly stated in the provided text, politely explain: 'I'm sorry, but I don't see that specific information in the documents I've been provided.' Do NOT make things up or guess.\n\n"
            f"=== KNOWLEDGE BASE DOCUMENTS ===\n{kb_text}\n================================="
        )

        success = False
        last_error = None
        
        # WATERFALL ROUTER: Try each provider until one successfully streams
        for provider_name, provider_data in available_clients.items():
            message_placeholder.markdown(f"*(Connecting to {provider_name}...)*")
            try:
                full_response = ""
                
                if provider_name == "Gemini":
                    # Format for Gemini
                    contents = []
                    for msg in st.session_state.messages[1:-1]: # Skip intro and current prompt
                        contents.append(types.Content(role=msg["role"], parts=[types.Part.from_text(text=msg["content"])]))
                    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))
                    
                    response = provider_data["client"].models.generate_content_stream(
                        model=provider_data["model"],
                        contents=contents,
                        config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.7)
                    )
                    for chunk in response:
                        if chunk.text:
                            full_response += chunk.text
                            # Use Markdown to label which AI provided the response
                            message_placeholder.markdown(f"**[{provider_name}]**\n\n" + full_response + "▌")
                
                else:
                    # Format for standard OpenAI SDK (OpenRouter, Groq, Cerebras, SambaNova)
                    api_messages = [{"role": "system", "content": system_instruction}]
                    for msg in st.session_state.messages[1:-1]:
                        r = "assistant" if msg["role"] == "model" else msg["role"]
                        api_messages.append({"role": r, "content": msg["content"]})
                    api_messages.append({"role": "user", "content": prompt})
                    
                    response = provider_data["client"].chat.completions.create(
                        model=provider_data["model"],
                        messages=api_messages,
                        stream=True,
                        temperature=0.7
                    )
                    for chunk in response:
                        if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(f"**[{provider_name}]**\n\n" + full_response + "▌")

                # If loop finishes without raising a 429 Error, we succeeded!
                message_placeholder.markdown(f"**[{provider_name}]**\n\n" + full_response)
                st.session_state.messages.append({"role": "model", "content": f"**[{provider_name}]**\n\n" + full_response})
                success = True
                break # Break out of the Waterfall Router
                
            except Exception as e:
                err_str = str(e).lower()
                # If the provider is rate limited, exhausted, or down, skip to the next!
                if "429" in err_str or "exhausted" in err_str or "rate" in err_str or "500" in err_str or "503" in err_str:
                    last_error = f"{provider_name} Overloaded: {e}"
                    continue
                elif "401" in err_str or "invalid" in err_str:
                    last_error = f"{provider_name} Auth Failed: {e}"
                    continue
                else:
                    last_error = f"{provider_name} Unknown Error: {e}"
                    continue
        
        if not success:
            st.error(f"SYSTEM FAILURE: All available AI providers are currently exhausted or disconnected. \n\nLast Error: {last_error}")
            st.session_state.messages.pop() # Remove failed prompt
