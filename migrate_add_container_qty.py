import sqlite3
import os

DB_PATH = "database/biosolids.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Attempting to add 'container_quantity' column to 'loads' table...")
        cursor.execute("ALTER TABLE loads ADD COLUMN container_quantity INTEGER")
        print("Column 'container_quantity' added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column 'container_quantity' already exists.")
        else:
            print(f"Error adding column: {e}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
