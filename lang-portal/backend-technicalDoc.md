## Business Goal: 
A language learning school wants to build a prototype of learning portal which will act as:
- Inventory of possible vocabulary that can be learned
- Act as a  Learning record store (LRS), providing correct and wrong score on practice vocabulary
- A unified launchpad to launch different learning apps

## Technical Restrictions:
- Use SQLite3 as the database
- I used Flask framework 
- Does not require authentication/authorization, assume there is a single user
- The API follows RESTful conventions and provides JSON responses, with the server running on port 4999.
- Flask-CORS for cross-origin resource sharing

## AI-coding assistants:
- Cursor
- Github Copilot

## Technical Specification

### Routes

- GET /words -> Get paginated list of words with review statistics
- GET /groups -> Get paginated list of word groups with word counts
- GET /groups/:id -> Get words from a specific group (This is intended to be used by target apps)
- POST /study_sessions -> Create a new study session for a group
- POST /study_sessions/:id/review -> Log a review attempt for a word during a study session

#### GET /words
- page: Page number (default: 1)
- sort_by: Sort field ('kanji', 'romaji', 'english', 'correct_count', 'wrong_count') (default: 'kanji')
- order: Sort order ('asc' or 'desc') (default: 'asc')

### GET /groups/:id
- page: Page number (default: 1)
- sort_by: Sort field ('name', 'words_count') (default: 'name')
- order: Sort order ('asc' or 'desc') (default: 'asc')

### POST /study_sessions
- `group_id`: ID of the group to study (required)
- `study_activity_id`: ID of the study activity (required)


### POST /study_sessions/:id/review


### Database Schema
#### words 
- Stores individual Japanese vocabulary words.
 - `id` (Primary Key)
 - `kanji`
 - `romaji`
 - `english`
 - `parts` (Required): Word components stored in JSON format

#### groups
- Manages collections of words.
 - `id` (Primary Key)
 - `name` (Required): Name of the group
 - `words_count` (Default: 0): Counter cache for the number of words in the group

#### word_groups
- join-table enabling many-to-many relationship between words and groups.
 - `word_id` (Foreign Key): References -> words.id
 - `group_id` (Foreign Key): References -> groups.id

#### study_activities
- a specific study activity, linking study session to a group
 - `id` (Primary Key)
 - `name` (Required): Name of the activity ("Flashcards", "Quiz")
 - `url` (Required): full URL of the study activity

#### study_sessions
- Records individual study sessions grouping word_review_item
 - `id` (Primary Key): Unique identifier for each session
 - `group_id` (Foreign Key): References -> groups.id
 - `study_activity_id` (Foreign Key): References -> study_activities.id
 - `created_at` (Default: Current Time): When the session was created

#### word_review_items
- Tracks individual word reviews within study sessions. Record of word practice, determining if word was correct or not
 - `id` (Primary Key): Unique identifier for each review
 - `word_id` (Foreign Key): References -> words.id
 - `study_session_id` (Foreign Key): References -> study_sessions.id
 - `correct` (Boolean, Required): Whether the answer was correct
 - `created_at` (Default: Current Time): When the review occurred

#### Relationships

- word belongs to groups through  word_groups
- group belongs to words through word_groups
- session belongs to a group
- session belongs to a study_activity
- session has many word_review_items
- word_review_item belongs to a study_session
- word_review_item belongs to a word

#### Design Notes
- All tables use auto-incrementing primary keys
- Timestamps are automatically set on creation where applicable
- Foreign key constraints maintain referential integrity
- JSON storage for word parts allows flexible component storage
- Counter cache on groups.words_count optimizes word counting queries

