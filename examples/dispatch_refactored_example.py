"""
PRACTICAL EXAMPLE: Dispatch Flow with New Architecture

This example shows how to refactor the dispatch truck flow using:
1. Modular container (bounded contexts)
2. Application service layer
3. Pydantic DTOs for validation

This is a TEMPLATE for migrating other UI flows.
"""

# ============================================================================
# PART 1: APPLICATION SERVICE (NEW LAYER)
# ============================================================================

from typing import Optional
from datetime import datetime
from domain.logistics.dtos import (
    DispatchRequestDTO,
    DispatchResponseDTO,
    ComplianceCheckRequestDTO,
    ComplianceCheckResponseDTO
)
from domain.logistics.services.dispatch_service import LogisticsDomainService
from domain.shared.services.compliance_service import ComplianceService
from domain.disposal.services.agronomy_service import AgronomyDomainService
from services.operations.manifest_service import ManifestService
from domain.shared.exceptions import ComplianceViolationError, DomainException


class DispatchApplicationService:
    """
    Application Service for Dispatch Use Cases.
    
    Responsibilities:
    - Receive validated DTOs from UI
    - Orchestrate domain services
    - Handle transactions
    - Return DTOs to UI
    
    This layer has NO business logic - only coordination.
    """
    
    def __init__(
        self,
        logistics_service: LogisticsDomainService,
        compliance_service: ComplianceService,
        agronomy_service: AgronomyDomainService,
        manifest_service: ManifestService
    ):
        self.logistics_service = logistics_service
        self.compliance_service = compliance_service
        self.agronomy_service = agronomy_service
        self.manifest_service = manifest_service
    
    def check_compliance_before_dispatch(
        self,
        request: ComplianceCheckRequestDTO
    ) -> ComplianceCheckResponseDTO:
        """
        Check if dispatch is compliant BEFORE creating load.
        
        This allows UI to show warnings before user commits.
        """
        try:
            # Use domain service to validate
            is_compliant = self.compliance_service.validate_dispatch(
                request.batch_id,
                request.site_id,
                request.planned_tonnage
            )
            
            # Calculate details
            agronomics = self.compliance_service.calculate_load_agronomics(
                request.batch_id,
                request.planned_tonnage
            )
            
            site_capacity = self.compliance_service.get_site_nitrogen_capacity(
                request.site_id
            )
            
            nitrogen_to_add = agronomics['total_n_kg']
            remaining_after = site_capacity['remaining_kg'] - nitrogen_to_add
            percent_after = ((site_capacity['applied_kg'] + nitrogen_to_add) / 
                           site_capacity['limit_kg'] * 100)
            
            warnings = []
            if percent_after > 80:
                warnings.append(f"Site will be at {percent_after:.1f}% capacity after this load")
            
            return ComplianceCheckResponseDTO(
                is_compliant=is_compliant,
                nitrogen_to_add_kg=nitrogen_to_add,
                site_nitrogen_remaining_kg=remaining_after,
                site_capacity_percent_after=percent_after,
                violations=[],
                warnings=warnings
            )
            
        except ComplianceViolationError as e:
            return ComplianceCheckResponseDTO(
                is_compliant=False,
                nitrogen_to_add_kg=0,
                site_nitrogen_remaining_kg=0,
                site_capacity_percent_after=0,
                violations=[str(e)],
                warnings=[]
            )
    
    def execute_dispatch(
        self,
        request: DispatchRequestDTO
    ) -> DispatchResponseDTO:
        """
        Execute the complete dispatch flow.
        
        Steps:
        1. Validate compliance
        2. Dispatch truck (create load)
        3. Reserve batch stock
        4. Register nitrogen application
        5. Generate manifest
        
        Args:
            request: Validated DispatchRequestDTO from UI
            
        Returns:
            DispatchResponseDTO with result or error
        """
        try:
            # Step 1: Final compliance check
            self.compliance_service.validate_dispatch(
                request.batch_id,
                request.destination_site_id,
                request.weight_net
            )
            
            # Step 2: Create load using logistics domain service
            load = self.logistics_service.dispatch_truck(
                batch_id=request.batch_id,
                driver_id=request.driver_id,
                vehicle_id=request.vehicle_id,
                destination_site_id=request.destination_site_id,
                origin_facility_id=request.origin_facility_id,
                weight_net=request.weight_net,
                guide_number=request.guide_number,
                container_id=request.container_id
            )
            
            # Step 3: Calculate agronomics for response
            agronomics = self.compliance_service.calculate_load_agronomics(
                request.batch_id,
                request.weight_net
            )
            
            # Step 4: Generate manifest
            manifest_path = self.manifest_service.generate_manifest(load.id)
            
            # Step 5: Return success DTO
            return DispatchResponseDTO(
                success=True,
                load_id=load.id,
                manifest_code=load.manifest_code,
                manifest_path=manifest_path,
                nitrogen_applied_kg=agronomics['total_n_kg'],
                estimated_arrival=load.eta if hasattr(load, 'eta') else None,
                error_message=None,
                validation_warnings=[]
            )
            
        except ComplianceViolationError as e:
            # Compliance violation (business rule)
            return DispatchResponseDTO(
                success=False,
                error_message=f"Compliance violation: {str(e)}",
                validation_warnings=[]
            )
            
        except DomainException as e:
            # Other domain errors
            return DispatchResponseDTO(
                success=False,
                error_message=f"Domain error: {str(e)}",
                validation_warnings=[]
            )
            
        except Exception as e:
            # Unexpected errors
            return DispatchResponseDTO(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                validation_warnings=[]
            )


