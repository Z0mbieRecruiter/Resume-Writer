import streamlit as st
import google.generativeai as genai
import re

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="Executive Resume Consultant", layout="wide")

st.title("💼 Executive Resume Strategist")
st.markdown("""
    ### *Transforming experience into impact.*
    This tool is a **Strategic Consultant** that interviews you to align your history with your target role.
    
    **How to Start:** 1. Enter your **Gemini API Key** and click **Verify & Connect**. 
    2. Paste the **Job Description**. 
    3. Type **"Hello"** to begin.
""")

# --- 2. SIDEBAR WITH FORCED STABLE CONNECTION ---
with st.sidebar:
    st.header("Step 1: Authorization")
    st.markdown("[🔗 Get your API Key here](https://aistudio.google.com/app/apikey)")
    
    # We use 'default' and no autocomplete to stop password manager popups
    input_key = st.text_input("Paste API Key", type="default", autocomplete="off")
    
    if st.button("Verify & Connect"):
        if input_key:
            try:
                # Force the library to use the stable v1 API
                genai.configure(api_key=input_key, transport='rest') 
                
                # Test connection by listing allowed models
                available = [m.name for m in genai.list_models()]
                st.session_state.api_key = input_key
                st.session_state.allowed_models = available
                st.success(f"Connected! (Found {len(available)} models)")
            except Exception as e:
                st.error(f"Connection Failed: {str(e)}")
        else:
            st.error("Please enter a key.")

    st.divider()
    st.header("Step 2: Context")
    target_job = st.text_area("Target Job Description", placeholder="Paste requirements here...", height=200)

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "Your draft will appear here..."

# --- 4. MAIN INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Consultation")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Talk to the Consultant..."):
        if "api_key" not in st.session_state:
            st.error("Please Verify & Connect in the sidebar first.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                genai.configure(api_key=st.session_state.api_key, transport='rest')
                
                # We find the first working model from your allowed list
                # This ensures we NEVER call a model that returns a 404
                model_name = "models/gemini-1.5-flash"
                if model_name not in st.session_state.allowed_models:
                    model_name = st.session_state.allowed_models[0] # Fallback to first available
                
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=st.secrets["SYSTEM_PROMPT"]
                )
                
                # Simplified chat call to stay on stable v1
                response = model.generate_content(
                    f"CONTEXT:\nJob: {target_job}\nHistory: {st.session_state.messages[:-1]}\n\nUSER INPUT: {prompt}"
                )
                
                res_text = response.text
                if "<resume>" in res_text:
                    parts = re.split(r'<\/?resume>', res_text)
                    st.session_state.resume_draft = parts[1].strip()
                    clean_res = parts[0] + (parts[2] if len(parts) > 2 else "")
                else:
                    clean_res = res_text

                st.session_state.messages.append({"role": "assistant", "content": clean_res})
                with st.chat_message("assistant"):
                    st.markdown(clean_res)
                st.rerun()

            except Exception as e:
                st.error(f"Consultation Error: {str(e)}")

with col2:
    st.subheader("Strategic Draft")
    st.markdown(f'<div style="background-color:#f8f9fa;padding:20px;border-radius:10px;height:75vh;overflow-y:auto;border:1px solid #dee2e6">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
