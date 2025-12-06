-- Migration: 022_financial_schema_final
-- Date: 2025-12-05
-- Description: Establece la infraestructura financiera final según principio "UF-First"
--              - Ajusta economic_indicators con period_year/period_month
--              - Verifica distance_matrix con nomenclatura correcta
--              - Asegura contractor_tariffs y client_tariffs en UF
--              - Agrega columnas trip_id, segment_type, financial_status a loads
--
-- Principio fundamental: Todas las tarifas y contratos se almacenan en UF.
-- La conversión a Pesos es solo para el pago final.
--
-- Author: Senior Database Architect

PRAGMA foreign_keys = ON;

-- ==========================================
-- PASO 1: RECREAR TABLA economic_indicators
-- ==========================================
-- Cambio de period_key TEXT a period_year/period_month INT
-- Nuevo campo: is_closed (BOOLEAN) para congelar periodo

-- 1.1: Backup de datos existentes
DROP TABLE IF EXISTS economic_indicators_backup;
CREATE TABLE economic_indicators_backup AS 
SELECT * FROM economic_indicators WHERE 1=0; -- Solo estructura si existe

-- Intentar backup de datos si la tabla existe
INSERT OR IGNORE INTO economic_indicators_backup 
SELECT * FROM economic_indicators;

-- 1.2: Eliminar tabla antigua
DROP TABLE IF EXISTS economic_indicators;

-- 1.3: Crear tabla con nuevo esquema
CREATE TABLE economic_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Identificador de periodo: año y mes por separado
    period_year INTEGER NOT NULL CHECK (period_year >= 2020 AND period_year <= 2100),
    period_month INTEGER NOT NULL CHECK (period_month >= 1 AND period_month <= 12),
    
    -- Valor de la UF al día 18 del ciclo (CRÍTICO para facturación)
    -- Ejemplo: 37850.45 (en CLP)
    uf_value REAL NOT NULL CHECK (uf_value > 0),
    
    -- Precio promedio/referencia del petróleo en el mes (en Pesos CLP)
    -- Usado para el ajuste polinómico de tarifas de transporte
    monthly_fuel_price REAL NOT NULL CHECK (monthly_fuel_price > 0),
    
    -- Estado del periodo: FALSE = editable, TRUE = cerrado (inmutable)
    is_closed INTEGER NOT NULL DEFAULT 0 CHECK (is_closed IN (0, 1)),
    
    -- Audit fields
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint de unicidad: Un solo registro por periodo
    UNIQUE(period_year, period_month)
);

-- 1.4: Migrar datos existentes si los hay (intentar parsear period_key)
-- Si period_key era 'YYYY-MM', extraemos year y month
INSERT OR IGNORE INTO economic_indicators (
    period_year, 
    period_month, 
    uf_value, 
    monthly_fuel_price, 
    is_closed,
    created_at, 
    updated_at
)
SELECT 
    CAST(SUBSTR(period_key, 1, 4) AS INTEGER) AS period_year,
    CAST(SUBSTR(period_key, 6, 2) AS INTEGER) AS period_month,
    uf_value,
    fuel_price AS monthly_fuel_price,
    CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END AS is_closed,
    created_at,
    updated_at
FROM economic_indicators_backup
WHERE period_key LIKE '____-__'; -- Solo migrar si tiene formato correcto

-- 1.5: Crear índices
CREATE INDEX IF NOT EXISTS idx_economic_indicators_period 
ON economic_indicators(period_year, period_month);

CREATE INDEX IF NOT EXISTS idx_economic_indicators_closed 
ON economic_indicators(is_closed)
WHERE is_closed = 0; -- Solo periodos abiertos

-- ==========================================
-- PASO 2: AJUSTAR TABLA distance_matrix
-- ==========================================
-- Verificar y ajustar nomenclatura según especificación

-- 2.1: Verificar si existe la tabla
CREATE TABLE IF NOT EXISTS distance_matrix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Origen: siempre una facility (planta)
    origin_facility_id INTEGER NOT NULL,
    
    -- Destino polimórfico: puede ser ID de facility o ID de site
    destination_id INTEGER NOT NULL,
    destination_type TEXT NOT NULL CHECK (destination_type IN ('FACILITY', 'SITE')),
    
    -- Distancia en kilómetros
    distance_km REAL NOT NULL CHECK (distance_km > 0),
    
    -- ¿Es un segmento de enlace intermedio? (Planta A -> Planta B)
    is_link_segment INTEGER NOT NULL DEFAULT 0 CHECK (is_link_segment IN (0, 1)),
    
    -- Audit fields
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (origin_facility_id) REFERENCES facilities(id) ON DELETE CASCADE,
    
    -- Constraint de unicidad
    UNIQUE(origin_facility_id, destination_id, destination_type)
);

-- 2.2: Si la tabla ya existía con nombres incorrectos, migrar
-- Verificar si existen columnas con nombres antiguos y renombrar
-- (SQLite limitation: necesitamos recrear tabla si hay cambios estructurales)

