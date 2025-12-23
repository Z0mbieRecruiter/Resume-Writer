import streamlit as st
import google.generativeai as genai
import re

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Executive Resume Consultant", layout="wide")

# --- 2. PROFESSIONAL STYLING ---
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

# --- 3. RESTORED INSTRUCTIONS & BRANDING ---
st.title("💼 Executive Resume Strategist")
st.markdown("""
    ### *Transforming experience into impact.*
    This tool is a **Strategic Consultant** that interviews you to align your history with your target role.
    
    **How to Start:** 1. Enter your **Gemini API Key** in the sidebar and click **Connect**. 
    2. Provide your **Job Description** (and resume if you have one). 
    3. Type **"Hello"** in the chat to begin your consultation.
""")

# --- 4. SIDEBAR (Fixed Password & API Logic) ---
with st.sidebar:
    st.header("Step 1: Setup")
    st.markdown("[🔗 Get your FREE Gemini API Key here](https://aistudio.google.com/app/apikey)")
    
    # Using 'label_visibility' and 'autocomplete' to stop browser password popups
    input_key = st.text_input(
        "Paste Gemini API Key", 
        type="default", 
        autocomplete="off",
        placeholder="Enter key here..."
    )
    
    if st.button("Connect Consultant"):
        if input_key:
            st.session_state.api_key = input_key
            st.success("Consultant Connected!")
        else:
            st.error("Please paste a key first.")

    st.divider()
    st.header("Step 2: Context")
    target_job = st.text_area("Target Job Description", placeholder="Paste requirements here...", height=200)
    uploaded_file = st.file_uploader("Current Resume (Optional)", type=["pdf", "txt"])

# --- 5. INITIALIZE STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "# Resume Draft\n*Your progress will appear here...*"

# --- 6. MAIN INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Consultation")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Talk to the Consultant..."):
        if "api_key" not in st.session_state:
            st.error("Please connect your API Key in the sidebar first.")
        elif "SYSTEM_PROMPT" not in st.secrets:
            st.error("Missing 'SYSTEM_PROMPT' in Streamlit Secrets.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                genai.configure(api_key=st.session_state.api_key)
                
                # --- SMART MODEL SELECTION ---
                # We try the best models in order of capability
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                # Preferred order: Flash 1.5 -> Pro 1.5 -> Pro 1.0
                model_to_use = "gemini-1.5-flash" # Default
                if "models/gemini-1.5-flash" not in available_models:
                    if "models/gemini-pro" in available_models:
                        model_to_use = "gemini-pro"
                
                model = genai.GenerativeModel(
                    model_name=model_to_use,
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
                
                # Parsing logic
                res_text = response.text
                if "<resume>" in res_text:
                    parts = re.split(r'<\/?resume>', res_text)
                    st.session_state.resume_draft = parts[1].strip()
                    clean_res = parts[0].strip() + "\n" + (parts[2].strip() if len(parts) > 2 else "")
                else:
                    clean_res = res_text

                st.session_state.messages.append({"role": "assistant", "content": clean_res})
                with st.chat_message("assistant"):
                    st.markdown(clean_res)
                st.rerun()

            except Exception as e:
                st.error(f"Consultation Error: {str(e)}")
                if "API_KEY_INVALID" in str(e):
                    st.info("💡 Your API key wasn't recognized. Make sure you copied the full string correctly from AI Studio.")

with col2:
    st.subheader("Strategic Draft")
    st.markdown(f'<div class="resume-box">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
