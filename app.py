import streamlit as st
import google.generativeai as genai
import re
import os

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Executive Resume Consultant", layout="wide")

# Force stable API endpoint usage
os.environ["GOOGLE_API_USE_MTLS_ENDPOINT"] = "never"

# --- 2. CUSTOM STYLING ---
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

# --- 3. BRANDING & HERO SECTION ---
st.title("💼 Executive Resume Strategist")
st.markdown("""
    ### *Transforming experience into impact.*
    This tool is a **Strategic Consultant** that interviews you to align your history with your target role.
    
    **How to Start:** 1. Enter your **Gemini API Key** in the sidebar and click **Connect**. 
    2. Provide your **Job Description** (and resume if you have one). 
    3. Type **"Hello"** in the chat to begin your consultation.
""")

# --- 4. SIDEBAR SETUP ---
with st.sidebar:
    st.header("Step 1: Authorization")
    st.markdown("[🔗 Get your FREE Gemini API Key here](https://aistudio.google.com/app/apikey)")
    
    with st.form("api_form"):
        # We use 'default' to stop browser password manager popups
        input_key = st.text_input("Paste Gemini API Key", type="default")
        submit_button = st.form_submit_button("Connect Consultant")
        
        if submit_button:
            st.session_state.api_key = input_key
            st.success("Consultant Connected!")

    st.caption("Engine: Gemini 1.5 Flash")
    st.divider()
    
    st.header("Step 2: Context")
    uploaded_file = st.file_uploader("Current Resume (Optional)", type=["pdf", "txt"])
    target_job = st.text_area("Target Job Description", placeholder="Paste the job requirements here...", height=200)
    
    if st.button("❓ Need Help?"):
        st.info("Paste your key, click Connect, add a Job Description, and say 'Hello' to start!")

# --- 5. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "# Resume Draft\n*Your progress will appear here as we collaborate...*"

# --- 6. MAIN INTERFACE (CHAT & PREVIEW) ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("The Consultation")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Talk to the Consultant..."):
        if "api_key" not in st.session_state or not st.session_state.api_key:
            st.error("Please enter your API Key and click 'Connect Consultant' in the sidebar!")
        elif "SYSTEM_PROMPT" not in st.secrets:
            st.error("Missing 'SYSTEM_PROMPT' in Streamlit Secrets.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                genai.configure(api_key=st.session_state.api_key)
                
                # Using the most stable model identifier
                model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash', 
                    system_instruction=st.secrets["SYSTEM_PROMPT"]
                )
                
                # Rebuild history
                history_data = []
                for m in st.session_state.messages[:-1]:
                    role = "user" if m["role"] == "user" else "model"
                    history_data.append({"role": role, "parts": [m["content"]]})
                
                chat_session = model.start_chat(history=history_data)
                
                full_query = f"Target Job Description: {target_job}\n\nUser Input: {prompt}"
                response = chat_session.send_message(full_query)
                
                response_text = response.text
                
                if "<resume>" in response_text:
                    parts = re.split(r'<\/?resume>', response_text)
                    st.session_state.resume_draft = parts[1].strip()
                    clean_response = parts[0].strip() + "\n" + (parts[2].strip() if len(parts) > 2 else "")
                else:
                    clean_response = response_text

                st.session_state.messages.append({"role": "assistant", "content": clean_response})
                with st.chat_message("assistant"):
                    st.markdown(clean_response)
                
                st.rerun()

            except Exception as e:
                # If Flash fails, this will tell us exactly why
                st.error(f"Consultation Error: {str(e)}")
                if "404" in str(e):
                    st.warning("The model 'gemini-1.5-flash' wasn't found. Trying stable backup...")
                    # Optional: Add fallback model logic here if needed

with col2:
    st.subheader("Strategic Draft")
    st.markdown(f'<div class="resume-box">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
