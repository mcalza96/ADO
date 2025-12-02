import json
from datetime import datetime
from services.common.event_bus import Event
from database.db_manager import DatabaseManager
from domain.compliance.repositories.regulatory_document_repository import RegulatoryDocumentRepository
from domain.compliance.entities.regulatory_document import RegulatoryDocument
from domain.logistics.repositories.load_repository import LoadRepository

class ComplianceListener:
    """
    Escucha eventos de finalización de carga y genera documentos regulatorios inmutables.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.doc_repo = RegulatoryDocumentRepository(db_manager)
        self.load_repo = LoadRepository(db_manager)
    
    def handle_load_completed(self, event: Event) -> None:
        """
        Genera certificado de disposición al completar la carga.
        """
        if event.data.get('to_status') != 'COMPLETED':
            return
            
        load_id = event.data.get('load_id')
        if not load_id:
            return
            
        # 1. Obtener datos completos de la carga (Snapshot)
        load = self.load_repo.get_by_id(load_id)
        if not load:
            print(f"⚠️ Compliance: Load {load_id} not found for snapshot.")
            return
            
        # Verificar si ya existe para evitar duplicados
        existing = self.doc_repo.get_by_load_id(load_id)
        if existing:
            return

        # Crear Snapshot (serialización simple de lo vital)
        # En producción usaríamos un serializer más robusto (Pydantic .dict() o similar)
        snapshot = {
            'load_id': load.id,
            'manifest': load.manifest_code,
            'origin_id': load.origin_facility_id,
            'destination_id': load.destination_site_id,
            'weight_net': load.net_weight,
            'dates': {
                'dispatch': load.dispatch_time.isoformat() if load.dispatch_time else None,
                'arrival': load.arrival_time.isoformat() if load.arrival_time else None
            },
            'attributes': load.attributes
        }
        
        # 2. Crear Documento
        doc = RegulatoryDocument(
            id=None,
            doc_type='CERTIFICADO_DISPOSICION',
            related_load_id=load_id,
            snapshot_data=snapshot,
            generated_at=datetime.now(),
            pdf_url=f"/docs/cert_{load_id}.pdf" # Mock URL
        )
        
        self.doc_repo.add(doc)
        print(f"📜 Certificado generado para Carga {load_id}")
