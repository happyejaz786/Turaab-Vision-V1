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

# SSL Fix for models download
ssl._create_default_https_context = ssl._create_unverified_context

# --- CONFIGURATION ---
st.set_page_config(page_title="Turaab Vision V1.2", page_icon="📄", layout="wide")

# --- FIREBASE SETUP (Using Secrets) ---
if not firebase_admin._apps:
    try:
        secret_json = json.loads(st.secrets["firebase"]["service_account"])
        cred = credentials.Certificate(secret_json)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase connection fail: {e}")

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
    
    # PDF Cleaning: Special symbols handling
    clean_text = text_content.replace('₹', 'Rs.').replace('*', '')
    # Encoding fix for FPDF
    safe_text = clean_text.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf.multi_cell(0, 10, txt=safe_text)
    return pdf.output(dest='S').encode('latin-1')

# --- UI DESIGN ---
st.title("📄 Turaab Vision - Version 1.2")
st.write("Bismillah_Arrahman_Arraheem")

tab1, tab2 = st.tabs(["🔍 Scan & Analyze", "📜 History"])

with tab1:
    source = st.radio("Photo Source:", ("Camera (Mobile/Webcam)", "Upload File (Gallery)"))
    if source == "Camera (Mobile/Webcam)":
        uploaded_file = st.camera_input("Document Scan Karein")
    else:
        uploaded_file = st.file_uploader("Document Upload Karein", type=['jpg', 'jpeg', 'png'])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=400, caption="Uploaded Document")
        
        if st.button("🚀 Process Document"):
            with st.spinner("Turaab Vision AI analysis kar raha hai..."):
                try:
                    # 1. OCR Section
                    reader = load_ocr_reader()
                    img_array = np.array(img)
                    ocr_res = reader.readtext(img_array, detail=0)
                    extracted_text = " ".join(ocr_res)

                    # 2. Gemini AI Section
                    prompt = f"""
                    Role: Professional CSC Document Summarizer.
                    Task: Summarize document type and key info into a table.
                    OCR Data: {extracted_text}
                    """
                    client = genai.Client(api_key=API_KEYS[0])
                    response = client.models.generate_content(
                        model="gemini-2.0-flash", # Latest Fast Model
                        contents=[prompt, img]
                    )
                    report_text = response.text

                    # 3. Save to Firebase
                    doc_ref = db.collection('scans').document()
                    doc_ref.set({
                        'timestamp': datetime.now(),
                        'summary': report_text,
                        'source': source
                    })

                    # 4. Results Display
                    st.success("✅ Analysis Complete & Saved to History!")
                    st.markdown(report_text)
                    
                    # 5. PDF Download Button (Indented correctly inside button)
                    st.markdown("---")
                    pdf_data = create_pdf(report_text)
                    st.download_button(
                        label="📥 Download Report as PDF",
                        data=pdf_data,
                        file_name=f"Turaab_Vision_{datetime.now().strftime('%d%m_%H%M')}.pdf",
                        mime="application/pdf",
                        key="main_download"
                    )

                except Exception as err:
                    st.error(f"Kuch galti hui: {err}")

with tab2:
    st.subheader("📜 Recent Scans")
    try:
        scans = db.collection('scans').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream()
        
        for scan in scans:
            data = scan.to_dict()
            with st.expander(f"Scan - {data['timestamp'].strftime('%d %b, %H:%M')}"):
                st.markdown(data['summary'])
                # History mein bhi PDF download option
                if st.button("Generate PDF", key=scan.id):
                    pdf_history = create_pdf(data['summary'])
                    st.download_button("Download Now", data=pdf_history, file_name="History_Report.pdf")
    except Exception as e:
        st.info("Abhi koi history nahi hai. Pehla scan karein!")

st.markdown("---")
st.caption("Developed for Mohammed Turab Khan | CSC Automation Tool")
