import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from gtts import gTTS
import tempfile
import os
from dotenv import load_dotenv
import google.generativeai as genai

# === 1. Load Environment Variables ===
load_dotenv()
api_key = os.getenv("Gemini_API_Key")  

# === 2. Configure Gemini API ===
if not api_key:
    st.error("❌ Gemini API key not found. Please set it in your .env file.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")

# === 3. Helper Functions ===
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    extracted_text = ""
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            extracted_text += text + "\n"
        else:
            try:
                images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1)
                for image in images:
                    extracted_text += pytesseract.image_to_string(image) + "\n"
            except Exception as e:
                st.warning(f"OCR failed for page {page_num + 1}: {e}")
    return extracted_text

def generate_summary(text):
    prompt = f"Summarize the following document in simple terms:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text

def generate_real_life_examples(text):
    prompt = f"""
You are an expert teacher tasked with explaining the following document to someone who is learning about this topic for the first time. Your goal is to provide a detailed, engaging, and easy-to-understand explanation that is at least 1000 words long. Use real-life examples to make the concepts relatable...

Document:
{text}

Now, generate the explanation based on the document provided.
"""
    response = model.generate_content(prompt)
    return response.text

def text_to_speech(text, filename="explanation_audio.mp3"):
    tts = gTTS(text)
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    tts.save(temp_path)
    return temp_path

# === 4. Streamlit App ===
st.title("📄 PDF to Audio with AI Explanation")

uploaded_pdf = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_pdf:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(uploaded_pdf.read())
        temp_pdf_path = temp_pdf.name

    if st.button("Process PDF"):
        try:
            with st.spinner("📄 Extracting text from PDF..."):
                extracted_text = extract_text_from_pdf(temp_pdf_path)

            if not extracted_text.strip():
                st.error("No text could be extracted from the PDF.")
            else:
                st.success("✅ Text extracted.")

                with st.spinner("🔊 Generating audio..."):
                    summary = generate_summary(extracted_text)
                    explanation = generate_real_life_examples(extracted_text)

                with st.spinner("🔊 Please wait for a while..."):
                    audio_file_path = text_to_speech(explanation)
                    st.success("✅ Audio generated.")

                st.subheader("🔊 Listen to AI Explanation")
                st.audio(audio_file_path)

                # Show summary and explanation after audio
                st.subheader("📝 Summary")
                st.write(summary)

                st.subheader("📘 Detailed Explanation")
                st.write(explanation)

        except Exception as e:
            st.error(f"Something went wrong: {e}")
