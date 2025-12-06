"""
Vista de Gestión de Parámetros Financieros del ERP.

Este módulo contiene la interfaz gráfica para configurar los parámetros que
alimentan el motor de cálculo de tarifas (Fase 2):
- Indicadores económicos mensuales (UF, Precio Petróleo)
- Matriz de distancias (Planta→Planta, Planta→Campo)
- Tarifarios de contratistas (costos) y clientes (ingresos)

Autor: Senior Frontend Engineer - ERP Team
"""

import streamlit as st
from datetime import datetime, date
from typing import List, Dict, Optional
from dataclasses import dataclass

# ==============================================================================
# MOCK DATA - Temporary data for visual testing
# ==============================================================================

@dataclass
class MockFacility:
    """Mock Facility (Plant) for testing."""
    id: int
    name: str
    type: str  # 'TREATMENT' or 'TRANSFER'

@dataclass
class MockSite:
    """Mock Site (Agricultural field) for testing."""
    id: int
    name: str
    client_name: str

@dataclass
class MockContractor:
    """Mock Contractor for testing."""
    id: int
    name: str
    rut: str

@dataclass
class MockClient:
    """Mock Client for testing."""
    id: int
    name: str
    rut: str


def _get_mock_facilities() -> List[MockFacility]:
    """Retorna lista de plantas mockeadas."""
    return [
        MockFacility(1, "Planta Tratamiento Maipú", "TREATMENT"),
        MockFacility(2, "Planta Tratamiento La Pintana", "TREATMENT"),
        MockFacility(3, "Estación de Transferencia Quilicura", "TRANSFER"),
        MockFacility(4, "Planta Tratamiento San Bernardo", "TREATMENT"),
    ]


def _get_mock_sites() -> List[MockSite]:
    """Retorna lista de campos/sitios mockeados."""
    return [
        MockSite(1, "Fundo Los Olivos - Parcela A", "AgroEmpresa SpA"),
        MockSite(2, "Huerto Santa Rosa", "Fruticola del Valle"),
        MockSite(3, "Campo El Roble", "AgroEmpresa SpA"),
        MockSite(4, "Predio San José", "Viñedos del Sur"),
        MockSite(5, "Fundo Las Palmas", "Hacienda Central"),
    ]


def _get_mock_contractors() -> List[MockContractor]:
    """Retorna lista de contratistas mockeados."""
    return [
        MockContractor(1, "Transportes González Ltda.", "76.123.456-7"),
        MockContractor(2, "Logística del Sur SA", "77.987.654-3"),
        MockContractor(3, "Camiones Pérez y Cía", "76.555.444-2"),
    ]


def _get_mock_clients() -> List[MockClient]:
    """Retorna lista de clientes mockeados."""
    return [
        MockClient(1, "AgroEmpresa SpA", "78.111.222-3"),
        MockClient(2, "Fruticola del Valle", "79.333.444-5"),
        MockClient(3, "Viñedos del Sur", "77.666.777-8"),
        MockClient(4, "Hacienda Central", "76.888.999-0"),
    ]


# ==============================================================================
# MAIN RENDER FUNCTION
# ==============================================================================

def render(finance_service=None, facility_service=None, site_service=None, 
           contractor_service=None, client_service=None):
    """
    Vista principal de Parámetros Financieros con inyección de dependencias.
    
    Args:
        finance_service: Servicio de finanzas (Future implementation)
        facility_service: Servicio de plantas (Future implementation)
        site_service: Servicio de sitios/campos (Future implementation)
        contractor_service: Servicio de contratistas (Future implementation)
        client_service: Servicio de clientes (Future implementation)
    
    Note:
        Esta versión inicial usa datos mockeados. Los servicios reales se
        integrarán cuando estén disponibles en container.py
    """
    st.title("💰 Parámetros Financieros")
    st.markdown("**Configuración de datos maestros para el motor de cálculo de tarifas**")
    
    # Inicializar estado de la sesión si no existe
    if 'finance_success_msg' not in st.session_state:
        st.session_state.finance_success_msg = None
    if 'finance_error_msg' not in st.session_state:
        st.session_state.finance_error_msg = None
    if 'economic_indicators_data' not in st.session_state:
        st.session_state.economic_indicators_data = []
    if 'distance_matrix_data' not in st.session_state:
        st.session_state.distance_matrix_data = []
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
        _render_distance_matrix_tab()
    
    with tab3:
        _render_tariffs_tab()


