import streamlit as st
from agent.agent import HindiLearningAgent
from utils.logger import get_logger
import random
import traceback
import speech_recognition as sr
import base64
import time

def init_session():
    """Initialize session state variables and agent."""
    st.session_state.setdefault("current_word", None)
    st.session_state.setdefault("show_learn_more", False)
    st.session_state.setdefault("learn_more", None)
    st.session_state.setdefault("show_hints", False)
    st.session_state.setdefault("practice_mode", None)
    st.session_state.setdefault("total_synonyms_correct", 0)
    st.session_state.setdefault("total_synonyms_incorrect", 0)
    st.session_state.setdefault("current_pronunciation_word", None)
    st.session_state.setdefault("show_pronunciation_hints", False) 
    st.session_state.setdefault("total_pronunciation_correct", 0)
    st.session_state.setdefault("total_pronunciation_incorrect", 0)
    st.session_state.setdefault("new_word_needed", True)
    st.session_state.setdefault("pronunciation_hints", None)

init_session()

st.set_page_config(page_title="हिंदी सीखें", layout="centered")
st.title("🇮🇳 हिंदी सीखें 📔")
st.write("सही उत्तर दो और गुब्बारे पाओ! 🎈")

logger = get_logger(__name__)
    
if "student_id" not in st.session_state:
    st.session_state.student_id = f"student_{random.randint(1000, 9999)}"
    logger.info(f"New session started with student_id: {st.session_state.student_id}")
if "agent" not in st.session_state:
    try:
        st.session_state.agent = HindiLearningAgent(st.session_state.student_id)
        # st.write(st.session_state.agent)
    except Exception as e:
        logger.error(f"Failed to initialize agent: {str(e)}\n{traceback.format_exc()}")
        st.error("शिक्षण एजेंट प्रारंभ करने में विफल। कृपया पुनः प्रयास करें।")
        st.stop()
    time.sleep(0.5)

def fetch_new_word():
    """Fetch a new word for the student."""
    try:
        new_word = st.session_state.agent.get_new_word()
        st.success("🎉 सत्र प्रारंभ हो रहा है।")
        logger.info(f"New word fetched: {new_word}")
        if new_word:
            st.session_state.current_word = new_word
            st.session_state.new_word_needed = False
        else:
            logger.warning("No new word returned from agent.get_new_word()")
            st.error("नया शब्द लाने में विफल। एजेंट ने कोई शब्द नहीं लौटाया।")
            st.session_state.new_word_needed = True  # Ensure it retries
    except Exception as e:
        logger.error(f"Error fetching new word: {str(e)}\n{traceback.format_exc()}")
        st.error("नया शब्द लाने में विफल। कृपया पुनः प्रयास करें।")
        st.stop()

def handle_user_answer(user_answer, practice_type):
    """Handle user's answer and provide feedback."""
    if not user_answer.strip():
        st.warning("⚠️ कृपया उत्तर दें।")
        return
    if practice_type == "synonyms":
        is_correct = st.session_state.agent.check_answer(user_answer.strip(), st.session_state.current_word)
        if is_correct:
            st.success("सही उत्तर! 🎉")
            st.balloons()
            st.session_state.show_learn_more = True
            st.session_state.total_synonyms_correct += 1
        else:
            st.error("गलत उत्तर! पुनः प्रयास करें।")
            st.session_state.show_hints = True
            time.sleep(0.5)
            st.session_state.total_synonyms_incorrect += 1
            display_hints()
        time.sleep(0.5)
        # st.rerun() # so that hints appear automatically
    elif practice_type == "pronunciation":
        response = st.session_state.agent.process_student_interaction(f"evaluate the pronuncation of student for the word {st.session_state.current_pronunciation_word} and student said {user_answer}")

        st.info(response.get("output"))

        if "सही" in response.get("output"):# quick hack instead implement correct parser
            st.session_state.total_pronunciation_correct += 1
            st.success("सही उत्तर! 🎉")
            st.balloons()
        else:
            st.error("गलत उत्तर! पुनः प्रयास करें।")
            st.session_state.total_pronunciation_incorrect += 1

