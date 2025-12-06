"""
Repository for disposal site tariffs.

Handles retrieval of disposal site cost tariffs (what sites charge per ton).
"""

from typing import Optional, List
from infrastructure.persistence.database_manager import DatabaseManager


class DisposalSiteTariffsRepository:
    """
    Repository for querying the disposal_site_tariffs table.
    
    These are COSTS - money the company pays to disposal sites.
    Different from client_tariffs which are REVENUES.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.table_name = "disposal_site_tariffs"
    
    def get_active_tariff(self, site_id: int) -> Optional[dict]:
        """
        Returns the currently active tariff for a disposal site.
        
        Active tariff is defined as valid_to IS NULL or valid_to >= today.
        
        Args:
            site_id: ID of the disposal site
            
        Returns:
            Dict with keys: id, site_id, rate_uf, min_weight_guaranteed, valid_from, valid_to
            None if not found
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, site_id, rate_uf, min_weight_guaranteed,
                           valid_from, valid_to, created_at, updated_at
                    FROM {self.table_name}
                    WHERE site_id = ? 
                      AND (valid_to IS NULL OR valid_to >= DATE('now'))
                      AND valid_from <= DATE('now')
                    ORDER BY valid_from DESC
                    LIMIT 1""",
                (site_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_active(self) -> List[dict]:
        """
        Returns all currently active disposal site tariffs.
        
        Useful for bulk operations and reporting.
        
        Returns:
            List of dicts with tariff data including site_name from JOIN
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT dst.id, dst.site_id, s.name as site_name,
                           dst.rate_uf, dst.min_weight_guaranteed,
                           dst.valid_from, dst.valid_to,
                           dst.created_at, dst.updated_at
                    FROM {self.table_name} dst
                    JOIN sites s ON dst.site_id = s.id
                    WHERE (dst.valid_to IS NULL OR dst.valid_to >= DATE('now'))
                      AND dst.valid_from <= DATE('now')
                    ORDER BY s.name"""
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_by_site(self, site_id: int) -> List[dict]:
        """
        Returns all tariffs (active and historical) for a specific site.
        
        Args:
            site_id: ID of the disposal site
            
        Returns:
            List of tariff dicts ordered by valid_from DESC
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT id, site_id, rate_uf, min_weight_guaranteed,
                           valid_from, valid_to
                    FROM {self.table_name}
                    WHERE site_id = ?
                    ORDER BY valid_from DESC""",
                (site_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def create(self, site_id: int, rate_uf: float, 
               min_weight_guaranteed: float = 0.0,
               valid_from: str = None) -> int:
        """
        Create a new disposal site tariff.
        
        Args:
            site_id: ID of the disposal site
            rate_uf: Tariff in UF per ton
            min_weight_guaranteed: Minimum billable weight (default 0)
            valid_from: Start date (default today)
            
        Returns:
            ID of the created tariff
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""INSERT INTO {self.table_name} 
                    (site_id, rate_uf, min_weight_guaranteed, valid_from)
                    VALUES (?, ?, ?, COALESCE(?, DATE('now')))""",
                (site_id, rate_uf, min_weight_guaranteed, valid_from)
            )
            conn.commit()
            return cursor.lastrowid
    
    def close_tariff(self, tariff_id: int, valid_to: str = None) -> bool:
        """
        Close a tariff by setting its valid_to date.
        
        Args:
            tariff_id: ID of the tariff to close
            valid_to: End date (default today)
            
        Returns:
            True if updated successfully
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""UPDATE {self.table_name}
                    SET valid_to = COALESCE(?, DATE('now')),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                (valid_to, tariff_id)
            )
            conn.commit()
            return cursor.rowcount > 0