# ============================================================================
# PART 2: UI LAYER (STREAMLIT)
# ============================================================================

import streamlit as st
from pydantic import ValidationError
from config.dependencies import get_container
from domain.logistics.dtos import (
    DispatchRequestDTO,
    ComplianceCheckRequestDTO
)


def dispatch_truck_view():
    """
    Streamlit UI for dispatching trucks.
    
    This is PRESENTATION ONLY - no business logic here.
    """
    st.header("🚛 Dispatch Truck")
    
    # Get container
    container = get_container()
    
    # Get master data for dropdowns
    batches = container.processing.batch_service.get_available_batches()
    drivers = container.logistics.driver_service.get_all(active_only=True)
    vehicles = container.logistics.vehicle_service.get_all(active_only=True)
    sites = container.agronomy.location_service.get_all_sites(active_only=True)
    facilities = container.processing.facility_service.get_all(active_only=True)
    
    # Form
    with st.form("dispatch_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Origin")
            facility = st.selectbox(
                "Facility",
                facilities,
                format_func=lambda f: f.name
            )
            
            batch = st.selectbox(
                "Batch",
                batches,
                format_func=lambda b: f"{b.code} - {b.available_volume_m3:.1f}m³"
            )
            
            weight = st.number_input(
                "Weight (kg)",
                min_value=0.0,
                max_value=50000.0,
                value=15000.0,
                step=100.0,
                help="Net weight to dispatch (max 50 tons)"
            )
            
            guide_number = st.text_input(
                "Transport Guide",
                help="Optional transport guide number"
            )
        
        with col2:
            st.subheader("Destination")
            site = st.selectbox(
                "Site",
                sites,
                format_func=lambda s: f"{s.name} ({s.region})"
            )
            
            driver = st.selectbox(
                "Driver",
                drivers,
                format_func=lambda d: f"{d.name} - {d.license}"
            )
            
            vehicle = st.selectbox(
                "Vehicle",
                vehicles,
                format_func=lambda v: f"{v.plate} ({v.type})"
            )
        
        # Preview compliance BEFORE dispatch
        check_button = st.form_submit_button("🔍 Check Compliance", type="secondary")
        dispatch_button = st.form_submit_button("✅ Dispatch", type="primary")
    
    # Handle compliance check
    if check_button:
        try:
            check_request = ComplianceCheckRequestDTO(
                batch_id=batch.id,
                site_id=site.id,
                planned_tonnage=weight
            )
            
            # Call application service (NOT domain service directly)
            check_result = container.dispatch_app_service.check_compliance_before_dispatch(
                check_request
            )
            
            if check_result.is_compliant:
                st.success("✅ Dispatch is compliant")
                st.info(f"This load will add {check_result.nitrogen_to_add_kg:.1f} kg N")
                st.info(f"Site will be at {check_result.site_capacity_percent_after:.1f}% capacity")
                
                for warning in check_result.warnings:
                    st.warning(f"⚠️ {warning}")
            else:
                st.error("❌ Dispatch is NOT compliant")
                for violation in check_result.violations:
                    st.error(f"🚫 {violation}")
                    
        except ValidationError as e:
            st.error(f"Validation error: {e}")
    
    # Handle dispatch
    if dispatch_button:
        try:
            # Create validated DTO (Pydantic validates automatically)
            dispatch_request = DispatchRequestDTO(
                batch_id=batch.id,
                driver_id=driver.id,
                vehicle_id=vehicle.id,
                destination_site_id=site.id,
                origin_facility_id=facility.id,
                weight_net=weight,
                guide_number=guide_number if guide_number else None,
                container_id=None,
                scheduled_date=datetime.now()
            )
            
            # Call application service (NOT domain service directly)
            result = container.dispatch_app_service.execute_dispatch(dispatch_request)
            
            # Handle response
            if result.success:
                st.success(f"✅ Load {result.manifest_code} dispatched successfully!")
                
                # Show details
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Load ID", result.load_id)
                    st.metric("Manifest Code", result.manifest_code)
                with col2:
                    st.metric("Nitrogen Applied", f"{result.nitrogen_applied_kg:.1f} kg N")
                    if result.estimated_arrival:
                        st.metric("ETA", result.estimated_arrival.strftime("%H:%M"))
                
                # Download manifest
                if result.manifest_path:
                    with open(result.manifest_path, 'rb') as f:
                        st.download_button(
                            "📄 Download Manifest",
                            f,
                            file_name=f"{result.manifest_code}.pdf",
                            mime="application/pdf"
                        )
                
                # Warnings (if any)
                for warning in result.validation_warnings:
                    st.warning(f"⚠️ {warning}")
                    
            else:
                # Show error from application service
                st.error(f"❌ Dispatch failed: {result.error_message}")
                
        except ValidationError as e:
            # Pydantic validation failed (data invalid)
            st.error("❌ Validation Error")
            st.error(str(e))
            st.info("Please check the form values and try again.")
            
        except Exception as e:
            # Unexpected error
            st.error(f"❌ Unexpected error: {str(e)}")


