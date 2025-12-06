-- Add financial_status column to loads table
ALTER TABLE loads ADD COLUMN financial_status TEXT DEFAULT 'OPEN';

-- Update existing loads based on their operational status
-- If COMPLETED, set to OPEN (ready for processing)
-- If CANCELLED, set to OPEN (or maybe ignore, but keep schema consistent)
-- We default to OPEN, which is safe.
