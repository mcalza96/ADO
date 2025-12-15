"""
Script para limpiar datos operacionales y dejar solo datos maestros.
Útil para resetear el sistema antes de pruebas.
"""

from infrastructure.persistence.database_manager import DatabaseManager

def reset_operational_data():
    """Elimina datos operacionales pero mantiene datos maestros."""
    
    db = DatabaseManager()
    
    print("=" * 60)
    print("LIMPIEZA DE DATOS OPERACIONALES")
    print("=" * 60)
    
    with db as conn:
        cursor = conn.cursor()
        
        # Tablas operacionales a limpiar (en orden por dependencias)
        operational_tables = [
            ('cost_records', 'Registros de costos'),
            ('status_transitions', 'Transiciones de estado'),
            ('container_filling_records', 'Registros de llenado de contenedores'),
            ('machine_logs', 'Registros de maquinaria'),
            ('pickup_requests', 'Solicitudes de retiro'),
            ('soil_samples', 'Muestras de suelo'),
            ('regulatory_documents', 'Documentos regulatorios'),
            ('loads', 'Cargas'),
            ('batches', 'Lotes de tratamiento'),
        ]
        
        print("\nEliminando datos operacionales...\n")
        
        for table, description in operational_tables:
            try:
                # Contar registros antes
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count_before = cursor.fetchone()[0]
                
                # Eliminar
                cursor.execute(f"DELETE FROM {table}")
                
                # Resetear autoincrement
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                
                print(f"  ✓ {description:40} ({count_before} registros eliminados)")
                
            except Exception as e:
                print(f"  ⚠️  {description:40} Error: {e}")
        
        conn.commit()
    
    print("\n" + "=" * 60)
    print("DATOS MAESTROS CONSERVADOS:")
    print("=" * 60)
    
    # Mostrar resumen de datos maestros que quedan
    with db as conn:
        cursor = conn.cursor()
        
        master_tables = [
            ('sites', 'Sitios/Predios'),
            ('plots', 'Parcelas'),
            ('facilities', 'Plantas de tratamiento'),
            ('vehicles', 'Vehículos'),
            ('drivers', 'Conductores'),
            ('contractors', 'Contratistas'),
            ('rate_sheets', 'Tarifas'),
            ('economic_indicators', 'Indicadores económicos'),
        ]
        
        print()
        for table, description in master_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {description:40} {count:3} registros")
            except:
                pass
    
    print("\n" + "=" * 60)
    print("✅ LIMPIEZA COMPLETADA")
    print("=" * 60)
    print("\nEl sistema está listo para nuevas pruebas.")
    print("Los datos maestros se han conservado.\n")

if __name__ == "__main__":
    confirm = input("⚠️  ¿Estás seguro de eliminar todos los datos operacionales? (escribe 'SI' para confirmar): ")
    
    if confirm == "SI":
        reset_operational_data()
    else:
        print("\n❌ Operación cancelada.")
