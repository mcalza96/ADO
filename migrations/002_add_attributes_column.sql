-- Migration 002: Agregar columna attributes (JSON) a tablas operacionales
-- Para permitir captura de atributos dinámicos sin cambios de schema

-- Tabla: loads
-- Permite almacenar datos variables como pH inicial, temperatura de llegada, odómetros
ALTER TABLE loads ADD COLUMN attributes TEXT DEFAULT '{}';

-- Tabla: treatment_batches  
-- Permite almacenar datos variables como dosis de cal, tiempo de mezclado, operador
ALTER TABLE treatment_batches ADD COLUMN attributes TEXT DEFAULT '{}';

-- Tabla: nitrogen_applications
-- Permite almacenar datos variables como humedad de suelo, velocidad del viento, temperatura ambiental
ALTER TABLE nitrogen_applications ADD COLUMN attributes TEXT DEFAULT '{}';

-- NOTA: SQLite no tiene tipo JSON nativo, por lo que se usa TEXT
-- La serialización/deserialización se maneja en la capa de aplicación (repositories)
