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

# Check for required environment variables
if not config.TESTING and not os.getenv('HUGGINGFACE_TOKEN'):
    raise ValueError(
        "HuggingFace token not found. Please set the HUGGINGFACE_TOKEN environment variable."
    )

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

# Initialize session
init_session()
agent = st.session_state.agent

try:
    # Streamlit UI Setup
    st.set_page_config(page_title="Hindi Synonym Learning Agent", layout="centered")
    st.title("🇮🇳 Hindi Synonym Learning Game 📔")
    st.write("Learn Hindi synonyms interactively! Answer correctly to see flying balloons! 🎈")

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
                logger.info("No more words available")
                st.success("🎉 Congratulations! You have learned all words!")
                st.stop()
        except Exception as e:
            logger.error(f"Error fetching new word: {str(e)}\n{traceback.format_exc()}")
            st.error("Failed to fetch a new word. Please try again.")
            st.stop()

    st.subheader(f"🔹 What's a synonym for: **{st.session_state.current_word}**?")

    # User input
    user_answer = st.text_input("Your Answer:", key="user_answer")

    if st.button("Submit Answer"):
        if user_answer.strip():
            logger.debug(f"Checking answer: {user_answer} for word: {st.session_state.current_word}")
            is_correct = agent.check_answer(user_answer.strip(), st.session_state.current_word)

            if is_correct:
                logger.info(f"Correct answer given for word: {st.session_state.current_word}")
                st.success("✅ Correct! Well done!")
                st.balloons()
                st.session_state.new_word_needed = True
            else:
                logger.info(f"Incorrect answer: {user_answer} for word: {st.session_state.current_word}")
                st.error("❌ Incorrect! Here's a hint:")
                hint_options = agent.get_hint(st.session_state.current_word)
                st.write(f"👉 Choose from: {', '.join(hint_options)}")
        else:
            logger.warning("Empty answer submitted")
            st.warning("⚠️ Please enter an answer before submitting!")

    # Quit option
    if st.button("Quit Game"):
        logger.info(f"Session ended for student: {st.session_state.student_id}")
        summary = agent.summarize_session()
        st.subheader("📊 Session Summary")
        st.write(f"✅ Correct Answers: {summary['correct_answers']}")
        st.write(f"❌ Incorrect Attempts: {summary['incorrect_answers']}")
        st.write(f"📚 Total Words Learned: {len(summary['words_learned'])}")
        if summary['words_learned']:
            st.write(f"📝 Words Mastered: {', '.join(summary['words_learned'])}")
        st.success("Thank you and Bye! 👋")
        st.stop()
except Exception as e:
    logger.error(f"Application error: {str(e)}", exc_info=True)
    st.error("An error occurred. Please try again or contact support.")

