import streamlit as st
import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.question_generator import QuestionGenerator
from backend.audio_generator import AudioGenerator
from backend.get_transcript import YouTubeTranscriptDownloader
from backend.structured_data import TranscriptStructurer
from backend.vector_store import QuestionVectorStore

from backend.chat import BedrockChat
from collections import Counter
from typing import Dict

# Page config
st.set_page_config(
    page_title="JLPT Listening Practice",
    page_icon="🎧",
    layout="wide"
)
# Initialize session state
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

def render_header():
    """Render the header section"""
    st.title("🎌 Japanese Learning Assistant")
    st.markdown("""
    Transform YouTube transcripts into interactive Japanese learning experiences.
    
    This tool demonstrates:
    - Base LLM Capabilities
    - RAG (Retrieval Augmented Generation)
    - Amazon Bedrock Integration
    - Agent-based Learning Systems
    """)

def render_sidebar():
    """Render the sidebar with component selection"""
    with st.sidebar:
        st.header("Development Stages")
        
        # Main component selection
        selected_stage = st.radio(
            "Select Stage:",
            [
                "1. Chat with Nova",
                "2. Raw Transcript",
                "3. Structured Data",
                "4. RAG Implementation",
                "5. Interactive Learning"
            ]
        )
        
        # Stage descriptions
        stage_info = {
            "1. Chat with Nova": """
            **Current Focus:**
            - Basic Japanese learning
            - Understanding LLM capabilities
            - Identifying limitations
            """,
            
            "2. Raw Transcript": """
            **Current Focus:**
            - YouTube transcript download
            - Raw text visualization
            - Initial data examination
            """,
            
            "3. Structured Data": """
            **Current Focus:**
            - Text cleaning
            - Dialogue extraction
            - Data structuring
            """,
            
            "4. RAG Implementation": """
            **Current Focus:**
            - Bedrock embeddings
            - Vector storage
            - Context retrieval
            """,
            
            "5. Interactive Learning": """
            **Current Focus:**
            - Scenario generation
            - Audio synthesis
            - Interactive practice
            """
        }
        
        st.markdown("---")
        st.markdown(stage_info[selected_stage])
        
        return selected_stage
    
def render_chat_stage():
    """Render an improved chat interface"""
    st.header("Chat with Nova")

    # Initialize BedrockChat instance if not in session state
    if 'bedrock_chat' not in st.session_state:
        st.session_state.bedrock_chat = BedrockChat()

    # Introduction text
    st.markdown("""
    Start by exploring Nova's base Japanese language capabilities. Try asking questions about Japanese grammar, 
    vocabulary, or cultural aspects.
    """)

    # Initialize chat history if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

    # Chat input area
    if prompt := st.chat_input("Ask about Japanese language..."):
        # Process the user input
        process_message(prompt)

    # Example questions in sidebar
    with st.sidebar:
        st.markdown("### Try These Examples")
        example_questions = [
            "How do I say 'Where is the train station?' in Japanese?",
            "Explain the difference between は and が",
            "What's the polite form of 食べる?",
            "How do I count objects in Japanese?",
            "What's the difference between こんにちは and こんばんは?",
            "How do I ask for directions politely?"
        ]
        
        for q in example_questions:
            if st.button(q, use_container_width=True, type="secondary"):
                # Process the example question
                process_message(q)
                st.rerun()

    # Add a clear chat button
    if st.session_state.messages:
        if st.button("Clear Chat", type="primary"):
            st.session_state.messages = []
            st.rerun()

def process_message(message: str):
    """Process a message and generate a response"""
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": message})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(message)

    # Generate and display assistant's response
    with st.chat_message("assistant", avatar="🤖"):
        response = st.session_state.bedrock_chat.generate_response(message)
        if response:
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})



def count_characters(text):
    """Count Japanese and total characters in text"""
    if not text:
        return 0, 0
        
    def is_japanese(char):
        return any([
            '\u4e00' <= char <= '\u9fff',  # Kanji
            '\u3040' <= char <= '\u309f',  # Hiragana
            '\u30a0' <= char <= '\u30ff',  # Katakana
        ])
    
    jp_chars = sum(1 for char in text if is_japanese(char))
    return jp_chars, len(text)

