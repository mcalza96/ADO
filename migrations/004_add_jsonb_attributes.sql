-- ============================================================================
-- Migration 004: Add JSONB Attributes and Heavy Equipment Support
-- ============================================================================
-- Description: 
--   1. Agrega columna 'attributes' (TEXT/JSON) a loads, treatment_batches y vehicles
--      para soportar almacenamiento flexible de datos variables.
--   2. Agrega campos de maquinaria pesada a vehicles (asset_type, odometer, 
--      hourmeter, cost tracking).
--
-- Fecha: 2025-12-02
-- Fase: 1 - Escalabilidad ERP
-- ============================================================================

-- 1. Agregar columna attributes a loads
-- Permite almacenar datos variables como: temperatura, pH inicial, condiciones climáticas, etc.
ALTER TABLE loads ADD COLUMN attributes TEXT;

-- 2. Agregar columna attributes a treatment_batches
-- Permite almacenar: dosis de cal, tiempo de mezclado, operador, temperatura, etc.
ALTER TABLE treatment_batches ADD COLUMN attributes TEXT;

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

-- ============================================================================
-- Verificación
-- ============================================================================
-- Para verificar que la migración se aplicó correctamente, ejecutar:
-- 
-- sqlite3 database/biosolids.db "PRAGMA table_info(loads);" | grep attributes
-- sqlite3 database/biosolids.db "PRAGMA table_info(treatment_batches);" | grep attributes
-- sqlite3 database/biosolids.db "PRAGMA table_info(vehicles);" | grep -E "asset_type|odometer|hourmeter|cost_per"
-- 
-- Salida esperada: Debe mostrar las nuevas columnas agregadas
-- ============================================================================
