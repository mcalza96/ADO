"""
Financial Reporting Service.

Implements monthly settlement calculations using vectorized pandas operations.
Architecture: All calculations in UF, CLP conversion is presentation-only.
"""

from typing import List, Optional, Union
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd

from domain.logistics.repositories.load_repository import LoadRepository
from domain.finance.repositories.economic_indicators_repository import EconomicIndicatorsRepository
from domain.finance.repositories.proforma_repository import ProformaRepository
from domain.finance.repositories.contractor_tariffs_repository import ContractorTariffsRepository
from domain.finance.repositories.client_tariffs_repository import ClientTariffsRepository
from domain.finance.repositories.disposal_site_tariffs_repository import DisposalSiteTariffsRepository
from domain.logistics.repositories.distance_matrix_repository import DistanceMatrixRepository
from domain.finance.entities.finance_entities import Proforma
from domain.finance.entities.financial_reporting_dtos import (
    SettlementResult,
    ContractorSettlement,
    ClientSettlement,
    DisposalCostSettlement
)


class FinancialReportingService:
    """
    Service for generating monthly financial settlement reports.
    
    This service coordinates between multiple repositories to:
    1. Calculate cycle dates (19th to 18th)
    2. Retrieve economic snapshot (UF, fuel price)
    3. Calculate contractor costs (transport) with fuel polynomial adjustment
    4. Calculate disposal site costs (what sites charge per ton)
    5. Calculate client revenues
    6. Return structured settlement result
    
    All calculations are performed in UF. CLP conversion happens at UI layer.
    """
    
    def __init__(
        self,
        load_repo: LoadRepository,
        economic_repo: Union[EconomicIndicatorsRepository, ProformaRepository],
        contractor_tariffs_repo: ContractorTariffsRepository,
        client_tariffs_repo: ClientTariffsRepository,
        distance_repo: DistanceMatrixRepository,
        disposal_site_tariffs_repo: DisposalSiteTariffsRepository = None,
        proforma_repo: ProformaRepository = None
    ):
        self.load_repo = load_repo
        # Support both old EconomicIndicatorsRepository and new ProformaRepository
        self.economic_repo = economic_repo
        self.proforma_repo = proforma_repo or (
            economic_repo if isinstance(economic_repo, ProformaRepository) else None
        )
        self.contractor_tariffs_repo = contractor_tariffs_repo
        self.client_tariffs_repo = client_tariffs_repo
        self.distance_repo = distance_repo
        self.disposal_site_tariffs_repo = disposal_site_tariffs_repo
    
    def get_monthly_settlement(self, year: int, month: int) -> SettlementResult:
        """
        Generate complete monthly settlement for billing and payments.
        
        Process:
        1. Calculate cycle dates (19th of previous month to 18th of current month)
        2. Fetch economic indicators (UF value at closure, fuel price)
        3. Fetch completed loads in the cycle
        4. Calculate contractor costs (vectorized with pandas)
        5. Calculate client revenues (vectorized with pandas)
        6. Return SettlementResult
        
        Args:
            year: Year of the settlement (e.g., 2025)
            month: Month of the settlement (1-12)
            
        Returns:
            SettlementResult with all settlement data
            
        Raises:
            ValueError: If economic indicators are missing for the period
            ValueError: If year/month are invalid
            
        Example:
            >>> service.get_monthly_settlement(2025, 11)
            SettlementResult(
                cycle_info={'period_key': '2025-11', 'uf_value': 37000.0, ...},
                contractor_df=<DataFrame with 50 rows>,
                client_df=<DataFrame with 50 rows>,
                total_costs_uf=450.23,
                total_revenue_uf=680.50
            )
        """
        # Validate inputs
        if not (1 <= month <= 12):
            raise ValueError(f"Invalid month: {month}. Must be between 1 and 12.")
        if year < 2020 or year > 2100:
            raise ValueError(f"Invalid year: {year}. Must be between 2020 and 2100.")
        
        # Step 1: Calculate cycle dates
        cycle_start, cycle_end = self._calculate_cycle_dates(year, month)
        
        # Step 2: Fetch proforma/economic indicators
        proforma = None
        economic_indicators = None
        
        # Prefer ProformaRepository if available
        if self.proforma_repo:
            proforma = self.proforma_repo.get_by_period(year, month)
            if proforma:
                economic_indicators = {
                    'period_key': proforma.get_period_key(),
                    'proforma_code': proforma.proforma_code,
                    'uf_value': proforma.uf_value,
                    'fuel_price': proforma.fuel_price,
                    'extra_indicators': proforma.extra_indicators,
                    'is_closed': proforma.is_closed
                }
        
        # Fallback to EconomicIndicatorsRepository for backward compatibility
        if not economic_indicators and self.economic_repo:
            economic_indicators = self.economic_repo.get_by_period(year, month)
        
        if not economic_indicators:
            raise ValueError(
                f"No se puede generar el reporte: Faltan Indicadores Económicos para "
                f"{self._format_month_name(month)} {year}"
            )
        
        # Validate required fields
        if not economic_indicators.get('uf_value') or economic_indicators['uf_value'] <= 0:
            raise ValueError(
                f"Valor de UF inválido para {self._format_month_name(month)} {year}. "
                f"Por favor configure el valor de la UF en el Maestro de Proformas."
            )
        
        if not economic_indicators.get('fuel_price') or economic_indicators['fuel_price'] <= 0:
            raise ValueError(
                f"Precio de Combustible inválido para {self._format_month_name(month)} {year}. "
                f"Por favor configure el precio del diésel en el Maestro de Proformas."
            )
        
        # Step 3: Fetch completed loads in the cycle
        loads_data = self._fetch_loads_in_cycle(cycle_start, cycle_end)
        
        # Step 4: Calculate contractor costs (vectorized) - TRANSPORT
        # Usar tarifas desde la Proforma del período
        contractor_df = self._calculate_contractor_costs(
            loads_data,
            fuel_price_month=economic_indicators['fuel_price'],
            proforma=proforma
        )
        
        # Step 5: Calculate disposal site costs (vectorized) - DISPOSAL
        disposal_df = self._calculate_disposal_costs(loads_data)
        
        # Step 6: Calculate client revenues (vectorized)
        client_df = self._calculate_client_revenues(loads_data)
        
        # Step 7: Build result with separated costs
        total_transport_costs_uf = contractor_df['subtotal_uf'].sum() if not contractor_df.empty else 0.0
        total_disposal_costs_uf = disposal_df['subtotal_uf'].sum() if not disposal_df.empty else 0.0
        total_costs_uf = total_transport_costs_uf + total_disposal_costs_uf
        total_revenue_uf = client_df['subtotal_uf'].sum() if not client_df.empty else 0.0
        
        cycle_info = {
            'period_key': economic_indicators.get('period_key', f"{year}-{month:02d}"),
            'proforma_code': economic_indicators.get('proforma_code', Proforma.generate_code(year, month)),
            'uf_value': economic_indicators['uf_value'],
            'fuel_price': economic_indicators['fuel_price'],
            'extra_indicators': economic_indicators.get('extra_indicators', {}),
            'start_date': cycle_start.strftime('%Y-%m-%d'),
            'end_date': cycle_end.strftime('%Y-%m-%d'),
            'is_closed': economic_indicators.get('is_closed', False)
        }
        
        return SettlementResult(
            cycle_info=cycle_info,
            contractor_df=contractor_df,
            disposal_df=disposal_df,
            client_df=client_df,
            total_transport_costs_uf=total_transport_costs_uf,
            total_disposal_costs_uf=total_disposal_costs_uf,
            total_costs_uf=total_costs_uf,
            total_revenue_uf=total_revenue_uf
        )
    
    def _calculate_cycle_dates(self, year: int, month: int) -> tuple:
        """
        Calculate cycle start and end dates.
        
        Cycle runs from 19th of previous month to 18th of current month.
        
        Args:
            year: Year of the settlement
            month: Month of the settlement
            
        Returns:
            Tuple of (start_date, end_date) as datetime objects
            
        Example:
            >>> _calculate_cycle_dates(2025, 11)
            (datetime(2025, 10, 19), datetime(2025, 11, 18))
        """
        # End date: 18th of the current month
        cycle_end = datetime(year, month, 18)
        
        # Start date: 19th of the previous month
        previous_month = datetime(year, month, 1) - relativedelta(months=1)
        cycle_start = datetime(previous_month.year, previous_month.month, 19)
        
        return cycle_start, cycle_end
    
    def _get_vehicle_type(self, vehicle_id: int) -> str:
        """
        Obtiene el tipo de vehículo desde la base de datos.
        
        Args:
            vehicle_id: ID del vehículo
            
        Returns:
            Tipo de vehículo ('BATEA', 'AMPLIROLL', 'AMPLIROLL_CARRO') o 'AMPLIROLL' por defecto
        """
        if not vehicle_id:
            return 'AMPLIROLL'  # Default
        
        try:
            with self.load_repo.db_manager as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT type FROM vehicles WHERE id = ?",
                    (vehicle_id,)
                )
                row = cursor.fetchone()
                if row and row['type']:
                    return row['type'].upper()
        except Exception:
            pass
        
        return 'AMPLIROLL'  # Default fallback
    
    def _fetch_loads_in_cycle(
        self, 
        cycle_start: datetime, 
        cycle_end: datetime
    ) -> List[dict]:
        """
        Fetch all completed loads in the cycle period.
        
        Completed loads are those with status 'ARRIVED' or 'COMPLETED'.
        Uses direct SQL query to get all required fields with JOINs.
        
        Args:
            cycle_start: Start date of the cycle
            cycle_end: End date of the cycle
            
        Returns:
            List of load dicts with joined details (client_name, origin_name, etc.)
        """
        # Build SQL query with all necessary fields and JOINs
        # Incluye origin_treatment_plant y destination_treatment_plant correctamente
        # El client_id viene de facilities, no de loads directamente
        query = """
            SELECT 
                l.id,
                l.manifest_code as manifest_number,
                l.vehicle_id,
                f_origin.client_id,
                l.status,
                l.scheduled_date,
                l.net_weight / 1000.0 as net_weight_tons,
                l.origin_facility_id,
                l.origin_treatment_plant_id,
                l.destination_site_id,
                l.destination_treatment_plant_id,
                v.license_plate as vehicle_name,
                c.name as client_name,
                COALESCE(f_origin.name, tp_origin.name, 'N/A') as origin_name,
                COALESCE(s.name, tp_dest.name, 'N/A') as destination_name
            FROM loads l
            LEFT JOIN vehicles v ON l.vehicle_id = v.id
            LEFT JOIN facilities f_origin ON l.origin_facility_id = f_origin.id
            LEFT JOIN clients c ON f_origin.client_id = c.id
            LEFT JOIN treatment_plants tp_origin ON l.origin_treatment_plant_id = tp_origin.id
            LEFT JOIN sites s ON l.destination_site_id = s.id
            LEFT JOIN treatment_plants tp_dest ON l.destination_treatment_plant_id = tp_dest.id
            WHERE l.status IN ('ARRIVED', 'COMPLETED')
              AND l.scheduled_date BETWEEN ? AND ?
            ORDER BY l.scheduled_date ASC
        """
        
        with self.load_repo.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (cycle_start.isoformat(), cycle_end.isoformat())
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def _calculate_contractor_costs(
        self,
        loads_data: List[dict],
        fuel_price_month: float,
        proforma: 'Proforma' = None
    ) -> pd.DataFrame:
        """
        Calculate contractor costs using vectorized pandas operations.
        
        Usa las tarifas definidas en la Proforma del período según el tipo de vehículo.
        
        Algorithm (vectorized):
        1. Load data into DataFrame
        2. Get tariffs from proforma (tariff_batea_uf, tariff_ampliroll_uf, tariff_ampliroll_carro_uf)
        3. Match vehicle_type to get the correct tariff
        4. Calculate billable_weight = max(net_weight, min_weight_guaranteed)
        5. Calculate subtotal_uf = billable_weight * distance_km * tariff_uf
        
        Args:
            loads_data: List of load dicts from database
            fuel_price_month: Current fuel price for the month (CLP) - for reference only
            proforma: Proforma entity with tariffs (optional, for direct access)
            
        Returns:
            DataFrame with columns matching ContractorSettlement
        """
        if not loads_data:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=[
                'load_id', 'manifest_number', 'vehicle_plate', 'date',
                'origin_name', 'destination_name', 'billable_weight',
                'base_rate_uf', 'fuel_factor', 'adjusted_rate_uf',
                'distance_km', 'subtotal_uf'
            ])
        
        # Convert to DataFrame
        df = pd.DataFrame(loads_data)
        
        # Basic validation - solo requerir ID
        if 'id' not in df.columns:
            raise ValueError("Missing required field in load data: id")
        
        # =========================================================================
        # NUEVA LÓGICA: Usar tarifas desde la Proforma
        # =========================================================================
        
        # Pesos mínimos garantizados por tipo de vehículo (hardcoded para MVP)
        MIN_WEIGHT_BATEA = 15.0  # toneladas
        MIN_WEIGHT_AMPLIROLL = 7.0  # toneladas
        MIN_WEIGHT_AMPLIROLL_CARRO = 7.0  # toneladas
        
        # Obtener tipo de vehículo para cada carga
        # Necesitamos hacer un JOIN con vehicles para obtener vehicle_type
        vehicle_types = []
        for _, row in df.iterrows():
            vehicle_id = row.get('vehicle_id')
            vehicle_type = self._get_vehicle_type(vehicle_id)
            vehicle_types.append(vehicle_type)
        
        df['vehicle_type'] = vehicle_types
        
        # Asignar tarifa según tipo de vehículo desde proforma
        def get_tariff_for_type(vtype):
            if proforma:
                tariff = proforma.get_tariff_for_vehicle_type(vtype)
                if tariff:
                    return tariff
            # Fallback: usar tarifas por defecto si no hay proforma
            defaults = {
                'BATEA': 0.001460,
                'AMPLIROLL': 0.002962,
                'AMPLIROLL_SIMPLE': 0.002962,
                'AMPLIROLL_CARRO': 0.001793
            }
            return defaults.get(vtype.upper() if vtype else '', 0.002)
        
        def get_min_weight_for_type(vtype):
            vtype_upper = vtype.upper() if vtype else ''
            if vtype_upper == 'BATEA':
                return MIN_WEIGHT_BATEA
            elif vtype_upper in ('AMPLIROLL', 'AMPLIROLL_SIMPLE'):
                return MIN_WEIGHT_AMPLIROLL
            elif vtype_upper == 'AMPLIROLL_CARRO':
                return MIN_WEIGHT_AMPLIROLL_CARRO
            return MIN_WEIGHT_AMPLIROLL  # Default
        
        # Aplicar tarifas y pesos mínimos
        df['base_rate_uf'] = df['vehicle_type'].apply(get_tariff_for_type)
        df['min_weight'] = df['vehicle_type'].apply(get_min_weight_for_type)
        
        # Las tarifas en proforma ya incluyen el ajuste por combustible
        # El fuel_factor es 1.0 porque la tarifa ya está ajustada
        df['fuel_factor'] = 1.0
        df['adjusted_rate_uf'] = df['base_rate_uf']  # Ya ajustada en proforma
        
        # Calculate billable weight (vectorized)
        # net_weight_tons ya viene convertido de kg a toneladas desde la query
        df['billable_weight'] = df.apply(
            lambda row: max(row['net_weight_tons'] if pd.notna(row['net_weight_tons']) else 0, row['min_weight']),
            axis=1
        )
        
        # Fetch distances for each route
        # TODO: Optimize this with bulk lookups or pre-loaded distance matrix
        distances = []
        for _, row in df.iterrows():
            # Usar origin_facility_id o origin_treatment_plant_id como origen
            origin_id = row.get('origin_facility_id') or row.get('origin_treatment_plant_id')
            dest_id = row.get('destination_site_id') or row.get('destination_treatment_plant_id')
            
            # Determinar tipo de destino según la columna que tiene valor
            if row.get('destination_site_id'):
                dest_type = 'SITE'
            elif row.get('destination_treatment_plant_id'):
                dest_type = 'TREATMENT_PLANT'
            else:
                dest_type = None
            
            distance = 0.0
            if origin_id and dest_id and dest_type:
                distance = self.distance_repo.get_route_distance(
                    origin_id, dest_id, dest_type
                ) or 0.0
            distances.append(distance)
        
        df['distance_km'] = distances
        
        # Calculate subtotal (vectorized)
        df['subtotal_uf'] = df['billable_weight'] * df['distance_km'] * df['adjusted_rate_uf']
        
        # Format output columns
        result_df = pd.DataFrame({
            'load_id': df['id'],
            'manifest_number': df.get('manifest_number', 'N/A'),
            'vehicle_plate': df.get('vehicle_name', 'N/A'),  # Assuming vehicle_name from join
            'vehicle_type': df['vehicle_type'],
            'date': df.get('scheduled_date', ''),
            'origin_name': df.get('origin_name', 'N/A'),
            'destination_name': df.get('destination_name', 'N/A'),
            'billable_weight': df['billable_weight'],
            'base_rate_uf': df['base_rate_uf'],
            'fuel_factor': df['fuel_factor'],
            'adjusted_rate_uf': df['adjusted_rate_uf'],
            'distance_km': df['distance_km'],
            'subtotal_uf': df['subtotal_uf']
        })
        
        return result_df
    
    def _calculate_disposal_costs(self, loads_data: List[dict]) -> pd.DataFrame:
        """
        Calculate disposal site costs using vectorized pandas operations.
        
        These are COSTS paid TO disposal sites for receiving waste.
        Only applies to loads with destination_site_id (not treatment plants).
        
        Algorithm:
        1. Filter loads that have a destination_site_id
        2. Fetch active tariffs for each site
        3. Calculate billable_weight = max(net_weight, min_guaranteed)
        4. Calculate subtotal_uf = billable_weight * rate_uf
        
        Args:
            loads_data: List of load dicts from database
            
        Returns:
            DataFrame with columns matching DisposalCostSettlement
        """
        if not loads_data:
            return pd.DataFrame(columns=[
                'load_id', 'manifest_number', 'site_name', 'date',
                'billable_weight', 'rate_uf', 'subtotal_uf'
            ])
        
        # Check if disposal tariffs repository is configured
        if self.disposal_site_tariffs_repo is None:
            return pd.DataFrame(columns=[
                'load_id', 'manifest_number', 'site_name', 'date',
                'billable_weight', 'rate_uf', 'subtotal_uf'
            ])
        
        # Filter only loads going to disposal sites (not treatment plants)
        site_loads = [l for l in loads_data if l.get('destination_site_id')]
        
        if not site_loads:
            return pd.DataFrame(columns=[
                'load_id', 'manifest_number', 'site_name', 'date',
                'billable_weight', 'rate_uf', 'subtotal_uf'
            ])
        
        # Fetch all active disposal site tariffs
        active_tariffs = self.disposal_site_tariffs_repo.get_all_active()
        tariffs_df = pd.DataFrame(active_tariffs)
        
        if tariffs_df.empty:
            # No disposal tariffs configured
            return pd.DataFrame(columns=[
                'load_id', 'manifest_number', 'site_name', 'date',
                'billable_weight', 'rate_uf', 'subtotal_uf'
            ])
        
        # Build result rows
        rows = []
        for load in site_loads:
            site_id = load.get('destination_site_id')
            
            # Find tariff for this site
            site_tariffs = tariffs_df[tariffs_df['site_id'] == site_id]
            if site_tariffs.empty:
                continue  # No tariff configured for this site
            
            tariff = site_tariffs.iloc[0]
            
            # Calculate billable weight
            # net_weight_tons ya viene convertido de kg a toneladas desde la query
            net_weight = load.get('net_weight_tons', 0.0) or 0.0
            min_weight = tariff.get('min_weight_guaranteed', 0.0) or 0.0
            billable_weight = max(net_weight, min_weight)
            
            # Calculate subtotal
            rate_uf = tariff['rate_uf']
            subtotal_uf = billable_weight * rate_uf
            
            rows.append({
                'load_id': load['id'],
                'manifest_number': load.get('manifest_number', 'N/A'),
                'site_name': tariff.get('site_name', load.get('destination_name', 'N/A')),
                'date': load.get('scheduled_date', ''),
                'billable_weight': billable_weight,
                'rate_uf': rate_uf,
                'subtotal_uf': subtotal_uf
            })
        
        return pd.DataFrame(rows) if rows else pd.DataFrame(columns=[
            'load_id', 'manifest_number', 'site_name', 'date',
            'billable_weight', 'rate_uf', 'subtotal_uf'
        ])
    
    def _calculate_client_revenues(self, loads_data: List[dict]) -> pd.DataFrame:
        """
        Calculate client revenues using vectorized pandas operations.
        
        Algorithm (vectorized):
        1. Load data into DataFrame
        2. Fetch active client tariffs by concept
        3. For each load, apply tariffs for all applicable concepts
        4. Calculate subtotal_uf = weight * rate_uf
        
        Args:
            loads_data: List of load dicts from database
            
        Returns:
            DataFrame with columns matching ClientSettlement
        """
        if not loads_data:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=[
                'load_id', 'manifest_number', 'client_name', 'date',
                'weight', 'concept', 'rate_uf', 'subtotal_uf'
            ])
        
        # Convert to DataFrame
        df = pd.DataFrame(loads_data)
        
        # Fetch all active client tariffs
        active_tariffs = self.client_tariffs_repo.get_all_active()
        tariffs_df = pd.DataFrame(active_tariffs)
        
        if tariffs_df.empty:
            # No tariffs configured
            return pd.DataFrame(columns=[
                'load_id', 'manifest_number', 'client_name', 'date',
                'weight', 'concept', 'rate_uf', 'subtotal_uf'
            ])
        
        # Expand each load by applicable concepts
        # Each load can have multiple billing concepts (TRANSPORTE, DISPOSICION, TRATAMIENTO)
        rows = []
        for _, load in df.iterrows():
            client_id = load.get('client_id')
            if not client_id:
                continue
            
            # Get tariffs for this client
            client_tariffs = tariffs_df[tariffs_df['client_id'] == client_id]
            
            for _, tariff in client_tariffs.iterrows():
                # net_weight_tons ya viene convertido de kg a toneladas desde la query
                weight = max(
                    load.get('net_weight_tons', 0.0),
                    tariff['min_weight_guaranteed']
                )
                
                subtotal_uf = weight * tariff['rate_uf']
                
                rows.append({
                    'load_id': load['id'],
                    'manifest_number': load.get('manifest_number', 'N/A'),
                    'client_name': load.get('client_name', 'N/A'),
                    'date': load.get('scheduled_date', ''),
                    'weight': weight,
                    'concept': tariff['concept'],
                    'rate_uf': tariff['rate_uf'],
                    'subtotal_uf': subtotal_uf
                })
        
        return pd.DataFrame(rows)
    
    def _format_month_name(self, month: int) -> str:
        """
        Convert month number to Spanish month name.
        
        Args:
            month: Month number (1-12)
            
        Returns:
            Spanish month name
        """
        month_names = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        return month_names.get(month, str(month))
