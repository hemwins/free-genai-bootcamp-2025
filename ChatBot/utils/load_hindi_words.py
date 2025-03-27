import json
from typing import List

def load_hindi_words(file_path: str) -> List[str]:
    """
    Load Hindi words from a JSON file.

    Args:
        file_path (str): Path to the JSON file containing Hindi words.

    Returns:
        List[str]: A list of Hindi words.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            words = json.load(file)
        return words
    except Exception as e:
        raise RuntimeError(f"Error loading Hindi words from {file_path}: {e}")
