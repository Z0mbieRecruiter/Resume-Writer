import streamlit as st
import google.generativeai as genai
import re

# --- APP CONFIG ---
st.set_page_config(page_title="Executive Resume Consultant", layout="wide")

# --- BRANDING & INTRO ---
st.title("💼 Executive Resume Strategist")
st.markdown("""
    ### *Transforming experience into impact.*
    This tool is a **Strategic Consultant** that interviews you to align your history with your target role.
    
    **How to Start:** 1. Enter your **Gemini API Key** in the sidebar. 
    2. Paste the **Job Description** (and upload your resume if you have one). 
    3. Type **"Hello"** to begin your consultation.
""")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Step 1: Authorization")
    api_key = st.text_input("Gemini API Key", type="password", help="Get a free key at aistudio.google.com")
    
    st.header("Step 2: Context")
    uploaded_file = st.file_uploader("Current Resume (Optional)", type=["pdf", "txt"])
    target_job = st.text_area("Target Job Description", placeholder="Paste job requirements here...")
    
    if st.button("❓ Need Help?"):
        st.info("Paste your API key, add a Job Description, and say 'Hello' in the chat to begin!")

# --- INITIALIZE STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "# Resume Draft\n*Your progress will appear here...*"

# --- CHAT INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Consultation")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Talk to the Consultant..."):
        if not api_key:
            st.error("Please enter your API Key in the sidebar!")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # CONFIGURE AI
            genai.configure(api_key=api_key)
            
            # PULL PROMPT FROM THE SECRET VAULT
            my_system_prompt = st.secrets["SYSTEM_PROMPT"]
            
            model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=my_system_prompt)
            
            # RUN CHAT
            chat = model.start_chat(history=[{"role": m["role"] == "user" and "user" or "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]])
            response = chat.send_message(f"User Input: {prompt}\n\nTarget JD: {target_job}")
            
            # HANDLE UPDATES
            full_text = response.text
            if "<resume>" in full_text:
                parts = re.split(r'<\/?resume>', full_text)
                st.session_state.resume_draft = parts[1]
                clean_response = parts[0] + (parts[2] if len(parts) > 2 else "")
            else:
                clean_response = full_text

            st.session_state.messages.append({"role": "assistant", "content": clean_response})
            with st.chat_message("assistant"):
                st.markdown(clean_response)
            st.rerun()

with col2:
    st.subheader("Live Preview")
    st.markdown(f'<div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; height: 80vh; overflow-y: auto;">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
