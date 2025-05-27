PaperTalk is a Streamlit app extracts text from a PDF, summarizes it, explains it using real-life examples (powered by Google Gemini AI), and finally converts the explanation into audio using Google Text-to-Speech (gTTS).

🚀 Features:

✅ Upload and process any PDF, including scanned PDFs (OCR supported)
📝 AI-generated summary using Gemini
📘 Detailed, easy-to-understand explanation with real-life examples
🔊 Audio output of explanation for better accessibility and learning
🔐 Uses a .env file to securely manage your Google Gemini API key
🔁 Get feedback and improve the explanation interactively

🧠 How It Works:

- Upload a PDF file.
- Text is extracted using PyMuPDF, and pytesseract is used for scanned/image-based pages.
- The extracted content is passed to Gemini AI to generate:
- A simplified summary
- A clear and friendly explanation using real-world examples
- The explanation is converted into speech using gTTS.
- The audio is played alongside the displayed summary and explanation.
- You can provide feedback to improve the explanation with one click!

🛠 Tech Stack:

Streamlit – Web App Framework
PyMuPDF – PDF Text Extraction
pytesseract – OCR for scanned pages
pdf2image – Convert PDF pages to images
gTTS – Google Text-to-Speech
google.generativeai – Gemini API
python-dotenv – Environment Variable Loader

📦 Installation

## STEP 1 — Clone the repository:

git clone https://github.com/yourusername/pdf-to-audio-ai.git
cd pdf-to-audio-ai

## STEP 2 — (Optional) Create a virtual environment:

python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

## STEP 3 — Install dependencies:

pip install -r requirements.txt

## STEP 4 — Set up your .env file:

Create a file named .env in the root of your project and add your API key like this:
GENAI_API_KEY="your_actual_gemini_api_key"
