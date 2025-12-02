import os

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database configuration
DB_NAME = "ado_system.db"
DB_PATH = os.getenv('DB_PATH', os.path.join(BASE_DIR, DB_NAME))

# Application settings
APP_NAME = "Biosolids Management ERP"
VERSION = "0.1.0"
