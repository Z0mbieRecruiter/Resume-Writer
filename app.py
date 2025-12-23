import streamlit as st
import google.generativeai as genai
import PyPDF2
import re
import io

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="Executive Resume Consultant", layout="wide")

# --- 2. PROFESSIONAL STYLING ---
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

# --- 3. BRANDING & INSTRUCTIONS ---
st.title("💼 Executive Resume Strategist")
st.markdown("""
    ### *Strategic Career Partnership*
    **How to Start:** 1. Enter your **API Key** and click **Connect**.
    2. Paste the **Job Description** and upload your **Resume (PDF/TXT)**.
    3. Type **"Hello"** to begin.
""")

# --- 4. SIDEBAR SETUP & DIAGNOSTICS ---
with st.sidebar:
    st.header("Step 1: Setup")
    st.markdown("[🔗 Get Gemini API Key](https://aistudio.google.com/app/apikey)")
    
    # Password manager fix
    user_key = st.text_input("Paste Gemini API Key", type="default", autocomplete="off")
    
    if st.button("Connect Consultant"):
        if user_key:
            st.session_state.api_key = user_key
            try:
                genai.configure(api_key=user_key)
                # DIAGNOSTIC: Check what the server actually sees
                v = genai.__version__
                models = [m.name for m in genai.list_models()]
                st.success(f"Connected! SDK Version: {v}")
                st.session_state.ready = True
            except Exception as e:
                st.error(f"Connection Failed: {str(e)}")

    st.divider()
    st.header("Step 2: Context")
    target_job = st.text_area("Target Job Description", height=150)
    uploaded_file = st.file_uploader("Current Resume (PDF/TXT)", type=["pdf", "txt"])

# --- 5. INITIALIZE STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "# Resume Draft\n*Your progress will appear here...*"

# --- 6. MAIN INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("The Consultation")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Talk to the Consultant..."):
        if "api_key" not in st.session_state:
            st.error("Please connect your API Key first.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                # REINFORCED CONNECTION
                genai.configure(api_key=st.session_state.api_key)
                
                # PDF/TXT Reading
                resume_text = ""
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
                        reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                        resume_text = " ".join([page.extract_text() for page in reader.pages])
                    else:
                        resume_text = uploaded_file.getvalue().decode('utf-8')

                # We use a direct generation call to avoid the 'start_chat' v1beta bug
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                history = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
                full_payload = f"{st.secrets['SYSTEM_PROMPT']}\n\nJD: {target_job}\nRESUME: {resume_text}\n\nHISTORY:\n{history}\n\nUSER: {prompt}"

                response = model.generate_content(full_payload)
                
                if "<resume>" in response.text:
                    parts = re.split(r'<\/?resume>', response.text)
                    st.session_state.resume_draft = parts[1].strip()
                    clean_res = parts[0].strip() + "\n" + (parts[2].strip() if len(parts) > 2 else "")
                else:
                    clean_res = response.text

                st.session_state.messages.append({"role": assistant_role := "assistant", "content": clean_res})
                with st.chat_message("assistant"):
                    st.markdown(clean_res)
                st.rerun()

            except Exception as e:
                st.error(f"Consultation Error: {str(e)}")

with col2:
    st.subheader("Strategic Draft")
    st.markdown(f'<div class="resume-box">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
