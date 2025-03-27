import os
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from prompts.prompt_manager import HindiTutorPromptManager

class GenerativeModel:
    def __init__(self):
        # Initialize prompt manager
        self.prompt_manager = HindiTutorPromptManager()
        
        # Initialize LangChain chat model
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.7,
            max_tokens=100
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=500
        )
        
        # self.chain = LLMChain(
        #     llm=self.llm,
        #     # prompt=self.prompt,
        #     memory=self.memory  # Ensures memory is used
        # )
    
    def _create_chain(self, prompt_template: str, output_key: str = "text") -> LLMChain:
        """Create a LangChain chain with the given prompt template."""
        chat_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are a helpful Hindi language tutor."),
            HumanMessagePromptTemplate.from_template(prompt_template)
        ])
        
        # Create chain using the | operator
        chain = chat_prompt | self.llm
        
        # Integrate memory into the chain by wrapping the LLMChain with memory
        if self.memory:
            chain = LLMChain(
                prompt=chat_prompt,
                llm=self.llm,
                memory=self.memory
            )
        return chain

    def _use_answer_check_prompt(self, tool_input: Dict[str, str]) -> bool:
        """Use LLM with the 'answer_check' prompt before checking answer similarity."""
        answer = tool_input.get("answer", "")
        word = tool_input.get("word", "")

        if not answer or not word:
            self.logger.error("Missing answer or word in tool_input")
            return False

        # Get the formatted prompt
        prompt = self.prompt_manager.format_prompt(
            "answer_check",
            student_answer=answer,
            word=word
        )

        # Prepare input for LLM
        base_input = {
            "chat_history": self.memory.load_memory_variables({}).get("chat_history", []),
            "input": prompt
        }

        # Invoke LLM to analyze the answer
        result = self.agent_executor.invoke(base_input)
        self.logger.info(f"LLM response from 'answer_check' prompt: {result}")

        # Call FastText similarity check
        return self._check_answer_similarity(answer, word)

    def generate_hints(self, word: str) -> Dict[str, str]:
        """Generate a contextual hint using LangChain.
        Args:
        word (str): The Hindi word to generate hints for
        
        Returns:
        Dict[str, str]: Dictionary containing hint, cultural context, and example
        """
        prompt_template = self.prompt_manager.get_prompt("hint_generation").template
        chain = self._create_chain(prompt_template, output_key="hint")
    
        try:
            response = chain.invoke({"word": word})
            content = response.content if hasattr(response, 'content') else str(response)
        
            # Parse the response into sections
            sections = content.split('\n\n')
            hint_response = {
                "hint": "",
                "cultural_context": "",
                "example": ""
            }
        
            for section in sections:
                section = section.strip()
                if section:
                    # First non-empty section is the hint
                    if not hint_response["hint"]:
                        hint_response["hint"] = section
                    # Second non-empty section is cultural context
                    elif not hint_response["cultural_context"]:
                        hint_response["cultural_context"] = section
                    # Third non-empty section is the example
                    elif not hint_response["example"]:
                        hint_response["example"] = section
        
            return hint_response
        
        except Exception as e:
            self.logger.error(f"Error generating hints: {e}")
            return {
                "hint": "एक समान अर्थ वाले शब्द के बारे में सोचें...",  # Think about words with similar meaning...
                "cultural_context": "",
                "example": ""
            }
    
    def generate_celebration(self, word: str, correct_answer: str) -> str:
        """Generate a celebration message using LangChain."""
        prompt_template = "The student correctly answered that '{correct_answer}' is a synonym for '{word}'."
        chain = self._create_chain(prompt_template, output_key="celebration")
        
        response = chain.invoke({"word": word, "correct_answer": correct_answer})
        return response.content if hasattr(response, 'content') else str(response)
    
    def generate_session_summary(self, stats: Dict) -> str:
        """Generate an encouraging session summary using LangChain."""
        prompt_template = self.prompt_manager.get_prompt("session_summary").template
        chain = self._create_chain(prompt_template, output_key="summary")
        
        response = chain.invoke({
            "correct_count": stats["correct_answers"],
            "incorrect_count": stats["incorrect_answers"],
            "learned_words": ", ".join(stats["words_learned"])
        })
        return response.content if hasattr(response, 'content') else str(response)
    
    def generate_error_feedback(self, word: str, student_answer: str, correct_synonyms: List[str]) -> str:
        """Generate constructive feedback using LangChain."""
        prompt_template = self.prompt_manager.get_prompt("answer_feedback").template
        chain = self._create_chain(prompt_template, output_key="feedback")
        
        response = chain.invoke({
            "word": word,
            "student_answer": student_answer,
            "correctness": "incorrect"
        })
        return response.content if hasattr(response, 'content') else str(response)
    
    def generate_response(self, prompt_name: str, **kwargs) -> str:
        """Generate a response using LangChain and a specific prompt template."""
        prompt_template = self.prompt_manager.get_prompt(prompt_name).template
        chain = self._create_chain(prompt_template, output_key="response")
        
        response = chain.invoke(kwargs)
        return response.content if hasattr(response, 'content') else str(response)
    
    def reset_memory(self):
        """Clears conversation memory when it exceeds a limit."""
        print("Resetting memory...")
        self.memory.clear()
    
    def get_next_word_prompt(self, learned_words: List[str]) -> str:
        """Generate a prompt for selecting the next word using LangChain."""
        prompt_template = self.prompt_manager.get_prompt("next_word_prompt").template
        chain = self._create_chain(prompt_template, output_key="next_word")
        
        response = chain.invoke({"learned_words": ", ".join(learned_words)})
        return response.content if hasattr(response, 'content') else str(response)
