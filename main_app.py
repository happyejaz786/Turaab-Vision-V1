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

# SSL Fix (for model download environments)
ssl._create_default_https_context = ssl._create_unverified_context

# ------------------ CONFIG ------------------
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

st.title("📄 Turaab Vision - Version 2.0 (Stable Edition)")

# ------------------ FIREBASE SETUP ------------------
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
    st.warning(
        "⚠️ Firebase connect nahi ho saka. History save nahi hogi.\nError: " + str(e)
    )

# ------------------ GEMINI SETUP ------------------
CURRENT_API_KEY = None

try:
    API_KEYS = st.secrets["gemini"]["api_keys"]
    CURRENT_API_KEY = random.choice(API_KEYS)
    genai.configure(api_key=CURRENT_API_KEY)

except Exception:
    st.error("❌ Gemini API Keys missing in Streamlit Secrets!")

# ------------------ OCR CACHE ------------------
@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['hi', 'en'], gpu=False)

# ------------------ PDF FUNCTION ------------------
def create_pdf(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Turaab Vision - Mission Summary", ln=1, align='C')
    pdf.ln(10)

    clean_text = text_content.replace('₹', 'Rs.')
    safe_text = clean_text.encode('latin-1', 'ignore').decode('latin-1')

    pdf.multi_cell(0, 8, txt=safe_text)

    return pdf.output(dest='S').encode('latin-1')

# ------------------ MODELS ------------------
# ------------------ ADVANCED MODEL + API ROTATION ------------------

FAST_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

API_KEYS = st.secrets["gemini"]["api_keys"]

report_text = None
max_attempts = len(FAST_MODELS) * len(API_KEYS)

attempt_count = 0

for model_name in FAST_MODELS:
    for api_key in API_KEYS:

        try:
            attempt_count += 1

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)

            response = model.generate_content(prompt)
            report_text = response.text

            st.success(
                f"✅ Success (Model: {model_name} | API Key #{API_KEYS.index(api_key)+1})"
            )
            break

        except Exception as e:
            error_str = str(e)

            if "429" in error_str or "503" in error_str:
                wait_time = 2 ** attempt_count  # exponential backoff
                st.warning(
                    f"{model_name} busy with this key. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                st.error(f"Non-retryable API Error: {e}")
                break

    if report_text:
        break

if not report_text:
    st.error("❌ All models and API keys exhausted. Please try later.")
# ------------------ UI ------------------
tab1, tab2 = st.tabs(["🔍 Scan Document", "📜 History"])

# ====================================================
# TAB 1
# ====================================================
with tab1:

    uploaded_file = st.file_uploader(
        "Upload Document Image (JPG, PNG)",
        type=['jpg', 'jpeg', 'png']
    )

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=400, caption="Uploaded Image")

        if st.button("🚀 Process & Save"):

            if not CURRENT_API_KEY:
                st.error("API Key missing hai. Process nahi ho sakta.")
                st.stop()

            with st.spinner("AI Analysis chal raha hai..."):

                try:
                    # -------- 1. OCR --------
                    reader = load_ocr_reader()
                    img_array = np.array(img)
                    ocr_result = reader.readtext(img_array, detail=0)
                    extracted_text = " ".join(ocr_result)

                    if not extracted_text.strip():
                        st.error("OCR koi text detect nahi kar paya.")
                        st.stop()

                    # -------- 2. CREATE PROMPT --------
prompt = f"""
You are a Professional Educator and Analytical Summarizer.

Your task:
1. Identify the document/topic type.
2. Provide a detailed executive summary.
3. Extract key points in simple bullet format.
4. Make explanation student friendly.

OCR TEXT:
{extracted_text}
"""

                    # -------- 3. GEMINI RETRY --------
                    report_text = None

                    for attempt, model_name in enumerate(FAST_MODELS):
                        try:
                            model = genai.GenerativeModel(model_name)

                            response = model.generate_content(prompt)

                            report_text = response.text

                            st.success(f"✅ Analysis Complete (Model: {model_name})")
                            break

                        except Exception as api_error:
                            if attempt < len(FAST_MODELS) - 1:
                                st.warning(
                                    f"{model_name} busy. Switching model..."
                                )
                                time.sleep(2)
                            else:
                                st.error(
                                    "❌ All Gemini models busy. Try again later."
                                )

                    # -------- 4. OUTPUT --------
                    if report_text:

                        # Save to Firebase
                        if db:
                            try:
                                db.collection('scans').add({
                                    'timestamp': firestore.SERVER_TIMESTAMP,
                                    'summary': report_text
                                })
                                st.toast("History Saved!", icon="💾")

                            except Exception as fb_error:
                                st.warning(
                                    f"Firebase save failed: {fb_error}"
                                )

                        st.subheader("💡 Mission Summary Report")
                        st.markdown(report_text)

                        with st.expander("📄 Raw OCR Text"):
                            st.write(extracted_text)

                        # PDF Download
                        pdf_data = create_pdf(report_text)

                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_data,
                            file_name=f"Turaab_Report_{datetime.now().strftime('%H%M%S')}.pdf"
                        )

                except Exception as e:
                    st.error(f"System Error: {e}")

# ====================================================
# TAB 2 - HISTORY
# ====================================================
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
                    time_display = "Unknown Time"

                with st.expander(f"Scan - {time_display}"):
                    st.markdown(data.get('summary', 'No summary found'))

            if count == 0:
                st.info("Abhi history khali hai.")

        except Exception as e:
            st.error(f"History load error: {e}")

    else:
        st.info("Database connected nahi hai.")

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("Powered by Turaab Vision 2.0 | Stable Production Edition")


