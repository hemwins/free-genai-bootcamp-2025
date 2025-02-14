## Install

```sh
pip install -r requirements.txt
```

## Setting up the database

```sh
invoke init-db
```

This will do the following:
- create the JapaneseDB.db (Sqlite3 database)
- run the migrations found in `seeds/`
- run the seed data found in `seed/`

Please note that migrations and seed data is manually coded to be imported in the `lib/db.py`. So you need to modify this code if you want to import other seed data.

## Clearing the database

Simply delete the `JapaneseDB.db` to clear entire database.

## Running the backend api

```sh
python app.py 
```

This should start the flask app on port `4999`

## Technical Specification

1. GET /words - Get paginated list of words with review statistics
2. GET /groups - Get paginated list of word groups with word counts
3. GET /groups/:id - Get words from a specific group (This is intended to be used by target apps)
4. POST /study_sessions - Create a new study session for a group
5. POST /study_sessions/:id/review - Log a review attempt for a word during a study session

6. GET /words
page: Page number (default: 1)
sort_by: Sort field ('kanji', 'romaji', 'english', 'correct_count', 'wrong_count') (default: 'kanji')
order: Sort order ('asc' or 'desc') (default: 'asc')

7. GET /groups/:id
page: Page number (default: 1)
sort_by: Sort field ('name', 'words_count') (default: 'name')
order: Sort order ('asc' or 'desc') (default: 'asc')

8. POST /study_sessions
group_id: ID of the group to study (required)
study_activity_id: ID of the study activity (required)


9. POST /study_sessions/:id/review  -- it records whether a word was answered correctly or incorrectly during a study session

## Leverage AI-coding assistants:

Github Copilot

## Running Tests

```sh
# Make sure you're in the backend-flask directory
cd to your backend-flask

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_study_sessions.py -v
```

