import gradio as gr
import requests
import json
import random
import logging
from openai import OpenAI
import os
import dotenv
import yaml
from word import WordPracticeApp  # Add this import

dotenv.load_dotenv()

def load_prompts():
    """Load prompts from YAML file"""
    with open('prompts.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Setup logging
logger = logging.getLogger('japanese_app')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('app.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

class JapaneseWritingApp:
    def __init__(self):
        self.client = OpenAI()
        self.vocabulary = None
        self.current_word = None
        self.current_sentence = None
        self.mocr = None
        self.load_vocabulary()
        # Initialize word practice with shared vocabulary
        self.word_practice = WordPracticeApp(self.vocabulary)

    def load_vocabulary(self):
        """Load vocabulary from API"""
        logger.debug("Loading vocabulary from API")
        """Fetch vocabulary from API using group_id"""
        try:
            # Get group_id from environment variable or use default
            group_id = 1
            url = f"http://localhost:4999/api/groups/{group_id}/words/raw"
            logger.debug(f"Fetching vocabulary from: {url}")
            
            response = requests.get(url)
            if response.status_code == 200:
                self.vocabulary = response.json()
                logger.info(f"Loaded {len(self.vocabulary.get('words', []))} words")
            else:
                logger.error(f"Failed to load vocabulary. Status code: {response.status_code}")
                self.vocabulary = {"words": []}
        except Exception as e:
            logger.error(f"Error loading vocabulary: {str(e)}")
            self.vocabulary = {"words": []}

    def generate_sentence(self, word):
        """Generate a sentence using OpenAI API"""
        logger.debug(f"Generating sentence for word: {word.get('kanji', '')}")
        
        try:
            prompts = load_prompts()
            messages = [
                {"role": "system", "content": prompts['sentence_generation']['system']},
                {"role": "user", "content": prompts['sentence_generation']['user'].format(word=word.get('kanji', ''))}
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=100
            )
            sentence = response.choices[0].message.content.strip()
            logger.info(f"Generated sentence: {sentence}")
            return sentence
        except Exception as e:
            logger.error(f"Error generating sentence: {str(e)}")
            return f"Error generating sentence. Please try again.{str(e)}"

    def get_random_word_and_sentence(self):
        """Get a random word and generate a sentence"""
        logger.debug("Getting random word and generating sentence")
        
        if not self.vocabulary or not self.vocabulary.get('words'):
            return "No vocabulary loaded", "", "", "Please make sure vocabulary is loaded properly."
            
        self.current_word = random.choice(self.vocabulary['words'])
        self.current_sentence = self.generate_sentence(self.current_word)
        
        return (
            self.current_sentence,
            f"English: {self.current_word.get('english', '')}",
            f"Kanji: {self.current_word.get('kanji', '')}",
            f"Reading: {self.current_word.get('reading', '')}"
        )

    def grade_submission(self, image):
        """Process image submission and grade it using MangaOCR and LLM"""
        try:
            # Initialize MangaOCR for transcription
            if self.mocr is None:
                from manga_ocr import MangaOcr
                self.mocr = MangaOcr()
            
            # Transcribe the image
            transcription = self.mocr(image)
            
            # Load prompts
            prompts = load_prompts()
            
            # Get literal translation
            logger.info("Getting literal translation")
            translation_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompts['translation']['system']},
                    {"role": "user", "content": prompts['translation']['user'].format(text=transcription)}
                ],
                temperature=0.3
            )
            translation = translation_response.choices[0].message.content.strip()
            logger.debug(f"Translation: {translation}")
            
            # Get grading and feedback
            logger.info("Getting grade and feedback")
            grading_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompts['grading']['system']},
                    {"role": "user", "content": prompts['grading']['user'].format(
                        target_sentence=self.current_sentence,
                        submission=transcription,
                        translation=translation
                    )}
                ],
                temperature=0.3
            )
            
            feedback = grading_response.choices[0].message.content.strip()
            # Parse grade and feedback from response
            grade = 'C'  # Default grade
            if 'Grade: S' in feedback:
                grade = 'S'
            elif 'Grade: A' in feedback:
                grade = 'A'
            elif 'Grade: B' in feedback:
                grade = 'B'
            
            # Extract just the feedback part
            feedback = feedback.split('Feedback:')[-1].strip()
            
            logger.info(f"Grading complete: {grade}")
            logger.debug(f"Feedback: {feedback}")
            
            return transcription, translation, grade, feedback
            
        except Exception as e:
            logger.error(f"Error in grade_submission: {str(e)}")
            return "Error processing submission", "Error processing submission", "C", f"An error occurred: {str(e)}"

