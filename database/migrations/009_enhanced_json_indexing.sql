-- Migration 009: Enhanced JSON Indexing with Generated Columns
-- Optimiza consultas sobre datos JSON críticos en loads y treatment_batches

-- ==================================================
-- LOADS TABLE - Generated Columns for Common Queries
-- ==================================================

-- Lab Analysis Results (VR-09 Compliance)
ALTER TABLE loads ADD COLUMN ph_final REAL 
GENERATED ALWAYS AS (json_extract(attributes, '$.lab_analysis_result.ph')) VIRTUAL;

ALTER TABLE loads ADD COLUMN moisture_percent REAL
GENERATED ALWAYS AS (json_extract(attributes, '$.lab_analysis_result.moisture_percent')) VIRTUAL;

ALTER TABLE loads ADD COLUMN nitrate_no3 REAL
GENERATED ALWAYS AS (json_extract(attributes, '$.lab_analysis_result.nitrate_no3')) VIRTUAL;

ALTER TABLE loads ADD COLUMN ammonium_nh4 REAL
GENERATED ALWAYS AS (json_extract(attributes, '$.lab_analysis_result.ammonium_nh4')) VIRTUAL;

-- Odometer readings for distance tracking
ALTER TABLE loads ADD COLUMN odometer_departure INTEGER
GENERATED ALWAYS AS (json_extract(attributes, '$.odometer_departure')) VIRTUAL;

ALTER TABLE loads ADD COLUMN odometer_arrival INTEGER
GENERATED ALWAYS AS (json_extract(attributes, '$.odometer_arrival')) VIRTUAL;

-- Temperature monitoring (critical for compliance)
ALTER TABLE loads ADD COLUMN temperature_arrival REAL
GENERATED ALWAYS AS (json_extract(attributes, '$.temperature_arrival')) VIRTUAL;

-- DO-04 Field conditions
ALTER TABLE loads ADD COLUMN soil_moisture_percent REAL
GENERATED ALWAYS AS (json_extract(attributes, '$.field_conditions.soil_moisture_percent')) VIRTUAL;

ALTER TABLE loads ADD COLUMN wind_speed_kmh REAL
GENERATED ALWAYS AS (json_extract(attributes, '$.field_conditions.wind_speed_kmh')) VIRTUAL;

-- ==================================================
-- TREATMENT_BATCHES TABLE - Process Control
-- ==================================================

-- TTO-03 Calibration results
ALTER TABLE treatment_batches ADD COLUMN ph_initial REAL
GENERATED ALWAYS AS (json_extract(attributes, '$.calibration.ph_initial')) VIRTUAL;

ALTER TABLE treatment_batches ADD COLUMN ph_target REAL
GENERATED ALWAYS AS (json_extract(attributes, '$.calibration.ph_target')) VIRTUAL;

ALTER TABLE treatment_batches ADD COLUMN lime_dose_kg REAL
GENERATED ALWAYS AS (json_extract(attributes, '$.calibration.lime_dose_kg')) VIRTUAL;

-- Equipment logs (machine hours)
ALTER TABLE treatment_batches ADD COLUMN mixer_hours REAL
GENERATED ALWAYS AS (json_extract(attributes, '$.equipment_logs.mixer_hours')) VIRTUAL;

-- ==================================================
-- PERFORMANCE INDEXES
-- ==================================================

-- Critical compliance queries
CREATE INDEX IF NOT EXISTS idx_loads_ph_final ON loads(ph_final) WHERE ph_final IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_loads_moisture ON loads(moisture_percent) WHERE moisture_percent IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_loads_nitrate ON loads(nitrate_no3) WHERE nitrate_no3 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_loads_temperature ON loads(temperature_arrival) WHERE temperature_arrival IS NOT NULL;

-- Distance/Cost analysis
CREATE INDEX IF NOT EXISTS idx_loads_odometer_departure ON loads(odometer_departure) WHERE odometer_departure IS NOT NULL;

-- Weather compliance (DO-04)
CREATE INDEX IF NOT EXISTS idx_loads_soil_moisture ON loads(soil_moisture_percent) WHERE soil_moisture_percent IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_loads_wind_speed ON loads(wind_speed_kmh) WHERE wind_speed_kmh IS NOT NULL;

-- Process control queries
CREATE INDEX IF NOT EXISTS idx_batches_ph_initial ON treatment_batches(ph_initial) WHERE ph_initial IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_batches_lime_dose ON treatment_batches(lime_dose_kg) WHERE lime_dose_kg IS NOT NULL;

-- ==================================================
-- COMPOSITE INDEXES for Common Queries
-- ==================================================

-- "Find all loads with pH outside acceptable range in last month"
CREATE INDEX IF NOT EXISTS idx_loads_ph_date ON loads(ph_final, created_at) 
WHERE ph_final IS NOT NULL;

-- "Track moisture trends by site"
CREATE INDEX IF NOT EXISTS idx_loads_moisture_site ON loads(destination_site_id, moisture_percent, created_at)
WHERE moisture_percent IS NOT NULL;

-- "Analyze lime usage efficiency by batch"
CREATE INDEX IF NOT EXISTS idx_batches_lime_ph ON treatment_batches(lime_dose_kg, ph_initial, ph_target)
WHERE lime_dose_kg IS NOT NULL;

-- ==================================================
-- NOTES
-- ==================================================
-- Benefits:
-- 1. Native SQL speed for JSON queries (no LIKE '%...%')
-- 2. Maintains schema flexibility (JSON still primary source)
-- 3. WHERE clauses exclude NULL values to save index space
-- 4. VIRTUAL columns = no storage overhead (computed on-the-fly)
--
-- Usage examples:
-- SELECT * FROM loads WHERE ph_final BETWEEN 6.0 AND 9.0;
-- SELECT AVG(moisture_percent) FROM loads WHERE destination_site_id = 5;
-- SELECT * FROM loads WHERE wind_speed_kmh > 30 AND created_at > date('now', '-7 days');
