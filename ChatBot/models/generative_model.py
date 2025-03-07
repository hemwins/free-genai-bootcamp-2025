import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import List, Dict, Optional
from prompts.prompt_manager import HindiTutorPromptManager

# Load API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class GenerativeModel:
    def __init__(self):
        # Initialize prompt manager
        self.prompt_manager = HindiTutorPromptManager()
        
        # Use OpenAI GPT-3.5-Turbo model
        self.model_name = "gpt-4o-mini"
        self.llm = ChatOpenAI(model_name=self.model_name, openai_api_key=OPENAI_API_KEY)
        
    def generate_hints(self, word: str, correct_synonym: str, num_hints: int = 2) -> List[str]:
        """Generate contextual hints using GPT-3.5-Turbo."""
        chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt_manager.get_prompt("hint_generation")
        )
        
        response = chain.run(num_hints=num_hints, word=word)
        hints = [hint.strip() for hint in response.split('\n') if hint.strip()]
        hints = hints[:num_hints]  # Limit to requested number of hints
        
        if correct_synonym not in hints:
            hints[-1] = correct_synonym
        
        return hints
    
    def generate_celebration(self, word: str, correct_answer: str) -> str:
        """Generate a celebration message for correct answers."""
        celebration_prompt = PromptTemplate(
            template="The student correctly answered that '{correct_answer}' is a synonym for '{word}'. Generate a short, encouraging celebration message in Hindi and English.",
            input_variables=["word", "correct_answer"]
        )
        
        chain = LLMChain(llm=self.llm, prompt=celebration_prompt)
        return chain.run(word=word, correct_answer=correct_answer)
    
    def generate_session_summary(self, stats: Dict) -> str:
        """Generate an encouraging session summary."""
        chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt_manager.get_prompt("session_summary")
        )
        
        return chain.run(
            correct_count=stats["correct_answers"],
            incorrect_count=stats["incorrect_answers"],
            learned_words=", ".join(stats["words_learned"])
        )
    
    def generate_error_feedback(self, word: str, student_answer: str, correct_synonyms: List[str]) -> str:
        """Generate constructive feedback for incorrect answers."""
        error_prompt = PromptTemplate(
            template="The student answered '{student_answer}' for the Hindi word '{word}', but this was incorrect. The correct synonyms are: {correct_synonyms}. Generate a helpful and encouraging feedback message that explains why the answer was incorrect and provides a hint for the correct answer.",
            input_variables=["word", "student_answer", "correct_synonyms"]
        )
        
        chain = LLMChain(llm=self.llm, prompt=error_prompt)
        return chain.run(
            word=word,
            student_answer=student_answer,
            correct_synonyms=", ".join(correct_synonyms)
        )
    
    def generate_response(self, prompt_name: str, **kwargs) -> str:
        """Generate a response using a specific prompt template."""
        chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt_manager.get_prompt(prompt_name)
        )
        return chain.run(**kwargs)
    
    def get_next_word_prompt(self, learned_words: List[str]) -> str:
        """Generate a prompt for selecting the next word."""
        next_word_prompt = PromptTemplate(
            template="The student has already learned these Hindi words: {learned_words}. Suggest a new word that would be appropriate for their next lesson.",
            input_variables=["learned_words"]
        )
        
        chain = LLMChain(llm=self.llm, prompt=next_word_prompt)
        return chain.run(learned_words=", ".join(learned_words))

def generate_response(prompt: str) -> str:
    """Utility function for quick response generation"""
    model = GenerativeModel()
    return model.generate_response(prompt)
