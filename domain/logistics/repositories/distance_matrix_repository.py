from typing import List, Optional, Tuple
from database.db_manager import DatabaseManager
from database.repository import BaseRepository
import sqlite3


class DistanceMatrixRepository:
    """
    Repository for querying and managing the distance_matrix table.
    
    Handles route lookups for trip linking and logistics optimization,
    as well as CRUD operations for distance matrix management.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.table_name = "distance_matrix"
    
    # ==========================================================================
    # READ OPERATIONS
    # ==========================================================================
    
    def get_linkable_routes(self, origin_facility_id: int) -> List[dict]:
        """
        Returns routes available for trip linking from a specific origin.
        
        A linkable route is one marked with is_link_segment=True, indicating it's
        suitable for multi-hop trips (e.g., Plant A -> Plant B -> Site).
        
        Args:
            origin_facility_id: ID of the origin facility (treatment plant)
            
        Returns:
            List of dicts with keys: destination_id, destination_type, distance_km, is_link_segment
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT destination_id, destination_type, distance_km, is_link_segment
                    FROM {self.table_name}
                    WHERE origin_facility_id = ? AND is_link_segment = 1
                    ORDER BY distance_km ASC""",
                (origin_facility_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_route_distance(
        self,
        origin_facility_id: int,
        destination_id: int,
        destination_type: str
    ) -> Optional[float]:
        """
        Gets the distance in km for a specific route.
        
        Args:
            origin_facility_id: Origin facility ID
            destination_id: Destination node ID (facility or site)
            destination_type: 'FACILITY' or 'SITE'
            
        Returns:
            Distance in km, or None if route not found
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT distance_km FROM {self.table_name}
                    WHERE origin_facility_id = ? 
                    AND destination_id = ?
                    AND destination_type = ?
                    LIMIT 1""",
                (origin_facility_id, destination_id, destination_type)
            )
            row = cursor.fetchone()
            return row['distance_km'] if row else None
    
    def get_all_routes(self, origin_facility_id: Optional[int] = None) -> List[dict]:
        """
        Returns all routes, optionally filtered by origin.
        
        Args:
            origin_facility_id: Optional filter by origin
            
        Returns:
            List of route dictionaries
        """
        query = f"SELECT * FROM {self.table_name}"
        params = []
        
        if origin_facility_id is not None:
            query += " WHERE origin_facility_id = ?"
            params.append(origin_facility_id)
        
        query += " ORDER BY origin_facility_id, distance_km"
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_all_routes_with_names(self, client_id: Optional[int] = None) -> List[dict]:
        """
        Returns all routes with resolved origin and destination names.
        Optionally filters by client (only shows routes from facilities belonging to that client).
        
        Args:
            client_id: Optional client ID to filter origins by
            
        Returns:
            List of route dictionaries with resolved names
        """
        query = """
            SELECT 
                dm.id,
                dm.origin_facility_id,
                f.name AS origin_name,
                f.client_id AS origin_client_id,
                c.name AS client_name,
                dm.destination_id,
                dm.destination_type,
                CASE 
                    WHEN dm.destination_type = 'FACILITY' THEN (SELECT name FROM facilities WHERE id = dm.destination_id)
                    WHEN dm.destination_type = 'TREATMENT_PLANT' THEN (SELECT name FROM treatment_plants WHERE id = dm.destination_id)
                    WHEN dm.destination_type = 'SITE' THEN (SELECT name FROM sites WHERE id = dm.destination_id)
                    ELSE 'Desconocido'
                END AS destination_name,
                dm.distance_km,
                dm.is_link_segment,
                dm.created_at,
                dm.updated_at
            FROM distance_matrix dm
            JOIN facilities f ON dm.origin_facility_id = f.id
            LEFT JOIN clients c ON f.client_id = c.id
        """
        params = []
        
        if client_id is not None:
            query += " WHERE f.client_id = ?"
            params.append(client_id)
        
        query += " ORDER BY c.name, f.name, dm.distance_km"
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_by_id(self, route_id: int) -> Optional[dict]:
        """
        Get a specific route by ID.
        
        Args:
            route_id: The route ID
            
        Returns:
            Route dictionary or None if not found
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ?",
                (route_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def check_duplicate(
        self,
        origin_facility_id: int,
        destination_id: int,
        destination_type: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Checks if a route already exists (for duplicate validation).
        
        Args:
            origin_facility_id: Origin facility ID
            destination_id: Destination ID
            destination_type: 'FACILITY', 'TREATMENT_PLANT', or 'SITE'
            exclude_id: Optional route ID to exclude (for updates)
            
        Returns:
            True if duplicate exists, False otherwise
        """
        query = f"""
            SELECT COUNT(*) as count FROM {self.table_name}
            WHERE origin_facility_id = ? 
            AND destination_id = ?
            AND destination_type = ?
        """
        params = [origin_facility_id, destination_id, destination_type]
        
        if exclude_id is not None:
            query += " AND id != ?"
            params.append(exclude_id)
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
            return row['count'] > 0
    
    # ==========================================================================
    # WRITE OPERATIONS
    # ==========================================================================
    
    def add(
        self,
        origin_facility_id: int,
        destination_id: int,
        destination_type: str,
        distance_km: float,
        is_link_segment: bool = False
    ) -> int:
        """
        Adds a new route to the distance matrix.
        
        Args:
            origin_facility_id: Origin facility ID
            destination_id: Destination ID (facility, treatment_plant, or site)
            destination_type: 'FACILITY', 'TREATMENT_PLANT', or 'SITE'
            distance_km: Distance in kilometers (decimal)
            is_link_segment: True if this is an intermediate link segment
            
        Returns:
            The new route ID
            
        Raises:
            ValueError: If duplicate route exists or validation fails
            sqlite3.Error: If database operation fails
        """
        # Validate destination_type
        valid_types = ('FACILITY', 'TREATMENT_PLANT', 'SITE')
        if destination_type not in valid_types:
            raise ValueError(f"destination_type must be one of {valid_types}")
        
        # Check for duplicates
        if self.check_duplicate(origin_facility_id, destination_id, destination_type):
            raise ValueError(
                f"Ya existe una ruta desde la planta {origin_facility_id} "
                f"hacia el destino {destination_id} ({destination_type})"
            )
        
        query = f"""
            INSERT INTO {self.table_name} 
            (origin_facility_id, destination_id, destination_type, distance_km, is_link_segment)
            VALUES (?, ?, ?, ?, ?)
        """
        
        try:
            with self.db_manager as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (origin_facility_id, destination_id, destination_type, distance_km, int(is_link_segment))
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Error de integridad: {str(e)}")
    
    def update(
        self,
        route_id: int,
        distance_km: Optional[float] = None,
        is_link_segment: Optional[bool] = None
    ) -> bool:
        """
        Updates an existing route's distance or link segment flag.
        
        Args:
            route_id: The route ID to update
            distance_km: New distance in kilometers (optional)
            is_link_segment: New link segment flag (optional)
            
        Returns:
            True if updated successfully, False if route not found
        """
        updates = []
        params = []
        
        if distance_km is not None:
            updates.append("distance_km = ?")
            params.append(distance_km)
        
        if is_link_segment is not None:
            updates.append("is_link_segment = ?")
            params.append(int(is_link_segment))
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(route_id)
        
        query = f"UPDATE {self.table_name} SET {', '.join(updates)} WHERE id = ?"
        
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            return cursor.rowcount > 0
    
    def delete(self, route_id: int) -> bool:
        """
        Deletes a route from the distance matrix.
        
        Args:
            route_id: The route ID to delete
            
        Returns:
            True if deleted successfully, False if route not found
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE id = ?",
                (route_id,)
            )
            return cursor.rowcount > 0
    
    def upsert(
        self,
        origin_facility_id: int,
        destination_id: int,
        destination_type: str,
        distance_km: float,
        is_link_segment: bool = False
    ) -> Tuple[int, bool]:
        """
        Insert or update a route (upsert operation).
        
        Args:
            origin_facility_id: Origin facility ID
            destination_id: Destination ID
            destination_type: 'FACILITY', 'TREATMENT_PLANT', or 'SITE'
            distance_km: Distance in kilometers
            is_link_segment: True if this is an intermediate link segment
            
        Returns:
            Tuple of (route_id, was_update) where was_update is True if existing route was updated
        """
        # Check if route exists
        existing = self.get_route_by_endpoints(origin_facility_id, destination_id, destination_type)
        
        if existing:
            # Update existing route
            self.update(existing['id'], distance_km=distance_km, is_link_segment=is_link_segment)
            return (existing['id'], True)
        else:
            # Insert new route
            new_id = self.add(origin_facility_id, destination_id, destination_type, distance_km, is_link_segment)
            return (new_id, False)
    
    def get_route_by_endpoints(
        self,
        origin_facility_id: int,
        destination_id: int,
        destination_type: str
    ) -> Optional[dict]:
        """
        Get a route by its origin and destination endpoints.
        
        Args:
            origin_facility_id: Origin facility ID
            destination_id: Destination ID
            destination_type: 'FACILITY', 'TREATMENT_PLANT', or 'SITE'
            
        Returns:
            Route dictionary or None if not found
        """
        with self.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""SELECT * FROM {self.table_name}
                    WHERE origin_facility_id = ? 
                    AND destination_id = ?
                    AND destination_type = ?
                    LIMIT 1""",
                (origin_facility_id, destination_id, destination_type)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
