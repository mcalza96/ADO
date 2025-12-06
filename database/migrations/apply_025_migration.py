#!/usr/bin/env python3
"""
Script para aplicar la migración 025_update_distance_matrix_types.sql

Actualiza la tabla distance_matrix para:
1. Renombrar destination_node_id a destination_id
2. Renombrar is_segment a is_link_segment
3. Añadir TREATMENT_PLANT como tipo de destino válido
"""

import sqlite3
import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import DB_PATH

def apply_migration():
    """Aplica la migración para actualizar distance_matrix."""
    db_path = DB_PATH
    
    print(f"📂 Base de datos: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar columnas actuales
        cursor.execute("PRAGMA table_info(distance_matrix)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        print(f"📊 Columnas actuales: {list(columns.keys())}")
        
        # Verificar si ya está migrada
        if 'destination_id' in columns and 'is_link_segment' in columns:
            print("✅ La tabla ya está actualizada con los nombres correctos")
            return True
        
        print("🔄 Migrando tabla distance_matrix...")
        
        # Crear backup
        cursor.execute("DROP TABLE IF EXISTS distance_matrix_backup")
        cursor.execute("CREATE TABLE distance_matrix_backup AS SELECT * FROM distance_matrix")
        print("   ✓ Backup creado")
        
        # Obtener datos existentes
        cursor.execute("SELECT * FROM distance_matrix_backup")
        existing_data = cursor.fetchall()
        print(f"   ✓ {len(existing_data)} registros guardados")
        
        # Eliminar tabla vieja
        cursor.execute("DROP TABLE IF EXISTS distance_matrix")
        print("   ✓ Tabla antigua eliminada")
        
        # Crear tabla nueva con nombres correctos
        cursor.execute("""
            CREATE TABLE distance_matrix (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin_facility_id INTEGER NOT NULL,
                destination_id INTEGER NOT NULL,
                destination_type TEXT NOT NULL CHECK (destination_type IN ('FACILITY', 'TREATMENT_PLANT', 'SITE')),
                distance_km REAL NOT NULL CHECK (distance_km > 0),
                is_link_segment INTEGER NOT NULL DEFAULT 0 CHECK (is_link_segment IN (0, 1)),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (origin_facility_id) REFERENCES facilities(id) ON DELETE CASCADE,
                UNIQUE(origin_facility_id, destination_id, destination_type)
            )
        """)
        print("   ✓ Tabla nueva creada")
        
        # Restaurar datos mapeando columnas
        if existing_data:
            # Determinar qué columnas tienen los datos
            backup_cols = []
            cursor.execute("PRAGMA table_info(distance_matrix_backup)")
            for row in cursor.fetchall():
                backup_cols.append(row[1])
            
            # Mapear columnas antiguas a nuevas
            has_node_id = 'destination_node_id' in backup_cols
            has_is_segment = 'is_segment' in backup_cols
            
            for row in existing_data:
                row_dict = dict(zip(backup_cols, row))
                
                # Mapear nombres de columnas
                dest_id = row_dict.get('destination_node_id') or row_dict.get('destination_id')
                is_link = row_dict.get('is_segment') or row_dict.get('is_link_segment') or 0
                
                cursor.execute("""
                    INSERT OR IGNORE INTO distance_matrix 
                    (origin_facility_id, destination_id, destination_type, distance_km, is_link_segment, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row_dict.get('origin_facility_id'),
                    dest_id,
                    row_dict.get('destination_type', 'SITE'),
                    row_dict.get('distance_km', 0),
                    int(is_link) if is_link else 0,
                    row_dict.get('created_at'),
                    row_dict.get('updated_at')
                ))
            
            print(f"   ✓ Datos migrados")
        
        # Eliminar backup
        cursor.execute("DROP TABLE IF EXISTS distance_matrix_backup")
        print("   ✓ Backup eliminado")
        
        # Crear índices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_distance_matrix_origin 
            ON distance_matrix(origin_facility_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_distance_matrix_destination 
            ON distance_matrix(destination_id, destination_type)
        """)
        print("   ✓ Índices creados")
        
        conn.commit()
        print("✅ Migración completada exitosamente")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error al aplicar migración: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


def verify_migration():
    """Verifica que la migración se aplicó correctamente."""
    db_path = DB_PATH
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(distance_matrix)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        print("\n📊 Verificación de migración:")
        
        expected_cols = ['id', 'origin_facility_id', 'destination_id', 'destination_type', 
                        'distance_km', 'is_link_segment', 'created_at', 'updated_at']
        
        all_present = True
        for col in expected_cols:
            if col in columns:
                print(f"   ✓ {col}: presente")
            else:
                print(f"   ✗ {col}: FALTA")
                all_present = False
        
        # Verificar datos
        cursor.execute("SELECT COUNT(*) FROM distance_matrix")
        count = cursor.fetchone()[0]
        print(f"\n   📈 Registros en la tabla: {count}")
        
        return all_present
            
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Migración 025: Actualizar distance_matrix")
    print("=" * 60)
    
    if apply_migration():
        verify_migration()
        print("\n✅ Migración completada exitosamente")
    else:
        print("\n❌ Error en la migración")
        sys.exit(1)