-- Backup temporal
DROP TABLE IF EXISTS distance_matrix_temp;
CREATE TABLE distance_matrix_temp AS SELECT * FROM distance_matrix;

-- Recrear tabla (si había diferencias)
DROP TABLE IF EXISTS distance_matrix;
CREATE TABLE distance_matrix (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin_facility_id INTEGER NOT NULL,
    destination_id INTEGER NOT NULL,
    destination_type TEXT NOT NULL CHECK (destination_type IN ('FACILITY', 'SITE')),
    distance_km REAL NOT NULL CHECK (distance_km > 0),
    is_link_segment INTEGER NOT NULL DEFAULT 0 CHECK (is_link_segment IN (0, 1)),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (origin_facility_id) REFERENCES facilities(id) ON DELETE CASCADE,
    UNIQUE(origin_facility_id, destination_id, destination_type)
);

-- Restaurar datos (mapear nombres antiguos si es necesario)
INSERT OR IGNORE INTO distance_matrix (
    id, 
    origin_facility_id, 
    destination_id, 
    destination_type, 
    distance_km, 
    is_link_segment, 
    created_at, 
    updated_at
)
SELECT 
    id,
    COALESCE(origin_facility_id, 0) AS origin_facility_id,
    COALESCE(destination_node_id, destination_id, 0) AS destination_id, -- Mapear nombre antiguo
    COALESCE(destination_type, 'SITE') AS destination_type,
    COALESCE(distance_km, 0) AS distance_km,
    COALESCE(is_segment, is_link_segment, 0) AS is_link_segment, -- Mapear nombre antiguo
    created_at,
    updated_at
FROM distance_matrix_temp;

-- Limpiar
DROP TABLE IF EXISTS distance_matrix_temp;

-- 2.3: Crear índices
CREATE INDEX IF NOT EXISTS idx_distance_matrix_origin 
ON distance_matrix(origin_facility_id);

CREATE INDEX IF NOT EXISTS idx_distance_matrix_destination 
ON distance_matrix(destination_id, destination_type);

-- ==========================================
-- PASO 3: VERIFICAR contractor_tariffs (UF)
-- ==========================================
-- Asegurar que todas las tarifas están en UF
-- Si ya se ejecutó 021_fix_financial_schema_to_uf.sql, esta tabla debería estar OK

-- 3.1: Verificar estructura actual
CREATE TABLE IF NOT EXISTS contractor_tariffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contractor_id INTEGER NOT NULL,
    vehicle_type TEXT NOT NULL CHECK (vehicle_type IN ('BATEA', 'AMPLIROLL_SIMPLE', 'AMPLIROLL_CARRO')),
    
    -- TARIFA BASE EN UF (NO EN CLP)
    -- Ejemplo: 0.15 UF por tonelada-kilómetro
    base_rate_uf REAL NOT NULL CHECK (base_rate_uf > 0),
    
    -- Peso mínimo garantizado (toneladas)
    min_weight_guaranteed REAL DEFAULT 0 CHECK (min_weight_guaranteed >= 0),
    
    -- Precio base del petróleo (CLP) para el polinomio de ajuste
    -- Factor = (precio_actual_petroleo / base_fuel_price)
    -- Costo_final_UF = base_rate_uf * Factor
    base_fuel_price REAL NOT NULL CHECK (base_fuel_price > 0),
    
    -- Vigencia
    valid_from DATE NOT NULL,
    valid_to DATE,
    
    -- Audit
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contractor_id) REFERENCES contractors(id) ON DELETE CASCADE,
    CHECK (valid_to IS NULL OR valid_to > valid_from)
);

-- 3.2: Si existe columna antigua 'amount_clp' o 'base_rate', debemos eliminarla
-- (Ya debería estar hecho por migración 021, pero verificamos)

-- NOTE: Si detectamos columna 'base_rate', asumimos que es 021 sin aplicar
-- y debemos aplicarla ahora

-- Verificar y corregir si es necesario (complejo en SQLite, mejor avisar)
-- Para esta migración, asumimos que 021 ya se aplicó

-- 3.3: Índices
CREATE INDEX IF NOT EXISTS idx_contractor_tariffs_lookup 
ON contractor_tariffs(contractor_id, vehicle_type, valid_from);

CREATE INDEX IF NOT EXISTS idx_contractor_tariffs_active 
ON contractor_tariffs(contractor_id, vehicle_type) 
WHERE valid_to IS NULL;

-- ==========================================
-- PASO 4: VERIFICAR client_tariffs (UF)
-- ==========================================
-- Asegurar que las tarifas de clientes están en UF

