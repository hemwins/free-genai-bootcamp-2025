# Hindi Learning Agent

An interactive AI-powered Hindi synonym learning system using FastText embeddings and ChromaDB for semantic similarity.

## Project Structure

```
ChatBot/
├── agent/
│   ├── __init__.py
│   ├── agent.py              # Main agent implementation
│   └── utils.py             # Agent utility functions
│
├── models/
│   ├── __init__.py
│   ├── embedding_model.py   # FastText embedding implementation
│   └── generative_model.py  # Text generation model
│
├── database/
│   ├── __init__.py
│   ├── db_manager.py        # Database management
│   ├── hindi_tutor.db       # SQLite database
│   └── chroma_db/          # ChromaDB storage
│
├── scripts/
│   ├── __init__.py
│   ├── create_tables.sql    # Database schema
│   ├── populate_data.py     # Data population script
│   ├── verify_setup.py      # Setup verification
│   └── sqlite_data_injector.py  # Standalone data injection
│
├── data/
│   ├── hindi_words.json     # Word and synonym data
│   └── learning_history/    # Student learning records
│
├── logs/
│   ├── debug.log           # Detailed debug logs
│   ├── error.log          # Error tracking
│   └── api.log            # API call monitoring
│
├── tests/
│   ├── __init__.py
│   ├── test_agent.py       # Agent tests
│   ├── test_embedding_model.py  # Embedding tests
│   ├── test_db_manager.py  # Database tests
│   └── test_data/         # Test fixtures
│
├── utils/
│   ├── __init__.py
│   └── logger.py          # Logging configuration
│
├── app.py                 # Main Streamlit application
├── requirements.txt       # Project dependencies
├── .env                  # Environment variables
└── README.md             # Project documentation
```

## Features

- Interactive Hindi synonym learning
- Semantic similarity using FastText embeddings
- Real-time feedback and hints
- Progress tracking
- Session summaries
- Comprehensive logging
- Caching and rate limiting
- Fallback mechanisms

## Dependencies

- streamlit
- transformers
- chromadb
- torch
- numpy
- requests
- python-dotenv
- FastText

