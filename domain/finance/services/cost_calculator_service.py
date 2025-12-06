"""
Motor de Cálculo de Costos de Transporte.

Este módulo implementa la lógica compleja de cálculo de costos operacionales,
incluyendo manejo de viajes consolidados (enlaces), pesos mínimos garantizados
y ajuste por variación de combustible.

Responsabilidad: Lógica de negocio pura. NO accede a base de datos.
"""

from typing import List, Dict, TYPE_CHECKING

# Import solo para type checking, no en runtime (evita dependencias circulares)
if TYPE_CHECKING:
    from domain.logistics.entities.load import Load

from domain.finance.entities.finance_entities import (
    DistanceRoute,
    TariffRule,
    EconomicCycle,
    TripCostResult
)
from domain.finance.services.tariff_adjustment_service import TariffAdjustmentService
from domain.shared.exceptions import InvalidRouteError, MissingTariffError


class TransportCostCalculator:
    """
    Motor de cálculo de costos de transporte para proveedores.
    
    Implementa reglas de negocio críticas:
    - Detección automática de viajes consolidados (enlaces)
    - Aplicación de pesos mínimos garantizados por tramo
    - Ajuste polinómico por variación de combustible
    - Diferenciación de tarifas según configuración vehicular
    """
    
    def calculate_trip_cost(
        self,
        loads: List['Load'],  # String literal para evitar NameError
        route_map: List[DistanceRoute],
        tariff: TariffRule,
        cycle: EconomicCycle
    ) -> TripCostResult:
        """
        Calcula el costo total de un viaje, considerando enlaces y mínimos garantizados.
        
        Lógica de Negocio:
        
        1. **Viaje Simple (1 carga)**:
           - Origen único → Destino único
           - Peso cobrado: max(peso_real, mínimo_garantizado)
           - Costo (UF): base_rate_uf × km × peso × factor_combustible  # *** CHANGED ***
        
        2. **Viaje Consolidado/Enlace (2+ cargas)**:
           - Ejemplo: Planta A (10t) → Planta B (8t) → Sitio C
           - Tramo 1 (A→B): "Camión Solo", peso = 10t, tarifa simple
           - Tramo 2 (B→C): "Camión + Carro", peso = 18t, tarifa compuesta
           - Cada tramo aplica su propio mínimo garantizado
        
        3. **Factor de Combustible**:
           - Se aplica uniformemente a todos los tramos
           - Factor = f(precio_actual, precio_base_contractual)
        
        Args:
            loads: Lista de cargas del viaje (1+ elementos)
            route_map: Matriz de distancias con rutas válidas
            tariff: Regla tarifaria aplicable (con min_weight y base_fuel_price)
            cycle: Ciclo económico con precio actual de combustible
        
        Returns:
            TripCostResult con costo total, factor aplicado y desglose por tramo
        
        Raises:
            InvalidRouteError: Si no se encuentra una ruta requerida en route_map
            MissingTariffError: Si falta información crítica en tariff
            ValueError: Si loads está vacía o contiene datos inválidos
        
        Example:
            >>> # Viaje simple: 1 carga de 20t, 50 km
            >>> loads = [Load(net_weight=20.0, origin_facility_id=1, destination_site_id=10)]
            >>> route_map = [DistanceRoute(origin_id=1, destination_id=10, km=50.0)]
            >>> tariff = TariffRule(base_rate_uf=0.027, min_weight=15, vehicle_type='BATEA', base_fuel_price=1000)
            >>> cycle = EconomicCycle(fuel_price=1200, uf_value=37000, is_closed=True, ...)
            >>> result = calculator.calculate_trip_cost(loads, route_map, tariff, cycle)
            >>> result.total_cost_uf
            32.4  # UF (0.027 * 50 * 20 * 1.2)
            >>> result.adjustment_factor
            1.2  # Combustible subió 20%
            >>> result.to_clp(uf_value=37000.0)
            1198800.0  # Conversión a CLP
        """
        # Validación de entrada
        if not loads:
            raise ValueError("La lista de cargas no puede estar vacía")
        
        if not tariff:
            raise MissingTariffError("Se requiere una TariffRule para calcular costos")
        
        # Calcular factor de ajuste por combustible (aplica a todos los tramos)
        fuel_factor = TariffAdjustmentService.calculate_fuel_factor(
            current_fuel_price=cycle.fuel_price,
            base_fuel_price=tariff.base_fuel_price
        )
        
        # Detectar tipo de viaje
        is_consolidated = len(loads) > 1
        
        if is_consolidated:
            return self._calculate_consolidated_trip(
                loads, route_map, tariff, fuel_factor
            )
        else:
            return self._calculate_single_trip(
                loads[0], route_map, tariff, fuel_factor
            )
    
    def _calculate_single_trip(
        self,
        load: 'Load',  # String literal
        route_map: List[DistanceRoute],
        tariff: TariffRule,
        fuel_factor: float
    ) -> TripCostResult:
        """
        Calcula costo de un viaje simple (1 origen → 1 destino).
        
        Args:
            load: Carga única del viaje
            route_map: Matriz de distancias
            tariff: Regla tarifaria
            fuel_factor: Factor de ajuste por combustible
        
        Returns:
            TripCostResult con costo calculado
        """
        # Buscar ruta desde origen a destino
        route = self._find_route(
            origin_id=load.origin_facility_id,
            destination_id=load.destination_site_id or load.destination_treatment_plant_id,
            route_map=route_map,
            is_segment=False
        )
        
        # Aplicar mínimo garantizado
        actual_weight = load.net_weight or 0.0
        billable_weight = max(actual_weight, tariff.min_weight)
        
        # Cálculo: UF = base_rate_uf × km × ton × fuel_factor
        base_cost_uf = tariff.base_rate_uf * route.km * billable_weight
        total_cost_uf = base_cost_uf * fuel_factor
        
        # Construir resultado
        return TripCostResult(
            total_cost_uf=total_cost_uf,
            adjustment_factor=fuel_factor,
            applied_weight=billable_weight,
            details={
                f"Tramo Único ({load.origin_facility_id}→{load.destination_site_id or load.destination_treatment_plant_id})": total_cost_uf,
                "base_cost_uf": base_cost_uf,
                "distance_km": route.km,
                "weight_tons": billable_weight
            }
        )
    
    def _calculate_consolidated_trip(
        self,
        loads: List['Load'],  # String literal
        route_map: List[DistanceRoute],
        tariff: TariffRule,
        fuel_factor: float
    ) -> TripCostResult:
        """
        Calcula costo de un viaje consolidado (enlace multi-hop).
        
        Lógica de Enlaces:
        - Tramo 1: Origen A → Origen B (pickup segment)
          * Peso: Carga A únicamente
          * Configuración: "Camión Solo" (puede ir vacío o con 1 carga)
        
        - Tramo 2: Origen B → Destino Final (main haul)
          * Peso: Suma de todas las cargas (A + B + ...)
          * Configuración: "Camión + Carro" (carga consolidada)
        
        Args:
            loads: Lista ordenada de cargas (2+ elementos)
            route_map: Matriz de distancias con segmentos marcados
            tariff: Regla tarifaria base
            fuel_factor: Factor de ajuste por combustible
        
        Returns:
            TripCostResult con costo total y desglose por tramo
        """
        total_cost_uf = 0.0
        details: Dict[str, float] = {}
        
        # Ordenar cargas por secuencia lógica (asumimos que vienen en orden correcto)
        # En producción, esto debería validarse o inferirse del campo load.segment_type
        
        # Tramo 1: Pickup Segment (Origen A → Origen B)
        # Solo la primera carga va en el camión
        first_load = loads[0]
        second_load = loads[1]
        
        pickup_route = self._find_route(
            origin_id=first_load.origin_facility_id,
            destination_id=second_load.origin_facility_id,
            route_map=route_map,
            is_segment=True  # Marcado como segmento intermedio
        )
        
        # Peso del tramo 1: solo primera carga
        pickup_weight = max(first_load.net_weight or 0.0, tariff.min_weight)
        pickup_base_cost_uf = tariff.base_rate_uf * pickup_route.km * pickup_weight
        pickup_total_cost_uf = pickup_base_cost_uf * fuel_factor
        
        total_cost_uf += pickup_total_cost_uf
        details[f"Tramo 1: Pickup ({first_load.origin_facility_id}→{second_load.origin_facility_id})"] = pickup_total_cost_uf
        
        # Tramo 2: Main Haul (Origen B → Destino Final)
        # Todas las cargas consolidadas
        final_destination = loads[-1].destination_site_id or loads[-1].destination_treatment_plant_id
        
        main_route = self._find_route(
            origin_id=second_load.origin_facility_id,
            destination_id=final_destination,
            route_map=route_map,
            is_segment=False
        )
        
        # Peso del tramo 2: suma de todas las cargas
        total_weight = sum(load.net_weight or 0.0 for load in loads)
        main_weight = max(total_weight, tariff.min_weight)
        main_base_cost_uf = tariff.base_rate_uf * main_route.km * main_weight
        main_total_cost_uf = main_base_cost_uf * fuel_factor
        
        total_cost_uf += main_total_cost_uf
        details[f"Tramo 2: Main Haul ({second_load.origin_facility_id}→{final_destination})"] = main_total_cost_uf
        
        # Metadata adicional
        details["total_distance_km"] = pickup_route.km + main_route.km
        details["consolidated_weight_tons"] = main_weight
        
        return TripCostResult(
            total_cost_uf=total_cost_uf,
            adjustment_factor=fuel_factor,
            applied_weight=main_weight,  # Peso máximo usado
            details=details
        )
    
    def _find_route(
        self,
        origin_id: int,
        destination_id: int,
        route_map: List[DistanceRoute],
        is_segment: bool
    ) -> DistanceRoute:
        """
        Busca una ruta en la matriz de distancias.
        
        Args:
            origin_id: ID del nodo de origen
            destination_id: ID del nodo de destino
            route_map: Lista de rutas disponibles
            is_segment: True si se busca un tramo intermedio (enlace)
        
        Returns:
            DistanceRoute encontrada
        
        Raises:
            InvalidRouteError: Si la ruta no existe en route_map
        """
        for route in route_map:
            if (route.origin_id == origin_id and
                route.destination_id == destination_id and
                route.is_segment_link == is_segment):
                return route
        
        # Ruta no encontrada
        segment_type = "enlace" if is_segment else "directa"
        raise InvalidRouteError(
            f"No se encontró ruta {segment_type} desde {origin_id} hasta {destination_id} "
            f"en la matriz de distancias. Verifique que la ruta esté configurada correctamente."
        )
