-- Migration: Load Status History
-- Purpose: Create table to track status transitions for full traceability and SLA measurement
-- Date: 2025-12-02

-- Create load_status_history table
CREATE TABLE IF NOT EXISTS load_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    load_id INTEGER NOT NULL,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    notes TEXT,
    
    FOREIGN KEY (load_id) REFERENCES loads(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_load_status_history_load_id 
    ON load_status_history(load_id);

CREATE INDEX IF NOT EXISTS idx_load_status_history_timestamp 
    ON load_status_history(timestamp);

CREATE INDEX IF NOT EXISTS idx_load_status_history_to_status 
    ON load_status_history(to_status);

-- Insert comment/documentation
-- This table enables:
-- 1. Full audit trail of load lifecycle
-- 2. SLA calculation (time in each status)
-- 3. Bottleneck analysis
-- 4. Compliance reporting
