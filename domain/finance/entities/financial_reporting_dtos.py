"""
DTOs for Financial Reporting Module.

These data transfer objects structure the results of monthly settlement calculations.
"""

from dataclasses import dataclass, field
from typing import Dict
import pandas as pd


@dataclass
class ContractorSettlement:
    """
    Single row of contractor cost settlement.
    
    Represents the billable amount for one load transported by a contractor.
    All monetary values are in UF (Unidad de Fomento).
    
    Attributes:
        load_id: ID of the load
        manifest_number: Load manifest/guide number
        vehicle_plate: License plate of the vehicle
        date: Date of the trip (ISO format string)
        origin_name: Name of origin facility
        destination_name: Name of destination (site or plant)
        billable_weight: max(real_weight, min_guaranteed) in tons
        base_rate_uf: Contractual base rate in UF per ton-km
        fuel_factor: Polynomial adjustment factor for fuel price variation
        adjusted_rate_uf: base_rate_uf * fuel_factor
        distance_km: Distance traveled in kilometers
        subtotal_uf: billable_weight * distance_km * adjusted_rate_uf
    """
    load_id: int
    manifest_number: str
    vehicle_plate: str
    date: str
    origin_name: str
    destination_name: str
    billable_weight: float
    base_rate_uf: float
    fuel_factor: float
    adjusted_rate_uf: float
    distance_km: float
    subtotal_uf: float


@dataclass
class DisposalCostSettlement:
    """
    Single row of disposal site cost settlement.
    
    Represents the cost to pay a disposal site for receiving waste.
    All monetary values are in UF (Unidad de Fomento).
    
    Attributes:
        load_id: ID of the load
        manifest_number: Load manifest/guide number
        site_name: Name of the disposal site
        date: Date of disposal (ISO format string)
        billable_weight: max(real_weight, min_guaranteed) in tons
        rate_uf: Tariff rate in UF per ton
        subtotal_uf: billable_weight * rate_uf
    """
    load_id: int
    manifest_number: str
    site_name: str
    date: str
    billable_weight: float
    rate_uf: float
    subtotal_uf: float


@dataclass
class ClientSettlement:
    """
    Single row of client revenue settlement.
    
    Represents the billable amount to charge a client for one service.
    All monetary values are in UF (Unidad de Fomento).
    
    Attributes:
        load_id: ID of the load
        manifest_number: Load manifest/guide number
        client_name: Name of the client
        date: Date of the service (ISO format string)
        weight: Weight in tons (may apply min_guaranteed)
        concept: Billing concept ('TRANSPORTE', 'DISPOSICION', 'TRATAMIENTO')
        rate_uf: Tariff rate in UF per ton
        subtotal_uf: weight * rate_uf
    """
    load_id: int
    manifest_number: str
    client_name: str
    date: str
    weight: float
    concept: str
    rate_uf: float
    subtotal_uf: float


@dataclass
class SettlementResult:
    """
    Complete monthly settlement result.
    
    Contains all data needed for financial proforma view:
    - Economic cycle metadata (UF value, fuel price, dates)
    - Contractor costs (transport expenses to pay)
    - Disposal costs (site expenses to pay)
    - Client revenues (income to collect)
    
    Architecture Invariant:
        All calculations are performed in UF. Conversion to CLP is done
        only at the presentation layer using cycle_info['uf_value'].
    
    Attributes:
        cycle_info: Dict with economic cycle metadata
                   Keys: period_key, uf_value, fuel_price, start_date, end_date
        contractor_df: DataFrame with contractor (transport) settlement details
                      Columns align with ContractorSettlement fields
        disposal_df: DataFrame with disposal site cost details
                    Columns align with DisposalCostSettlement fields
        client_df: DataFrame with client settlement details
                  Columns align with ClientSettlement fields
        total_transport_costs_uf: Sum of contractor_df['subtotal_uf']
        total_disposal_costs_uf: Sum of disposal_df['subtotal_uf']
        total_costs_uf: total_transport_costs_uf + total_disposal_costs_uf
        total_revenue_uf: Sum of client_df['subtotal_uf']
    """
    cycle_info: Dict[str, any]
    contractor_df: pd.DataFrame
    disposal_df: pd.DataFrame
    client_df: pd.DataFrame
    total_transport_costs_uf: float
    total_disposal_costs_uf: float
    total_costs_uf: float
    total_revenue_uf: float
    
    def get_margin_uf(self) -> float:
        """
        Calculate profit margin in UF.
        
        Returns:
            total_revenue_uf - total_costs_uf
        """
        return self.total_revenue_uf - self.total_costs_uf
    
    def to_clp_conversion(self) -> Dict[str, float]:
        """
        Convert all UF totals to CLP using the cycle's UF value.
        
        Returns:
            Dict with keys: total_costs_clp, total_revenue_clp, margin_clp
        """
        uf_value = self.cycle_info['uf_value']
        return {
            'total_transport_costs_clp': self.total_transport_costs_uf * uf_value,
            'total_disposal_costs_clp': self.total_disposal_costs_uf * uf_value,
            'total_costs_clp': self.total_costs_uf * uf_value,
            'total_revenue_clp': self.total_revenue_uf * uf_value,
            'margin_clp': self.get_margin_uf() * uf_value
        }

