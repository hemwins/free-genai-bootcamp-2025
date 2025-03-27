import sys
import os

from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.memory import BaseMemory
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnablePassthrough
import sqlite3
import chromadb
import json
import requests
import traceback
from typing import List, Dict, Optional, Union, Any
from .utils import load_hindi_words
from models.generative_model import GenerativeModel
from models.audio_model import AudioModel
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
            # self.embedding_model = FastTextEmbedding()  # Local FastText model
            self.generative_model = GenerativeModel()
            self.audio_model = AudioModel()
            
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
                func= self._select_next_word,
                description="Select an unlearned Hindi word from the database"
            ),
            Tool(
                name="answer_checker",
                func=self._use_answer_check_prompt,
                description="Check if the student's answer is correct. Input should be a dictionary with 'answer' and 'word' keys or will use values from current interaction."
            ),
            Tool(
                name="hint_generator",
                func=self._generate_hints,
                description="Generate a common phrase or sentence related to word and explain the cultural nuances or proper usage of the phrase or sentence using GPT-4o-mini"
            ),
            Tool(
                name="generate_pronunciation_hints",
                func=self._generate_pronunciation_hints_tool,
                description="Generate similar-sounding words and the correct audio for pronunciation practice"
            ),
            Tool(
                name="evaluate_pronunciation",
                func=self._evaluate_pronunciation_tool,
                description="Evaluate the student's pronunciation and provide feedback"
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
                "tools": lambda _: [tool.model_dump() for tool in self.tools],
                "tool_names": lambda _: ", ".join([tool.name for tool in self.tools])
            }
            | base_prompt
            | self.generative_model.llm.with_config({"temperature": 0.2, "tool_preference": True})
            | self._parse_agent_output
        )
        self.logger.debug(f"!!!!!!!Agent base prompt chain!!!!!!!: {agent_chain}")
        return agent_chain
    
    def _parse_agent_output(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Parse the agent's output text into an action or final answer."""
        # Check for final answer first
        if isinstance(text, str) and "Final Answer:" in text:
            self.logger.info(f"Final answer in IF detected: {text}")
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text
            )
        elif hasattr(text, 'content') and "Final Answer:" in text.content:
            self.logger.info(f"Final answer in ELSE detected: {text.content}")
            return AgentFinish(
                return_values={"output": text.content.split("Final Answer:")[-1].strip()},
                log=text.content
            )
            
        self.logger.info(f"text in parse agent output: {text}")
        
        # Try to parse action and input
        try:
            if isinstance(text, str):
                if "Action:" in text and "Action Input:" in text:
                    action = text.split("Action:", 1)[1].split("\n")[0].strip().rstrip('.')
                    action_input = text.split("Action Input:", 1)[1].strip()
                    self.logger.info(f"Tool selected: {action}")
                    # Ensure action_input is a dictionary
                    if action_input.lower() == "none":
                        action_input = {}
                    return AgentAction(tool=action, tool_input=action_input, log=text)
                else:
                    return AgentFinish(return_values={"output": text.strip()}, log=text)
            elif hasattr(text, 'content'):
                if "Action:" in text.content and "Action Input:" in text.content:
                    action = text.content.split("Action:", 1)[1].split("\n")[0].strip().rstrip('.')
                    action_input = text.content.split("Action Input:", 1)[1].strip()
                    self.logger.info(f"tool in ELSE: {action}")
                    self.logger.info(f"tool input in ELSE: {action_input}")
                    # Ensure action_input is a dictionary
                    if action_input.lower() == "none":
                        action_input = {}
                    return AgentAction(
                        tool=action,
                        tool_input=action_input,
                        log=text.content
                    )   
            else:
                return AgentFinish(return_values={"output": text.content.strip()}, log=text.content)
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

    def _use_answer_check_prompt(self, tool_input: Dict[str, str]) -> bool:
        """Check if student's answer matches the word using FastText embeddings."""
        try:
            self.logger.info(f"Answer checker received tool_input: {tool_input}")
        
            # Get answer and word from current_kwargs
            answer = self.current_kwargs.get('answer')
            word = self.current_kwargs.get('word')
            
            if not answer or not word:
                self.logger.error("Missing answer or word")
                return False
        
            # Use the answer_check prompt
            prompt = self.prompt_manager.get_prompt("answer_check")
            formatted_prompt = prompt.format(
                student_answer=answer,
                word=word
            )
            self.logger.info(f"Using answer_check prompt: {formatted_prompt}")
            self.logger.info(f"Checking answer: {answer} against word: {word}")
            if answer == word:
                self.logger.info(f"Exact match found with original word: {word}")
                return False
            synonym_words = self.db.find_synonyms(word)
            
            self.logger.info(f"Number of synonyms words retrieved: {len(synonym_words)}")  # Log the number of words

            
            if not synonym_words:
                self.logger.info("No synonym words found")
            else:
                is_match = False
                for synonym in synonym_words:
                    if answer == synonym:
                        self.logger.info(f"Exact match found with synonym: {synonym}")
                        is_match = True
                        break
                if is_match:
                    self.logger.info(f"Match found with synonym: {synonym}")
                    return True
                else:
                    self.logger.info(f"No match found with any synonym")
            return False
        
        except Exception as e:
            self.logger.error(f"Error in use_answer_check_prompt: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _select_next_word(self, _: Optional[str] = None) -> Optional[str]:
        """Tool: Select next unlearned word from SQLite database."""
        try:
            self.logger.info(f"Selecting next word for student: {self.student_id}")  #Log student ID

            # Get unlearned words from SQLite database
            unlearned_words = self.db.get_unlearned_words(self.student_id)
            self.logger.info(f"Number of unlearned words retrieved: {len(unlearned_words)}")  # Log the number of words

            if not unlearned_words:
                self.logger.info("No unlearned words found, checking if all words are learned")
                # Check total words in SQLite
                with sqlite3.connect(self.db.sqlite_path) as conn:
                    word_count = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]

                if word_count > 0:
                    self.logger.info(f"Student has learned all {word_count} available words")
                else:
                    self.logger.warning("No words found in database - please populate SQLite first")
                return "No words available"
            else:
                self.logger.info(f"Unlearned words: {unlearned_words}") # Log the list of words
            # Return the first unlearned word
            selected_word = unlearned_words[0]
            self.logger.info(f"Selected unlearned word: {selected_word} from SQLite database")
            return selected_word

        except Exception as e:
            self.logger.error(f"Error selecting next word from SQLite: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None


    def _generate_hints(self, word: str) -> Dict[str, Union[List[str], str]]:
        """Tool: Generate multiple-choice options and contextual hints using gpt-4o-mini."""
        hint = self.generative_model.generate_hints(word)
        
        return {
            "hint": hint
        }
    
    def _generate_pronunciation_hints_tool(self, word: str) -> Dict[str, Union[List[str], bytes]]:
        """Tool: Generate similar-sounding words and the correct audio."""
        return self._get_pronunciation_hints(word)

    def _evaluate_pronunciation_tool(self, spoken_text: str, word: str) -> Dict[str, Union[bool, str]]:
        """Tool: Evaluate the student's pronunciation and provide feedback."""
        return self._generate_pronunciation_feedback(word, spoken_text)

        
    def _generate_pronunciation_feedback(self, word: str, spoken_text: str) -> Dict[str, Union[bool, str]]:
        """
        Generates feedback on the student's pronunciation using GPT-4o-mini.
        """
        try:
            # Use GPT-4o-mini to compare the student's spoken text with the correct pronunciation of the word
            prompt = self.prompt_manager.format_prompt(
                "pronunciation_feedback",
                word=word,
                spoken_text=spoken_text
            )

            base_input = {
                "chat_history": self.memory.load_memory_variables({}).get("chat_history", []),
            }
            base_input["input"] = prompt

            result = self.agent_executor.invoke(base_input)
            feedback = result.get("output", "") if hasattr(result, 'get') else result.return_values.get("output", "") if hasattr(result.return_values, 'get') else ""
            # Check if the feedback indicates that the pronunciation is correct
            is_correct = "सही" in feedback or "अच्छा" in feedback or "उत्तम" in feedback  # Adjust keywords as needed

            #Logic to output correct pronuncation
            if not is_correct:
              #if pronunciation is not correct Generate Correct Pronunciation and include in feedback
              correct_audio = self.audio_model.generate_speech(word)
              if correct_audio:
                feedback = f"{feedback}। यहाँ सही उच्चारण है: " # include right pronunciation of the word

                #if again it is not correct. give encouraging word and correct pronounciation.
                prompt_repeat = self.prompt_manager.format_prompt(
                    "pronunciation_repeat",
                    word=word,
                    feedback=feedback
                )
                base_input["input"] = prompt_repeat

                repeat_result = self.agent_executor.invoke(base_input)
                feedback_repeat = repeat_result.get("output", "") if hasattr(repeat_result, 'get') else repeat_result.return_values.get("output", "") if hasattr(repeat_result.return_values, 'get') else ""

                feedback = feedback_repeat
              else:
                  self.logger.warning("could not generate correct audio")
            return {"is_correct": is_correct, "feedback": feedback}

        except Exception as e:
            self.logger.error(f"Error generating pronunciation feedback: {e}")
            return {"is_correct": False, "feedback": "उच्चारण जांच में त्रुटि।"} # "Error in pronunciation check."

    def _get_pronunciation_hints(self, word: str) -> Dict[str, Union[List[str], bytes]]:
        """Generates pronunciation hints including similar words and the correct audio."""
        try:
            # 1. Get similar-sounding words using GPT-4o-mini
            prompt = self.prompt_manager.format_prompt(
                "similar_sounding_words",  # New prompt in hindi_tutor_prompts.json
                word=word
            )
            base_input = {
                "chat_history": self.memory.load_memory_variables({}).get("chat_history", []),
            }
            base_input["input"] = prompt

            result = self.agent_executor.invoke(base_input)
            similar_words_str = result.get("output", "") if hasattr(result, 'get') else result.return_values.get("output", "") if hasattr(result.return_values, 'get') else ""
            similar_words = [w.strip() for w in similar_words_str.split(",") if w.strip()] # split by comma and strip any spaces


            # 2. Generate correct pronunciation audio using gTTS
            correct_audio = self.audio_model.generate_speech(word)

            if correct_audio:
                return {"similar_words": similar_words, "correct_audio": correct_audio}
            else:
                self.logger.warning("Could not generate correct audio.")
                return {"similar_words": similar_words, "correct_audio": None}

        except Exception as e:
            self.logger.error(f"Error generating pronunciation hints: {e}")
            return {"similar_words": [], "correct_audio": None}

    def process_student_interaction(self, input: str, **kwargs) -> Dict:
        """Process student interaction using the LangChain Expression Language (LCEL)."""
        try:
            self.logger.info(f"Entered process_student_interaction with input: {input}")
            self.logger.info(f"Entered process_student_interaction with kwargs: {kwargs}")
            self.logger.info(f"Available tools inside process student interaction: {[tool.name for tool in self.tools]}")
            self.current_kwargs = kwargs
            
            # Direct tool calls for deterministic operations
            # if input == "check_answer":
            #     answer = kwargs.get('answer')
            #     word = kwargs.get('word')
            
            #     if not answer or not word:
            #         self.logger.error("Missing answer or word for answer checking")
            #         return {"error": "Missing answer or word"}
                
            #     self.logger.info(f"Directly checking answer: {answer} against word: {word}")
            #     is_correct = self._use_answer_check_prompt({
            #         'answer': answer,
            #         'word': word
            #     })
            #     self.logger.info(f"Answer check result: {is_correct}")
            #     return {"is_correct": is_correct}
            
            # if input == "get_hint":
            #     word = kwargs.get('word')
            
            #     if not word:
            #         self.logger.error("Missing word for hint generation")
            #         return {"error": "Missing word"}
                
            #     self.logger.info(f"Directly generating hint against word: {word}")
            #     hint = self._generate_hints(word)
            #     self.logger.info(f"Hint generated: {hint}")
            #     return hint
            
            # Prepare base input with memory
            base_input = {
                "chat_history": self.memory.load_memory_variables({}).get("chat_history", []),
                "agent_scratchpad": "",
                "input": input,
                **kwargs # Include all kwargs in base_input
            }    
            self.logger.info(f"updated base_input with kwargs and new base_input is: {base_input}")
            
            try:
                result = self.agent_executor.invoke(base_input)
                self.logger.info(f"Result from agent executor: {result}")
            except Exception as e:
                self.logger.error(f"Error during agent_executor.invoke: {e}")
                self.logger.error(f"Traceback: {traceback.format_exc()}")
                return {"error": str(e)}
            
            self.logger.info(f"Type of result: {type(result)}")
            # Handle agent results and Extract output for app.py
            if isinstance(result, AgentFinish):
                return result.return_values
            elif isinstance(result, AgentAction):
                tool_name = result.tool
                tool_input = result.tool_input

                self.logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
                tool = next((t for t in self.tools if t.name == tool_name), None)

                if tool:
                    try:
                        # Ensure tool_input is a dictionary
                        if isinstance(tool_input, str):
                            if tool_input.lower().strip() == "none" or not tool_input.strip():
                                tool_input = None
                        tool_result = tool.func(tool_input)
                        self.logger.info(f"Tool '{tool_name}' executed successfully, result: {tool_result}")
                        return {"output": tool_result}
                    except Exception as e:
                        self.logger.error(f"Error executing tool {tool_name}: {e}")
                        return {"output": f"Error executing {tool_name}"}
                else:
                    self.logger.error(f"Tool '{tool_name}' not found in available tools.")
                    return {"output": f"Action failed: {tool_name} (tool not found)"}

            else:
                return {"output": "Unexpected response format"}

        except Exception as e:
            self.logger.error(f"Error in process_student_interaction: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": str(e)}

    def check_answer(self, answer: str, word: str) -> bool:
        """Check if the student's answer is correct."""
        self.logger.info(f"check_answer called with word: {word}, answer put before parsing: {answer}")
        result = self.process_student_interaction(
            "check_answer",
            answer=answer,
            word=word
        )
        is_correct = result.get("is_correct", False)
        
        # Save learning history to database and local file
        if word and is_correct:
            try:
                # Mark the word as learned
                self.db.mark_word_learned(self.student_id, word)
                self.learning_history["correct"].append(word)
                self.learning_history["total_correct"] += 1
                # Save to file
                self._save_learning_history()
                # Add a message to the conversation history asking if the student wants to learn more and clear existing word from session
                self.memory.chat_memory.add_user_message("Great job! Would you like to learn another word? (yes/no)")
                
            except Exception as e:
                self.logger.error(f"Error marking word as learned: {e}")
        else:
        # Update incorrect attempts
            self.learning_history["total_incorrect"] += 1
            self._save_learning_history()
        
        return is_correct

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
        self.logger.info(f"Result from process_student_interaction: {result}")  # Debugging
        new_word = result.get("output", None)

        #self.logger.info(f"New word extracted: {new_word}")
        return new_word

    def get_hint(self, word: str) -> Dict[str, str]:
        """Get hints for the current word."""
        try:
            result = self.process_student_interaction(
                "get_hint",
                word=word
            )
        
        # Structure the hint response
            hint_response = {
                "hint": result.get("hint", ""),
                "cultural_context": result.get("cultural_context", ""),
                "example": result.get("example", "")
            }
            return hint_response
        
        except Exception as e:
            self.logger.error(f"Error getting hint: {e}")
            return {"hint": "संकेत उपलब्ध नहीं है।"}

    def summarize_session(self) -> Dict:
        """Get a summary of the current learning session."""
        summary = {
            "words_learned": self.learning_history.get("correct", []),
            "correct_answers": self.learning_history.get("total_correct", 0),
            "incorrect_answers": self.learning_history.get("total_incorrect", 0)
        }
        self._save_learning_history()
        self.logger.info(f"Session summary: {summary}")
        return summary

if __name__ == "__main__":
    import sys

    def print_menu():
        print("\n=== Hindi Learning Agent Debug Menu ===")
        print("1. Fetch a new word")
        print("2. Check an answer")
        print("3. Generate hints for a word")
        print("4. Summarize session")
        print("5. Exit")
        print("=======================================")

    def main():
        student_id = f"student_{random.randint(1000, 9999)}"
        print(f"Initializing agent for student ID: {student_id}")
        agent = HindiLearningAgent(student_id)

        while True:
            print_menu()
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                print("\nFetching a new word...")
                new_word = agent.get_new_word()
                if new_word:
                    print(f"New word fetched: {new_word}")
                else:
                    print("No new word available or an error occurred.")

            elif choice == "2":
                word = input("\nEnter the word to check against: ").strip()
                answer = input("Enter the student's answer: ").strip()
                print("\nChecking the answer...")
                is_correct = agent.check_answer(answer, word)
                if is_correct:
                    print("Correct answer!")
                else:
                    print("Incorrect answer.")

            elif choice == "3":
                word = input("\nEnter the word to generate hints for: ").strip()
                print("\nGenerating hints...")
                hints = agent.get_hint(word)
                if hints:
                    print(f"Hints: {hints.get('hint', 'No hint available')}")
                    print(f"Cultural Context: {hints.get('cultural_context', 'No cultural context available')}")
                    print(f"Example: {hints.get('example', 'No example available')}")
                else:
                    print("No hints available or an error occurred.")

            elif choice == "4":
                print("\nSummarizing session...")
                summary = agent.summarize_session()
                print(f"Words Learned: {summary.get('words_learned', [])}")
                print(f"Correct Answers: {summary.get('correct_answers', 0)}")
                print(f"Incorrect Answers: {summary.get('incorrect_answers', 0)}")

            elif choice == "5":
                print("\nExiting...")
                sys.exit(0)

            else:
                print("\nInvalid choice. Please try again.")

    main()