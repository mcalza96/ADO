-- Migration: 027_create_proformas_table
-- Date: 2025-12-05
-- Description: Crea la tabla maestra de proformas (estados de pago)
--              Migra datos existentes de economic_indicators
--              
-- Nomenclatura Proformas:
--   - PROF YY-MM: Período del 19 del mes anterior al 18 del mes indicado
--   - Ejemplo: PROF 25-03 = 19-Feb-2025 a 18-Mar-2025
--
-- Author: Senior Database Architect

PRAGMA foreign_keys = ON;

-- ==========================================
-- PASO 1: CREAR TABLA proformas
-- ==========================================

CREATE TABLE IF NOT EXISTS proformas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Código único de la proforma (ej: "PROF 25-03")
    proforma_code TEXT NOT NULL UNIQUE,
    
    -- Identificador de periodo
    period_year INTEGER NOT NULL CHECK (period_year >= 2020 AND period_year <= 2100),
    period_month INTEGER NOT NULL CHECK (period_month >= 1 AND period_month <= 12),
    
    -- Fechas del ciclo operacional (19 al 18)
    cycle_start_date DATE NOT NULL,
    cycle_end_date DATE NOT NULL,
    
    -- Indicadores financieros principales
    -- UF: Valor de la Unidad de Fomento al día 18 del ciclo (en CLP)
    uf_value REAL NOT NULL CHECK (uf_value > 0),
    
    -- Precio promedio del petróleo/diésel en el período (en CLP/litro)
    fuel_price REAL NOT NULL CHECK (fuel_price > 0),
    
    -- Estado del periodo: 0 = abierto/editable, 1 = cerrado/inmutable
    is_closed INTEGER NOT NULL DEFAULT 0 CHECK (is_closed IN (0, 1)),
    
    -- Campo JSONB para indicadores adicionales futuros
    -- Ejemplos: {"costo_area_central": 1500000, "ipc": 0.3, "dolar": 950}
    extra_indicators TEXT DEFAULT '{}',
    
    -- Campos de auditoría
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CHECK (cycle_end_date > cycle_start_date),
    UNIQUE(period_year, period_month)
);

-- Índices para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_proformas_period 
ON proformas(period_year, period_month);

CREATE INDEX IF NOT EXISTS idx_proformas_code 
ON proformas(proforma_code);

CREATE INDEX IF NOT EXISTS idx_proformas_dates 
ON proformas(cycle_start_date, cycle_end_date);

CREATE INDEX IF NOT EXISTS idx_proformas_open 
ON proformas(is_closed)
WHERE is_closed = 0;

-- ==========================================
-- PASO 2: MIGRAR DATOS DE economic_indicators
-- ==========================================

-- Migrar registros existentes de economic_indicators a proformas
-- period_key tiene formato 'YYYY-MM', extraemos year y month
INSERT OR IGNORE INTO proformas (
    proforma_code,
    period_year,
    period_month,
    cycle_start_date,
    cycle_end_date,
    uf_value,
    fuel_price,
    is_closed,
    extra_indicators,
    created_at,
    updated_at
)
SELECT 
    'PROF ' || SUBSTR(period_key, 3, 2) || '-' || SUBSTR(period_key, 6, 2) AS proforma_code,
    CAST(SUBSTR(period_key, 1, 4) AS INTEGER) AS period_year,
    CAST(SUBSTR(period_key, 6, 2) AS INTEGER) AS period_month,
    cycle_start_date,
    cycle_end_date,
    uf_value,
    fuel_price,
    CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END AS is_closed,
    '{}' AS extra_indicators,
    created_at,
    updated_at
FROM economic_indicators
WHERE period_key LIKE '____-__';

-- ==========================================
-- PASO 3: CREAR TRIGGER PARA updated_at
-- ==========================================

DROP TRIGGER IF EXISTS trg_proformas_updated_at;
CREATE TRIGGER trg_proformas_updated_at
AFTER UPDATE ON proformas
FOR EACH ROW
BEGIN
    UPDATE proformas 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- ==========================================
-- PASO 4: CREAR VISTA DE COMPATIBILIDAD
-- ==========================================
-- Vista para mantener compatibilidad con código que use economic_indicators
-- Permite que consultas antiguas sigan funcionando

DROP VIEW IF EXISTS v_economic_indicators;
CREATE VIEW v_economic_indicators AS
SELECT 
    id,
    period_year || '-' || 
        CASE WHEN period_month < 10 THEN '0' || CAST(period_month AS TEXT) 
             ELSE CAST(period_month AS TEXT) END AS period_key,
    period_year,
    period_month,
    uf_value,
    fuel_price AS monthly_fuel_price,
    fuel_price,
    is_closed,
    CASE WHEN is_closed = 1 THEN 'CLOSED' ELSE 'OPEN' END AS status,
    cycle_start_date,
    cycle_end_date,
    created_at,
    updated_at
FROM proformas;
