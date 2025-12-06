"""
Servicio de Ajuste Polinómico de Tarifas por Combustible.

Este módulo implementa la fórmula contractual para ajustar tarifas de transporte
según variaciones en el precio del combustible.

Responsabilidad: Cálculo puro del factor de ajuste. NO accede a base de datos.
"""

from domain.shared.exceptions import InvalidFuelPriceError


class TariffAdjustmentService:
    """
    Servicio estático para cálculo de factor de ajuste por combustible.
    
    Implementa la fórmula polinómica contractual que ajusta las tarifas base
    según la variación del precio del combustible respecto al precio de referencia.
    """
    
    @staticmethod
    def calculate_fuel_factor(current_fuel_price: float, base_fuel_price: float) -> float:
        """
        Calcula el factor de ajuste polinómico por variación de combustible.
        
        Fórmula contractual:
            Factor = 1 + (Precio_Actual - Precio_Base) / Precio_Base
        
        Ejemplo:
            >>> # Precio base: 1000 CLP/L, Precio actual: 1200 CLP/L
            >>> factor = TariffAdjustmentService.calculate_fuel_factor(1200.0, 1000.0)
            >>> factor
            1.2
            >>> # Interpretación: incremento del 20% sobre tarifa base
            
            >>> # Precio disminuye a 800 CLP/L
            >>> factor = TariffAdjustmentService.calculate_fuel_factor(800.0, 1000.0)
            >>> factor
            0.8
            >>> # Interpretación: descuento del 20% sobre tarifa base
        
        Args:
            current_fuel_price: Precio actual del combustible en CLP/litro
            base_fuel_price: Precio de referencia contractual en CLP/litro
        
        Returns:
            Factor multiplicador a aplicar sobre la tarifa base.
            - Factor > 1: El combustible subió, tarifa aumenta
            - Factor < 1: El combustible bajó, tarifa disminuye
            - Factor = 1: Sin cambio en precio de combustible
        
        Raises:
            InvalidFuelPriceError: Si base_fuel_price es <= 0 (división por cero)
        
        Notes:
            - Este servicio es STATELESS: no modifica estado ni accede a BD
            - Todos los datos necesarios se pasan como argumentos
            - El resultado depende únicamente de los inputs (función pura)
        """
        # Validación: Precio base debe ser positivo (evitar división por cero)
        if base_fuel_price <= 0:
            raise InvalidFuelPriceError(
                f"base_fuel_price debe ser positivo, recibido: {base_fuel_price}. "
                "No se puede calcular el factor de ajuste con precio base cero o negativo."
            )
        
        # Aplicar fórmula polinómica contractual
        # Factor = 1 + ΔPrecio/PrecioBase
        delta_price = current_fuel_price - base_fuel_price
        factor = 1.0 + (delta_price / base_fuel_price)
        
        return factor
