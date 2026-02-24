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
    health_status = {}
    
    # 1. Cerebras
    ck = get_key("CEREBRAS_API_KEY")
    if ck:
        clients["Cerebras"] = {"client": OpenAI(base_url="https://api.cerebras.ai/v1", api_key=ck), "model": "llama3.1-8b"}
        health_status["Cerebras"] = "✅ Active"
    else:
        health_status["Cerebras"] = "❌ Missing"
        
    # 2. Groq
    gk = get_key("GROQ_API_KEY")
    if gk:
        clients["Groq"] = {"client": OpenAI(base_url="https://api.groq.com/openai/v1", api_key=gk), "model": "llama-3.3-70b-versatile"}
        health_status["Groq"] = "✅ Active"
    else:
        health_status["Groq"] = "❌ Missing"
        
    # 3. SambaNova
    sk = get_key("SAMBANOVA_API_KEY")
    if sk:
        clients["SambaNova"] = {"client": OpenAI(base_url="https://api.sambanova.ai/v1", api_key=sk), "model": "Meta-Llama-3.1-8B-Instruct"}
        health_status["SambaNova"] = "✅ Active"
    else:
        health_status["SambaNova"] = "❌ Missing"

    # 4. OpenRouter
    ok = get_key("OPENROUTER_API_KEY")
    if ok:
        clients["OpenRouter"] = {"client": OpenAI(base_url="https://openrouter.ai/api/v1", api_key=ok), "model": "meta-llama/llama-3.3-70b-instruct:free"}
        health_status["OpenRouter"] = "✅ Active"
    else:
        health_status["OpenRouter"] = "❌ Missing"
        
    # 5. Gemini
    gmk = get_key("GEMINI_API_KEY")
    if gmk:
        clients["Gemini"] = {"client": genai.Client(api_key=gmk), "model": "gemini-2.5-flash"}
        health_status["Gemini"] = "✅ Active"
    else:
        health_status["Gemini"] = "❌ Missing"

    # Display health in sidebar
    with st.sidebar:
        st.divider()
        st.subheader("🛡️ API Waterfall Status")
        for api, status in health_status.items():
            st.write(f"**{api}:** {status}")
        st.info("The bot will automatically skip failed or missing providers.")

    return clients

available_clients = get_clients()
if not available_clients:
    st.error("Admin error: No API Keys found in Streamlit Secrets.")
    st.info("Check the sidebar for status. Please add keys to Streamlit Cloud Secrets.")
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

                # If loop finishes without raising an Error, we succeeded!
                message_placeholder.markdown(f"**[{provider_name}]**\n\n" + full_response)
                st.session_state.messages.append({"role": "model", "content": f"**[{provider_name}]**\n\n" + full_response})
                success = True
                break # Break out of the Waterfall Router
                
            except Exception as e:
                # CATCH-ALL: If ANY provider fails for ANY reason (429, 401, 402, 403, etc.),
                # we immediately move to the next one in the Waterfall sequence.
                last_error = f"{provider_name}: {str(e)}"
                continue
        
        if not success:
            st.error(f"SYSTEM FAILURE: All configured AI providers failed. \n\n**Common Fixes:**\n1. Get a **fresh** Gemini Key (yours was reported as leaked).\n2. Add extra free keys (Cerebras, Groq, or SambaNova) to your Streamlit Secrets for 100% uptime.\n\n*Technical Detail: {last_error}*")
            st.session_state.messages.pop() # Remove failed prompt
