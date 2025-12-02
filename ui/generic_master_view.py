import streamlit as st
from dataclasses import fields, is_dataclass
from typing import Any, Type, List

def render_generic_master_view(service, model_cls: Type[Any], title: str, list_columns: List[str] = None):
    """
    Renders a generic CRUD view for a master entity.
    
    Args:
        service: GenericCrudService instance
        model_cls: Dataclass model
        title: Section title
        list_columns: Columns to show in the table (default: all)
    """
    st.subheader(title)
    
    # --- Create / Edit Form ---
    with st.expander(f"Nuevo/Editar {title}"):
        with st.form(f"form_{model_cls.__name__}"):
            form_data = {}
            model_fields = fields(model_cls)
            
            # Simple form generation based on type hints
            # This is basic; for production, we might need more metadata
            for field in model_fields:
                if field.name in ('id', 'created_at', 'updated_at', 'is_active'):
                    continue
                    
                # Determine input type
                if field.type == int:
                    form_data[field.name] = st.number_input(field.name, step=1)
                elif field.type == float:
                    form_data[field.name] = st.number_input(field.name, step=0.1)
                else:
                    form_data[field.name] = st.text_input(field.name)
            
            if st.form_submit_button("Guardar"):
                try:
                    # Create instance
                    # We need to handle 'id' being None for new items
                    # And other auto-fields
                    entity = model_cls(id=None, **form_data)
                    # Note: This doesn't handle 'created_at' if it's required in __init__ but not in form
                    # Assuming models have defaults or optional fields for these
                    
                    service.save(entity)
                    st.success("✅ Guardado exitosamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    # --- List View ---
    items = service.get_all()
    if items:
        data = [vars(item) for item in items]
        if list_columns:
            # Filter columns
            data = [{k: v for k, v in d.items() if k in list_columns} for d in data]
            
        st.dataframe(data, use_container_width=True)
    else:
        st.info("No hay registros.")