# ============================================================================
# PART 3: WIRING IN CONTAINER
# ============================================================================

"""
Add to config/dependencies.py in LogisticsContainer:

class LogisticsContainer:
    def __init__(self, db_manager, event_bus, batch_service, compliance_service, 
                 agronomy_service, manifest_service):
        # ... existing code ...
        
        # Application Service (NEW)
        from domain.logistics.application_service import DispatchApplicationService
        self.dispatch_app_service = DispatchApplicationService(
            self.dispatch_service,
            compliance_service,
            agronomy_service,
            manifest_service
        )

Then update the backward compatibility aliases:
    container.dispatch_app_service = container.logistics.dispatch_app_service
"""


# ============================================================================
# PART 4: TESTING
# ============================================================================

import pytest
from unittest.mock import Mock, MagicMock
from domain.logistics.dtos import DispatchRequestDTO, DispatchResponseDTO


class TestDispatchApplicationService:
    """
    Unit tests for DispatchApplicationService.
    
    Note: Application services are easy to test because they
    just orchestrate - no complex business logic.
    """
    
    def test_execute_dispatch_success(self):
        # Arrange
        mock_logistics = Mock()
        mock_compliance = Mock()
        mock_agronomy = Mock()
        mock_manifest = Mock()
        
        mock_load = Mock(id=123, manifest_code="MAN-2024-001")
        mock_logistics.dispatch_truck.return_value = mock_load
        
        mock_compliance.validate_dispatch.return_value = True
        mock_compliance.calculate_load_agronomics.return_value = {
            'total_n_kg': 750.0
        }
        
        mock_manifest.generate_manifest.return_value = "/tmp/manifest.pdf"
        
        service = DispatchApplicationService(
            mock_logistics,
            mock_compliance,
            mock_agronomy,
            mock_manifest
        )
        
        request = DispatchRequestDTO(
            batch_id=10,
            driver_id=5,
            vehicle_id=3,
            destination_site_id=7,
            origin_facility_id=1,
            weight_net=15000.0
        )
        
        # Act
        response = service.execute_dispatch(request)
        
        # Assert
        assert response.success is True
        assert response.load_id == 123
        assert response.manifest_code == "MAN-2024-001"
        assert response.nitrogen_applied_kg == 750.0
        assert response.manifest_path == "/tmp/manifest.pdf"
        
        # Verify orchestration
        mock_compliance.validate_dispatch.assert_called_once()
        mock_logistics.dispatch_truck.assert_called_once()
        mock_manifest.generate_manifest.assert_called_once_with(123)
    
    def test_execute_dispatch_compliance_violation(self):
        # Arrange
        mock_logistics = Mock()
        mock_compliance = Mock()
        mock_agronomy = Mock()
        mock_manifest = Mock()
        
        mock_compliance.validate_dispatch.side_effect = ComplianceViolationError(
            "Site nitrogen capacity exceeded"
        )
        
        service = DispatchApplicationService(
            mock_logistics,
            mock_compliance,
            mock_agronomy,
            mock_manifest
        )
        
        request = DispatchRequestDTO(
            batch_id=10,
            driver_id=5,
            vehicle_id=3,
            destination_site_id=7,
            origin_facility_id=1,
            weight_net=15000.0
        )
        
        # Act
        response = service.execute_dispatch(request)
        
        # Assert
        assert response.success is False
        assert "nitrogen capacity exceeded" in response.error_message.lower()
        
        # Verify dispatch was NOT called after compliance failure
        mock_logistics.dispatch_truck.assert_not_called()