def display_hints():
    
    hint_result = st.session_state.agent.get_hint(st.session_state.current_word)
    if isinstance(hint_result, dict):
        # Display the main hint/context
        with st.container():
            st.markdown("### 💡 संकेत")
            if "hint" in hint_result:
                st.write(hint_result["hint"])
            
            # Display cultural context if available
            if "cultural_context" in hint_result and hint_result["cultural_context"]:
                st.markdown("#### 🎯 सांस्कृतिक संदर्भ")
                st.write(hint_result["cultural_context"])
            
            # Display example usage if available
            if "example" in hint_result and hint_result["example"]:
                st.markdown("#### 📝 उदाहरण")
                st.write(hint_result["example"])
        
        #Add button to hide hints
        if st.button("संकेत छिपाएं", key="hide_hints"):
            st.session_state.show_hints = False
            st.rerun()
    else:
        st.info(f"💡 संकेत: {hint_result}")

def handle_learn_more():
    """Handle learn more option."""
    learn_more_choice = st.radio("क्या आप और सीखना चाहेंगे?", ("हाँ", "नहीं"), key="learn_more")
    if learn_more_choice == "हाँ":
        st.session_state.new_word_needed = True
        st.session_state.show_learn_more = False
        st.rerun()
    elif learn_more_choice == "नहीं":
        display_summary()

def display_summary():
    """Display session summary."""
    logger.info(f"Session ended for student: {st.session_state.student_id}")
    summary = st.session_state.agent.summarize_session()
    st.empty()
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    if st.session_state.practice_mode == "synonyms":
        st.write(f"📝 सीखे गए शब्द: {summary.get('words_learned', '')}")
        st.write(f"✅ पर्यायवाची सही: {st.session_state.total_synonyms_correct}")
        st.write(f"❌ पर्यायवाची गलत: {st.session_state.total_synonyms_incorrect}")
    elif st.session_state.practice_mode == "pronunciation":
        st.write(f"✅ उच्चारण सही: {st.session_state.total_pronunciation_correct}")
        st.write(f"❌ उच्चारण गलत: {st.session_state.total_pronunciation_incorrect}")
    st.success("फिर मिलेंगे! 👋")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()
    
