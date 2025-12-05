"""
Disposal Operations Tabs Module.

Each tab from the disposal operations page is extracted into its own module
following the Single Responsibility Principle.
"""

from ui.disposal.tabs.reception_view import render as render_reception
from ui.disposal.tabs.disposal_view import render as render_disposal
from ui.disposal.tabs.preparation_view import render as render_preparation
from ui.disposal.tabs.closure_view import render as render_closure

__all__ = [
    'render_reception',
    'render_disposal', 
    'render_preparation',
    'render_closure'
]
