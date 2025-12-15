"""
Script para insertar datos de prueba para el módulo de reportes financieros.

Inserta:
- Indicadores económicos para Noviembre 2025
- Tarifas de contratistas (costos)
- Tarifas de clientes (ingresos)
- Distancias de rutas

IMPORTANTE: Este script usa la configuración centralizada de DB desde settings.py
"""

import sqlite3
import sys
import os
from datetime import datetime

# Importar configuración centralizada
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DB_PATH

def insert_test_data():
    """Inserta datos de prueba para el módulo de reportes financieros."""
    print(f"📊 Insertando datos de prueba en: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔧 Insertando datos de prueba para Reportes Financieros...")
    
    # 1. Indicadores Económicos para Noviembre 2025
    print("\n📊 1. Insertando Indicadores Económicos...")
    cursor.execute("""
        INSERT OR REPLACE INTO economic_indicators 
        (period_key, cycle_start_date, cycle_end_date, uf_value, fuel_price, status)
        VALUES 
        ('2025-11', '2025-10-19', '2025-11-18', 37250.50, 1200.00, 'CLOSED')
    """)
    print("   ✓ Insertado: Noviembre 2025 | UF: $37,250.50 | Diésel: $1,200")
    
    # Diciembre 2025 (para probar otro mes)
    cursor.execute("""
        INSERT OR REPLACE INTO economic_indicators 
        (period_key, cycle_start_date, cycle_end_date, uf_value, fuel_price, status)
        VALUES 
        ('2025-12', '2025-11-19', '2025-12-18', 37500.00, 1250.00, 'OPEN')
    """)
    print("   ✓ Insertado: Diciembre 2025 | UF: $37,500.00 | Diésel: $1,250")
    
    # 2. Tarifas de Contratistas
    print("\n🚚 2. Insertando Tarifas de Contratistas...")
    
    # Obtener IDs de contratistas (si existen)
    cursor.execute("SELECT id FROM contractors LIMIT 3")
    contractors = cursor.fetchall()
    
    if contractors:
        for contractor in contractors:
            contractor_id = contractor[0]
            
            # Tarifa para BATEA
            cursor.execute("""
                INSERT OR REPLACE INTO contractor_tariffs
                (contractor_id, vehicle_type, base_rate, min_weight_guaranteed, base_fuel_price, valid_from)
                VALUES (?, 'BATEA', 0.027, 15.0, 1000.0, '2025-01-01')
            """, (contractor_id,))
            
            # Tarifa para AMPLIROLL_SIMPLE
            cursor.execute("""
                INSERT OR REPLACE INTO contractor_tariffs
                (contractor_id, vehicle_type, base_rate, min_weight_guaranteed, base_fuel_price, valid_from)
                VALUES (?, 'AMPLIROLL_SIMPLE', 0.022, 7.0, 1000.0, '2025-01-01')
            """, (contractor_id,))
            
            print(f"   ✓ Insertadas tarifas para contractor_id={contractor_id}")
    else:
        print("   ⚠️  No hay contratistas en la BD. Insertando contratista de prueba...")
        cursor.execute("""
            INSERT INTO contractors (name, rut, is_active)
            VALUES ('Transportes Demo S.A.', '76123456-7', 1)
        """)
        contractor_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO contractor_tariffs
            (contractor_id, vehicle_type, base_rate, min_weight_guaranteed, base_fuel_price, valid_from)
            VALUES (?, 'BATEA', 0.027, 15.0, 1000.0, '2025-01-01')
        """, (contractor_id,))
        
        cursor.execute("""
            INSERT INTO contractor_tariffs
            (contractor_id, vehicle_type, base_rate, min_weight_guaranteed, base_fuel_price, valid_from)
            VALUES (?, 'AMPLIROLL_SIMPLE', 0.022, 7.0, 1000.0, '2025-01-01')
        """, (contractor_id,))
        
        print(f"   ✓ Creado contratista demo con ID={contractor_id}")
    
    # 3. Tarifas de Clientes (Ingresos)
    print("\n💰 3. Insertando Tarifas de Clientes...")
    
    # Obtener IDs de clientes
    cursor.execute("SELECT id FROM clients LIMIT 3")
    clients = cursor.fetchall()
    
    if clients:
        for client in clients:
            client_id = client[0]
            
            # Concepto TRANSPORTE
            cursor.execute("""
                INSERT OR REPLACE INTO client_tariffs
                (client_id, concept, rate_uf, min_weight_guaranteed, valid_from)
                VALUES (?, 'TRANSPORTE', 0.05, 10.0, '2025-01-01')
            """, (client_id,))
            
            # Concepto DISPOSICION
            cursor.execute("""
                INSERT OR REPLACE INTO client_tariffs
                (client_id, concept, rate_uf, min_weight_guaranteed, valid_from)
                VALUES (?, 'DISPOSICION', 0.03, 10.0, '2025-01-01')
            """, (client_id,))
            
            # Concepto TRATAMIENTO
            cursor.execute("""
                INSERT OR REPLACE INTO client_tariffs
                (client_id, concept, rate_uf, min_weight_guaranteed, valid_from)
                VALUES (?, 'TRATAMIENTO', 0.025, 10.0, '2025-01-01')
            """, (client_id,))
            
            print(f"   ✓ Insertadas tarifas para client_id={client_id}")
    else:
        print("   ⚠️  No hay clientes en la BD. Las tarifas se insertarán cuando existan clientes.")
    
    # 4. Distancias (Distance Matrix)
    print("\n📍 4. Verificando Distance Matrix...")
    cursor.execute("SELECT COUNT(*) FROM distance_matrix")
    distance_count = cursor.fetchone()[0]
    
    if distance_count == 0:
        print("   ⚠️  No hay rutas configuradas. Insertando ejemplos...")
        
        # Obtener facilities y sites
        cursor.execute("SELECT id FROM facilities LIMIT 2")
        facilities = cursor.fetchall()
        
        cursor.execute("SELECT id FROM sites LIMIT 2")
        sites = cursor.fetchall()
        
        if facilities and sites:
            # Ruta: Facility 1 -> Site 1
            cursor.execute("""
                INSERT INTO distance_matrix
                (origin_facility_id, destination_node_id, destination_type, distance_km, is_segment)
                VALUES (?, ?, 'SITE', 50.0, 0)
            """, (facilities[0][0], sites[0][0]))
            
            print(f"   ✓ Insertada ruta demo: Facility {facilities[0][0]} -> Site {sites[0][0]} (50 km)")
    else:
        print(f"   ✓ Distance Matrix tiene {distance_count} rutas configuradas")
    
    # 5. Actualizar fechas de loads para que caigan en el ciclo de prueba
    print("\n📦 5. Actualizando fechas de loads para prueba...")
    cursor.execute("""
        UPDATE loads 
        SET scheduled_date = '2025-11-10 10:00:00'
        WHERE status IN ('ARRIVED', 'COMPLETED')
    """)
    updated = cursor.rowcount
    print(f"   ✓ Actualizados {updated} loads al periodo de Noviembre 2025")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n✅ Datos de prueba insertados correctamente!")
    print("\nAhora puedes probar el reporte en Streamlit:")
    print("1. Navega a: Reportes → 💰 Reportes Financieros")
    print("2. Selecciona: Año=2025, Mes=Noviembre")
    print("3. Haz clic en 'Generar Liquidación'")

if __name__ == "__main__":
    insert_test_data()
