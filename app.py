import streamlit as st
import google.generativeai as genai
import re

# --- 1. STABLE CONFIGURATION ---
st.set_page_config(page_title="Executive Resume Strategist", layout="wide")

# --- 2. PROFESSIONAL INTERFACE ---
st.title("💼 Executive Resume Strategist")
st.markdown("""
    ### *Strategic Career Partnership*
    **Instructions:**
    1. Enter your **API Key** below and click **Connect**.
    2. Paste your **Target Job Description**.
    3. Type **"Hello"** to start the consultation.
""")

with st.sidebar:
    st.header("1. Authorization")
    st.markdown("[🔗 Get Gemini API Key](https://aistudio.google.com/app/apikey)")
    
    # type="default" stops the browser from treating this as a 'password'
    user_key = st.text_input("API Key", type="default", autocomplete="off")
    
    if st.button("Connect Consultant"):
        if user_key:
            st.session_state.api_key = user_key
            st.success("Consultant Connected!")
        else:
            st.error("Please enter a key.")

    st.divider()
    st.header("2. Context")
    target_job = st.text_area("Target Job Description", placeholder="Paste the job requirements here...", height=200)

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "Your draft will appear here..."

# --- 4. THE CONSULTATION ---
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
                # FORCE STABLE TRANSPORT: This is the critical line to bypass 404s
                genai.configure(api_key=st.session_state.api_key, transport='rest')
                
                # We call the model using the direct 'v1' stable path
                model = genai.GenerativeModel(model_name='gemini-1.5-flash')
                
                # Bundle everything into a single instruction set for stability
                history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                
                final_prompt = f"""
                SYSTEM INSTRUCTIONS: {st.secrets['SYSTEM_PROMPT']}
                
                JOB DESCRIPTION: {target_job}
                
                CONVERSATION HISTORY:
                {history_text}
                
                USER INPUT: {prompt}
                """
                
                # Direct generation avoids the buggy 'start_chat' beta logic
                response = model.generate_content(final_prompt)
                
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
