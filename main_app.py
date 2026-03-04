import streamlit as st
import easyocr
from google import genai
from PIL import Image
import numpy as np
import ssl
import random
import time
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
st.title("📄 Turaab Vision - Version 2.0 (Superfast)")

# --- SECRETS LOAD & FIREBASE SETUP (Bulletproof) ---
db = None
try:
    if not firebase_admin._apps:
        firebase_creds = dict(st.secrets["firebase"])
        if "private_key" in firebase_creds:
            firebase_creds["private_key"] = firebase_creds["private_key"].replace("\\n", "\n")
        
        cred = credentials.Certificate(firebase_creds)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.warning("⚠️ Database connect nahi ho saka. App kaam karegi, par History save nahi hogi. Error: " + str(e))

# --- GEMINI API & MODEL SETUP (Gen-Z Speed Rotator) ---
try:
    API_KEYS = st.secrets["gemini"]["api_keys"]
    CURRENT_API_KEY = random.choice(API_KEYS) 
    
    # Gen-Z Fast Models Pool (Sirf sabse tez aur available models)
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
    
    clean_text = text_content.replace('₹', 'Rs.').replace('*', '')
    safe_text = clean_text.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf.multi_cell(0, 10, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# --- UI DESIGN ---
tab1, tab2 = st.tabs(["🔍 Scan Document", "📜 History"])

with tab1:
    uploaded_file = st.file_uploader("Upload Document Image (JPG, PNG)", type=['jpg', 'jpeg', 'png'])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=400, caption="Uploaded Image")
        
        if st.button("🚀 Process & Save"):
            if not CURRENT_API_KEY:
                st.error("API Key missing hai, process aage nahi badh sakta.")
            else:
                with st.spinner(f"AI Analysis kar raha hai... (Model: {CURRENT_MODEL})"):
                    try:
                        # 1. OCR Section
                        reader = load_ocr_reader()
                        img_array = np.array(img)
                        ocr_result = reader.readtext(img_array, detail=0)
                        extracted_text = " ".join(ocr_result)
                        
                        # 2. Gemini Analysis (Mission Summary)
                        prompt = f"""
                        System Role: Professional Educator & Analytical Summarizer.
                        Task: Decode text from OCR and summarize for students.
                        1. Identify Document/Topic Type.
                        2. Provide detailed Executive Summary.
                        3. Extract Key Points in simple bullet points.
                        
                        OCR RAW: {extracted_text}
                        """
                        
                        client = genai.Client(api_key=CURRENT_API_KEY)
                        
                        # --- AUTO-RETRY MECHANISM (The Game Changer) ---
                        max_retries = 3
                        report_text = None
                        
                        for attempt in range(max_retries):
                            try:
                                response = client.models.generate_content(
                                    model=CURRENT_MODEL, 
                                    contents=[prompt, img]
                                )
                                report_text = response.text
                                break # Success, exit loop
                                
                            except Exception as api_err:
                                err_str = str(api_err)
                                if "503" in err_str or "429" in err_str:
                                    if attempt < max_retries - 1:
                                        wait_time = attempt + 2
                                        st.toast(f"Server busy. Retrying in {wait_time}s...", icon="⏳")
                                        time.sleep(wait_time)
                                    else:
                                        st.error("Google ke servers abhi bahut zyada load par hain. Kripya thodi der baad try karein.")
                                else:
                                    st.error(f"API Error: {api_err}")
                                    break
                        
                        # Agar summary ban gayi toh aage badho
                        if report_text:
                            # 3. Save to Firebase safely
                            if db is not None:
                                try:
                                    db.collection('scans').add({'timestamp': datetime.now(), 'summary': report_text})
                                    st.success("✅ Analysis Complete & Saved to History!")
                                except Exception as fb_err:
                                    st.warning(f"Report ban gayi hai, par Firebase mein save nahi hui: {fb_err}")
                            else:
                                st.success("✅ Analysis Complete!")
                                
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
            count = 0
            for scan in scans:
                count += 1
                data = scan.to_dict()
                with st.expander(f"Scan - {data['timestamp'].strftime('%d %b, %H:%M')}"):
                    st.markdown(data['summary'])
            if count == 0:
                st.info("Abhi history khali hai.")
        except Exception as e:
            st.error(f"History load karne mein error: {e}")
    else:
        st.info("Database connected nahi hai isliye history yahan nahi dikhegi.")
            
st.markdown("---")
st.caption("Powered by Turaab Vision | Superfast Edition")
