-- Phase 0-4 Tables Creation Script
-- Execute this directly in Railway PostgreSQL

-- Create insights table
CREATE TABLE IF NOT EXISTS insights (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    evaluation_id INTEGER REFERENCES evaluations(id),
    insight_type VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    metrics JSONB,
    suggested_actions JSONB,
    is_read BOOLEAN NOT NULL DEFAULT false,
    is_resolved BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    deleted_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_insights_company_id ON insights(company_id);
CREATE INDEX IF NOT EXISTS ix_insights_deleted_at ON insights(deleted_at);

-- Create tags table
CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    category VARCHAR NOT NULL DEFAULT 'general',
    color VARCHAR NOT NULL DEFAULT '#6b7280',
    company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    is_active BOOLEAN NOT NULL DEFAULT true
);

-- Create evaluation_tags table
CREATE TABLE IF NOT EXISTS evaluation_tags (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER NOT NULL REFERENCES evaluations(id),
    tag_id INTEGER NOT NULL REFERENCES tags(id),
    auto_tagged BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Create alert_thresholds table
CREATE TABLE IF NOT EXISTS alert_thresholds (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    metric_name VARCHAR NOT NULL,
    condition VARCHAR NOT NULL,
    threshold_value FLOAT NOT NULL,
    threshold_value_max FLOAT,
    alert_severity VARCHAR NOT NULL DEFAULT 'medium',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Create trends table
CREATE TABLE IF NOT EXISTS trends (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    metric_name VARCHAR NOT NULL,
    period VARCHAR NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    average_value FLOAT NOT NULL,
    min_value FLOAT NOT NULL,
    max_value FLOAT NOT NULL,
    sample_count INTEGER NOT NULL,
    trend_direction VARCHAR,
    trend_metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Create prompts table
CREATE TABLE IF NOT EXISTS prompts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    template TEXT NOT NULL,
    category VARCHAR NOT NULL,
    variables JSONB NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    version INTEGER NOT NULL DEFAULT 1,
    company_id INTEGER REFERENCES companies(id),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_prompts_category ON prompts(category);

-- Create widget_definitions table
CREATE TABLE IF NOT EXISTS widget_definitions (
    id SERIAL PRIMARY KEY,
    widget_type VARCHAR NOT NULL,
    widget_name VARCHAR NOT NULL,
    description TEXT NOT NULL,
    data_source VARCHAR NOT NULL,
    default_config JSONB,
    available_for_roles JSONB NOT NULL,
    category VARCHAR NOT NULL DEFAULT 'general',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Create dashboard_configs table
CREATE TABLE IF NOT EXISTS dashboard_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    layout_config JSONB NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT false,
    config_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    deleted_at TIMESTAMP
);

-- Create company_themes table
CREATE TABLE IF NOT EXISTS company_themes (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    primary_color VARCHAR(7) NOT NULL,
    secondary_color VARCHAR(7) NOT NULL,
    accent_color VARCHAR(7) NOT NULL,
    logo_url TEXT,
    favicon_url TEXT,
    custom_css TEXT,
    font_family VARCHAR,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_company_themes_company_id ON company_themes(company_id);

-- Insert default widget definitions
INSERT INTO widget_definitions (widget_type, widget_name, description, data_source, available_for_roles, category)
VALUES 
    ('metric', 'Total Evaluations', 'Shows total number of evaluations', 'evaluations', '["admin", "manager"]', 'metrics'),
    ('chart', 'Satisfaction Trend', 'Line chart showing satisfaction over time', 'evaluations', '["admin", "manager"]', 'charts'),
    ('list', 'Recent Evaluations', 'List of most recent evaluations', 'evaluations', '["admin", "manager", "shopper"]', 'lists')
ON CONFLICT DO NOTHING;

-- Verification query
SELECT 
    'insights' as table_name, COUNT(*) as count FROM insights
UNION ALL
SELECT 'tags', COUNT(*) FROM tags
UNION ALL
SELECT 'prompts', COUNT(*) FROM prompts
UNION ALL
SELECT 'widget_definitions', COUNT(*) FROM widget_definitions
UNION ALL
SELECT 'dashboard_configs', COUNT(*) FROM dashboard_configs
UNION ALL
SELECT 'company_themes', COUNT(*) FROM company_themes;
