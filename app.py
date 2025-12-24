import streamlit as st
import requests
import json
import PyPDF2
import re
import io

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="Executive Resume Strategist", layout="wide")

# --- 2. SESSION STATE (Memory Management) ---
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "# Executive Resume Draft\n*Consultation pending...*"

# --- 3. PROFESSIONAL STYLING ---
st.markdown("""
    <style>
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; }
    .resume-box { 
        background-color: #f8f9fa; padding: 25px; border-radius: 15px; 
        border: 1px solid #e9ecef; height: 85vh; overflow-y: auto; 
        color: #212529; font-family: 'serif'; white-space: pre-wrap;
    }
    .instruction-card {
        background-color: #e8f0fe; padding: 15px; border-radius: 10px;
        border-left: 5px solid #1a73e8; margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR: PERSISTENT CONNECTION ---
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
        # Defaulting to 2.5 Flash as confirmed by your health check
        model_choice = st.selectbox("Select Model", ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"])
        if st.button("Disconnect / Reset App"):
            st.session_state.api_key = None
            st.session_state.messages = []
            st.session_state.resume_draft = "# Executive Resume Draft..."
            st.rerun()

    st.divider()
    st.header("Step 2: Core Context")
    target_job = st.text_area("Target Job Description", height=200, placeholder="What is the problem the company is trying to solve?")
    uploaded_file = st.file_uploader("Current Resume (PDF/TXT)", type=["pdf", "txt"])

# --- 5. MAIN INTERFACE ---
st.title("💼 Executive Resume Strategist")

# RESTORED: User Instructions
st.markdown("""
    <div class="instruction-card">
        <strong>How to use this Strategist:</strong>
        <ol>
            <li><strong>Connect:</strong> Enter your API Key in the sidebar.</li>
            <li><strong>Context:</strong> Paste the Target Job and upload your current Resume.</li>
            <li><strong>Consult:</strong> Type <strong>"Hello"</strong> or <strong>"Let's begin"</strong> in the chat below to start your partnership.</li>
        </ol>
        <em>The Strategist will interview you to find the 'Wins' that align with the market gap.</em>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("Consultation")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

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
                # Verifying the direct v1 URL logic
                url = f"https://generativelanguage.googleapis.com/v1/models/{model_choice}:generateContent?key={st.session_state.api_key}"
                
                # Verbatim PDF/TXT Extraction
                resume_text = ""
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                        resume_text = " ".join([p.extract_text() for p in pdf_reader.pages])
                    else:
                        resume_text = uploaded_file.getvalue().decode('utf-8')

                history_log = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])

                # --- VERBATIM PASSTHROUGH PAYLOAD ---
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"""
{st.secrets['SYSTEM_PROMPT']}

---
CONTEXT DATA:
Target Job: {target_job}
Existing Resume: {resume_text}
Current Draft State: {st.session_state.resume_draft}

---
CONVERSATION LOG:
{history_log}

LATEST USER INPUT: {prompt}
"""
                        }]
                    }]
                }

                response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
                response_data = response.json()

                if response.status_code == 200:
                    ai_response = response_data['candidates'][0]['content']['parts'][0]['text']
                    
                    # Split tags for the persistent draft box
                    if "<resume>" in ai_response:
                        parts = re.split(r'<\/?resume>', ai_response)
                        st.session_state.resume_draft = parts[1].strip()
                        clean_chat = parts[0].strip() + "\n" + (parts[2].strip() if len(parts) > 2 else "")
                    else:
                        clean_chat = ai_response

                    st.session_state.messages.append({"role": "assistant", "content": clean_chat})
                    with st.chat_message("assistant"):
                        st.markdown(clean_chat)
                    st.rerun()
                else:
                    st.error(f"API Error: {response_data.get('error', {}).get('message')}")

            except Exception as e:
                st.error(f"System Error: {str(e)}")

with col2:
    st.subheader("Strategic Draft Preview")
    st.markdown(f'<div class="resume-box">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
