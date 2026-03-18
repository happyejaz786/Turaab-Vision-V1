import streamlit as st
from google import genai
from PIL import Image
import os
import asyncio
import edge_tts
import json
import random
import time
from file_engine import TuraabFileEngine
import turaab_actions

# --- 1. INITIALIZE ENGINES ---
engine = TuraabFileEngine()

# --- 2. SESSION STATE ---
if 'rep' not in st.session_state: st.session_state.rep = None
if 'final_trans' not in st.session_state: st.session_state.final_trans = None
if 'audio_stream' not in st.session_state: st.session_state.audio_stream = None
if 'play_request' not in st.session_state: st.session_state.play_request = False

# --- 3. FUNCTION: BUG-FREE MEMORY MANAGER ---
def manage_history(key, data=None, mode="read"):
    db_path = "history.json"
    history = {}
    if os.path.exists(db_path):
        with open(db_path, "r") as f:
            try: history = json.load(f)
            except: history = {}
    
    if mode == "write":
        # SAFETY LOCK: Kabhi error ko memory mein save mat karo!
        if data and "Error" not in data and "RESOURCE_EXHAUSTED" not in data:
            history[key] = data
            with open(db_path, "w") as f: json.dump(history, f)
            return True
        return False
    return history.get(key)

# --- 4. FUNCTION: SPEECH ENGINE ---
async def generate_voice_output(text, lang_code="English"):
    prefix = "Bismillah hir Rahman nir Raheem. Assalaatu wassaalaamu alaika ya rasool Allah."
    full_message = f"{prefix} {text}"
    voices = {"Urdu": "ur-PK-UzmaNeural", "Hindi": "hi-IN-MadhurNeural", "English": "en-US-GuyNeural"}
    voice = voices.get(lang_code, "en-US-GuyNeural")
    try:
        communicate = edge_tts.Communicate(full_message, voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": audio_data += chunk["data"]
        return audio_data
    except: return None

# --- 5. FUNCTION: ULTIMATE AI CORE (Dual-Model Rescue) ---
def ai_smart_engine(prompt, image=None):
    try:
        api_keys = st.secrets["gemini"]["api_keys"]
    except: return "System Error: API Keys missing in secrets.toml"

    # Agar 2.0 limit zero (0) de raha hai, toh 2.5 par auto-shift ho jayega
    rescue_models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-flash-latest"]
    last_err = ""

    for key in api_keys:
        try:
            client = genai.Client(api_key=key)
            for model in rescue_models:
                try:
                    contents = [image, prompt] if image else prompt
                    res = client.models.generate_content(model=model, contents=contents)
                    if res and res.text: return res.text
                except Exception as e:
                    last_err = str(e)
                    continue # Try next model
        except Exception as e:
            last_err = str(e)
            continue # Try next key
            
    return f"API Limit Error: Please try again tomorrow. Details: {last_err}"

# --- 6. FUNCTION: ACTION CONTROLLER (V3.0 Strict Gatekeeper & Health) ---
def handle_user_action(user_input):
    cmd = user_input.strip().lower()
    
    if cmd == "help": return "COMMANDS: 'open [app]', 'type [text]', 'stop [app]', 'speak [text]', 'play', 'organize', 'pc health'"
    elif cmd.startswith("type "): return turaab_actions.type_text_automation(user_input.strip()[5:])
    elif cmd.startswith("stop "): return turaab_actions.stop_process(cmd.replace("stop ", ""))
    elif cmd.startswith("speak "):
        text_to_say = user_input.strip()[6:]
        st.session_state.audio_stream = asyncio.run(generate_voice_output(text_to_say, "English"))
        return f"Speaking: {text_to_say}"
    elif cmd == "play":
        st.session_state.play_request = True
        return "Select media player from dropdown."
    elif "organize" in cmd: return turaab_actions.organize_junk("D:/Turaab_Test")
    
    # --- V3.0 SYSTEM HEALTH ROUTING ---
    elif cmd in ["system status", "pc health", "health check"]:
        return turaab_actions.get_system_health()
        
    # --- V3.0 STRICT ROUTING ---
    elif cmd.startswith("open "): 
        # Sirf tabhi app khulega jab pehla word 'open ' hoga
        return turaab_actions.execute_system_command(cmd.replace("open ", ""))
    else:
        # V3.0 SECURITY: Agar proper action command nahi mili
        return "⚠️ Incomplete task check and try again...*** (E.g., type 'open msw')"    
    
# --- UI DESIGN ---
st.set_page_config(page_title="Turaab Vision V2.8", layout="wide")

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/10431/10431032.png", width=80)
    st.title("Turaab Control")
    if st.button("🔄 Refresh System Index", use_container_width=True):
        st.success(engine.v23_smart_scan())
        st.balloons()
    if st.button("🗑️ Clear Memory Cache"):
        if os.path.exists("history.json"): os.remove("history.json")
        st.success("Memory Cleared!")

st.markdown("<h1 style='text-align: center; color: #4CAF50;'>بِسْمِ ٱللَّٰهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ</h1>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🔍 Search", "📸 Vision", "🎮 Commander"])

