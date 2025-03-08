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
            
            # Initialize learning history
            self.learning_history = self._load_learning_history()
            
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
        
        # Log the prompt
        self.logger.debug(f"Agent base prompt: {base_prompt}")
        
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
        if isinstance(text, str) and "Final Answer:" in text:
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text
            )
        elif hasattr(text, 'content') and "Final Answer:" in text.content:
            return AgentFinish(
                return_values={"output": text.content.split("Final Answer:")[-1].strip()},
                log=text.content
            )
        
        # Try to parse action and input
        try:
            if isinstance(text, str) and "Action:" in text and "Action Input:" in text:
                action = text.split("Action:", 1)[1].split("\n")[0].strip()
                action_input = text.split("Action Input:", 1)[1].split("\n")[0].strip()
                
                return AgentAction(
                    tool=action,
                    tool_input=action_input,
                    log=text
                )
            elif hasattr(text, 'content') and "Action:" in text.content and "Action Input:" in text.content:
                action = text.content.split("Action:", 1)[1].split("\n")[0].strip()
                action_input = text.content.split("Action Input:", 1)[1].split("\n")[0].strip()
                
                return AgentAction(
                    tool=action,
                    tool_input=action_input,
                    log=text.content
                )
        except Exception as e:
            self.logger.warning(f"Failed to parse agent output: {e}")
        
        # Default to treating as final answer if parsing fails
        if isinstance(text, str):
            return AgentFinish(
                return_values={"output": text.strip()},
                log=text
            )
        elif hasattr(text, 'content'):
            return AgentFinish(
                return_values={"output": text.content.strip()},
                log=text.content
            )
        else:
            return AgentFinish(
                return_values={"output": str(text)},
                log=str(text)
            )

    def _select_next_word(self, input_data: str) -> Optional[str]:
        """Tool: Select next unlearned word from SQLite database."""
        try:
            # Get unlearned words from SQLite database
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
                "chat_history": self.memory.load_memory_variables({}).get("chat_history", []),
                "agent_scratchpad": ""
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
                feedback = result.get("output", "") if hasattr(result, 'get') else result.return_values.get("output", "") if hasattr(result.return_values, 'get') else ""
                
                # Update learning history
                if is_correct:
                    self.learning_history["correct"].append(word)
                    self.learning_history["total_correct"] += 1
                else:
                    self.learning_history["incorrect"].append(word)
                    self.learning_history["total_incorrect"] += 1
                
                self._save_learning_history()
                return {"is_correct": is_correct, "feedback": feedback}
                
            elif action == "get_hint":
                word = kwargs.get("word")
                
                # Generate hints using prompt
                prompt = self.prompt_manager.format_prompt(
                    "hint_generation",
                    num_hints=3,
                    word=word
                )
                base_input["input"] = prompt
                
                result = self.agent_executor.invoke(base_input)
                hints = result.get("output", []) if hasattr(result, 'get') else result.return_values.get("output", []) if hasattr(result.return_values, 'get') else []
                return {"hints": hints}
            elif action == "summarize_session":
                # Generate session summary
                base_input = {
                    "chat_history": self.memory.load_memory_variables({}).get("chat_history", []),
                }
                prompt = self.prompt_manager.format_prompt(
                    "session_summary",
                    correct_count=self.learning_history["total_correct"],
                    incorrect_count=self.learning_history["total_incorrect"],
                    learned_words=", ".join(self.learning_history["correct"])
                )
                base_input["input"] = prompt
                
                result = self.agent_executor.invoke(base_input)
                summary = result.get("output", "") if hasattr(result, 'get') else result.return_values.get("output", "") if hasattr(result.return_values, 'get') else ""
                
                # Update total words learned
                self.learning_history["total_words_learned"] = len(self.learning_history["correct"])
                self._save_learning_history()
                
                return {
                    "correct_answers": self.learning_history["total_correct"],
                    "incorrect_answers": self.learning_history["total_incorrect"],
                    "words_learned": self.learning_history["correct"],
                    "total_words_learned": self.learning_history["total_words_learned"],
                    "summary_message": summary
                }
            elif action == "get_next_word_prompt":
                # Generate prompt asking if the student wants to learn more
                prompt = self.prompt_manager.format_prompt(
                    "next_word_prompt",
                    learned_words=", ".join(self.learning_history["correct"])
                )
                base_input["input"] = prompt
                
                result = self.agent_executor.invoke(base_input)
                next_word_prompt = result.get("output", "") if hasattr(result, 'get') else result.return_values.get("output", "") if hasattr(result.return_values, 'get') else ""
                
                return {"next_word_prompt": next_word_prompt}
                
            else:
                self.logger.warning(f"Unknown action: {action}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error in process_student_interaction: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": str(e)}

    def _load_learning_history(self) -> Dict:
        """Load student's learning history."""
        history_file = f"data/learning_history_{self.student_id}.json"
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                return json.load(f)
        return {"correct": [], "incorrect": [], "total_correct": 0, "total_incorrect": 0, "total_words_learned": 0}

    def _save_learning_history(self):
        """Save student's learning history."""
        history_file = f"data/learning_history_{self.student_id}.json"
        # Ensure directory exists
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        
        # Update total words learned count
        self.learning_history["total_words_learned"] = len(self.learning_history["correct"])
        
        with open(history_file, 'w') as f:
            json.dump(self.learning_history, f)

    def get_new_word(self) -> Optional[str]:
        """Get a new word for the student to learn."""
        result = self.process_student_interaction("get_new_word")
        return result.get("word")

    def check_answer(self, answer: str, word: str) -> bool:
        """Check if the student's answer is correct."""
        result = self.process_student_interaction(
            "check_answer",
            answer=answer,
            word=word
        )
        is_correct = result.get("is_correct", False)
        
        # Save learning history to database
        if word and is_correct:
            try:
                # Mark the word as learned
                self.db.mark_word_as_learned(self.student_id, word)
                
                # Add a message to the conversation history asking if the student wants to learn more
                self.memory.save_context(
                    {"input": f"Great job! '{answer}' is correct. Would you like to learn another word? (yes/no)"},
                    {"output": "Okay, let me find a new word for you."}  # This output doesn't really matter
                )
                
            except Exception as e:
                self.logger.error(f"Error marking word as learned: {e}")
        
        return is_correct

    def get_hint(self, word: str) -> List[str]:
        """Get hints for the current word."""
        result = self.process_student_interaction(
            "get_hint",
            word=word
        )
        return result.get("hints", [])

    def summarize_session(self) -> Dict:
        """Get a summary of the current learning session."""
        return self.process_student_interaction("summarize_session")