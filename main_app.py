import streamlit as st
from google import genai
from PIL import Image
import os
import asyncio
import json
import time
import uuid
import re
import tempfile
from prompt_manager import PromptLibraryManager

try:
    import edge_tts
except ImportError:
    st.error("⚠️ Module 'edge-tts' not found. Please install it using 'pip install edge-tts'")

# --- 1. PAGE SETUP & PURE GEMINI THEME (YOUR EXACT CSS) ---
st.set_page_config(page_title="Turaab AI", page_icon="😊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;} 
    .stDeployButton {display:none;}
    .stApp { background-color: #ffffff; }
    
    [data-testid="stSidebar"] { background-color: #f0f4f9 !important; }
    
    [data-testid="stSidebar"] .stButton > button {
        border: none !important; outline: none !important;
        background-color: transparent !important; box-shadow: none !important;
        color: #3c4043 !important; text-align: left !important;
        justify-content: flex-start !important; width: 100% !important;
        padding: 8px 12px !important; font-size: 14px !important;
        border-radius: 0 24px 24px 0 !important; transition: background 0.2s ease-in-out !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #e1e5ea !important; color: #1a73e8 !important; 
    }

    .sidebar-header { font-size: 13px; color: #5f6368; font-weight: 600; margin: 20px 0 10px 15px; letter-spacing: 0.5px; }

    div.stButton > button[kind="primary"] {
        background-color: #c2e7ff !important; color: #001d35 !important;
        border-radius: 16px !important; font-weight: bold !important;
        padding: 12px 24px !important; margin: 10px 15px !important;
        width: auto !important; box-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
    }

    /* Input Attach Button (+) */
    div[data-testid="stPopover"] > button { 
        border-radius: 50% !important; width: 42px !important; height: 42px !important; 
        display: flex !important; justify-content: center !important; 
        align-items: center !important; border: 1px solid #dadce0 !important;
        background-color: #ffffff !important;
    }

    /* --- POPOVER MENU BUTTON FIX --- */
    div[data-testid="stPopoverBody"] {
        padding: 8px 4px !important; min-width: 180px !important; border-radius: 12px !important;
    }
    div[data-testid="stPopoverBody"] div.stVerticalBlock { gap: 0px !important; }
    div[data-testid="stPopoverBody"] .stButton > button {
        border: none !important; background-color: transparent !important; box-shadow: none !important; 
        color: #3c4043 !important; text-align: left !important; justify-content: flex-start !important; 
        width: 100% !important; padding: 8px 12px !important; min-height: 36px !important; 
        line-height: 1.2 !important; font-size: 14px !important; border-radius: 4px !important; margin-bottom: 2px !important;
    }
    div[data-testid="stPopoverBody"] .stButton > button:hover {
        background-color: #f0f4f9 !important; color: #202124 !important;
    }
    .trans-btn button { padding: 4px 8px !important; border-radius: 8px !important; text-align: center !important; justify-content: center !important;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. ATOMIC SESSION MANAGER ---
SESSION_FILE = "chat_sessions.json"

def load_sessions():
    if not os.path.exists(SESSION_FILE): return {}
    try:
        with open(SESSION_FILE, "r", encoding='utf-8') as f: return json.load(f)
    except Exception: return {} 

def save_sessions(sessions):
    clean_sessions = {}
    for chat_id, chat_data in sessions.items():
        if len(chat_data.get("messages", [])) > 0 or chat_data.get("pinned", False):
            clean_sessions[chat_id] = {
                "title": chat_data.get("title", "New chat"),
                "pinned": chat_data.get("pinned", False),
                "messages": []
            }
            for msg in chat_data.get("messages", []):
                clean_msg = {k: v for k, v in msg.items() if k not in ["audio_bytes"]}
                clean_sessions[chat_id]["messages"].append(clean_msg)
    
    temp_file = SESSION_FILE + ".tmp"
    try:
        with open(temp_file, "w", encoding='utf-8') as f: json.dump(clean_sessions, f, ensure_ascii=False, indent=4)
        os.replace(temp_file, SESSION_FILE)
    except Exception: pass

if "sessions" not in st.session_state: st.session_state.sessions = load_sessions()
if "admin_mode" not in st.session_state: st.session_state.admin_mode = False
if "force_translate" not in st.session_state: st.session_state.force_translate = False

if "current_chat_id" not in st.session_state or st.session_state.current_chat_id not in st.session_state.sessions:
    new_id = str(uuid.uuid4())
    st.session_state.sessions[new_id] = {"title": "New chat", "pinned": False, "messages": []}
    st.session_state.current_chat_id = new_id

current_msgs = st.session_state.sessions[st.session_state.current_chat_id]["messages"]
prompt_engine = PromptLibraryManager()

# --- 3. ENGINES (WITH LATEST MODELS & AUTO-VOICE) ---
def ai_smart_engine(prompt, file_obj=None, doc_path=None):
    try: api_keys = st.secrets["gemini"]["api_keys"]
    except: return "Error: API Keys missing in secrets.toml."
    
    latest_models = ["gemini-3.1-pro-preview", "gemini-3-flash-preview", "gemini-2.0-flash", "gemma-3-27b-it"]
    
    for key in api_keys:
        try:
            client = genai.Client(api_key=key)
            for model_name in latest_models:
                try:
                    contents = [prompt]
                    if file_obj: contents.insert(0, file_obj)
                    elif doc_path:
                        up_f = client.files.upload(file=os.path.abspath(doc_path))
                        contents.insert(0, up_f)
                    res = client.models.generate_content(model=model_name, contents=contents)
                    if res and res.text: return res.text
                except Exception: continue 
        except Exception: continue 
    return "Turaab is taking a breath (Quota Exceeded). Please wait a minute."

def detect_voice(text):
    if re.search(r'[\u0600-\u06FF]', text): return "ur-PK-UzmaNeural"
    elif re.search(r'[\u0900-\u097F]', text): return "hi-IN-MadhurNeural"
    else: return "en-US-GuyNeural"

async def generate_voice_auto(text):
    voice_name = detect_voice(text)
    clean_text = re.sub(r'[*#]', '', text)
    try:
        # Playing Bismillah before speaking, as per your original file
        comm = edge_tts.Communicate(f"Bismillah. {clean_text}", voice_name)
        data = b""
        async for chunk in comm.stream():
            if chunk["type"] == "audio": data += chunk["data"]
        return data
    except: return None

# --- 4. SIDEBAR ---
with st.sidebar:
    if st.button("➕ New chat", type="primary", use_container_width=False):
        new_id = str(uuid.uuid4())
        st.session_state.sessions[new_id] = {"title": "New chat", "pinned": False, "messages": []}
        st.session_state.current_chat_id = new_id
        save_sessions(st.session_state.sessions)
        st.rerun()
    
    st.markdown('<p class="sidebar-header">Recent</p>', unsafe_allow_html=True)
    
    # FIXED: Used v.get("pinned", False) to prevent KeyError with old chats
    valid_sess = {k: v for k, v in st.session_state.sessions.items() if v.get("messages", []) or v.get("pinned", False) or k == st.session_state.current_chat_id}
    sorted_sess = sorted(valid_sess.items(), key=lambda x: x[1].get('pinned', False), reverse=True)
    
    for sess_id, sess_data in sorted_sess:
        col_link, col_pop = st.columns([5, 1])
        icon = "📌" if sess_data.get('pinned', False) else "💬"
        
        if col_link.button(f"{icon} {sess_data['title'][:20]}", key=f"link_{sess_id}"):
            st.session_state.current_chat_id = sess_id
            st.rerun()
            
        with col_pop.popover("⋮"):
            if st.button("📌 Pin", key=f"p_{sess_id}"):
                st.session_state.sessions[sess_id]['pinned'] = not sess_data.get('pinned', False)
                save_sessions(st.session_state.sessions); st.rerun()
            if st.button("🗑️ Delete", key=f"d_{sess_id}"):
                del st.session_state.sessions[sess_id]
                save_sessions(st.session_state.sessions); st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown('<p class="sidebar-header">Language & Translation</p>', unsafe_allow_html=True)
    
    c_lang, c_btn = st.columns([3, 1])
    with c_lang:
        selected_lang = st.radio("Lang", ["English", "Hindi", "Urdu"], index=0, label_visibility="collapsed")
    with c_btn:
        st.markdown('<div class="trans-btn">', unsafe_allow_html=True)
        btn_color = "🟢" if st.session_state.force_translate else "🌐"
        if st.button(btn_color, help="Force Translation to Selected Language"):
            st.session_state.force_translate = not st.session_state.force_translate
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.force_translate:
        st.caption(f"Translation: ON ({selected_lang})")
    else:
        st.caption("Auto-Detect Document Lang")
    
    st.divider()
    with st.expander("⚙️ Settings"):
        pwd = st.text_input("Admin PIN", type="password")
        if pwd == "turaab786" and st.button("📂 Admin DB"):
            st.session_state.admin_mode = True; st.rerun()

# --- 5. ADMIN LOGIC ---
if st.session_state.admin_mode:
    if st.button("🔙 Back"): st.session_state.admin_mode = False; st.rerun()
    if os.path.exists("prompt_bank.json"):
        with open("prompt_bank.json", "r", encoding='utf-8') as f: db = json.load(f)
        for cat in db:
            with st.expander(f"📁 {cat}"):
                for r, m in list(db[cat].items()):
                    col1, col2 = st.columns([9, 1])
                    col1.text_area(f"Q: {r}", m, height=80, key=f"a_{cat}_{r}")
                    if col2.button("🗑️", key=f"del_{cat}_{r}"):
                        del db[cat][r]
                        with open("prompt_bank.json", "w", encoding='utf-8') as f: json.dump(db, f, indent=4, ensure_ascii=False)
                        st.rerun()
    st.stop()

# --- 6. WORKSPACE ---

chat_container = st.container()

with chat_container:
    if not current_msgs:
        st.markdown("<h2 style='text-align: center; margin-top: 15vh; color: #4CAF50;'>بِسْمِ ٱللَّٰهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ</h2>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #5f6368; font-weight: normal;'>Assalaam,,</h3>", unsafe_allow_html=True)

    for i, m in enumerate(current_msgs):
        with st.chat_message(m["role"]):
            if m["role"] == "user":
                # ADDED EYE ICON 👁️
                col1, col2 = st.columns([14, 1])
                col1.markdown(m["content"])
                with col2.popover("👁️"):
                    st.caption("Enhanced Prompt:")
                    st.code(m.get("enhanced", "Original prompt used"), language="text")
            
            elif m["role"] == "assistant":
                # AUTO-VOICE AT THE TOP 🔊
                with st.popover("🔊"):
                    st.write("Play Auto-Detect Voice:")
                    if st.button("▶ Play", key=f"play_{i}"):
                        with st.spinner("Loading audio..."):
                            audio = asyncio.run(generate_voice_auto(m["content"]))
                            if audio: st.audio(audio, autoplay=True)
                st.markdown(m["content"])

active_generation_container = st.container()

st.markdown("<br><br><br>", unsafe_allow_html=True)

# Container 3: Input Area (Renders at the bottom)
c_at, c_in = st.columns([1, 15])
with c_at:
    with st.popover("➕"):
        up_f = st.file_uploader("File", label_visibility="collapsed")

if user_input := c_in.chat_input("Ask Turaab anything..."):
    if st.session_state.sessions[st.session_state.current_chat_id]["title"] == "New chat":
        st.session_state.sessions[st.session_state.current_chat_id]["title"] = user_input[:20]
    
    file_obj, d_path, is_img, file_name = None, None, False, None
    if up_f:
        file_name = up_f.name
        if up_f.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            file_obj, is_img = Image.open(up_f), True
        else:
            d_path = os.path.join("temp_uploads", up_f.name)
            os.makedirs("temp_uploads", exist_ok=True)
            with open(d_path, "wb") as f: f.write(up_f.getbuffer())

    with active_generation_container:
        with st.chat_message("user"): 
            st.markdown(user_input)
        
        with st.chat_message("assistant"):
            st_e = st.empty()
            pb_e = st.empty()
            st_e.markdown("### 😊 Thinking...")
            pb = pb_e.progress(0, text="Analyzing...")
            
            full_q = user_input
            if st.session_state.force_translate:
                full_q += f" (CRITICAL INSTRUCTION: Translate and respond strictly in {selected_lang} language)"

            m_prompt, cat = prompt_engine.generate_and_save_prompt(full_q, has_image=is_img, file_name=file_name)
            
            pb.progress(50, text="Extracting with Gemini 3.1...")
            res = ai_smart_engine(m_prompt, file_obj=file_obj, doc_path=d_path)
            pb.progress(100, text="Done!")
            
            st_e.empty()
            pb_e.empty()
            st.markdown(res)

    # Saved with "enhanced" key for the Eye Icon
    current_msgs.append({"role": "user", "content": user_input, "enhanced": m_prompt})
    current_msgs.append({"role": "assistant", "content": res})
    save_sessions(st.session_state.sessions)
    st.rerun()