-- Initial schema

CREATE TABLE IF NOT EXISTS user_state (
    user_id BIGINT PRIMARY KEY,
    current_day INTEGER DEFAULT 1,
    current_mode TEXT DEFAULT 'study',
    voice_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS study_progress (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    day_number INTEGER NOT NULL,
    status TEXT DEFAULT 'not_started',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    UNIQUE(user_id, day_number)
);

CREATE TABLE IF NOT EXISTS review_notes (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    day_number INTEGER,
    topic TEXT NOT NULL,
    note TEXT,
    priority TEXT DEFAULT 'medium',
    reviewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vocabulary (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    word TEXT NOT NULL,
    times_practiced INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    last_practiced TIMESTAMPTZ,
    next_review TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, word)
);

CREATE TABLE IF NOT EXISTS grammar_topics (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    topic TEXT NOT NULL,
    times_practiced INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    last_practiced TIMESTAMPTZ,
    next_review TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, topic)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_study_progress_user ON study_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_review_notes_user ON review_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_vocabulary_user_review ON vocabulary(user_id, next_review);
CREATE INDEX IF NOT EXISTS idx_grammar_user_review ON grammar_topics(user_id, next_review);
