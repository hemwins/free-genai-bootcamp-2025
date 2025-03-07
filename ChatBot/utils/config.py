import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Application configuration."""
    # Environment
    ENV: str
    TESTING: bool
    DEBUG: bool
    
    # Paths
    BASE_DIR: Path
    DB_PATH: Path
    CHROMA_PATH: Path
    
    # API Configuration
    HUGGINGFACE_TOKEN: str
    MAX_REQUESTS_PER_MINUTE: int
    REQUEST_WINDOW: int
    
    # Cache Settings
    MAX_CACHE_SIZE: int
    CACHE_EXPIRY_DAYS: int
    
    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from environment."""
        load_dotenv()
        
        # Determine environment
        env = os.getenv('ENV', 'development')
        testing = os.getenv('TESTING', 'False').lower() == 'true'
        
        # Set base directory
        base_dir = Path(__file__).parent.parent
        
        # Use test database if in testing mode
        if testing:
            db_path = base_dir / "tests" / "test_data" / "test.db"
            chroma_path = base_dir / "tests" / "test_data" / "chroma_db"
        else:
            db_path = base_dir / "database" / "hindi_tutor.db"
            chroma_path = base_dir / "database" / "chroma_db"
        
        return cls(
            ENV=env,
            TESTING=testing,
            DEBUG=os.getenv('DEBUG', 'False').lower() == 'true',
            
            BASE_DIR=base_dir,
            DB_PATH=db_path,
            CHROMA_PATH=chroma_path,
            
            HUGGINGFACE_TOKEN=os.getenv('HUGGINGFACE_TOKEN', ''),
            MAX_REQUESTS_PER_MINUTE=int(os.getenv('MAX_REQUESTS_PER_MINUTE', '20')),
            REQUEST_WINDOW=int(os.getenv('REQUEST_WINDOW', '60')),
            
            MAX_CACHE_SIZE=int(os.getenv('MAX_CACHE_SIZE', '1000')),
            CACHE_EXPIRY_DAYS=int(os.getenv('CACHE_EXPIRY_DAYS', '30'))
        )

    def validate(self) -> None:
        """Validate configuration."""
        if not self.TESTING:
            # Only validate required settings in non-test environment
            if not self.HUGGINGFACE_TOKEN:
                raise ValueError("HUGGINGFACE_TOKEN is required in non-test environment")
            
            if not self.DB_PATH.parent.exists():
                raise ValueError(f"Database directory does not exist: {self.DB_PATH.parent}")

# Global configuration instance
config = Config.load() 