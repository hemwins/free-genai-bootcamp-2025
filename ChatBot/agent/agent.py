from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.agents import AgentAction, AgentFinish
from langchain.agents import LLMSingleActionAgent
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
import chromadb
import json
import os
import requests
import traceback
from typing import List, Dict, Optional, Union
from .utils import load_hindi_words
from models.embedding_model import FastTextEmbedding
from models.generative_model import GenerativeModel
from prompts.prompt_manager import HindiTutorPromptManager
from database.db_manager import DatabaseManager
from utils.config import config
from utils.logger import get_logger
import time
from langchain.agents import AgentOutputParser

class HindiLearningAgent:
    def __init__(self, student_id: str):
        self.student_id = student_id
        self.logger = get_logger(__name__)
        self.logger.info(f"Initializing HindiLearningAgent for student: {student_id}")
        
        try:
            self.db = DatabaseManager()
            # Initialize prompt manager
            self.prompt_manager = HindiTutorPromptManager()
            
            # Initialize LangChain components first
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                input_key="input",
                return_messages=True)

            # Initialize models
            self.embedding_model = FastTextEmbedding()  # Local FastText model
            self.generative_model = GenerativeModel()  
            
            self.learning_history = self._load_learning_history()
            self.tools = self._initialize_tools()
            self.agent_chain = self._setup_agent_chain()
            
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
                description="Generate contextual hints using gpt4o-mini"
            )
        ]

    def _setup_agent_chain(self) -> AgentExecutor:
        # Get the base prompt from prompt manager
        agent_prompt = self.prompt_manager.get_prompt("agent_base_prompt")
        
        # Create an LLMChain for the agent chain
        llm_chain = LLMChain(
            llm=self.generative_model.llm,
            prompt=agent_prompt
        )
        
        # Initialize empty agent_scratchpad
        self.agent_scratchpad = ""
        
        # Custom output parser for the agent
        class HindiTutorOutputParser(AgentOutputParser):
            def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
                if "Final Answer:" in text:
                    return AgentFinish(
                        return_values={"output": text.split("Final Answer:")[-1].strip()},
                        log=text
                    )
                
                # Check if text contains required action parts
                if "Action:" not in text or "Action Input:" not in text:
                    # If missing required parts, treat as final answer
                    return AgentFinish(
                        return_values={"output": text.strip()},
                        log=text
                    )
                
                try:
                    action_match = text.split("Action:", 1)[1].split("\n")[0].strip()
                    action_input_match = text.split("Action Input:", 1)[1].split("\n")[0].strip()
                    
                    return AgentAction(
                        tool=action_match,
                        tool_input=action_input_match,
                        log=text
                    )
                except (IndexError, ValueError):
                    # If parsing fails, treat as final answer
                    return AgentFinish(
                        return_values={"output": text.strip()},
                        log=text
                    )
        
        agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=HindiTutorOutputParser(),
            tools=self.tools,
            max_iterations=3,
            stop=["Final Answer:"]
        )
        
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )

    def _select_next_word(self, input_data: str) -> Optional[str]:
        """Tool: Select next unlearned word using FastText embeddings."""
        learned_words = self.learning_history["correct"]
        unlearned_words = self.embedding_model.get_unlearned_words(learned_words)
        return unlearned_words[0] if unlearned_words else None

    def _check_answer_similarity(self, answer: str, word: str) -> bool:
        """Tool: Check answer using FastText similarity."""
        is_match, similarity = self.embedding_model.find_closest_match(answer, word)
        return is_match

    def _generate_hints(self, word: str) -> List[str]:
        """Tool: Generate hints using gpt-4o-mini."""
        word_data = self.embedding_model.collection.get(
            where={"type": "main_word", "documents": word}
        )
        correct_synonym = word_data["metadatas"][0]["synonyms"][0]
        return self.generative_model.generate_hints(word, correct_synonym)

    def process_student_interaction(self, action: str, **kwargs) -> Dict:
        """Process student interaction using the LangChain agent."""
        if action == "get_new_word":
            result = self._select_next_word("")
            return {"word": result}
            
        elif action == "check_answer":
            answer = kwargs.get("answer")
            word = kwargs.get("word")
            # Use the answer feedback prompt
            prompt = self.prompt_manager.format_prompt(
                "answer_feedback",
                answer=answer,
                word=word,
                correctness="correct" if self._check_answer_similarity(answer, word) else "incorrect"
            )
            # Reset agent_scratchpad for new interaction
            self.agent_scratchpad = ""
            
            result = self.agent_chain.invoke({
                "input": prompt,
                "agent_scratchpad": self.agent_scratchpad
            })
            
            # Update agent_scratchpad with the result
            if isinstance(result.get("output"), str):
                self.agent_scratchpad = result["output"]
            is_correct = "correct" in result["output"].lower()
            
            if is_correct:
                self.learning_history["correct"].append(word)
                self.learning_history["total_correct"] += 1
            else:
                self.learning_history["incorrect"].append(word)
                self.learning_history["total_incorrect"] += 1
            
            self._save_learning_history()
            return {"is_correct": is_correct, "feedback": result["output"]}
            
        elif action == "get_hint":
            word = kwargs.get("word")
            # Use the hint generation prompt
            prompt = self.prompt_manager.format_prompt(
                "hint_generation",
                num_hints=3,
                word=word
            )
            # Reset agent_scratchpad for new interaction
            self.agent_scratchpad = ""
            
            result = self.agent_chain.invoke({
                "input": prompt,
                "agent_scratchpad": self.agent_scratchpad
            })
            
            # Update agent_scratchpad with the result
            if isinstance(result.get("output"), str):
                self.agent_scratchpad = result["output"]
            return {"hints": result["output"]}
            
        elif action == "summarize_session":
            # Use the session summary prompt
            prompt = self.prompt_manager.format_prompt(
                "session_summary",
                correct_count=self.learning_history["total_correct"],
                incorrect_count=self.learning_history["total_incorrect"],
                learned_words=", ".join(self.learning_history["correct"])
            )
            # Reset agent_scratchpad for new interaction
            self.agent_scratchpad = ""
            
            result = self.agent_chain.invoke({
                "input": prompt,
                "agent_scratchpad": self.agent_scratchpad
            })
            
            # Update agent_scratchpad with the result
            if isinstance(result.get("output"), str):
                self.agent_scratchpad = result["output"]
            # Update total words learned before returning summary
            self.learning_history["total_words_learned"] = len(self.learning_history["correct"])
            self._save_learning_history()
            
            return {
                "correct_answers": self.learning_history["total_correct"],
                "incorrect_answers": self.learning_history["total_incorrect"],
                "words_learned": self.learning_history["correct"],
                "total_words_learned": self.learning_history["total_words_learned"],
                "summary_message": result["output"]
            }

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
        return result.get("is_correct", False)

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
