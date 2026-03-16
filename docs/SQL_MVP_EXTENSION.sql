-- ============================================
-- MVP Extension: Transcript Segments & Metadata
-- Run this script on your PostgreSQL database
-- ============================================

-- 1. Create transcript_segments table
CREATE TABLE IF NOT EXISTS transcript_segments (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    text TEXT NOT NULL,
    speaker VARCHAR(100),
    confidence FLOAT,
    embedding_json TEXT,  -- JSON array for embeddings (temporary until pgvector)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups by evaluation
CREATE INDEX IF NOT EXISTS idx_transcript_segments_evaluation_id ON transcript_segments(evaluation_id);

-- Create index for text search
CREATE INDEX IF NOT EXISTS idx_transcript_segments_text_search ON transcript_segments USING gin(to_tsvector('spanish', text));

-- 2. Add new metadata columns to evaluations table
-- Location/Branch info
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS country VARCHAR(100);
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS branch_id VARCHAR(100);
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS branch_name VARCHAR(255);

-- Interaction details
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS interaction_type VARCHAR(50) DEFAULT 'presencial';
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS interaction_date DATE;
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS interaction_duration INTEGER;

-- Customer info
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS customer_segment VARCHAR(100);
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS product_consulted VARCHAR(255);

-- AI-extracted fields
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS customer_emotion VARCHAR(100);
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS agent_emotion VARCHAR(100);
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS problem_resolved BOOLEAN;
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS product_offered BOOLEAN;
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS risk_of_churn INTEGER;
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS service_quality_score INTEGER;
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS customer_effort_score INTEGER;
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS nps_inferred INTEGER;
ALTER TABLE evaluations ADD COLUMN IF NOT EXISTS greeting_detected BOOLEAN;

-- Create indexes for common filter columns
CREATE INDEX IF NOT EXISTS idx_evaluations_branch_id ON evaluations(branch_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_country ON evaluations(country);
CREATE INDEX IF NOT EXISTS idx_evaluations_interaction_date ON evaluations(interaction_date);
CREATE INDEX IF NOT EXISTS idx_evaluations_interaction_type ON evaluations(interaction_type);

-- ============================================
-- Verification queries
-- ============================================

-- Check transcript_segments table exists
SELECT 'transcript_segments table created' AS status 
FROM information_schema.tables 
WHERE table_name = 'transcript_segments';

-- Check new columns in evaluations
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'evaluations' 
AND column_name IN ('country', 'branch_id', 'customer_emotion', 'nps_inferred');

-- ============================================
-- OPTIONAL: Enable pgvector (when ready)
-- ============================================
-- Uncomment these lines when you want to enable semantic search

-- CREATE EXTENSION IF NOT EXISTS vector;
-- ALTER TABLE transcript_segments ADD COLUMN embedding vector(1536);
-- CREATE INDEX IF NOT EXISTS idx_transcript_segments_embedding ON transcript_segments USING ivfflat (embedding vector_cosine_ops);
