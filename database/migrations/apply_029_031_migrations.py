#!/usr/bin/env python3
"""
Script para aplicar las migraciones 029-031 relacionadas con:
- Tarifas cliente/planta (matriz de tarifas)
- Rellenos sanitarios como destino
- Integración con tabla loads

Autor: System
Fecha: 2025-12-09
"""

import sqlite3
import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.persistence.database_manager import DatabaseManager
from config.settings import DATABASE_PATH


def apply_migration_029(conn: sqlite3.Connection):
    """Aplica migración 029: client_plant_tariffs"""
    print("📋 Aplicando migración 029: client_plant_tariffs...")
    
    migration_path = Path(__file__).parent / "029_client_plant_tariffs.sql"
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Ejecutar SQL
    conn.executescript(sql)
    conn.commit()
    
    print("✅ Migración 029 aplicada correctamente")


def apply_migration_030(conn: sqlite3.Connection):
    """Aplica migración 030: sanitary_landfills"""
    print("📋 Aplicando migración 030: sanitary_landfills...")
    
    migration_path = Path(__file__).parent / "030_sanitary_landfills.sql"
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Ejecutar SQL
    conn.executescript(sql)
    conn.commit()
    
    print("✅ Migración 030 aplicada correctamente")


def apply_migration_031(conn: sqlite3.Connection):
    """Aplica migración 031: destination_sanitary_landfill_id en loads"""
    print("📋 Aplicando migración 031: destination_sanitary_landfill_id...")
    
    migration_path = Path(__file__).parent / "031_add_sanitary_landfill_to_loads.sql"
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Ejecutar SQL
    conn.executescript(sql)
    conn.commit()
    
    print("✅ Migración 031 aplicada correctamente")


def verify_migrations(conn: sqlite3.Connection):
    """Verifica que las migraciones se aplicaron correctamente"""
    print("\n🔍 Verificando migraciones...")
    
    cursor = conn.cursor()
    
    # Verificar tabla client_plant_tariffs
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM sqlite_master 
        WHERE type='table' AND name='client_plant_tariffs'
    """)
    if cursor.fetchone()['count'] == 1:
        print("✅ Tabla client_plant_tariffs existe")
    else:
        print("❌ ERROR: Tabla client_plant_tariffs no encontrada")
        return False
    
    # Verificar tabla sanitary_landfills
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM sqlite_master 
        WHERE type='table' AND name='sanitary_landfills'
    """)
    if cursor.fetchone()['count'] == 1:
        print("✅ Tabla sanitary_landfills existe")
    else:
        print("❌ ERROR: Tabla sanitary_landfills no encontrada")
        return False
    
    # Verificar columna destination_sanitary_landfill_id en loads
    cursor.execute("PRAGMA table_info(loads)")
    columns = [row['name'] for row in cursor.fetchall()]
    
    if 'destination_sanitary_landfill_id' in columns:
        print("✅ Columna destination_sanitary_landfill_id agregada a loads")
    else:
        print("❌ ERROR: Columna destination_sanitary_landfill_id no encontrada en loads")
        return False
    
    # Verificar datos de ejemplo en sanitary_landfills
    cursor.execute("SELECT COUNT(*) as count FROM sanitary_landfills")
    count = cursor.fetchone()['count']
    print(f"✅ Rellenos sanitarios en base de datos: {count}")
    
    return True


def main():
    """Función principal para aplicar todas las migraciones"""
    print("=" * 70)
    print("🚀 APLICADOR DE MIGRACIONES 029-031")
    print("   Tarifas Cliente/Planta + Rellenos Sanitarios")
    print("=" * 70)
    print(f"\n📂 Base de datos: {DATABASE_PATH}\n")
    
    # Confirmar con el usuario
    response = input("¿Desea continuar con la aplicación de migraciones? (s/n): ")
    if response.lower() not in ('s', 'si', 'yes', 'y'):
        print("❌ Operación cancelada por el usuario")
        return
    
    try:
        # Crear conexión usando DatabaseManager
        db_manager = DatabaseManager(DATABASE_PATH)
        
        with db_manager as conn:
            # Aplicar migraciones en orden
            apply_migration_029(conn)
            apply_migration_030(conn)
            apply_migration_031(conn)
            
            # Verificar
            if verify_migrations(conn):
                print("\n" + "=" * 70)
                print("✅ TODAS LAS MIGRACIONES APLICADAS CORRECTAMENTE")
                print("=" * 70)
                print("\n📌 Próximos pasos:")
                print("   1. Reiniciar la aplicación Streamlit")
                print("   2. Ir a Configuración Financiera → Tarifarios → Tarifas Cliente/Planta")
                print("   3. Configurar las tarifas por cliente y planta")
                print("   4. En Programación y Planificación, ahora verás 'Relleno Sanitario' como opción")
                print("\n")
            else:
                print("\n❌ ERROR: Verificación de migraciones falló")
                sys.exit(1)
                
    except Exception as e:
        print(f"\n❌ ERROR aplicando migraciones: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
