"""
Motor de Cálculo de Ingresos de Clientes.

Este módulo implementa la lógica de facturación al cliente, calculando
montos a cobrar por concepto (Transporte, Tratamiento, Disposición).

Responsabilidad: Lógica de negocio pura en UF y CLP. NO accede a base de datos.
"""

from typing import List, Dict, TYPE_CHECKING
from datetime import date

# Import solo para type checking, no en runtime (evita dependencias circulares)
if TYPE_CHECKING:
    from domain.logistics.entities.load import Load

from domain.finance.entities.finance_entities import ClientTariff, RevenueResult
from domain.shared.exceptions import MissingTariffError


class ClientRevenueCalculator:
    """
    Motor de cálculo de ingresos por facturación a clientes.
    
    Implementa reglas de negocio:
    - Cálculo independiente por concepto (Transporte, Disposición, Tratamiento)
    - Aplicación de mínimos garantizados específicos del cliente
    - Conversión automática UF → CLP
    - Tratamiento condicional (solo si el biosólido pasa por planta de tratamiento)
    """
    
    def calculate_load_revenue(
        self,
        load: 'Load',  # String literal para evitar NameError
        tariffs: List[ClientTariff],
        uf_value: float,
        calculation_date: date = None
    ) -> RevenueResult:
        """
        Calcula los ingresos a facturar al cliente por una carga.
        
        Lógica de Negocio:
        
        1. **Transporte**: Siempre se cobra (movimiento físico del biosólido)
        2. **Disposición**: Siempre se cobra (aplicación al campo)
        3. **Tratamiento**: Solo si load.goes_to_treatment == True
        
        Cada concepto:
        - Tiene su propia tarifa en UF/ton
        - Aplica su propio mínimo garantizado
        - Se calcula independientemente de los demás
        
        Conversión:
        - Cálculo base en UF (unidad indexada)
        - Conversión final: total_clp = total_uf × uf_value
        
        Args:
            load: Carga a facturar (debe tener net_weight, client_id, etc.)
            tariffs: Lista de tarifas del cliente (filtradas por client_id)
            uf_value: Valor de la UF en CLP para conversión
            calculation_date: Fecha para validar vigencia de tarifas (default: hoy)
        
        Returns:
            RevenueResult con total_uf, total_clp y desglose por concepto
        
        Raises:
            MissingTariffError: Si no se encuentra tarifa para un concepto obligatorio
            ValueError: Si load.net_weight es None o uf_value <= 0
        
        Example:
            >>> # Cliente con tarifas: Transporte 0.5 UF/t, Disposición 0.3 UF/t, Tratamiento 0.2 UF/t
            >>> load = Load(net_weight=20.0, goes_to_treatment=True, ...)
            >>> tariffs = [
            ...     ClientTariff(client_id=1, concept='TRANSPORTE', rate_uf=0.5, min_weight=6),
            ...     ClientTariff(client_id=1, concept='DISPOSICION', rate_uf=0.3, min_weight=6),
            ...     ClientTariff(client_id=1, concept='TRATAMIENTO', rate_uf=0.2, min_weight=0)
            ... ]
            >>> result = calculator.calculate_load_revenue(load, tariffs, uf_value=37000)
            >>> result.total_uf
            20.0  # (0.5 + 0.3 + 0.2) * 20
            >>> result.total_clp
            740000.0  # 20 UF * 37000 CLP/UF
        """
        # Validación de entrada
        if load.net_weight is None or load.net_weight <= 0:
            raise ValueError(
                f"load.net_weight debe ser positivo para calcular ingresos. "
                f"Recibido: {load.net_weight}"
            )
        
        if uf_value <= 0:
            raise ValueError(f"uf_value debe ser positivo. Recibido: {uf_value}")
        
        # Fecha de cálculo (para validar vigencia de tarifas)
        calc_date = calculation_date or date.today()
        
        # Filtrar tarifas vigentes en la fecha de cálculo
        active_tariffs = self._filter_active_tariffs(tariffs, calc_date)
        
        # Inicializar acumuladores
        total_uf = 0.0
        details_uf: Dict[str, float] = {}
        
        # 1. Calcular TRANSPORTE (obligatorio)
        transport_tariff = self._find_tariff(active_tariffs, 'TRANSPORTE')
        if not transport_tariff:
            raise MissingTariffError(
                f"No se encontró tarifa vigente de TRANSPORTE para el cliente. "
                f"Fecha: {calc_date}"
            )
        
        transport_uf = self._calculate_concept(
            weight=load.net_weight,
            tariff=transport_tariff
        )
        total_uf += transport_uf
        details_uf['TRANSPORTE'] = transport_uf
        
        # 2. Calcular DISPOSICION (obligatorio)
        disposal_tariff = self._find_tariff(active_tariffs, 'DISPOSICION')
        if not disposal_tariff:
            raise MissingTariffError(
                f"No se encontró tarifa vigente de DISPOSICION para el cliente. "
                f"Fecha: {calc_date}"
            )
        
        disposal_uf = self._calculate_concept(
            weight=load.net_weight,
            tariff=disposal_tariff
        )
        total_uf += disposal_uf
        details_uf['DISPOSICION'] = disposal_uf
        
        # 3. Calcular TRATAMIENTO (condicional)
        # Solo se cobra si el biosólido pasa por planta de tratamiento
        goes_to_treatment = getattr(load, 'goes_to_treatment', False)
        
        if goes_to_treatment:
            treatment_tariff = self._find_tariff(active_tariffs, 'TRATAMIENTO')
            if not treatment_tariff:
                raise MissingTariffError(
                    f"La carga requiere tratamiento pero no se encontró tarifa "
                    f"vigente de TRATAMIENTO para el cliente. Fecha: {calc_date}"
                )
            
            treatment_uf = self._calculate_concept(
                weight=load.net_weight,
                tariff=treatment_tariff
            )
            total_uf += treatment_uf
            details_uf['TRATAMIENTO'] = treatment_uf
        else:
            # Registro explícito de que no se cobra tratamiento
            details_uf['TRATAMIENTO'] = 0.0
        
        # Conversión UF → CLP
        total_clp = total_uf * uf_value
        
        # Construir resultado
        return RevenueResult(
            total_uf=total_uf,
            total_clp=total_clp,
            details=details_uf
        )
    
    def _filter_active_tariffs(
        self,
        tariffs: List[ClientTariff],
        calc_date: date
    ) -> List[ClientTariff]:
        """
        Filtra tarifas vigentes en una fecha específica.
        
        Una tarifa es vigente si:
        - calc_date >= tariff.valid_from
        - calc_date <= tariff.valid_to (o valid_to es None)
        
        Args:
            tariffs: Lista de tarifas a filtrar
            calc_date: Fecha de referencia
        
        Returns:
            Lista de tarifas vigentes
        """
        active = []
        for tariff in tariffs:
            # Verificar que la fecha esté en el rango de vigencia
            if tariff.valid_from <= calc_date:
                if tariff.valid_to is None or calc_date <= tariff.valid_to:
                    active.append(tariff)
        
        return active
    
    def _find_tariff(
        self,
        tariffs: List[ClientTariff],
        concept: str
    ) -> ClientTariff | None:
        """
        Busca una tarifa específica por concepto.
        
        Args:
            tariffs: Lista de tarifas donde buscar
            concept: Concepto a buscar ('TRANSPORTE', 'DISPOSICION', 'TRATAMIENTO')
        
        Returns:
            ClientTariff si se encuentra, None si no existe
        """
        for tariff in tariffs:
            if tariff.concept == concept:
                return tariff
        return None
    
    def _calculate_concept(
        self,
        weight: float,
        tariff: ClientTariff
    ) -> float:
        """
        Calcula el monto en UF para un concepto específico.
        
        Fórmula:
            Monto UF = rate_uf × max(peso_real, mínimo_garantizado)
        
        Args:
            weight: Peso real de la carga en toneladas
            tariff: Tarifa del concepto con rate_uf y min_weight
        
        Returns:
            Monto calculado en UF
        """
        # Aplicar mínimo garantizado
        billable_weight = max(weight, tariff.min_weight)
        
        # Cálculo: UF = rate_uf × toneladas
        amount_uf = tariff.rate_uf * billable_weight
        
        return amount_uf
