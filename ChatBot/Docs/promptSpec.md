# Project Specification: AI Agent for Learning Hindi Synonyms
## Project Overview
We are building an AI-powered learning agent that helps students learn Hindi synonyms in an interactive and gamified manner. The agent will act as a personal tutor, tracking the student's progress and selecting appropriate words dynamically based on their learning history.
## Functional Requirements
### AI Agent Core Features
* The agent will choose a Hindi word from a database and ask the student for a synonym.
* It will check correctness of the student's answer.
* If the answer is correct, the game screen will show flying balloons animation, and a new word will be selected.
* If the answer is incorrect, the agent will generate hints (multiple choice options), including the correct answer along with interrelated words.
* The agent will always select words that the student has not mastered yet.
* The student can choose to quit at any time.
*At the end of the session, the agent will provide a summary of learning progress, including:
* * Total correct answers
* * Total incorrect answers
* * List of words the student learned.
* * The agent will update the student’s learning history and store it for future sessions.
### Learning History & Progress Tracking
* The agent maintains a personalized learning history for each student.
* Every session will use only unanswered or incorrectly answered words from past sessions.
* The agent will not repeat words the student has already answered correctly.
#### The agent will store:
* Correct answers (so the same word is not repeated in future sessions).
* Incorrect answers (so these words are asked again in later sessions).
* Total session count & performance metrics.
### User Interaction & Game Experience
* Interactive Streamlit UI where students engage with the chatbot.
* Animations (flying balloons) on correct answers.
* Multiple-choice hints for incorrect answers.
* Session Summary after quitting, including a "Thank You & Bye" message.
##T ech Stack & Implementation Details
### Core AI Logic
Component and Tool/Framework
* AI Agent Framework -> LangChain
* Language Model -> Hugging Face Transformer Model (e.g., BERT)
* Vector Database -> ChromaDB (for storing student history)
* Memory Management -> LangChain Memory using dictionary datastructure
* Tool Use & Decision Making	LangChain’s Agent with Tools
### Backend & Data Storage
Component and Tool/Framework
* Database for words & synonyms -> SQLite 
* User Learning History Storage -> ChromaDB 
* API Calls for Language Processing -> Hugging Face Inference API
* Session Tracking -> Local JSON / Database
### Frontend & User Interaction
Component and Tool/Framework
* UI Framework -> Streamlit
* Animations (Balloons) -> Streamlit + Lottie Animations
* User Input Handling -> Streamlit Forms & Buttons
## How the Agent Works (Step-by-Step Flow)
### Session Start
* Student opens the Streamlit web app.
* The agent loads the student's learning history (if available).
* The agent selects a word (that the student has not yet learned) and asks for a synonym.
### User Answer Handling
#### If correct:
* Flying balloons animation is triggered.
* The word is marked as "learned" in the student's history.
* A new word (not previously learned) is chosen.
#### If incorrect:
* The agent provides multiple-choice hints with related but different words, including the correct answer.
* Student selects an answer from the choices.
* If wrong again, the correct answer is revealed.
* The word remains in the "to be learned" list for future sessions.
### Session End
#### Student can quit at any time.
#### Before exiting, the agent:
* Says "Thank you and Bye".
* Shows a summary of the learning session (correct vs. incorrect answers, words learned).
* Updates the student’s learning history.
## API Endpoints (If Needed)
Endpoint and Purpose
* /get-word	Fetch a new word for the student
* /check-answer	Validate student’s response
* /get-hints	Provide hint words for incorrect answers
* /update-history	Update student's learning history
## Implementation Breakdown (Modules & Functions)
### Word Selection Module
* get_next_word(user_id): Fetches the next word that the student has not mastered.
### Answer Checking Module
* check_answer(user_id, word, answer): Verifies the correctness of the student's answer.
### Hint Generation Module
* generate_hints(correct_word): Provides related words with only one correct answer.
### Learning History Management
* update_learning_history(user_id, word, result): Updates the student's history.
* fetch_learning_history(user_id): Retrieves the student’s progress for personalized learning.
## Summary
This project will implement an AI-powered learning agent that:
* Engages students in learning Hindi synonyms.
* Tracks learning history for personalized sessions.
* Provides real-time feedback and hints for incorrect answers.
* Gamifies learning with animations and progress tracking.
* Uses LangChain, Hugging Face, and Streamlit to build an autonomous AI agent.

## When is FastText Used? (Embeddings & Retrieval)
FastText is used for embedding Hindi words into a vector database (ChromaDB) and retrieving relevant synonyms.

### Workflow:

Every word and its synonyms are converted into embeddings (numeric vectors) using FastText.
When the student answers, the agent retrieves the most similar words from ChromaDB to check correctness.
Why FastText? It understands Hindi-specific nuances better than general models.
* Example:

* * Word: "सुंदर" (Beautiful)
* * FastText Embedding: Converts "सुंदर" and its synonyms into vectors.
* * Retrieval: If the student enters "खूबसूरत", FastText helps match it correctly.
## When is gpt-4o-mini Used? (Response Generation & Hints)
gpt is used for generating natural responses and giving hints dynamically.

### Workflow:

If the student answers correctly, gpt celebrates and moves to the next word.
If the answer is wrong, gpt generates multiple hint words, where only one is correct.
If the student quits, gpt summarizes the learning session in a conversational manner.
* Example:

* * Student's wrong answer for "बड़ा" → gpt generates:
* * "Here are three possible synonyms: विशाल, छोटा, संकुचित. Choose wisely!"
* * Session Summary:
"Great job! You got 5 correct answers and 2 incorrect. Keep practicing!"
## How These Two Models Work Together
Before Asking the Question → FastText finds unlearned words from ChromaDB.
After Student's Answer →
Correct: The word is marked as "learned" and FastText fetches a new word.
Wrong: gpt generates hints with related words.
At the End → gpt summarizes the session and gives feedback.
## Final Outcome
* * FastText ensures fast & accurate synonym matching.
* * gpt makes the chatbot engaging & interactive.
* * ChromaDB keeps track of student learning history.



