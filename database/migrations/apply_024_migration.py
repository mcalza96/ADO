#!/usr/bin/env python3
"""
Script para aplicar la migración 024_add_link_point_field.sql

Añade el campo is_link_point a la tabla facilities para permitir
que ciertas plantas de cliente actúen como puntos de enlace.
"""

import sqlite3
import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import DB_PATH

def apply_migration():
    """Aplica la migración para añadir is_link_point a facilities."""
    db_path = DB_PATH
    
    print(f"📂 Base de datos: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(facilities)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_link_point' in columns:
            print("✅ La columna is_link_point ya existe en facilities")
            return True
        
        print("🔄 Añadiendo columna is_link_point a facilities...")
        
        # Añadir la columna
        cursor.execute("""
            ALTER TABLE facilities 
            ADD COLUMN is_link_point INTEGER DEFAULT 0 CHECK (is_link_point IN (0, 1))
        """)
        
        conn.commit()
        print("✅ Columna is_link_point añadida exitosamente")
        
        # Crear índice
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_facilities_link_point 
                ON facilities(is_link_point) WHERE is_link_point = 1
            """)
            conn.commit()
            print("✅ Índice creado exitosamente")
        except sqlite3.Error as e:
            print(f"⚠️ No se pudo crear el índice (puede que SQLite no soporte partial indexes): {e}")
        
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
        cursor.execute("PRAGMA table_info(facilities)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        if 'is_link_point' in columns:
            print("\n📊 Verificación de migración:")
            print(f"   - Columna is_link_point: ✅ Presente")
            col_info = columns['is_link_point']
            print(f"   - Tipo: {col_info[2]}")
            print(f"   - Default: {col_info[4]}")
            return True
        else:
            print("❌ La columna is_link_point NO está presente")
            return False
            
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Migración 024: Añadir is_link_point a facilities")
    print("=" * 60)
    
    if apply_migration():
        verify_migration()
        print("\n✅ Migración completada exitosamente")
    else:
        print("\n❌ Error en la migración")
        sys.exit(1)
