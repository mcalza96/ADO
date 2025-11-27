import sqlite3
import os

db_path = "database/biosolids.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if column exists
cursor.execute("PRAGMA table_info(loads)")
columns = [info[1] for info in cursor.fetchall()]

if "requested_date" not in columns:
    print("Column 'requested_date' missing in 'loads'. Adding it...")
    try:
        cursor.execute("ALTER TABLE loads ADD COLUMN requested_date DATETIME")
        conn.commit()
        print("Column added successfully.")
    except Exception as e:
        print(f"Error adding column: {e}")
else:
    print("Column 'requested_date' already exists.")

conn.close()
