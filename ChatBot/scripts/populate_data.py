"""
DEPRECATED: This script is no longer used for data population.
The AI agent now handles all data population in real-time.

To add new words and synonyms, use the AI agent interface instead.
The MuRILEmbedding class in models/embedding_model.py now handles real-time word additions.
"""

import sys
print("⚠️ This script is deprecated.")
print("The AI agent now handles all data population in real-time.")
print("Please use the AI agent interface to add new words and synonyms.")

from pathlib import Path
import json
import numpy as np
import sqlite3
from typing import Dict, List, Any
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from database.db_manager import DatabaseManager
from models.embedding_model import MuRILEmbedding

class DataPopulator:
    def __init__(self, use_embeddings=True):
        self.db = DatabaseManager()
        self.use_embeddings = use_embeddings
        if use_embeddings:
            try:
                self.embedding_model = MuRILEmbedding()
                print("✅ Embedding model initialized successfully")
            except Exception as e:
                print(f"⚠️ Warning: Could not initialize embedding model: {e}")
                print("Falling back to non-embedding mode")
                self.use_embeddings = False
        
    def load_data(self, file_path: str) -> Dict[str, Any]:
        """Load data from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def populate_database(self, data: Dict[str, Any]):
        """Populate database with words and synonyms."""
        print("Starting database population...")
        print(f"Mode: {'Using embeddings' if self.use_embeddings else 'Without embeddings'}")
        
        for hindi_word, details in data.items():
            try:
                synonyms, confidence_score, learned, category = details
                
                # Add word to SQLite
                print(f"\nProcessing word: {hindi_word}")
                word_id = self.db.add_word(
                    hindi_word=hindi_word,
                    category=category,
                    learned=learned
                )
                print(f"✅ Added word: {hindi_word}")
                
                # Add synonyms
                for synonym in synonyms:
                    try:
                        if self.use_embeddings:
                            # Get real embedding from MuRIL
                            try:
                                embedding = self.embedding_model.get_word_embedding(synonym)
                                print(f"✅ Generated embedding for: {synonym}")
                            except Exception as e:
                                print(f"⚠️ Warning: Could not generate embedding for {synonym}: {e}")
                                print("Using dummy embedding instead")
                                embedding = np.zeros(768)  # MuRIL's embedding size
                        else:
                            # Use dummy embedding
                            embedding = np.zeros(768)
                        
                        # Add to database
                        self.db.add_synonym_with_embedding(
                            word_id=word_id,
                            synonym=synonym,
                            embedding=embedding.tolist(),
                            confidence=confidence_score
                        )
                        print(f"✅ Added synonym: {synonym}")
                    except Exception as e:
                        print(f"❌ Error processing synonym {synonym}: {e}")
                        continue
                
            except Exception as e:
                print(f"❌ Error processing word {hindi_word}: {e}")
                continue
        
        print("\n🎉 Database population completed!")
        if not self.use_embeddings:
            print("\n⚠️ Note: Database was populated without real embeddings.")
            print("Similarity matching in the AI agent may not work accurately.")
            print("To enable embeddings, please set up HuggingFace authentication.")
    
    def verify_population(self):
        """Verify that data was populated correctly."""
        print("\nVerifying database population...")
        
        try:
            # Check SQLite tables
            with sqlite3.connect(self.db.sqlite_path) as conn:
                cursor = conn.cursor()
                
                # Check words table
                cursor.execute("SELECT COUNT(*) FROM words")
                word_count = cursor.fetchone()[0]
                print(f"✅ Words in database: {word_count}")
                
                # Check synonyms table
                cursor.execute("SELECT COUNT(*) FROM synonyms")
                synonym_count = cursor.fetchone()[0]
                print(f"✅ Synonyms in database: {synonym_count}")
                
                # Sample check
                cursor.execute("""
                    SELECT w.hindi_word, GROUP_CONCAT(s.synonym) as synonyms
                    FROM words w
                    JOIN synonyms s ON w.word_id = s.word_id
                    GROUP BY w.hindi_word
                    LIMIT 3
                """)
                samples = cursor.fetchall()
                print("\nSample entries:")
                for word, syns in samples:
                    print(f"{word}: {syns}")
                
        except Exception as e:
            print(f"❌ Error during verification: {e}")

def main():
    # Check if HuggingFace token is available
    use_embeddings = bool(os.getenv('HUGGINGFACE_TOKEN'))
    
    # Sample data (you would typically load this from a file)
    sample_data = {
        "आनंद": [["खुशी", "प्रसन्नता", "हर्ष"], 1, 1, "adjective"],
        "तेज": [["धारदार", "चुस्त", "तीव्र"], 1, 1, "adjective"],
        "शांत": [["शीतल", "स्थिर", "सौम्य"], 1, 1, "adjective"],
        "ज्ञान": [["बुद्धि", "विवेक", "समझ"], 1, 1, "adjective"]
    }
    
    populator = DataPopulator(use_embeddings=use_embeddings)
    
    # If you want to load from file instead:
    # data = populator.load_data('data/hindi_words.json')
    
    # Populate database
    populator.populate_database(sample_data)
    
    # Verify population
    populator.verify_population()

if __name__ == "__main__":
    main() 