import numpy as np
import fasttext
import os
import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores.chroma import Chroma

class FastTextEmbeddings(Embeddings):
    """Custom FastText embeddings wrapper for LangChain."""
    def __init__(self, model_path: str):
        self.model = fasttext.load_model(model_path)

    def embed_query(self, text: str) -> List[float]:
        """Embed a single piece of text."""
        return self.model.get_word_vector(text).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts."""
        return [self.model.get_word_vector(text).tolist() for text in texts]

class FastTextEmbedding:
    MAX_CACHE_SIZE = 10
    CACHE_EXPIRY_DAYS = 20
    
    def __init__(self):
        self._setup_logging()
        
        # Load FastText model via LangChain wrapper
        self.model_path = "cc.hi.300.bin"  # Ensure this file is downloaded
        self.embedding_dim = 300
        self.embeddings = FastTextEmbeddings(self.model_path)

        # Setup database paths
        self.db_dir = Path("database")
        self.sqlite_path = self.db_dir / "hindi_tutor.db"
        self.chroma_path = self.db_dir / "chroma_db"
        
        # Initialize Chroma vector store
        self.vector_store = Chroma(
            persist_directory=str(self.chroma_path),
            embedding_function=self.embeddings,
            collection_name="hindi_words"
        )
        
        self.logger.info("FastTextEmbedding initialized successfully")
        self._sync_databases()
    
    def _setup_logging(self):
        self.logger = logging.getLogger('hindi_tutor')
        self.logger.setLevel(logging.DEBUG)
        logs_dir = Path("logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(logs_dir / f"hindi_tutor_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        fh.setFormatter(file_formatter)
        ch.setFormatter(console_formatter)
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def _get_exact_match_embedding(self, text: str) -> bool:
        """Get embedding from vector store."""
        try:
            results = self.vector_store.similarity_search_with_score(text, k=1)
            if results:
                doc, score = results[0]
                if score > 0.95:  # Very high similarity threshold for exact match
                    return True
        except Exception:
            pass
        return False
    
    def _sync_databases(self):
        """Sync words and synonyms from SQLite to ChromaDB."""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT w.word_id, w.hindi_word, GROUP_CONCAT(s.synonym) as synonyms
                    FROM words w
                    LEFT JOIN synonyms s ON w.word_id = s.word_id
                    GROUP BY w.word_id
                """)
                rows = cursor.fetchall()
                
                for row in rows:
                    word_id, word, synonyms_str = row
                    synonyms = synonyms_str.split(',') if synonyms_str else []
                    if not self._get_exact_match_embedding(word):
                        self.add_word_with_synonyms(word, synonyms)
        except Exception as e:
            self.logger.error(f"Error syncing databases: {e}")
    
    def get_word_embedding(self, text: str) -> np.ndarray:
        """Fetch word embedding using LangChain FastText wrapper."""
        return np.array(self.embeddings.embed_query(text))
    
    def add_word_with_synonyms(self, word: str, synonyms: List[str]) -> None:
        """Add word and its synonyms to both SQLite and vector store."""
        try:
            # Add to vector store with proper metadata
            # Add the main word
            self.vector_store.add_texts(
                texts=[word],
                metadatas=[{"type": "word", "synonym_count": len(synonyms)}]
            )
            
            # Add each synonym separately
            for synonym in synonyms:
                self.vector_store.add_texts(
                    texts=[synonym],
                    metadatas=[{"type": "synonym", "main_word": word}]
                )
            
        except sqlite3.IntegrityError:
            self.logger.warning(f"Word {word} already exists in database")
        except Exception as e:
            self.logger.error(f"Error adding word {word}: {e}")
    
    def find_closest_match(self, student_answer: str, target_word: str) -> Tuple[bool, float]:
        """Find similarity between a student's answer and target word using vector store."""
        try:
            results = self.vector_store.similarity_search_with_score(student_answer, k=1)
            if results:
                doc, similarity = results[0]
                is_match = similarity > 0.8  # Define a threshold for matching
                return is_match, float(similarity)
        except Exception as e:
            self.logger.error(f"Error finding closest match: {e}")
        return False, 0.0
    
    def get_unlearned_words(self, learned_words: List[str]) -> List[str]:
        """Fetch words that haven't been learned yet using vector store."""
        try:
            # Get all documents with type 'word'
            results = self.vector_store.similarity_search(
                "",  # Empty query to get all documents
                k=100,  # Increase if needed
                filter={"type": "word"}
            )
            all_words = [doc.page_content for doc in results]
            return [word for word in all_words if word not in learned_words]
        except Exception as e:
            self.logger.error(f"Error fetching unlearned words: {e}")
            return []
    
    def get_word_synonyms(self, word: str) -> List[str]:
        """Get all synonyms for a given word from vector store."""
        try:
            results = self.vector_store.similarity_search(
                word,
                k=1,
                filter={"type": "word"}
            )
            if results:
                return results[0].metadata.get("synonyms", [])
        except Exception as e:
            self.logger.error(f"Error fetching synonyms for {word}: {e}")
        return []

    def get_similar_words(self, word: str, k: int = 3) -> List[str]:
        """Get k similar words from vector store excluding the input word."""
        try:
            results = self.vector_store.similarity_search_with_score(
                word,
                k=k + 1,  # Get one extra to account for the word itself
                filter={"type": "word"}
            )
            # Filter out the input word and get unique words
            similar_words = []
            for doc, _ in results:
                if doc.page_content != word and len(similar_words) < k:
                    similar_words.append(doc.page_content)
            return similar_words
        except Exception as e:
            self.logger.error(f"Error fetching similar words for {word}: {e}")
            return []
            
    def get_all_words(self) -> Dict[str, List[str]]:
        """Get all words and their synonyms from SQLite database."""
        try:
            words_dict = {}
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT w.hindi_word, GROUP_CONCAT(s.synonym) as synonyms
                    FROM words w
                    LEFT JOIN synonyms s ON w.word_id = s.word_id
                    GROUP BY w.word_id
                """)
                for row in cursor.fetchall():
                    word, synonyms_str = row
                    synonyms = synonyms_str.split(',') if synonyms_str else []
                    words_dict[word] = synonyms
            return words_dict
        except Exception as e:
            self.logger.error(f"Error getting all words from SQLite: {e}")
            return {}
        
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single piece of text."""
        return self.embeddings.embed_query(text)