def render_transcript_stage():
    """Render the raw transcript stage"""
    st.header("Raw Transcript Processing")
    
    # URL input
    url = st.text_input(
        "YouTube URL",
        placeholder="Enter a Japanese lesson YouTube URL"
    )
    
    # Download button and processing
    if url:
        if st.button("Download Transcript"):
            try:
                print(f"URL in MAIN : {url}")
                downloader = YouTubeTranscriptDownloader()
                transcript = downloader.get_transcript(url)
                if transcript:
                    # Store the raw transcript text in session state
                    transcript_text = "\n".join([entry['text'] for entry in transcript])
                    #print(f"TRANSCRIPT TEXT in MAIN: {transcript_text}")
                    st.session_state.transcript = transcript_text
                    #print("BEFORE TRANSCRIPT SAVED")
                    
                    
                    filename = downloader.extract_video_id(url) #HEMA
                    print(f"FILE NAME in MAIN : {filename}")
                    #filenameMade = f"./transcripts/{filename}.txt"
                    #print(f"FILE NAME MADE TEXT in MAIN: {filenameMade}")
                    
                    downloader.save_transcript(transcript, filename) #HEMA
                    #print("AFTER TRANSCRIPT SAVED")
                    
                    
                    st.success("Transcript downloaded successfully!")
                else:
                    print(f"TRANSCRIPT TEXT ERROR in MAIN: {transcript_text}")
                    st.error("No transcript found for this video.")
            except Exception as e:
                st.error(f"Error downloading transcript: {str(e)}")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Raw Transcript")
        if st.session_state.transcript:
            st.text_area(
                label="Raw text",
                value=st.session_state.transcript,
                height=400,
                disabled=True
            )
    
        else:
            st.info("No transcript loaded yet")
    
    with col2:
        st.subheader("Transcript Stats")
        if st.session_state.transcript:
            # Calculate stats
            jp_chars, total_chars = count_characters(st.session_state.transcript)
            total_lines = len(st.session_state.transcript.split('\n'))
            
            # Display stats
            st.metric("Total Characters", total_chars)
            st.metric("Japanese Characters", jp_chars)
            st.metric("Total Lines", total_lines)
        else:
            st.info("Load a transcript to see statistics")

def render_structured_stage():
    """Render the structured data stage"""
    st.header("Structured Data Processing")
    structurer = TranscriptStructurer()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Dialogue Extraction")
        
        # Only show dialogue extraction if transcript is loaded
        if 'transcript' in st.session_state and st.session_state.transcript:
            # Add extract button
            if st.button("Extract Dialogues"):
                try:
                    # Extract dialogues using section 2 prompt (dialogue-focused)
                    dialogue_result = structurer._invoke_bedrock(
                        structurer.prompts[2], 
                        st.session_state.transcript
                    )
                    
                    if dialogue_result:
                        # Store extracted dialogues in session state
                        st.session_state.dialogues = dialogue_result
                        st.success("Dialogues extracted successfully!")
                        print(f"Dialogues extracted successfully!: {dialogue_result}")
                        # Display extracted dialogues
                        dialogues = dialogue_result.split("<question>")
                        for dialogue in dialogues[1:]:  # Skip empty first split
                            with st.expander("Dialogue"):
                                st.text(dialogue.strip().replace("</question>", ""))
                    else:
                        st.error("Failed to extract dialogues")
                        
                except Exception as e:
                    st.error(f"Error extracting dialogues: {str(e)}")
        else:
            st.info("Please load a transcript first in the Raw Transcript stage")

    with col2:
        st.subheader("Structured Data View")
        
        # Only show structured view if dialogues are extracted
        if 'dialogues' in st.session_state and st.session_state.dialogues:
            try:
                # Parse dialogues into structured format
                dialogues = st.session_state.dialogues.split("<question>")
                structured_data = []
                
                for dialogue in dialogues[1:]:  # Skip empty first split
                    # Parse dialogue sections
                    sections = dialogue.strip().replace("</question>", "").split("\n\n")
                    dialogue_dict = {}
                    
                    for section in sections:
                        if section.startswith("Introduction:"):
                            dialogue_dict["Introduction"] = section.replace("Introduction:", "").strip()
                        elif section.startswith("Conversation:"):
                            dialogue_dict["Conversation"] = section.replace("Conversation:", "").strip()
                        elif section.startswith("Question:"):
                            dialogue_dict["Question"] = section.replace("Question:", "").strip()
                        elif section.startswith("Topic:"):
                            dialogue_dict["Topic"] = section.replace("Topic:", "").strip()
                        elif section.startswith("Options:"):
                            dialogue_dict["Options"] = section.replace("Options:", "").strip().split('<option-separator>')
                    #<option-separator>
                    
                    structured_data.append(dialogue_dict)
                
                # Display structured data
                for idx, data in enumerate(structured_data, 1):
                    with st.expander(f"Question {idx}"):
                        st.markdown("**Introduction**")
                        st.text(data.get("Introduction", "N/A"))
                        
                        st.markdown("**Conversation**")
                        st.text(data.get("Conversation", "N/A"))
                        
                        st.markdown("**Question**")
                        st.text(data.get("Question", "N/A"))
                        
                        print(f"Save Quesation {data}")
                        # Add save button for each dialogue
                        if st.button(f"Save Question {idx}", key=f"save_{idx}"):
                            save_question(
                                question=data,
                                practice_type="Dialogue Practice",
                                topic=data.get("Topic", "Other")  # Use default if topic not found
                            )
                            st.success(f"Question {idx} saved!")
                            
            except Exception as e:
                st.error(f"Error displaying structured data: {str(e)}")
        else:
            st.info("Extract dialogues first to view structured data")

