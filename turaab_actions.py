import os
import subprocess
#import pyautogui
import time
#import pygetwindow as gw
import psutil
import difflib  # NEW: For V3.0 Smart Fuzzy Matching

# --- V3.0 LAYER 1: THE MASTER DICTIONARY ---
APP_ALIASES = {
    "notepad": "notepad",
    "chrome": "chrome",
    "google": "chrome",
    "browser": "chrome",
    "excel": "excel",
    "msword": "winword",
    "word": "winword",
    "calculator": "calc",
    "calc": "calc",
    "edge": "msedge",
    "msedge": "msedge",
    "powerpoint": "powerpnt",
    "ppt": "powerpnt",
    "paint": "mspaint",
    "mspaint": "mspaint",
    "cmd": "cmd",
    "settings": "ms-settings:",
    "youtube": "chrome www.youtube.com" # Quick Win added!
}

# --- V3.0 THE SMART BRAIN FUNCTION ---
def get_smart_app_name(user_input):
    """4-Layer Filter: Aadhure ya ghalat spelling ko sahi app mein badalta hai."""
    user_input = user_input.lower().strip()
    
    # Layer 1: Exact Match Check (Agar seedha dictionary mein mil jaye)
    if user_input in APP_ALIASES:
        return APP_ALIASES[user_input], True
    
    # Layer 2: Substring Match (Jaise 'msw' se 'msword' pakadna)
    for alias, true_cmd in APP_ALIASES.items():
        if user_input in alias:  # Agar user ka aadhura word alias ke andar hai
            return true_cmd, True
            
    # Layer 3: Fuzzy Logic Core (Typo/Spelling mistakes jaise 'crome')
    # cutoff=0.6 ka matlab hai 60% similarity honi chahiye
    matches = difflib.get_close_matches(user_input, APP_ALIASES.keys(), n=1, cutoff=0.6)
    if matches:
        return APP_ALIASES[matches[0]], True
        
    # Layer 4: Universal Fallback (Agar kuch samajh na aaye toh wahi try karo)
    return user_input, False

# --- V3.3 SYSTEM OPENER (NLP-Lite & Portal Engine) ---
# --- V3.4 SYSTEM OPENER (True Intelligence & Fallback Engine) ---
def execute_system_command(app_name):
    """Understands intent, fixes URLs, and auto-Googles unknown commands."""
    try:
        # Command ko clean karo
        cmd_text = app_name.replace("open ", "").replace("launch ", "").strip().lower()

        # 1. THE ENTERPRISE PORTAL DICTIONARY (Ab https:// ke sath)
        SMART_PORTALS = {
            "manav sampada": "https://ehrms.upsdc.gov.in",
            "upmsp": "https://upmsp.edu.in",
            "whatsapp": "https://web.whatsapp.com",
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com"
        }
        
        # 2. BROWSER DETECTOR
        BROWSERS = ["chrome", "edge", "msedge", "brave", "firefox"]
        selected_browser = None
        
        for b in BROWSERS:
            if b in cmd_text:
                selected_browser = b
                cmd_text = cmd_text.replace(b, "").strip()
                break
        
        # 3. NLP STOP-WORD REMOVAL
        STOP_WORDS = [" in ", " on ", " using ", " with ", " me ", " par ", " se "]
        for word in STOP_WORDS:
            if word in cmd_text:
                cmd_text = cmd_text.replace(word, " ").strip()
        
        target = cmd_text.strip()
        final_url = ""
        
        # 4. PORTAL MATCHING
        for key, url in SMART_PORTALS.items():
            if key in target:
                final_url = url
                break
        
        if not final_url and "." in target and not target.endswith(".exe"):
            # Agar direct URL diya hai, toh ensure karo https laga ho
            final_url = target if target.startswith("http") else f"https://{target}"
            
        # --- 5. THE TRUE INTELLIGENCE CORE ---
        
        # SCENARIO A: Portal ya URL mil gaya
        if final_url:
            if selected_browser:
                smart_browser, _ = get_smart_app_name(selected_browser)
                subprocess.Popen(["cmd", "/c", f"start {smart_browser} {final_url}"], shell=True)
                return f"🌐 Opening Portal in '{smart_browser}'... 🚀"
            else:
                # Ab https:// laga hai, toh default browser automatically khulega, error nahi aayega!
                subprocess.Popen(["cmd", "/c", f"start {final_url}"], shell=True)
                return f"🌐 Opening '{target}' in Default Browser... 🚀"

        # SCENARIO B: Portal nahi hai, App check karo
        smart_name, is_smart_match = get_smart_app_name(target)
        
        if is_smart_match:
            # App mil gaya (Layer 1/2/3 pass)
            subprocess.Popen(["cmd", "/c", f"start {smart_name}"], shell=True)
            return f"💻 Launching App: '{smart_name}'... 🚀"
            
        else:
            # SCENARIO C: THE ULTIMATE FALLBACK (App nahi mila -> Google Search)
            # URL safe text banata hai (e.g., spaces ko %20 mein badalna)
            import urllib.parse
            search_query = urllib.parse.quote(target)
            google_search_url = f"https://www.google.com/search?q={search_query}"
            
            if selected_browser:
                smart_browser, _ = get_smart_app_name(selected_browser)
                subprocess.Popen(["cmd", "/c", f"start {smart_browser} {google_search_url}"], shell=True)
                return f"🔍 System didn't find '{target}'. Googling it in {smart_browser}... 🚀"
            else:
                subprocess.Popen(["cmd", "/c", f"start {google_search_url}"], shell=True)
                return f"🔍 System didn't find '{target}'. Googling it... 🚀"
                
    except Exception as e: 
        return f"Launch Error: {str(e)}"
      
