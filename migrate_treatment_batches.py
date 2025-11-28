import sqlite3
import os

db_path = "database/biosolids.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if columns exist
cursor.execute("PRAGMA table_info(loads)")
columns = [info[1] for info in cursor.fetchall()]

new_columns = ["treatment_batch_1_id", "treatment_batch_2_id"]

for col in new_columns:
    if col not in columns:
        print(f"Column '{col}' missing in 'loads'. Adding it...")
        try:
            cursor.execute(f"ALTER TABLE loads ADD COLUMN {col} INTEGER REFERENCES treatment_batches(id)")
            conn.commit()
            print(f"Column '{col}' added successfully.")
        except Exception as e:
            print(f"Error adding column '{col}': {e}")
    else:
        print(f"Column '{col}' already exists.")

conn.close()
