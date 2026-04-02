import streamlit as st
from google import genai
from PIL import Image
import os
import asyncio
import json
import uuid
import re
from prompt_manager import PromptLibraryManager

try:
    import edge_tts
except ImportError:
    st.error("⚠️ Module 'edge-tts' not found.")

# --- 1. PASSWORD PROTECTED DIALOG (FIXED) ---
@st.dialog("🔐 Secret Prompt Vault")
def show_secret_prompt(prompt_text):
    pwd = st.text_input("Enter Master Password:", type="password")
    if st.button("Unlock"):
        if pwd == "turaab786":
            st.success("Access Granted!")
            st.text_area("AI Prompt (Internal Use Only):", value=prompt_text, height=200)
        elif pwd:
            st.error("Access Denied!")

def run_main_app():
    # --- 2. THE FINAL 'KACHRA-FREE' CSS ---
    st.markdown("""
        <style>
        #MainMenu, footer, .stDeployButton {visibility: hidden;}

        /* FIXED CHAT INPUT - 750px Centered Box */
        div[data-testid="stChatInput"] {
            position: fixed !important;
            bottom: 30px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: 750px !important;
            z-index: 9999 !important;
            background: white !important;
            border-radius: 15px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
        }
        .main .block-container { padding-bottom: 150px !important; }

        /* --------------------------------------------------- */
        /* FILE UPLOADER CSS - REMOVING ALL THE JUNK TEXT      */
        /* --------------------------------------------------- */
        
        /* 1. Hide the "Drag and drop" and "Limit 200MB" text completely */
        [data-testid="stSidebar"] [data-testid="stFileUploader"] section > div > span,
        [data-testid="stSidebar"] [data-testid="stFileUploader"] section > div > small,
        [data-testid="stSidebar"] [data-testid="stFileUploader"] section > div > p {
            display: none !important; 
        }

        /* 2. Make the container super small and clean */
        [data-testid="stSidebar"] [data-testid="stFileUploader"] section {
            padding: 5px !important;
            min-height: 0px !important;
            border: 2px dashed #1a73e8 !important;
            background-color: transparent !important;
        }

        /* 3. Make the "Browse files" button take full width */
        [data-testid="stSidebar"] [data-testid="stFileUploader"] section button {
            width: 100% !important;
            margin: 0 !important;
            font-weight: bold !important;
        }

        /* 4. PIN UPLOADER TO BOTTOM OF SIDEBAR */
        [data-testid="stSidebar"] div:has(> [data-testid="stFileUploader"]) {
            position: -webkit-sticky !important;
            position: sticky !important;
            bottom: 0 !important;
            background-color: #f8f9fa !important; /* matches sidebar bg */
            padding-top: 15px !important;
            padding-bottom: 20px !important;
            border-top: 1px solid #ddd !important;
            z-index: 99 !important;
        }

        .sidebar-header { 
            font-size: 16px; font-weight: bold; color: #1a73e8; margin-top: 5px; border-bottom: 1px solid #ddd; padding-bottom: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- 3. CONFIGURATION & SESSIONS ---
    SESSION_FILE = "chat_sessions.json"
    PROMPT_FILE = "prompt_bank.json"
    prompt_engine = PromptLibraryManager(PROMPT_FILE)

    if "sessions" not in st.session_state:
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r", encoding='utf-8') as f:
                    st.session_state.sessions = json.load(f)
            except: st.session_state.sessions = {}
        else: st.session_state.sessions = {}

    if "current_chat_id" not in st.session_state or not st.session_state.sessions:
        new_id = str(uuid.uuid4())
        st.session_state.sessions[new_id] = {"title": "New chat", "messages": []}
        st.session_state.current_chat_id = new_id

    # --- 4. SMART AI ENGINE WITH FULL ROTATION ---
    def ai_smart_engine(prompt, file_obj=None):
        try: api_keys = st.secrets["gemini"]["api_keys"]
        except Exception: return "Error: API Keys missing in st.secrets."
            
        latest_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest", "gemini-3.1-pro-preview"]
        
        for key in api_keys:
            try:
                client = genai.Client(api_key=key)
                for model_name in latest_models:
                    try:
                        contents = [prompt]
                        if file_obj: contents.insert(0, file_obj)
                        res = client.models.generate_content(model=model_name, contents=contents)
                        if res and res.text: return res.text
                    except Exception: continue 
            except Exception: continue 
        return "System overload: All API keys and models failed."

    async def generate_voice_auto(text):
        voice_name = "en-US-GuyNeural"
        if re.search(r'[\u0600-\u06FF]', text): voice_name = "ur-PK-AsadNeural"
        elif re.search(r'[\u0900-\u097F]', text): voice_name = "hi-IN-MadhurNeural"
        try:
            clean_text = re.sub(r'[*#_`]', '', text)
            comm = edge_tts.Communicate(f"Bismillaahir-rahman-nir-raheem. {clean_text}", voice_name)
            data = b""
            async for chunk in comm.stream():
                if chunk["type"] == "audio": data += chunk["data"]
            return data
        except Exception: return None

    # --- 5. SIDEBAR (PERFECT ORDER) ---
    with st.sidebar:
        # TOP: NEW CHAT
        st.markdown('<p class="sidebar-header">🛠️ ACTIONS</p>', unsafe_allow_html=True)
        if st.button("➕ New Chat Session", use_container_width=True):
            new_id = str(uuid.uuid4())
            st.session_state.sessions[new_id] = {"title": "New chat", "messages": []}
            st.session_state.current_chat_id = new_id
            st.rerun()

        # MIDDLE: RECENT HISTORY
        st.markdown('<p class="sidebar-header">⏳ RECENT HISTORY</p>', unsafe_allow_html=True)
        for sid, sdata in list(st.session_state.sessions.items()):
            if st.button(sdata["title"][:25], key=f"hist_{sid}", use_container_width=True):
                st.session_state.current_chat_id = sid
                st.rerun()

        # BOTTOM (FIXED VIA CSS): UPLOADER
        st.markdown('<br>', unsafe_allow_html=True)
        up_file = st.file_uploader("Attach Image/PDF", type=["png", "jpg", "jpeg", "pdf"], key="turaab_side_up", label_visibility="collapsed")
        if up_file:
            st.success(f"Selected: {up_file.name}")

    # --- 6. MAIN CHAT DISPLAY ---
    curr_chat = st.session_state.sessions[st.session_state.current_chat_id]
    
    for i, m in enumerate(curr_chat["messages"]):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            
            # Action Buttons Layout
            col1, col2, col3 = st.columns([2, 2, 10])
            if m["role"] == "user":
                if "enhanced" in m:
                    # DIRECT BUTTON FOR PASSWORD LOCK (No Popover = No Bugs)
                    with col1:
                        if st.button("👁️ View Prompt", key=f"eye_{i}"):
                            show_secret_prompt(m["enhanced"])
            else:
                with col1:
                    if st.button("▶ Play Audio", key=f"v_{i}"):
                        with st.spinner("Generating audio..."):
                            audio = asyncio.run(generate_voice_auto(m["content"]))
                            if audio: st.audio(audio, autoplay=True)
                            else: st.error("Audio generation failed.")

    # --- 7. CHAT INPUT LOGIC ---
    if user_input := st.chat_input("Ask Turaab Anything..."):
        if curr_chat["title"] == "New chat":
            curr_chat["title"] = user_input[:20]

        img_obj = None
        file_name = None
        if up_file:
            file_name = up_file.name
            try: img_obj = Image.open(up_file)
            except: pass

        with st.spinner("Turaab is thinking..."):
            enhanced, cat = prompt_engine.generate_and_save_prompt(user_input, has_image=bool(img_obj), file_name=file_name)
            response_text = ai_smart_engine(enhanced, file_obj=img_obj)

        curr_chat["messages"].append({"role": "user", "content": user_input, "enhanced": enhanced, "category": cat})
        curr_chat["messages"].append({"role": "assistant", "content": response_text})
        
        with open(SESSION_FILE, "w", encoding='utf-8') as f:
            json.dump(st.session_state.sessions, f, ensure_ascii=False, indent=4)
        
        st.rerun()

if __name__ == "__main__":
    run_main_app()