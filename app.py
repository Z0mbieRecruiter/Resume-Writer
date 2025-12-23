import streamlit as st
import google.generativeai as genai
import re

# --- 1. SETTINGS ---
st.set_page_config(page_title="Resume Consultant", layout="wide")

# --- 2. SIDEBAR WITH REAL VERIFICATION ---
with st.sidebar:
    st.header("Step 1: Real-Time Connection")
    st.markdown("[🔗 Get your API Key here](https://aistudio.google.com/app/apikey)")
    
    # type="default" and autocomplete="off" prevents password manager popups
    input_key = st.text_input("Paste API Key", type="default", autocomplete="off")
    
    if st.button("Verify & Connect"):
        if input_key:
            try:
                genai.configure(api_key=input_key)
                # THIS IS THE REAL TEST: We ask Google for a list of what you can use
                available_models = [m.name for m in genai.list_models()]
                
                st.session_state.api_key = input_key
                st.session_state.models = available_models
                st.success(f"Connected! Your key has access to {len(available_models)} models.")
            except Exception as e:
                st.error(f"Connection Failed: {str(e)}")
                st.info("Ensure the 'Generative Language API' is enabled in your Google AI Studio settings.")
        else:
            st.error("Please enter a key.")

    st.divider()
    st.header("Step 2: Context")
    target_job = st.text_area("Target Job Description", height=200)

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "Draft will appear here..."

# --- 4. MAIN INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Consultation")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Say 'Hello' to begin..."):
        if "api_key" not in st.session_state:
            st.error("Please Verify & Connect in the sidebar first.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                genai.configure(api_key=st.session_state.api_key)
                
                # AUTO-SELECTION: Use Flash if available, otherwise use Pro
                selected_model = "models/gemini-1.5-flash"
                if selected_model not in st.session_state.models:
                    selected_model = "models/gemini-pro"
                
                model = genai.GenerativeModel(
                    model_name=selected_model,
                    system_instruction=st.secrets["SYSTEM_PROMPT"]
                )
                
                chat = model.start_chat(history=[])
                response = chat.send_message(f"Job: {target_job}\n\nUser: {prompt}")
                
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
                st.error(f"Error: {str(e)}")

with col2:
    st.subheader("Strategic Draft")
    st.markdown(f'<div style="background-color:#f8f9fa;padding:20px;border-radius:10px;height:70vh;overflow-y:auto;border:1px solid #dee2e6">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
