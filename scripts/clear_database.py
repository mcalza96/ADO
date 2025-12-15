#!/usr/bin/env python3
"""
Script para limpiar todos los datos de la base de datos.

⚠️ ADVERTENCIA: Este script elimina TODOS los datos pero mantiene la estructura (tablas).
"""
import sqlite3
import sys
import os
from datetime import datetime
import shutil

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DB_PATH, BASE_DIR


def create_backup():
    """Crea un backup de la base de datos antes de limpiar."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(BASE_DIR, 'database', 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_path = os.path.join(backup_dir, f'ado_system_backup_{timestamp}.db')
    
    print(f"📦 Creando backup en: {backup_path}")
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Backup creado exitosamente")
    
    return backup_path


def get_all_tables(conn):
    """Obtiene lista de todas las tablas de usuario."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    return [row[0] for row in cursor.fetchall()]


def clear_all_data(create_backup_first=True):
    """
    Limpia todos los datos de todas las tablas.
    
    Args:
        create_backup_first: Si True, crea backup antes de limpiar
    """
    print("=" * 60)
    print("⚠️  LIMPIEZA DE BASE DE DATOS")
    print("=" * 60)
    print(f"\nBase de datos: {DB_PATH}")
    
    # Crear backup si se solicita
    if create_backup_first:
        backup_path = create_backup()
        print(f"\n💾 Backup guardado en: {backup_path}")
    
    # Conectar a la base de datos
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Obtener todas las tablas
    tables = get_all_tables(conn)
    
    print(f"\n📊 Tablas encontradas: {len(tables)}")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   - {table}: {count} registros")
    
    # Confirmar con usuario
    print("\n" + "=" * 60)
    print("⚠️  Esta operación eliminará TODOS los datos")
    print("=" * 60)
    
    response = input("\n¿Estás seguro de que deseas continuar? (escribe 'SI' para confirmar): ")
    
    if response.strip().upper() != 'SI':
        print("\n❌ Operación cancelada")
        conn.close()
        return
    
    # Deshabilitar foreign keys temporalmente
    cursor.execute("PRAGMA foreign_keys = OFF")
    
    print("\n🗑️  Eliminando datos...")
    
    # Eliminar datos de todas las tablas
    deleted_counts = {}
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            deleted = cursor.rowcount
            deleted_counts[table] = deleted
            print(f"   ✓ {table}: {deleted} registros eliminados")
        except Exception as e:
            print(f"   ✗ {table}: Error - {e}")
    
    # Resetear autoincrement
    cursor.execute("DELETE FROM sqlite_sequence")
    print(f"   ✓ Secuencias de autoincrement reseteadas")
    
    # Re-habilitar foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Commit cambios
    conn.commit()
    
    # Vacuum para optimizar
    print("\n🔧 Optimizando base de datos...")
    cursor.execute("VACUUM")
    
    conn.close()
    
    # Resumen
    total_deleted = sum(deleted_counts.values())
    print("\n" + "=" * 60)
    print("✅ LIMPIEZA COMPLETADA")
    print("=" * 60)
    print(f"\nTotal de registros eliminados: {total_deleted}")
    print(f"Tablas procesadas: {len(tables)}")
    
    if create_backup_first:
        print(f"\n💾 Backup disponible en: {backup_path}")
        print("   Puedes restaurar usando:")
        print(f"   cp '{backup_path}' '{DB_PATH}'")
    
    print("\n🎯 La estructura de la base de datos se mantiene intacta")
    print("   Puedes insertar nuevos datos cuando lo necesites")


def main():
    """Punto de entrada principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Limpia todos los datos de la base de datos'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='No crear backup antes de limpiar (NO RECOMENDADO)'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='No pedir confirmación (PELIGROSO)'
    )
    
    args = parser.parse_args()
    
    if args.yes:
        # Modo automático sin confirmación
        print("⚠️  Modo automático activado - NO se pedirá confirmación")
    
    clear_all_data(create_backup_first=not args.no_backup)


if __name__ == "__main__":
    main()
