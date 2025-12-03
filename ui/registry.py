"""
UI Registry System - Dynamic Menu and Module Registration

This module implements the Registry pattern for UI components, allowing
modules to self-register without modifying main.py.

Benefits:
- Open/Closed Principle: Add new modules without changing main.py
- Dynamic menu generation
- Future RBAC integration ready
- Clean separation of concerns

Usage:
    # In a module file (e.g., ui/modules/logistics.py)
    from ui.registry import UIRegistry, MenuItem
    
    @UIRegistry.auto_register("Operaciones", "🚛 Despacho", permission="dispatch")
    def dispatch_page(container):
        st.title("Dispatch")
        # ... implementation
    
    # Or register manually
    UIRegistry.register(
        category="Operaciones",
        item=MenuItem(
            title="Recepción",
            icon="📦",
            page_func=reception_page,
            permission_required="reception"
        )
    )
    
    # In main.py (automatic menu generation)
    menu = UIRegistry.get_menu()
    # Render sidebar from menu
"""

from typing import Callable, Dict, List, Optional
from dataclasses import dataclass, field
from functools import wraps
import streamlit as st


@dataclass
class MenuItem:
    """
    Represents a menu item in the UI.
    
    Attributes:
        title: Display name in menu
        icon: Emoji or icon to display
        page_func: Function to call when selected
        permission_required: Permission needed to access (for RBAC)
        order: Display order (lower = first)
        description: Optional tooltip/help text
        visible_for_roles: List of roles that can see this item
    """
    title: str
    icon: str
    page_func: Callable
    permission_required: Optional[str] = None
    order: int = 100
    description: Optional[str] = None
    visible_for_roles: Optional[List[str]] = None
    
    @property
    def display_title(self) -> str:
        """Returns title with icon for display."""
        return f"{self.icon} {self.title}"
    
    def is_visible_for_user(self, user_role: str) -> bool:
        """Check if menu item should be visible for user role."""
        if self.visible_for_roles is None:
            return True
        return user_role in self.visible_for_roles


