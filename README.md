# ADO

Repositorio `ADO` — proyecto de ejemplo para gestión de operaciones.

Descripción
- Código fuente Python con servicios, modelos y una interfaz de usuario básica.

Requisitos
- Python 3.10+ (o la versión que uses en el proyecto)
- Dependencias listadas en `requirements.txt`

Instalación y ejecución (macOS / Linux / WSL)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Base de Datos
Este proyecto utiliza SQLite como base de datos única:
- **Ubicación**: `ado_system.db` (raíz del proyecto)
- **Schema**: `database/schema.sql`
- **Backups**: `database/*_backup_*.db`
- **Inicialización**: `python3 -m infrastructure.persistence.database_manager`

Para crear un backup manual:
```bash
timestamp=$(date +%Y%m%d_%H%M%S)
cp ado_system.db "database/ado_system_backup_${timestamp}.db"
```

Pruebas
```bash
pytest -q
```

Contacto
- Autor: Marcelo Calzadilla
# ADO