# ==============================================================================
# TAB 1: ECONOMIC INDICATORS
# ==============================================================================

def _render_economic_indicators_tab():
    """Renderiza el tab de Indicadores Económicos (UF y Precio Petróleo)."""
    st.header("📈 Indicadores Económicos Mensuales")
    st.markdown("""
    Configure los valores mensuales de UF (al día 18) y Precio de Petróleo para el 
    ajuste polinómico de tarifas y facturación.
    """)
    
    # Formulario de ingreso
    st.subheader("Ingresar Nuevo Indicador")
    with st.form("economic_indicators_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            year = st.selectbox(
                "Año",
                options=list(range(2024, 2027)),
                index=1  # Default 2025
            )
            
            uf_value = st.number_input(
                "Valor UF (al día 18) *",
                min_value=0.01,
                max_value=100000.0,
                value=37500.0,
                step=100.0,
                help="Valor de la UF en CLP al día 18 del mes"
            )
        
        with col2:
            month = st.selectbox(
                "Mes",
                options=list(range(1, 13)),
                format_func=lambda x: datetime(2025, x, 1).strftime('%B'),
                index=11  # Default Diciembre
            )
            
            fuel_price = st.number_input(
                "Precio Petróleo Mensual (CLP/litro) *",
                min_value=0.01,
                max_value=10000.0,
                value=1250.0,
                step=10.0,
                help="Precio promedio mensual del petróleo/combustible"
            )
        
        submitted = st.form_submit_button("💾 Guardar Indicadores", type="primary")
        
        if submitted:
            # Validaciones
            if uf_value <= 0 or fuel_price <= 0:
                st.session_state.finance_error_msg = "❌ Los valores deben ser positivos (> 0)"
                st.rerun()
            
            # Verificar duplicados
            existing = [
                item for item in st.session_state.economic_indicators_data
                if item['year'] == year and item['month'] == month
            ]
            
            if existing:
                st.warning(f"⚠️ Ya existe un registro para {datetime(year, month, 1).strftime('%B %Y')}. ¿Desea sobrescribir?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Sí, sobrescribir"):
                        # Eliminar registro existente
                        st.session_state.economic_indicators_data = [
                            item for item in st.session_state.economic_indicators_data
                            if not (item['year'] == year and item['month'] == month)
                        ]
                        # Agregar nuevo
                        st.session_state.economic_indicators_data.append({
                            'year': year,
                            'month': month,
                            'uf_value': uf_value,
                            'fuel_price': fuel_price,
                            'created_at': datetime.now()
                        })
                        st.session_state.finance_success_msg = f"✅ Indicadores actualizados para {datetime(year, month, 1).strftime('%B %Y')}"
                        st.rerun()
                with col_no:
                    if st.button("❌ Cancelar"):
                        st.rerun()
            else:
                # Guardar nuevo registro
                st.session_state.economic_indicators_data.append({
                    'year': year,
                    'month': month,
                    'uf_value': uf_value,
                    'fuel_price': fuel_price,
                    'created_at': datetime.now()
                })
                st.session_state.finance_success_msg = f"✅ Indicadores guardados para {datetime(year, month, 1).strftime('%B %Y')}"
                st.rerun()
    
    # Tabla histórica
    st.subheader("Historial de Indicadores")
    if st.session_state.economic_indicators_data:
        # Ordenar descendente por fecha
        sorted_data = sorted(
            st.session_state.economic_indicators_data,
            key=lambda x: (x['year'], x['month']),
            reverse=True
        )
        
        display_data = [{
            'Año': item['year'],
            'Mes': datetime(item['year'], item['month'], 1).strftime('%B'),
            'Valor UF (CLP)': f"${item['uf_value']:,.2f}",
            'Precio Petróleo (CLP/L)': f"${item['fuel_price']:,.2f}",
            'Registrado': item['created_at'].strftime('%Y-%m-%d %H:%M')
        } for item in sorted_data]
        
        st.dataframe(display_data, hide_index=True, use_container_width=True)
    else:
        st.info("📊 No hay indicadores registrados aún. Utilice el formulario superior para agregar.")


