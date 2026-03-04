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
import pandas as pd
from datetime import datetime

# SSL Fix
ssl._create_default_https_context = ssl._create_unverified_context

# --- CONFIGURATION ---
st.set_page_config(page_title="Turaab Vision V1.2", page_icon="📄", layout="wide")

# --- FIREBASE SETUP (Using Secrets) ---
if not firebase_admin._apps:
    secret_json = json.loads(st.secrets["firebase"]["service_account"])
    cred = credentials.Certificate(secret_json)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# API Keys List
API_KEYS = [
    "AIzaSyDOJgU4z1Wap9gGjmh0k8DRe__PlcHPams",
    "AIzaSyAitNRt0gCpm2vuK_5qqHvuY8Hsplf75PQ",
    "AIzaSyD-2RSNcCnSo43ixbdpzKcyvNNaQzjfEvc",
    "AIzaSyCl5SZGRIsk8-3DAiXsuslkCf--s4HtpeQ"
]

# --- FUNCTIONS ---
@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['hi', 'en'], gpu=False)

def create_pdf(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Turaab Vision - Analytical Report", ln=1, align='C')
    pdf.ln(10)
    # Cleaning text for FPDF (replaces non-latin chars if any)
    pdf.multi_cell(0, 10, txt=text_content.encode('latin-1', 'ignore').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- UI DESIGN ---
st.title("📄 Turaab Vision - Version 1.2")
st.write("Bismillah_Arrahman_Arraheem")

tab1, tab2 = st.tabs(["🔍 Scan New Document", "📜 History"])

with tab1:
    source = st.radio("Photo Kaise Lein?", ("Camera (Mobile/Webcam)", "Upload File (Gallery)"))
    uploaded_file = st.camera_input("Photo kheenchiye") if source == "Camera (Mobile/Webcam)" else st.file_uploader("Upload karein", type=['jpg', 'jpeg', 'png'])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=400)
        
        if st.button("🚀 Analyze & Save"):
            with st.spinner("AI Kaam kar raha hai..."):
                # 1. OCR
                reader = load_ocr_reader()
                img_array = np.array(img)
                extracted_text = " ".join(reader.readtext(img_array, detail=0))

                # 2. Gemini Analysis
                prompt = f"Identify document type, 2-line summary, and key data in a Table. OCR: {extracted_text}"
                client = genai.Client(api_key=API_KEYS[0])
                response = client.models.generate_content(model="gemini-3-flash-preview", contents=[prompt, img])
                report_text = response.text

                # 3. Save to Firebase
                doc_ref = db.collection('scans').document()
                doc_ref.set({
                    'timestamp': datetime.now(),
                    'summary': report_text,
                    'raw_text': extracted_text
                })

               # --- OUTPUT SECTION ---
                st.success("✅ Analysis Complete & Saved to Firebase!")
                st.markdown(report_text)
                
                # --- PDF GENERATION (Ye button tabhi dikhega jab report generate hogi) ---
                try:
                    pdf_bytes = create_pdf(report_text)
                    st.download_button(
                        label="📥 Download Report (PDF)",
                        data=pdf_bytes,
                        file_name=f"Turaab_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        key="pdf_download_btn"
                    )
                except Exception as pdf_err:
                    st.warning(f"PDF generate karne mein thodi dikkat hui: {pdf_err}")

with tab2:
    st.subheader("Pichle Scans (History)")
    scans = db.collection('scans').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream()
    
    for scan in scans:
        data = scan.to_dict()
        with st.expander(f"Scan - {data['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
            st.markdown(data['summary'])

