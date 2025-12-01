import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Generator

from config.settings import DB_PATH

class DatabaseManager:
    """
    Manages SQLite database connections and transactions using the Context Manager pattern.
    Ensures foreign keys are enabled and WAL mode is active.
    """

    def __init__(self, db_path: str = DB_PATH):
        """
        Initialize the DatabaseManager.
        
        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._transaction_depth = 0

    def __enter__(self) -> sqlite3.Connection:
        """
        Enter the runtime context related to this object.
        Establishes the connection and configures pragmas.
        Supports nested transactions via reference counting.
        """
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            
            # Configure SQLite for integrity and concurrency
            self.connection.execute("PRAGMA foreign_keys = ON;")
            self.connection.execute("PRAGMA journal_mode = WAL;")
        
        self._transaction_depth += 1
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context.
        Commits if no error, rolls back if error.
        Only closes if it was the top-level context.
        """
        self._transaction_depth -= 1
        
        if self.connection:
            if exc_type:
                # If an error occurred, we rollback. 
                # In a nested context, this rollback might affect the whole transaction 
                # depending on how SQLite handles it, but typically we want to bubble up the error.
                self.connection.rollback()
                print(f"Transaction rolled back due to: {exc_val}")
            
            if self._transaction_depth == 0:
                if not exc_type:
                    self.connection.commit()
                
                self.connection.close()
                self.connection = None

    def get_connection(self) -> sqlite3.Connection:
        """
        Returns a raw connection object. 
        Useful for manual transaction management.
        """
        if self.connection is None:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON;")
            self.connection.execute("PRAGMA journal_mode = WAL;")
        return self.connection

    def begin_transaction(self) -> sqlite3.Connection:
        """
        Starts a transaction explicitly.
        """
        return self.get_connection()

    def commit(self):
        """
        Commits the current transaction.
        """
        if self.connection:
            self.connection.commit()

    def rollback(self):
        """
        Rolls back the current transaction.
        """
        if self.connection:
            self.connection.rollback()
            
    def close(self):
        """
        Closes the connection explicitly.
        """
        if self.connection:
            self.connection.close()
            self.connection = None

    @staticmethod
    def initialize_db(schema_path: str = "database/schema.sql", db_path: str = DB_PATH):
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
