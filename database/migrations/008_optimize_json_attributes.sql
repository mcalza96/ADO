-- Agrega una columna virtual para consultar el pH rápidamente sin duplicar datos
ALTER TABLE loads ADD COLUMN ph_final REAL 
GENERATED ALWAYS AS (json_extract(attributes, '$.lab_analysis_result.ph')) VIRTUAL;

-- Crea un índice sobre esa columna virtual
CREATE INDEX idx_loads_ph_final ON loads(ph_final);
