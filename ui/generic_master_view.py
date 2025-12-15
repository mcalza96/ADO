import streamlit as st
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Type, List, Optional, Dict, Callable
from enum import Enum

@dataclass
class FieldConfig:
    """Configuration for a form field in GenericMasterView."""
    label: Optional[str] = None
    widget: str = "text_input"  # text_input, text_area, number_input, selectbox, date_input, enum
    options: Optional[Any] = None  # For selectbox: service, list, callable, or Enum class
    required: bool = False
    help: Optional[str] = None
    default: Any = None
    enum_class: Optional[Type[Enum]] = None  # For enum widget: the Enum class to use

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
        exclude_fields: Optional[List[str]] = None,
        data_source: Optional[Callable] = None
    ):
        """
        Args:
            service: GenericCrudService instance
            model_class: Dataclass model
            title: Section title
            display_columns: Columns to show in table (default: all except id, timestamps, is_active)
            form_config: Custom configuration for form fields
            exclude_fields: Fields to exclude from form (default: id, created_at, updated_at)
            data_source: Optional callable that returns filtered list of items (default: service.get_all)
        """
        self.service = service
        self.model_class = model_class
        self.title = title
        self.display_columns = display_columns
        self.form_config = form_config or {}
        self.exclude_fields = exclude_fields or ['id', 'created_at', 'updated_at']
        self.data_source = data_source
        # Unique key prefix for this view instance
        self._key_prefix = f"{self.model_class.__name__}_{self.title.replace(' ', '_')}"
        
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
        # Use unique key prefix for this view instance
        with st.form(f"form_{self._key_prefix}"):
            form_data = {}
            model_fields = fields(self.model_class)
            
            for field in model_fields:
                if field.name in self.exclude_fields:
                    continue
                
                # Skip is_active - we'll handle it separately at the end
                if field.name == 'is_active':
                    continue
                
                # Get field configuration
                config = self.form_config.get(field.name, FieldConfig())
                label = config.label or field.name.replace('_', ' ').title()
                
                # Render widget based on configuration or auto-detect from field type
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
                elif config.widget == "enum":
                    # Handle Enum fields - auto-generate selectbox from Enum class
                    enum_class = config.enum_class or config.options
                    if enum_class and isinstance(enum_class, type) and issubclass(enum_class, Enum):
                        enum_options = {e.value: e.value for e in enum_class}
                        default_idx = 0
                        if config.default:
                            try:
                                default_idx = list(enum_options.keys()).index(config.default)
                            except ValueError:
                                default_idx = 0
                        form_data[field.name] = st.selectbox(
                            label,
                            options=list(enum_options.keys()),
                            index=default_idx,
                            help=config.help
                        )
                    else:
                        form_data[field.name] = st.text_input(label, help=config.help)
                elif config.widget == "multiselect":
                    # Handle multiselect - options should be list of tuples (display_name, value)
                    # Convención: DisplayableEnum.choices() retorna [(display_name, value), ...]
                    if config.options:
                        options = config.options if isinstance(config.options, list) else list(config.options)
                        if options and isinstance(options[0], tuple):
                            # List of (display_name, value) tuples - extraer valores y labels
                            option_values = [value for _, value in options]  # Los VALUES para guardar
                            option_labels = {value: display_name for display_name, value in options}  # value -> display
                            selected = st.multiselect(
                                label,
                                options=option_values,
                                default=config.default or [],
                                format_func=lambda x: option_labels.get(x, x),
                                help=config.help
                            )
                        else:
                            # Simple list of values
                            selected = st.multiselect(
                                label,
                                options=options,
                                default=config.default or [],
                                help=config.help
                            )
                        # Convert to CSV string for storage
                        form_data[field.name] = ",".join(selected) if selected else None
                    else:
                        form_data[field.name] = st.text_input(label, help=config.help)
                elif config.widget == "checkbox":
                    form_data[field.name] = st.checkbox(
                        label,
                        value=config.default if config.default is not None else True,
                        help=config.help
                    )
                else:  # Default: text_input
                    form_data[field.name] = st.text_input(
                        label,
                        value=config.default or "",
                        help=config.help
                    )
            
            # Always show is_active checkbox at the end if the model has it
            has_is_active = any(f.name == 'is_active' for f in model_fields)
            if has_is_active:
                form_data['is_active'] = st.checkbox("✅ Activo", value=True, help="Desmarcar para desactivar el registro")
            
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
                # Tuplas de (display_name, value) - convención de DisplayableEnum.choices()
                return {display_name: value for display_name, value in options_source}
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
            
            # Ensure is_active has a value (default True if not in form_data)
            if 'is_active' not in form_data:
                form_data['is_active'] = True
            
            # Create entity instance
            entity = self.model_class(id=None, **form_data)
            
            # Save
            self.service.save(entity)
            st.success("✅ Guardado exitosamente")
            st.rerun()
        except ValueError as e:
            st.error(f"⚠️ Error de validación: {e}")
        except Exception as e:
            error_msg = str(e)
            # Detect UNIQUE constraint violations
            if "UNIQUE constraint failed" in error_msg:
                # Extract field name from error
                if "rut" in error_msg.lower():
                    st.error("⚠️ Ya existe un registro con este RUT")
                elif "username" in error_msg.lower():
                    st.error("⚠️ Ya existe un usuario con este nombre de usuario")
                elif "email" in error_msg.lower():
                    st.error("⚠️ Ya existe un registro con este email")
                elif "license_plate" in error_msg.lower():
                    st.error("⚠️ Ya existe un vehículo con esta patente")
                else:
                    st.error(f"⚠️ Ya existe un registro con estos datos: {error_msg}")
            else:
                st.error(f"❌ Error: {e}")
    
    def _render_list(self):
        """Render the list of items with edit capability."""
        # Use data_source if provided, otherwise default to service.get_all()
        if self.data_source and callable(self.data_source):
            items = self.data_source()
        else:
            items = self.service.get_all()
        
        if not items:
            st.info("No hay registros.")
            return
        
        # Convert to dict for dataframe display
        data = []
        for item in items:
            item_dict = vars(item).copy() if hasattr(item, '__dict__') else dict(item)
            data.append(item_dict)
        
        # Display columns for table
        display_cols = self.display_columns or [k for k in data[0].keys() if k not in ['id', 'created_at', 'updated_at']]
        
        # Create header row
        cols = st.columns([3] + [2] * (len(display_cols) - 1) + [1, 1, 1])
        for i, col_name in enumerate(display_cols):
            label = col_name.replace('_', ' ').title()
            cols[i].markdown(f"**{label}**")
        cols[-3].markdown("**Editar**")
        cols[-2].markdown("**Estado**")
        cols[-1].markdown("**Eliminar**")
        
        st.divider()
        
        # Render each row with edit button
        for item in items:
            item_dict = vars(item).copy() if hasattr(item, '__dict__') else dict(item)
            cols = st.columns([3] + [2] * (len(display_cols) - 1) + [1, 1, 1])
            
            for i, col_name in enumerate(display_cols):
                value = item_dict.get(col_name, "")
                # Format boolean values nicely
                if isinstance(value, bool):
                    value = "✅ Sí" if value else "❌ No"
                cols[i].write(value if value else "-")
            
            # Edit button
            if cols[-3].button("✏️", key=f"edit_{self._key_prefix}_{item.id}"):
                st.session_state[f"editing_{self._key_prefix}"] = item.id
                st.rerun()
            
            # Toggle active status
            is_active = item_dict.get('is_active', True)
            status_icon = "🟢" if is_active else "🔴"
            if cols[-2].button(status_icon, key=f"toggle_{self._key_prefix}_{item.id}"):
                self._toggle_active(item)
            
            # Delete button with confirmation
            if cols[-1].button("🗑️", key=f"delete_{self._key_prefix}_{item.id}"):
                st.session_state[f"confirming_delete_{self._key_prefix}"] = item.id
                st.rerun()
        
        # Show delete confirmation modal if needed
        confirming_delete_id = st.session_state.get(f"confirming_delete_{self._key_prefix}")
        if confirming_delete_id:
            self._render_delete_confirmation(confirming_delete_id)
        
        # Show edit form if editing
        editing_id = st.session_state.get(f"editing_{self._key_prefix}")
        if editing_id:
            self._render_edit_form(editing_id)
    
    def _toggle_active(self, item):
        """Toggle the is_active status of an item."""
        try:
            item.is_active = not item.is_active
            self.service.save(item)
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al cambiar estado: {e}")
    
    def _render_delete_confirmation(self, item_id: int):
        """Render delete confirmation dialog."""
        item = self.service.get_by_id(item_id)
        if not item:
            del st.session_state[f"confirming_delete_{self._key_prefix}"]
            return
        
        item_dict = vars(item).copy() if hasattr(item, '__dict__') else dict(item)
        item_name = item_dict.get('name', f'ID {item_id}')
        
        st.divider()
        st.warning(f"⚠️ **¿Estás seguro de que deseas eliminar '{item_name}'?**")
        st.caption("Esta acción no se puede deshacer.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí, eliminar", key=f"confirm_delete_{self._key_prefix}_{item_id}", use_container_width=True):
                self._handle_delete(item_id)
        with col2:
            if st.button("❌ Cancelar", key=f"cancel_delete_{self._key_prefix}_{item_id}", use_container_width=True):
                del st.session_state[f"confirming_delete_{self._key_prefix}"]
                st.rerun()
    
    def _handle_delete(self, item_id: int):
        """Handle item deletion."""
        try:
            if hasattr(self.service, 'delete'):
                self.service.delete(item_id)
            elif hasattr(self.service, 'soft_delete'):
                self.service.soft_delete(item_id)
            else:
                # Fallback: set is_active to False
                item = self.service.get_by_id(item_id)
                if item:
                    item.is_active = False
                    self.service.save(item)
            
            st.success("✅ Eliminado exitosamente")
            del st.session_state[f"confirming_delete_{self._key_prefix}"]
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al eliminar: {e}")
            del st.session_state[f"confirming_delete_{self._key_prefix}"]
    
    def _render_edit_form(self, item_id: int):
        """Render the edit form for an existing item."""
        # Get the item to edit
        item = self.service.get_by_id(item_id)
        if not item:
            st.error("Registro no encontrado")
            del st.session_state[f"editing_{self._key_prefix}"]
            return
        
        item_dict = vars(item).copy() if hasattr(item, '__dict__') else dict(item)
        
        st.divider()
        st.subheader(f"✏️ Editando: {item_dict.get('name', f'ID {item_id}')}")
        
        with st.form(f"edit_form_{self._key_prefix}_{item_id}"):
            form_data = {'id': item_id}
            model_fields = fields(self.model_class)
            
            for field in model_fields:
                if field.name in self.exclude_fields:
                    continue
                
                if field.name == 'is_active':
                    continue
                
                # Get field configuration and current value
                config = self.form_config.get(field.name, FieldConfig())
                label = config.label or field.name.replace('_', ' ').title()
                current_value = item_dict.get(field.name)
                
                # Render widget with current value
                if config.widget == "text_area":
                    form_data[field.name] = st.text_area(
                        label,
                        value=current_value or "",
                        help=config.help
                    )
                elif config.widget == "number_input":
                    form_data[field.name] = st.number_input(
                        label,
                        value=float(current_value) if current_value else 0.0,
                        help=config.help
                    )
                elif config.widget == "selectbox":
                    if config.options:
                        options = self._resolve_options(config.options)
                        option_keys = list(options.keys())
                        # Find current selection index
                        current_idx = 0
                        for i, (name, opt_id) in enumerate(options.items()):
                            if opt_id == current_value:
                                current_idx = i
                                break
                        form_data[field.name] = st.selectbox(
                            label,
                            options=option_keys,
                            index=current_idx,
                            help=config.help
                        )
                        if form_data[field.name]:
                            form_data[field.name] = options[form_data[field.name]]
                    else:
                        form_data[field.name] = st.text_input(label, value=current_value or "", help=config.help)
                elif config.widget == "checkbox":
                    form_data[field.name] = st.checkbox(
                        label,
                        value=current_value if current_value is not None else (config.default if config.default is not None else False),
                        help=config.help
                    )
                elif config.widget == "multiselect":
                    if config.options:
                        options = config.options if isinstance(config.options, list) else list(config.options)
                        # Parse current value (stored as CSV)
                        current_list = current_value.split(",") if current_value else []
                        
                        if options and isinstance(options[0], tuple):
                            option_values = [value for _, value in options]
                            option_labels = {value: display_name for display_name, value in options}
                            selected = st.multiselect(
                                label,
                                options=option_values,
                                default=[v for v in current_list if v in option_values],
                                format_func=lambda x: option_labels.get(x, x),
                                help=config.help
                            )
                        else:
                            selected = st.multiselect(
                                label,
                                options=options,
                                default=[v for v in current_list if v in options],
                                help=config.help
                            )
                        form_data[field.name] = ",".join(selected) if selected else None
                    else:
                        form_data[field.name] = st.text_input(label, value=current_value or "", help=config.help)
                else:  # Default: text_input
                    form_data[field.name] = st.text_input(
                        label,
                        value=current_value or "",
                        help=config.help
                    )
            
            # is_active checkbox
            has_is_active = any(f.name == 'is_active' for f in model_fields)
            if has_is_active:
                form_data['is_active'] = st.checkbox(
                    "✅ Activo", 
                    value=item_dict.get('is_active', True),
                    help="Desmarcar para desactivar el registro"
                )
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
            with col2:
                cancelled = st.form_submit_button("❌ Cancelar", use_container_width=True)
            
            if submitted:
                self._handle_edit_submit(form_data)
            elif cancelled:
                del st.session_state[f"editing_{self._key_prefix}"]
                st.rerun()
    
    def _handle_edit_submit(self, form_data: Dict[str, Any]):
        """Handle edit form submission."""
        try:
            # Validate required fields
            for field_name, config in self.form_config.items():
                if config.required and not form_data.get(field_name):
                    st.error(f"⚠️ {config.label or field_name} es obligatorio")
                    return
            
            # Create entity instance with existing ID
            entity = self.model_class(**form_data)
            
            # Update
            self.service.save(entity)
            st.success("✅ Actualizado exitosamente")
            del st.session_state[f"editing_{self._key_prefix}"]
            st.rerun()
        except ValueError as e:
            st.error(f"⚠️ Error de validación: {e}")
        except Exception as e:
            error_msg = str(e)
            if "UNIQUE constraint failed" in error_msg:
                if "rut" in error_msg.lower():
                    st.error("⚠️ Ya existe otro registro con este RUT")
                elif "username" in error_msg.lower():
                    st.error("⚠️ Ya existe otro usuario con este nombre de usuario")
                elif "email" in error_msg.lower():
                    st.error("⚠️ Ya existe otro registro con este email")
                elif "license_plate" in error_msg.lower():
                    st.error("⚠️ Ya existe otro vehículo con esta patente")
                else:
                    st.error(f"⚠️ Ya existe otro registro con estos datos")
            else:
                st.error(f"❌ Error: {e}")
