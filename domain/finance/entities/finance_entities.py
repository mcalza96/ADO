from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime, date

# ==========================================
# Legacy Entities (backward compatibility)
# ==========================================

@dataclass
class RateSheet:
    """
    Tarifario para actividades.
    Ej: Transporte ($1000/km), Maquinaria ($50000/hora).
    """
    id: Optional[int]
    client_id: Optional[int] # Si es NULL, es tarifa base/default
    activity_type: str # 'TRANSPORTE', 'DISPOSICION', 'MAQUINARIA'
    
    unit_price: float
    unit_type: str # 'POR_KM', 'POR_TON', 'POR_HORA'
    
    currency: str = 'CLP'
    valid_from: datetime = None
    valid_to: Optional[datetime] = None

@dataclass
class CostRecord:
    """
    Registro de costo calculado para una operación específica.
    """
    id: Optional[int]
    related_entity_id: int # load_id o machine_log_id
    related_entity_type: str # 'LOAD' o 'MACHINE_LOG'
    
    amount: float
    currency: str = 'CLP'
    
    calculated_at: Optional[datetime] = None
    rate_sheet_id: Optional[int] = None # Trazabilidad de qué tarifa se usó


# ==========================================
# Financial Domain Entities
# ==========================================

@dataclass
class EconomicCycle:
    """
    Ciclo económico con indicadores financieros inmutables.
    
    Representa un período operacional (ej. del 19 de un mes al 18 del siguiente)
    con valores de referencia para UF y precio de combustible.
    
    Attributes:
        uf_value: Valor de la UF en CLP para este ciclo
        fuel_price: Precio de combustible de referencia en CLP/litro
        is_closed: Si True, el ciclo está cerrado y los valores son inmutables
        start_date: Fecha de inicio del ciclo
        end_date: Fecha de término del ciclo
    """
    uf_value: float
    fuel_price: float
    is_closed: bool
    start_date: date
    end_date: date
    
    def __post_init__(self):
        """Validación de negocio: end_date debe ser posterior a start_date."""
        if self.end_date <= self.start_date:
            raise ValueError(f"end_date ({self.end_date}) debe ser posterior a start_date ({self.start_date})")
        if self.uf_value <= 0:
            raise ValueError(f"uf_value debe ser positivo, recibido: {self.uf_value}")
        if self.fuel_price <= 0:
            raise ValueError(f"fuel_price debe ser positivo, recibido: {self.fuel_price}")


@dataclass
class TariffRule:
    """
    Regla tarifaria para cálculo de costos de transporte (Contractor side).
    
    Representa las condiciones contractuales con un transportista, incluyendo
    tarifa base, peso mínimo garantizado y precio base de combustible para
    ajuste polinómico.
    
    Attributes:
        base_rate_uf: Tarifa base en UF por ton-km (*** CHANGED from CLP ***)
        min_weight: Peso mínimo garantizado en toneladas (ej. 15t para Batea, 7t para Ampliroll)
        vehicle_type: Clasificación del vehículo ('BATEA', 'AMPLIROLL_SIMPLE', 'AMPLIROLL_CARRO')
        base_fuel_price: Precio de combustible de referencia en CLP/litro (usado para factor polinómico)
                         Nota: Este valor permanece en CLP porque calcula un factor adimensional:
                         factor = current_fuel_price (CLP) / base_fuel_price (CLP)
    """
    base_rate_uf: float  # *** RENAMED from base_rate ***
    min_weight: float
    vehicle_type: str
    base_fuel_price: float  # Permanece en CLP
    
    def __post_init__(self):
        """Validación de negocio."""
        if self.base_rate_uf <= 0:
            raise ValueError(f"base_rate_uf debe ser positivo, recibido: {self.base_rate_uf}")
        if self.min_weight < 0:
            raise ValueError(f"min_weight no puede ser negativo, recibido: {self.min_weight}")
        if self.base_fuel_price <= 0:
            raise ValueError(f"base_fuel_price debe ser positivo, recibido: {self.base_fuel_price}")
        if self.vehicle_type not in ('BATEA', 'AMPLIROLL_SIMPLE', 'AMPLIROLL_CARRO'):
            raise ValueError(f"vehicle_type inválido: {self.vehicle_type}")


