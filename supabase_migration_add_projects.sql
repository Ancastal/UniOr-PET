-- Migration Script: Add Project File Upload Support
-- Run this script on existing Supabase databases to add project and file management features
-- This is safe to run multiple times (uses IF NOT EXISTS)

-- Step 1: Add project_key column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS project_key TEXT;

-- Step 2: Create index for project_key lookups
CREATE INDEX IF NOT EXISTS idx_users_project_key ON users(project_key);

-- Step 3: Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id BIGSERIAL PRIMARY KEY,
    project_key TEXT NOT NULL UNIQUE,
    pm_name TEXT NOT NULL,
    pm_surname TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    db_type TEXT,
    db_connection TEXT
);

-- Step 4: Create indexes for projects table
CREATE INDEX IF NOT EXISTS idx_projects_key ON projects(project_key);
CREATE INDEX IF NOT EXISTS idx_projects_pm ON projects(pm_name, pm_surname);

-- Step 5: Create project_files table
CREATE TABLE IF NOT EXISTS project_files (
    id BIGSERIAL PRIMARY KEY,
    project_key TEXT NOT NULL UNIQUE,
    source_filename TEXT NOT NULL,
    translation_filename TEXT NOT NULL,
    source_content TEXT NOT NULL,
    translation_content TEXT NOT NULL,
    line_count INTEGER NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Step 6: Create index for project_files table
CREATE INDEX IF NOT EXISTS idx_project_files_key ON project_files(project_key);

-- Migration complete!
-- Note: Existing users will have project_key = NULL, which is fine for backward compatibility
