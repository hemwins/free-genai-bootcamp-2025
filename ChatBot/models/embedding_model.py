import numpy as np
import chromadb
import fasttext
import os
import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from langchain.embeddings.base import Embeddings
import fasttext
from langchain_community.vectorstores import Chroma

class FastTextEmbeddings(Embeddings):
    """Custom wrapper for FastText embeddings in LangChain."""
    def __init__(self, model_path: str):
        self.model = fasttext.load_model(model_path)

    def embed_query(self, text: str) -> list:
        return self.model.get_word_vector(text).tolist()

    def embed_documents(self, texts: list) -> list:
        return [self.model.get_word_vector(text).tolist() for text in texts]
    
class FastTextEmbedding:
    MAX_CACHE_SIZE = 10
    CACHE_EXPIRY_DAYS = 20
    
    def __init__(self):
        self._setup_logging()
        
        # Load FastText model using LangChain
        self.model_path = "cc.hi.300.bin"  # Ensure this file is downloaded
        self.embedding_dim = 300
        #self.fasttext_embeddings = FastTextEmbeddings(model_path=self.model_path)
        self.fasttext_embeddings = FastTextEmbeddings(self.model_path)

        # Setup database paths
        self.db_dir = Path("database")
        self.chroma_path = self.db_dir / "chroma_db"
        self.sqlite_path = self.db_dir / "hindi_tutor.db"
        
        # Setup ChromaDB using LangChain
        self.vector_store = Chroma(
            persist_directory=str(self.chroma_path),
            embedding_function=self.fasttext_embeddings,
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

    def _get_exact_match_embedding(self, text: str) -> np.ndarray:
        """Get embedding from ChromaDB for exact matches."""
        try:
            results = self.vector_store.similarity_search(text, k=1)
            if results:
                return np.array(results[0].embedding)
        except Exception:
            pass
        return None
    
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
        return np.array(self.fasttext_embeddings.embed_query(text))
    
    def add_word_with_synonyms(self, word: str, synonyms: List[str]) -> None:
        """Add word and its synonyms with embeddings."""
        word_embedding = self.get_word_embedding(word)
        documents = [word] + synonyms
        embeddings = [word_embedding] + [self.get_word_embedding(syn) for syn in synonyms]
        
        self.vector_store.add_texts(texts=documents, embeddings=embeddings)
    
    def find_closest_match(self, student_answer: str, target_word: str) -> Tuple[bool, float]:
        """Find similarity between a student's answer and target word."""
        answer_embedding = self.get_word_embedding(student_answer)
        results = self.vector_store.similarity_search_with_score(student_answer, k=1)
        if results:
            similarity = results[0][1]  # Similarity score
            is_match = similarity > 0.8  # Define a threshold for matching
            return is_match, similarity
        return False, 0.0
    
    def get_unlearned_words(self, learned_words: List[str]) -> List[str]:
        """Fetch words that haven't been learned yet."""
        all_words = [doc.page_content for doc in self.vector_store.similarity_search("", k=50)]
        return [word for word in all_words if word not in learned_words]
    
    def get_word_synonyms(self, word: str) -> List[str]:
        """Get all synonyms for a given word."""
        try:
            results = self.vector_store.similarity_search(word, k=1)
            if results:
                return results[0].metadata.get("synonyms", [])
        except Exception as e:
            self.logger.error(f"Error fetching synonyms for {word}: {e}")
        return []
