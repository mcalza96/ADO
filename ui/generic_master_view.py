import streamlit as st
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Type, List, Optional, Dict, Callable

@dataclass
class FieldConfig:
    """Configuration for a form field in GenericMasterView."""
    label: Optional[str] = None
    widget: str = "text_input"  # text_input, text_area, number_input, selectbox, date_input
    options: Optional[Any] = None  # For selectbox: service, list, or callable
    required: bool = False
    help: Optional[str] = None
    default: Any = None

class GenericMasterView:
    """
    Generic CRUD view for master data entities.
    Supports custom field rendering, foreign keys, and validation.
    """
    
    def __init__(
        self,
        service,
        model_class: Type[Any],
        title: str,
        display_columns: Optional[List[str]] = None,
        form_config: Optional[Dict[str, FieldConfig]] = None,
        exclude_fields: Optional[List[str]] = None
    ):
        """
        Args:
            service: GenericCrudService instance
            model_class: Dataclass model
            title: Section title
            display_columns: Columns to show in table (default: all except id, timestamps, is_active)
            form_config: Custom configuration for form fields
            exclude_fields: Fields to exclude from form (default: id, created_at, updated_at)
        """
        self.service = service
        self.model_class = model_class
        self.title = title
        self.display_columns = display_columns
        self.form_config = form_config or {}
        self.exclude_fields = exclude_fields or ['id', 'created_at', 'updated_at']
        
    def render(self):
        """Render the complete CRUD view."""
        st.subheader(self.title)
        
        # Create/Edit Form
        with st.expander(f"➕ Nuevo {self.title}"):
            self._render_form()
        
        # List View
        self._render_list()
    
    def _render_form(self):
        """Render the create/edit form."""
        with st.form(f"form_{self.model_class.__name__}"):
            form_data = {}
            model_fields = fields(self.model_class)
            
            for field in model_fields:
                if field.name in self.exclude_fields:
                    continue
                
                # Get field configuration
                config = self.form_config.get(field.name, FieldConfig())
                label = config.label or field.name.replace('_', ' ').title()
                
                # Render widget based on configuration
                if config.widget == "text_area":
                    form_data[field.name] = st.text_area(
                        label,
                        value=config.default or "",
                        help=config.help
                    )
                elif config.widget == "number_input":
                    form_data[field.name] = st.number_input(
                        label,
                        value=config.default or 0.0,
                        help=config.help
                    )
                elif config.widget == "selectbox":
                    # Handle foreign keys
                    if config.options:
                        options = self._resolve_options(config.options)
                        form_data[field.name] = st.selectbox(
                            label,
                            options=list(options.keys()),
                            help=config.help,
                            format_func=lambda x: x  # Display function
                        )
                        # Get the actual ID value
                        if form_data[field.name]:
                            form_data[field.name] = options[form_data[field.name]]
                    else:
                        form_data[field.name] = st.text_input(label, help=config.help)
                elif config.widget == "date_input":
                    form_data[field.name] = st.date_input(label, help=config.help)
                else:  # Default: text_input
                    form_data[field.name] = st.text_input(
                        label,
                        value=config.default or "",
                        help=config.help
                    )
            
            submitted = st.form_submit_button("💾 Guardar")
            if submitted:
                self._handle_submit(form_data)
    
    def _resolve_options(self, options_source: Any) -> Dict[str, int]:
        """
        Resolve options for selectbox from various sources.
        
        Args:
            options_source: Service (with get_all method), list, or callable
            
        Returns:
            Dict mapping display names to IDs
        """
        if hasattr(options_source, 'get_all'):
            # It's a service
            items = options_source.get_all()
            return {self._get_display_name(item): item.id for item in items}
        elif callable(options_source):
            # It's a function
            items = options_source()
            return {self._get_display_name(item): item.id for item in items}
        elif isinstance(options_source, list):
            # It's a list of items or tuples
            if options_source and isinstance(options_source[0], tuple):
                return {name: value for name, value in options_source}
            else:
                return {self._get_display_name(item): item.id for item in options_source}
        else:
            return {}
    
    def _get_display_name(self, item: Any) -> str:
        """Get display name for an item (tries 'name' attribute first)."""
        if hasattr(item, 'name'):
            return item.name
        elif hasattr(item, '__str__'):
            return str(item)
        else:
            return repr(item)
    
    def _handle_submit(self, form_data: Dict[str, Any]):
        """Handle form submission."""
        try:
            # Validate required fields
            for field_name, config in self.form_config.items():
                if config.required and not form_data.get(field_name):
                    st.error(f"⚠️ {config.label or field_name} es obligatorio")
                    return
            
            # Create entity instance
            entity = self.model_class(id=None, **form_data)
            
            # Save
            self.service.save(entity)
            st.success("✅ Guardado exitosamente")
            st.rerun()
        except ValueError as e:
            st.error(f"⚠️ Error de validación: {e}")
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    def _render_list(self):
        """Render the list of items."""
        items = self.service.get_all()
        
        if items:
            # Convert to dict for dataframe
            data = []
            for item in items:
                item_dict = vars(item) if hasattr(item, '__dict__') else item
                
                # Filter columns if specified
                if self.display_columns:
                    item_dict = {k: v for k, v in item_dict.items() if k in self.display_columns}
                
                data.append(item_dict)
            
            st.dataframe(data, use_container_width=True, hide_index=True)
        else:
            st.info("No hay registros.")
