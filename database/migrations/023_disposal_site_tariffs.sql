-- Migration: 023_disposal_site_tariffs
-- Date: 2025-12-05
-- Description: Agrega tabla de tarifas de sitios de disposición (costos a pagar al contratista del sitio)
--              Estos son COSTOS para la empresa, no ingresos (a diferencia de client_tariffs)
--              Ejemplo: Sitio Vertedero Loma Negra cobra 0.24 UF/tonelada por recibir residuos
--
-- Principio: UF-First. Todas las tarifas en UF.
-- Author: ADO Financial Module

PRAGMA foreign_keys = ON;

-- ==========================================
-- TABLA: disposal_site_tariffs
-- ==========================================
-- Tarifas que el sitio de disposición cobra por recibir los residuos
-- Es un COSTO para la empresa (salida de dinero)

CREATE TABLE IF NOT EXISTS disposal_site_tariffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Sitio de disposición que cobra
    site_id INTEGER NOT NULL,
    
    -- Tarifa en UF por tonelada
    -- Ejemplo: 0.24 UF/ton para disposición estándar
    rate_uf REAL NOT NULL CHECK (rate_uf > 0),
    
    -- Peso mínimo garantizado (toneladas)
    -- Si el camión llega con menos de este peso, se cobra como si trajera el mínimo
    min_weight_guaranteed REAL DEFAULT 0 CHECK (min_weight_guaranteed >= 0),
    
    -- Vigencia de la tarifa
    valid_from DATE NOT NULL,
    valid_to DATE, -- NULL = vigente indefinidamente
    
    -- Audit fields
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
);

-- Índices para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_disposal_site_tariffs_site 
ON disposal_site_tariffs(site_id);

CREATE INDEX IF NOT EXISTS idx_disposal_site_tariffs_validity 
ON disposal_site_tariffs(site_id, valid_from, valid_to);

-- Índice parcial para tarifas activas (sin fecha fin)
CREATE INDEX IF NOT EXISTS idx_disposal_site_tariffs_active 
ON disposal_site_tariffs(site_id) 
WHERE valid_to IS NULL;

-- ==========================================
-- DATOS INICIALES (opcional, comentar si no se necesitan)
-- ==========================================
-- INSERT INTO disposal_site_tariffs (site_id, rate_uf, min_weight_guaranteed, valid_from)
-- SELECT id, 0.24, 0, DATE('2025-01-01')
-- FROM sites 
-- WHERE is_active = 1;
