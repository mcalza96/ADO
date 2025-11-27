import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Generator

class DatabaseManager:
    """
    Manages SQLite database connections and transactions using the Context Manager pattern.
    Ensures foreign keys are enabled and WAL mode is active.
    """

    def __init__(self, db_path: str = "database/biosolids.db"):
        """
        Initialize the DatabaseManager.
        
        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        """
        Enter the runtime context related to this object.
        Establishes the connection and configures pragmas.
        """
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.connection = sqlite3.connect(self.db_path)
        
        # Configure SQLite for integrity and concurrency
        self.connection.execute("PRAGMA foreign_keys = ON;")
        self.connection.execute("PRAGMA journal_mode = WAL;")
        
        # Return the connection to be used in the 'with' block
        # We could also return self and expose execute methods, but returning connection is flexible
        # However, to strictly follow "DatabaseManager" pattern often implies wrapping methods.
        # But the prompt asks for "Context Manager (with DatabaseManager() as db:)"
        # If 'db' is the connection, then the user uses raw cursor.
        # If 'db' is the manager, I should provide helper methods.
        # I will return the connection for maximum flexibility as it's a standard pythonic pattern for simple wrappers,
        # OR I can return 'self' and set self.connection.
        # Let's return the connection object but customized with Row factory.
        
        self.connection.row_factory = sqlite3.Row
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context.
        Commits if no error, rolls back if error, and closes connection.
        """
        if self.connection:
            if exc_type:
                self.connection.rollback()
                print(f"Transaction rolled back due to: {exc_val}")
            else:
                self.connection.commit()
            
            self.connection.close()
            self.connection = None

    @staticmethod
    def initialize_db(schema_path: str = "database/schema.sql", db_path: str = "database/biosolids.db"):
        """
        Initialize the database structure from the schema file.
        """
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema file not found at {schema_path}")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        try:
            # We use a fresh connection for initialization
            with sqlite3.connect(db_path) as conn:
                conn.executescript(schema_sql)
                print(f"Database initialized successfully at {db_path}")
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
            raise

if __name__ == "__main__":
    # Allow running this script to initialize the DB
    DatabaseManager.initialize_db()
