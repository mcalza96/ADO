from container import get_container
from services.ui.task_resolver import TaskResolver

container = get_container()
resolver = TaskResolver(container.db_manager)

print("🚀 Iniciando Verificación de Lógica UI (TaskResolver)")

# 1. Test ADMIN (Debe ver todas las tareas de Cargas)
print("\n👤 Rol: ADMIN")
tasks_admin = resolver.get_pending_tasks("ADMIN", user_id=1)
print(f"✅ Tareas encontradas: {len(tasks_admin)}")
for t in tasks_admin:
    print(f"  - [{t.priority}] {t.title} (ID: {t.id}) -> Form: {t.form_type}")

# Validar que existan las tareas esperadas del seed
expected_forms = ["lab_check", "gate_check", "pickup_check"]
found_forms = [t.form_type for t in tasks_admin]

if all(f in found_forms for f in expected_forms):
    print("✅ Todas las tareas de carga esperadas están presentes.")
else:
    print(f"❌ Faltan tareas. Encontradas: {found_forms}")

# 2. Test OPERATOR (Debe ver tarea de Maquinaria)
print("\n👤 Rol: OPERATOR")
tasks_op = resolver.get_pending_tasks("OPERATOR", user_id=1)
print(f"✅ Tareas encontradas: {len(tasks_op)}")
for t in tasks_op:
    print(f"  - [{t.priority}] {t.title} (ID: {t.id})")

if any(t.form_type == "daily_log" for t in tasks_op):
    print("✅ Tarea de Parte Diario encontrada.")
else:
    print("❌ No se encontró tarea de Parte Diario (¿Existe la máquina 1?).")
