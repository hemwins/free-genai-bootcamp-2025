# This is a chatbot application
import streamlit as st
from agent.agent import HindiLearningAgent
from models.embedding_model import FastTextEmbedding
from models.generative_model import generate_response
from utils.logger import get_logger
from utils.config import config
import random
import traceback
import sys
import os

# Initialize logger
logger = get_logger(__name__)

def init_session():
    """Initialize session state and return agent instance"""
    if "student_id" not in st.session_state:
        st.session_state.student_id = f"student_{random.randint(1000, 9999)}"
        logger.info(f"New session started with student_id: {st.session_state.student_id}")
    
    if "agent" not in st.session_state:
        try:
            logger.debug("Initializing HindiLearningAgent")
            st.session_state.agent = HindiLearningAgent(st.session_state.student_id)
            logger.info("Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}\n{traceback.format_exc()}")
            st.error("Failed to initialize the learning agent. Please try again or contact support.")
            st.stop()

def clear_text_input():
    """Clear the text input field."""
    st.session_state.user_answer = ""

def display_summary():
    """Display the session summary."""
    logger.info(f"Session ended for student: {st.session_state.student_id}")
    summary = agent.summarize_session()
    
    clear_text_input()  # Clear the text input when the session summary is displayed
    # Clear the page
    st.empty()
    
    # Display the summary in the center of the page
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.subheader("📊 आज का प्रदर्शन")
    st.write(f"✅ सही जवाब: {summary.get('correct_answers', 0)}")
    st.write(f"❌ त्रुटियाँ: {summary.get('incorrect_answers', 0)}")
    st.write(f"📚 कितना सीखा: {len(summary.get('words_learned', []))}")
    if summary.get('words_learned'):
        st.write(f"📝 नए शब्द: {', '.join(summary['words_learned'])}")
    st.success("फिर मिलेंगे! 👋")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# Initialize session
init_session()
agent = st.session_state.agent

try:
    # Streamlit UI Setup
    st.set_page_config(page_title="हिंदी सीखें", layout="centered")
    st.title("🇮🇳 चलो, हिंदी सीखें 📔")
    st.write("सही जवाब दो तो गुब्बारे लो! 🎈")

    # Fetch a new word for the student
    if "current_word" not in st.session_state or st.session_state.get("new_word_needed", True):
        logger.debug("Fetching new word")
        try:
            new_word = agent.get_new_word()
            if new_word:
                st.session_state.current_word = new_word
                st.session_state.new_word_needed = False
                logger.info(f"New word selected: {new_word}")
                clear_text_input()  # Clear the text input when a new word is fetched
            else:
                # Try to initialize the database with words if it's empty
                logger.info("No words found, attempting to initialize database")
                # This will trigger word initialization in the agent
                new_word = agent.get_new_word()
                if new_word:
                    st.session_state.current_word = new_word
                    st.session_state.new_word_needed = False
                    logger.info(f"Database initialized, new word selected: {new_word}")
                else:
                    logger.info("No more unlearned words available")
                    st.success("🎉 Congratulations! You have learned all words! Let's start a new session to practice more.")
                    # Clear session state to start fresh
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
        except Exception as e:
            logger.error(f"Error fetching new word: {str(e)}\n{traceback.format_exc()}")
            st.error("Failed to fetch a new word. Please try again.")
            st.stop()

    st.subheader(f"इस शब्द का पर्यायवाची क्या होगा: **{st.session_state.current_word}**?")

    # Initialize state for showing hints
    if "show_hints" not in st.session_state:
        st.session_state.show_hints = False

    # User input - show only if hints are not displayed
    if not st.session_state.show_hints:
        user_answer = st.text_input("बताओ:", key="user_answer")

        if st.button("जवाब"):
            if user_answer.strip():
                logger.debug(f"Checking answer: {user_answer} for word: {st.session_state.current_word}")
                is_correct = agent.check_answer(user_answer.strip(), st.session_state.current_word)

                if is_correct:
                    logger.info(f"Correct answer given for word: {st.session_state.current_word}")
                    # Mark word as learned in the database
                    try:
                        agent.db.mark_word_as_learned(st.session_state.student_id, st.session_state.current_word)
                        logger.info(f"Word {st.session_state.current_word} marked as learned for student {st.session_state.student_id}")
                    except Exception as e:
                        logger.error(f"Error marking word as learned: {str(e)}")
                    
                    st.success("वाह! बहुत खूब!")
                    st.balloons()
                    
                    # Ask if the student wants to learn more
                    if "learn_more" not in st.session_state:
                        st.session_state.learn_more = st.radio(
                            "क्या अगला शब्द सीखना चाहोगे?",
                            ("हाँ", "नहीं"),
                            key="learn_more"
                        )
                    
                    if st.session_state.learn_more == "हाँ":
                        st.session_state.new_word_needed = True
                        st.session_state.show_hints = False
                    else:
                        display_summary()  # Display summary when the student selects "नहीं"
                else:
                    logger.info(f"Incorrect answer: {user_answer} for word: {st.session_state.current_word}")
                    st.error("❌ ओहो! थोड़ा और सोचो:")
                    st.session_state.show_hints = True
                    st.rerun()
            else:
                logger.warning("Empty answer submitted")
                st.warning("⚠️ भई, जवाब दो, लाजवाब मत करो")

    # Show hints and multiple choice options
    if st.session_state.show_hints:
        hint_result = agent.get_hint(st.session_state.current_word)
        
        # Display contextual hint
        st.info(f"💡 मदद: {hint_result.get('hint')}")
        
        # Display multiple choice options with buttons
        st.write("शायद इनमें से कोई हो:")
        
        # Create two columns for options
        col1, col2 = st.columns(2)
        
        # Display options in a 2x2 grid
        for i, option in enumerate(hint_result['options']):
            with col1 if i < 2 else col2:
                if st.button(f"👉 {option}", key=f"option_{i}", use_container_width=True):
                    is_correct = agent.check_answer(option, st.session_state.current_word)
                    if is_correct:
                        # Mark word as learned in the database
                        try:
                            agent.db.mark_word_as_learned(st.session_state.student_id, st.session_state.current_word)
                            logger.info(f"Word {st.session_state.current_word} marked as learned for student {st.session_state.student_id}")
                        except Exception as e:
                            logger.error(f"Error marking word as learned: {str(e)}")
                            
                        st.success("वाह! बहुत खूब!")
                        st.balloons()
                        st.session_state.new_word_needed = True
                        st.session_state.show_hints = False
                        st.rerun()
                    else:
                        st.error("❌ ओहो! यह भी नहीं...")
        
        # Add a button to go back to text input
        st.button("नया जवाब लिखें", on_click=lambda: setattr(st.session_state, 'show_hints', False))

    # Quit option
    if st.button("अब बस"):
        display_summary()  # Display summary when the "अब बस" button is clicked

except Exception as e:
    logger.error(f"Application error: {str(e)}", exc_info=True)
    st.error("An error occurred. Please try again or contact support.")

