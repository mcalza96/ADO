from datetime import date
from database.db_manager import DatabaseManager
from repositories.application_repository import ApplicationRepository
from services.compliance.compliance_service import ComplianceService
from models.agronomy.application import NitrogenApplication

class NitrogenApplicationService:
    """
    Handles nitrogen application tracking for agronomic compliance.
    Extracted from DispatchService to comply with Single Responsibility Principle.
    """
    def __init__(
        self,
        application_repo: ApplicationRepository,
        compliance_service: ComplianceService
    ):
        self.application_repo = application_repo
        self.compliance_service = compliance_service

    def register_application(
        self,
        site_id: int,
        load_id: int,
        batch_id: int,
        weight_net: float
    ) -> None:
        """
        Registers a nitrogen application for a dispatched load.
        
        Args:
            site_id: ID of the destination site
            load_id: ID of the load
            batch_id: ID of the batch
            weight_net: Net weight of the load (kg)
        """
        try:
            # Calculate actual N applied
            agronomics = self.compliance_service.calculate_load_agronomics(batch_id, weight_net)
            nitrogen_kg = agronomics['total_n_kg']
            
            app = NitrogenApplication(
                id=None,
                site_id=site_id,
                load_id=load_id,
                nitrogen_applied_kg=nitrogen_kg,
                application_date=date.today()
            )
            self.application_repo.add(app)
        except Exception as e:
            # Log warning but don't fail the dispatch
            print(f"Warning: Failed to register nitrogen application: {str(e)}")
