import streamlit as st
import google.generativeai as genai
import re

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="Executive Resume Strategist", layout="wide")

# --- 2. THE CONSULTANT STYLING ---
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

# --- 3. BRANDING & UI ---
st.title("💼 Executive Resume Strategist")
st.markdown("### *Strategic Career Partnership*")

# --- 4. SIDEBAR (Simplified to avoid browser password interference) ---
with st.sidebar:
    st.header("Step 1: Setup")
    st.markdown("[🔗 Get Gemini API Key](https://aistudio.google.com/app/apikey)")
    
    # We use 'default' type and autocomplete="off" to stop password popups
    user_key = st.text_input("Paste API Key", type="default", autocomplete="off")
    
    if st.button("Connect Consultant"):
        if user_key:
            st.session_state.api_key = user_key
            st.success("Consultant Connected!")
        else:
            st.error("Please enter a key.")

    st.divider()
    st.header("Step 2: Context")
    target_job = st.text_area("Target Job Description", placeholder="Paste requirements here...", height=200)
    uploaded_file = st.file_uploader("Upload Current Resume (Optional)", type=["txt"])

# --- 5. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "Your draft will appear here..."

# --- 6. MAIN INTERFACE: CHAT & PREVIEW ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Consultation")
    # Display message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input Logic
    if prompt := st.chat_input("Talk to the Consultant..."):
        if "api_key" not in st.session_state:
            st.error("Please connect your API Key in the sidebar.")
        else:
            # Add user message to UI
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                # FORCE THE CONNECTION: This bypasses the library's 'Beta' default
                genai.configure(api_key=st.session_state.api_key, transport='rest')
                
                # We use the direct model name (no models/ prefix for maximal compatibility)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Handling File Content
                resume_content = ""
                if uploaded_file:
                    try:
                        resume_content = f"Existing Resume: {uploaded_file.getvalue().decode('utf-8')}"
                    except:
                        resume_content = "File uploaded, but could not be read as text."

                # BUILDING THE PROMPT MANUALLY (Stability Fix)
                # Instead of 'start_chat', we send the history as text.
                history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
                
                # Pull system prompt from secrets safely
                system_instr = st.secrets.get("SYSTEM_PROMPT", "You are a resume consultant.")
                
                final_input = f"""
                {system_instr}
                
                TARGET JOB: {target_job}
                {resume_content}
                
                CONVERSATION HISTORY:
                {history_text}
                
                LATEST RESPONSE FROM USER: {prompt}
                """
                
                # Direct generation call
                response = model.generate_content(final_input)
                
                # Process AI Response
                response_text = response.text
                if "<resume>" in response_text:
                    parts = re.split(r'<\/?resume>', response_text)
                    st.session_state.resume_draft = parts[1].strip()
                    clean_res = parts[0].strip() + "\n" + (parts[2].strip() if len(parts) > 2 else "")
                else:
                    clean_res = response_text

                # Update UI with Assistant message
                st.session_state.messages.append({"role": "assistant", "content": clean_res})
                with st.chat_message("assistant"):
                    st.markdown(clean_res)
                
                # Refresh page to show updates
                st.rerun()

            except Exception as e:
                st.error(f"Consultation Error: {str(e)}")

with col2:
    st.subheader("Strategic Draft")
    # Styled draft box
    st.markdown(f'<div class="resume-box">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
