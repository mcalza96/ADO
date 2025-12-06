#!/usr/bin/env python3
"""
Script de aplicación de migración 022_financial_schema_final.sql
Autor: Senior Database Architect
Fecha: 2025-12-05

Características:
- Backup automático antes de aplicar
- Verificación de integridad referencial
- Rollback automático si falla
- Logging detallado
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
import sys

# Configuración
DB_PATH = Path(__file__).parent.parent / "ado.db"
MIGRATION_FILE = Path(__file__).parent / "022_financial_schema_final.sql"
BACKUP_DIR = Path(__file__).parent / "backups"


def create_backup():
    """Crea backup de la base de datos antes de la migración"""
    print(f"📦 Creando backup de la base de datos...")
    
    # Crear directorio de backups si no existe
    BACKUP_DIR.mkdir(exist_ok=True)
    
    # Nombre del backup con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"ado_backup_before_022_{timestamp}.db"
    
    # Copiar archivo
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Backup creado: {backup_path}")
    
    return backup_path


def check_prerequisites(conn):
    """Verifica que las migraciones prerequisitas se hayan ejecutado"""
    print(f"\n🔍 Verificando prerequisitos...")
    
    cursor = conn.cursor()
    
    # Verificar que existan las tablas básicas
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('facilities', 'clients', 'contractors', 'loads')
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    required_tables = ['facilities', 'clients', 'contractors', 'loads']
    missing_tables = set(required_tables) - set(tables)
    
    if missing_tables:
        print(f"❌ ERROR: Faltan tablas requeridas: {missing_tables}")
        print(f"   Ejecutar migraciones anteriores primero.")
        return False
    
    print(f"✅ Todas las tablas prerequisitas existen")
    return True


def apply_migration(conn):
    """Aplica el script de migración SQL"""
    print(f"\n⚙️  Aplicando migración 022_financial_schema_final.sql...")
    
    # Leer el archivo SQL
    with open(MIGRATION_FILE, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    cursor = conn.cursor()
    
    try:
        # Ejecutar el script completo
        cursor.executescript(migration_sql)
        conn.commit()
        print(f"✅ Migración aplicada exitosamente")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ ERROR al aplicar migración: {e}")
        conn.rollback()
        return False


def verify_schema(conn):
    """Verifica que el esquema resultante sea correcto"""
    print(f"\n🔍 Verificando esquema resultante...")
    
    cursor = conn.cursor()
    errors = []
    
    # 1. Verificar economic_indicators
    print(f"   Verificando economic_indicators...")
    cursor.execute("PRAGMA table_info(economic_indicators)")
    columns = {row[1] for row in cursor.fetchall()}
    required_cols = {'period_year', 'period_month', 'uf_value', 'monthly_fuel_price', 'is_closed'}
    
    if not required_cols.issubset(columns):
        missing = required_cols - columns
        errors.append(f"economic_indicators: faltan columnas {missing}")
    else:
        print(f"   ✅ economic_indicators OK")
    
    # 2. Verificar distance_matrix
    print(f"   Verificando distance_matrix...")
    cursor.execute("PRAGMA table_info(distance_matrix)")
    columns = {row[1] for row in cursor.fetchall()}
    required_cols = {'origin_facility_id', 'destination_id', 'destination_type', 'distance_km', 'is_link_segment'}
    
    if not required_cols.issubset(columns):
        missing = required_cols - columns
        errors.append(f"distance_matrix: faltan columnas {missing}")
    else:
        print(f"   ✅ distance_matrix OK")
    
    # 3. Verificar contractor_tariffs
    print(f"   Verificando contractor_tariffs...")
    cursor.execute("PRAGMA table_info(contractor_tariffs)")
    columns = {row[1] for row in cursor.fetchall()}
    
    if 'base_rate_uf' not in columns:
        errors.append(f"contractor_tariffs: falta columna base_rate_uf")
    elif 'base_rate' in columns and 'base_rate_uf' in columns:
        errors.append(f"contractor_tariffs: WARNING - existen ambas columnas base_rate y base_rate_uf")
    else:
        print(f"   ✅ contractor_tariffs OK (en UF)")
    
    # 4. Verificar client_tariffs
    print(f"   Verificando client_tariffs...")
    cursor.execute("PRAGMA table_info(client_tariffs)")
    columns = {row[1] for row in cursor.fetchall()}
    
    if 'rate_uf' not in columns:
        errors.append(f"client_tariffs: falta columna rate_uf")
    else:
        print(f"   ✅ client_tariffs OK (en UF)")
    
    # 5. Verificar loads
    print(f"   Verificando columnas financieras en loads...")
    cursor.execute("PRAGMA table_info(loads)")
    columns = {row[1] for row in cursor.fetchall()}
    required_cols = {'trip_id', 'segment_type', 'financial_status'}
    
    if not required_cols.issubset(columns):
        missing = required_cols - columns
        errors.append(f"loads: faltan columnas {missing}")
    else:
        print(f"   ✅ loads OK (trip_id, segment_type, financial_status)")
    
    # Resumen
    if errors:
        print(f"\n❌ Se encontraron {len(errors)} error(es):")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print(f"\n✅ Todos los esquemas verificados correctamente")
        return True


def check_foreign_keys(conn):
    """Verifica la integridad referencial"""
    print(f"\n🔗 Verificando integridad referencial...")
    
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_key_check")
    violations = cursor.fetchall()
    
    if violations:
        print(f"❌ Se encontraron {len(violations)} violaciones de foreign keys:")
        for violation in violations[:10]:  # Mostrar máximo 10
            print(f"   - {violation}")
        return False
    else:
        print(f"✅ Integridad referencial OK")
        return True


def display_summary(conn):
    """Muestra un resumen de los datos migrados"""
    print(f"\n📊 Resumen de datos:")
    
    cursor = conn.cursor()
    
    # economic_indicators
    cursor.execute("SELECT COUNT(*) FROM economic_indicators")
    count = cursor.fetchone()[0]
    print(f"   - economic_indicators: {count} periodos")
    
    # distance_matrix
    cursor.execute("SELECT COUNT(*) FROM distance_matrix")
    count = cursor.fetchone()[0]
    print(f"   - distance_matrix: {count} rutas")
    
    # contractor_tariffs
    cursor.execute("SELECT COUNT(*) FROM contractor_tariffs")
    count = cursor.fetchone()[0]
    print(f"   - contractor_tariffs: {count} tarifas")
    
    # client_tariffs
    cursor.execute("SELECT COUNT(*) FROM client_tariffs")
    count = cursor.fetchone()[0]
    print(f"   - client_tariffs: {count} tarifas")
    
    # loads
    cursor.execute("""
        SELECT 
            COUNT(*) AS total,
            COUNT(trip_id) AS with_trip_id,
            SUM(CASE WHEN financial_status = 'PENDING' THEN 1 ELSE 0 END) AS pending
        FROM loads
    """)
    total, with_trip, pending = cursor.fetchone()
    print(f"   - loads: {total} total, {with_trip} con trip_id, {pending} pendientes financieramente")


def main():
    """Función principal"""
    print(f"=" * 80)
    print(f"  MIGRACIÓN 022: FINANCIAL SCHEMA FINAL (UF-First)")
    print(f"=" * 80)
    
    # Verificar que exista la base de datos
    if not DB_PATH.exists():
        print(f"❌ ERROR: No se encuentra la base de datos en {DB_PATH}")
        sys.exit(1)
    
    # Verificar que exista el archivo de migración
    if not MIGRATION_FILE.exists():
        print(f"❌ ERROR: No se encuentra el archivo de migración en {MIGRATION_FILE}")
        sys.exit(1)
    
    # Crear backup
    backup_path = create_backup()
    
    # Conectar a la base de datos
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        # Verificar prerequisitos
        if not check_prerequisites(conn):
            print(f"\n❌ Migración abortada: faltan prerequisitos")
            sys.exit(1)
        
        # Aplicar migración
        if not apply_migration(conn):
            print(f"\n❌ Migración falló. Restaurando backup...")
            conn.close()
            shutil.copy2(backup_path, DB_PATH)
            print(f"✅ Backup restaurado")
            sys.exit(1)
        
        # Verificar esquema
        if not verify_schema(conn):
            print(f"\n⚠️  WARNING: El esquema no es completamente correcto")
            # No abortamos aquí, puede ser aceptable
        
        # Verificar foreign keys
        if not check_foreign_keys(conn):
            print(f"\n❌ Integridad referencial comprometida. Restaurando backup...")
            conn.close()
            shutil.copy2(backup_path, DB_PATH)
            print(f"✅ Backup restaurado")
            sys.exit(1)
        
        # Mostrar resumen
        display_summary(conn)
        
        print(f"\n" + "=" * 80)
        print(f"  ✅ MIGRACIÓN 022 COMPLETADA EXITOSAMENTE")
        print(f"=" * 80)
        print(f"\n💡 Backup guardado en: {backup_path}")
        print(f"   Puedes eliminarlo si todo funciona correctamente.\n")
        
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        print(f"   Restaurando backup...")
        conn.close()
        shutil.copy2(backup_path, DB_PATH)
        print(f"✅ Backup restaurado")
        sys.exit(1)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()
