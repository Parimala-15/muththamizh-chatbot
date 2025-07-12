import streamlit as st
from googletrans import Translator
from gtts import gTTS
import os
import io
import json
from deep_translator import GoogleTranslator
import PyPDF2
import docx
import nltk
from nltk.tokenize import sent_tokenize
import sounddevice as sd
import soundfile as sf
import numpy as np
from PIL import Image
import re

# Download required NLTK data
nltk.download('punkt')

def load_thirukkural_database():
    """Load Thirukkural data from JSON file"""
    try:
        with open(os.path.join("data", "thirukkural_data.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            # Convert to a more convenient format for searching
            thirukkural_db = {
                kural["number"]: {
                    "kural_number": kural["number"],
                    "tamil_kural": kural["kural"],
                    "tamil_meaning": kural["tamil_meaning"],
                    "english_translation": kural["english_meaning"]
                }
                for kural in data["thirukkural"]
            }
            return thirukkural_db
    except Exception as e:
        st.error(f"Error loading Thirukkural database: {str(e)}")
        return {}

def get_thirukkural_response(query, thirukkural_db):
    """Get relevant Thirukkural response based on query"""
    query = query.lower()
    matches = []
    
    # Search through the database
    for kural_num, kural_data in thirukkural_db.items():
        search_text = f"{kural_data['tamil_kural']} {kural_data['tamil_meaning']} {kural_data['english_translation']}".lower()
        
        if query in search_text:
            matches.append(kural_data)
    
    if matches:
        return format_thirukkural_response(matches)
    return "I couldn't find a relevant Thirukkural for your query. Please try with different keywords."

def format_thirukkural_response(matches):
    """Format Thirukkural matches into a readable response"""
    response = []
    
    for match in matches:
        response.append(f"\n### திருக்குறள் {match['kural_number']} | Thirukkural {match['kural_number']}")
        response.append("\n**குறள் | Kural:**")
        response.append(f"*{match['tamil_kural']}*")
        
        if match['tamil_meaning']:
            response.append("\n**தமிழ் விளக்கம் | Tamil Explanation:**")
            response.append(match['tamil_meaning'])
        
        if match['english_translation']:
            response.append("\n**English Translation & Meaning:**")
            response.append(match['english_translation'])
        
        response.append("\n---")
    
    return "\n".join(response)

def text_to_speech(text, lang='ta'):
    """Convert text to speech"""
    tts = gTTS(text=text, lang=lang)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp

def summarize_tamil_text(text, ratio=0.3):
    """Summarize Tamil text"""
    # Translate to English for better processing
    translator = Translator()
    eng_text = translator.translate(text, src='ta', dest='en').text
    
    # Tokenize and select important sentences
    sentences = sent_tokenize(eng_text)
    n_sentences = max(1, int(len(sentences) * ratio))
    summary_eng = " ".join(sentences[:n_sentences])
    
    # Translate back to Tamil
    summary_tamil = translator.translate(summary_eng, src='en', dest='ta').text
    return summary_tamil

def search_word_in_document(document_text, search_word):
    """Search for a word in document and return context"""
    results = []
    sentences = sent_tokenize(document_text)
    for sentence in sentences:
        if search_word.lower() in sentence.lower():
            results.append(sentence)
    return results

def translate_word(text, source_lang="en"):
    """Translate a word using the local database"""
    text = text.lower()
    if source_lang == "en":
        translations = translations_data["translations"]["english_to_tamil"]
        poetic_translations = {}  # English to Tamil not available in poetic_words
        return translations.get(text, None)
    else:
        translations = translations_data["translations"]["tamil_to_english"]
        poetic_translations = translations_data["poetic_words"]["tamil_to_english"]
        # Try normal translations first, then poetic words
        return translations.get(text, poetic_translations.get(text, None))

# Custom CSS for Tamil-themed styling
CUSTOM_CSS = """
<style>
.main {
    background-color: #FFF7E6;
}
.stApp {
    font-family: 'Latha', 'Arial', sans-serif;
}
.title {
    color: #8B4513;
    text-align: center;
    font-size: 2.5em;
}
.tamil-border {
    border: 2px solid #8B4513;
    border-radius: 10px;
    padding: 20px;
    margin: 10px;
}
</style>
"""

# Tamil literature database (sample)
TAMIL_LITERATURE = {
    "thirukkural": {
        "info": "Classical Tamil text containing 1330 couplets",
        "examples": {
            "அறம்": "Virtue/Dharma",
            "பொருள்": "Wealth/Material",
            "இன்பம்": "Love/Pleasure"
        }
    },
    "silappatikaram": {
        "info": "One of the Five Great Epics of Tamil Literature",
        "examples": {
            "கண்ணகி": "Kannagi - The protagonist",
            "கோவலன்": "Kovalan - Kannagi's husband"
        }
    }
}

def main():
    st.set_page_config(page_title="முத்தமிழ் - Muththamizh Chatbot", layout="wide")
    
    # Load Thirukkural database at startup
    thirukkural_db = load_thirukkural_database()
    
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Header with Tamil-themed design
    st.markdown("<h1 class='title'>முத்தமிழ் - Muththamizh</h1>", unsafe_allow_html=True)
    
    # Sidebar for navigation
    option = st.sidebar.selectbox(
        "Choose a Service",
        ["Translation", "Literature Query", "Thirukkural Search", "Text Summarization", "Word Search"]
    )

    if option == "Translation":
        st.markdown("<div class='tamil-border'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            source_lang = st.selectbox("From:", ["English", "Tamil"])
            input_text = st.text_area("Enter text:", height=150)
            
        with col2:
            target_lang = "Tamil" if source_lang == "English" else "English"
            st.write(f"Translating to: {target_lang}")
            
            if st.button("Translate"):
                if input_text:
                    src = 'en' if source_lang == "English" else 'ta'
                    dest = 'ta' if target_lang == "Tamil" else 'en'
                    
                    # First try local database for single words
                    local_translation = translate_word(input_text.strip(), src)
                    
                    if local_translation:
                        st.text_area("Translation:", value=local_translation, height=150)
                    else:
                        # Fall back to online translation for phrases or unknown words
                        translator = Translator()
                        translated = translator.translate(input_text, src=src, dest=dest)
                        st.text_area("Translation:", value=translated.text, height=150)
                    
                    # Text-to-speech
                    if st.button("Listen"):
                        audio_fp = text_to_speech(translated.text, lang=dest)
                        st.audio(audio_fp)
        
        st.markdown("</div>", unsafe_allow_html=True)

    elif option == "Literature Query":
        st.markdown("<div class='tamil-border'>", unsafe_allow_html=True)
        query = st.text_input("Ask about Tamil literature:")
        
        if query:
            # Simple keyword-based response system
            response = ""
            query_lower = query.lower()
            
            for work, details in TAMIL_LITERATURE.items():
                if work in query_lower:
                    response = f"{work.title()}: {details['info']}\n\nCommon terms:\n"
                    for term, meaning in details['examples'].items():
                        response += f"{term}: {meaning}\n"
            
            if response:
                st.write(response)
            else:
                st.write("I'm sorry, I don't have information about that specific topic.")
        
        st.markdown("</div>", unsafe_allow_html=True)

    elif option == "Thirukkural Search":
        st.markdown("<div class='tamil-border'>", unsafe_allow_html=True)
        st.markdown("### திருக்குறள் தேடல் | Thirukkural Search")
        
        # Add description
        st.markdown("""
        இந்த பகுதியில் நீங்கள் திருக்குறள்களைத் தேடலாம். தமிழிலோ அல்லது ஆங்கிலத்திலோ உங்கள் 
        தேடல் சொற்களை உள்ளிடவும்.
        
        Search Thirukkural by entering keywords in Tamil or English. The search will look through both 
        the Kural text and its meanings.
        """)
        
        col1, col2 = st.columns([2,1])
        
        with col1:
            search_query = st.text_input("Enter keywords | சொற்களை உள்ளிடவும்:", 
                                       placeholder="Example: love, அன்பு, virtue, அறம்")
            
            if search_query:
                response = get_thirukkural_response(search_query, thirukkural_db)
                st.markdown(response)
        
        with col2:
            st.markdown("""
            **Popular Topics | பிரபல தலைப்புகள்:**
            - அறம் (Virtue)
            - பொருள் (Wealth)
            - இன்பம் (Love)
            - நட்பு (Friendship)
            - கல்வி (Education)
            """)
        
        st.markdown("</div>", unsafe_allow_html=True)

    elif option == "Text Summarization":
        st.markdown("<div class='tamil-border'>", unsafe_allow_html=True)
        text_input = st.text_area("Enter Tamil text for summarization:", height=200)
        ratio = st.slider("Summary length ratio:", 0.1, 0.5, 0.3)
        
        if st.button("Summarize"):
            if text_input:
                summary = summarize_tamil_text(text_input, ratio)
                st.write("Summary:")
                st.write(summary)
        
        st.markdown("</div>", unsafe_allow_html=True)

    elif option == "Word Search":
        st.markdown("<div class='tamil-border'>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload a document (PDF/DOCX)", type=['pdf', 'docx'])
        search_word = st.text_input("Enter word to search:")
        
        if uploaded_file and search_word:
            document_text = ""
            
            if uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    document_text += page.extract_text()
            
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = docx.Document(uploaded_file)
                document_text = " ".join([paragraph.text for paragraph in doc.paragraphs])
            
            results = search_word_in_document(document_text, search_word)
            if results:
                st.write(f"Found {len(results)} occurrences:")
                for i, result in enumerate(results, 1):
                    st.write(f"{i}. {result}")
            else:
                st.write("Word not found in document.")
        
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