def render_rag_stage():
    """Render the RAG implementation stage"""
    st.header("RAG Implementation")
    
    # Initialize vector store if not in session state
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = QuestionVectorStore()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Retrieved Context")
        
        # Search parameters
        search_section = st.selectbox(
            "Select Section",
            options=[2, 3],
            format_func=lambda x: f"Section {x}"
        )
        
        query = st.text_input(
            "Search Query",
            placeholder="Enter search terms for similar questions"
        )
        
        n_results = st.slider(
            "Number of Results",
            min_value=1,
            max_value=5,
            value=2
        )
        
        if st.button("Search Similar Questions"):
            try:
                # Search for similar questions
                similar_questions = st.session_state.vector_store.search_similar_questions(
                    section_num=search_section,
                    query=query,
                    n_results=n_results
                )
                
                if similar_questions:
                    st.session_state.retrieved_questions = similar_questions
                    
                    # Display retrieved questions
                    for idx, question in enumerate(similar_questions, 1):
                        with st.expander(f"Retrieved Question {idx} (Score: {question['similarity_score']:.3f})"):
                            if search_section == 2:
                                st.markdown("**Introduction**")
                                st.text(question.get('Introduction', 'N/A'))
                                st.markdown("**Conversation**")
                                st.text(question.get('Conversation', 'N/A'))
                            else:  # section 3
                                st.markdown("**Situation**")
                                st.text(question.get('Situation', 'N/A'))
                            
                            st.markdown("**Question**")
                            st.text(question.get('Question', 'N/A'))
                            
                            if 'Options' in question:
                                st.markdown("**Options**")
                                for i, opt in enumerate(question['Options'], 1):
                                    st.text(f"{i}. {opt}")
                else:
                    st.warning("No similar questions found")
                    
            except Exception as e:
                st.error(f"Error searching questions: {str(e)}")
    
    with col2:
        st.subheader("Generated Response")
        
        if 'retrieved_questions' in st.session_state:
            generation_type = st.radio(
                "Generation Type",
                ["Similar Question", "Answer Explanation"]
            )
            
            if st.button("Generate"):
                try:
                    if generation_type == "Similar Question":
                        # Initialize question generator
                        generator = QuestionGenerator()
                        
                        # Generate similar question
                        new_question = generator.generate_similar_question(
                            section_num=search_section,
                            topic=query  # Use query as topic for generation
                        )
                        
                        if new_question:
                            with st.expander("Generated Question", expanded=True):
                                if search_section == 2:
                                    st.markdown("**Introduction**")
                                    st.text(new_question.get('Introduction', 'N/A'))
                                    st.markdown("**Conversation**")
                                    st.text(new_question.get('Conversation', 'N/A'))
                                else:  # section 3
                                    st.markdown("**Situation**")
                                    st.text(new_question.get('Situation', 'N/A'))
                                
                                st.markdown("**Question**")
                                st.text(new_question.get('Question', 'N/A'))
                                
                                if 'Options' in new_question:
                                    st.markdown("**Options**")
                                    for i, opt in enumerate(new_question['Options'], 1):
                                        st.text(f"{i}. {opt}")
                                
                                # Save button
                                if st.button("Save Generated Question"):
                                    save_question(
                                        question=new_question,
                                        practice_type=f"section{search_section}",
                                        topic=query
                                    )
                                    st.success("Question saved successfully!")
                        else:
                            st.error("Failed to generate similar question")
                            
                    else:  # Answer Explanation
                        # Use the first retrieved question for explanation
                        question = st.session_state.retrieved_questions[0]
                        
                        # Generate explanation using Bedrock
                        chat = BedrockChat()
                        prompt = f"""
                        Explain the correct approach to answer this JLPT listening question:
                        
                        {json.dumps(question, ensure_ascii=False, indent=2)}
                        
                        Provide a step-by-step explanation in English.
                        """
                        
                        explanation = chat.get_response(prompt)
                        
                        if explanation:
                            st.markdown("### Answer Explanation")
                            st.markdown(explanation)
                        else:
                            st.error("Failed to generate explanation")
                            
                except Exception as e:
                    st.error(f"Error in generation: {str(e)}")
        else:
            st.info("Search for similar questions first to enable generation")