# --- V3.0 THE SYSTEM HEALTH MONITOR ---
def get_system_health():
    """Fetches real-time CPU, RAM, and Battery status."""
    try:
        # 1. CPU Check
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # 2. RAM Check (Convert bytes to GB)
        ram = psutil.virtual_memory()
        ram_total = round(ram.total / (1024**3), 2)
        ram_used = round(ram.used / (1024**3), 2)
        ram_percent = ram.percent
        
        # 3. Battery Check (Agar laptop hai)
        battery = psutil.sensors_battery()
        batt_str = ""
        if battery:
            plugged = "Plugged In ⚡" if battery.power_plugged else "On Battery 🔋"
            batt_str = f"🔋 **Battery:** {battery.percent}% ({plugged})"
        else:
            batt_str = "🔋 **Battery:** Desktop PC (No Battery detected)"
            
        # 4. Generate Professional Report
        report = (
            f"🩺 **Turaab PC Vitals Report:**\n\n"
            f"🖥️ **CPU Load:** {cpu_usage}%\n"
            f"🧠 **RAM Usage:** {ram_used} GB / {ram_total} GB ({ram_percent}%)\n"
            f"{batt_str}"
        )
        return report
    except Exception as e:
        return f"⚠️ Health Check Error: {str(e)}"
    
    # --- V3.0 TARGETED SMART TYPING ---
def type_text_automation(command_text):
    """Types text either globally or in a specific app using the Smart Brain."""
    try:
        # Check agar command mein " in " likha hai (e.g., 'Hello in notepad')
        if " in " in command_text.lower():
            # Text aur App name ko alag alag karo
            parts = command_text.rsplit(" in ", 1)
            text_to_type = parts[0].strip()
            app_name = parts[1].strip()
            
            # Hamare Smart Brain se app ka asli naam pata karo
            smart_name, _ = get_smart_app_name(app_name)
            
            # App kholo
            subprocess.Popen(["cmd", "/c", f"start {smart_name}"], shell=True)
            
            # App ko khulne ke liye 2.5 second ka time do (safe side)
            time.sleep(2.5) 
            
            # Type kar do
            pyautogui.write(text_to_type, interval=0.05)
            return f"📝 Typed '{text_to_type}' in '{smart_name}' successfully! 🚀"
            
        else:
            # Normal mode (bina app bataye, jahan mouse hoga wahan type karega)
            time.sleep(2.5)
            pyautogui.write(command_text, interval=0.05)
            return f"📝 Typed text successfully! 🚀"
            
    except Exception as e:
        return f"⚠️ Typing Error: {str(e)}"
