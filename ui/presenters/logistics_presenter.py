"""
Logistics Presenter - Transforma datos para dashboards logísticos

Responsabilidades:
- Formatear DataFrames de monitoreo de flota
- Aplicar estilos condicionales (colores de alerta)
- Calcular métricas de demora y espera
"""

import pandas as pd
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass


@dataclass
class FleetMetrics:
    """Métricas agregadas de la flota."""
    en_ruta: int = 0
    atrasados: int = 0
    en_cola: int = 0
    espera_larga: int = 0
    
    @property
    def has_alerts(self) -> bool:
        """Indica si hay alertas activas."""
        return self.atrasados > 0 or self.espera_larga > 0


class LogisticsPresenter:
    """
    Presenter para dashboards de logística.
    
    Encapsula toda la lógica de formateo y cálculo de métricas.
    """
    
    # Constantes de umbral (pueden configurarse externamente)
    DELAY_THRESHOLD_HOURS = 4.0
    WAITING_ALERT_HOURS = 2.0
    
    @classmethod
    def calculate_fleet_metrics(
        cls,
        df_dispatched: pd.DataFrame,
        df_arrived: pd.DataFrame
    ) -> FleetMetrics:
        """
        Calcula métricas agregadas de la flota.
        
        Args:
            df_dispatched: DataFrame de camiones en ruta
            df_arrived: DataFrame de camiones en cola
            
        Returns:
            FleetMetrics con conteos y alertas
        """
        delayed = 0
        long_wait = 0
        
        if not df_dispatched.empty and 'hours_elapsed' in df_dispatched.columns:
            delayed = len(df_dispatched[df_dispatched['hours_elapsed'] > cls.DELAY_THRESHOLD_HOURS])
        
        if not df_arrived.empty and 'waiting_time' in df_arrived.columns:
            long_wait = len(df_arrived[df_arrived['waiting_time'] > cls.WAITING_ALERT_HOURS])
        
        return FleetMetrics(
            en_ruta=len(df_dispatched),
            atrasados=delayed,
            en_cola=len(df_arrived),
            espera_larga=long_wait
        )
    
    @classmethod
    def format_dispatched_table(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Formatea la tabla de camiones despachados.
        
        Args:
            df: DataFrame crudo del servicio
            
        Returns:
            DataFrame con columnas renombradas para display
        """
        if df.empty:
            return df
        
        # Columnas a mostrar
        display_cols = [
            'load_id', 'license_plate', 'driver_name',
            'facility_name', 'site_name', 'dispatch_time',
            'hours_elapsed', 'weight_net', 'ticket_number'
        ]
        
        available = [c for c in display_cols if c in df.columns]
        result = df[available].copy()
        
        # Renombrar para presentación
        result = result.rename(columns={
            'load_id': 'ID',
            'license_plate': 'Patente',
            'driver_name': 'Conductor',
            'facility_name': 'Origen',
            'site_name': 'Destino',
            'dispatch_time': 'Hora Salida',
            'hours_elapsed': 'Tiempo Viaje (h)',
            'weight_net': 'Peso Neto (kg)',
            'ticket_number': 'Ticket'
        })
        
        return result
    
    @classmethod
    def format_arrived_table(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Formatea la tabla de camiones en cola.
        
        Args:
            df: DataFrame crudo del servicio
            
        Returns:
            DataFrame con columnas renombradas para display
        """
        if df.empty:
            return df
        
        display_cols = [
            'load_id', 'license_plate', 'driver_name',
            'site_name', 'arrival_time', 'hours_elapsed',
            'waiting_time', 'weight_arrival', 'ticket_number'
        ]
        
        available = [c for c in display_cols if c in df.columns]
        result = df[available].copy()
        
        result = result.rename(columns={
            'load_id': 'ID',
            'license_plate': 'Patente',
            'driver_name': 'Conductor',
            'site_name': 'Sitio',
            'arrival_time': 'Hora Llegada',
            'hours_elapsed': 'Duración Viaje (h)',
            'waiting_time': 'Tiempo Espera (h)',
            'weight_arrival': 'Peso Báscula (kg)',
            'ticket_number': 'Ticket'
        })
        
        return result
    
    @classmethod
    def get_delay_highlighter(cls) -> Callable:
        """
        Retorna función de estilo para resaltar demoras.
        
        Returns:
            Callable para usar con DataFrame.style.apply()
        """
        def highlight_delayed(row):
            if 'Tiempo Viaje (h)' in row and row['Tiempo Viaje (h)'] > cls.DELAY_THRESHOLD_HOURS:
                return ['background-color: #ffcccc'] * len(row)
            return [''] * len(row)
        return highlight_delayed
    
    @classmethod
    def get_waiting_highlighter(cls) -> Callable:
        """
        Retorna función de estilo para resaltar esperas largas.
        
        Returns:
            Callable para usar con DataFrame.style.apply()
        """
        def highlight_waiting(row):
            if 'Tiempo Espera (h)' in row and row['Tiempo Espera (h)'] > cls.WAITING_ALERT_HOURS:
                return ['background-color: #fff3cd'] * len(row)
            return [''] * len(row)
        return highlight_waiting
    
    @staticmethod
    def get_format_dict() -> Dict[str, str]:
        """
        Retorna diccionario de formato para columnas numéricas.
        
        Returns:
            Dict para usar con DataFrame.style.format()
        """
        return {
            'Tiempo Viaje (h)': "{:.1f}",
            'Tiempo Espera (h)': "{:.1f}",
            'Duración Viaje (h)': "{:.1f}",
            'Peso Neto (kg)': "{:,.0f}",
            'Peso Báscula (kg)': "{:,.0f}",
        }
