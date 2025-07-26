-- AI_analyst Database Initialization Script

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS ai_analyst;

-- Connect to the database
\c ai_analyst;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS monitoring;
CREATE SCHEMA IF NOT EXISTS audit;

-- Set default privileges
GRANT ALL PRIVILEGES ON DATABASE ai_analyst TO ai_analyst_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO ai_analyst_user;
GRANT ALL PRIVILEGES ON SCHEMA monitoring TO ai_analyst_user;
GRANT ALL PRIVILEGES ON SCHEMA audit TO ai_analyst_user;

-- Create audit table for tracking changes
CREATE TABLE IF NOT EXISTS audit.audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    user_id VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create monitoring tables
CREATE TABLE IF NOT EXISTS monitoring.performance_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    tags JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS monitoring.api_requests (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms DECIMAL(10,4) NOT NULL,
    user_agent TEXT,
    ip_address INET,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit.audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_table_name ON audit.audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON monitoring.performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON monitoring.performance_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_api_requests_timestamp ON monitoring.api_requests(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_requests_endpoint ON monitoring.api_requests(endpoint);

-- Grant permissions on monitoring tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA monitoring TO ai_analyst_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA monitoring TO ai_analyst_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audit TO ai_analyst_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA audit TO ai_analyst_user;

-- Create function for automatic audit logging
CREATE OR REPLACE FUNCTION audit.audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit.audit_log (table_name, operation, old_data)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit.audit_log (table_name, operation, old_data, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit.audit_log (table_name, operation, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Set timezone
SET timezone = 'UTC';

-- Optimize PostgreSQL settings for AI workloads
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Reload configuration
SELECT pg_reload_conf();

COMMIT;