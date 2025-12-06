#!/usr/bin/env python3
"""
Script para aplicar la migración 027_create_proformas_table.sql

Crea la tabla maestra de proformas y migra datos existentes de economic_indicators.
"""

import sqlite3
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import DB_PATH


def apply_migration():
    """Aplica la migración 027_create_proformas_table."""
    migration_file = os.path.join(os.path.dirname(__file__), '027_create_proformas_table.sql')
    
    print(f"Conectando a base de datos: {DB_PATH}")
    print(f"Aplicando migración: {migration_file}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Leer el archivo de migración
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Ejecutar la migración
        cursor.executescript(migration_sql)
        conn.commit()
        
        # Verificar resultados
        cursor.execute("SELECT COUNT(*) FROM proformas")
        count = cursor.fetchone()[0]
        print(f"✅ Migración aplicada exitosamente. Proformas creadas: {count}")
        
        # Mostrar proformas creadas
        if count > 0:
            cursor.execute("""
                SELECT proforma_code, period_year, period_month, uf_value, fuel_price, 
                       cycle_start_date, cycle_end_date,
                       CASE WHEN is_closed = 1 THEN 'CERRADA' ELSE 'ABIERTA' END as estado
                FROM proformas 
                ORDER BY period_year DESC, period_month DESC
                LIMIT 10
            """)
            rows = cursor.fetchall()
            print("\nÚltimas proformas:")
            print("-" * 100)
            print(f"{'Código':<12} {'Año':>6} {'Mes':>4} {'UF':>12} {'Petróleo':>10} {'Inicio':<12} {'Fin':<12} {'Estado':<10}")
            print("-" * 100)
            for row in rows:
                print(f"{row[0]:<12} {row[1]:>6} {row[2]:>4} {row[3]:>12,.2f} {row[4]:>10,.2f} {row[5]:<12} {row[6]:<12} {row[7]:<10}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error aplicando migración: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()


if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
