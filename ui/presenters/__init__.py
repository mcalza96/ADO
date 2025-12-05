"""
UI Presenters Module

Este módulo contiene los presenters que transforman datos del dominio
a formatos listos para mostrar en la UI. Separa la lógica de transformación
de las vistas de Streamlit.

Patrón Presenter/ViewModel:
- Las vistas (views) solo se encargan de renderizar
- Los presenters se encargan de formatear, renombrar y calcular
- Mejora la testabilidad (los presenters son funciones puras)
"""

from .planning_presenter import PlanningPresenter
from .logistics_presenter import LogisticsPresenter
from .status_presenter import StatusPresenter

__all__ = [
    'PlanningPresenter',
    'LogisticsPresenter', 
    'StatusPresenter'
]
