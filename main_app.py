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

# --- CONFIGURATION ---
st.set_page_config(page_title="Turaab Vision V1.2", page_icon="📄", layout="wide")

# --- FIREBASE SETUP ---
if not firebase_admin._apps:
    try:
        # Streamlit secrets se JSON load kar rahe hain
        service_account_info = json.loads(st.secrets["firebase"]["service_account"])
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Init Error: {e}")

db = firestore.client()

# API Keys
API_KEYS = ["AIzaSyDOJgU4z1Wap9gGjmh0k8DRe__PlcHPams"]

# --- FUNCTIONS ---
@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['hi', 'en'], gpu=False)

def create_pdf(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Turaab Vision - Analysis Report", ln=1, align='C')
    pdf.ln(10)
    clean_text = text_content.replace('₹', 'Rs.').replace('*', '')
    safe_text = clean_text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# --- UI ---
st.title("📄 Turaab Vision - Version 1.2")
st.write("Bismillah_Arrahman_Arraheem")

tab1, tab2 = st.tabs(["🔍 Scan", "📜 History"])

with tab1:
    uploaded_file = st.file_uploader("Document Upload Karein", type=['jpg', 'jpeg', 'png'])
    if not uploaded_file:
        uploaded_file = st.camera_input("Ya Photo Kheenchiye")

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=400) # Warning fix
        
        if st.button("🚀 Process"):
            with st.spinner("AI Analysis..."):
                reader = load_ocr_reader()
                img_array = np.array(img)
                ocr_res = reader.readtext(img_array, detail=0)
                extracted_text = " ".join(ocr_res)

                client = genai.Client(api_key=API_KEYS[0])
                response = client.models.generate_content(
                    model="gemini-2.0-flash", 
                    contents=[f"Summarize this: {extracted_text}", img]
                )
                report_text = response.text

                # Save to Firebase
                db.collection('scans').add({
                    'timestamp': datetime.now(),
                    'summary': report_text
                })

                st.success("✅ Saved to History!")
                st.markdown(report_text)
                
                pdf_data = create_pdf(report_text)
                st.download_button("📥 Download PDF", data=pdf_data, file_name="Report.pdf")

with tab2:
    scans = db.collection('scans').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream()
    for scan in scans:
        data = scan.to_dict()
        with st.expander(f"Scan - {data['timestamp'].strftime('%H:%M %d/%m')}"):
            st.markdown(data['summary'])
