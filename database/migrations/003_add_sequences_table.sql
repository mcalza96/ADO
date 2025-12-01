-- Create sequences table for safe concurrent code generation
CREATE TABLE IF NOT EXISTS sequences (
    name TEXT PRIMARY KEY,
    current_value INTEGER DEFAULT 0
);

-- Initialize manifest_code sequence if it doesn't exist
INSERT OR IGNORE INTO sequences (name, current_value) VALUES ('manifest_code', 0);