@dataclass
class DistanceRoute:
    """
    Segmento de ruta en la matriz de distancias.
    
    Representa una conexión válida en el grafo de logística, permitiendo
    rutas directas (Planta→Sitio) o enlaces (Planta→Planta→Sitio).
    
    Attributes:
        origin_id: ID del nodo de origen (siempre una Facility)
        destination_id: ID del nodo de destino (Facility o Site)
        km: Distancia en kilómetros
        is_segment_link: True si es un tramo intermedio en un viaje consolidado (A→B en A→B→C)
    """
    origin_id: int
    destination_id: int
    km: float
    is_segment_link: bool = False
    
    def __post_init__(self):
        """Validación de negocio."""
        if self.km <= 0:
            raise ValueError(f"km debe ser positivo, recibido: {self.km}")


@dataclass
class TripCostResult:
    """
    Resultado del cálculo de costo de un viaje.
    
    Objeto de valor inmutable retornado por TransportCostCalculator.
    Incluye el costo total en UF y desglose detallado para auditoría.
    
    Attributes:
        total_cost_uf: Costo total calculado en UF (*** CHANGED from CLP ***)
        adjustment_factor: Multiplicador del polinomio de combustible aplicado
        applied_weight: Peso mayor entre real y mínimo garantizado (toneladas)
        details: Diccionario con desglose de costos por tramo en UF
                 Ejemplo: {"Tramo 1 (A→B)": 4.05, "Tramo 2 (B→C)": 7.56}
    """
    total_cost_uf: float  # *** RENAMED from total_cost_clp ***
    adjustment_factor: float
    applied_weight: float
    details: Dict[str, float] = field(default_factory=dict)
    
    def to_clp(self, uf_value: float) -> float:
        """
        Convierte el costo total a CLP usando el valor UF proporcionado.
        
        Args:
            uf_value: Valor de la UF en CLP (ej. 37000.0)
            
        Returns:
            Costo total en Pesos Chilenos (CLP)
            
        Example:
            >>> result = TripCostResult(total_cost_uf=10.5, adjustment_factor=1.2, applied_weight=20.0)
            >>> result.to_clp(uf_value=37000.0)
            388500.0
        """
        if uf_value <= 0:
            raise ValueError(f"uf_value debe ser positivo, recibido: {uf_value}")
        return self.total_cost_uf * uf_value


@dataclass
class ClientTariff:
    """
    Tarifa de cliente para cálculo de ingresos (Revenue side).
    
    Representa las tarifas de facturación al cliente en UF, por concepto
    (Transporte, Tratamiento, Disposición).
    
    Attributes:
        client_id: ID del cliente
        concept: Concepto de cobro ('TRANSPORTE', 'TRATAMIENTO', 'DISPOSICION')
        rate_uf: Tarifa en UF por tonelada
        min_weight: Peso mínimo garantizado en toneladas
        valid_from: Fecha de inicio de vigencia
        valid_to: Fecha de fin de vigencia (None = vigente actualmente)
    """
    client_id: int
    concept: str
    rate_uf: float
    min_weight: float
    valid_from: date
    valid_to: Optional[date] = None
    
    def __post_init__(self):
        """Validación de negocio."""
        if self.concept not in ('TRANSPORTE', 'TRATAMIENTO', 'DISPOSICION'):
            raise ValueError(f"concept inválido: {self.concept}")
        if self.rate_uf <= 0:
            raise ValueError(f"rate_uf debe ser positivo, recibido: {self.rate_uf}")
        if self.min_weight < 0:
            raise ValueError(f"min_weight no puede ser negativo, recibido: {self.min_weight}")
        if self.valid_to and self.valid_to <= self.valid_from:
            raise ValueError(f"valid_to ({self.valid_to}) debe ser posterior a valid_from ({self.valid_from})")


@dataclass
class RevenueResult:
    """
    Resultado del cálculo de ingresos de un cliente.
    
    Objeto de valor retornado por ClientRevenueCalculator.
    Incluye totales en UF y CLP, más desglose por concepto.
    
    Attributes:
        total_uf: Monto total en UF
        total_clp: Monto total en CLP (total_uf * uf_value)
        details: Diccionario con montos por concepto
                 Ejemplo: {"TRANSPORTE": 10.5, "DISPOSICION": 6.3, "TRATAMIENTO": 4.2}
    """
    total_uf: float
    total_clp: float
    details: Dict[str, float] = field(default_factory=dict)


