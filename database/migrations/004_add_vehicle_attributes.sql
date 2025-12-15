-- Migration: Add Vehicle Attributes (Heavy Equipment Support)
-- Extracted from legacy migration 004
-- Date: 2025-12-06

-- 3. Agregar soporte para maquinaria pesada a vehicles
-- asset_type: Clasificación del activo (ROAD_VEHICLE o HEAVY_EQUIPMENT)
ALTER TABLE vehicles ADD COLUMN asset_type TEXT DEFAULT 'ROAD_VEHICLE';

-- current_odometer: Kilometraje actual (para vehículos de carretera)
ALTER TABLE vehicles ADD COLUMN current_odometer INTEGER;

-- current_hourmeter: Horómetro actual en horas (para maquinaria pesada)
ALTER TABLE vehicles ADD COLUMN current_hourmeter REAL;

-- cost_per_km: Costo por kilómetro de operación
ALTER TABLE vehicles ADD COLUMN cost_per_km REAL;

-- cost_per_hour: Costo por hora de operación
ALTER TABLE vehicles ADD COLUMN cost_per_hour REAL;

-- attributes: Datos variables del vehículo/maquinaria
-- Ejemplos: última mantención, próximo service, configuraciones específicas, etc.
ALTER TABLE vehicles ADD COLUMN attributes TEXT;
