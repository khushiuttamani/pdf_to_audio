This Streamlit app extracts text from a PDF, summarizes it, explains it using real-life examples (powered by Google Gemini AI), and finally converts the explanation into audio using Google Text-to-Speech (gTTS).

---

## 🚀 Features

- ✅ Upload and process any PDF (including scanned images via OCR)
- 📝 AI-generated **summary**
- 📘 AI-generated **detailed explanation** with real-life examples
- 🔊 Explanation converted to **audio**
- 🔐 Uses `.env` file for secure API key management

---

## STEP 1

git clone https://github.com/yourusername/pdf-to-audio-ai.git
cd pdf-to-audio-ai

## STEP 2 -> Create a virtual environment (optional but recommended):

python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

## STEP 3 -> Install dependencies:

pip install -r requirements.txt

## STEP 4 -> Set up your .env file: Create a file named .env in the project root and add your Google Gemini API key:

Gemini_API_Key="your_actual_gemini_api_key"

🧠 How It Works

1. Upload a PDF file.

2. Text is extracted using PyMuPDF (and OCR for image-based PDFs).

3. Gemini AI generates:

- A simplified summary
- A detailed explanation with real-life examples

4. The explanation is converted to audio using gTTS.

5. The audio is played, followed by the display of summary and explanation.

🛠 Tech Stack
Streamlit
PyMuPDF (fitz)
pytesseract (OCR)
pdf2image
Google Gemini API
gTTS (Google Text-to-Speech)
python-dotenv
