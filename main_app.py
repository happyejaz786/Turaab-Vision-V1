import streamlit as st
import easyocr
from google import genai
from PIL import Image
import numpy as np
import ssl
import json
import firebase_admin
from firebase_admin import credentials, firestore
from fpdf import FPDF
from datetime import datetime

# SSL Fix
ssl._create_default_https_context = ssl._create_unverified_context

st.set_page_config(page_title="Turaab Vision V1.2", page_icon="📄", layout="wide")

# --- FIREBASE SETUP (Safe Mode - Does not disturb existing secrets) ---
if not firebase_admin._apps:
    try:
        # Check karta hai ki secrets ka format kaisa hai aur us hisab se load karta hai
        if "firebase" in st.secrets and "service_account" in st.secrets["firebase"]:
            info = json.loads(st.secrets["firebase"]["service_account"])
        else:
            info = dict(st.secrets)
            
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            
        cred = credentials.Certificate(info)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Init Error: {e}")

# Database initialize
try:
    db = firestore.client()
except Exception:
    st.warning("Database connect nahi ho saka.")
    db = None

# API Key
API_KEY = "AIzaSyDOJgU4z1Wap9gGjmh0k8DRe__PlcHPams"

@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['hi', 'en'], gpu=False)

def create_pdf(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Turaab Vision Report", ln=1, align='C')
    pdf.ln(10)
    clean_text = text_content.replace('₹', 'Rs.').replace('*', '')
    safe_text = clean_text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

st.title("📄 Turaab Vision - Version 1.2")
st.write("Bismillah_Arrahman_Arraheem")

tab1, tab2 = st.tabs(["🔍 Scan Document", "📜 History"])

with tab1:
    uploaded_file = st.file_uploader("Upload Document", type=['jpg', 'jpeg', 'png'])
    if not uploaded_file:
        uploaded_file = st.camera_input("Photo Lein")

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=400)
        
        if st.button("🚀 Process & Save"):
            with st.spinner("AI Analysis..."):
                try:
                    reader = load_ocr_reader()
                    img_array = np.array(img)
                    extracted_text = " ".join(reader.readtext(img_array, detail=0))
                    
                    client = genai.Client(api_key=API_KEY)
                    response = client.models.generate_content(
                        model="gemini-2.0-flash", 
                        contents=[f"Identify document and extract key data: {extracted_text}", img]
                    )
                    report_text = response.text
                    
                    if db is not None:
                        db.collection('scans').add({'timestamp': datetime.now(), 'summary': report_text})
                        st.success("✅ Saved to History!")
                    
                    st.markdown(report_text)
                    
                    # PDF Download Button
                    st.markdown("---")
                    pdf_data = create_pdf(report_text)
                    st.download_button("📥 Download PDF", data=pdf_data, file_name=f"Turaab_Report_{datetime.now().strftime('%H%M%S')}.pdf")
                    
                except Exception as err:
                    st.error(f"Error: {err}")

with tab2:
    if db is not None:
        try:
            scans = db.collection('scans').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream()
            for scan in scans:
                data = scan.to_dict()
                with st.expander(f"Scan - {data['timestamp'].strftime('%H:%M %d/%m')}"):
                    st.markdown(data['summary'])
        except Exception:
            st.info("Abhi history khali hai.")
