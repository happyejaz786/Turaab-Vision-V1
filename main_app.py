import streamlit as st
import easyocr
from google import genai
from PIL import Image
import numpy as np
import ssl
import random
import time
from fpdf import FPDF
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# SSL Fix
ssl._create_default_https_context = ssl._create_unverified_context

st.set_page_config(page_title="Turaab Vision V2.0", page_icon="📄", layout="centered")
st.markdown("<h2 style='text-align: center; color: #4CAF50;'>بِسْمِ ٱللَّٰهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ</h2>", unsafe_allow_html=True)
st.title("📄 Turaab Vision - V2.0 (Lite & Fast)")

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

# --- GEMINI SETUP ---
try:
    API_KEYS = st.secrets["gemini"]["api_keys"]
    CURRENT_API_KEY = random.choice(API_KEYS) 
except Exception:
    CURRENT_API_KEY = None
    st.error("API Keys missing in Streamlit Secrets!")

# Memory-Safe OCR Loading
@st.cache_resource
def load_ocr_reader():
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

# --- UI ---
uploaded_file = st.file_uploader("Upload Document Image", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, width=400)
    
    if st.button("🚀 Process Document"):
        if not CURRENT_API_KEY:
            st.error("API Key missing hai.")
        else:
            with st.spinner("AI Analysis chal raha hai... (Thoda sabr karein)"):
                try:
                    reader = load_ocr_reader()
                    img_array = np.array(img)
                    ocr_result = reader.readtext(img_array, detail=0)
                    extracted_text = " ".join(ocr_result)
                    
                    prompt = f"""
                    System Role: Professional Educator.
                    Task: Decode OCR and summarize.
                    1. Identify Topic.
                    2. Provide Summary.
                    3. Key Points.
                    OCR RAW: {extracted_text}
                    """
                    
                    client = genai.Client(api_key=CURRENT_API_KEY)
                    FAST_MODELS = ["gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-2.0-flash-lite"]
                    
                    report_text = None
                    for attempt, model_name in enumerate(FAST_MODELS):
                        try:
                            response = client.models.generate_content(model=model_name, contents=[prompt, img])
                            report_text = response.text
                            st.success(f"✅ Analysis Complete! (Model: {model_name})")
                            break
                        except Exception as e:
                            if "503" in str(e) or "429" in str(e):
                                if attempt < len(FAST_MODELS) - 1:
                                    st.warning(f"⚠️ {model_name} busy. Switching model...")
                                    time.sleep(2)
                                else:
                                    st.error("❌ Servers busy hain. Thodi der baad try karein.")
                            else:
                                st.error(f"Error: {e}")
                                break
                    
                    if report_text:
                        if db is not None:
                            try:
                                db.collection('scans').add({'timestamp': datetime.now(), 'summary': report_text})
                            except:
                                pass
                        
                        st.markdown(report_text)
                        st.download_button(label="📥 Download PDF", data=create_pdf(report_text), file_name="Turaab_Report.pdf")
                except Exception as err:
                    st.error(f"System Error: {err}")
