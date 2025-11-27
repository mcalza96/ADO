from domain.exceptions import LogisticsException

class LogisticsRules:
    """
    Domain Service for Logistics and Load Control.
    """

    @staticmethod
    def calculate_net_weight(gross: float, tare: float) -> float:
        """
        Calculates Net Weight.
        Validates that Gross >= Tare.
        """
        if gross < 0 or tare < 0:
            raise LogisticsException("Weights cannot be negative.")
            
        if gross < tare:
            raise LogisticsException(f"Gross weight ({gross}) cannot be less than Tare weight ({tare}).")
            
        return gross - tare

    @staticmethod
    def validate_vehicle_capacity(net_weight: float, max_capacity: float) -> str:
        """
        Validates Net Weight against Vehicle Capacity.
        Returns a status: 'OK', 'WARNING', or raises LogisticsException for 'BLOCK'.
        """
        if net_weight > max_capacity * 1.10:
            # Critical Overweight (> 10% excess) -> BLOCK
            raise LogisticsException(f"CRITICAL OVERWEIGHT: Net {net_weight} exceeds Max {max_capacity} by >10%. Operation Blocked.")
        
        if net_weight > max_capacity:
            # Mild Overweight -> WARNING
            return "WARNING: Overweight detected but within tolerance."
            
        return "OK"
