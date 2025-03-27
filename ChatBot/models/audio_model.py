import io
from gtts import gTTS
from typing import Optional
from utils.logger import get_logger

class AudioModel:
    def __init__(self):
        self.logger = get_logger(__name__)

    def generate_speech(self, text: str, lang: str = 'hi') -> Optional[bytes]:
        """Generates speech from the given text and returns it as bytes."""
        try:
            tts = gTTS(text=text, lang=lang)
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)  # Important: Reset the pointer to the beginning
            return mp3_fp.read()
        except Exception as e:
            self.logger.error(f"Error generating speech: {e}")
            return None