def recognize_speech():
    """Recognizes speech from the microphone."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("बोलिए...")  # "Speak..."
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio, language="hi-IN")  # Recognize Hindi
        st.info(f"आपने कहा: {text}")  # "You said: {text}"
        return text
    except sr.UnknownValueError:
        st.error("मैं समझ नहीं पाया। कृपया फिर से बोलें।")  # "I couldn't understand. Please speak again."
        return None
    except sr.RequestError as e:
        st.error(f"Google Speech Recognition सेवा उपलब्ध नहीं है: {e}")  # "Google Speech Recognition service is not available: {e}"
        return None
      
def play_audio(audio_bytes: bytes):
    """Plays audio in Streamlit."""
    audio_base64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio autoplay="true" controls="false">
          <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

def display_pronunciation_hints():
    """Displays pronunciation hints (similar words and correct audio)."""
    if st.session_state.show_pronunciation_hints and st.session_state.get("pronunciation_hints"):
        hints = st.session_state.pronunciation_hints
        st.info("यहाँ कुछ मिलते-जुलते शब्द हैं:")  # "Here are some similar-sounding words:"
        for word in hints["similar_words"]:
            st.write(f"- {word}")

        if hints["correct_audio"]:
            st.info("सही उच्चारण:")  # "Correct Pronunciation:"
            play_audio(hints["correct_audio"])
        else:
            st.warning("सही उच्चारण उपलब्ध नहीं है।")  # "Correct pronunciation not available."

def pronunciation_practice():
    """UI for pronunciation practice."""

    if not st.session_state.current_pronunciation_word:
        #This will be handled by agent now.
        #fetch_new_pronunciation_word()
        response = st.session_state.agent.process_student_interaction("Lets practice pronunciation")
        st.session_state.current_pronunciation_word = response.get("word")

    if st.session_state.current_word:
        st.subheader(f"उच्चारण अभ्यास")  
        st.subheader(f"इस शब्द का उच्चारण क्या होगा: **{st.session_state.current_word}**?")

        col1, col2, col3 = st.columns(3) # added one more column
        with col1:
            if st.button("बोलें"):  # "Speak"
                spoken_text = recognize_speech()
                if spoken_text:
                    #instead of directly calling process_student_interaction, pass it as string
                    response = st.session_state.agent.process_student_interaction(f"evaluate the pronuncation of student for the word {st.session_state.current_word} and student said {spoken_text}")
                    st.info(response.get("output"))

        with col2:
            if st.button("संकेत दिखाएँ"):  # "Show Hints"
                #instead of directly calling process_student_interaction, pass it as string
                response = st.session_state.agent.process_student_interaction(f"generate pronounciation hints for the word {st.session_state.current_word}")

                if response:
                    st.session_state.pronunciation_hints = {
                        "similar_words": [w.strip() for w in response.get("similar_words", "").split(",") if w.strip()],
                        "correct_audio": response.get("correct_audio")
                    }
                    st.session_state.show_pronunciation_hints = True
                else:
                    st.error("संकेत लाने में विफल।")  # "Failed to fetch hints."
                    st.session_state.show_pronunciation_hints = False

        with col3:
            if st.button("सत्र समाप्त करें"):  # "End Session"
                display_summary() #reuse the same display summary function

        if st.session_state.show_pronunciation_hints:
            display_pronunciation_hints()

# Main execution
agent = st.session_state.agent

# Fetch the word before practice mode selection
if st.session_state.get("new_word_needed", True):
    with st.spinner("Loading new word..."):
        fetch_new_word()

# Practice mode selection
practice_mode = st.radio(
    "आप क्या अभ्यास करना चाहेंगे?",
    ("हिंदी पर्यायवाची शब्द अभ्यास", "हिंदी उच्चारण अभ्यास"), # "Hindi Synonyms Practice", "Hindi Pronunciation Practice"
    key="practice_mode_selection"
)

if practice_mode == "हिंदी पर्यायवाची शब्द अभ्यास": # "Hindi Synonyms Practice"
    st.session_state.practice_mode = "synonyms"
elif practice_mode == "हिंदी उच्चारण अभ्यास": # "Hindi Pronunciation Practice"
    st.session_state.practice_mode = "pronunciation"

# UI based on practice mode
if st.session_state.practice_mode == "synonyms":
    # Ensure current_word and show_hints are initialized
    if "current_word" not in st.session_state:
        st.session_state.current_word = None
    if "show_hints" not in st.session_state:
        st.session_state.show_hints = False

    # Check if current_word is still None after fetch_new_word()
    if not st.session_state.show_learn_more:
        if "current_word" not in st.session_state or st.session_state.get("new_word_needed", True):
            with st.spinner("Loading new word..."):
                fetch_new_word()
        
        if st.session_state.current_word is not None:
            st.subheader(f"इस शब्द का पर्यायवाची क्या होगा: **{st.session_state.current_word}**?")
            
            if not st.session_state.show_hints:
                user_answer = st.text_input("आपका उत्तर:", key="user_answer")
                if st.button("जवाब"):
                    handle_user_answer(user_answer, "synonyms")
        else:
            st.error("नया शब्द लाने में विफल।")
            st.stop()
        if st.button("सत्र समाप्त करें"):
            display_summary()
    else:
        # Show only the learn more options when in learn more state
        handle_learn_more()
        
elif st.session_state.practice_mode == "pronunciation":
    pronunciation_practice()
