import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chains.llm import LLMChain
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
            max_tokens=150
        )
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    
    def _create_chain(self, prompt_template: str, output_key: str = "text") -> LLMChain:
        """Create a LangChain chain with the given prompt template."""
        chat_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are a helpful Hindi language tutor."),
            HumanMessagePromptTemplate.from_template(prompt_template)
        ])
        
        # Create chain using the | operator
        chain = chat_prompt | self.llm
        # Add memory if needed
        if self.memory:
            chain = chain.with_memory(self.memory)
        return chain

    def generate_hints(self, word: str) -> str:
        """Generate a contextual hint using LangChain."""
        prompt_template = self.prompt_manager.get_prompt("hint_generation").template
        chain = self._create_chain(prompt_template, output_key="hint")
        
        response = chain.invoke({"word": word})
        if isinstance(response, str):
            # Return the first non-empty line as the hint
            for line in response.split('\n'):
                if line.strip():
                    return line.strip()
        elif hasattr(response, 'content'):
            # Handle new LangChain message format
            for line in response.content.split('\n'):
                if line.strip():
                    return line.strip()
        return "Think about words with similar meaning..."  # Fallback hint
    
    def generate_celebration(self, word: str, correct_answer: str) -> str:
        """Generate a celebration message using LangChain."""
        prompt_template = "The student correctly answered that '{correct_answer}' is a synonym for '{word}'. Generate a short, encouraging celebration message in Hindi and English."
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
        prompt_template = "The student answered '{student_answer}' for the Hindi word '{word}', but this was incorrect. The correct synonyms are: {correct_synonyms}. Generate a helpful and encouraging feedback message that explains why the answer was incorrect and provides a hint for the correct answer."
        chain = self._create_chain(prompt_template, output_key="feedback")
        
        response = chain.invoke({
            "word": word,
            "student_answer": student_answer,
            "correct_synonyms": ", ".join(correct_synonyms)
        })
        return response.content if hasattr(response, 'content') else str(response)
    
    def generate_response(self, prompt_name: str, **kwargs) -> str:
        """Generate a response using LangChain and a specific prompt template."""
        prompt_template = self.prompt_manager.get_prompt(prompt_name).template
        chain = self._create_chain(prompt_template, output_key="response")
        
        response = chain.invoke(kwargs)
        return response.content if hasattr(response, 'content') else str(response)
    
    def get_next_word_prompt(self, learned_words: List[str]) -> str:
        """Generate a prompt for selecting the next word using LangChain."""
        prompt_template = "The student has already learned these Hindi words: {learned_words}. Suggest a new word that would be appropriate for their next lesson."
        chain = self._create_chain(prompt_template, output_key="next_word")
        
        response = chain.invoke({"learned_words": ", ".join(learned_words)})
        return response.content if hasattr(response, 'content') else str(response)

def generate_response(prompt: str) -> str:
    """Utility function for quick response generation using LangChain."""
    model = GenerativeModel()
    chain = model._create_chain("{prompt}", output_key="response")
    return chain.run(prompt=prompt)
