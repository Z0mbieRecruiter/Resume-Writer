import streamlit as st
import google.generativeai as genai
import re

# --- 1. SETTINGS & BRANDING ---
st.set_page_config(page_title="Resume Consultant", layout="wide")
st.title("💼 Executive Resume Strategist")

# --- 2. SIDEBAR (Simplified for Non-Devs) ---
with st.sidebar:
    st.header("1. Setup")
    st.markdown("[Get a Free API Key here](https://aistudio.google.com/app/apikey)")
    
    # We use a simple text input. No 'Connect' button needed - it will check live.
    user_key = st.text_input("Paste your API Key here:", type="password")
    
    st.divider()
    st.header("2. Context")
    target_job = st.text_area("Target Job Description", height=200)
    uploaded_file = st.file_uploader("Upload Resume (Optional)", type=["pdf", "txt"])

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "Your draft will appear here..."

# --- 4. THE CONSULTATION ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Consultation")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Say 'Hello' to start..."):
        if not user_key:
            st.error("Please paste your API Key in the sidebar.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                # Initialize the API
                genai.configure(api_key=user_key)
                
                # STABILITY FIX: Use the most basic, universal model name
                # This avoids the 404 errors by using the global standard
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Start chat with System Instructions pulled from Secrets
                chat = model.start_chat(history=[])
                
                # Send the secret prompt first, then the user's message
                full_context = f"{st.secrets['SYSTEM_PROMPT']}\n\nJob: {target_job}\n\nUser: {prompt}"
                response = chat.send_message(full_context)
                
                # Update UI
                response_text = response.text
                if "<resume>" in response_text:
                    parts = re.split(r'<\/?resume>', response_text)
                    st.session_state.resume_draft = parts[1].strip()
                    clean_res = parts[0] + (parts[2] if len(parts) > 2 else "")
                else:
                    clean_res = response_text

                st.session_state.messages.append({"role": "assistant", "content": clean_res})
                with st.chat_message("assistant"):
                    st.markdown(clean_res)
                st.rerun()

            except Exception as e:
                st.error(f"Connection Error: {str(e)}")
                st.info("Check if 'Generative Language API' is enabled in your Google AI Studio.")

with col2:
    st.subheader("Strategic Draft")
    st.markdown(f'<div style="background-color:#f0f2f6;padding:20px;border-radius:10px;height:70vh;overflow-y:auto">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
