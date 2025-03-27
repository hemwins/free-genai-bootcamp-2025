import sqlite3
import chromadb
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import uuid
from utils.logger import get_logger
from utils.config import config

class DatabaseManager:
    def __init__(self):
        try:
            # Initialize logger first
            self.logger = get_logger(__name__)
            # db_path = "database/hindi_tutor.db"
            # self.sqlite_path = db_path
            
            # Use configuration paths
            self.sqlite_path = config.DB_PATH
            self.chroma_path = config.CHROMA_PATH
            
            # Ensure directories exist
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            self.chroma_path.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Database directory initialized at {self.sqlite_path.parent}")
            
            # Initialize databases
            self.init_sqlite()
            self.init_chroma()
            self.logger.info("Database manager initialized successfully")
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to initialize database manager: {e}", exc_info=True)
            raise

    def init_sqlite(self):
        """Initialize SQLite database with schema."""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                # Read and execute schema
                schema_path = Path(__file__).parent.parent / "scripts" / "create_tables.sql"
                with open(schema_path) as f:
                    conn.executescript(f.read())
                conn.commit()
                self.logger.info("SQLite database initialized with schema")
        except Exception as e:
            self.logger.error(f"Error initializing SQLite database: {e}", exc_info=True)
            raise

    def init_chroma(self):
        """Initialize ChromaDB."""
        try:
            # Initialize ChromaDB client and collection
            self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_path))
            self.word_embeddings = self.chroma_client.get_or_create_collection(
                name="word_embeddings",
                metadata={"hnsw:space": "cosine"}
            )
            
            # After successful initialization, handle test mode if needed
            if hasattr(config, 'TESTING') and config.TESTING:
                self.logger.warning("Test mode enabled - resetting word embeddings collection")
                self.word_embeddings.delete(where={})
                
        except Exception as e:
            self.logger.error(f"Error initializing ChromaDB: {e}", exc_info=True)
            raise

    def add_word(self, hindi_word: str, category: str = None, learned: int = 1) -> str:
        """Add a new word to SQLite."""
        word_id = str(uuid.uuid4())
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.execute("""
                    INSERT INTO words (word_id, hindi_word, category, learned)
                    VALUES (?, ?, ?, ?)
                """, (word_id, hindi_word, category, 0))
                self.logger.info(f"Added word: {hindi_word} with ID: {word_id}")
            return word_id
        except Exception as e:
            self.logger.error(f"Error adding word {hindi_word}: {e}", exc_info=True)
            raise

    def add_synonym_with_embedding(self, word_id: str, synonym: str, embedding: List[float], 
                                 confidence: float = 1.0):
        """Add synonym to both SQLite and ChromaDB."""
        try:
            # Add to SQLite
            synonym_id = str(uuid.uuid4())
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.execute("""
                    INSERT INTO synonyms (synonym_id, word_id, synonym, confidence_score)
                    VALUES (?, ?, ?, ?)
                """, (synonym_id, word_id, synonym, confidence))
                self.logger.info(f"Added synonym: {synonym} for word_id: {word_id}")

            # Add to ChromaDB
            self.word_embeddings.add(
                ids=[synonym_id],
                embeddings=[embedding],
                documents=[synonym],
                metadatas=[{"word_id": word_id, "type": "synonym"}]
            )
        except Exception as e:
            self.logger.error(f"Error adding synonym {synonym}: {e}", exc_info=True)
            raise

    def find_similar_words(self, query_embedding: List[float], n_results: int = 5) -> List[Dict]:
        """Find similar words using ChromaDB."""
        results = self.word_embeddings.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Get additional info from SQLite
        word_ids = [m["word_id"] for m in results["metadatas"][0]]
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            words = conn.execute("""
                SELECT w.*, s.synonym 
                FROM words w 
                JOIN synonyms s ON w.word_id = s.word_id 
                WHERE s.synonym_id IN ({})
            """.format(','.join('?' * len(word_ids))), word_ids).fetchall()
            
        return [dict(word) for word in words]

    def save_learning_history(self, student_id: str, word_id: str, 
                            answer: str, is_correct: bool, session_id: str):
        """Save a learning interaction."""
        try:
            history_id = str(uuid.uuid4())
            with sqlite3.connect(self.sqlite_path) as conn:
                # Save learning history
                conn.execute("""
                    INSERT INTO learning_history 
                    (history_id, student_id, word_id, student_answer, is_correct, session_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (history_id, student_id, word_id, answer, is_correct, session_id))
                
                self.logger.info(
                    f"Saved learning history - Student: {student_id}, " +
                    f"Word: {word_id}, Correct: {is_correct}"
                )
        except Exception as e:
            self.logger.error(f"Error saving learning history: {e}", exc_info=True)
            raise
            
    def mark_word_learned(self, student_id: str, hindi_word: str) -> bool:
        """Mark a word as learned for a student using the hindi_word."""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                # Get word_id from hindi_word
                cursor.execute(
                    "SELECT word_id FROM words WHERE hindi_word = ?",
                    (hindi_word,)
                )
                word_record = cursor.fetchone()
                
                if word_record:
                    word_id = word_record[0]
                    # Update words table
                    cursor.execute("""
                        UPDATE words SET learned = 1 WHERE word_id = ?
                    """, (word_id,))
                    
                    # Add to learning history as correct answer
                    history_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO learning_history 
                        (history_id, student_id, word_id, student_answer, is_correct, session_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (history_id, student_id, word_id, hindi_word, True, None))
                    
                    conn.commit()
                    self.logger.info(f"Marked word '{hindi_word}' as learned for student {student_id}")
                    return True
                else:
                    self.logger.warning(f"Word '{hindi_word}' not found in database")
                    return False
        except Exception as e:
            self.logger.error(f"Error marking word as learned: {e}", exc_info=True)
            return False
        
    def find_synonyms(self, word: str) -> List[str]:
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "SELECT word_id FROM words WHERE hindi_word = ?",
                        (word,)
                    )
                    word_id_result = cursor.fetchone()
                    word_id = word_id_result[0]
 
                    self.logger.debug(f"Successfully fetched word_id {word_id} for word {word}")
                except sqlite3.Error as e:
                    self.logger.error(f"Error fetching word_id for word {word}: {e}")
                    
                cursor.execute("""
                    SELECT synonym 
                    FROM synonyms 
                    WHERE word_id = ?
                    """, (word_id,))
                
                # Fetch all synonyms and return as list of strings
                synonyms = [row[0] for row in cursor.fetchall()]
                self.logger.debug(f"Retrieved {len(synonyms)} synonyms for word: {word}")
                return synonyms
        except Exception as e:
            self.logger.error(f"Error finding synonyms for word {word}: {e}")
            return []
            
    def get_unlearned_words(self, student_id: str) -> List[str]:
        """Get words the student hasn't learned yet using learning_history table."""
        try:
            # Ensure student exists
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO students (student_id) VALUES (?)",
                        (student_id,)
                    )
                    conn.commit()
                    self.logger.debug(f"Successfully inserted or ignored student {student_id}")
                except sqlite3.Error as e:
                    self.logger.error(f"Error inserting student ID: {e}")
                    raise  # Re-raise the exception to stop execution if the student ID cannot be inserted.

                cursor.execute("""
                    SELECT w.hindi_word 
                    FROM words w
                    WHERE w.word_id NOT IN (
                        SELECT word_id 
                        FROM learning_history
                        WHERE student_id = ? AND is_correct = 1
                    )
                    ORDER BY w.created_at ASC
                LIMIT ?
            """, (student_id, 3))
            
                # Return list of strings instead of list of dicts
                result = [row[0] for row in cursor.fetchall()]
                self.logger.debug(f"Retrieved {len(result)} unlearned words for student: {student_id}")
                return result
        except Exception as e:
            self.logger.error(f"Error getting unlearned words: {e}")
            return []

# Example usage
if __name__ == "__main__":
    # Initialize database
    db = DatabaseManager()
    
    # Add some sample data
    #word_id = db.add_word("सुंदर", "adjectives", 1)
    unLearnedWords = db.get_unlearned_words(student_id="student_1042")
    
    
    # Add synonyms with embeddings (you'd get these from FastText)
    #sample_embedding = [0.1] * 768  # Replace with actual FastText embedding
    #db.add_synonym_with_embedding(word_id, "खूबसूरत", sample_embedding)
    
    print("Database unlearned words fetched! " + str(unLearnedWords))