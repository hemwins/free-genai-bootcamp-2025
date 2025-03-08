import numpy as np
import json
import os
from typing import Dict, List

def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def format_synonym_list(synonyms):
    """Format a list of synonyms for display."""
    return ", ".join(synonyms)

def load_hindi_words() -> Dict[str, List[str]]:
    """Load Hindi words and their synonyms from JSON file"""
    file_path = "data/hindi_words.json"
    if not os.path.exists(file_path):
        # Create a sample dictionary if file doesn't exist
        sample_words = {
            "सुंदर": ["खूबसूरत", "मनोहर", "सोहना"],
            "बड़ा": ["विशाल", "महान", "विराट"],
            "आनंद": ["खुशी", "प्रसन्नता", "हर्ष"]
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sample_words, f, ensure_ascii=False, indent=4)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def ensure_data_directory():
    """Ensure data directory exists"""
    os.makedirs("data", exist_ok=True)
    
def initialize_learning_history(student_id: str) -> Dict:
    """Initialize or load learning history for a student"""
    history_file = f"data/learning_history_{student_id}.json"
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            return json.load(f)
    return {
        "correct": [],
        "incorrect": [],
        "total_correct": 0,
        "total_incorrect": 0,
        "sessions": []
    }

def save_learning_history(student_id: str, history: Dict):
    """Save learning history to file"""
    history_file = f"data/learning_history_{student_id}.json"
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=4)
