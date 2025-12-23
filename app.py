import streamlit as st
import google.generativeai as genai
import PyPDF2
import re
import io

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="Executive Resume Strategist", layout="wide")

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

# --- 3. RESTORED BRANDING & INSTRUCTIONS ---
st.title("💼 Executive Resume Strategist")
st.markdown("""
    ### *Strategic Career Partnership*
    This tool is a **Strategic Consultant** that interviews you to align your history with your target role.
    
    **How to Start:** 1. Enter your **API Key** and click **Connect**.
    2. Paste the **Job Description** and upload your **Resume (PDF/TXT)**.
    3. Type **"Hello"** to begin.
""")

# --- 4. SIDEBAR SETUP ---
with st.sidebar:
    st.header("Step 1: Setup")
    st.markdown("[🔗 Get Gemini API Key](https://aistudio.google.com/app/apikey)")
    
    # Use 'default' to stop password managers, and 'label_visibility' for a clean look
    user_key = st.text_input("Paste Gemini API Key", type="default", autocomplete="off")
    
    if st.button("Connect Consultant"):
        if user_key:
            st.session_state.api_key = user_key
            st.success("Consultant Ready!")

    st.divider()
    st.header("Step 2: Context")
    target_job = st.text_area("Target Job Description", placeholder="Paste requirements here...", height=200)
    uploaded_file = st.file_uploader("Current Resume (PDF or TXT)", type=["pdf", "txt"])

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
            st.error("Please connect your API Key in the sidebar.")
        elif "SYSTEM_PROMPT" not in st.secrets:
            st.error("Missing 'SYSTEM_PROMPT' in Streamlit Secrets.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                genai.configure(api_key=st.session_state.api_key)
                # Forced stable model call
                model = genai.GenerativeModel(model_name='gemini-1.5-flash')
                
                # --- PDF & TXT READING LOGIC ---
                resume_text = ""
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                        for page in pdf_reader.pages:
                            resume_text += page.extract_text()
                    else:
                        resume_text = uploaded_file.getvalue().decode('utf-8')

                # Building Manual History for Stability
                history_block = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
                
                full_payload = f"""
                SYSTEM PROMPT: {st.secrets['SYSTEM_PROMPT']}
                TARGET JOB: {target_job}
                UPLOADED RESUME: {resume_text}
                
                CHAT HISTORY:
                {history_block}
                
                USER LATEST MESSAGE: {prompt}
                """

                # Direct generation call
                response = model.generate_content(full_payload)
                ai_text = response.text
                
                # Update Draft logic
                if "<resume>" in ai_text:
                    parts = re.split(r'<\/?resume>', ai_text)
                    st.session_state.resume_draft = parts[1].strip()
                    clean_res = parts[0].strip() + "\n" + (parts[2].strip() if len(parts) > 2 else "")
                else:
                    clean_res = ai_text

                st.session_state.messages.append({"role": "assistant", "content": clean_res})
                with st.chat_message("assistant"):
                    st.markdown(clean_res)
                st.rerun()

            except Exception as e:
                st.error(f"Consultation Error: {str(e)}")

with col2:
    st.subheader("Strategic Draft")
    st.markdown(f'<div class="resume-box">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
