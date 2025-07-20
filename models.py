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

# --- Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# --- API Configuration ---
try:
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=API_KEY)
    # Using a system instruction can prime the model for all subsequent requests
    system_instruction = "You are an expert educator who explains complex topics in simple terms."
    model = genai.GenerativeModel(
        "models/gemini-1.5-flash-latest",
        system_instruction=system_instruction
    )
except Exception as e:
    logging.error(f"Failed to configure Gemini API: {e}")
    model = None # Set model to None if configuration fails

# --- Constants ---
LANGUAGES = {
    "English": "en", "Hindi": "hi", "Gujarati": "gu", "Marathi": "mr",
    "Tamil": "ta", "Telugu": "te", "Kannada": "kn", "Bengali": "bn",
    "Malayalam": "ml", "Punjabi": "pa", "Urdu": "ur"
}

# === DATABASE PLACEHOLDER FUNCTIONS ===
# In a real app, these would interact with your database (e.g., SQLite, PostgreSQL)
def save_feedback_to_db(pdf_id, generated_content, feedback, keywords):
    logging.info(f"DATABASE_STUB: Saving feedback for PDF {pdf_id}.")
    # Example: conn.execute("INSERT INTO feedback ...", (pdf_id, ...))
    pass

def get_user_keywords_from_db(user_id):
    logging.info(f"DATABASE_STUB: Getting personalized keywords for user {user_id}.")
    # Example: rows = conn.execute("SELECT keyword FROM user_prefs WHERE user_id=?", (user_id,))
    # return [row[0] for row in rows]
    return [] # Return empty list for now

# --- Core Functions ---
def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF, using OCR for image-based pages more efficiently.
    """
    logging.info(f"Extracting text from: {pdf_path}")
    extracted_text = ""
    image_pages = []
    try:
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc):
            # First, try to get text directly
            text = page.get_text().strip()
            if text:
                extracted_text += text + "\n"
            else:
                # If no text, mark page for OCR
                image_pages.append(page_num + 1)
        
        # Process all image-based pages in one go for efficiency
        if image_pages:
            logging.info(f"Performing OCR on pages: {image_pages}")
            try:
                images = convert_from_path(pdf_path, first_page=min(image_pages), last_page=max(image_pages))
                # Create a map of page number to image object
                page_to_image_map = {p_num: img for p_num, img in zip(range(min(image_pages), max(image_pages) + 1), images)}

                for page_num in image_pages:
                     if page_num in page_to_image_map:
                        extracted_text += pytesseract.image_to_string(page_to_image_map[page_num]) + "\n"
            except Exception as ocr_error:
                logging.error(f"OCR processing failed for {pdf_path}: {ocr_error}")

        doc.close()
        logging.info(f"Text extraction complete for {pdf_path}.")
        return clean_text(extracted_text)
    except Exception as e:
        logging.error(f"Failed to open or process PDF {pdf_path}: {e}")
        return "" # Return empty string on failure

def clean_text(text):
    """
    Cleans extracted text by removing unwanted characters and normalizing whitespace.
    """
    logging.info("Cleaning extracted text.")
    # Remove special characters but keep essential punctuation and multilingual characters
    text = re.sub(r'(\n\s*)+\n', '\n', text) # Replace multiple newlines with a single one
    text = re.sub(r'[ \t]+', ' ', text)      # Replace multiple spaces/tabs with a single space
    return text.strip()

def generate_summary(text, language):
    """
    Generates a concise summary of the text in the specified language.
    """
    if not model: return "Error: Gemini model is not configured. Please check API key."
    logging.info(f"Generating summary in {language}.")
    prompt = (
        f"You are a helpful assistant. Summarize the following document in a few simple sentences in {language}. "
        "Focus only on the core message. The goal is a very quick overview.\n\n"
        f"DOCUMENT:\n---\n{text}"
    )
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Gemini API call for summary failed: {e}")
        return f"Error: Could not generate summary. ({e})"

def generate_explanation(text, language, feedback_history=None, user_keywords=None):
    """
    Generates a simple, beginner-friendly explanation with real-life examples.
    """
    if not model: return "Error: Gemini model is not configured. Please check API key."
    logging.info(f"Generating explanation in {language}.")
    
    prompt_parts = [
        f"Explain the following document in {language} for a complete beginner. Use simple words, short sentences, and a friendly tone. "
        "Crucially, provide a relatable, real-life example or analogy to make the main concept understandable.",
        f"\nDOCUMENT:\n---\n{text}"
    ]
    
    if feedback_history:
        feedback_str = "\n".join(feedback_history)
        prompt_parts.append(f"\nIMPROVEMENT INSTRUCTIONS:\nThe user was not satisfied with a previous version. "
                            f"Based on their feedback, please refine the explanation. Feedback: '{feedback_str}'")

    if user_keywords:
        keywords_str = ", ".join(user_keywords)
        prompt_parts.append(f"\nUSER PREFERENCES: The user is particularly interested in these topics: {keywords_str}. Please emphasize them if relevant.")

    prompt = "\n".join(prompt_parts)

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Gemini API call for explanation failed: {e}")
        return f"Error: Could not generate explanation. ({e})"

def text_to_speech(text, lang_code="en"):
    """
    Converts text to an MP3 audio file using gTTS.
    """
    logging.info(f"Converting text to speech in language: {lang_code}")
    # Remove markdown for cleaner speech
    clean_audio_text = re.sub(r"[\*#_`~]+", "", text)
    try:
        tts = gTTS(text=clean_audio_text, lang=lang_code, slow=False)
        # Use a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        logging.error(f"gTTS failed: {e}")
        return None