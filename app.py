import streamlit as st
import google.generativeai as genai
import re

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="Executive Resume Consultant", layout="wide")

# --- 2. PROFESSIONAL BRANDING ---
st.title("💼 Executive Resume Strategist")
st.markdown("""
    ### *Transforming experience into impact.*
    **Instructions:** 1. Connect Key. 2. Paste Job Description. 3. Say 'Hello'.
""")

# --- 3. SIDEBAR SETUP ---
with st.sidebar:
    st.header("Step 1: Setup")
    st.markdown("[🔗 Get Gemini API Key](https://aistudio.google.com/app/apikey)")
    
    # Using 'default' avoids browser password popups
    user_key = st.text_input("Paste API Key", type="default", autocomplete="off")
    
    if st.button("Connect Consultant"):
        if user_key:
            st.session_state.api_key = user_key
            st.success("Consultant Connected!")

    st.divider()
    st.header("Step 2: Context")
    target_job = st.text_area("Target Job Description", placeholder="Paste requirements here...", height=200)
    uploaded_file = st.file_uploader("Current Resume (Optional)", type=["pdf", "txt"])

# --- 4. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "# Resume Draft\n*Your progress will appear here...*"

# --- 5. MAIN INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Consultation")
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
                # MANDATORY FIX: Force stable v1 and REST transport
                genai.configure(api_key=st.session_state.api_key, transport='rest')
                
                # We use the specific stable model name
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                
                # Safe Resume Decoding
                resume_text = ""
                if uploaded_file:
                    try:
                        resume_text = f"User Resume: {uploaded_file.getvalue().decode('utf-8')}"
                    except:
                        resume_text = "User uploaded a file (PDF/Binary). Ask for specific details."

                # Construct full context package
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                full_query = f"""
                SYSTEM PROMPT: {st.secrets['SYSTEM_PROMPT']}
                TARGET JOB: {target_job}
                {resume_text}
                
                HISTORY: {history}
                USER INPUT: {prompt}
                """

                # Direct generation call to avoid the 'v1beta' error
                response = model.generate_content(full_query)
                
                # Update UI
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
                # If it fails, show the exact raw error for a final review
                st.error(f"Consultation Error: {str(e)}")

with col2:
    st.subheader("Strategic Draft")
    st.markdown(f'<div style="background-color:#f8f9fa;padding:25px;border-radius:15px;height:75vh;overflow-y:auto;border:1px solid #e9ecef">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
