import xx_app as st
import os
import tempfile # <--- ADD THIS LINE
import models # Imports your models.py file

# --- Page Configuration ---
st.set_page_config(
    page_title="PDF Explainer AI",
    page_icon="🤖",
    layout="wide"
)

# --- App State Management ---
# Initialize session state variables to store data across reruns
if "processed_text" not in st.session_state:
    st.session_state.processed_text = ""
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "explanation" not in st.session_state:
    st.session_state.explanation = ""
if "audio_path" not in st.session_state:
    st.session_state.audio_path = None
if "feedback_history" not in st.session_state:
    st.session_state.feedback_history = []
if "processing_done" not in st.session_state:
    st.session_state.processing_done = False


# --- UI Layout ---
st.title("📚 PDF Explainer AI")
st.markdown("Upload your PDFs, choose a language, and get a simple summary, a detailed explanation, and an audio version!")

# --- Sidebar for Controls ---
with st.sidebar:
    st.header("⚙️ Controls")
    
    uploaded_files = st.file_uploader(
        "1. Upload PDF Files",
        type="pdf",
        accept_multiple_files=True,
        help="You can upload one or more PDF documents."
    )

    selected_lang_name = st.selectbox(
        "2. Select Output Language",
        options=list(models.LANGUAGES.keys()),
        index=0 # Default to English
    )
    
    # Get the language code (e.g., 'en', 'hi')
    lang_code = models.LANGUAGES[selected_lang_name]

    if st.button("🚀 Process Documents", type="primary", use_container_width=True, disabled=not uploaded_files):
        # Reset state for new processing
        st.session_state.processing_done = False
        st.session_state.feedback_history = []

        with st.spinner("Processing documents... This might take a moment for large files or scanned pages."):
            # 1. Extract Text from all PDFs
            all_texts = []
            for uploaded_file in uploaded_files:
                # To process, save the file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                text = models.extract_text_from_pdf(tmp_path)
                if text:
                    all_texts.append(text)
                os.remove(tmp_path) # Clean up the temp file
            
            if not all_texts:
                st.error("Could not extract any text from the uploaded PDF(s). Please try a different file.")
            else:
                st.session_state.processed_text = "\n\n--- (End of Document) ---\n\n".join(all_texts)
                
                # 2. Generate Content
                # Placeholder for fetching personalized keywords from a database
                user_keywords = models.get_user_keywords_from_db(user_id="user123") # Example user_id
                
                st.session_state.summary = models.generate_summary(st.session_state.processed_text, selected_lang_name)
                st.session_state.explanation = models.generate_explanation(
                    st.session_state.processed_text, 
                    selected_lang_name,
                    user_keywords=user_keywords
                )

                # 3. Generate Audio
                if "Error:" not in st.session_state.explanation:
                    st.session_state.audio_path = models.text_to_speech(st.session_state.explanation, lang_code)
                else:
                    st.session_state.audio_path = None
                    
                st.session_state.processing_done = True
        st.success("Processing complete!")


# --- Main Content Area ---
if st.session_state.processing_done:
    
    # Use tabs for a clean layout
    tab1, tab2 = st.tabs(["📄 Summary & Explanation", "📝 Extracted Text"])

    with tab1:
        st.header(f"Results in {selected_lang_name}")

        # --- Summary Section ---
        with st.container(border=True):
            st.subheader("Quick Summary")
            st.markdown(st.session_state.summary)

        st.divider()
        
        # --- Explanation Section ---
        with st.container(border=True):
            st.subheader("Simple Explanation")
            st.markdown(st.session_state.explanation)

            # --- Audio Player ---
            if st.session_state.audio_path:
                st.subheader("🎧 Listen to the Explanation")
                st.audio(st.session_state.audio_path, format="audio/mp3")
                # Provide a download button for the audio
                with open(st.session_state.audio_path, "rb") as f:
                    st.download_button("Download Audio (MP3)", f, file_name="explanation.mp3")
            else:
                st.warning("Could not generate audio for the explanation.")

        st.divider()

        # --- Feedback Section ---
        st.subheader("🗣️ Give Feedback")
        st.markdown("Not quite right? Tell the AI how to improve the explanation.")
        
        feedback_prompt = st.text_area(
            "Example: 'Explain it more simply', 'Use an analogy about cars', 'Focus more on the second part'",
            key="feedback_input"
        )
        
        if st.button("🔄 Regenerate with Feedback", use_container_width=True):
            if feedback_prompt:
                with st.spinner("Rethinking the explanation based on your feedback..."):
                    st.session_state.feedback_history.append(feedback_prompt)
                    
                    # Save feedback to DB (placeholder)
                    models.save_feedback_to_db("pdf123", st.session_state.explanation, feedback_prompt, [])

                    # Regenerate explanation
                    st.session_state.explanation = models.generate_explanation(
                        st.session_state.processed_text,
                        selected_lang_name,
                        feedback_history=st.session_state.feedback_history
                    )

                    # Regenerate audio
                    if "Error:" not in st.session_state.explanation:
                        st.session_state.audio_path = models.text_to_speech(st.session_state.explanation, lang_code)
                    else:
                        st.session_state.audio_path = None
                
                st.success("Explanation updated!")
                # A st.rerun() is implicitly called when a button is clicked, updating the UI.
            else:
                st.warning("Please enter some feedback to regenerate.")


    with tab2:
        st.header("Raw Extracted Text")
        st.text_area("Text extracted from your documents:", value=st.session_state.processed_text, height=400, disabled=True)
        
else:
    st.info("Upload PDF files and click 'Process Documents' to begin.")