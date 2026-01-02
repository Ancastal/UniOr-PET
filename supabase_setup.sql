-- UniOr-PET Supabase Database Setup
-- Run this script in your Supabase SQL Editor to create the necessary tables

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'translator',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    db_type TEXT,
    db_connection TEXT,
    UNIQUE(name, surname)
);

-- Create user_progress table
CREATE TABLE IF NOT EXISTS user_progress (
    id BIGSERIAL PRIMARY KEY,
    user_name TEXT NOT NULL,
    user_surname TEXT NOT NULL,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metrics JSONB,
    full_text JSONB,
    time_tracker JSONB,
    timer_mode TEXT,
    UNIQUE(user_name, user_surname)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_name_surname ON users(name, surname);
CREATE INDEX IF NOT EXISTS idx_user_progress_name_surname ON user_progress(user_name, user_surname);

-- Enable Row Level Security (RLS) - optional but recommended
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;

-- Create policies if you want to enable RLS
-- This is optional and depends on your security requirements

-- Example policy: Users can read their own data
-- CREATE POLICY "Users can view their own data" ON users
--     FOR SELECT
--     USING (true);  -- Adjust based on your authentication setup

-- CREATE POLICY "Users can view their own progress" ON user_progress
--     FOR SELECT
--     USING (true);  -- Adjust based on your authentication setup

-- Example policy: Users can insert/update their own data
-- CREATE POLICY "Users can insert data" ON users
--     FOR INSERT
--     WITH CHECK (true);

-- CREATE POLICY "Users can update their own progress" ON user_progress
--     FOR ALL
--     USING (true);
