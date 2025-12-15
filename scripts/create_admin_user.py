#!/usr/bin/env python3
"""
Script para crear usuario administrador.
"""
import sqlite3
import sys
import os
import hashlib
from datetime import datetime

# Agregar path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import DB_PATH


def create_admin_user():
    """Crea un usuario administrador."""
    print("=" * 60)
    print("👤 CREACIÓN DE USUARIO ADMINISTRADOR")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Datos del usuario admin
    username = "admin"
    password = "admin123"  # Contraseña temporal
    email = "admin@ado.cl"
    full_name = "Administrador del Sistema"
    role = "Admin"  # Debe ser uno de: Admin, Planificador, Chofer, Operador
    
    # Hashear contraseña con SHA256
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    print(f"\n📝 Creando usuario:")
    print(f"   Username: {username}")
    print(f"   Full Name: {full_name}")
    print(f"   Email: {email}")
    print(f"   Role: {role}")
    print(f"   Password: {password}")
    print(f"   Hash: {password_hash[:32]}...")
    print(f"\n⚠️  IMPORTANTE: Cambia la contraseña después del primer login")
    
    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, full_name, role, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (username, password_hash, email, full_name, role, datetime.now()))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        print(f"\n✅ Usuario creado exitosamente (ID: {user_id})")
        print(f"\n🔐 Credenciales de acceso:")
        print(f"   Usuario: {username}")
        print(f"   Contraseña: {password}")
        print(f"   Rol: {role}")
        
    except sqlite3.IntegrityError as e:
        print(f"\n⚠️  Error de integridad: {e}")
        print(f"   El usuario '{username}' probablemente ya existe")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    create_admin_user()