# ==============================================================================
# TAB 2: DISTANCE MATRIX
# ==============================================================================

def _render_distance_matrix_tab():
    """Renderiza el tab de Matriz de Distancias (polimórfico: Planta→Planta o Planta→Campo)."""
    st.header("🛣️ Matriz de Distancias")
    st.markdown("""
    Configure las distancias para viajes directos (Planta→Campo) y tramos de enlace (Planta→Planta→Campo).
    """)
    
    # Obtener datos mockeados
    facilities = _get_mock_facilities()
    sites = _get_mock_sites()
    
    st.subheader("Configurar Nueva Ruta")
    with st.form("distance_matrix_form"):
        # Origen (siempre una Planta)
        origin_options = {f"{f.name} ({f.type})": f.id for f in facilities}
        selected_origin = st.selectbox(
            "Origen (Planta) *",
            options=list(origin_options.keys())
        )
        
        # Tipo de destino (Radio button)
        dest_type = st.radio(
            "Tipo de Destino *",
            options=["Planta (Enlace)", "Campo (Destino Final)"],
            horizontal=True,
            help="Seleccione si el destino es otra planta (enlace) o un campo (destino final)"
        )
        
        # Destino dinámico basado en tipo
        if dest_type == "Planta (Enlace)":
            dest_options = {f"{f.name} ({f.type})": ('facility', f.id) for f in facilities}
            is_link = True
        else:
            dest_options = {f"{s.name} - {s.client_name}": ('site', s.id) for s in sites}
            is_link = False
        
        selected_dest = st.selectbox(
            f"Destino ({dest_type.split()[0]}) *",
            options=list(dest_options.keys())
        )
        
        # Distancia
        distance_km = st.number_input(
            "Distancia (Km) *",
            min_value=0.1,
            max_value=1000.0,
            value=45.0,
            step=0.5,
            help="Distancia en kilómetros del tramo"
        )
        
        # Checkbox de enlace (auto-marcado si es Planta)
        is_segment_link = st.checkbox(
            "Es Tramo de Enlace",
            value=is_link,
            disabled=True,
            help="Auto-detectado: marcado si el destino es otra planta"
        )
        
        submitted = st.form_submit_button("💾 Guardar Ruta", type="primary")
        
        if submitted:
            if distance_km <= 0:
                st.session_state.finance_error_msg = "❌ La distancia debe ser positiva (> 0)"
                st.rerun()
            
            # Guardar ruta
            origin_id = origin_options[selected_origin]
            dest_type_str, dest_id = dest_options[selected_dest]
            
            st.session_state.distance_matrix_data.append({
                'origin_name': selected_origin,
                'origin_id': origin_id,
                'dest_name': selected_dest,
                'dest_id': dest_id,
                'dest_type': dest_type_str,
                'distance_km': distance_km,
                'is_segment_link': is_segment_link,
                'created_at': datetime.now()
            })
            
            st.session_state.finance_success_msg = f"✅ Ruta guardada: {selected_origin} → {selected_dest} ({distance_km} km)"
            st.rerun()
    
    # Tabla de rutas configuradas
    st.subheader("Rutas Configuradas")
    if st.session_state.distance_matrix_data:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            filter_type = st.selectbox(
                "Filtrar por tipo",
                options=["Todas", "Solo Enlaces (Planta→Planta)", "Solo Destinos Finales (Planta→Campo)"]
            )
        
        # Aplicar filtros
        filtered_data = st.session_state.distance_matrix_data
        if filter_type == "Solo Enlaces (Planta→Planta)":
            filtered_data = [r for r in filtered_data if r['is_segment_link']]
        elif filter_type == "Solo Destinos Finales (Planta→Campo)":
            filtered_data = [r for r in filtered_data if not r['is_segment_link']]
        
        if filtered_data:
            display_data = [{
                'Origen': r['origin_name'],
                'Destino': r['dest_name'],
                'Tipo Destino': 'Planta (Enlace)' if r['is_segment_link'] else 'Campo',
                'Distancia (km)': f"{r['distance_km']:.1f}",
                'Registrado': r['created_at'].strftime('%Y-%m-%d')
            } for r in filtered_data]
            
            st.dataframe(display_data, hide_index=True, use_container_width=True)
        else:
            st.info("📊 No hay rutas que cumplan con el filtro seleccionado.")
    else:
        st.info("🛣️ No hay rutas configuradas aún. Utilice el formulario superior para agregar.")


