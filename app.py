import streamlit as st
import google.generativeai as genai
import re
import os

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Executive Resume Consultant", layout="wide")
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

# --- 3. BRANDING & HERO ---
st.title("💼 Executive Resume Strategist")
st.markdown("""
    ### *Transforming experience into impact.*
    **How to Start:** 1. Connect your API key. 2. Choose a Model version. 3. Type **"Hello"** to begin.
""")

# --- 4. SIDEBAR: AUTHORIZATION & MODEL CHOICE ---
with st.sidebar:
    st.header("Step 1: Authorization")
    st.markdown("[🔗 Get your FREE Gemini API Key here](https://aistudio.google.com/app/apikey)")
    
    with st.form("api_form"):
        input_key = st.text_input("Paste Gemini API Key", type="default")
        submit_button = st.form_submit_button("Connect Consultant")
        if submit_button:
            st.session_state.api_key = input_key
            st.success("Consultant Connected!")

    # NEW: Let the user choose the engine
    st.divider()
    st.header("Step 2: Engine Selection")
    model_choice = st.selectbox(
        "Select AI Model",
        ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"],
        help="If you get a 404 error, try switching to a different model version here."
    )
    
    st.divider()
    st.header("Step 3: Context")
    uploaded_file = st.file_uploader("Current Resume (Optional)", type=["pdf", "txt"])
    target_job = st.text_area("Target Job Description", placeholder="Paste requirements here...", height=150)

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
                
                # Use the user's selected model
                model = genai.GenerativeModel(
                    model_name=model_choice, 
                    system_instruction=st.secrets["SYSTEM_PROMPT"]
                )
                
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
                st.error(f"Consultation Error: {str(e)}")
                if "404" in str(e):
                    st.info("💡 **Tip:** This model version might not be available for your account yet. Try selecting a different version from the sidebar (e.g., 'gemini-1.5-pro' or 'gemini-pro') and try again.")

with col2:
    st.subheader("Strategic Draft")
    st.markdown(f'<div class="resume-box">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
