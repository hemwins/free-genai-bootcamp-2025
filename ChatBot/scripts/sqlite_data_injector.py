import sqlite3
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Union

class SQLiteDataInjector:
    def __init__(self, db_path: Union[str, Path] = None):
        """Initialize the data injector with database path."""
        if db_path is None:
            # Use default path relative to project root
            db_path = Path(__file__).parent.parent / "database" / "hindi_tutor.db"
        self.db_path = Path(db_path)
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def inject_data(self, data: Dict[str, List[Any]]) -> None:
        """
        Inject data into words and synonyms tables.
        
        Data format expected:
        {
            "hindi_word": [[synonyms], confidence_score, difficulty_level, category],
            ...
        }
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                print("\n🚀 Starting data injection...")
                
                for hindi_word, details in data.items():
                    try:
                        synonyms, confidence_score, difficulty_level, category = details
                        
                        # Generate a unique word_id
                        word_id = str(uuid.uuid4())
                        
                        # Insert into words table
                        cursor.execute("""
                            INSERT INTO words (word_id, hindi_word, difficulty_level, category)
                            VALUES (?, ?, ?, ?)
                        """, (word_id, hindi_word, difficulty_level, category))
                        
                        print(f"✅ Added word: {hindi_word}")
                        
                        # Insert synonyms
                        for synonym in synonyms:
                            synonym_id = str(uuid.uuid4())
                            cursor.execute("""
                                INSERT INTO synonyms (synonym_id, word_id, synonym, confidence_score)
                                VALUES (?, ?, ?, ?)
                            """, (synonym_id, word_id, synonym, confidence_score))
                            print(f"  ➕ Added synonym: {synonym}")
                            
                    except Exception as e:
                        print(f"❌ Error processing word {hindi_word}: {e}")
                        continue
                
                conn.commit()
                print("\n✨ Data injection completed successfully!")
                
                # Print summary
                cursor.execute("SELECT COUNT(*) FROM words")
                word_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM synonyms")
                synonym_count = cursor.fetchone()[0]
                
                print("\n📊 Summary:")
                print(f"Total words added: {word_count}")
                print(f"Total synonyms added: {synonym_count}")
                
        except Exception as e:
            print(f"❌ Error during data injection: {e}")
            raise

    def load_json_file(self, file_path: Union[str, Path]) -> Dict[str, List[Any]]:
        """Load data from a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def verify_data(self) -> None:
        """Verify the injected data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                print("\n🔍 Verifying injected data...")
                
                # Check words table
                cursor.execute("""
                    SELECT w.hindi_word, w.category, w.difficulty_level,
                           GROUP_CONCAT(s.synonym) as synonyms
                    FROM words w
                    LEFT JOIN synonyms s ON w.word_id = s.word_id
                    GROUP BY w.word_id
                    LIMIT 5
                """)
                
                rows = cursor.fetchall()
                
                print("\nSample entries:")
                for row in rows:
                    word, category, difficulty, synonyms = row
                    print(f"\nWord: {word}")
                    print(f"Category: {category}")
                    print(f"Difficulty: {difficulty}")
                    print(f"Synonyms: {synonyms}")
                    
        except Exception as e:
            print(f"❌ Error during verification: {e}")
            raise

def main():
    # Sample data
    sample_data = {
        "प्यार": [["प्रेम", "स्नेह", "अनुराग"], 1, 1, "noun"],
        "पानी": [["जल", "नीर", "वारि"], 1, 1, "noun"],
        "अच्छा": [["उत्तम", "श्रेष्ठ", "उम्दा"], 1, 1, "adjective"],
        "घर": [["आवास", "निवास", "गृह"], 1, 1, "noun"],
        "लाल": [["रक्त", "सुर्ख", "अरुण"], 1, 1, "adjective"],
        "समय": [["काल", "वक्त", "वेला"], 1, 1, "noun"],
        "खुश": [["प्रसन्न", "आनंदित", "हर्षित"], 1, 1, "adjective"],
        "मित्र": [["दोस्त", "सखा", "साथी"], 1, 1, "noun"],
        "तेज़": [["तीव्र", "तीक्ष्ण", "प्रखर"], 1, 1, "adjective"],
        "आँख": [["नेत्र", "नयन", "लोचन"], 1, 1, "noun"],
        "नया": [["नवीन", "नूतन", "अभिनव"], 1, 1, "adjective"],
        "फूल": [["पुष्प", "कुसुम", "सुमन"], 1, 1, "noun"],
        "मीठा": [["मधुर", "स्वादिष्ट", "शीरीन"], 1, 1, "adjective"],
        "दिल": [["हृदय", "मन", "अंतःकरण"], 1, 1, "noun"],
        "गरम": [["उष्ण", "तप्त", "दाहक"], 1, 1, "adjective"],
        "आकाश": [["नभ", "गगन", "अंबर"], 1, 1, "noun"],
        "किताब": [["पुस्तक", "ग्रंथ", "पोथी"], 1, 1, "noun"]
    }
    
    # Initialize injector
    injector = SQLiteDataInjector()
    
    # Inject data
    injector.inject_data(sample_data)
    
    # Verify injection
    injector.verify_data()

if __name__ == "__main__":
    main() 