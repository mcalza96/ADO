-- Migration: 026_add_contractor_type
-- Date: 2025-12-05
-- Description: Agrega columna contractor_type a la tabla contractors para diferenciar
--              entre tipos de proveedores (TRANSPORT, DISPOSAL, etc.)
--              Todos los contratistas existentes se marcan como TRANSPORT.
--
-- Author: ADO ERP Team

PRAGMA foreign_keys = ON;

-- ==========================================
-- AGREGAR COLUMNA contractor_type
-- ==========================================

-- Agregar columna con valor default 'TRANSPORT' para datos existentes
ALTER TABLE contractors ADD COLUMN contractor_type TEXT DEFAULT 'TRANSPORT' 
    CHECK (contractor_type IN ('TRANSPORT', 'DISPOSAL', 'SERVICES', 'MECHANICS'));

-- Actualizar todos los registros existentes (por si el DEFAULT no aplica retroactivamente)
UPDATE contractors SET contractor_type = 'TRANSPORT' WHERE contractor_type IS NULL;

-- ==========================================
-- ÍNDICES PARA BÚSQUEDAS POR TIPO
-- ==========================================

-- Índice para filtrar contratistas por tipo
CREATE INDEX IF NOT EXISTS idx_contractors_type ON contractors(contractor_type);

-- Índice compuesto para filtrar por tipo y estado activo
CREATE INDEX IF NOT EXISTS idx_contractors_type_active ON contractors(contractor_type, is_active);
