import streamlit as st
import google.generativeai as genai
import PyPDF2
import re
import io

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="Executive Resume Strategist", layout="wide")

# --- 2. SESSION STATE INITIALIZATION (Crucial for Memory) ---
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "# Resume Draft\n*Your progress will appear here...*"

# --- 3. PERSISTENT API CONFIGURATION ---
# This runs on EVERY refresh. If a key is in memory, we re-verify the stable route.
if st.session_state.api_key:
    genai.configure(api_key=st.session_state.api_key, transport='rest')

# --- 4. PROFESSIONAL STYLING ---
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

# --- 5. SIDEBAR: PERSISTENT CONNECTION ---
with st.sidebar:
    st.header("Step 1: Setup")
    st.markdown("[🔗 Get Gemini API Key](https://aistudio.google.com/app/apikey)")
    
    # If not connected, show the input. If connected, show status.
    if not st.session_state.api_key:
        user_key = st.text_input("Paste Gemini API Key", type="default", autocomplete="off")
        if st.button("Connect Consultant"):
            if user_key:
                st.session_state.api_key = user_key
                st.rerun() # Force refresh to lock in the key
    else:
        st.success("✅ Consultant Online")
        if st.button("Disconnect / Change Key"):
            st.session_state.api_key = None
            st.rerun()

    st.divider()
    st.header("Step 2: Context")
    target_job = st.text_area("Target Job Description", height=150)
    uploaded_file = st.file_uploader("Current Resume (PDF or TXT)", type=["pdf", "txt"])

# --- 6. BRANDING & INSTRUCTIONS ---
st.title("💼 Executive Resume Strategist")
st.markdown("""
    ### *Strategic Career Partnership*
    **How to Start:** 1. Connect Key. 2. Paste Job Description. 3. Say 'Hello'.
""")

# --- 7. MAIN INTERFACE ---
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
            st.error("Missing 'SYSTEM_PROMPT' in Secrets. Check your Streamlit settings.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                # Direct call to the stable model
                model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
                
                # PDF/TXT Extraction
                resume_text = ""
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                        resume_text = " ".join([p.extract_text() for p in pdf_reader.pages])
                    else:
                        resume_text = uploaded_file.getvalue().decode('utf-8')

                history = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
                full_payload = f"{st.secrets['SYSTEM_PROMPT']}\n\nTARGET JD: {target_job}\nUPLOADED RESUME: {resume_text}\n\nHISTORY:\n{history}\n\nUSER: {prompt}"

                response = model.generate_content(full_payload)
                ai_response = response.text
                
                # Update Draft logic
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
                st.error(f"Consultation Error: {str(e)}")

with col2:
    st.subheader("Strategic Draft")
    st.markdown(f'<div class="resume-box">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