def render_interactive_stage():
    """Render the interactive learning stage"""
    # Initialize session state
    if 'question_generator' not in st.session_state:
        st.session_state.question_generator = QuestionGenerator()
    if 'audio_generator' not in st.session_state:
        st.session_state.audio_generator = AudioGenerator()
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'feedback' not in st.session_state:
        st.session_state.feedback = None
    if 'current_practice_type' not in st.session_state:
        st.session_state.current_practice_type = None
    if 'current_topic' not in st.session_state:
        st.session_state.current_topic = None
    if 'current_audio' not in st.session_state:
        st.session_state.current_audio = None
        
    # Load stored questions for sidebar
    stored_questions = load_stored_questions()
    
    # Create sidebar
    with st.sidebar:
        st.header("Saved Questions")
        if stored_questions:
            for qid, qdata in stored_questions.items():
                # Create a button for each question
                button_label = f"{qdata['practice_type']} - {qdata['topic']}\n{qdata['created_at']}"
                if st.button(button_label, key=qid):
                    st.session_state.current_question = qdata['question']
                    st.session_state.current_practice_type = qdata['practice_type']
                    st.session_state.current_topic = qdata['topic']
                    st.session_state.current_audio = qdata.get('audio_file')
                    st.session_state.feedback = None
                    st.rerun()
        else:
            st.info("No saved questions yet. Generate some questions to see them here!")
    
    # Practice type selection - now using session state
    practice_types = ["Dialogue Practice", "Phrase Matching"]
    default_index = practice_types.index(st.session_state.current_practice_type) if st.session_state.current_practice_type in practice_types else 0
    
    practice_type = st.selectbox(
        "Select Practice Type",
        practice_types,
        index=default_index
    )
    
    # Topic selection
    topics = {
        "Dialogue Practice": ["Daily Conversation", "Shopping", "Restaurant", "Travel", "School/Work"],
        "Phrase Matching": ["Announcements", "Instructions", "Weather Reports", "News Updates"]
    }
    
    # Set default topic based on current_topic if it exists
    available_topics = topics[practice_type]
    default_topic_index = available_topics.index(st.session_state.current_topic) if st.session_state.current_topic in available_topics else 0
    
    topic = st.selectbox(
        "Select Topic",
        available_topics,
        index=default_topic_index
    )

    # Generate new question button
    if st.button("Generate New Question"):
        section_num = 2 if practice_type == "Dialogue Practice" else 3
        new_question = st.session_state.question_generator.generate_similar_question(
            section_num, topic
        )
        st.session_state.current_question = new_question
        st.session_state.current_practice_type = practice_type
        st.session_state.current_topic = topic
        st.session_state.feedback = None
        
        # Save the generated question
        save_question(new_question, practice_type, topic)
        st.session_state.current_audio = None
    
    if st.session_state.current_question:
        st.subheader("Practice Scenario")
        
        # Display question components
        if practice_type == "Dialogue Practice":
            st.write("**Introduction:**")
            st.write(st.session_state.current_question['Introduction'])
            st.write("**Conversation:**")
            st.write(st.session_state.current_question['Conversation'])
        else:
            st.write("**Situation:**")
            st.write(st.session_state.current_question['Situation'])
        
        st.write("**Question:**")
        st.write(st.session_state.current_question['Question'])
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display options
            options = st.session_state.current_question['Options']
            
            # If we have feedback, show which answers were correct/incorrect
            if st.session_state.feedback:
                correct = st.session_state.feedback.get('correct', False)
                print(st.session_state.feedback.get('correct_answer'))
                correct_answer = int(st.session_state.feedback.get('correct_answer', 1)) - 1
                selected_index = st.session_state.selected_answer - 1 if hasattr(st.session_state, 'selected_answer') else -1
                
                st.write("\n**Your Answer:**")
                for i, option in enumerate(options):
                    if i == correct_answer and i == selected_index:
                        st.success(f"{i+1}. {option} ✓ (Correct!)")
                    elif i == correct_answer:
                        st.success(f"{i+1}. {option} ✓ (This was the correct answer)")
                    elif i == selected_index:
                        st.error(f"{i+1}. {option} ✗ (Your answer)")
                    else:
                        st.write(f"{i+1}. {option}")
                
                # Show explanation
                st.write("\n**Explanation:**")
                explanation = st.session_state.feedback.get('explanation', 'No feedback available')
                if correct:
                    st.success(explanation)
                else:
                    st.error(explanation)
                
                # Add button to try new question
                if st.button("Try Another Question"):
                    st.session_state.feedback = None
                    st.rerun()
            else:
                # Display options as radio buttons when no feedback yet
                selected = st.radio(
                    "Choose your answer:",
                    options,
                    index=None,
                    format_func=lambda x: f"{options.index(x) + 1}. {x}"
                )
                
                # Submit answer button
                if selected and st.button("Submit Answer"):
                    selected_index = options.index(selected) + 1
                    st.session_state.selected_answer = selected_index
                    st.session_state.feedback = st.session_state.question_generator.get_feedback(
                        st.session_state.current_question,
                        selected_index
                    )
                    st.rerun()
        
        with col2:
            st.subheader("Audio")
            if st.session_state.current_audio:
                # Display audio player
                st.audio(st.session_state.current_audio)
            elif st.session_state.current_question:
                # Show generate audio button
                if st.button("Generate Audio"):
                    with st.spinner("Generating audio..."):
                        try:
                            # Clear any previous audio
                            if st.session_state.current_audio and os.path.exists(st.session_state.current_audio):
                                try:
                                    os.unlink(st.session_state.current_audio)
                                except Exception:
                                    pass
                            st.session_state.current_audio = None
                            
                            # Generate new audio
                            audio_file = st.session_state.audio_generator.generate_audio(
                                st.session_state.current_question
                            )
                            
                            # Verify the audio file exists
                            if not os.path.exists(audio_file):
                                raise Exception("Audio file was not created")
                                
                            st.session_state.current_audio = audio_file
                            
                            # Update stored question with audio file
                            save_question(
                                st.session_state.current_question,
                                st.session_state.current_practice_type,
                                st.session_state.current_topic,
                                audio_file
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error generating audio: {str(e)}")
                            # Clear the audio state on error
                            st.session_state.current_audio = None
            else:
                st.info("Generate a question to create audio.")
    else:
        st.info("Click 'Generate New Question' to start practicing!")
        
def load_stored_questions():
    """Load previously stored questions from JSON file"""
    questions_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend/data/stored_questions.json"
    )
    if os.path.exists(questions_file):
        with open(questions_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_question(question, practice_type, topic, audio_file=None):
    """Save a generated question to JSON file"""
    questions_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend/data/stored_questions.json"
    )
    
    # Load existing questions
    stored_questions = load_stored_questions()
    
    # Create a unique ID for the question using timestamp
    question_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if "Options" in question:
        question["Options"] = [opt.strip() for opt in question["Options"]]
    # Add metadata
    question_data = {
        "question": question,
        "practice_type": practice_type,
        "topic": topic,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "audio_file": audio_file
    }
    
    # Add to stored questions
    stored_questions[question_id] = question_data
    
    # Save back to file
    os.makedirs(os.path.dirname(questions_file), exist_ok=True)
    with open(questions_file, 'w', encoding='utf-8') as f:
        json.dump(stored_questions, f, ensure_ascii=False, indent=2)
    
    return question_id


def main():
    render_header()
    selected_stage = render_sidebar()
    
    # Render appropriate stage
    if selected_stage == "1. Chat with Nova":
        render_chat_stage()
    elif selected_stage == "2. Raw Transcript":
        render_transcript_stage()
    elif selected_stage == "3. Structured Data":
        render_structured_stage()
    elif selected_stage == "4. RAG Implementation":
        render_rag_stage()
    elif selected_stage == "5. Interactive Learning":
        render_interactive_stage()
    
    # Debug section at the bottom
    with st.expander("Debug Information"):
        st.json({
            "selected_stage": selected_stage,
            "transcript_loaded": st.session_state.transcript is not None,
            "chat_messages": len(st.session_state.messages)
        })

if __name__ == "__main__":
    main()

