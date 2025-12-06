"""
Repository para la gestión de Proformas (Estados de Pago).

Este repositorio maneja todas las operaciones de base de datos relacionadas
con las proformas, incluyendo CRUD, consultas por período, y auto-generación
de nuevas proformas.
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import json

from database.db_manager import DatabaseManager
from domain.finance.entities.finance_entities import Proforma


class ProformaRepository:
    """
    Repository for querying and managing the proformas table.
    
    Handles:
    - CRUD operations for proformas
    - Period-based queries
    - Auto-generation of new proformas when closing one
    - Migration from economic_indicators format
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.table_name = "proformas"
    
    # ==========================================
    # READ OPERATIONS
    # ==========================================
    
    def get_by_id(self, proforma_id: int) -> Optional[Proforma]:
        """
        Returns a proforma by its ID.
        
        Args:
            proforma_id: ID of the proforma
            
        Returns:
            Proforma entity or None if not found
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, proforma_code, period_year, period_month,
                           cycle_start_date, cycle_end_date,
                           uf_value, fuel_price,
                           tariff_batea_uf, tariff_ampliroll_uf, tariff_ampliroll_carro_uf,
                           is_closed, extra_indicators,
                           created_at, updated_at
                    FROM {self.table_name}
                    WHERE id = ?""",
                (proforma_id,)
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def get_by_code(self, proforma_code: str) -> Optional[Proforma]:
        """
        Returns a proforma by its code (e.g., "PROF 25-03").
        
        Args:
            proforma_code: Proforma code
            
        Returns:
            Proforma entity or None if not found
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, proforma_code, period_year, period_month,
                           cycle_start_date, cycle_end_date,
                           uf_value, fuel_price,
                           tariff_batea_uf, tariff_ampliroll_uf, tariff_ampliroll_carro_uf,
                           is_closed, extra_indicators,
                           created_at, updated_at
                    FROM {self.table_name}
                    WHERE proforma_code = ?""",
                (proforma_code,)
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def get_by_period(self, year: int, month: int) -> Optional[Proforma]:
        """
        Returns the proforma for a specific year and month.
        
        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            
        Returns:
            Proforma entity or None if not found
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, proforma_code, period_year, period_month,
                           cycle_start_date, cycle_end_date,
                           uf_value, fuel_price,
                           tariff_batea_uf, tariff_ampliroll_uf, tariff_ampliroll_carro_uf,
                           is_closed, extra_indicators,
                           created_at, updated_at
                    FROM {self.table_name}
                    WHERE period_year = ? AND period_month = ?""",
                (year, month)
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def get_by_period_key(self, period_key: str) -> Optional[dict]:
        """
        Returns proforma data by period key (format: 'YYYY-MM').
        Compatibility method for existing code using economic_indicators format.
        
        Args:
            period_key: Period identifier (e.g., '2025-11')
            
        Returns:
            Dict with economic indicator data format, or None if not found
        """
        try:
            year, month = map(int, period_key.split('-'))
            proforma = self.get_by_period(year, month)
            if proforma:
                return {
                    'id': proforma.id,
                    'period_key': proforma.get_period_key(),
                    'uf_value': proforma.uf_value,
                    'fuel_price': proforma.fuel_price,
                    'cycle_start_date': proforma.cycle_start_date.isoformat() if proforma.cycle_start_date else None,
                    'cycle_end_date': proforma.cycle_end_date.isoformat() if proforma.cycle_end_date else None,
                    'status': 'CLOSED' if proforma.is_closed else 'OPEN'
                }
        except (ValueError, AttributeError):
            pass
        return None
    
    def get_current_open(self) -> Optional[Proforma]:
        """
        Returns the current open (not closed) proforma.
        
        Returns:
            The most recent open Proforma, or None if all are closed
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, proforma_code, period_year, period_month,
                           cycle_start_date, cycle_end_date,
                           uf_value, fuel_price,
                           tariff_batea_uf, tariff_ampliroll_uf, tariff_ampliroll_carro_uf,
                           is_closed, extra_indicators,
                           created_at, updated_at
                    FROM {self.table_name}
                    WHERE is_closed = 0
                    ORDER BY period_year DESC, period_month DESC
                    LIMIT 1"""
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def get_for_date(self, target_date: date) -> Optional[Proforma]:
        """
        Returns the proforma that contains a specific date in its cycle.
        
        Args:
            target_date: Date to find the containing proforma for
            
        Returns:
            Proforma that contains the date in its cycle, or None
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, proforma_code, period_year, period_month,
                           cycle_start_date, cycle_end_date,
                           uf_value, fuel_price,
                           tariff_batea_uf, tariff_ampliroll_uf, tariff_ampliroll_carro_uf,
                           is_closed, extra_indicators,
                           created_at, updated_at
                    FROM {self.table_name}
                    WHERE cycle_start_date <= ? AND cycle_end_date >= ?
                    LIMIT 1""",
                (target_date.isoformat(), target_date.isoformat())
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def get_previous(self, year: int, month: int) -> Optional[Proforma]:
        """
        Returns the proforma for the previous period.
        
        Args:
            year: Year of the current period
            month: Month of the current period
            
        Returns:
            Proforma of the previous period or None if not found
        """
        # Calculate previous period
        if month == 1:
            prev_year = year - 1
            prev_month = 12
        else:
            prev_year = year
            prev_month = month - 1
        
        return self.get_by_period(prev_year, prev_month)
    
    def get_first_proforma(self) -> Optional[Proforma]:
        """
        Returns the first proforma (earliest period).
        Used to determine which proforma is the base for tariff editing.
        
        Returns:
            First proforma by period or None if no proformas exist
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, proforma_code, period_year, period_month,
                           cycle_start_date, cycle_end_date,
                           uf_value, fuel_price,
                           tariff_batea_uf, tariff_ampliroll_uf, tariff_ampliroll_carro_uf,
                           is_closed, extra_indicators,
                           created_at, updated_at
                    FROM {self.table_name}
                    ORDER BY period_year ASC, period_month ASC
                    LIMIT 1"""
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def get_all(self, include_closed: bool = True) -> List[Proforma]:
        """
        Returns all proformas ordered by period descending.
        
        Args:
            include_closed: If False, only returns open proformas
            
        Returns:
            List of Proforma entities
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            sql = f"""SELECT id, proforma_code, period_year, period_month,
                             cycle_start_date, cycle_end_date,
                             uf_value, fuel_price,
                             tariff_batea_uf, tariff_ampliroll_uf, tariff_ampliroll_carro_uf,
                             is_closed, extra_indicators,
                             created_at, updated_at
                      FROM {self.table_name}"""
            
            if not include_closed:
                sql += " WHERE is_closed = 0"
            
            # Ordenar: primero 25-11, luego 25-12, etc. (ASC por año y mes)
            sql += " ORDER BY period_year ASC, period_month ASC"
            
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [self._row_to_entity(row) for row in rows]
    
    def get_all_as_dict(self) -> List[dict]:
        """
        Returns all proformas as dictionaries (for UI compatibility).
        
        Returns:
            List of dicts with proforma data
        """
        proformas = self.get_all()
        return [self._entity_to_dict(p) for p in proformas]
    
    # ==========================================
    # WRITE OPERATIONS
    # ==========================================
    
    def create(self, proforma: Proforma) -> int:
        """
        Creates a new proforma in the database.
        
        Args:
            proforma: Proforma entity to create
            
        Returns:
            ID of the created proforma
            
        Raises:
            ValueError: If proforma for this period already exists
        """
        # Verify period doesn't already exist
        existing = self.get_by_period(proforma.period_year, proforma.period_month)
        if existing:
            raise ValueError(
                f"Ya existe una proforma para el período {proforma.period_year}-{proforma.period_month:02d}"
            )
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""INSERT INTO {self.table_name} 
                    (proforma_code, period_year, period_month,
                     cycle_start_date, cycle_end_date,
                     uf_value, fuel_price,
                     tariff_batea_uf, tariff_ampliroll_uf, tariff_ampliroll_carro_uf,
                     is_closed, extra_indicators)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    proforma.proforma_code,
                    proforma.period_year,
                    proforma.period_month,
                    proforma.cycle_start_date.isoformat(),
                    proforma.cycle_end_date.isoformat(),
                    proforma.uf_value,
                    proforma.fuel_price,
                    proforma.tariff_batea_uf,
                    proforma.tariff_ampliroll_uf,
                    proforma.tariff_ampliroll_carro_uf,
                    1 if proforma.is_closed else 0,
                    json.dumps(proforma.extra_indicators or {})
                )
            )
            conn.commit()
            return cursor.lastrowid
    
    def update(self, proforma: Proforma) -> bool:
        """
        Updates an existing proforma.
        
        Args:
            proforma: Proforma entity with updated values
            
        Returns:
            True if updated successfully
            
        Raises:
            ValueError: If proforma is closed and modifications are attempted
        """
        existing = self.get_by_id(proforma.id)
        if not existing:
            raise ValueError(f"No existe proforma con ID {proforma.id}")
        
        if existing.is_closed:
            raise ValueError(
                f"La proforma {existing.proforma_code} está cerrada y no puede ser modificada"
            )
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""UPDATE {self.table_name}
                    SET uf_value = ?,
                        fuel_price = ?,
                        tariff_batea_uf = ?,
                        tariff_ampliroll_uf = ?,
                        tariff_ampliroll_carro_uf = ?,
                        extra_indicators = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                (
                    proforma.uf_value,
                    proforma.fuel_price,
                    proforma.tariff_batea_uf,
                    proforma.tariff_ampliroll_uf,
                    proforma.tariff_ampliroll_carro_uf,
                    json.dumps(proforma.extra_indicators or {}),
                    proforma.id
                )
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def save(self, year: int, month: int, uf_value: float, fuel_price: float,
             extra_indicators: Dict[str, Any] = None) -> int:
        """
        Creates or updates a proforma for the specified period.
        
        If the proforma already exists and is open, updates it.
        If it doesn't exist, creates it with auto-generated code and dates.
        
        Args:
            year: Year of the period
            month: Month of the period
            uf_value: UF value for this period
            fuel_price: Fuel price for this period
            extra_indicators: Optional additional indicators
            
        Returns:
            ID of the created/updated proforma
            
        Raises:
            ValueError: If trying to modify a closed proforma
        """
        existing = self.get_by_period(year, month)
        
        if existing:
            if existing.is_closed:
                raise ValueError(
                    f"La proforma {existing.proforma_code} está cerrada y no puede ser modificada"
                )
            existing.uf_value = uf_value
            existing.fuel_price = fuel_price
            existing.extra_indicators = extra_indicators or existing.extra_indicators
            self.update(existing)
            return existing.id
        else:
            # Create new proforma with auto-generated values
            cycle_start, cycle_end = Proforma.calculate_cycle_dates(year, month)
            proforma = Proforma(
                id=None,
                proforma_code=Proforma.generate_code(year, month),
                period_year=year,
                period_month=month,
                cycle_start_date=cycle_start,
                cycle_end_date=cycle_end,
                uf_value=uf_value,
                fuel_price=fuel_price,
                is_closed=False,
                extra_indicators=extra_indicators or {}
            )
            return self.create(proforma)
    
    def close_proforma(self, proforma_id: int, auto_create_next: bool = True) -> Optional[int]:
        """
        Closes a proforma and optionally creates the next one.
        
        Args:
            proforma_id: ID of the proforma to close
            auto_create_next: If True, creates the next proforma automatically
            
        Returns:
            ID of the newly created proforma if auto_create_next=True, else None
            
        Raises:
            ValueError: If proforma doesn't exist or is already closed
        """
        proforma = self.get_by_id(proforma_id)
        if not proforma:
            raise ValueError(f"No existe proforma con ID {proforma_id}")
        
        if proforma.is_closed:
            raise ValueError(f"La proforma {proforma.proforma_code} ya está cerrada")
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""UPDATE {self.table_name}
                    SET is_closed = 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                (proforma_id,)
            )
            conn.commit()
        
        # Auto-create next proforma
        if auto_create_next:
            next_month = proforma.period_month + 1
            next_year = proforma.period_year
            if next_month > 12:
                next_month = 1
                next_year += 1
            
            # Check if next proforma already exists
            existing_next = self.get_by_period(next_year, next_month)
            if not existing_next:
                return self._create_next_proforma(proforma)
        
        return None
    
    def _create_next_proforma(self, previous: Proforma) -> int:
        """
        Creates the next proforma based on the previous one.
        
        Copies indicator values from the previous proforma as starting point.
        Calcula las tarifas usando: tarifa_nueva = tarifa_anterior × (fuel_nuevo / fuel_anterior)
        
        Args:
            previous: The previous proforma
            
        Returns:
            ID of the new proforma
        """
        # Calculate next period
        next_date = date(previous.period_year, previous.period_month, 1) + relativedelta(months=1)
        next_year = next_date.year
        next_month = next_date.month
        
        # Calculate cycle dates
        cycle_start, cycle_end = Proforma.calculate_cycle_dates(next_year, next_month)
        
        # Create new proforma with previous values as default
        new_proforma = Proforma(
            id=None,
            proforma_code=Proforma.generate_code(next_year, next_month),
            period_year=next_year,
            period_month=next_month,
            cycle_start_date=cycle_start,
            cycle_end_date=cycle_end,
            uf_value=previous.uf_value,  # Copy previous value as starting point
            fuel_price=previous.fuel_price,  # Copy previous value
            tariff_batea_uf=previous.tariff_batea_uf,  # Copy tariffs (will be recalculated)
            tariff_ampliroll_uf=previous.tariff_ampliroll_uf,
            tariff_ampliroll_carro_uf=previous.tariff_ampliroll_carro_uf,
            is_closed=False,
            extra_indicators=previous.extra_indicators.copy() if previous.extra_indicators else {}
        )
        
        # Las tarifas se calcularán cuando el usuario actualice el fuel_price
        # usando new_proforma.calculate_tariffs_from_previous(previous)
        
        return self.create(new_proforma)
    
    def delete(self, proforma_id: int) -> bool:
        """
        Deletes a proforma (only if open and no associated data).
        
        Args:
            proforma_id: ID of the proforma to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            ValueError: If proforma is closed or has associated data
        """
        proforma = self.get_by_id(proforma_id)
        if not proforma:
            raise ValueError(f"No existe proforma con ID {proforma_id}")
        
        if proforma.is_closed:
            raise ValueError(
                f"La proforma {proforma.proforma_code} está cerrada y no puede ser eliminada"
            )
        
        # TODO: Check for associated loads/transactions before allowing delete
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE id = ?",
                (proforma_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def _row_to_entity(self, row) -> Optional[Proforma]:
        """Converts a database row to a Proforma entity."""
        if not row:
            return None
        
        row_dict = dict(row)
        
        # Parse dates
        cycle_start = row_dict.get('cycle_start_date')
        cycle_end = row_dict.get('cycle_end_date')
        created_at = row_dict.get('created_at')
        updated_at = row_dict.get('updated_at')
        
        if isinstance(cycle_start, str):
            cycle_start = date.fromisoformat(cycle_start)
        if isinstance(cycle_end, str):
            cycle_end = date.fromisoformat(cycle_end)
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        # Parse extra_indicators JSON
        extra_indicators = row_dict.get('extra_indicators', '{}')
        if isinstance(extra_indicators, str):
            try:
                extra_indicators = json.loads(extra_indicators)
            except (json.JSONDecodeError, TypeError):
                extra_indicators = {}
        
        return Proforma(
            id=row_dict.get('id'),
            proforma_code=row_dict.get('proforma_code'),
            period_year=row_dict.get('period_year'),
            period_month=row_dict.get('period_month'),
            cycle_start_date=cycle_start,
            cycle_end_date=cycle_end,
            uf_value=row_dict.get('uf_value'),
            fuel_price=row_dict.get('fuel_price'),
            tariff_batea_uf=row_dict.get('tariff_batea_uf'),
            tariff_ampliroll_uf=row_dict.get('tariff_ampliroll_uf'),
            tariff_ampliroll_carro_uf=row_dict.get('tariff_ampliroll_carro_uf'),
            is_closed=bool(row_dict.get('is_closed')),
            extra_indicators=extra_indicators,
            created_at=created_at,
            updated_at=updated_at
        )
    
    def _entity_to_dict(self, proforma: Proforma) -> dict:
        """Converts a Proforma entity to a dictionary."""
        return {
            'id': proforma.id,
            'proforma_code': proforma.proforma_code,
            'period_key': proforma.get_period_key(),
            'period_year': proforma.period_year,
            'period_month': proforma.period_month,
            'cycle_start_date': proforma.cycle_start_date.isoformat() if proforma.cycle_start_date else None,
            'cycle_end_date': proforma.cycle_end_date.isoformat() if proforma.cycle_end_date else None,
            'uf_value': proforma.uf_value,
            'fuel_price': proforma.fuel_price,
            'tariff_batea_uf': proforma.tariff_batea_uf,
            'tariff_ampliroll_uf': proforma.tariff_ampliroll_uf,
            'tariff_ampliroll_carro_uf': proforma.tariff_ampliroll_carro_uf,
            'is_closed': proforma.is_closed,
            'extra_indicators': proforma.extra_indicators,
            'created_at': proforma.created_at.isoformat() if proforma.created_at else None,
            'updated_at': proforma.updated_at.isoformat() if proforma.updated_at else None
        }