# ==========================================
# Proforma Entity (Payment Statement Cycle)
# ==========================================

@dataclass
class Proforma:
    """
    Proforma / Estado de Pago - Ciclo financiero mensual.
    
    Representa un período operacional que va del día 19 de un mes al día 18 del
    siguiente. Centraliza todos los indicadores financieros mensuales que se usan
    para los cálculos de estados de pago.
    
    Nomenclatura:
        - PROF 25-03: Proforma de marzo 2025 (19-Feb al 18-Mar)
        - El mes en el código corresponde al mes de CIERRE (día 18)
    
    Attributes:
        id: ID único en base de datos
        proforma_code: Código único (ej: "PROF 25-03")
        period_year: Año del período (ej: 2025)
        period_month: Mes del período (1-12, corresponde al mes de cierre)
        cycle_start_date: Fecha inicio del ciclo (día 19 del mes anterior)
        cycle_end_date: Fecha fin del ciclo (día 18 del mes actual)
        uf_value: Valor de la UF en CLP al día 18 del ciclo
        fuel_price: Precio promedio del petróleo/diésel en CLP/litro
        tariff_batea_uf: Tarifa para vehículos Batea en UF/ton-km (6 decimales)
        tariff_ampliroll_uf: Tarifa para Ampliroll simple en UF/ton-km (6 decimales)
        tariff_ampliroll_carro_uf: Tarifa para Ampliroll+Carro en UF/ton-km (6 decimales)
        is_closed: True si la proforma está cerrada (valores inmutables)
        extra_indicators: Diccionario para indicadores adicionales futuros
                         (ej: {"costo_area_central": 1500000, "ipc": 0.3})
        created_at: Fecha de creación del registro
        updated_at: Fecha de última actualización
    
    Business Rules:
        - Una vez cerrada (is_closed=True), los valores no pueden modificarse
        - Solo puede existir una proforma por período (period_year, period_month)
        - Al cerrar una proforma, se debe crear automáticamente la siguiente
        - Las tarifas de la primera proforma (base) son editables manualmente
        - Las tarifas de proformas siguientes se calculan: tarifa_nueva = tarifa_anterior × (fuel_nuevo / fuel_anterior)
    """
    id: Optional[int]
    proforma_code: str
    period_year: int
    period_month: int
    cycle_start_date: date
    cycle_end_date: date
    uf_value: float
    fuel_price: float
    tariff_batea_uf: Optional[float] = None  # UF/ton-km, 6 decimales
    tariff_ampliroll_uf: Optional[float] = None  # UF/ton-km, 6 decimales
    tariff_ampliroll_carro_uf: Optional[float] = None  # UF/ton-km, 6 decimales
    is_closed: bool = False
    extra_indicators: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validación de reglas de negocio."""
        if self.period_month < 1 or self.period_month > 12:
            raise ValueError(f"period_month debe estar entre 1 y 12, recibido: {self.period_month}")
        if self.period_year < 2020 or self.period_year > 2100:
            raise ValueError(f"period_year debe estar entre 2020 y 2100, recibido: {self.period_year}")
        if self.uf_value <= 0:
            raise ValueError(f"uf_value debe ser positivo, recibido: {self.uf_value}")
        if self.fuel_price <= 0:
            raise ValueError(f"fuel_price debe ser positivo, recibido: {self.fuel_price}")
        if self.cycle_end_date <= self.cycle_start_date:
            raise ValueError(
                f"cycle_end_date ({self.cycle_end_date}) debe ser posterior a "
                f"cycle_start_date ({self.cycle_start_date})"
            )
    
    @staticmethod
    def generate_code(year: int, month: int) -> str:
        """
        Genera el código de proforma para un período.
        
        Args:
            year: Año (ej: 2025)
            month: Mes (1-12)
            
        Returns:
            Código en formato "PROF YY-MM" (ej: "PROF 25-03")
        """
        return f"PROF {year % 100:02d}-{month:02d}"
    
    @staticmethod
    def calculate_cycle_dates(year: int, month: int) -> tuple:
        """
        Calcula las fechas de inicio y fin del ciclo.
        
        El ciclo va del día 19 del mes anterior al día 18 del mes actual.
        
        Args:
            year: Año del período de cierre
            month: Mes del período de cierre (1-12)
            
        Returns:
            Tuple (cycle_start_date, cycle_end_date)
            
        Example:
            >>> Proforma.calculate_cycle_dates(2025, 3)
            (date(2025, 2, 19), date(2025, 3, 18))
        """
        from dateutil.relativedelta import relativedelta
        
        # Fecha de cierre: día 18 del mes indicado
        cycle_end = date(year, month, 18)
        
        # Fecha de inicio: día 19 del mes anterior
        previous_month = date(year, month, 1) - relativedelta(months=1)
        cycle_start = date(previous_month.year, previous_month.month, 19)
        
        return cycle_start, cycle_end
    
    def to_economic_cycle(self) -> 'EconomicCycle':
        """
        Convierte a EconomicCycle para compatibilidad con servicios existentes.
        
        Returns:
            EconomicCycle con los mismos valores financieros
        """
        return EconomicCycle(
            uf_value=self.uf_value,
            fuel_price=self.fuel_price,
            is_closed=self.is_closed,
            start_date=self.cycle_start_date,
            end_date=self.cycle_end_date
        )
    
    def get_period_key(self) -> str:
        """
        Retorna la clave del período en formato YYYY-MM.
        
        Returns:
            String en formato "YYYY-MM" (ej: "2025-03")
        """
        return f"{self.period_year}-{self.period_month:02d}"
    
    def get_tariff_for_vehicle_type(self, vehicle_type: str) -> Optional[float]:
        """
        Obtiene la tarifa correspondiente según el tipo de vehículo.
        
        Args:
            vehicle_type: Tipo de vehículo ('BATEA', 'AMPLIROLL', 'AMPLIROLL_SIMPLE', 'AMPLIROLL_CARRO')
            
        Returns:
            Tarifa en UF/ton-km o None si no está configurada
        """
        vehicle_type_upper = vehicle_type.upper() if vehicle_type else ''
        
        if vehicle_type_upper == 'BATEA':
            return self.tariff_batea_uf
        elif vehicle_type_upper in ('AMPLIROLL', 'AMPLIROLL_SIMPLE'):
            return self.tariff_ampliroll_uf
        elif vehicle_type_upper == 'AMPLIROLL_CARRO':
            return self.tariff_ampliroll_carro_uf
        else:
            return None
    
    def calculate_tariffs_from_previous(self, previous: 'Proforma') -> None:
        """
        Calcula las tarifas de esta proforma basándose en la anterior.
        
        Fórmula polinómica de ajuste por combustible:
        tarifa_nueva = tarifa_anterior × (1 + 0.5 × (fuel_nuevo - fuel_anterior) / fuel_anterior)
        
        El factor 0.5 representa que las tarifas se ajustan proporcionalmente
        a la mitad de la variación porcentual del combustible.
        
        Args:
            previous: Proforma anterior con tarifas base
        """
        if previous.fuel_price and previous.fuel_price > 0:
            # Factor de ajuste polinómico: 1 + 0.5 × variación_porcentual_combustible
            fuel_variation = (self.fuel_price - previous.fuel_price) / previous.fuel_price
            adjustment_factor = 1 + 0.5 * fuel_variation
            
            if previous.tariff_batea_uf:
                self.tariff_batea_uf = round(previous.tariff_batea_uf * adjustment_factor, 6)
            if previous.tariff_ampliroll_uf:
                self.tariff_ampliroll_uf = round(previous.tariff_ampliroll_uf * adjustment_factor, 6)
            if previous.tariff_ampliroll_carro_uf:
                self.tariff_ampliroll_carro_uf = round(previous.tariff_ampliroll_carro_uf * adjustment_factor, 6)
    
    def has_tariffs(self) -> bool:
        """
        Verifica si la proforma tiene al menos una tarifa configurada.
        
        Returns:
            True si tiene al menos una tarifa definida
        """
        return any([
            self.tariff_batea_uf is not None,
            self.tariff_ampliroll_uf is not None,
            self.tariff_ampliroll_carro_uf is not None
        ])
