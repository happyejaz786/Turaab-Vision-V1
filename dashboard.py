import streamlit as st

# Pichli dono files se functions import kar rahe hain
from main_app import run_main_app
from app import run_image_gen

# --- 1. DASHBOARD PAGE SETUP ---
# Ye sirf main file mein hona chahiye
st.set_page_config(
    page_title="Turaab Dashboard", 
    page_icon="🌟", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. CREATE TABS ---
# 6 Tabs define kiye gaye hain
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🕌 Welcome", 
    "💬 Turaab AI", 
    "🎨 Vision", 
    "🪄 Image Enhancer", 
    "🎬 Text to Video", 
    "🔬 Research Workspace"
])

# --- TAB 1: WELCOME INTERFACE ---
with tab1:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Bismillah in Arabic script (Green color)
    st.markdown("<h1 style='text-align: center; color: #4CAF50; font-family: \"Amiri\", \"Traditional Arabic\", serif; font-size: 50px;'>بِسْمِ ٱللَّٰهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ</h1>", unsafe_allow_html=True)
    
    # Greeting
    st.markdown("<h3 style='text-align: center; color: #5f6368; font-weight: normal; margin-bottom: 30px;'>Assalāmu ʿalaykum wa-raḥmatu -llāhi wa-barakātuh</h3>", unsafe_allow_html=True)
    
    # --- NEW CALLIGRAPHY BLOCK FOR SALAT WA SALAAM ---
    # Dark charcoal color, large size, with a beautiful classic frame/box
    st.markdown("""
    <div style="display: flex; justify-content: center; margin: 30px 0;">
        <div style="
            background-color: #fdfbf7; 
            border: 3px solid #6d4c41; 
            border-radius: 12px; 
            padding: 25px 40px; 
            box-shadow: 0px 6px 15px rgba(0, 0, 0, 0.1);
            max-width: 800px;
            width: 100%;
        ">
            <p style='text-align: center; color: #212121; font-family: "Amiri", "Traditional Arabic", serif; font-size: 60px; font-weight: bold; margin: 0; line-height: 1.4; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);'>
                اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وَعَلَى آلِ مُحَمَّدٍ
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='width: 50%; margin: 40px auto; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
    
    st.markdown("<h4 style='text-align: center; color: #1a73e8; margin-top: 20px;'>Welcome to Turaab Unified Dashboard</h4>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Upar diye gaye tabs se apna workspace select karein.</p>", unsafe_allow_html=True)

# --- TAB 2: TURAAB AI (main_app.py) ---
with tab2:
    run_main_app()

# --- TAB 3: IMAGE GENERATOR (app.py) ---
with tab3:
    run_image_gen()

# --- TAB 4: IMAGE ENHANCER (Coming Soon) ---
with tab4:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.info("🚀 **Coming Soon: Turaab V2.0** - Image Enhancer (Upscale, Fix, Edit)")
    st.markdown("<p style='color: #666;'>Yahan par future mein images ko edit aur enhance karne ka tool lagaya jayega.</p>", unsafe_allow_html=True)

# --- TAB 5: TEXT TO VIDEO (Coming Soon) ---
with tab5:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.info("🚀 **Coming Soon: Turaab V2.0** - Text to Video AI Generation")
    st.markdown("<p style='color: #666;'>AI ki madad se text ko cinematic video mein badalne ka feature yahan aayega.</p>", unsafe_allow_html=True)

# --- TAB 6: RESEARCH WORKSPACE (Coming Soon) ---
with tab6:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.info("🚀 **Coming Soon: Turaab V2.0** - Research Workspace")
    st.markdown("<p style='color: #666;'>This Tab is for research purpose only.(Drafts & Prompt Testing)</p>", unsafe_allow_html=True)