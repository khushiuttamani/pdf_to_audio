import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from gtts import gTTS
import tempfile
import os
import re
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()
API_KEY = os.getenv("GENAI_API_KEY")

# === Configure Gemini API ===
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("models/gemini-1.5-flash-latest")

# === Logging Configuration ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# === Helper Functions ===

def extract_text_from_pdf(pdf_path):
    logging.info(f"Extracting text from: {pdf_path}")
    doc = fitz.open(pdf_path)
    extracted_text = ""
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text and text.strip():
            extracted_text += text + "\n"
        else:
            try:
                images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1)
                for image in images:
                    extracted_text += pytesseract.image_to_string(image) + "\n"
            except Exception as e:
                logging.warning(f"OCR failed for page {page_num + 1}: {e}")
                st.warning(f"OCR failed for page {page_num + 1}: {e}")
    doc.close()
    logging.info("Text extraction complete.")
    return extracted_text

def clean_text(text):
    logging.info("Cleaning extracted text.")
    cleaned = re.sub(r"[^A-Za-z0-9\s.,!?':;\"()\-]", '', text)
    return cleaned

def remove_markdown_formatting(text):
    logging.info("Removing markdown from explanation text.")
    return re.sub(r"[*_`~]+", "", text)

def generate_summary(text):
    logging.info("Generating summary.")
    prompt = (
        "Please read the following document and write a short and simple summary. "
        "Use clear language that anyone can understand. Focus only on the main ideas, not small details. "
        "The goal is to help someone quickly understand what this document is about, even if they don't know anything about the topic.\n\n"
        f"Document:\n{text}")
    response = model.generate_content(prompt)
    return getattr(response, 'text', str(response))

def generate_explanation(text, feedback=None):
    logging.info("Generating explanation with feedback." if feedback else "Generating initial explanation.")
    base_prompt = (
        "You are a kind and smart teacher. You have to explain the ideas in the text below to someone who is learning it for the first time. "
        "Use very simple words. Break hard ideas into small, easy steps. Use real-life examples so it's easy to understand. "
        "Try to make the explanation fun and interesting, like you are talking to a friend.\n\n"
        f"Document:\n{text}\n\n"
        "Please explain in a friendly and clear way, not like a textbook. Your goal is to help the person really understand, not just memorize.\n"
    )
    if feedback:
        base_prompt += f"\nThe user found the previous explanation unclear. Here's what they said: '{feedback}'. Please improve the explanation based on this feedback.\n"

    word_count = len(text.split())
    if word_count < 500:
        base_prompt += "Keep it short and to the point (less than 300 words)."
    elif word_count > 5000:
        base_prompt += "Provide a long, comprehensive explanation (at least 1000 words)."
    else:
        base_prompt += "Keep it around 500–700 words."

    response = model.generate_content(base_prompt)
    return getattr(response, 'text', str(response))

def text_to_speech(text, filename="explanation_audio.mp3"):
    logging.info("Converting explanation text to speech.")
    tts = gTTS(text)
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    tts.save(temp_path)
    return temp_path

# === Streamlit App ===

st.title("📄 PDF to Audio with AI Explanation & Feedback")

uploaded_pdf = st.file_uploader("Upload a PDF file", type=["pdf"])

# Step 1: Process PDF
if uploaded_pdf is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(uploaded_pdf.read())
        temp_pdf_path = temp_pdf.name
    logging.info(f"Uploaded file saved to: {temp_pdf_path}")

    if st.button("Process PDF"):
        try:
            with st.spinner("📄 Extracting text from PDF..."):
                extracted_text = extract_text_from_pdf(temp_pdf_path)

            if not extracted_text.strip():
                st.error("No text could be extracted from the PDF.")
                logging.error("No text extracted.")
            else:
                with st.spinner("🧹 Cleaning text..."):
                    cleaned_text = clean_text(extracted_text)
                    st.session_state.cleaned_text = cleaned_text
                st.success("✅ Text cleaned successfully.")
                logging.info("Text cleaned.")

                with st.spinner("✍ Generating summary..."):
                    summary = generate_summary(cleaned_text)
                    st.subheader("📝 Summary")
                    st.write(summary)
                    st.session_state.summary = summary
                logging.info("Summary generated.")

                with st.spinner("📘 Generating explanation..."):
                    explanation = generate_explanation(cleaned_text)
                    st.subheader("📚 Detailed Explanation")
                    st.write(explanation)
                    st.session_state.explanation = explanation
                logging.info("Explanation generated.")

                with st.spinner("🔊 Generating audio..."):
                    speech_text = remove_markdown_formatting(explanation)
                    audio_file_path = text_to_speech(speech_text)
                    st.success("✅ Audio generated.")
                    with open(audio_file_path, "rb") as audio_file:
                        st.audio(audio_file.read(), format="audio/mp3")
                    st.session_state.audio_path = audio_file_path
                logging.info("Audio played.")

        except Exception as e:
            logging.error(f"Error: {e}", exc_info=True)
            st.error(f"Something went wrong: {e}")

# Step 2: Feedback and Self-Improvement
if "cleaned_text" in st.session_state:
    st.markdown("---")
    st.subheader("💬 Feedback & Improve Explanation")

    user_feedback = st.text_input("What part was confusing or could be better? (Leave empty if you're satisfied)")

    if st.button("Improve Explanation"):
        if user_feedback.strip() == "":
            st.info("Thanks! No feedback provided.")
        else:
            with st.spinner("🔁 Improving explanation based on your feedback..."):
                improved = generate_explanation(st.session_state.cleaned_text, feedback=user_feedback)
                st.session_state.explanation = improved
                st.success("✅ Explanation improved!")
                st.write(improved)

                with st.spinner("🔊 Updating audio..."):
                    improved_speech = remove_markdown_formatting(improved)
                    audio_file_path = text_to_speech(improved_speech)
                    st.session_state.audio_path = audio_file_path
                    with open(audio_file_path, "rb") as audio_file:
                        st.audio(audio_file.read(), format="audio/mp3")