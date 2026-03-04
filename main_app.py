import streamlit as st
import easyocr
import google.generativeai as genai
from PIL import Image
import numpy as np
import ssl
import random
import time
import firebase_admin
from firebase_admin import credentials, firestore
from fpdf import FPDF
from datetime import datetime

# =====================================================
# BASIC CONFIG
# =====================================================

ssl._create_default_https_context = ssl._create_unverified_context

st.set_page_config(
    page_title="Turaab Vision V2.0",
    page_icon="📄",
    layout="wide"
)

st.markdown(
    "<h2 style='text-align: center; color: #4CAF50;'>"
    "بِسْمِ ٱللَّٰهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ</h2>",
    unsafe_allow_html=True
)

st.title("📄 Turaab Vision - Version 2.0 (Production Edition)")

# =====================================================
# FIREBASE INITIALIZATION
# =====================================================

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
    st.warning("⚠️ Firebase not connected. History disabled.")

# =====================================================
# GEMINI SETUP
# =====================================================

API_KEYS = []
try:
    API_KEYS = st.secrets["gemini"]["api_keys"]
except Exception:
    st.error("❌ Gemini API Keys missing in Streamlit Secrets!")

# =====================================================
# OCR CACHE
# =====================================================

@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['hi', 'en'], gpu=False)

# =====================================================
# PDF FUNCTION
# =====================================================

def create_pdf(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Turaab Vision - Mission Summary", ln=True, align='C')
    pdf.ln(10)

    clean_text = text_content.replace('₹', 'Rs.')
    safe_text = clean_text.encode('latin-1', 'ignore').decode('latin-1')

    pdf.multi_cell(0, 8, txt=safe_text)

    return pdf.output(dest='S').encode('latin-1')

# =====================================================
# UI TABS
# =====================================================

tab1, tab2 = st.tabs(["🔍 Scan Document", "📜 History"])

# =====================================================
# TAB 1 - DOCUMENT SCAN
# =====================================================

with tab1:

    uploaded_file = st.file_uploader(
        "Upload Document Image (JPG, PNG)",
        type=['jpg', 'jpeg', 'png']
    )

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=400, caption="Uploaded Image")

        if st.button("🚀 Process & Save"):

            if not API_KEYS:
                st.error("No API keys available.")
                st.stop()

            with st.spinner("AI Analysis in progress..."):

                try:
                    # ---------------- OCR ----------------
                    reader = load_ocr_reader()
                    img_array = np.array(img)
                    ocr_result = reader.readtext(img_array, detail=0)
                    extracted_text = " ".join(ocr_result)

                    if not extracted_text.strip():
                        st.error("No text detected by OCR.")
                        st.stop()

                    # ---------------- PROMPT ----------------
                    prompt = f"""
You are a Professional Educator and Analytical Summarizer.

Your tasks:
1. Identify the document/topic type.
2. Provide a detailed executive summary.
3. Extract key points in simple bullet format.
4. Make explanation student-friendly.

OCR TEXT:
{extracted_text}
"""

                    # ---------------- MODEL ROTATION ----------------
                    FAST_MODELS = [
                        "gemini-1.5-flash",
                        "gemini-1.5-pro"
                    ]

                    report_text = None

                    for model_name in FAST_MODELS:
                        for api_key in API_KEYS:
                            try:
                                genai.configure(api_key=api_key)
                                model = genai.GenerativeModel("gemini-pro")
                                #model = genai.GenerativeModel(model_name)

                                response = model.generate_content(prompt)
                                report_text = response.text

                                st.success(
                                    f"✅ Success (Model: {model_name})"
                                )
                                break

                            except Exception as api_error:
                                error_str = str(api_error)

                                if "429" in error_str or "503" in error_str:
                                    st.warning(
                                        f"{model_name} busy. Switching..."
                                    )
                                    time.sleep(2)
                                else:
                                    st.error(f"API Error: {api_error}")
                                    break

                        if report_text:
                            break

                    if not report_text:
                        st.error("❌ All models and keys exhausted.")
                        st.stop()

                    # ---------------- SAVE TO FIREBASE ----------------
                    if db:
                        try:
                            db.collection('scans').add({
                                'timestamp': firestore.SERVER_TIMESTAMP,
                                'summary': report_text
                            })
                            st.toast("History Saved!", icon="💾")
                        except Exception:
                            st.warning("Could not save to Firebase.")

                    # ---------------- DISPLAY OUTPUT ----------------
                    st.subheader("💡 Mission Summary Report")
                    st.markdown(report_text)

                    with st.expander("📄 Raw OCR Text"):
                        st.write(extracted_text)

                    # ---------------- PDF DOWNLOAD ----------------
                    pdf_data = create_pdf(report_text)

                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_data,
                        file_name=f"Turaab_Report_{datetime.now().strftime('%H%M%S')}.pdf"
                    )

                except Exception as e:
                    st.error(f"System Error: {e}")

# =====================================================
# TAB 2 - HISTORY
# =====================================================

with tab2:

    if db:
        try:
            scans = (
                db.collection('scans')
                .order_by('timestamp', direction=firestore.Query.DESCENDING)
                .limit(10)
                .stream()
            )

            count = 0

            for scan in scans:
                count += 1
                data = scan.to_dict()
                timestamp = data.get('timestamp')

                if timestamp:
                    time_display = timestamp.strftime('%d %b, %H:%M')
                else:
                    time_display = "Unknown"

                with st.expander(f"Scan - {time_display}"):
                    st.markdown(data.get('summary', 'No summary found'))

            if count == 0:
                st.info("History is empty.")

        except Exception as e:
            st.error(f"History load error: {e}")

    else:
        st.info("Database not connected.")

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")
st.caption("Powered by Turaab Vision | Production Stable Edition")

