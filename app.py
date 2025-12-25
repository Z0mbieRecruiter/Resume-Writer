import streamlit as st
import requests
import json
import PyPDF2
import re
import io
import time # Added for wait logic

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="Executive Resume Strategist", layout="centered")

# --- 2. SESSION STATE ---
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = ""

# --- 3. PROFESSIONAL STYLING ---
st.markdown("""
    <style>
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; }
    .instruction-card {
        background-color: #e8f0fe; color: #1e3a8a; padding: 20px; 
        border-radius: 10px; border-left: 5px solid #1a73e8; margin-bottom: 20px;
    }
    .instruction-card strong, .instruction-card li, .instruction-card em { color: #1e3a8a !important; }
    .draft-header { margin-top: 50px; padding: 10px; border-bottom: 2px solid #1a73e8; color: #1a73e8; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("Step 1: Setup")
    if not st.session_state.api_key:
        user_key = st.text_input("Paste Gemini API Key", type="default", autocomplete="off")
        if st.button("Connect Strategist"):
            if user_key:
                st.session_state.api_key = user_key
                st.rerun()
    else:
        st.success("✅ Strategist Online")
        model_choice = st.selectbox("Select Model", ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"])
        
        if st.button("🗑️ Clear Consultation"):
            st.session_state.messages = []
            st.session_state.resume_draft = ""
            st.rerun()

    st.divider()
    st.header("Step 2: Core Context")
    target_job = st.text_area("Target Job Description", height=200)
    uploaded_file = st.file_uploader("Current Resume (PDF/TXT)", type=["pdf", "txt"])

# --- 5. MAIN INTERFACE ---
st.title("💼 Executive Resume Strategist")

st.markdown("""
    <div class="instruction-card">
        <strong>Status:</strong> Ready for consultation. <br>
        <em>If you see a 'Quota' error, wait 30 seconds and try again. This usually means the per-minute limit was hit, not your total daily limit.</em>
    </div>
    """, unsafe_allow_html=True)

# Display Conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Talk to the Strategist..."):
    if not st.session_state.api_key:
        st.error("Please connect in the sidebar.")
    elif "SYSTEM_PROMPT" not in st.secrets:
        st.error("SYSTEM_PROMPT not found in Secrets.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        try:
            url = f"https://generativelanguage.googleapis.com/v1/models/{model_choice}:generateContent?key={st.session_state.api_key}"
            
            # Verbatim Extraction
            resume_text = ""
            if uploaded_file:
                if uploaded_file.type == "application/pdf":
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                    resume_text = " ".join([p.extract_text() for p in pdf_reader.pages])
                else:
                    resume_text = uploaded_file.getvalue().decode('utf-8')

            history_log = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])

            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"{st.secrets['SYSTEM_PROMPT']}\n\nCONTEXT:\nJob: {target_job}\nResume: {resume_text}\nDraft: {st.session_state.resume_draft}\n\nHISTORY:\n{history_log}\n\nUSER: {prompt}"
                    }]
                }]
            }

            response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
            response_data = response.json()

            # --- SMART QUOTA HANDLING ---
            if response.status_code == 429:
                st.warning("⚠️ Rate Limit Hit (Too many requests per minute). Retrying in 5 seconds...")
                time.sleep(5)
                # Second Attempt
                response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                response_data = response.json()

            if response.status_code == 200:
                ai_response = response_data['candidates'][0]['content']['parts'][0]['text']
                
                if "<resume>" in ai_response:
                    parts = re.split(r'<\/?resume>', ai_response)
                    st.session_state.resume_draft = parts[1].strip()
                    clean_chat = parts[0].strip() + "\n" + (parts[2].strip() if len(parts) > 2 else "")
                else:
                    clean_chat = ai_response

                st.session_state.messages.append({"role": "assistant", "content": clean_chat})
                st.rerun()
            else:
                st.error(f"API Error ({response.status_code}): {response_data.get('error', {}).get('message')}")

        except Exception as e:
            st.error(f"System Error: {str(e)}")

# --- 6. DRAFT AREA ---
if st.session_state.resume_draft:
    st.markdown('<h3 class="draft-header">📄 Strategic Resume Draft</h3>', unsafe_allow_html=True)
    st.code(st.session_state.resume_draft, language=None)