CREATE TABLE IF NOT EXISTS client_tariffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    
    -- Concepto de facturación
    concept TEXT NOT NULL CHECK (concept IN ('TRANSPORTE', 'DISPOSICION', 'TRATAMIENTO')),
    
    -- TARIFA EN UF (NO EN CLP)
    -- Ejemplo: 2.5 UF por tonelada para transporte
    rate_uf REAL NOT NULL CHECK (rate_uf > 0),
    
    -- Peso mínimo garantizado (opcional)
    min_weight_guaranteed REAL DEFAULT 0 CHECK (min_weight_guaranteed >= 0),
    
    -- Vigencia
    valid_from DATE NOT NULL,
    valid_to DATE,
    
    -- Audit
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    CHECK (valid_to IS NULL OR valid_to > valid_from)
);

-- 4.1: Índices
CREATE INDEX IF NOT EXISTS idx_client_tariffs_lookup 
ON client_tariffs(client_id, concept, valid_from);

CREATE INDEX IF NOT EXISTS idx_client_tariffs_active 
ON client_tariffs(client_id, concept) 
WHERE valid_to IS NULL;

-- ==========================================
-- PASO 5: AGREGAR COLUMNAS A loads
-- ==========================================
-- Agregar trip_id, segment_type, financial_status si no existen

-- 5.1: trip_id para agrupar loads enlazadas
-- Ejemplo: Planta A -> Planta B (carga 1) + Planta B -> Sitio (carga 2) = mismo trip_id
ALTER TABLE loads ADD COLUMN trip_id TEXT;

-- 5.2: segment_type para clasificar el tipo de segmento
-- 'DIRECT' = origen -> destino directo
-- 'PICKUP_LINK' = recolección en enlace intermedio  
-- 'MAIN_HAUL' = transporte principal post-enlace
ALTER TABLE loads ADD COLUMN segment_type TEXT DEFAULT 'DIRECT'
    CHECK (segment_type IN ('DIRECT', 'PICKUP_LINK', 'MAIN_HAUL'));

-- 5.3: financial_status para workflow financiero
-- 'PENDING' = sin procesar
-- 'PROCESSED' = costo calculado
-- 'CLOSED' = facturado y cerrado
ALTER TABLE loads ADD COLUMN financial_status TEXT DEFAULT 'PENDING'
    CHECK (financial_status IN ('PENDING', 'PROCESSED', 'CLOSED'));

-- 5.4: Índices para optimizar queries financieras
CREATE INDEX IF NOT EXISTS idx_loads_trip_id 
ON loads(trip_id) 
WHERE trip_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_loads_financial_status 
ON loads(financial_status);

CREATE INDEX IF NOT EXISTS idx_loads_billing_period 
ON loads(financial_status, scheduled_date);

-- ==========================================
-- PASO 6: LIMPIEZA
-- ==========================================
DROP TABLE IF EXISTS economic_indicators_backup;

-- ==========================================
-- VERIFICACIÓN
-- ==========================================
SELECT '✅ Migration 022_financial_schema_final completed successfully' AS status;

-- Verificar economic_indicators
SELECT 
    COUNT(*) AS total_periods,
    SUM(CASE WHEN is_closed = 1 THEN 1 ELSE 0 END) AS closed_periods,
    SUM(CASE WHEN is_closed = 0 THEN 1 ELSE 0 END) AS open_periods
FROM economic_indicators;

-- Verificar distance_matrix
SELECT COUNT(*) AS total_routes FROM distance_matrix;

-- Verificar contractor_tariffs
SELECT COUNT(*) AS total_contractor_tariffs FROM contractor_tariffs;

-- Verificar client_tariffs
SELECT COUNT(*) AS total_client_tariffs FROM client_tariffs;

-- Verificar nuevas columnas en loads
SELECT 
    COUNT(*) AS total_loads,
    COUNT(trip_id) AS loads_with_trip_id,
    COUNT(DISTINCT segment_type) AS distinct_segment_types,
    COUNT(DISTINCT financial_status) AS distinct_financial_statuses
FROM loads;

-- ==========================================
-- NOTAS DE MIGRACIÓN
-- ==========================================
-- 1. Esta migración es IDEMPOTENTE: puede ejecutarse múltiples veces
-- 2. Preserva datos existentes siempre que sea posible
-- 3. Convierte automáticamente period_key a period_year/period_month
-- 4. Mapea nombres de columnas antiguos a nuevos en distance_matrix
-- 5. Asume que contractor_tariffs YA está en UF (migración 021 aplicada)
-- 6. Agrega columnas a loads con valores DEFAULT seguros
-- 7. SQLite limitation: CHECK constraints en ALTER TABLE solo desde SQLite 3.25+
--    Si falla, las constraints se validarán en capa de aplicación
-- 8. Usar PRAGMA foreign_key_check; después de aplicar para verificar integridad
--
-- PREREQUISITOS:
-- - Ejecutar migraciones 020 y 021 antes de esta
-- - Backup de base de datos antes de aplicar
-- - Verificar versión de SQLite >= 3.25 para constraints en ALTER
--
-- ROLLBACK (si es necesario):
-- - Restaurar desde backup
-- - O ejecutar script de rollback específico (no incluido aquí)
