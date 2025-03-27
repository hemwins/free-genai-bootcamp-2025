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
    DEBUG: bool
    
    # Paths
    BASE_DIR: Path
    DB_PATH: Path
    CHROMA_PATH: Path
    
    # Cache Settings
    MAX_CACHE_SIZE: int
    CACHE_EXPIRY_DAYS: int
    
    # Testing mode
    TESTING: bool = False
    
    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from environment."""
        load_dotenv()
        
        # Determine environment
        env = os.getenv('ENV', 'development')
        
        # Set base directory
        base_dir = Path(__file__).parent.parent
        
        # Set database paths
        db_path = base_dir / "database" / "hindi_tutor.db"
        chroma_path = base_dir / "database" / "chroma_db"
        
        return cls(
            ENV=env,
            DEBUG=os.getenv('DEBUG', 'False').lower() == 'true',
            
            BASE_DIR=base_dir,
            DB_PATH=db_path,
            CHROMA_PATH=chroma_path,
            
            MAX_CACHE_SIZE=int(os.getenv('MAX_CACHE_SIZE', '1000')),
            CACHE_EXPIRY_DAYS=int(os.getenv('CACHE_EXPIRY_DAYS', '30')),
            
            TESTING=os.getenv('TESTING', 'False').lower() == 'true'
        )

    def validate(self) -> None:
        """Validate configuration."""
        if not self.DB_PATH.parent.exists():
            raise ValueError(f"Database directory does not exist: {self.DB_PATH.parent}")

# Global configuration instance
config = Config.load() 