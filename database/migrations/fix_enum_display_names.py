"""
Migration: Fix enum display names stored as values

Este script corrige datos donde se guardaron display_names en lugar de valores de enum.
Ejemplo: 'Batea (carga directa)' -> 'BATEA'

Ejecutar con: python -m database.migrations.fix_enum_display_names
"""

import sqlite3
import os
from pathlib import Path


# Mapeo de display_names incorrectos a valores correctos
VEHICLE_TYPE_FIXES = {
    "Batea (carga directa)": "BATEA",
    "Ampliroll (contenedores)": "AMPLIROLL",
}

ASSET_TYPE_FIXES = {
    "Vehículo de Carretera": "ROAD_VEHICLE",
    "Maquinaria Pesada": "HEAVY_EQUIPMENT",
}


def get_db_path() -> str:
    """Obtiene la ruta de la base de datos."""
    # Buscar en ubicaciones comunes
    possible_paths = [
        "ado_system.db",
        "../ado_system.db",
        "../../ado_system.db",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError("No se encontró la base de datos ado_system.db")


def fix_vehicle_types(conn: sqlite3.Connection) -> int:
    """Corrige tipos de vehículo incorrectos."""
    cursor = conn.cursor()
    total_fixed = 0
    
    for display_name, correct_value in VEHICLE_TYPE_FIXES.items():
        cursor.execute(
            "UPDATE vehicles SET type = ? WHERE type = ?",
            (correct_value, display_name)
        )
        fixed = cursor.rowcount
        if fixed > 0:
            print(f"  - Corregidos {fixed} vehículos: '{display_name}' -> '{correct_value}'")
            total_fixed += fixed
    
    return total_fixed


def fix_allowed_vehicle_types(conn: sqlite3.Connection) -> int:
    """Corrige allowed_vehicle_types en facilities y treatment_plants."""
    cursor = conn.cursor()
    total_fixed = 0
    
    for table in ["facilities", "treatment_plants"]:
        # Obtener registros con valores potencialmente incorrectos
        cursor.execute(f"SELECT id, allowed_vehicle_types FROM {table} WHERE allowed_vehicle_types IS NOT NULL")
        rows = cursor.fetchall()
        
        for row_id, allowed_types in rows:
            if not allowed_types:
                continue
            
            # Procesar CSV y corregir cada valor
            original_values = [v.strip() for v in allowed_types.split(",")]
            corrected_values = []
            needs_fix = False
            
            for value in original_values:
                if value in VEHICLE_TYPE_FIXES:
                    corrected_values.append(VEHICLE_TYPE_FIXES[value])
                    needs_fix = True
                else:
                    corrected_values.append(value)
            
            if needs_fix:
                new_value = ",".join(corrected_values)
                cursor.execute(
                    f"UPDATE {table} SET allowed_vehicle_types = ? WHERE id = ?",
                    (new_value, row_id)
                )
                print(f"  - {table}[{row_id}]: '{allowed_types}' -> '{new_value}'")
                total_fixed += 1
    
    return total_fixed


def main():
    """Ejecuta la migración."""
    print("=" * 60)
    print("Migración: Corrigiendo display_names guardados como valores")
    print("=" * 60)
    
    try:
        db_path = get_db_path()
        print(f"\nUsando base de datos: {db_path}")
        
        conn = sqlite3.connect(db_path)
        
        print("\n1. Corrigiendo vehicles.type...")
        vehicles_fixed = fix_vehicle_types(conn)
        
        print("\n2. Corrigiendo allowed_vehicle_types...")
        allowed_fixed = fix_allowed_vehicle_types(conn)
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 60)
        print(f"Migración completada:")
        print(f"  - Vehículos corregidos: {vehicles_fixed}")
        print(f"  - Registros allowed_vehicle_types corregidos: {allowed_fixed}")
        print("=" * 60)
        
        if vehicles_fixed == 0 and allowed_fixed == 0:
            print("\n✅ No se encontraron datos incorrectos. La base de datos está OK.")
        else:
            print(f"\n✅ Se corrigieron {vehicles_fixed + allowed_fixed} registros.")
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        raise


if __name__ == "__main__":
    main()
