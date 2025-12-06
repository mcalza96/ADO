-- ============================================================================
-- Migration 005: Machine Logs Table
-- ============================================================================
-- Description: 
--   Crear tabla para registros de trabajo de maquinaria pesada.
--   Soporta trazabilidad, mantenimiento preventivo, y costeo.
--
-- Fecha: 2025-12-02
-- Fase: 2 - Motor de Estados y Maquinaria
-- ============================================================================

-- Crear tabla machine_logs
CREATE TABLE IF NOT EXISTS machine_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id INTEGER NOT NULL,
    date DATETIME NOT NULL,
    operator_id INTEGER NOT NULL,
    site_id INTEGER NOT NULL,
    
    -- Horómetros (horas motor)
    start_hourmeter REAL NOT NULL,
    end_hourmeter REAL NOT NULL,
    
    -- Total de horas (calculado automáticamente)
    -- SQLite: Columna generada disponible desde versión 3.31.0+
    total_hours REAL GENERATED ALWAYS AS (end_hourmeter - start_hourmeter) STORED,
    
    -- Actividades realizadas (JSON array)
    -- Ejemplo: '[{"task": "Excavación", "plot_id": 5}, {"task": "Nivelación", "plot_id": 6}]'
    activities TEXT,
    
    -- Auditoría
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id INTEGER,
    
    -- Relaciones
    FOREIGN KEY (machine_id) REFERENCES vehicles(id),
    FOREIGN KEY (operator_id) REFERENCES drivers(id),
    FOREIGN KEY (site_id) REFERENCES sites(id),
    FOREIGN KEY (created_by_user_id) REFERENCES users(id),
    
    -- Constraint: El horómetro final debe ser mayor al inicial
    CHECK (end_hourmeter > start_hourmeter)
);

-- Índices para optimizar consultas comunes
CREATE INDEX IF NOT EXISTS idx_machine_logs_machine_id 
    ON machine_logs(machine_id);

CREATE INDEX IF NOT EXISTS idx_machine_logs_date 
    ON machine_logs(date);

CREATE INDEX IF NOT EXISTS idx_machine_logs_site_id 
    ON machine_logs(site_id);

-- Índice compuesto para consulta de último registro por máquina
CREATE INDEX IF NOT EXISTS idx_machine_logs_machine_date_desc 
    ON machine_logs(machine_id, date DESC, end_hourmeter DESC);

-- ============================================================================
-- Verificación
-- ============================================================================
-- Para verificar que la migración se aplicó correctamente, ejecutar:
-- 
-- sqlite3 ado_system.db "PRAGMA table_info(machine_logs);"
-- 
-- Salida esperada: Debe mostrar todas las columnas incluyendo total_hours
-- ============================================================================
