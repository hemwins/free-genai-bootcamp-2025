import sys
from pathlib import Path
import numpy as np
import sqlite3

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from database.db_manager import DatabaseManager

def verify_database_setup():
    """Verify the complete database setup with test data."""
    print("Starting database verification...")
    
    # Initialize database manager
    try:
        db = DatabaseManager()
        print("✅ Database manager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database manager: {e}")
        return False

    # Test 1: Check if database files exist
    try:
        if db.sqlite_path.exists():
            print("✅ SQLite database file exists")
        else:
            print("❌ SQLite database file not found")
            return False
    except Exception as e:
        print(f"❌ Error checking SQLite file: {e}")
        return False

    try:
        if not db.chroma_path.exists():
            print("❌ ChromaDB directory not found")
            return False
        print("✅ ChromaDB directory exists")
    except Exception as e:
        print(f"❌ Error checking ChromaDB directory: {e}")
        return False

    # Test 2: Add test data
    try:
        # Add a test student using sqlite3.connect()
        with sqlite3.connect(db.sqlite_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO students (student_id, name)
                VALUES (?, ?)
            """, ("test_student_1", "Test Student"))
            conn.commit()
            print("✅ Added test student successfully")

        # Add test words with synonyms
        test_words = [
            ("सुंदर", ["खूबसूरत", "मनोहर"], "adjectives", 1),
            ("बड़ा", ["विशाल", "महान"], "adjectives", 1)
        ]

        for word, synonyms, category, learned in test_words:
            try:
                # Add word
                word_id = db.add_word(word, category, learned)
                print(f"✅ Added word: {word}")

                # Add synonyms with dummy embeddings
                for synonym in synonyms:
                    # Create a random embedding vector (300 dimensions for FastText)
                    dummy_embedding = np.random.rand(300).tolist()
                    db.add_synonym_with_embedding(word_id, synonym, dummy_embedding)
                    print(f"✅ Added synonym: {synonym} with embedding")
            except Exception as e:
                print(f"❌ Error adding word {word}: {e}")
                continue

        # Test 3: Query data
        try:
            # Test word retrieval
            unlearned = db.get_unlearned_words("test_student_1")
            print(f"✅ Retrieved {len(unlearned)} unlearned words")

            # Test similarity search
            test_embedding = np.random.rand(300).tolist()
            similar_words = db.find_similar_words(test_embedding)
            print(f"✅ Similarity search returned {len(similar_words)} results")
        except Exception as e:
            print(f"❌ Error during data querying: {e}")
            return False

        # Test 4: Save learning history
        try:
            db.save_learning_history(
                "test_student_1",
                word_id,  # Using the last word_id from the loop above
                "खूबसूरत",
                True,
                "test_session_1"
            )
            print("✅ Saved learning history successfully")
        except Exception as e:
            print(f"❌ Error saving learning history: {e}")
            return False

        print("\n🎉 All verification tests passed successfully!")
        return True

    except Exception as e:
        print(f"❌ Verification failed with error: {e}")
        return False

def display_database_contents(db_path):
    """Display the contents of all tables in the database."""
    print("\n📊 Database Contents:")
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                print(f"\n--- {table_name} Table ---")
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                # Get column names
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [column[1] for column in cursor.fetchall()]
                print("Columns:", columns)
                
                # Print rows
                for row in rows:
                    print(row)
    except Exception as e:
        print(f"❌ Error displaying database contents: {e}")

if __name__ == "__main__":
    db = DatabaseManager()
    if verify_database_setup():
        # If verification passed, display the database contents
        display_database_contents(db.sqlite_path) 