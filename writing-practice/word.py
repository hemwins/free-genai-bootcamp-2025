import logging
import requests
import random
import tempfile
from PIL import Image
import os
from manga_ocr import MangaOcr
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logger = logging.getLogger('word_practice')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('word_practice.log')
fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)

class WordPracticeApp:
    def __init__(self):
        self.mocr = None
        self.current_word = None

    def get_random_word(self):
        """Get a random word from vocabulary"""
        logger.debug("Getting random word")
        
        if not self.vocabulary or not self.vocabulary.get('words'):
            logger.error("No vocabulary available")
            return "", "", "", "No vocabulary loaded. Please check your configuration."
            
        self.current_word = random.choice(self.vocabulary['words'])
        
        return (
            self.current_word.get('kanji', ''),
            self.current_word.get('reading', ''),
            self.current_word.get('english', ''),
            "Write the kanji character shown above"
        )

    def grade_submission(self, image):
        """Process image submission and grade it"""
        try:
            # Initialize MangaOCR for transcription if not already initialized
            if self.mocr is None:
                logger.info("Initializing MangaOCR")
                self.mocr = MangaOcr()
            
            # Image is already a filepath when using type="filepath"
            img = Image.open(image)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                img.save(temp_file.name)
                temp_path = temp_file.name
            
            # Transcribe the image
            logger.info("Transcribing image with MangaOCR")
            transcription = self.mocr(temp_path)
            logger.debug(f"Transcription result: {transcription}")
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            # Compare transcription with target word
            is_correct = transcription.strip() == self.current_word.get('japanese', '').strip()
            result = "✓ Correct!" if is_correct else "✗ Incorrect"
            
            logger.debug(f"Current word: {self.current_word}")
            logger.debug(f"Transcription: {transcription}, Target: {self.current_word.get('japanese', '')}, Is correct: {is_correct}")
            
            # Submit result to backend
            self.submit_result(is_correct)
            
            logger.info(f"Grading complete: {result}")
            
            return transcription, result
            
        except Exception as e:
            logger.error(f"Error in grade_submission: {str(e)}")
            return "Error processing submission", "Error: " + str(e)

    def submit_result(self, is_correct):
        """Submit the result to the backend"""
        try:
            if not self.current_word:
                return
            session_id = self.session_id or -1
            # session_id = qp.get("session_id", -1)
            if not session_id:
                logger.warning("No session ID found, skipping result submission")
                return
            logger.info(f"Submitting result: is_correct={is_correct} and session id={session_id}")
            url = f"http://localhost:4999/api/study-sessions/{session_id}/review"
            data = {
                "word_id": self.current_word.get('id'),
                "correct": is_correct
            }
            
            response = requests.post(url, json=data)
            if response.status_code == 200:
                logger.info("Successfully submitted review")
            else:
                logger.error(f"Failed to submit review. Status code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error submitting result: {str(e)}")
