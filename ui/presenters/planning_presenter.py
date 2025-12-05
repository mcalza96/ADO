"""
Planning Presenter - Transforma datos para la vista de planificación

Responsabilidades:
- Convertir listas de cargas a DataFrames con columnas renombradas
- Formatear fechas y horas
- Calcular destinos combinados (predio o planta)
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PlanningLoadViewModel:
    """ViewModel para una carga en la vista de planificación."""
    id: int
    fecha_solicitud: str
    origen: str
    estado: str


@dataclass  
class ScheduledLoadViewModel:
    """ViewModel para una carga programada."""
    id: int
    fecha: str
    hora: str
    origen: str
    destino: str
    transportista: str
    patente: str
    conductor: str
    estado: str


class PlanningPresenter:
    """
    Presenter para la vista de planificación.
    
    Transforma datos crudos del servicio a ViewModels listos para renderizar.
    """
    
    @staticmethod
    def get_origin_vehicle_restriction(df: pd.DataFrame, selected_rows: List[int]) -> Optional[str]:
        """
        Obtiene la restricción de tipos de vehículos del origen de las cargas seleccionadas.
        
        Args:
            df: DataFrame con las cargas
            selected_rows: Índices de filas seleccionadas
            
        Returns:
            CSV de tipos permitidos o None si no hay restricción
        """
        if 'origin_allowed_vehicle_types' not in df.columns or df.empty:
            return None
        
        # Obtener restricciones únicas de las cargas seleccionadas
        restrictions = df.iloc[selected_rows]['origin_allowed_vehicle_types'].dropna().unique()
        
        if len(restrictions) == 0:
            return None
        
        # Si todas las cargas tienen la misma restricción, usarla
        if len(restrictions) == 1:
            return restrictions[0] if restrictions[0] else None
        
        # Si hay múltiples restricciones diferentes, encontrar intersección
        # Por ahora retornamos la primera (las cargas deberían ser del mismo origen)
        return restrictions[0] if restrictions[0] else None
    
    @staticmethod
    def format_backlog_loads(loads: List[Any]) -> pd.DataFrame:
        """
        Transforma cargas en backlog a DataFrame para mostrar.
        
        Args:
            loads: Lista de cargas (dicts o objetos) del servicio
            
        Returns:
            DataFrame con columnas renombradas listas para UI
        """
        if not loads:
            return pd.DataFrame()
        
        df = pd.DataFrame(loads)
        
        # Mapeo de columnas visibles: nombre_original -> nombre_display
        column_mapping = {
            'id': 'ID',
            'created_at': 'Fecha Solicitud',
            'origin_facility_name': 'Origen',
            'status': 'Estado'
        }
        
        # Columnas ocultas necesarias para lógica (no se muestran pero se usan)
        hidden_columns = ['origin_allowed_vehicle_types']
        
        # Seleccionar columnas visibles y ocultas
        available_visible = [col for col in column_mapping.keys() if col in df.columns]
        available_hidden = [col for col in hidden_columns if col in df.columns]
        
        # Crear DataFrame con columnas visibles renombradas
        result_df = df[available_visible].rename(columns=column_mapping)
        
        # Agregar columnas ocultas sin renombrar
        for col in available_hidden:
            result_df[col] = df[col]
        
        return result_df
    
    @staticmethod
    def format_scheduled_loads(loads: List[Any]) -> pd.DataFrame:
        """
        Transforma cargas programadas a DataFrame para mostrar.
        
        Args:
            loads: Lista de cargas programadas del servicio
            
        Returns:
            DataFrame con fechas formateadas y destino combinado
        """
        if not loads:
            return pd.DataFrame()
        
        df = pd.DataFrame(loads)
        
        # Formatear fecha y hora si existe scheduled_date
        if 'scheduled_date' in df.columns:
            df['Fecha'] = pd.to_datetime(df['scheduled_date']).dt.strftime('%d/%m/%Y')
            df['Hora'] = pd.to_datetime(df['scheduled_date']).dt.strftime('%H:%M')
        else:
            df['Fecha'] = '-'
            df['Hora'] = '-'
        
        # Combinar destino (predio o planta)
        df['Destino'] = df.apply(
            lambda x: x.get('destination_site_name') 
                      if pd.notna(x.get('destination_site_name')) 
                      else x.get('destination_plant_name', '-'), 
            axis=1
        )
        
        # Mapeo de columnas
        column_mapping = {
            'id': 'ID',
            'origin_facility_name': 'Origen',
            'contractor_name': 'Transportista',
            'vehicle_plate': 'Patente',
            'driver_name': 'Conductor',
            'status': 'Estado'
        }
        
        # Renombrar columnas existentes
        df = df.rename(columns=column_mapping)
        
        # Seleccionar columnas para display
        display_columns = ['ID', 'Fecha', 'Hora', 'Origen', 'Destino', 
                          'Transportista', 'Patente', 'Conductor', 'Estado']
        available = [col for col in display_columns if col in df.columns]
        
        return df[available]
    
    @staticmethod
    def get_selected_load_ids(df: pd.DataFrame, selected_rows: List[int]) -> List[int]:
        """
        Extrae los IDs de las cargas seleccionadas.
        
        Args:
            df: DataFrame con columna 'ID'
            selected_rows: Índices de filas seleccionadas
            
        Returns:
            Lista de IDs de carga
        """
        if not selected_rows or df.empty:
            return []
        
        return df.iloc[selected_rows]["ID"].tolist()
