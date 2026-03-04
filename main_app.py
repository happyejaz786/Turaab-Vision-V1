import streamlit as st
import easyocr
from google import genai
from PIL import Image
import numpy as np
import ssl

# SSL Fix for models download
ssl._create_default_https_context = ssl._create_unverified_context

# --- CONFIGURATION ---
st.set_page_config(page_title="Turaab Vision V1.0", page_icon="📄", layout="centered")

# API Keys List
API_KEYS = [
    "AIzaSyDOJgU4z1Wap9gGjmh0k8DRe__PlcHPams",
    "AIzaSyAitNRt0gCpm2vuK_5qqHvuY8Hsplf75PQ",
    "AIzaSyD-2RSNcCnSo43ixbdpzKcyvNNaQzjfEvc",
    "AIzaSyCl5SZGRIsk8-3DAiXsuslkCf--s4HtpeQ"
]

# --- CACHING MODELS (Speed Boost for i3/i7) ---
@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['hi', 'en'], gpu=False)

def get_gemini_client(key_index):
    return genai.Client(api_key=API_KEYS[key_index])

# --- UI DESIGN ---
st.title("📄 Turaab Vision - Version 1.0")
st.write("Bismillah_Arrahman_Arraheem")
st.markdown("---")

# Input Options: Camera or Upload
source = st.radio("Photo Kaise Lein?", ("Camera (Mobile/Webcam)", "Upload File (Gallery)"))

if source == "Camera (Mobile/Webcam)":
    uploaded_file = st.camera_input("Document ki photo kheenchiye")
else:
    uploaded_file = st.file_uploader("Document upload karein", type=['jpg', 'jpeg', 'png'])

# --- LOGIC ---
if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Document Process ho raha hai...", use_container_width=True)
    
    if st.button("🚀 Start Digitization & Summary"):
        with st.spinner("🔍 OCR Scanning & AI Analysis in progress..."):
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
                
                client = get_gemini_client(0) # Pehli key use kar rahe hain
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=[prompt, img]
                )

                # --- OUTPUT ---
                st.success("✅ Analysis Complete!")
                st.subheader("💡 Mission Summary Report")
                st.markdown(response.text)
                
                with st.expander("See Raw Extracted Text"):
                    st.write(extracted_text)

            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")
st.caption("Powered by Turaab Vision | Version 1.0 (Beta)")
