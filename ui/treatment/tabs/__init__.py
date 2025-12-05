"""
Treatment Operations Tabs Module.

Each tab from the treatment operations page is extracted into its own module
following the Single Responsibility Principle.
"""

from ui.treatment.tabs.reception_view import render as render_reception

__all__ = ['render_reception']
