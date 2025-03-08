from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.memory import BaseMemory
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnablePassthrough
import sqlite3
import chromadb
import json
import os
import requests
import traceback
from typing import List, Dict, Optional, Union, Any
from .utils import load_hindi_words
from models.embedding_model import FastTextEmbedding
from models.generative_model import GenerativeModel
from prompts.prompt_manager import HindiTutorPromptManager
from database.db_manager import DatabaseManager
from utils.config import config
from utils.logger import get_logger
import time

class HindiLearningAgent:
    def __init__(self, student_id: str):
        self.student_id = student_id
        self.logger = get_logger(__name__)
        self.logger.info(f"Initializing HindiLearningAgent for student: {student_id}")
        
        try:
            # Initialize core components
            self.db = DatabaseManager()
            self.prompt_manager = HindiTutorPromptManager()
            self.embedding_model = FastTextEmbedding()  # Local FastText model
            self.generative_model = GenerativeModel()
            
            # Initialize memory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                input_key="input",
                return_messages=True,
                output_key="output"
            )
            
            # Initialize agent components
            self.tools = self._initialize_tools()
            self.agent_executor = self._setup_agent_executor()
            
            self.logger.info("HindiLearningAgent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def _initialize_tools(self) -> List[Tool]:
        return [
            Tool(
                name="word_selector",
                func=self._select_next_word,
                description="Select an unlearned Hindi word from the database using FastText embeddings"
            ),
            Tool(
                name="answer_checker",
                func=self._check_answer_similarity,
                description="Check if the student's answer is correct using FastText embeddings"
            ),
            Tool(
                name="hint_generator",
                func=self._generate_hints,
                description="Generate a list of 4 words from vector database, one of which is correct answer, along with contextual hints using GPT-4o-mini"
            )
        ]

    def _setup_agent_executor(self) -> RunnablePassthrough:
        """Setup the agent executor using the new LangChain Expression Language (LCEL)."""
        # Get base prompt from prompt manager
        base_prompt = self.prompt_manager.get_prompt("agent_base_prompt")
        
        # Define the agent's chain of operations
        agent_chain = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: self.memory.load_memory_variables(x)["chat_history"],
                "tools": lambda _: [tool.dict() for tool in self.tools]
            }
            | base_prompt
            | self.generative_model.llm
            | self._parse_agent_output
        )
        
        return agent_chain
    
    def _parse_agent_output(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Parse the agent's output text into an action or final answer."""
        # Check for final answer first
        if "Final Answer:" in text:
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text
            )
        
        # Try to parse action and input
        try:
            if "Action:" in text and "Action Input:" in text:
                action = text.split("Action:", 1)[1].split("\n")[0].strip()
                action_input = text.split("Action Input:", 1)[1].split("\n")[0].strip()
                
                return AgentAction(
                    tool=action,
                    tool_input=action_input,
                    log=text
                )
        except Exception as e:
            self.logger.warning(f"Failed to parse agent output: {e}")
        
        # Default to treating as final answer if parsing fails
        return AgentFinish(
            return_values={"output": text.strip()},
            log=text
        )

    def _select_next_word(self, input_data: str) -> Optional[str]:
        """Tool: Select next unlearned word from SQLite database.
        
        The learning status (unlearned/learned) is tracked in SQLite using the learning_history table.
        ChromaDB is populated from SQLite and only used for word embeddings and similarity search.
        """
        try:
            # Get unlearned words from SQLite database using learning_history
            unlearned_words = self.db.get_unlearned_words(self.student_id)
            
            # If no unlearned words, check if student has learned everything
            if not unlearned_words:
                self.logger.info("No unlearned words found, checking if all words are learned")
                
                # Check total words in SQLite
                with sqlite3.connect(self.db.sqlite_path) as conn:
                    word_count = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
                
                if word_count > 0:
                    self.logger.info(f"Student has learned all {word_count} available words")
                else:
                    self.logger.warning("No words found in database - please populate SQLite first")
                return None
            
            # Return the first unlearned word
            selected_word = unlearned_words[0]['hindi_word']
            self.logger.info(f"Selected unlearned word: {selected_word} from SQLite database")
            return selected_word
            
        except Exception as e:
            self.logger.error(f"Error selecting next word from SQLite: {e}")
            return None

    def _check_answer_similarity(self, answer: str, word: str) -> bool:
        """Tool: Check answer using FastText similarity."""
        is_match, similarity = self.embedding_model.find_closest_match(answer, word)
        return is_match

    def _generate_hints(self, word: str) -> Dict[str, Union[List[str], str]]:
        """Tool: Generate multiple-choice options and contextual hints using gpt-4o-mini."""
        # Get 3 similar words from vector store
        similar_words = self.embedding_model.get_similar_words(word, k=3)
        
        # Create multiple choice options with the correct word and similar words
        options = similar_words + [word]
        
        # Generate contextual hint using GPT-4o-mini
        hint = self.generative_model.generate_hints(word)
        
        return {
            "options": options,
            "hint": hint
        }

    def process_student_interaction(self, action: str, **kwargs) -> Dict:
        """Process student interaction using the LangChain Expression Language (LCEL)."""
        try:
            # Prepare base input with memory
            base_input = {
                "chat_history": self.memory.load_memory_variables({}).get("chat_history", [])
            }
            
            if action == "get_new_word":
                result = self._select_next_word("")
                return {"word": result}
                
            elif action == "check_answer":
                answer = kwargs.get("answer")
                word = kwargs.get("word")
                
                # Check answer using FastText similarity
                is_correct = self._check_answer_similarity(answer, word)
                
                # Get feedback using prompt
                prompt = self.prompt_manager.format_prompt(
                    "answer_feedback",
                    answer=answer,
                    word=word,
                    correctness="correct" if is_correct else "incorrect"
                )
                base_input["input"] = prompt
                
                result = self.agent_executor.invoke(base_input)
                feedback = result.get("output", "")
                
                # Save learning history to database
                if word:
                    try:
                        # Get the word_id from database
                        with sqlite3.connect(self.db.sqlite_path) as conn:
                            conn.row_factory = sqlite3.Row
                            word_record = conn.execute(
                                "SELECT word_id FROM words WHERE hindi_word = ?", 
                                (word,)
                            ).fetchone()
                            
                            if word_record:
                                # Save the learning interaction
                                self.db.save_learning_history(
                                    student_id=self.student_id,
                                    word_id=word_record['word_id'],
                                    answer=answer,
                                    is_correct=is_correct,
                                    session_id=str(uuid.uuid4())
                                )
                    except Exception as e:
                        self.logger.error(f"Error saving learning history: {e}")
                
                return {"is_correct": is_correct, "feedback": feedback}
                
            elif action == "get_hint":
                word = kwargs.get("word")
                return self._generate_hints(word)
            
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            self.logger.error(f"Error processing student interaction: {e}")
            return {"error": str(e)}
    
    def get_new_word(self) -> Optional[str]:
        """Get a new word for the student to learn."""
        result = self.process_student_interaction("get_new_word")
        return result.get("word")
    
    def check_answer(self, answer: str, word: str) -> bool:
        """Check if the student's answer is correct."""
        return self._check_answer_similarity(answer, word)
    
    def get_hint(self, word: str) -> Dict[str, Union[List[str], str]]:
        """Get a hint for the current word."""
        return self._generate_hints(word)
    
    def summarize_session(self) -> Dict[str, Any]:
        """Summarize the student's learning session."""
        try:
            with sqlite3.connect(self.db.sqlite_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get correct and incorrect answers
                stats = conn.execute("""
                    SELECT 
                        SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers,
                        SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as incorrect_answers
                    FROM learning_history
                    WHERE student_id = ?
                """, (self.student_id,)).fetchone()
                
                # Get learned words
                learned_words = conn.execute("""
                    SELECT DISTINCT w.hindi_word
                    FROM words w
                    JOIN learning_history h ON w.word_id = h.word_id
                    WHERE h.student_id = ? AND h.is_correct = 1
                    ORDER BY h.created_at DESC
                """, (self.student_id,)).fetchall()
                
                return {
                    "correct_answers": stats["correct_answers"] or 0,
                    "incorrect_answers": stats["incorrect_answers"] or 0,
                    "words_learned": [row["hindi_word"] for row in learned_words]
                }
        except Exception as e:
            self.logger.error(f"Error generating session summary: {e}", exc_info=True)
            return {
                "correct_answers": 0,
                "incorrect_answers": 0,
                "words_learned": []
            }
