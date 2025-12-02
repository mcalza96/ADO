import streamlit as st
from models.masters.transport import Contractor
from models.masters.vehicle import Vehicle
from models.masters.driver import Driver
from ui.generic_master_view import render_generic_master_view

def render(driver_service, vehicle_service, contractor_service):
    """
    Vista de gestión de Transporte usando Vistas Genéricas.
    """
    st.header("🚛 Gestión de Transporte (Genérico)")
    
    tab1, tab2, tab3 = st.tabs(["Contratistas", "Choferes", "Camiones"])
    
    with tab1:
        render_generic_master_view(contractor_service, Contractor, "Contratista", ["id", "name", "rut", "phone"])
        
    with tab2:
        # Note: Generic view doesn't handle foreign key dropdowns yet.
        # For now, we accept manual ID entry or we need to enhance GenericMasterView.
        # Given the instruction "si logras hacer que...", I'll use the basic version.
        # If the user wants dropdowns, I'd need to pass related services or options.
        render_generic_master_view(driver_service, Driver, "Chofer", ["id", "name", "rut", "contractor_id"])
        
    with tab3:
        render_generic_master_view(vehicle_service, Vehicle, "Camión", ["id", "license_plate", "brand", "model", "contractor_id"])