with tab1:
    st.subheader("Drive Search Engine")
    query = st.text_input("Enter filename:")
    if query:
        results = engine.v24_deep_search(query)
        if results:
            st.write(f"🔍 Found {len(results)} items:")
            for r in results:
                with st.expander(r['path']): st.code(r['path'], language="text")
        else: st.warning("No match found. Please Refresh System Index from sidebar.")

with tab2:
    st.subheader("AI Analysis")
    file = st.file_uploader("Upload Image", type=['jpg', 'png'])
    if file:
        st.image(file, width=300)
        if st.button("Analyze Image"):
            mem = manage_history(file.name)
            if mem:
                st.session_state.rep = mem
                st.success("Loaded from Memory.")
            else:
                with st.spinner("Analyzing..."):
                    rep = ai_smart_engine("Summary in 5 bullet points.", Image.open(file))
                    st.session_state.rep = rep
                    manage_history(file.name, rep, "write")
                    
        if st.session_state.rep:
            if "Error" in st.session_state.rep: st.error(st.session_state.rep)
            else: st.info(st.session_state.rep)
            st.write("---")
            sel_lang = st.radio("Translate to:", ["English", "Hindi", "Urdu"], horizontal=True)
            
            if st.button("Translate & Speak"):
                cache_key = f"{file.name}_{sel_lang}"
                cached_trans = manage_history(cache_key)
                if cached_trans:
                    st.session_state.final_trans = cached_trans
                    st.success("Loaded from Memory.")
                else:
                    with st.spinner(f"Translating to {sel_lang}..."):
                        trans_text = ai_smart_engine(f"Translate to {sel_lang}: {st.session_state.rep}")
                        st.session_state.final_trans = trans_text
                        manage_history(cache_key, trans_text, "write")
                
                if "Error" not in st.session_state.final_trans:
                    st.session_state.audio_stream = asyncio.run(generate_voice_output(st.session_state.final_trans, sel_lang))

            if st.session_state.final_trans:
                if "Error" in st.session_state.final_trans: st.error(st.session_state.final_trans)
                else: st.success(st.session_state.final_trans)
                if st.session_state.audio_stream:
                    st.audio(st.session_state.audio_stream)
                    st.session_state.audio_stream = None
                    
# --- TAB 3: COMMANDER (Polished UI & Enter Key Support) ---
with tab3:
    st.subheader("🎮 Universal Action Center")
    
    # st.form ensures pressing 'Enter' works exactly like clicking the button
    with st.form(key="commander_form", clear_on_submit=True):
        # UI Layout: Textbox bada (4) aur button chota (1) ek hi line mein
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_cmd = st.text_input(
                "Enter Command:", 
                label_visibility="collapsed", 
                placeholder="Type command here and press Enter..."
            )
            
        with col2:
            # Form submit button
            submit_btn = st.form_submit_button("Execute 🚀", use_container_width=True)

    # Action Logic
    if submit_btn:
        if user_cmd:
            with st.spinner("Processing..."):
                res = handle_user_action(user_cmd)
                st.success(f"**[{user_cmd}]** -> {res}") # Ye command bhi dikhayega aur result bhi
                
                # Audio check
                if st.session_state.audio_stream:
                    st.audio(st.session_state.audio_stream)
                    st.session_state.audio_stream = None
        else:
            st.warning("⚠️ Please enter a command first.")

    # Play Keyword Extra Logic
    if st.session_state.play_request:
        choice = st.selectbox("Select Player:", ["VLC", "Windows Media Player", "Chrome"])
        if st.button("Launch Player"):
            st.success(turaab_actions.execute_system_command(choice))
            st.session_state.play_request = False
            st.rerun()