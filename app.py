import streamlit as st
import requests
import json
import PyPDF2
import re
import io

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="Executive Resume Strategist", layout="wide")

# --- 2. SESSION STATE (Memory Management) ---
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "# Resume Draft\n*Your progress will appear here...*"

# --- 3. PROFESSIONAL STYLING ---
st.markdown("""
    <style>
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; }
    .resume-box { 
        background-color: #f8f9fa; padding: 25px; border-radius: 15px; 
        border: 1px solid #e9ecef; height: 80vh; overflow-y: auto; 
        color: #212529; font-family: 'serif'; white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR: PERSISTENT CONNECTION & MODEL SELECTOR ---
with st.sidebar:
    st.header("Step 1: Setup")
    st.markdown("[🔗 Get Gemini API Key](https://aistudio.google.com/app/apikey)")
    
    if not st.session_state.api_key:
        user_key = st.text_input("Paste Gemini API Key", type="default", autocomplete="off")
        if st.button("Connect Consultant"):
            if user_key:
                st.session_state.api_key = user_key
                st.rerun()
    else:
        st.success("✅ Consultant Online")
        
        # --- DYNAMIC MODEL SELECTOR ---
        # Based on your key results, we offer the 2.5 and 2.0 options
        model_choice = st.selectbox(
            "Select Model", 
            ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
            help="If you get a 'Quota' error, try switching models."
        )

        if st.button("Disconnect / Change Key"):
            st.session_state.api_key = None
            st.session_state.messages = [] 
            st.rerun()

    st.divider()
    st.header("Step 2: Context")
    target_job = st.text_area("Target Job Description", height=150)
    uploaded_file = st.file_uploader("Current Resume (PDF or TXT)", type=["pdf", "txt"])

# --- 5. BRANDING & INSTRUCTIONS ---
st.title("💼 Executive Resume Strategist")
st.markdown("### *Strategic Career Partnership*")

# --- 6. MAIN INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("The Consultation")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Talk to the Consultant..."):
        if not st.session_state.api_key:
            st.error("Please connect your API Key in the sidebar.")
        elif "SYSTEM_PROMPT" not in st.secrets:
            st.error("Missing 'SYSTEM_PROMPT' in Secrets.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                # --- DYNAMIC API URL ---
                url = f"https://generativelanguage.googleapis.com/v1/models/{model_choice}:generateContent?key={st.session_state.api_key}"
                
                # PDF/TXT Extraction
                resume_text = ""
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                        resume_text = " ".join([p.extract_text() for p in pdf_reader.pages])
                    else:
                        resume_text = uploaded_file.getvalue().decode('utf-8')

                history = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"{st.secrets['SYSTEM_PROMPT']}\n\nJD: {target_job}\nRESUME: {resume_text}\n\nHISTORY:\n{history}\n\nUSER: {prompt}"
                        }]
                    }]
                }

                response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                response_data = response.json()

                if response.status_code != 200:
                    st.error(f"API Error: {response_data.get('error', {}).get('message', 'Unknown Error')}")
                    if "quota" in str(response_data).lower():
                        st.warning(f"⚠️ Quota exceeded for {model_choice}. Please select a different model from the sidebar.")
                else:
                    ai_response = response_data['candidates'][0]['content']['parts'][0]['text']
                    
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
