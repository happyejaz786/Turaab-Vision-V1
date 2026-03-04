import streamlit as st
import easyocr
import google.generativeai as genai
from PIL import Image
import numpy as np
import ssl
import random
import time
from fpdf import FPDF
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# SSL Fix for models download
ssl._create_default_https_context = ssl._create_unverified_context

# --- CONFIGURATION ---
st.set_page_config(page_title="Turaab Vision V2.0", page_icon="📄", layout="centered")

# --- ARABIC BISMILLAH & TITLE ---
st.markdown("<h2 style='text-align: center; color: #4CAF50;'>بِسْمِ ٱللَّٰهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ</h2>", unsafe_allow_html=True)
st.title("📄 Turaab Vision - V2.0 (Stable & Fast)")

# --- FIREBASE SETUP ---
db = None
try:
    if not firebase_admin._apps:
        firebase_creds = dict(st.secrets["firebase"])
        if "private_key" in firebase_creds:
            firebase_creds["private_key"] = firebase_creds["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(firebase_creds)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception:
    st.warning("⚠️ Firebase connect nahi hua, par app chalti rahegi.")

# --- GEMINI STABLE API SETUP ---
try:
    API_KEYS = st.secrets["gemini"]["api_keys"]
    CURRENT_API_KEY = random.choice(API_KEYS)
    # Sahi aur Stable API Configuration
    if CURRENT_API_KEY:
        genai.configure(api_key=CURRENT_API_KEY)
except Exception:
    CURRENT_API_KEY = None
    st.error("API Keys missing in Streamlit Secrets!")

# --- FUNCTIONS ---
@st.cache_resource
def load_ocr_reader():
    # Memory safe OCR loading
    return easyocr.Reader(['en', 'hi'], gpu=False)

def create_pdf(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Turaab Vision - Mission Summary", ln=1, align='C')
    pdf.ln(10)
    
    clean_text = text_content.replace('₹', 'Rs.').replace('*', '')
    safe_text = clean_text.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf.multi_cell(0, 10, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# --- MAIN UI ---
uploaded_file = st.file_uploader("Upload Document Image (JPG, PNG)", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, width=400)
    
    if st.button("🚀 Process Document"):
        if not CURRENT_API_KEY:
            st.error("API Key missing hai, process aage nahi badh sakta.")
        else:
            with st.spinner("AI Analysis chal raha hai... (Stable Mode)"):
                try:
                    # 1. OCR Section
                    reader = load_ocr_reader()
                    img_array = np.array(img)
                    ocr_result = reader.readtext(img_array, detail=0)
                    extracted_text = " ".join(ocr_result)
                    
                    # 2. Gemini Analysis Prompt
                    prompt = f"""
                    System Role: Professional Educator & Analytical Summarizer.
                    Task: Decode text from OCR and summarize for students.
                    1. Identify Document/Topic Type.
                    2. Provide detailed Executive Summary.
                    3. Extract Key Points in simple bullet points.
                    
                    OCR RAW: {extracted_text}
                    """
                    
                    # 3. FAST MODELS POOL (Aapki List Ke Mutabiq)
                    FAST_MODELS = [
                        "gemini-2.5-flash-lite",   # Aapki list se 
                        "gemini-2.0-flash-lite",   # Aapki list se 
                        "gemini-flash-latest"      # Aapki list se 
                    ]
                    
                    report_text = None
                    
                    # 4. AUTO-RETRY & ROTATION LOGIC
                    for attempt, model_name in enumerate(FAST_MODELS):
                        try:
                            # Naye Client() ki jagah GenerativeModel() ka use
                            model = genai.GenerativeModel(model_name)
                            response = model.generate_content([prompt, img])
                            report_text = response.text
                            
                            st.success(f"✅ Analysis Complete! (Powered by: {model_name})")
                            break # Success! Loop se bahar aayein
                            
                        except Exception as api_err:
                            error_message = str(api_err)
                            if "503" in error_message or "429" in error_message:
                                if attempt < len(FAST_MODELS) - 1:
                                    st.warning(f"⚠️ {model_name} par load hai. Agle model par switch kar raha hoon...")
                                    time.sleep(2)
                                else:
                                    st.error("❌ Google ke sabhi fast servers abhi busy hain. Kripya thodi der baad try karein.")
                            else:
                                st.error(f"❌ Gemini Error: {error_message}")
                                break
                    
                    # 5. RENDER UI & SAVE DATA
                    if report_text:
                        # Save to Firebase safely
                        if db is not None:
                            try:
                                db.collection('scans').add({'timestamp': datetime.now(), 'summary': report_text})
                            except Exception:
                                pass # Agar save nahi hua toh app crash nahi hogi
                                
                        st.subheader("💡 Mission Summary Report")
                        st.markdown(report_text)
                        
                        with st.expander("See Raw Extracted Text"):
                            st.write(extracted_text)
                        
                        # PDF Download Generation
                        st.markdown("---")
                        pdf_data = create_pdf(report_text)
                        st.download_button(
                            label="📥 Download PDF", 
                            data=pdf_data, 
                            file_name=f"Turaab_Report_{datetime.now().strftime('%H%M%S')}.pdf"
                        )
                        
                except Exception as err:
                    st.error(f"System Error: {err}")

