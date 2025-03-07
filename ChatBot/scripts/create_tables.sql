-- Create Students table
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP,
    total_sessions INTEGER DEFAULT 0,
    total_correct INTEGER DEFAULT 0,
    total_incorrect INTEGER DEFAULT 0
);

-- Create Words table
CREATE TABLE IF NOT EXISTS words (
    word_id TEXT PRIMARY KEY,
    hindi_word TEXT NOT NULL,
    difficulty_level INTEGER,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

-- Create Synonyms table (without embeddings - these go to ChromaDB)
CREATE TABLE IF NOT EXISTS synonyms (
    synonym_id TEXT PRIMARY KEY,
    word_id TEXT NOT NULL,
    synonym TEXT NOT NULL,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (word_id) REFERENCES words(word_id),
    UNIQUE(word_id, synonym)
);

-- Create Learning History table
CREATE TABLE IF NOT EXISTS learning_history (
    history_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    word_id TEXT NOT NULL,
    student_answer TEXT,
    is_correct BOOLEAN,
    attempt_count INTEGER DEFAULT 1,
    session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hints_used INTEGER DEFAULT 0,
    response_time_seconds INTEGER,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (word_id) REFERENCES words(word_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_word_category ON words(category);
CREATE INDEX IF NOT EXISTS idx_learning_history_session ON learning_history(session_id);
CREATE INDEX IF NOT EXISTS idx_student_last_active ON students(last_active);

-- Create view for student performance analytics
CREATE VIEW IF NOT EXISTS student_performance AS
SELECT 
    s.student_id,
    s.name,
    COUNT(DISTINCT lh.session_id) as total_sessions,
    SUM(CASE WHEN lh.is_correct THEN 1 ELSE 0 END) as correct_answers,
    AVG(lh.response_time_seconds) as avg_response_time
FROM students s
LEFT JOIN learning_history lh ON s.student_id = lh.student_id
GROUP BY s.student_id, s.name; 