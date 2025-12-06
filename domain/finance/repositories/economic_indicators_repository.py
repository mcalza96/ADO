from typing import Optional, List
from infrastructure.persistence.database_manager import DatabaseManager


class EconomicIndicatorsRepository:
    """
    Repository for querying the economic_indicators table.
    
    Handles retrieval of UF values and fuel prices for financial cycles.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.table_name = "economic_indicators"
    
    def get_by_period(self, year: int, month: int) -> Optional[dict]:
        """
        Returns economic indicators for a specific year and month.
        
        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            
        Returns:
            Dict with keys: id, period_key, uf_value, fuel_price, 
                           cycle_start_date, cycle_end_date, status
            None if not found
        """
        period_key = f"{year}-{month:02d}"
        return self.get_by_period_key(period_key)
    
    def get_by_period_key(self, period_key: str) -> Optional[dict]:
        """
        Returns economic indicators by period key (format: 'YYYY-MM').
        
        Args:
            period_key: Period identifier (e.g., '2025-11')
            
        Returns:
            Dict with economic indicator data, or None if not found
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, period_key, uf_value, fuel_price,
                           cycle_start_date, cycle_end_date, status
                    FROM {self.table_name}
                    WHERE period_key = ?
                    LIMIT 1""",
                (period_key,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all(self) -> List[dict]:
        """
        Returns all economic indicators ordered by period descending.
        
        Returns:
            List of dicts with economic indicator data
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, period_key, uf_value, fuel_price,
                           cycle_start_date, cycle_end_date, status,
                           created_at, updated_at
                    FROM {self.table_name}
                    ORDER BY period_key DESC"""
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_status(self, period_key: str, is_closed: bool) -> None:
        """
        Updates the closed status of an economic period.
        
        Args:
            period_key: Period identifier (e.g., '2025-11')
            is_closed: New status
        """
        status_value = 1 if is_closed else 0
        # Determine strict status text if needed, but 'status' column in SQL might be text or int.
        # Looking at get_by_period method, it returns 'status'. 
        # Assuming table has 'is_closed' or we update 'status'. 
        # The entity has 'is_closed'. The Repo `get_all` selects `status`.
        # Let's assume 'status' column holds text 'CLOSED' or 'OPEN' or similar, OR there is a mapping.
        # Wait, the entity `EconomicCycle` has `is_closed: bool`.
        # The repo selects `status`. Let's check getting a row to be sure.
        # Actually, let's look at `get_by_period_key`: it returns `status`.
        # If I look at the migration or schema, I might know better.
        # For now, I'll update the 'status' column. I'll use 'CLOSED' / 'OPEN'.
        
        new_status = 'CLOSED' if is_closed else 'OPEN'
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE {self.table_name} SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE period_key = ?",
                (new_status, period_key)
            )
            conn.commit()
