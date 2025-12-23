import streamlit as st
import google.generativeai as genai

# --- APP CONFIG ---
st.set_page_config(page_title="Executive Resume Consultant", layout="wide")
st.title("💼 Executive Resume Strategy Consultant")

# --- SIDEBAR: API KEY & FAST TRACK ---
with st.sidebar:
    st.header("Setup")
    user_api_key = st.text_input("Enter your Gemini API Key", type="password")
    st.info("Get a free key at [Google AI Studio](https://aistudio.google.com/)")
    
    st.divider()
    st.header("Fast Track (Optional)")
    uploaded_file = st.file_uploader("Upload current resume (PDF/Text)", type=["pdf", "txt"])
    job_desc = st.text_area("Paste Target Job Description")
    if st.button("Initialize with Data"):
        st.session_state.fast_track = True
        st.success("Data loaded! Start the chat to begin.")

# --- SYSTEM PROMPT (YOUR HIDDEN GEM) ---
SYSTEM_PROMPT = """
Role: You are an expert Executive Resume Consultant... [INSERT YOUR FULL PROMPT HERE] ...
ADDITIONAL INSTRUCTION: You are connected to a live preview window. 
Whenever you finalize a section or a bullet point, wrap the updated resume text in 
<resume_update> tags so the app can display it on the right.
"""

# --- CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_draft" not in st.session_state:
    st.session_state.resume_draft = "Your resume draft will appear here as we collaborate..."

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Consultation")
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Answer the Consultant..."):
        # Process and send to Gemini...
        # (This is where the API call happens)
        st.session_state.messages.append({"role": "user", "content": prompt})
        # [Simplified for brevity: You'd use genai.GenerativeModel here]

with col2:
    st.subheader("Live Resume Draft")
    st.markdown(f"```markdown\n{st.session_state.resume_draft}\n```")
