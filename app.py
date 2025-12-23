import streamlit as st
import google.generativeai as genai
import re

# --- APP CONFIG ---
st.set_page_config(page_title="Executive Resume Consultant", layout="wide")

# --- STYLING (The Custom Consultant Look) ---
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
    }
    </style>
    """, unsafe_allow_html=True)

# --- BRANDING & INTRO ---
st.title("💼 Executive Resume Strategist")
st.markdown("""
    ### *Transforming experience into impact.*
    This tool is a **Strategic Consultant** that interviews you to align your history with your target role.
    
    **How to Start:** 1. Enter your **Gemini API Key** in the sidebar and click **Connect**. 
    2. Provide your **Job Description** (and resume if you have one). 
    3. Type **"Hello"** to begin your partnership.
""")

# --- SIDEBAR: AUTHORIZATION & CONTEXT ---
with st.sidebar:
    st.header("Step 1: Authorization")
    st.markdown("[🔗 Get your FREE Gemini API Key here](https://aistudio.google.com/app/apikey)")
    
    with st.form("api_form"):
        # type="default" prevents the browser from forcing a 'save password' popup
        input_key = st.text_input("Paste Gemini API Key", type="default", help="The key stays in your browser session.")
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
        st.info("Paste your key, click Connect, add a Job Description, and say 'Hello' in the chat!")

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "# Resume Draft\n*Your progress will appear here as we collaborate...*"

# --- MAIN INTERFACE: CHAT & PREVIEW ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("The Consultation")
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Talk to the Consultant..."):
        if "api_key" not in st.session_state or not st.session_state.api_key:
            st.error("Please enter your API Key and click 'Connect Consultant' in the sidebar!")
        elif "SYSTEM_PROMPT" not in st.secrets:
            st.error("Developer Error: SYSTEM_PROMPT not found in Streamlit Secrets.")
        else:
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                # Configure the AI
                genai.configure(api_key=st.session_state.api_key)
                model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash', 
                    system_instruction=st.secrets["SYSTEM_PROMPT"]
                )
                
                # Format history for Gemini API
                history = [
                    {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} 
                    for m in st.session_state.messages[:-1]
                ]
                
                chat_session = model.start_chat(history=history)
                
                # Combine input with JD context
                full_query = f"Target Job Description: {target_job}\n\nUser Input: {prompt}"
                response = chat_session.send_message(full_query)
                
                # Parse for Resume Updates
                response_text = response.text
                if "<resume>" in response_text:
                    parts = re.split(r'<\/?resume>', response_text)
                    # Update the preview window with the content inside tags
                    st.session_state.resume_draft = parts[1].strip()
                    # Clean the AI's chat response to remove the tags
                    clean_response = parts[0] + (parts[2] if len(parts) > 2 else "")
                else:
                    clean_response = response_text

                # Display Assistant message
                st.session_state.messages.append({"role": "assistant", "content": clean_response})
                with st.chat_message("assistant"):
                    st.markdown(clean_response)
                
                # Refresh to update the Resume Draft column
                st.rerun()

            except Exception as e:
                st.error(f"Consultation Interrupted: {str(e)}")

with col2:
    st.subheader("Strategic Draft")
    # Use Markdown inside a div for better styling
    st.markdown(f'<div class="resume-box">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
