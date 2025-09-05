import streamlit as st
import time
from utils import log_progress
import requests

st.title("Student Translation & Post-Editing Platform")

# --- User login ---
username = st.text_input("Enter your username")

if username:
    st.subheader("Enter Source Text")
    source_text = st.text_area("Source Text")

    mt_type_option = st.radio("Choose MT type", ['Automatic MT', 'Manual MT'])
    
    if mt_type_option == 'Automatic MT' and source_text:
        # --- Call LibreTranslate API ---
        url = "https://libretranslate.com/translate"
        payload = {
            "q": source_text,
            "source": "en",
            "target": "ar",
            "format": "text"
        }
        response = requests.post(url, data=payload)
        mt_output = response.json().get('translatedText', '')
        st.text_area("MT Output", mt_output, height=150)
        mt_type = 'auto'
    else:
        mt_output = st.text_area("Paste MT output here", height=150)
        mt_type = 'manual'

    student_edit = st.text_area("Your Post-Edited Translation", height=150)
    start_time = time.time()
    if st.button("Submit"):
        duration = time.time() - start_time
        if source_text and mt_output and student_edit:
            log_progress(username, source_text, mt_output, student_edit, duration, mt_type)
            st.success("Submission logged!")
        else:
            st.error("Please fill all fields.")