def create_ui():
    # Initialize app with query parameters
    app = JapaneseWritingApp()
    word_app = app.word_practice
    custom_css = """
    .large-text-output textarea {
        font-size: 40px !important;
        line-height: 1.5 !important;
        font-family: 'Noto Sans JP', sans-serif !important;
    }
    """
    
    with gr.Blocks(title="Japanese Writing Practice", css=custom_css) as interface:
        gr.Markdown("# Japanese Writing Practice")
        
        # Add practice mode selection
        with gr.Row():
            practice_mode = gr.Radio(
                choices=["Sentence Practice", "Word Practice"],
                value="Sentence Practice",
                label="Select Practice Mode"
            )
        
        # Sentence Practice UI
        with gr.Column() as sentence_container:
            with gr.Row():
                with gr.Column():
                    generate_sentence_btn = gr.Button("Generate New Sentence", variant="primary")
                    sentence_output = gr.Textbox(
                        label="Generated Sentence",
                        lines=3,
                        scale=2,
                        show_label=True,
                        container=True,
                        elem_classes=["large-text-output"]
                    )
                    sentence_word_info = gr.Markdown("### Word Information")
                    sentence_english = gr.Textbox(label="English", interactive=False)
                    sentence_kanji = gr.Textbox(label="Kanji", interactive=False)
                    sentence_reading = gr.Textbox(label="Reading", interactive=False)
                
                with gr.Column():
                    sentence_image = gr.Image(label="Upload your handwritten sentence", type="filepath")
                    sentence_submit = gr.Button("Submit", variant="secondary")
                    
                    with gr.Group():
                        gr.Markdown("### Feedback")
                        sentence_transcription = gr.Textbox(
                            label="Transcription",
                            lines=3,
                            scale=2,
                            show_label=True,
                            container=True,
                            elem_classes=["large-text-output"]
                        )
                        sentence_translation = gr.Textbox(label="Translation", lines=2)
                        sentence_grade = gr.Textbox(label="Grade")
                        sentence_feedback = gr.Textbox(label="Feedback", lines=3)

        # Word Practice UI
        with gr.Column(visible=False) as word_container:
            with gr.Row():
                with gr.Column():
                    generate_word_btn = gr.Button("Get New Word", variant="primary")
                    kanji_output = gr.Textbox(
                        label="Kanji",
                        lines=2,
                        scale=2,
                        show_label=True,
                        container=True,
                        elem_classes=["large-text-output"],
                        interactive=False
                    )
                    word_info = gr.Markdown("### Word Information")
                    reading_output = gr.Textbox(label="Reading", interactive=False)
                    english_output = gr.Textbox(label="English", interactive=False)
                    instruction_output = gr.Textbox(label="Instructions", interactive=False)
                
                with gr.Column():
                    word_image = gr.Image(label="Upload your handwritten word", type="filepath")
                    word_submit = gr.Button("Submit", variant="secondary")
                    
                    with gr.Group():
                        gr.Markdown("### Results")
                        word_transcription = gr.Textbox(
                            label="Your Writing",
                            lines=1,
                            scale=2,
                            show_label=True,
                            container=True,
                            elem_classes=["large-text-output"]
                        )
                        word_grade = gr.Textbox(label="Result")

        # Event handlers
        def switch_mode(choice):
            if choice == "Sentence Practice":
                return gr.update(visible=True), gr.update(visible=False)
            else:
                return gr.update(visible=False), gr.update(visible=True)
        
        practice_mode.change(
            fn=switch_mode,
            inputs=[practice_mode],
            outputs=[sentence_container, word_container]
        )
        
        # Sentence practice handlers
        generate_sentence_btn.click(
            fn=app.get_random_word_and_sentence,
            outputs=[sentence_output, sentence_english, sentence_kanji, sentence_reading]
        )
        
        sentence_submit.click(
            fn=app.grade_submission,
            inputs=[sentence_image],
            outputs=[sentence_transcription, sentence_translation, sentence_grade, sentence_feedback]
        )
        
        # Word practice handlers
        generate_word_btn.click(
            fn=word_app.get_random_word,
            outputs=[kanji_output, reading_output, english_output, instruction_output]
        )
        
        def handle_word_submission(image):
            return word_app.grade_submission(image, 20)
        
        word_submit.click(
            fn=handle_word_submission,
            inputs=[word_image],
            outputs=[word_transcription, word_grade]
        )

    return interface

if __name__ == "__main__":
    interface = create_ui()
    interface.launch(server_name="0.0.0.0", server_port=8081)
