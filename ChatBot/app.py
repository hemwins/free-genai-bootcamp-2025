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

def show_session_summary():
    """Show the session summary and stop the application"""
    logger.info(f"Session ended for student: {st.session_state.student_id}")
    summary = agent.summarize_session()
    st.subheader("📊 आज का प्रदर्शन")
    st.write(f"✅ सही जवाब: {summary['correct_answers']}")
    st.write(f"❌ त्रुटियाँ: {summary['incorrect_answers']}")
    st.write(f"📚 कितना सीखा: {len(summary['words_learned'])}")
    if summary['words_learned']:
        st.write(f"📝 नए शब्द: {', '.join(summary['words_learned'])}")
    st.success("फिर मिलेंगे! 👋")
    st.stop()

def init_session():
    """Initialize session state and return agent instance"""
    # Set up page first
    st.set_page_config(page_title="हिंदी सीखें", layout="centered")
    st.title("🇮🇳 चलो, हिंदी सीखें 📔")
    
    if "initialization_stage" not in st.session_state:
        st.session_state.initialization_stage = "start"
    
    if st.session_state.initialization_stage == "start":
        # Show loading message
        with st.spinner("⚡ आपका स्वागत है! रुको थोड़ा..."):
            # Initialize student ID
            if "student_id" not in st.session_state:
                st.session_state.student_id = f"student_{random.randint(1000, 9999)}"
                logger.info(f"New session started with student_id: {st.session_state.student_id}")
            
            # Initialize agent
            if "agent" not in st.session_state:
                try:
                    logger.debug("Initializing HindiLearningAgent")
                    st.session_state.agent = HindiLearningAgent(st.session_state.student_id)
                    logger.info("Agent initialized successfully")
                    st.session_state.initialization_stage = "complete"
                    st.rerun()
                except Exception as e:
                    logger.error(f"Failed to initialize agent: {str(e)}\n{traceback.format_exc()}")
                    st.error("Failed to initialize the learning agent. Please try again or contact support.")
                    st.stop()

# Initialize session
init_session()

# Only proceed if initialization is complete
if st.session_state.initialization_stage != "complete":
    st.stop()

agent = st.session_state.agent

try:
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

        if st.button("मेरा जवाब"):
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
                    
                    # Ask if student wants to continue learning
                    st.write("क्या आप और सीखना चाहेंगे?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✨ हाँ, और सीखें!", key="continue_yes"):
                            st.session_state.new_word_needed = True
                            st.session_state.show_hints = False
                            st.rerun()
                    with col2:
                        # Show session summary when student chooses to stop
                        if st.button("🔚 नहीं, बस", key="continue_no"):
                            # Get and display the session summary
                            summary = agent.summarize_session()
                            st.subheader("📊 आज का प्रदर्शन")
                            st.write(f"✅ सही जवाब: {summary['correct_answers']}")
                            st.write(f"❌ त्रुटियाँ: {summary['incorrect_answers']}")
                            st.write(f"📚 कितना सीखा: {len(summary['words_learned'])}")
                            if summary['words_learned']:
                                st.write(f"📝 नए शब्द: {', '.join(summary['words_learned'])}")
                            st.success("फिर मिलेंगे! 👋")
                            st.stop()
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
        st.info(f"💡 मदद: {hint_result['hint']}")
        
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
                        
                        # Ask if student wants to continue learning
                        st.write("क्या आप और सीखना चाहेंगे?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✨ हाँ, और सीखें!", key="continue_yes_mc"):
                                st.session_state.new_word_needed = True
                                st.session_state.show_hints = False
                                st.rerun()
                        with col2:
                            # Show session summary when student chooses to stop
                            if st.button("🔚 नहीं, बस", key="continue_no_mc"):
                                # Get and display the session summary
                                summary = agent.summarize_session()
                                st.subheader("📊 आज का प्रदर्शन")
                                st.write(f"✅ सही जवाब: {summary['correct_answers']}")
                                st.write(f"❌ त्रुटियाँ: {summary['incorrect_answers']}")
                                st.write(f"📚 कितना सीखा: {len(summary['words_learned'])}")
                                if summary['words_learned']:
                                    st.write(f"📝 नए शब्द: {', '.join(summary['words_learned'])}")
                                st.success("फिर मिलेंगे! 👋")
                                st.stop()
                    else:
                        st.error("❌ ओहो! यह भी नहीं...")
        
        # Add a button to go back to text input
        st.button("नया जवाब लिखें", on_click=lambda: setattr(st.session_state, 'show_hints', False))



    # Quit option - only show the main quit button
    if st.button("अब बस"):
        show_session_summary()
except Exception as e:
    logger.error(f"Application error: {str(e)}", exc_info=True)
    st.error("An error occurred. Please try again or contact support.")

