"""
Vista de Gestión de Parámetros Financieros del ERP.

Este módulo contiene la interfaz gráfica para configurar los parámetros que
alimentan el motor de cálculo de tarifas:
- Indicadores económicos mensuales (UF, Precio Petróleo)
- Matriz de distancias (Planta→Planta, Planta→Campo)
- Tarifarios de contratistas (costos) y clientes (ingresos)

Autor: Senior Frontend Engineer - ERP Team
Refactorizado: 2025-12-05 - Datos reales con persistencia en BD
"""

import streamlit as st
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from container import get_container


# ==============================================================================
# HELPER FUNCTIONS - Data Loading
# ==============================================================================

def _load_clients(client_service) -> List[Dict[str, Any]]:
    """Carga clientes desde la base de datos."""
    clients = client_service.get_all()
    return [{"id": c.id, "name": c.name, "rut": c.rut or ""} for c in clients]


def _load_facilities(facility_service, client_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Carga facilities (plantas de cliente/origen) desde la base de datos.
    
    Args:
        facility_service: Servicio de facilities inyectado
        client_id: Si se proporciona, filtra solo las de ese cliente
    """
    if client_id:
        facilities = facility_service.get_by_client(client_id)
    else:
        facilities = facility_service.get_all()
    
    return [{
        "id": f.id,
        "name": f.name,
        "client_id": f.client_id,
        "is_link_point": getattr(f, 'is_link_point', False),
        "type": "FACILITY"
    } for f in facilities]


def _load_treatment_plants(treatment_plant_service) -> List[Dict[str, Any]]:
    """
    Carga plantas de tratamiento propias desde la base de datos.
    Estas siempre aparecen como destinos disponibles.
    
    Args:
        treatment_plant_service: Servicio de plantas de tratamiento inyectado
    """
    plants = treatment_plant_service.get_all()
    return [{
        "id": p.id,
        "name": p.name,
        "type": "TREATMENT_PLANT"
    } for p in plants]


def _load_sites(location_service) -> List[Dict[str, Any]]:
    """Carga sitios/campos de disposición desde la base de datos.
    
    Args:
        location_service: Servicio de ubicaciones inyectado
    """
    sites = location_service.get_all_sites()
    return [{
        "id": s.id,
        "name": s.name,
        "owner_name": getattr(s, 'owner_name', ''),
        "type": "SITE"
    } for s in sites]


def _load_contractors(contractor_service) -> List[Dict[str, Any]]:
    """Carga contratistas desde la base de datos.
    
    Args:
        contractor_service: Servicio de contratistas inyectado
    """
    contractors = contractor_service.get_all()
    return [{"id": c.id, "name": c.name, "rut": c.rut or ""} for c in contractors]


# ==============================================================================
# MAIN RENDER FUNCTION
# ==============================================================================

def render(economic_repo=None, distance_repo=None, contractor_tariffs_repo=None, 
           client_tariffs_repo=None, facility_service=None, site_service=None,
           contractor_service=None, client_service=None):
    """
    Vista principal de Parámetros Financieros con inyección de dependencias.
    
    Args:
        economic_repo: Repositorio de indicadores económicos (EconomicIndicatorsRepository)
        distance_repo: Repositorio de matriz de distancias (DistanceMatrixRepository)
        contractor_tariffs_repo: Repositorio de tarifas de contratistas (ContractorTariffsRepository)
        client_tariffs_repo: Repositorio de tarifas de clientes (ClientTariffsRepository)
        facility_service: Servicio de facilities
        site_service: Servicio de sitios (alias de location_service)
        contractor_service: Servicio de contratistas
        client_service: Servicio de clientes
    """
    st.title("💰 Parámetros Financieros")
    st.markdown("**Configuración de datos maestros para el motor de cálculo de tarifas**")
    
    # Obtener servicios del container si no fueron inyectados
    container = get_container()
    client_service = client_service or container.client_service
    facility_service = facility_service or container.facility_service
    location_service = site_service or container.location_service
    contractor_service = contractor_service or container.contractor_service
    treatment_plant_service = container.treatment_plant_service
    
    # Inicializar estado de la sesión
    if 'finance_success_msg' not in st.session_state:
        st.session_state.finance_success_msg = None
    if 'finance_error_msg' not in st.session_state:
        st.session_state.finance_error_msg = None
    if 'economic_indicators_data' not in st.session_state:
        st.session_state.economic_indicators_data = []
    if 'contractor_tariffs_data' not in st.session_state:
        st.session_state.contractor_tariffs_data = []
    if 'client_tariffs_data' not in st.session_state:
        st.session_state.client_tariffs_data = []
    
    # Mostrar mensajes de estado
    if st.session_state.finance_success_msg:
        st.success(st.session_state.finance_success_msg)
        st.session_state.finance_success_msg = None
    
    if st.session_state.finance_error_msg:
        st.error(st.session_state.finance_error_msg)
        st.session_state.finance_error_msg = None
    
    # Crear tabs principales
    tab1, tab2, tab3 = st.tabs([
        "📈 Indicadores Económicos",
        "🛣️ Matriz de Distancias",
        "💲 Tarifarios"
    ])
    
    with tab1:
        _render_economic_indicators_tab()
    
    with tab2:
        _render_distance_matrix_tab(distance_repo, client_service, facility_service, location_service, treatment_plant_service)
    
    with tab3:
        _render_tariffs_tab(client_service, contractor_service)


# ==============================================================================
# TAB 1: PROFORMAS (Economic Indicators + Vehicle Tariffs)
# ==============================================================================

def _render_economic_indicators_tab():
    """Renderiza el tab de Proformas con indicadores económicos y tarifas por tipo de vehículo."""
    st.header("📈 Proformas - Estados de Pago")
    st.markdown("""
    Configure los valores mensuales de UF, Precio de Petróleo y **tarifas por tipo de vehículo** 
    para el cálculo de costos de transporte.
    
    **Reglas de Tarifas:**
    - Solo la **primera proforma** permite editar las tarifas base manualmente.
    - Las proformas siguientes calculan las tarifas automáticamente: `tarifa = tarifa_anterior × (fuel_nuevo / fuel_anterior)`
    """)
    
    # Cargar proformas desde el repositorio
    container = get_container()
    proforma_repo = container.proforma_repo
    
    # Obtener todas las proformas ordenadas ASC (primera es la base)
    proformas = proforma_repo.get_all()
    first_proforma = proforma_repo.get_first_proforma()
    
    # Tabs para Nueva Proforma vs Lista Existente
    tab_list, tab_new = st.tabs(["📋 Proformas Existentes", "➕ Nueva Proforma"])
    
    with tab_list:
        _render_proformas_list(proforma_repo, proformas, first_proforma)
    
    with tab_new:
        _render_new_proforma_form(proforma_repo, proformas, first_proforma)


def _render_proformas_list(proforma_repo, proformas, first_proforma):
    """Renderiza la lista de proformas existentes con tarifas."""
    st.subheader("📋 Proformas Registradas")
    
    if not proformas:
        st.info("📊 No hay proformas registradas. Cree la primera proforma (base) para comenzar.")
        return
    
    # Mostrar tabla de proformas
    display_data = []
    for p in proformas:
        is_first = first_proforma and p.id == first_proforma.id
        status_icon = "🔒" if p.is_closed else "🔓"
        base_badge = " ⭐" if is_first else ""
        
        display_data.append({
            'Código': f"{p.proforma_code}{base_badge}",
            'Período': f"{p.period_year}-{p.period_month:02d}",
            'Ciclo': f"{p.cycle_start_date.strftime('%d/%m')} → {p.cycle_end_date.strftime('%d/%m/%Y')}",
            'UF': f"${p.uf_value:,.2f}",
            'Petróleo': f"${p.fuel_price:,.0f}/L",
            'Batea': f"{p.tariff_batea_uf:.6f}" if p.tariff_batea_uf else "-",
            'Ampliroll': f"{p.tariff_ampliroll_uf:.6f}" if p.tariff_ampliroll_uf else "-",
            'Ampliroll+Carro': f"{p.tariff_ampliroll_carro_uf:.6f}" if p.tariff_ampliroll_carro_uf else "-",
            'Estado': f"{status_icon} {'Cerrada' if p.is_closed else 'Abierta'}"
        })
    
    st.dataframe(display_data, hide_index=True, use_container_width=True)
    
    st.caption("⭐ = Proforma base (tarifas editables manualmente)")
    
    # Sección de edición
    st.divider()
    st.subheader("✏️ Editar Proforma")
    
    # Filtrar proformas abiertas
    open_proformas = [p for p in proformas if not p.is_closed]
    
    if not open_proformas:
        st.warning("⚠️ No hay proformas abiertas para editar.")
        return
    
    # Selector de proforma
    proforma_options = {f"{p.proforma_code} ({p.period_year}-{p.period_month:02d})": p for p in open_proformas}
    selected_key = st.selectbox("Seleccionar Proforma", list(proforma_options.keys()))
    selected_proforma = proforma_options[selected_key]
    
    is_first = first_proforma and selected_proforma.id == first_proforma.id
    
    # Formulario de edición
    with st.form("edit_proforma_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Indicadores Económicos**")
            new_uf = st.number_input(
                "Valor UF (CLP)",
                min_value=0.01,
                max_value=100000.0,
                value=float(selected_proforma.uf_value),
                step=100.0
            )
            new_fuel = st.number_input(
                "Precio Petróleo (CLP/L)",
                min_value=0.01,
                max_value=10000.0,
                value=float(selected_proforma.fuel_price),
                step=10.0
            )
        
        with col2:
            st.markdown("**🚛 Tarifas por Tipo de Vehículo (UF/ton-km)**")
            
            if is_first:
                # Primera proforma: tarifas editables
                new_tariff_batea = st.number_input(
                    "Tarifa Batea",
                    min_value=0.000001,
                    max_value=1.0,
                    value=float(selected_proforma.tariff_batea_uf or 0.001460),
                    step=0.000001,
                    format="%.6f"
                )
                new_tariff_ampliroll = st.number_input(
                    "Tarifa Ampliroll",
                    min_value=0.000001,
                    max_value=1.0,
                    value=float(selected_proforma.tariff_ampliroll_uf or 0.002962),
                    step=0.000001,
                    format="%.6f"
                )
                new_tariff_ampliroll_carro = st.number_input(
                    "Tarifa Ampliroll + Carro",
                    min_value=0.000001,
                    max_value=1.0,
                    value=float(selected_proforma.tariff_ampliroll_carro_uf or 0.001793),
                    step=0.000001,
                    format="%.6f"
                )
            else:
                # Proformas siguientes: tarifas calculadas automáticamente
                st.info("💡 Las tarifas se calculan automáticamente con fórmula polinómica (factor 0.5).")
                
                # Obtener proforma anterior para calcular preview
                previous = proforma_repo.get_previous(selected_proforma.period_year, selected_proforma.period_month)
                
                if previous and previous.fuel_price and previous.fuel_price > 0:
                    # Fórmula polinómica: 1 + 0.5 × (fuel_nuevo - fuel_anterior) / fuel_anterior
                    fuel_variation = (new_fuel - previous.fuel_price) / previous.fuel_price
                    adjustment_factor = 1 + 0.5 * fuel_variation
                    
                    calc_batea = round((previous.tariff_batea_uf or 0) * adjustment_factor, 6)
                    calc_ampliroll = round((previous.tariff_ampliroll_uf or 0) * adjustment_factor, 6)
                    calc_ampliroll_carro = round((previous.tariff_ampliroll_carro_uf or 0) * adjustment_factor, 6)
                    
                    st.metric("Batea (calculada)", f"{calc_batea:.6f}")
                    st.metric("Ampliroll (calculada)", f"{calc_ampliroll:.6f}")
                    st.metric("Ampliroll+Carro (calculada)", f"{calc_ampliroll_carro:.6f}")
                    st.caption(f"Variación fuel: {fuel_variation*100:.2f}% → Factor ajuste: {adjustment_factor:.4f}")
                    
                    new_tariff_batea = calc_batea
                    new_tariff_ampliroll = calc_ampliroll
                    new_tariff_ampliroll_carro = calc_ampliroll_carro
                else:
                    st.warning("⚠️ No se encontró proforma anterior para calcular tarifas.")
                    new_tariff_batea = selected_proforma.tariff_batea_uf
                    new_tariff_ampliroll = selected_proforma.tariff_ampliroll_uf
                    new_tariff_ampliroll_carro = selected_proforma.tariff_ampliroll_carro_uf
        
        col_save, col_close = st.columns(2)
        
        with col_save:
            save_clicked = st.form_submit_button("💾 Guardar Cambios", type="primary")
        
        with col_close:
            close_clicked = st.form_submit_button("🔒 Cerrar Proforma")
        
        if save_clicked:
            try:
                # Actualizar proforma
                selected_proforma.uf_value = new_uf
                selected_proforma.fuel_price = new_fuel
                selected_proforma.tariff_batea_uf = new_tariff_batea
                selected_proforma.tariff_ampliroll_uf = new_tariff_ampliroll
                selected_proforma.tariff_ampliroll_carro_uf = new_tariff_ampliroll_carro
                
                proforma_repo.update(selected_proforma)
                st.session_state.finance_success_msg = f"✅ Proforma {selected_proforma.proforma_code} actualizada"
                st.rerun()
            except Exception as e:
                st.session_state.finance_error_msg = f"❌ Error: {str(e)}"
                st.rerun()
        
        if close_clicked:
            try:
                proforma_repo.close_proforma(selected_proforma.id, auto_create_next=True)
                st.session_state.finance_success_msg = f"✅ Proforma {selected_proforma.proforma_code} cerrada. Se creó la siguiente proforma automáticamente."
                st.rerun()
            except Exception as e:
                st.session_state.finance_error_msg = f"❌ Error al cerrar: {str(e)}"
                st.rerun()


def _render_new_proforma_form(proforma_repo, proformas, first_proforma):
    """Renderiza el formulario para crear una nueva proforma."""
    st.subheader("➕ Crear Nueva Proforma")
    
    is_first_ever = len(proformas) == 0
    
    if is_first_ever:
        st.info("🌟 Esta será la **proforma base**. Las tarifas que ingrese serán la referencia para cálculos futuros.")
    else:
        st.info("💡 Las tarifas se calcularán automáticamente basándose en la última proforma.")
    
    with st.form("new_proforma_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            year = st.selectbox(
                "Año",
                options=list(range(2024, 2027)),
                index=1  # Default 2025
            )
            month = st.selectbox(
                "Mes",
                options=list(range(1, 13)),
                format_func=lambda x: f"{x:02d} - {['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'][x-1]}",
                index=10  # Default Noviembre
            )
            
            # Preview del código y ciclo
            from domain.finance.entities.finance_entities import Proforma
            preview_code = Proforma.generate_code(year, month)
            cycle_start, cycle_end = Proforma.calculate_cycle_dates(year, month)
            st.caption(f"**Código:** {preview_code}")
            st.caption(f"**Ciclo:** {cycle_start.strftime('%d/%m/%Y')} → {cycle_end.strftime('%d/%m/%Y')}")
        
        with col2:
            uf_value = st.number_input(
                "Valor UF (CLP)",
                min_value=0.01,
                max_value=100000.0,
                value=38000.0,
                step=100.0
            )
            fuel_price = st.number_input(
                "Precio Petróleo (CLP/L)",
                min_value=0.01,
                max_value=10000.0,
                value=1250.0,
                step=10.0
            )
        
        # Tarifas
        st.markdown("---")
        st.markdown("**🚛 Tarifas por Tipo de Vehículo (UF/ton-km)**")
        
        if is_first_ever:
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                tariff_batea = st.number_input(
                    "Tarifa Batea",
                    min_value=0.000001,
                    max_value=1.0,
                    value=0.001460,
                    step=0.000001,
                    format="%.6f"
                )
            with col_t2:
                tariff_ampliroll = st.number_input(
                    "Tarifa Ampliroll",
                    min_value=0.000001,
                    max_value=1.0,
                    value=0.002962,
                    step=0.000001,
                    format="%.6f"
                )
            with col_t3:
                tariff_ampliroll_carro = st.number_input(
                    "Tarifa Ampliroll + Carro",
                    min_value=0.000001,
                    max_value=1.0,
                    value=0.001793,
                    step=0.000001,
                    format="%.6f"
                )
        else:
            # Calcular desde la última proforma con fórmula polinómica
            last_proforma = proformas[-1] if proformas else None
            if last_proforma and last_proforma.fuel_price and last_proforma.fuel_price > 0:
                # Fórmula polinómica: 1 + 0.5 × (fuel_nuevo - fuel_anterior) / fuel_anterior
                fuel_variation = (fuel_price - last_proforma.fuel_price) / last_proforma.fuel_price
                adjustment_factor = 1 + 0.5 * fuel_variation
                
                tariff_batea = round((last_proforma.tariff_batea_uf or 0.001460) * adjustment_factor, 6)
                tariff_ampliroll = round((last_proforma.tariff_ampliroll_uf or 0.002962) * adjustment_factor, 6)
                tariff_ampliroll_carro = round((last_proforma.tariff_ampliroll_carro_uf or 0.001793) * adjustment_factor, 6)
                
                col_t1, col_t2, col_t3 = st.columns(3)
                with col_t1:
                    st.metric("Batea", f"{tariff_batea:.6f}")
                with col_t2:
                    st.metric("Ampliroll", f"{tariff_ampliroll:.6f}")
                with col_t3:
                    st.metric("Ampliroll+Carro", f"{tariff_ampliroll_carro:.6f}")
                
                st.caption(f"Variación fuel: {fuel_variation*100:.2f}% → Factor ajuste: {adjustment_factor:.4f}")
            else:
                tariff_batea = 0.001460
                tariff_ampliroll = 0.002962
                tariff_ampliroll_carro = 0.001793
                st.warning("⚠️ No se pudo calcular desde proforma anterior, usando valores por defecto.")
        
        submitted = st.form_submit_button("💾 Crear Proforma", type="primary")
        
        if submitted:
            # Verificar si ya existe
            existing = proforma_repo.get_by_period(year, month)
            if existing:
                st.session_state.finance_error_msg = f"❌ Ya existe una proforma para {year}-{month:02d}"
                st.rerun()
            
            try:
                # Crear nueva proforma
                from domain.finance.entities.finance_entities import Proforma
                cycle_start, cycle_end = Proforma.calculate_cycle_dates(year, month)
                
                new_proforma = Proforma(
                    id=None,
                    proforma_code=Proforma.generate_code(year, month),
                    period_year=year,
                    period_month=month,
                    cycle_start_date=cycle_start,
                    cycle_end_date=cycle_end,
                    uf_value=uf_value,
                    fuel_price=fuel_price,
                    tariff_batea_uf=tariff_batea,
                    tariff_ampliroll_uf=tariff_ampliroll,
                    tariff_ampliroll_carro_uf=tariff_ampliroll_carro,
                    is_closed=False
                )
                
                proforma_repo.create(new_proforma)
                st.session_state.finance_success_msg = f"✅ Proforma {new_proforma.proforma_code} creada exitosamente"
                st.rerun()
            except Exception as e:
                st.session_state.finance_error_msg = f"❌ Error al crear: {str(e)}"
                st.rerun()


# ==============================================================================
# TAB 2: DISTANCE MATRIX
# ==============================================================================

def _render_distance_matrix_tab(distance_repo, client_service, facility_service, location_service, treatment_plant_service):
    """
    Renderiza el tab de Matriz de Distancias con datos reales.
    
    Características:
    - Filtro por cliente (las plantas de tratamiento propias siempre aparecen)
    - Validación de duplicados
    - Edición de distancias existentes
    - Persistencia en base de datos
    
    Args:
        distance_repo: Repositorio de distancias
        client_service: Servicio de clientes
        facility_service: Servicio de facilities
        location_service: Servicio de ubicaciones (sitios)
        treatment_plant_service: Servicio de plantas de tratamiento
    """
    st.header("🛣️ Matriz de Distancias")
    st.markdown("""
    Configure las distancias para viajes directos (Planta→Campo) y tramos de enlace (Planta→Planta).
    Las **plantas de tratamiento propias** siempre aparecen como destinos disponibles.
    """)
    
    # Cargar datos reales usando servicios inyectados
    clients = _load_clients(client_service)
    treatment_plants = _load_treatment_plants(treatment_plant_service)
    sites = _load_sites(location_service)
    
    # Subtabs para organizar
    sub_tab_new, sub_tab_existing = st.tabs(["➕ Nueva Ruta", "📋 Rutas Existentes"])
    
    with sub_tab_new:
        _render_new_route_form(distance_repo, clients, treatment_plants, sites, facility_service)
    
    with sub_tab_existing:
        _render_existing_routes(distance_repo, clients)


def _render_new_route_form(distance_repo, clients, treatment_plants, sites, facility_service):
    """Formulario para crear nueva ruta.
    
    Args:
        distance_repo: Repositorio de distancias
        clients: Lista de clientes
        treatment_plants: Lista de plantas de tratamiento
        sites: Lista de sitios
        facility_service: Servicio de facilities para cargar facilities dinámicamente
    """
    st.subheader("Configurar Nueva Ruta")
    
    # =========================================================================
    # PASO 1: Seleccionar Origen (fuera del form para actualización dinámica)
    # =========================================================================
    st.markdown("##### 1️⃣ Seleccionar Origen")
    
    client_options = {"Todos los clientes": None}
    client_options.update({f"{c['name']} ({c['rut']})" if c['rut'] else c['name']: c['id'] for c in clients})
    
    selected_client_label = st.selectbox(
        "Filtrar por Cliente",
        options=list(client_options.keys()),
        key="filter_client_new"
    )
    selected_client_id = client_options[selected_client_label]
    
    # Cargar facilities filtradas por cliente usando servicio inyectado
    facilities = _load_facilities(facility_service, selected_client_id)
    
    if not facilities:
        st.warning("⚠️ No hay plantas de origen registradas para este cliente. Debe crear primero las plantas en la sección de Empresas.")
        return
    
    # Selector de origen (fuera del form)
    origin_options = {f.get('name', f'Planta {f["id"]}'): f['id'] for f in facilities}
    selected_origin_label = st.selectbox(
        "Planta de Origen *",
        options=list(origin_options.keys()),
        key="origin_select",
        help="Seleccione la planta del cliente desde donde parte el viaje"
    )
    origin_id = origin_options.get(selected_origin_label)
    
    # =========================================================================
    # PASO 2: Seleccionar Destino (fuera del form para actualización dinámica)
    # =========================================================================
    st.markdown("##### 2️⃣ Seleccionar Destino")
    
    # Tipo de destino (fuera del form para que actualice dinámicamente)
    dest_type = st.radio(
        "Tipo de Destino *",
        options=[
            "🏭 Planta de Tratamiento (Propia)",
            "🔗 Planta de Enlace (Cliente)",
            "🌾 Campo (Destino Final)"
        ],
        horizontal=True,
        key="dest_type_radio",
        help="Las plantas de tratamiento propias y las de enlace son para viajes multi-tramo"
    )
    
    # Construir opciones de destino según el tipo seleccionado
    dest_options = {}
    is_link = False
    
    if "Planta de Tratamiento" in dest_type:
        if not treatment_plants:
            st.warning("⚠️ No hay plantas de tratamiento propias registradas.")
        else:
            dest_options = {p['name']: ('TREATMENT_PLANT', p['id']) for p in treatment_plants}
        is_link = True
    elif "Planta de Enlace" in dest_type:
        # Solo mostrar facilities marcadas como link_point, excluyendo el origen
        link_facilities = [f for f in _load_facilities(facility_service) if f.get('is_link_point', False) and f['id'] != origin_id]
        
        if not link_facilities:
            st.warning("⚠️ No hay plantas de enlace configuradas. Marque plantas como 'Punto de Enlace' en la sección de Empresas > Plantas del Cliente.")
        else:
            dest_options = {f['name']: ('FACILITY', f['id']) for f in link_facilities}
        is_link = True
    else:  # Campo
        if not sites:
            st.warning("⚠️ No hay campos/sitios registrados.")
        else:
            dest_options = {f"{s['name']} - {s['owner_name']}" if s['owner_name'] else s['name']: ('SITE', s['id']) for s in sites}
        is_link = False
    
    # Selector de destino (fuera del form)
    if dest_options:
        selected_dest_label = st.selectbox(
            "Destino *",
            options=list(dest_options.keys()),
            key="dest_select"
        )
    else:
        selected_dest_label = None
        st.info("Seleccione un tipo de destino con opciones disponibles")
    
    # =========================================================================
    # PASO 3: Distancia y Guardar (dentro del form)
    # =========================================================================
    st.markdown("##### 3️⃣ Configurar Distancia")
    
    with st.form("distance_matrix_form"):
        col1, col2 = st.columns(2)
        with col1:
            distance_km = st.number_input(
                "Distancia (Km) *",
                min_value=0.1,
                max_value=2000.0,
                value=45.0,
                step=0.1,
                format="%.1f",
                help="Distancia en kilómetros del tramo (decimales permitidos)"
            )
        
        with col2:
            st.info(f"{'🔗 Tramo de Enlace' if is_link else '🏁 Destino Final'}")
        
        # Mostrar resumen de la ruta
        if selected_dest_label and dest_options:
            dest_type_str, dest_id = dest_options[selected_dest_label]
            st.caption(f"**Ruta:** {selected_origin_label} → {selected_dest_label}")
        
        submitted = st.form_submit_button("💾 Guardar Ruta", type="primary", use_container_width=True)
        
        if submitted:
            if not selected_dest_label or not dest_options:
                st.error("❌ Debe seleccionar un destino válido")
                st.stop()
            
            if distance_km <= 0:
                st.error("❌ La distancia debe ser positiva (> 0)")
                st.stop()
            
            # Obtener IDs para validación
            dest_type_str, dest_id = dest_options[selected_dest_label]
            
            # Validar que origen != destino (solo aplica si destino es FACILITY)
            if dest_type_str == 'FACILITY' and origin_id == dest_id:
                st.error("❌ El origen y el destino no pueden ser la misma planta")
                st.stop()
            
            # Verificar duplicados
            if distance_repo.check_duplicate(origin_id, dest_id, dest_type_str):
                st.error(f"❌ Ya existe una ruta desde '{selected_origin_label}' hacia '{selected_dest_label}'. Use la pestaña 'Rutas Existentes' para editarla.")
                st.stop()
            
            # Guardar en base de datos
            try:
                route_id = distance_repo.add(
                    origin_facility_id=origin_id,
                    destination_id=dest_id,
                    destination_type=dest_type_str,
                    distance_km=distance_km,
                    is_link_segment=is_link
                )
                st.success(f"✅ Ruta guardada: {selected_origin_label} → {selected_dest_label} ({distance_km:.1f} km)")
            except ValueError as e:
                st.error(f"❌ Error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error al guardar: {str(e)}")


def _render_existing_routes(distance_repo, clients):
    """Muestra y permite editar las rutas existentes."""
    st.subheader("Rutas Configuradas")
    
    # Filtro por cliente
    col1, col2 = st.columns([2, 1])
    with col1:
        client_filter_options = {"Todos los clientes": None}
        client_filter_options.update({f"{c['name']}": c['id'] for c in clients})
        
        selected_filter_client = st.selectbox(
            "Filtrar por Cliente",
            options=list(client_filter_options.keys()),
            key="filter_client_existing"
        )
        filter_client_id = client_filter_options[selected_filter_client]
    
    with col2:
        route_type_filter = st.selectbox(
            "Tipo de Ruta",
            options=["Todas", "Solo Enlaces", "Solo Destinos Finales"],
            key="filter_route_type"
        )
    
    # Cargar rutas con nombres
    routes = distance_repo.get_all_routes_with_names(client_id=filter_client_id)
    
    # Filtrar por tipo de ruta
    if route_type_filter == "Solo Enlaces":
        routes = [r for r in routes if r.get('is_link_segment')]
    elif route_type_filter == "Solo Destinos Finales":
        routes = [r for r in routes if not r.get('is_link_segment')]
    
    if not routes:
        st.info("📊 No hay rutas configuradas que cumplan con los filtros seleccionados.")
        return
    
    # Mostrar resumen
    st.markdown(f"**{len(routes)} rutas encontradas**")
    
    # Edición de rutas
    if 'editing_route_id' not in st.session_state:
        st.session_state.editing_route_id = None
    
    for route in routes:
        route_id = route['id']
        origin_name = route.get('origin_name', f"Planta {route['origin_facility_id']}")
        dest_name = route.get('destination_name', f"Destino {route['destination_id']}")
        client_name = route.get('client_name', 'Sin cliente')
        dest_type = route.get('destination_type', 'SITE')
        distance = route.get('distance_km', 0)
        is_link = route.get('is_link_segment', False)
        
        # Badge de tipo
        type_badge = "🔗 Enlace" if is_link else "🏁 Final"
        dest_type_label = {
            'TREATMENT_PLANT': '🏭 Planta Tratamiento',
            'FACILITY': '🏢 Planta Cliente',
            'SITE': '🌾 Campo'
        }.get(dest_type, dest_type)
        
        with st.container():
            col_info, col_distance, col_actions = st.columns([4, 2, 2])
            
            with col_info:
                st.markdown(f"**{origin_name}** → **{dest_name}**")
                st.caption(f"Cliente: {client_name} | {dest_type_label} | {type_badge}")
            
            with col_distance:
                if st.session_state.editing_route_id == route_id:
                    new_distance = st.number_input(
                        "Km",
                        min_value=0.1,
                        max_value=2000.0,
                        value=float(distance),
                        step=0.1,
                        format="%.1f",
                        key=f"edit_distance_{route_id}"
                    )
                else:
                    st.markdown(f"### {distance:.1f} km")
            
            with col_actions:
                if st.session_state.editing_route_id == route_id:
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾", key=f"save_{route_id}", help="Guardar"):
                            if distance_repo.update(route_id, distance_km=new_distance):
                                st.session_state.finance_success_msg = f"✅ Distancia actualizada a {new_distance:.1f} km"
                                st.session_state.editing_route_id = None
                                st.rerun()
                            else:
                                st.session_state.finance_error_msg = "❌ Error al actualizar"
                                st.rerun()
                    with col_cancel:
                        if st.button("❌", key=f"cancel_{route_id}", help="Cancelar"):
                            st.session_state.editing_route_id = None
                            st.rerun()
                else:
                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        if st.button("✏️", key=f"edit_{route_id}", help="Editar"):
                            st.session_state.editing_route_id = route_id
                            st.rerun()
                    with col_delete:
                        if st.button("🗑️", key=f"delete_{route_id}", help="Eliminar"):
                            if distance_repo.delete(route_id):
                                st.session_state.finance_success_msg = f"✅ Ruta eliminada"
                                st.rerun()
                            else:
                                st.session_state.finance_error_msg = "❌ Error al eliminar"
                                st.rerun()
            
            st.divider()


# ==============================================================================
# TAB 3: TARIFFS
# ==============================================================================

def _render_tariffs_tab(client_service, contractor_service):
    """Renderiza el tab de Tarifarios con sub-tabs para Contratistas y Clientes.
    
    Args:
        client_service: Servicio de clientes
        contractor_service: Servicio de contratistas
    """
    st.header("💲 Tarifarios")
    
    tab_contractors, tab_clients = st.tabs([
        "🚛 Contratistas (Costos)",
        "🏢 Clientes (Ingresos)"
    ])
    
    with tab_contractors:
        _render_contractor_tariffs(contractor_service)
    
    with tab_clients:
        _render_client_tariffs(client_service)


def _render_contractor_tariffs(contractor_service):
    """Sub-tab de tarifas de contratistas (costos de transporte).
    
    Args:
        contractor_service: Servicio de contratistas
    """
    st.subheader("🚛 Tarifas de Contratistas")
    st.markdown("Configure las tarifas de costo con transportistas, incluyendo el precio base de combustible para ajustes polinómicos.")
    
    # Cargar contratistas reales
    contractors = _load_contractors(contractor_service)
    vehicle_types = ["BATEA", "AMPLIROLL_SIMPLE", "AMPLIROLL_CARRO"]
    
    if not contractors:
        st.warning("⚠️ No hay contratistas registrados. Debe crear primero los contratistas en la sección de Transporte.")
        return
    
    with st.form("contractor_tariff_form"):
        contractor_opts = {f"{c['name']} ({c['rut']})" if c['rut'] else c['name']: c['id'] for c in contractors}
        selected_contractor = st.selectbox("Contratista *", list(contractor_opts.keys()))
        
        col1, col2 = st.columns(2)
        
        with col1:
            vehicle_type = st.selectbox(
                "Tipo de Vehículo *",
                options=vehicle_types,
                help="BATEA: Camión batea abierto | AMPLIROLL: Camión porta-contenedor"
            )
            
            base_rate_uf = st.number_input(
                "Tarifa Base (UF/ton-km) *",
                min_value=0.0001,
                max_value=10.0,
                value=0.0027,
                step=0.0001,
                format="%.4f",
                help="Precio base en UF por tonelada-kilómetro"
            )
        
        with col2:
            min_weight = st.number_input(
                "Peso Mínimo Garantizado (ton) *",
                min_value=0.0,
                max_value=50.0,
                value=15.0 if vehicle_type == "BATEA" else 7.0,
                step=0.5,
                help="Peso mínimo que se cobrará aunque el viaje lleve menos carga"
            )
            
            base_fuel_price = st.number_input(
                "Precio Petróleo Base ($/litro) *",
                min_value=0.01,
                max_value=10000.0,
                value=1200.0,
                step=10.0,
                help="Precio de referencia del contrato para el polinomio de ajuste"
            )
        
        submitted = st.form_submit_button("💾 Guardar Tarifa Contratista", type="primary")
        
        if submitted:
            if base_rate_uf <= 0 or base_fuel_price <= 0:
                st.session_state.finance_error_msg = "❌ Tarifa Base y Precio Petróleo Base deben ser > 0"
                st.rerun()
            
            if min_weight < 0:
                st.session_state.finance_error_msg = "❌ Peso Mínimo no puede ser negativo"
                st.rerun()
            
            contractor_id = contractor_opts[selected_contractor]
            st.session_state.contractor_tariffs_data.append({
                'contractor_name': selected_contractor,
                'contractor_id': contractor_id,
                'vehicle_type': vehicle_type,
                'base_rate_uf': base_rate_uf,
                'min_weight': min_weight,
                'base_fuel_price': base_fuel_price,
                'created_at': datetime.now()
            })
            
            st.session_state.finance_success_msg = f"✅ Tarifa guardada para {selected_contractor} ({vehicle_type})"
            st.rerun()
    
    # Tabla de tarifas
    st.subheader("Tarifas de Contratistas Registradas")
    if st.session_state.contractor_tariffs_data:
        display_data = [{
            'Contratista': t['contractor_name'],
            'Tipo Vehículo': t['vehicle_type'],
            'Tarifa Base (UF/ton-km)': f"UF {t['base_rate_uf']:.4f}",
            'Peso Mín. (ton)': f"{t['min_weight']:.1f}",
            'Precio Petróleo Base ($/L)': f"${t['base_fuel_price']:.0f}",
            'Registrado': t['created_at'].strftime('%Y-%m-%d')
        } for t in st.session_state.contractor_tariffs_data]
        
        st.dataframe(display_data, hide_index=True, use_container_width=True)
    else:
        st.info("📋 No hay tarifas de contratistas registradas.")


def _render_client_tariffs(client_service):
    """Sub-tab de tarifas de clientes (ingresos en UF).
    
    Args:
        client_service: Servicio de clientes
    """
    st.subheader("🏢 Tarifas de Clientes")
    st.markdown("Configure las tarifas de facturación a clientes en UF por concepto.")
    
    # Cargar clientes reales
    clients = _load_clients(client_service)
    concepts = ["TRANSPORTE", "DISPOSICION", "TRATAMIENTO"]
    
    if not clients:
        st.warning("⚠️ No hay clientes registrados. Debe crear primero los clientes en la sección de Empresas.")
        return
    
    with st.form("client_tariff_form"):
        client_opts = {f"{c['name']} ({c['rut']})" if c['rut'] else c['name']: c['id'] for c in clients}
        selected_client = st.selectbox("Cliente *", list(client_opts.keys()))
        
        col1, col2 = st.columns(2)
        
        with col1:
            concept = st.selectbox(
                "Concepto de Cobro *",
                options=concepts,
                help="TRANSPORTE: Flete | DISPOSICION: Riego/Aplicación | TRATAMIENTO: Procesamiento en planta"
            )
            
            rate_uf = st.number_input(
                "Tarifa (UF/ton) *",
                min_value=0.01,
                max_value=100.0,
                value=0.5,
                step=0.05,
                help="Tarifa en UF por tonelada"
            )
        
        with col2:
            min_weight = st.number_input(
                "Peso Mínimo Garantizado (ton)",
                min_value=0.0,
                max_value=50.0,
                value=0.0,
                step=0.5,
                help="Peso mínimo que se facturará (0 = sin mínimo)"
            )
            
            valid_from = st.date_input(
                "Vigencia Desde *",
                value=date.today(),
                help="Fecha de inicio de vigencia de esta tarifa"
            )
        
        submitted = st.form_submit_button("💾 Guardar Tarifa Cliente", type="primary")
        
        if submitted:
            if rate_uf <= 0:
                st.session_state.finance_error_msg = "❌ La tarifa en UF debe ser > 0"
                st.rerun()
            
            if min_weight < 0:
                st.session_state.finance_error_msg = "❌ Peso Mínimo no puede ser negativo"
                st.rerun()
            
            client_id = client_opts[selected_client]
            st.session_state.client_tariffs_data.append({
                'client_name': selected_client,
                'client_id': client_id,
                'concept': concept,
                'rate_uf': rate_uf,
                'min_weight': min_weight,
                'valid_from': valid_from,
                'created_at': datetime.now()
            })
            
            st.session_state.finance_success_msg = f"✅ Tarifa guardada para {selected_client} ({concept})"
            st.rerun()
    
    # Tabla de tarifas
    st.subheader("Tarifas de Clientes Registradas")
    if st.session_state.client_tariffs_data:
        display_data = [{
            'Cliente': t['client_name'],
            'Concepto': t['concept'],
            'Tarifa (UF/ton)': f"{t['rate_uf']:.3f} UF",
            'Peso Mín. (ton)': f"{t['min_weight']:.1f}",
            'Vigencia Desde': t['valid_from'].strftime('%Y-%m-%d'),
            'Registrado': t['created_at'].strftime('%Y-%m-%d')
        } for t in st.session_state.client_tariffs_data]
        
        st.dataframe(display_data, hide_index=True, use_container_width=True)
    else:
        st.info("📋 No hay tarifas de clientes registradas.")