class TestDispatchRequestDTO:
    """
    Tests for Pydantic validation in DTOs.
    """
    
    def test_valid_dispatch_request(self):
        # Valid request
        request = DispatchRequestDTO(
            batch_id=10,
            driver_id=5,
            vehicle_id=3,
            destination_site_id=7,
            origin_facility_id=1,
            weight_net=15000.0
        )
        
        assert request.weight_net == 15000.0
    
    def test_negative_weight_raises_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            DispatchRequestDTO(
                batch_id=10,
                driver_id=5,
                vehicle_id=3,
                destination_site_id=7,
                origin_facility_id=1,
                weight_net=-100.0  # Invalid!
            )
        
        assert "weight_net" in str(exc_info.value)
    
    def test_weight_exceeds_max_raises_validation_error(self):
        with pytest.raises(ValidationError):
            DispatchRequestDTO(
                batch_id=10,
                driver_id=5,
                vehicle_id=3,
                destination_site_id=7,
                origin_facility_id=1,
                weight_net=60000.0  # Too heavy! Max is 50000
            )
    
    def test_zero_id_raises_validation_error(self):
        with pytest.raises(ValidationError):
            DispatchRequestDTO(
                batch_id=0,  # Invalid! Must be > 0
                driver_id=5,
                vehicle_id=3,
                destination_site_id=7,
                origin_facility_id=1,
                weight_net=15000.0
            )


# ============================================================================
# SUMMARY
# ============================================================================

"""
This example shows the COMPLETE refactored flow:

1. ✅ Application Service Layer
   - DispatchApplicationService
   - Orchestrates domain services
   - Receives/returns DTOs
   - No business logic

2. ✅ Pydantic DTOs
   - DispatchRequestDTO (automatic validation)
   - DispatchResponseDTO (type-safe response)
   - ComplianceCheckDTO (pre-validation)

3. ✅ Clean UI
   - No business logic
   - Calls application service
   - Handles DTOs only
   - Type-safe

4. ✅ Easy to Test
   - Mock domain services
   - Test orchestration only
   - DTO validation tested separately

NEXT STEPS:
1. Save this as domain/logistics/application_service.py
2. Update config/dependencies.py to wire it up
3. Refactor ui/operations/dispatch_view.py to use it
4. Run tests
5. Repeat for other flows (reception, batch creation, etc.)
"""
