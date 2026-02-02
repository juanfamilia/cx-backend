-- SQL Script to create clips tables
-- Run this manually in your PostgreSQL database

-- Create clip_configs table
CREATE TABLE IF NOT EXISTS clip_configs (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    critical_before INTEGER NOT NULL DEFAULT 10,
    critical_after INTEGER NOT NULL DEFAULT 20,
    negative_before INTEGER NOT NULL DEFAULT 5,
    negative_after INTEGER NOT NULL DEFAULT 15,
    positive_before INTEGER NOT NULL DEFAULT 5,
    positive_after INTEGER NOT NULL DEFAULT 10,
    max_clip_duration INTEGER NOT NULL DEFAULT 60,
    max_clips_delivered INTEGER NOT NULL DEFAULT 5,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_clip_configs_company_id ON clip_configs(company_id);

-- Create clips table
CREATE TABLE IF NOT EXISTS clips (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER NOT NULL REFERENCES evaluations(id),
    cloudflare_uid VARCHAR,
    stream_url VARCHAR,
    thumbnail_url VARCHAR,
    verbatim_type VARCHAR NOT NULL,
    verbatim_text TEXT NOT NULL,
    verbatim_origin VARCHAR NOT NULL DEFAULT 'cliente',
    original_timestamp INTEGER NOT NULL,
    clip_start INTEGER NOT NULL,
    clip_end INTEGER NOT NULL,
    clip_duration INTEGER NOT NULL,
    priority_score FLOAT NOT NULL DEFAULT 0.0,
    priority_rank INTEGER,
    is_delivered BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR NOT NULL DEFAULT 'pending',
    error_message TEXT,
    extra_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_clips_evaluation_id ON clips(evaluation_id);
CREATE INDEX IF NOT EXISTS ix_clips_status ON clips(status);
CREATE INDEX IF NOT EXISTS ix_clips_verbatim_type ON clips(verbatim_type);
CREATE INDEX IF NOT EXISTS ix_clips_is_delivered ON clips(is_delivered);

-- Verify tables were created
SELECT 'clip_configs created' AS status WHERE EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'clip_configs');
SELECT 'clips created' AS status WHERE EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'clips');
