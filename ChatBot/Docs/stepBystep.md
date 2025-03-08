Step-by-Step Working:
Initial Setup (When application starts)
# app.py initializes the agent
    agent = HindiLearningAgent(student_id)

    ## HindiLearningAgent initialization sequence:
        1. Loads prompts from hindi_tutor_prompts.json via PromptManager
        2. Initializes FastText embedding model
        3. Initializes gpt generative model
        4. Sets up LangChain tools and agent chain
# Learning Session Flow
## 1. Get New Word
app.py -> agent.process_student_interaction("get_new_word")
  -> _select_next_word() 
    -> embedding_model.get_unlearned_words()
      -> ChromaDB query

## 2. Student Answers
app.py -> agent.process_student_interaction("check_answer", answer=user_input, word=current_word)
  -> _check_answer_similarity()
    -> embedding_model.find_closest_match()
      -> FastText similarity check
  -> generative_model.generate_celebration() or generate_error_feedback()
    -> gpt generates response

## 3. Get Hints (if needed)
app.py -> agent.process_student_interaction("get_hint", word=current_word)
  -> _generate_hints()
    -> generative_model.generate_hints()
      -> gpt generates hints

## 4. Session Summary
app.py -> agent.process_student_interaction("summarize_session")
  -> generative_model.generate_session_summary()
    -> gpt generates summary

## Word Selection Flow:
app.py
  -> agent.process_student_interaction("get_new_word")
    -> agent._select_next_word()
      -> embedding_model.get_unlearned_words()
        -> chromadb.query()
## Answer Checking Flow:
app.py
  -> agent.process_student_interaction("check_answer")
    -> agent._check_answer_similarity()
      -> embedding_model.find_closest_match()
        -> FastText.get_embeddings()
        -> chromadb.query()
## Response Generation Flow:
app.py
  -> agent.process_student_interaction()
    -> generative_model.generate_response()
      -> prompt_manager.get_prompt()
      -> gpt.generate()

File-by-File Breakdown:
### app.py
Entry point of application
Manages Streamlit UI
Initializes agent
Handles user interactions
### agent/agent.py
Core orchestrator
Manages tools and decision making
Coordinates between FastText and gpt
Handles learning history
### prompts/prompt_manager.py
Loads prompts from JSON
Provides prompt templates
Manages prompt formatting
### models/embedding_model.py
Handles FastText embeddings
Manages ChromaDB interactions
Performs similarity matching
### models/generative_model.py
Manages gpt model
Generates natural language responses
Handles different types of generations
### prompts/hindi_tutor_prompts.json
Stores prompt templates
Defines input variables
Maintains consistent prompting

### Key Points About the Two-Database Approach:
## SQLite (Regular Data):
* Student information
* Word metadata
* Learning history
* Basic synonym relationships
* Analytics and reporting data
## ChromaDB (Vector Data):
* Word and synonym embeddings
* Vector similarity search
* Fast nearest neighbor lookups

### a sequence diagram to visualize this flow: mermaid
sequenceDiagram
    participant U as User/Streamlit UI
    participant A as app.py
    participant AG as agent.py
    participant PM as prompt_manager.py
    participant EM as embedding_model.py
    participant GM as generative_model.py
    participant DB as ChromaDB

    Note over U,DB: Initialization Phase
    A->>AG: Create HindiLearningAgent(student_id)
    AG->>PM: Initialize PromptManager
    PM-->>AG: Load prompts
    AG->>EM: Initialize FastText
    AG->>GM: Initialize gpt
    AG->>AG: Setup LangChain tools

    Note over U,DB: Learning Session
    U->>A: Start session
    A->>AG: process_student_interaction("get_new_word")
    AG->>EM: get_unlearned_words()
    EM->>DB: Query unlearned words
    DB-->>EM: Return words
    EM-->>AG: Return next word
    AG-->>A: Return word
    A-->>U: Display word

    Note over U,DB: Answer Processing
    U->>A: Submit answer
    A->>AG: process_student_interaction("check_answer")
    AG->>EM: find_closest_match(answer, word)
    EM->>DB: Query synonyms
    DB-->>EM: Return matches
    EM-->>AG: Return match result
    
    alt Correct Answer
        AG->>GM: generate_celebration()
        GM-->>AG: Return celebration
    else Incorrect Answer
        AG->>GM: generate_error_feedback()
        GM->>PM: Get error prompt
        PM-->>GM: Return prompt
        GM-->>AG: Return feedback
        AG->>GM: generate_hints()
        GM-->>AG: Return hints
    end
    
    AG-->>A: Return response
    A-->>U: Display feedback/hints

    Note over U,DB: Session End
    U->>A: End session
    A->>AG: process_student_interaction("summarize_session")
    AG->>GM: generate_session_summary()
    GM->>PM: Get summary prompt
    PM-->>GM: Return prompt
    GM-->>AG: Return summary
    AG-->>A: Return session stats
    A-->>U: Display summary

### Get Embedding Request
   ↓
   Check Cache → Found? → Return Cached
   ↓ (not found)
   Check Exact DB Match → Found? → Return & Cache
   ↓ (not found)
   Try API with Rate Limiting → Success? → Return & Cache
   ↓ (API fails)
   Try Similar Words in DB → Found? → Return Similar
   ↓ (not found)
   Use Average of Cached → Have Cache? → Return Average
   ↓ (no cache)
   Return Zero Vector (last resort)

### Log format:
Debug/Error logs: timestamp - name - level - [file:line] - message
API logs: timestamp - level - message
Console: LEVEL: message

### comprehensive test suite with three main test modules:
### test_agent.py: Tests the main Hindi Learning Agent
Initialization
Answer checking
Hint generation
New word retrieval
Session summary
Error handling
### test_embedding_model.py: Tests the embedding functionality
Word embedding generation
Cache management
Rate limiting
Fallback mechanisms
Similarity matching
### test_db_manager.py: Tests database operations
Database initialization
Word addition
Synonym management
Learning history
Unlearned words retrieval
Error handling

### To run the tests:
### Run all tests:
python -m unittest discover ChatBot/tests
### Run specific test module:
python -m unittest ChatBot/tests/test_agent.py
python -m unittest ChatBot/tests/test_embedding_model.py
python -m unittest ChatBot/tests/test_db_manager.py
### Run specific test case:
python -m unittest ChatBot/tests/test_agent.py -k test_check_answer
