import streamlit as st
import requests
import json
import re

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="Executive Resume Strategist", layout="wide")

# --- 2. THE CONSULTANT STYLING ---
st.markdown("""
    <style>
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; }
    .resume-box { 
        background-color: #f8f9fa; 
        padding: 25px; 
        border-radius: 15px; 
        border: 1px solid #e9ecef; 
        height: 80vh; 
        overflow-y: auto; 
        color: #212529;
        font-family: 'serif';
        white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BRANDING & UI ---
st.title("💼 Executive Resume Strategist")
st.markdown("### *Strategic Career Partnership*")

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("Step 1: Setup")
    st.markdown("[🔗 Get Gemini API Key](https://aistudio.google.com/app/apikey)")
    
    user_key = st.text_input("Paste API Key", type="password")
    
    if st.button("Connect Consultant"):
        if user_key:
            st.session_state.api_key = user_key
            st.success("Consultant Connected!")
        else:
            st.error("Please enter a key.")

    st.divider()
    st.header("Step 2: Context")
    target_job = st.text_area("Target Job Description", placeholder="Paste requirements here...", height=200)
    uploaded_file = st.file_uploader("Upload Current Resume (Optional)", type=["txt"])

# --- 5. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "Your draft will appear here..."

# --- 6. MAIN INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Consultation")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Talk to the Consultant..."):
        if "api_key" not in st.session_state:
            st.error("Please connect your API Key in the sidebar.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                # --- DIRECT API CALL (Bypassing the Google Library) ---
                api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={st.session_state.api_key}"
                
                # Build context
                resume_text = ""
                if uploaded_file:
                    resume_text = f"Existing Resume: {uploaded_file.getvalue().decode('utf-8')}"
                
                history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
                system_instr = st.secrets.get("SYSTEM_PROMPT", "You are a resume consultant.")
                
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"{system_instr}\n\nJOB: {target_job}\n{resume_text}\n\nHISTORY:\n{history_text}\n\nUSER: {prompt}"
                        }]
                    }]
                }

                # Send direct web request
                response = requests.post(api_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                response_data = response.json()

                if response.status_code != 200:
                    st.error(f"API Error {response.status_code}: {response_data.get('error', {}).get('message', 'Unknown error')}")
                else:
                    # Extract the text
                    ai_response = response_data['candidates'][0]['content']['parts'][0]['text']
                    
                    # Process Draft Tags
                    if "<resume>" in ai_response:
                        parts = re.split(r'<\/?resume>', ai_response)
                        st.session_state.resume_draft = parts[1].strip()
                        clean_res = parts[0].strip() + "\n" + (parts[2].strip() if len(parts) > 2 else "")
                    else:
                        clean_res = ai_response

                    st.session_state.messages.append({"role": "assistant", "content": clean_res})
                    with st.chat_message("assistant"):
                        st.markdown(clean_res)
                    st.rerun()

            except Exception as e:
                st.error(f"System Error: {str(e)}")

with col2:
    st.subheader("Strategic Draft")
    st.markdown(f'<div class="resume-box">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
