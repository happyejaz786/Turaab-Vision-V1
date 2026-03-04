import streamlit as st
import easyocr
from google import genai
from PIL import Image
import numpy as np
import ssl
import random
import firebase_admin
from firebase_admin import credentials, firestore
from fpdf import FPDF
from datetime import datetime

# SSL Fix for models download
ssl._create_default_https_context = ssl._create_unverified_context

# --- CONFIGURATION ---
st.set_page_config(page_title="Turaab Vision V2.0", page_icon="📄", layout="wide")

# --- ARABIC BISMILLAH & TITLE ---
st.markdown("<h2 style='text-align: center; color: #4CAF50;'>بِسْمِ ٱللَّٰهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ</h2>", unsafe_allow_html=True)
st.title("📄 Turaab Vision - Version 2.0")

# --- SECRETS LOAD & FIREBASE SETUP ---
if not firebase_admin._apps:
    try:
        # Firebase secrets load kar rahe hain
        firebase_creds = dict(st.secrets["firebase"])
        if "private_key" in firebase_creds:
            firebase_creds["private_key"] = firebase_creds["private_key"].replace("\\n", "\n")
        
        cred = credentials.Certificate(firebase_creds)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Setup Error: {e}")

# Database initialize
try:
    db = firestore.client()
except Exception:
    st.warning("Database connect nahi ho saka.")
    db = None

# --- GEMINI API SETUP (Smart Rotator) ---
# --- GEMINI API & MODEL SETUP (Gen-Z Speed Rotator) ---
try:
    API_KEYS = st.secrets["gemini"]["api_keys"]
    CURRENT_API_KEY = random.choice(API_KEYS) 
    
    # Gen-Z Fast Models Pool (Sirf sabse tez models)
    FAST_MODELS = [
        "gemini-2.5-flash-lite", 
        "gemini-flash-latest",
        "gemini-2.0-flash-lite"
    ]
    CURRENT_MODEL = random.choice(FAST_MODELS)
    
except Exception:
    CURRENT_API_KEY = None
    CURRENT_MODEL = None
    st.error("API Keys missing in Streamlit Secrets!")

# --- FUNCTIONS ---
@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['hi', 'en'], gpu=False)

def create_pdf(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Turaab Vision - Mission Summary", ln=1, align='C')
    pdf.ln(10)
    
    # Cleaning text for PDF compatibility
    clean_text = text_content.replace('₹', 'Rs.').replace('*', '')
    safe_text = clean_text.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf.multi_cell(0, 10, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# --- UI DESIGN ---
tab1, tab2 = st.tabs(["🔍 Scan Document", "📜 History"])

with tab1:
    # Camera option removed. Only File Uploader remains.
    uploaded_file = st.file_uploader("Upload Document Image (JPG, PNG)", type=['jpg', 'jpeg', 'png'])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=400, caption="Uploaded Image")
        
        if st.button("🚀 Process & Save"):
            if not CURRENT_API_KEY:
                st.error("API Key missing hai, process aage nahi badh sakta.")
            else:
                with st.spinner("AI Analysis kar raha hai..."):
                    try:
                        # 1. OCR Section
                        reader = load_ocr_reader()
                        img_array = np.array(img)
                        ocr_result = reader.readtext(img_array, detail=0)
                        extracted_text = " ".join(ocr_result)
                        
                        # 2. Gemini Analysis (Mission Summary)
                        prompt = f"""
                        System Role: Professional CSC Expert & Analytical Summarizer.
                        Task: Decode Krutidev/Legacy symbols from OCR and summarize.
                        1. Identify Document Type.
                        2. Provide 2-line Executive Summary.
                        3. Extract Key Details in a Table (Name, ID, Address, Mobile).
                        
                        OCR RAW: {extracted_text}
                        """
                        
                        client = genai.Client(api_key=CURRENT_API_KEY)
                    
                    # Ab code khud har baar naya aur fast model use karega
                    response = client.models.generate_content(
                        model=CURRENT_MODEL, 
                        contents=[prompt, img]
                    )
                        report_text = response.text
                        
                        # 3. Save to Firebase
                        if db is not None:
                            db.collection('scans').add({'timestamp': datetime.now(), 'summary': report_text})
                            st.success("✅ Analysis Complete & Saved to History!")
                        else:
                            st.warning("⚠️ Report ban gayi hai par Database connect na hone ki wajah se save nahi hui.")
                        
                        st.subheader("💡 Mission Summary Report")
                        st.markdown(report_text)
                        
                        with st.expander("See Raw Extracted Text"):
                            st.write(extracted_text)
                        
                        # 4. PDF Download Generation
                        st.markdown("---")
                        pdf_data = create_pdf(report_text)
                        st.download_button(
                            label="📥 Download PDF", 
                            data=pdf_data, 
                            file_name=f"Turaab_Report_{datetime.now().strftime('%H%M%S')}.pdf"
                        )
                        
                    except Exception as err:
                        st.error(f"System Error: {err}")

with tab2:
    if db is not None:
        try:
            scans = db.collection('scans').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream()
            for scan in scans:
                data = scan.to_dict()
                with st.expander(f"Scan - {data['timestamp'].strftime('%d %b, %H:%M')}"):
                    st.markdown(data['summary'])
        except Exception:
            st.info("Abhi history khali hai.")
            
st.markdown("---")
st.caption("Powered by Turaab Vision | Version 2.0")