class UIRegistry:
    """
    Central registry for UI pages and menu items.
    
    Modules self-register by calling UIRegistry.register() at import time.
    Main.py then generates the menu dynamically from the registry.
    
    Example:
        # Module registration (happens at import)
        UIRegistry.register("Operaciones", MenuItem(...))
        
        # Menu generation (in main.py)
        menu = UIRegistry.get_menu()
        for category, items in menu.items():
            st.sidebar.header(category)
            for item in items:
                if st.sidebar.button(item.display_title):
                    item.page_func(container)
    """
    
    # Private registry storage
    _pages: Dict[str, List[MenuItem]] = {}
    
    # Default categories (can be extended)
    DEFAULT_CATEGORIES = [
        "Mi Bandeja",      # Inbox, tasks
        "Operaciones",     # Daily operations
        "Gestión",         # Masters, configuration
        "Reportes",        # Reports and dashboards
        "Administración"   # System admin
    ]
    
    @classmethod
    def register(cls, category: str, item: MenuItem) -> None:
        """
        Register a menu item in a category.
        
        Args:
            category: Category name (e.g., "Operaciones", "Reportes")
            item: MenuItem to register
            
        Example:
            UIRegistry.register(
                "Operaciones",
                MenuItem(
                    title="Despacho",
                    icon="🚛",
                    page_func=dispatch_page,
                    permission_required="dispatch"
                )
            )
        """
        if category not in cls._pages:
            cls._pages[category] = []
        
        cls._pages[category].append(item)
        
        # Sort items by order
        cls._pages[category].sort(key=lambda x: (x.order, x.title))
    
    @classmethod
    def get_menu(cls, user_role: Optional[str] = None) -> Dict[str, List[MenuItem]]:
        """
        Get the complete menu structure.
        
        Args:
            user_role: Optional role to filter visible items
            
        Returns:
            Dictionary of category -> list of MenuItems
            
        Example:
            menu = UIRegistry.get_menu(user_role="operator")
            for category, items in menu.items():
                print(f"{category}:")
                for item in items:
                    print(f"  - {item.display_title}")
        """
        if user_role is None:
            return cls._pages.copy()
        
        # Filter items by role
        filtered_menu = {}
        for category, items in cls._pages.items():
            visible_items = [
                item for item in items 
                if item.is_visible_for_user(user_role)
            ]
            if visible_items:
                filtered_menu[category] = visible_items
        
        return filtered_menu
    
    @classmethod
    def get_category_items(cls, category: str, user_role: Optional[str] = None) -> List[MenuItem]:
        """
        Get all items in a specific category.
        
        Args:
            category: Category name
            user_role: Optional role to filter
            
        Returns:
            List of MenuItems in category
        """
        items = cls._pages.get(category, [])
        
        if user_role is None:
            return items
        
        return [item for item in items if item.is_visible_for_user(user_role)]
    
    @classmethod
    def get_all_categories(cls) -> List[str]:
        """Get list of all registered categories."""
        return list(cls._pages.keys())
    
    @classmethod
    def get_all_items(cls) -> Dict[str, List[MenuItem]]:
        """Get all registered items (alias for get_menu)."""
        return cls._pages.copy()
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registrations (useful for testing)."""
        cls._pages.clear()
    
    @classmethod
    def auto_register(
        cls, 
        category: str, 
        title: str,
        icon: str = "📄",
        permission: Optional[str] = None,
        order: int = 100,
        roles: Optional[List[str]] = None
    ):
        """
        Decorator for auto-registering page functions.
        
        Args:
            category: Menu category
            title: Display title
            icon: Display icon
            permission: Required permission
            order: Display order
            roles: Visible for these roles
            
        Example:
            @UIRegistry.auto_register("Operaciones", "Despacho", "🚛", order=10)
            def dispatch_page(container):
                st.title("Despacho")
                # ... implementation
        """
        def decorator(func: Callable):
            # Register the function
            cls.register(
                category,
                MenuItem(
                    title=title,
                    icon=icon,
                    page_func=func,
                    permission_required=permission,
                    order=order,
                    visible_for_roles=roles
                )
            )
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            return wrapper
        
        return decorator


class MenuBuilder:
    """
    Helper class to build Streamlit menus from UIRegistry.
    
    Example:
        builder = MenuBuilder(container, user)
        builder.render_sidebar()
        builder.render_selected_page()
    """
    
    def __init__(self, container, user):
        """
        Initialize menu builder.
        
        Args:
            container: Service container
            user: Current user object
        """
        self.container = container
        self.user = user
        self.menu = UIRegistry.get_menu(user_role=user.role if user else None)
    
    def render_sidebar(self) -> Optional[MenuItem]:
        """
        Render the sidebar menu and return selected item.
        
        Returns:
            Selected MenuItem or None
        """
        with st.sidebar:
            st.title("Biosolids ERP")
            if self.user:
                st.write(f"User: **{self.user.username}** ({self.user.role})")
            st.divider()
            
            # Category selection
            categories = list(self.menu.keys())
            if not categories:
                st.warning("No hay módulos disponibles")
                return None
            
            selected_category = st.selectbox(
                "Módulo",
                categories,
                key="menu_category"
            )
            
            # Page selection within category
            items = self.menu.get(selected_category, [])
            if not items:
                return None
            
            # Use radio for page selection
            page_titles = [item.display_title for item in items]
            selected_title = st.radio(
                "Actividad",
                page_titles,
                key="menu_page"
            )
            
            # Find selected item
            selected_item = next(
                (item for item in items if item.display_title == selected_title),
                None
            )
            
            st.divider()
            
            # Logout button
            if st.button("Logout"):
                st.session_state['user'] = None
                st.rerun()
            
            return selected_item
    
    def render_selected_page(self, selected_item: Optional[MenuItem]) -> None:
        """
        Render the selected page.
        
        Args:
            selected_item: MenuItem to render
        """
        if selected_item is None:
            st.info("Seleccione una página del menú lateral")
            return
        
        # Check permission (future RBAC integration)
        if selected_item.permission_required:
            # TODO: Check if user has permission
            # For now, just allow
            pass
        
        # Call the page function with container
        try:
            selected_item.page_func(self.container)
        except Exception as e:
            st.error(f"Error al cargar la página: {str(e)}")
            st.exception(e)


# ============================================================================
# EXAMPLE REGISTRATIONS (for reference)
# ============================================================================

"""
Example: How modules register themselves
-----------------------------------------

# ui/modules/logistics.py
from ui.registry import UIRegistry, MenuItem

def dispatch_page(container):
    st.title("🚛 Despacho")
    # ... implementation

def reception_page(container):
    st.title("📦 Recepción")
    # ... implementation

# Register at module level (runs at import)
UIRegistry.register(
    "Operaciones",
    MenuItem(
        title="Despacho",
        icon="🚛",
        page_func=dispatch_page,
        order=10,
        permission_required="dispatch"
    )
)

UIRegistry.register(
    "Operaciones",
    MenuItem(
        title="Recepción",
        icon="📦",
        page_func=reception_page,
        order=20,
        permission_required="reception"
    )
)

# Alternative: Using decorator
@UIRegistry.auto_register("Reportes", "Dashboard Logístico", "📊", order=10)
def logistics_dashboard_page(container):
    st.title("Dashboard Logístico")
    # ... implementation
"""
