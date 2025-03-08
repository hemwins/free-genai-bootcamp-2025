import json
from pathlib import Path
from typing import Dict, List
from langchain_core.prompts import PromptTemplate

class HindiTutorPromptManager:
    def __init__(self):
        self.prompts: Dict[str, PromptTemplate] = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """Load prompts from JSON file and convert to PromptTemplates."""
        prompt_file = Path(__file__).parent / "hindi_tutor_prompts.json"
        
        with open(prompt_file, 'r') as f:
            prompt_data = json.load(f)
        
        # Convert each prompt definition to a PromptTemplate
        for prompt_name, prompt_info in prompt_data.items():
            self.prompts[prompt_name] = PromptTemplate(
                template=prompt_info["template"],
                input_variables=prompt_info["input_variables"]
            )
    
    def get_prompt(self, prompt_name: str) -> PromptTemplate:
        """Get a prompt template by name."""
        if prompt_name not in self.prompts:
            raise KeyError(f"Prompt '{prompt_name}' not found")
        return self.prompts[prompt_name]
    
    def format_prompt(self, prompt_name: str, **kwargs) -> str:
        """Format a prompt with the given variables."""
        prompt = self.get_prompt(prompt_name)
        return prompt.format(**kwargs)
    
    def list_prompts(self) -> List[str]:
        """List all available prompt names."""
        return list(self.prompts.keys())
    
    def add_prompt(self, name: str, template: str, input_variables: List[str]):
        """Add a new prompt template programmatically."""
        self.prompts[name] = PromptTemplate(
            template=template,
            input_variables=input_variables
        )
    
    def save_prompts(self):
        """Save all prompts back to the JSON file."""
        prompt_data = {
            name: {
                "template": prompt.template,
                "input_variables": prompt.input_variables
            }
            for name, prompt in self.prompts.items()
        }
        
        prompt_file = Path(__file__).parent / "hindi_tutor_prompts.json"
        with open(prompt_file, 'w') as f:
            json.dump(prompt_data, f, indent=4)