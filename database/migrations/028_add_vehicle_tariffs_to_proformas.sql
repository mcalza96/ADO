-- Migration: 028_add_vehicle_tariffs_to_proformas
-- Date: 2025-12-05
-- Description: Agrega columnas de tarifas por tipo de vehículo a la tabla proformas
--              - tariff_batea_uf: Tarifa para vehículos tipo Batea
--              - tariff_ampliroll_uf: Tarifa para Ampliroll simple
--              - tariff_ampliroll_carro_uf: Tarifa para Ampliroll + Carro
--
-- Valores iniciales para proforma base (25-11):
--   - Ampliroll: 0.002962 UF/ton-km
--   - Ampliroll + Carro: 0.001793 UF/ton-km
--   - Batea: 0.001460 UF/ton-km
--
-- Las proformas siguientes calculan sus tarifas usando:
--   tarifa_nueva = tarifa_anterior × (fuel_price_nuevo / fuel_price_anterior)
--
-- Author: Senior Database Architect

PRAGMA foreign_keys = ON;

-- ==========================================
-- PASO 1: AGREGAR COLUMNAS DE TARIFAS
-- ==========================================

-- Tarifa para vehículos tipo Batea (sin contenedores)
-- Precisión: 6 decimales para valores pequeños en UF
ALTER TABLE proformas ADD COLUMN tariff_batea_uf REAL DEFAULT NULL;

-- Tarifa para Ampliroll simple (1-2 contenedores)
ALTER TABLE proformas ADD COLUMN tariff_ampliroll_uf REAL DEFAULT NULL;

-- Tarifa para Ampliroll + Carro (contenedores con carro adicional)
ALTER TABLE proformas ADD COLUMN tariff_ampliroll_carro_uf REAL DEFAULT NULL;

-- ==========================================
-- PASO 2: ACTUALIZAR PROFORMAS EXISTENTES
-- ==========================================

-- Si existe la proforma 25-11, establecer los valores base
UPDATE proformas 
SET tariff_batea_uf = 0.001460,
    tariff_ampliroll_uf = 0.002962,
    tariff_ampliroll_carro_uf = 0.001793
WHERE proforma_code = 'PROF 25-11';

-- ==========================================
-- PASO 3: CREAR ÍNDICE PARA CONSULTAS
-- ==========================================

-- Índice para búsquedas por período (ya existe en creación original)
-- Solo verificamos que existe
CREATE INDEX IF NOT EXISTS idx_proformas_period ON proformas(period_year, period_month);

-- ==========================================
-- VERIFICACIÓN
-- ==========================================

-- Mostrar estructura actualizada
-- SELECT sql FROM sqlite_master WHERE type='table' AND name='proformas';
