-- Migration: Add is_link_point field to facilities
-- Date: 2025-12-05
-- Description: Allows marking certain client facilities as link points
--              These facilities can act as intermediate stops (origin -> link_facility -> final_dest)

-- Add is_link_point column to facilities table
-- This allows client facilities to serve as intermediate transfer points
ALTER TABLE facilities ADD COLUMN is_link_point INTEGER DEFAULT 0 CHECK (is_link_point IN (0, 1));

-- Create index for quick lookups of link points
CREATE INDEX IF NOT EXISTS idx_facilities_link_point ON facilities(is_link_point) WHERE is_link_point = 1;