# ==============================================================================
# TAB 3: TARIFFS
# ==============================================================================

def _render_tariffs_tab():
    """Renderiza el tab de Tarifarios con sub-tabs para Contratistas y Clientes."""
    st.header("💲 Tarifarios")
    
    # Sub-tabs
    subtab1, subtab2 = st.tabs([
        "🚛 Contratistas (Costos)",
        "🏢 Clientes (Ingresos)"
    ])
    
    with subtab1:
        _render_contractor_tariffs()
    
    with subtab2:
        _render_client_tariffs()


def _render_contractor_tariffs():
    """Sub-tab de tarifas de contratistas (costos de transporte)."""
    st.subheader("🚛 Tarifas de Contratistas")
    st.markdown("Configure las tarifas de costo con transportistas, incluyendo el precio base de combustible para ajustes polinómicos.")
    
    contractors = _get_mock_contractors()
    vehicle_types = ["BATEA", "AMPLIROLL_SIMPLE", "AMPLIROLL_CARRO"]
    
    with st.form("contractor_tariff_form"):
        # Selector de contratista
        contractor_opts = {f"{c.name} ({c.rut})": c.id for c in contractors}
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
                value=0.0027,  # Equivalente a ~100 CLP @ UF 37000
                step=0.0001,
                format="%.4f",
                help="Precio base en UF por tonelada-kilómetro (la fórmula polinómica ajustará este valor según combustible)"
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
                help="⚠️ CRÍTICO: Precio de referencia del contrato en PESOS para el polinomio de ajuste (el factor es adimensional)"
            )
        
        submitted = st.form_submit_button("💾 Guardar Tarifa Contratista", type="primary")
        
        if submitted:
            # Validaciones
            if base_rate_uf <= 0 or base_fuel_price <= 0:
                st.session_state.finance_error_msg = "❌ Tarifa Base y Precio Petróleo Base deben ser > 0"
                st.rerun()
            
            if min_weight < 0:
                st.session_state.finance_error_msg = "❌ Peso Mínimo no puede ser negativo"
                st.rerun()
            
            # Guardar tarifa
            contractor_id = contractor_opts[selected_contractor]
            st.session_state.contractor_tariffs_data.append({
                'contractor_name': selected_contractor,
                'contractor_id': contractor_id,
                'vehicle_type': vehicle_type,
                'base_rate_uf': base_rate_uf,  # *** CHANGED ***
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
            'Tarifa Base (UF/ton-km)': f"UF {t['base_rate_uf']:.4f}",  # *** CHANGED ***
            'Peso Mín. (ton)': f"{t['min_weight']:.1f}",
            'Precio Petróleo Base ($/L)': f"${t['base_fuel_price']:.0f}",
            'Registrado': t['created_at'].strftime('%Y-%m-%d')
        } for t in st.session_state.contractor_tariffs_data]
        
        st.dataframe(display_data, hide_index=True, use_container_width=True)
    else:
        st.info("📋 No hay tarifas de contratistas registradas.")


def _render_client_tariffs():
    """Sub-tab de tarifas de clientes (ingresos en UF)."""
    st.subheader("🏢 Tarifas de Clientes")
    st.markdown("Configure las tarifas de facturación a clientes en UF por concepto.")
    
    clients = _get_mock_clients()
    concepts = ["TRANSPORTE", "DISPOSICION", "TRATAMIENTO"]
    
    with st.form("client_tariff_form"):
        # Selector de cliente
        client_opts = {f"{c.name} ({c.rut})": c.id for c in clients}
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
            # Validaciones
            if rate_uf <= 0:
                st.session_state.finance_error_msg = "❌ La tarifa en UF debe ser > 0"
                st.rerun()
            
            if min_weight < 0:
                st.session_state.finance_error_msg = "❌ Peso Mínimo no puede ser negativo"
                st.rerun()
            
            # Guardar tarifa
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
