import streamlit as st
import google.generativeai as genai
import re

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Executive Resume Consultant", layout="wide")

# --- 2. PROFESSIONAL INTERFACE ---
st.title("💼 Executive Resume Strategist")
st.markdown("""
    ### *Strategic Career Partnership*
    **How to start:** 1. Connect API Key. 2. Paste Job Description. 3. Upload current resume (optional).
""")

with st.sidebar:
    st.header("1. Authorization")
    st.markdown("[🔗 Get Gemini API Key](https://aistudio.google.com/app/apikey)")
    
    user_key = st.text_input("API Key", type="default", autocomplete="off")
    
    if st.button("Connect Consultant"):
        if user_key:
            st.session_state.api_key = user_key
            st.success("Consultant Connected!")

    st.divider()
    st.header("2. Context")
    target_job = st.text_area("Target Job Description", placeholder="Paste here...", height=150)
    
    # RESTORED: Resume Input
    uploaded_file = st.file_uploader("Upload Current Resume (Optional)", type=["pdf", "txt"])

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "Your draft will appear here..."

# --- 4. THE CONSULTATION LOGIC ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Consultation")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Talk to the Consultant..."):
        if "api_key" not in st.session_state:
            st.error("Please connect your API Key in the sidebar.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            try:
                genai.configure(api_key=st.session_state.api_key, transport='rest')
                model = genai.GenerativeModel(model_name='gemini-1.5-flash')
                
                # FIXED: Safe Resume Decoding
                resume_context = ""
                if uploaded_file:
                    try:
                        # Attempt standard text decoding
                        resume_context = f"USER'S CURRENT RESUME DATA: {uploaded_file.getvalue().decode('utf-8')}"
                    except UnicodeDecodeError:
                        # Fallback for PDFs or binary files
                        resume_context = "USER UPLOADED A BINARY FILE (PDF/DOCX). ASSUME THEY WANT TO START FROM SCRATCH OR PROVIDE DETAILS MANUALLY."

                full_context = f"""
                SYSTEM PROMPT: {st.secrets.get('SYSTEM_PROMPT', 'You are a resume expert.')}
                TARGET JOB: {target_job}
                {resume_context}
                
                HISTORY: {[m['content'] for m in st.session_state.messages[:-1]]}
                USER INPUT: {prompt}
                """
                
                response = model.generate_content(full_context)
                
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

with col2:
    st.subheader("Strategic Draft")
    st.markdown(f'<div style="background-color:#f8f9fa;padding:20px;border-radius:15px;height:75vh;overflow-y:auto;border:1px solid #dee2e6">{st.session_state.resume_draft}</div>', unsafe_allow_html=True)
