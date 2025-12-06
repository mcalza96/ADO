"""
Portal Financiero - Estados de Pago.

Vista para visualizar, calcular y exportar estados de pago por entidad.
Cada pestaña tiene su propio flujo independiente de cálculo.

Regla de oro: "Cálculo en UF, Pago en Pesos".
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO


# Constantes
MONTH_NAMES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


def financial_portal_page(container):
    """
    Renderiza el Portal de Estados de Pago.
    
    Estructura independiente por pestaña:
    - Tab Clientes: Estado de pago por cliente (lo que cobramos)
    - Tab Transportistas: Estado de pago por transportista (lo que pagamos)
    - Tab Disposición: Estado de pago por contratista de disposición (lo que pagamos)
    - Tab Otros: Gastos genéricos (placeholder)
    
    Args:
        container: SimpleNamespace con todos los servicios inyectados
    """
    # Extraer servicios del container
    financial_reporting_service = container.financial_reporting_service
    contractor_service = container.contractor_service
    client_service = container.client_service
    
    st.header("Estados de Pago")
    st.markdown("**Cálculo en UF, Pago en Pesos** | Ciclo: 19 mes anterior → 18 mes actual")
    
    # ============================================
    # Sistema de Pestañas - Cada una independiente
    # ============================================
    tab_clientes, tab_transportistas, tab_disposicion, tab_otros = st.tabs([
        "Clientes", 
        "Transportistas", 
        "Disposición",
        "Otros Proveedores"
    ])
    
    # --------------------------------------------
    # Tab 1: Clientes (Ingresos - lo que cobramos)
    # --------------------------------------------
    with tab_clientes:
        _render_client_settlement_tab(financial_reporting_service, client_service)
    
    # --------------------------------------------
    # Tab 2: Transportistas (Costos - lo que pagamos)
    # --------------------------------------------
    with tab_transportistas:
        _render_transport_settlement_tab(financial_reporting_service, contractor_service)
    
    # --------------------------------------------
    # Tab 3: Disposición (Costos - lo que pagamos)
    # --------------------------------------------
    with tab_disposicion:
        _render_disposal_settlement_tab(financial_reporting_service, contractor_service)
    
    # --------------------------------------------
    # Tab 4: Otros Proveedores (Gastos genéricos)
    # --------------------------------------------
    with tab_otros:
        _render_otros_settlement_tab(contractor_service)


def _render_period_selector(key_prefix: str):
    """
    Renderiza selector de periodo reutilizable.
    
    Returns:
        tuple: (year, month, calculate_btn)
    """
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        year = st.selectbox(
            "Año",
            options=list(range(2024, 2031)),
            index=list(range(2024, 2031)).index(datetime.now().year) if datetime.now().year >= 2024 else 0,
            key=f"{key_prefix}_year"
        )
    
    with col2:
        month = st.selectbox(
            "Mes",
            options=list(range(1, 13)),
            format_func=lambda x: MONTH_NAMES[x - 1],
            index=datetime.now().month - 1,
            key=f"{key_prefix}_month"
        )
    
    with col3:
        st.write("")  # Spacer
        calculate_btn = st.button("Calcular", type="primary", key=f"{key_prefix}_calc", use_container_width=True)
    
    return year, month, calculate_btn


def _render_economic_indicators(cycle_info: dict):
    """Renderiza indicadores económicos del ciclo (proforma)."""
    uf_value = cycle_info.get('uf_value', 0)
    fuel_price = cycle_info.get('fuel_price', 0)
    start_date = cycle_info.get('start_date', 'N/A')
    end_date = cycle_info.get('end_date', 'N/A')
    proforma_code = cycle_info.get('proforma_code', 'N/A')
    is_closed = cycle_info.get('is_closed', False)
    
    # Mostrar código de proforma en el encabezado
    status_emoji = "🔒" if is_closed else "📝"
    status_text = "Cerrada" if is_closed else "Abierta"
    st.markdown(f"**Proforma:** `{proforma_code}` {status_emoji} {status_text}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("UF", f"$ {uf_value:,.0f}".replace(",", "."))
    with col2:
        st.metric("Diesel", f"$ {fuel_price:,.0f}/L".replace(",", "."))
    with col3:
        st.metric("Desde", start_date)
    with col4:
        st.metric("Hasta", end_date)
    
    return uf_value


# ============================================
# TAB: CLIENTES
# ============================================
def _render_client_settlement_tab(financial_reporting_service, client_service):
    """
    Renderiza la pestaña de estados de pago para clientes.
    Vista independiente con su propio selector de cliente, periodo y cálculo.
    """
    st.subheader("Estado de Pago - Clientes")
    st.info("**Ingresos** - Lo que cobramos a los clientes por los servicios prestados.")
    
    # Obtener clientes configurados
    clients = client_service.get_all()
    
    if not clients:
        st.warning("⚠️ No hay clientes configurados.")
        st.caption("Configure clientes en: **Configuración → Empresas → Clientes**")
        return
    
    # Selector de cliente
    client_options = {"Todos los Clientes": None}
    client_options.update({c.name: c.id for c in clients})
    
    selected_client_name = st.selectbox(
        "Seleccione Cliente",
        options=list(client_options.keys()),
        key="client_settlement_selector"
    )
    selected_client_id = client_options[selected_client_name]
    
    st.markdown("---")
    
    # Selector de periodo y botón calcular
    year, month, calculate_btn = _render_period_selector("client")
    
    # Estado de sesión para este tab
    session_key = f"client_settlement_{year}_{month}"
    
    if calculate_btn:
        if session_key in st.session_state:
            del st.session_state[session_key]
    
    if session_key not in st.session_state:
        if not calculate_btn:
            st.info("👆 Seleccione cliente y periodo, luego haga clic en **Calcular**.")
            return
        
        with st.spinner(f"Calculando estado de pago para {MONTH_NAMES[month - 1]} {year}..."):
            try:
                settlement = financial_reporting_service.get_monthly_settlement(year, month)
                st.session_state[session_key] = settlement
            except ValueError as e:
                st.error(f"❌ Error: {str(e)}")
                st.caption("Configure la proforma en: **Configuración → Parámetros Financieros → Maestro de Proformas**")
                return
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                return
    
    settlement = st.session_state.get(session_key)
    if not settlement:
        return
    
    # Mostrar indicadores económicos
    st.markdown("---")
    uf_value = _render_economic_indicators(settlement.cycle_info)
    
    # Filtrar por cliente seleccionado
    client_df = settlement.client_df
    
    if client_df.empty:
        st.info("No hay movimientos para este periodo.")
        return
    
    if selected_client_id:
        # Filtrar por cliente específico
        if 'client_id' in client_df.columns:
            client_df = client_df[client_df['client_id'] == selected_client_id]
        elif 'client_name' in client_df.columns:
            client_df = client_df[client_df['client_name'] == selected_client_name]
    
    if client_df.empty:
        st.info(f"No hay movimientos para **{selected_client_name}** en este periodo.")
        return
    
    # Calcular total
    total_uf = client_df['subtotal_uf'].sum()
    
    st.markdown("---")
    st.metric("Total a Facturar", f"{total_uf:,.2f} UF = $ {total_uf * uf_value:,.0f} CLP".replace(",", "."))
    
    # Mostrar detalle
    _display_client_detail(client_df, uf_value)
    
    # Exportar
    st.markdown("---")
    _render_export_button(client_df, f"Estado_Pago_Cliente_{selected_client_name}_{year}_{month:02d}.xlsx", "client")


def _display_client_detail(client_df, uf_value):
    """Muestra el detalle de movimientos del cliente."""
    # Pivotear para tener conceptos como columnas
    if 'concept' in client_df.columns:
        pivot_df = client_df.pivot_table(
            index=['load_id', 'manifest_number', 'client_name', 'date', 'weight'],
            columns='concept',
            values='subtotal_uf',
            fill_value=0.0
        ).reset_index()
        
        display_df = pivot_df.copy()
        display_df.columns.name = None
        
        # Calcular total por fila
        concept_cols = [col for col in display_df.columns if col in ['TRANSPORTE', 'DISPOSICION', 'TRATAMIENTO']]
        if concept_cols:
            display_df['Total (UF)'] = display_df[concept_cols].sum(axis=1)
        
        display_df = display_df.rename(columns={
            'date': 'Fecha',
            'client_name': 'Cliente',
            'manifest_number': 'Manifiesto',
            'weight': 'Toneladas',
            'TRANSPORTE': 'Transp (UF)',
            'DISPOSICION': 'Disp (UF)',
            'TRATAMIENTO': 'Trat (UF)'
        })
    else:
        display_df = client_df.copy()
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)


# ============================================
# TAB: TRANSPORTISTAS
# ============================================
def _render_transport_settlement_tab(financial_reporting_service, contractor_service):
    """
    Renderiza la pestaña de estados de pago para transportistas.
    Muestra siempre la tabla de viajes, el botón Calcular muestra los totales.
    """
    st.subheader("Estado de Pago - Transportistas")
    st.info("**Costos** - Lo que pagamos a los transportistas por el servicio de transporte.")
    
    # Obtener proforma_repo desde el servicio
    proforma_repo = financial_reporting_service.proforma_repo
    
    if not proforma_repo:
        st.warning("⚠️ No hay proformas configuradas.")
        st.caption("Configure proformas en: **Configuración → Parámetros Financieros → Maestro de Proformas**")
        return
    
    # Obtener todas las proformas
    proformas = proforma_repo.get_all(include_closed=True)
    
    if not proformas:
        st.warning("⚠️ No hay proformas registradas.")
        st.caption("Configure proformas en: **Configuración → Parámetros Financieros → Maestro de Proformas**")
        return
    
    # Selector de proforma
    proforma_options = {p.proforma_code: p for p in proformas}
    
    selected_code = st.selectbox(
        "Seleccione Proforma",
        options=list(proforma_options.keys()),
        key="transport_proforma_selector",
        help="Seleccione la proforma para ver los viajes del período"
    )
    selected_proforma = proforma_options[selected_code]
    
    st.markdown("---")
    
    # Mostrar indicadores económicos de la proforma seleccionada
    _render_transport_proforma_info(selected_proforma)
    
    st.markdown("---")
    
    # Siempre cargar los viajes del período (sin cálculos de costo)
    trips_df = _get_transport_trips_for_period(financial_reporting_service, selected_proforma)
    
    if trips_df.empty:
        st.info("No hay viajes registrados para este período.")
        return
    
    # Mostrar tabla de viajes siempre
    st.markdown(f"**Viajes del período:** {len(trips_df)}")
    _display_transport_trips_table(trips_df)
    
    st.markdown("---")
    
    # Sección de cálculo de totales
    session_key = f"transport_totals_{selected_proforma.period_year}_{selected_proforma.period_month}"
    
    col1, col2 = st.columns([1, 4])
    with col1:
        calculate_btn = st.button("💰 Calcular Totales", type="primary", key="transport_calc_btn")
    
    if calculate_btn:
        if session_key in st.session_state:
            del st.session_state[session_key]
    
    # Calcular si se presionó el botón o ya hay datos en sesión
    if calculate_btn or session_key in st.session_state:
        if session_key not in st.session_state:
            with st.spinner(f"Calculando totales para {selected_code}..."):
                try:
                    settlement = financial_reporting_service.get_monthly_settlement(
                        selected_proforma.period_year, 
                        selected_proforma.period_month
                    )
                    st.session_state[session_key] = settlement
                except ValueError as e:
                    st.error(f"❌ Error: {str(e)}")
                    return
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    return
        
        settlement = st.session_state.get(session_key)
        if settlement and not settlement.contractor_df.empty:
            contractor_df = settlement.contractor_df
            total_uf = contractor_df['subtotal_uf'].sum()
            uf_value = selected_proforma.uf_value or 0
            
            # Mostrar totales
            st.markdown("### 💰 Resumen de Costos")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Viajes", f"{len(contractor_df)}")
            with col2:
                st.metric("Total UF", f"{total_uf:,.2f}".replace(",", "."))
            with col3:
                st.metric("Total CLP", f"$ {total_uf * uf_value:,.0f}".replace(",", "."))
            
            # Exportar
            st.markdown("---")
            _render_transport_export_button(contractor_df, selected_proforma)
    else:
        st.caption("👆 Presione **Calcular Totales** para ver el resumen de costos y exportar.")


def _get_transport_trips_for_period(financial_reporting_service, proforma):
    """
    Obtiene los viajes del período CON datos de cálculo para auditoría.
    
    Para viajes enlazados genera tramos separados:
    - Tramo 1: Planta A → Punto Enlace (tarifa AMPLIROLL)
    - Tramo 2: Punto Enlace → Destino Final (tarifa AMPLIROLL_CARRO)
    
    Convierte pesos de kg a toneladas.
    """
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    
    # Calcular fechas del ciclo
    year = proforma.period_year
    month = proforma.period_month
    cycle_end = datetime(year, month, 18)
    previous_month = datetime(year, month, 1) - relativedelta(months=1)
    cycle_start = datetime(previous_month.year, previous_month.month, 19)
    
    # Pesos mínimos garantizados por tipo de vehículo
    MIN_WEIGHTS = {
        'BATEA': 15.0,
        'AMPLIROLL': 7.0,
        'AMPLIROLL_SIMPLE': 7.0,
        'AMPLIROLL_CARRO': 7.0
    }
    
    # Query para obtener viajes con información completa
    # Incluye is_link_point de facility para detectar puntos de enlace
    query = """
        SELECT 
            l.id,
            l.manifest_code as manifest_number,
            l.scheduled_date as date,
            l.net_weight / 1000.0 as net_weight_tons,
            l.segment_type,
            l.trip_id,
            l.origin_facility_id,
            l.origin_treatment_plant_id,
            l.destination_site_id,
            l.destination_treatment_plant_id,
            v.license_plate as vehicle_plate,
            v.type as vehicle_type,
            f_origin.is_link_point as origin_is_link_point,
            COALESCE(f_origin.name, tp_origin.name, 'N/A') as origin_name,
            COALESCE(s.name, tp_dest.name, 'N/A') as destination_name
        FROM loads l
        LEFT JOIN vehicles v ON l.vehicle_id = v.id
        LEFT JOIN facilities f_origin ON l.origin_facility_id = f_origin.id
        LEFT JOIN treatment_plants tp_origin ON l.origin_treatment_plant_id = tp_origin.id
        LEFT JOIN sites s ON l.destination_site_id = s.id
        LEFT JOIN treatment_plants tp_dest ON l.destination_treatment_plant_id = tp_dest.id
        WHERE l.status IN ('ARRIVED', 'COMPLETED')
          AND l.scheduled_date BETWEEN ? AND ?
        ORDER BY l.scheduled_date ASC, l.trip_id ASC, l.segment_type ASC
    """
    
    try:
        with financial_reporting_service.load_repo.db_manager as conn:
            cursor = conn.cursor()
            cursor.execute(query, (cycle_start.isoformat(), cycle_end.isoformat()))
            rows = cursor.fetchall()
            
            if not rows:
                return pd.DataFrame()
            
            df = pd.DataFrame([dict(row) for row in rows])
            
            # === PROCESAR VIAJES ENLAZADOS ===
            # Agrupar por trip_id para identificar viajes enlazados
            processed_rows = []
            
            # Obtener tarifas desde proforma
            def get_tariff(vtype):
                if proforma:
                    tariff = proforma.get_tariff_for_vehicle_type(vtype)
                    if tariff:
                        return tariff
                defaults = {'BATEA': 0.001460, 'AMPLIROLL': 0.002962, 'AMPLIROLL_SIMPLE': 0.002962, 'AMPLIROLL_CARRO': 0.001793}
                return defaults.get(str(vtype).upper() if vtype else '', 0.0)
            
            tariff_ampliroll = get_tariff('AMPLIROLL')
            tariff_ampliroll_carro = get_tariff('AMPLIROLL_CARRO')
            
            # Separar viajes directos de enlazados
            linked_trips = df[df['trip_id'].notna() & (df['trip_id'] != '')].groupby('trip_id')
            direct_trips = df[df['trip_id'].isna() | (df['trip_id'] == '')]
            
            # Procesar viajes directos (sin cambios)
            for _, row in direct_trips.iterrows():
                row_dict = row.to_dict()
                row_dict['tariff_type'] = row_dict.get('vehicle_type', 'N/A')
                row_dict['tariff_uf'] = get_tariff(row_dict.get('vehicle_type'))
                row_dict['min_weight'] = MIN_WEIGHTS.get(str(row_dict.get('vehicle_type', '')).upper(), 7.0)
                row_dict['segment_desc'] = 'Directo'
                processed_rows.append(row_dict)
            
            # Procesar viajes enlazados (generar tramos)
            for trip_id, trip_loads in linked_trips:
                trip_list = trip_loads.to_dict('records')
                
                # Ordenar: primero la planta NO enlace, luego la enlace
                trip_list.sort(key=lambda x: x.get('origin_is_link_point', 0) or 0)
                
                if len(trip_list) >= 2:
                    # Carga de la planta origen (NO es punto de enlace)
                    primary_load = trip_list[0]
                    # Carga del punto de enlace
                    link_load = trip_list[1]
                    
                    # Calcular distancias
                    dist_to_link = 0.0  # Distancia: Planta Origen → Punto Enlace
                    dist_from_link = 0.0  # Distancia: Punto Enlace → Destino Final
                    
                    origin_fac = primary_load.get('origin_facility_id')
                    link_fac = link_load.get('origin_facility_id')
                    dest_tp = primary_load.get('destination_treatment_plant_id')
                    
                    if origin_fac and link_fac:
                        try:
                            # Distancia planta origen a punto enlace
                            dist_to_link = financial_reporting_service.distance_repo.get_route_distance(
                                int(origin_fac), int(link_fac), 'FACILITY'
                            ) or 0.0
                        except:
                            dist_to_link = 0.0
                    
                    if link_fac and dest_tp:
                        try:
                            # Distancia punto enlace a destino final
                            dist_from_link = financial_reporting_service.distance_repo.get_route_distance(
                                int(link_fac), int(dest_tp), 'TREATMENT_PLANT'
                            ) or 0.0
                        except:
                            dist_from_link = 0.0
                    
                    # TRAMO 1: Planta Origen → Punto de Enlace (tarifa AMPLIROLL)
                    # Solo peso de la carga primaria
                    tramo1 = primary_load.copy()
                    tramo1['segment_desc'] = 'T1: Origen→Enlace'
                    tramo1['tariff_type'] = 'AMPLIROLL'
                    tramo1['tariff_uf'] = tariff_ampliroll
                    tramo1['min_weight'] = MIN_WEIGHTS['AMPLIROLL']
                    tramo1['_dest_facility_id'] = link_load.get('origin_facility_id')
                    tramo1['_dest_type'] = 'FACILITY'
                    tramo1['link_point_name'] = link_load.get('origin_name', '')
                    tramo1['dist_to_link'] = dist_to_link
                    tramo1['_fixed_distance'] = dist_to_link  # Forzar esta distancia
                    tramo1['_original_origin'] = primary_load.get('origin_name', '')  # Mantener planta original
                    # Ocultar destino final para T1 - solo mostrar el enlace
                    tramo1['destination_name'] = '-'
                    processed_rows.append(tramo1)
                    
                    # TRAMO 2A: Punto Enlace → Destino (tarifa AMPLIROLL_CARRO)
                    # Carga primaria en el segundo tramo - MANTENER ORIGEN ORIGINAL
                    tramo2a = primary_load.copy()
                    tramo2a['segment_desc'] = 'T2: Enlace→Destino'
                    tramo2a['tariff_type'] = 'AMPLIROLL_CARRO'
                    tramo2a['tariff_uf'] = tariff_ampliroll_carro
                    tramo2a['min_weight'] = MIN_WEIGHTS['AMPLIROLL_CARRO']
                    # NO sobrescribir origin_name - mantener la planta original (Los Álamos)
                    tramo2a['_original_origin'] = primary_load.get('origin_name', '')
                    tramo2a['_segment_origin'] = link_load.get('origin_name', 'Enlace')  # Solo para referencia
                    tramo2a['link_point_name'] = '-'
                    tramo2a['dist_to_link'] = 0
                    tramo2a['_fixed_distance'] = dist_from_link  # Forzar esta distancia
                    processed_rows.append(tramo2a)
                    
                    # TRAMO 2B: Punto Enlace → Destino (tarifa AMPLIROLL_CARRO)
                    # Carga del punto de enlace
                    tramo2b = link_load.copy()
                    tramo2b['segment_desc'] = 'T2: Enlace→Destino'
                    tramo2b['tariff_type'] = 'AMPLIROLL_CARRO'
                    tramo2b['tariff_uf'] = tariff_ampliroll_carro
                    tramo2b['min_weight'] = MIN_WEIGHTS['AMPLIROLL_CARRO']
                    # origin_name de link_load ya es correcto (Cañete)
                    tramo2b['_original_origin'] = link_load.get('origin_name', '')
                    tramo2b['link_point_name'] = '-'
                    tramo2b['dist_to_link'] = 0
                    tramo2b['_fixed_distance'] = dist_from_link  # Forzar esta distancia
                    processed_rows.append(tramo2b)
                else:
                    # Solo una carga con trip_id (caso raro), procesar como directo
                    for load in trip_list:
                        load['tariff_type'] = load.get('vehicle_type', 'N/A')
                        load['tariff_uf'] = get_tariff(load.get('vehicle_type'))
                        load['min_weight'] = MIN_WEIGHTS.get(str(load.get('vehicle_type', '')).upper(), 7.0)
                        load['segment_desc'] = 'Directo'
                        processed_rows.append(load)
            
            # Convertir a DataFrame
            result_df = pd.DataFrame(processed_rows)
            
            if result_df.empty:
                return result_df
            
            # === CALCULAR DISTANCIAS Y SUBTOTALES ===
            
            # Peso facturable = max(peso_real, peso_mínimo)
            result_df['billable_weight'] = result_df.apply(
                lambda row: max(row.get('net_weight_tons') or 0, row.get('min_weight', 7.0)),
                axis=1
            )
            
            # Obtener distancias
            distances = []
            for idx, row in result_df.iterrows():
                row_dict = row.to_dict()
                
                # Si hay distancia fija (_fixed_distance), usarla directamente
                if '_fixed_distance' in row_dict and pd.notna(row_dict.get('_fixed_distance')):
                    distances.append(row_dict.get('_fixed_distance'))
                    continue
                
                # Para tramos de enlace T1, usar destino especial (_dest_facility_id)
                if '_dest_facility_id' in row_dict and pd.notna(row_dict.get('_dest_facility_id')):
                    origin_id = row_dict.get('origin_facility_id')
                    dest_id = row_dict.get('_dest_facility_id')
                    dest_type = 'FACILITY'
                else:
                    # Determinar origen
                    origin_id = row_dict.get('origin_facility_id') if pd.notna(row_dict.get('origin_facility_id')) else row_dict.get('origin_treatment_plant_id')
                    
                    # Determinar destino y su tipo
                    if pd.notna(row_dict.get('destination_site_id')):
                        dest_id = row_dict.get('destination_site_id')
                        dest_type = 'SITE'
                    elif pd.notna(row_dict.get('destination_treatment_plant_id')):
                        dest_id = row_dict.get('destination_treatment_plant_id')
                        dest_type = 'TREATMENT_PLANT'
                    else:
                        dest_id = None
                        dest_type = None
                
                distance = 0.0
                # Validar que los IDs sean válidos (no NaN, no None)
                origin_valid = pd.notna(origin_id) and origin_id is not None
                dest_valid = pd.notna(dest_id) and dest_id is not None
                
                if origin_valid and dest_valid and dest_type:
                    try:
                        origin_int = int(origin_id)
                        dest_int = int(dest_id)
                        distance = financial_reporting_service.distance_repo.get_route_distance(
                            origin_int, dest_int, dest_type
                        ) or 0.0
                    except (ValueError, TypeError):
                        distance = 0.0
                distances.append(distance)
            
            result_df['distance_km'] = distances
            
            # Redondear valores para que el cálculo coincida con lo que ve el usuario
            # Peso facturable: 2 decimales (como se muestra en tabla)
            # Distancia: 1 decimal
            # Tarifa: 6 decimales
            result_df['billable_weight'] = result_df['billable_weight'].round(2)
            result_df['distance_km'] = result_df['distance_km'].round(1)
            result_df['tariff_uf'] = result_df['tariff_uf'].round(6)
            
            # Calcular subtotal = peso_facturable × distancia × tarifa
            result_df['subtotal_uf'] = result_df['billable_weight'] * result_df['distance_km'] * result_df['tariff_uf']
            
            return result_df
            
    except Exception as e:
        st.error(f"Error al cargar viajes: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame()


def _display_transport_trips_table(trips_df):
    """Muestra la tabla de viajes CON datos de cálculo para auditoría."""
    display_df = trips_df.copy()
    
    # Detectar tipo de viaje/tramo
    def get_trip_type_display(row):
        segment_desc = str(row.get('segment_desc', '')).upper() if pd.notna(row.get('segment_desc')) else ''
        tariff_type = str(row.get('tariff_type', '')).upper() if pd.notna(row.get('tariff_type')) else ''
        
        # Iconos según tipo de tarifa
        if 'T1' in segment_desc:
            return '🔗T1 🔄 Ampliroll'
        elif 'T2' in segment_desc:
            return '🔗T2 🚛+🚗 Amp+Carro'
        elif tariff_type == 'BATEA':
            return '🚛 Batea'
        elif tariff_type == 'AMPLIROLL_CARRO':
            return '🚛+🚗 Amp+Carro'
        elif tariff_type in ('AMPLIROLL', 'AMPLIROLL_SIMPLE'):
            return '🔄 Ampliroll'
        return '❓ N/A'
    
    display_df['Tipo'] = display_df.apply(get_trip_type_display, axis=1)
    
    # Marcar distancias = 0 para revisión
    display_df['⚠️'] = display_df['distance_km'].apply(lambda d: '⚠️' if d == 0 else '')
    
    # Descripción del tramo
    display_df['Tramo'] = display_df.get('segment_desc', 'Directo')
    
    # Formatear punto de enlace y distancia
    if 'link_point_name' in display_df.columns:
        display_df['Punto Enlace'] = display_df.apply(
            lambda row: f"{row.get('link_point_name', '')} ({row.get('dist_to_link', 0):.0f} km)" 
            if pd.notna(row.get('link_point_name')) and row.get('link_point_name') and row.get('link_point_name') != '-' else '-',
            axis=1
        )
    else:
        display_df['Punto Enlace'] = '-'
    
    # Renombrar columnas
    display_df = display_df.rename(columns={
        'date': 'Fecha',
        'vehicle_plate': 'Patente',
        'origin_name': 'Origen',
        'destination_name': 'Destino',
        'net_weight_tons': 'Peso Real (t)',
        'min_weight': 'Peso Mín (t)',
        'billable_weight': 'Peso Fact. (t)',
        'distance_km': 'Dist (km)',
        'tariff_uf': 'Tarifa UF',
        'subtotal_uf': 'Subtotal UF'
    })
    
    # Seleccionar columnas a mostrar (incluyendo auditoría)
    display_cols = [
        '⚠️', 'Fecha', 'Tramo', 'Tipo', 
        'Origen', 'Punto Enlace', 'Destino', 
        'Peso Real (t)', 'Peso Mín (t)', 'Peso Fact. (t)',
        'Dist (km)', 'Tarifa UF', 'Subtotal UF'
    ]
    display_df = display_df[[c for c in display_cols if c in display_df.columns]]
    
    # Mostrar resumen de problemas
    zero_distance = (display_df['Dist (km)'] == 0).sum() if 'Dist (km)' in display_df.columns else 0
    if zero_distance > 0:
        st.warning(f"⚠️ **{zero_distance} viajes sin distancia configurada** - Revise la matriz de distancias")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            '⚠️': st.column_config.TextColumn(width="small"),
            'Fecha': st.column_config.DateColumn(format="DD/MM/YYYY"),
            'Tramo': st.column_config.TextColumn(width="medium"),
            'Peso Real (t)': st.column_config.NumberColumn(format="%.2f"),
            'Peso Mín (t)': st.column_config.NumberColumn(format="%.1f"),
            'Peso Fact. (t)': st.column_config.NumberColumn(format="%.2f"),
            'Dist (km)': st.column_config.NumberColumn(format="%.1f"),
            'Tarifa UF': st.column_config.NumberColumn(format="%.6f"),
            'Subtotal UF': st.column_config.NumberColumn(format="%.4f")
        }
    )


def _render_transport_proforma_info(proforma):
    """Muestra información de la proforma seleccionada con tarifas."""
    status_emoji = "🔒" if proforma.is_closed else "📝"
    status_text = "Cerrada" if proforma.is_closed else "Abierta"
    
    # Información general
    st.markdown(f"**{proforma.proforma_code}** {status_emoji} {status_text}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("UF", f"$ {proforma.uf_value or 0:,.0f}".replace(",", "."))
    with col2:
        st.metric("Diesel", f"$ {proforma.fuel_price or 0:,.0f}/L".replace(",", "."))
    with col3:
        cycle_start = proforma.cycle_start_date.strftime('%d/%m') if proforma.cycle_start_date else 'N/A'
        st.metric("Desde", cycle_start)
    with col4:
        cycle_end = proforma.cycle_end_date.strftime('%d/%m') if proforma.cycle_end_date else 'N/A'
        st.metric("Hasta", cycle_end)
    
    # Mostrar tarifas si están configuradas
    if proforma.has_tariffs():
        st.markdown("**Tarifas (UF/t·km):**")
        tcol1, tcol2, tcol3 = st.columns(3)
        with tcol1:
            batea = proforma.tariff_batea_uf or 0
            st.markdown(f"🚛 **Batea:** `{batea:.6f}`")
        with tcol2:
            ampli = proforma.tariff_ampliroll_uf or 0
            st.markdown(f"🔄 **Ampliroll:** `{ampli:.6f}`")
        with tcol3:
            ampli_carro = proforma.tariff_ampliroll_carro_uf or 0
            st.markdown(f"🚛+🚗 **Ampliroll+Carro:** `{ampli_carro:.6f}`")


def _display_transport_detail(contractor_df, proforma=None):
    """Muestra el detalle de viajes del transportista."""
    display_df = contractor_df.copy()
    
    # Detectar tipo de viaje basado en vehicle_type
    def get_trip_type(row):
        vtype = row.get('vehicle_type', '').upper() if pd.notna(row.get('vehicle_type')) else ''
        if vtype == 'BATEA':
            return '🚛 Batea'
        elif vtype == 'AMPLIROLL_CARRO':
            return '🚛+🚗 Amp+Carro'
        elif vtype in ('AMPLIROLL', 'AMPLIROLL_SIMPLE'):
            return '🔄 Ampliroll'
        return '❓ N/A'
    
    if 'vehicle_type' in display_df.columns:
        display_df['Tipo Vehículo'] = display_df.apply(get_trip_type, axis=1)
    
    # Renombrar columnas
    display_df = display_df.rename(columns={
        'date': 'Fecha',
        'origin_name': 'Origen',
        'destination_name': 'Destino',
        'vehicle_plate': 'Patente',
        'manifest_number': 'Manifiesto',
        'billable_weight': 'Toneladas',
        'adjusted_rate_uf': 'Tarifa (UF/t·km)',
        'distance_km': 'Km',
        'subtotal_uf': 'Total (UF)'
    })
    
    # Seleccionar y ordenar columnas
    if 'Tipo Vehículo' in display_df.columns:
        display_cols = [
            'Fecha', 'Manifiesto', 'Patente', 'Tipo Vehículo',
            'Origen', 'Destino', 'Toneladas', 'Km', 
            'Tarifa (UF/t·km)', 'Total (UF)'
        ]
    else:
        display_cols = [
            'Fecha', 'Manifiesto', 'Patente',
            'Origen', 'Destino', 'Toneladas', 'Km', 
            'Tarifa (UF/t·km)', 'Total (UF)'
        ]
    display_df = display_df[[c for c in display_cols if c in display_df.columns]]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Fecha': st.column_config.DateColumn(format="DD/MM/YYYY"),
            'Toneladas': st.column_config.NumberColumn(format="%.2f"),
            'Km': st.column_config.NumberColumn(format="%.1f"),
            'Tarifa (UF/t·km)': st.column_config.NumberColumn(format="%.6f"),
            'Total (UF)': st.column_config.NumberColumn(format="%.4f")
        }
    )


def _render_transport_export_button(contractor_df, proforma):
    """Renderiza botón de exportación a Excel con resumen."""
    if contractor_df.empty:
        return
    
    # Preparar datos para exportar
    export_df = contractor_df.copy()
    
    # Renombrar columnas
    export_df = export_df.rename(columns={
        'date': 'Fecha',
        'origin_name': 'Origen',
        'destination_name': 'Destino',
        'vehicle_plate': 'Patente',
        'vehicle_type': 'Tipo Vehículo',
        'manifest_number': 'Manifiesto',
        'billable_weight': 'Toneladas',
        'adjusted_rate_uf': 'Tarifa (UF/t·km)',
        'distance_km': 'Distancia (km)',
        'subtotal_uf': 'Total (UF)'
    })
    
    # Crear Excel con múltiples hojas
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Hoja de detalle
        export_cols = [
            'Fecha', 'Manifiesto', 'Patente', 'Tipo Vehículo',
            'Origen', 'Destino', 'Toneladas', 'Distancia (km)',
            'Tarifa (UF/t·km)', 'Total (UF)'
        ]
        export_df[[c for c in export_cols if c in export_df.columns]].to_excel(
            writer, sheet_name='Detalle', index=False
        )
        
        # Hoja de resumen
        total_uf = export_df['Total (UF)'].sum()
        uf_value = proforma.uf_value or 0
        
        summary_data = {
            'Concepto': [
                'Proforma',
                'Período',
                'UF Cierre',
                'Precio Diesel',
                'Total Viajes',
                'Total UF',
                'Total CLP'
            ],
            'Valor': [
                proforma.proforma_code,
                f"{MONTH_NAMES[proforma.period_month - 1]} {proforma.period_year}",
                f"$ {uf_value:,.0f}",
                f"$ {proforma.fuel_price or 0:,.0f}",
                len(export_df),
                f"{total_uf:,.2f}",
                f"$ {total_uf * uf_value:,.0f}"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Resumen', index=False)
        
        # Hoja de tarifas
        if proforma.has_tariffs():
            tariff_data = {
                'Tipo Vehículo': ['Batea', 'Ampliroll', 'Ampliroll + Carro'],
                'Tarifa (UF/t·km)': [
                    proforma.tariff_batea_uf or 0,
                    proforma.tariff_ampliroll_uf or 0,
                    proforma.tariff_ampliroll_carro_uf or 0
                ]
            }
            tariff_df = pd.DataFrame(tariff_data)
            tariff_df.to_excel(writer, sheet_name='Tarifas', index=False)
    
    output.seek(0)
    
    filename = f"Estado_Pago_Transporte_{proforma.proforma_code.replace(' ', '_')}_{proforma.period_year}_{proforma.period_month:02d}.xlsx"
    
    st.download_button(
        label="📥 Exportar a Excel",
        data=output,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ============================================
# TAB: DISPOSICIÓN
# ============================================
def _render_disposal_settlement_tab(financial_reporting_service, contractor_service):
    """
    Renderiza la pestaña de estados de pago para contratistas de disposición.
    Vista independiente con su propio selector de contratista, periodo y cálculo.
    """
    st.subheader("Estado de Pago - Disposición")
    st.info("**Costos** - Lo que pagamos a los contratistas por el servicio de disposición final.")
    
    # Obtener contratistas de disposición configurados
    disposal_contractors = contractor_service.get_contractors_by_type('DISPOSAL')
    
    if not disposal_contractors:
        st.warning("⚠️ No hay contratistas de disposición configurados.")
        st.caption("Configure contratistas en: **Configuración → Disposición → Contratistas**")
        return
    
    # Selector de contratista
    contractor_options = {"Todos los Contratistas": None}
    contractor_options.update({c.name: c.id for c in disposal_contractors})
    
    selected_contractor_name = st.selectbox(
        "Seleccione Contratista de Disposición",
        options=list(contractor_options.keys()),
        key="disposal_settlement_selector"
    )
    selected_contractor_id = contractor_options[selected_contractor_name]
    
    st.markdown("---")
    
    # Selector de periodo y botón calcular
    year, month, calculate_btn = _render_period_selector("disposal")
    
    # Estado de sesión para este tab
    session_key = f"disposal_settlement_{year}_{month}"
    
    if calculate_btn:
        if session_key in st.session_state:
            del st.session_state[session_key]
    
    if session_key not in st.session_state:
        if not calculate_btn:
            st.info("👆 Seleccione contratista y periodo, luego haga clic en **Calcular**.")
            return
        
        with st.spinner(f"Calculando estado de pago para {MONTH_NAMES[month - 1]} {year}..."):
            try:
                settlement = financial_reporting_service.get_monthly_settlement(year, month)
                st.session_state[session_key] = settlement
            except ValueError as e:
                st.error(f"❌ Error: {str(e)}")
                st.caption("Configure indicadores en: **Configuración → Parámetros Financieros**")
                return
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                return
    
    settlement = st.session_state.get(session_key)
    if not settlement:
        return
    
    # Mostrar indicadores económicos
    st.markdown("---")
    uf_value = _render_economic_indicators(settlement.cycle_info)
    
    # Filtrar por contratista seleccionado
    disposal_df = settlement.disposal_df
    
    if disposal_df.empty:
        st.info("No hay movimientos de disposición para este periodo.")
        st.caption("Verifique que existan tarifas configuradas para los sitios de disposición.")
        return
    
    if selected_contractor_id:
        # Filtrar por contratista específico
        if 'contractor_id' in disposal_df.columns:
            disposal_df = disposal_df[disposal_df['contractor_id'] == selected_contractor_id]
        elif 'site_name' in disposal_df.columns:
            disposal_df = disposal_df[disposal_df['site_name'] == selected_contractor_name]
    
    if disposal_df.empty:
        st.info(f"No hay movimientos para **{selected_contractor_name}** en este periodo.")
        return
    
    # Calcular total
    total_uf = disposal_df['subtotal_uf'].sum()
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total a Pagar", f"{total_uf:,.2f} UF".replace(",", "."))
    with col2:
        st.metric("En Pesos", f"$ {total_uf * uf_value:,.0f} CLP".replace(",", "."))
    
    # Mostrar detalle
    _display_disposal_detail(disposal_df)
    
    # Exportar
    st.markdown("---")
    _render_export_button(disposal_df, f"Estado_Pago_Disposicion_{selected_contractor_name}_{year}_{month:02d}.xlsx", "disposal")


def _display_disposal_detail(disposal_df):
    """Muestra el detalle de movimientos de disposición."""
    display_df = disposal_df.copy()
    display_df = display_df.rename(columns={
        'date': 'Fecha',
        'site_name': 'Sitio Disposición',
        'manifest_number': 'Manifiesto',
        'billable_weight': 'Toneladas',
        'rate_uf': 'Tarifa (UF/ton)',
        'subtotal_uf': 'Total (UF)'
    })
    
    display_cols = ['Fecha', 'Manifiesto', 'Sitio Disposición', 'Toneladas', 'Tarifa (UF/ton)', 'Total (UF)']
    display_df = display_df[[c for c in display_cols if c in display_df.columns]]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Fecha': st.column_config.DateColumn(format="DD/MM/YYYY"),
            'Toneladas': st.column_config.NumberColumn(format="%.2f"),
            'Tarifa (UF/ton)': st.column_config.NumberColumn(format="%.4f"),
            'Total (UF)': st.column_config.NumberColumn(format="%.4f")
        }
    )


# ============================================
# TAB: OTROS PROVEEDORES
# ============================================
def _render_otros_settlement_tab(contractor_service):
    """
    Renderiza la pestaña de otros proveedores/gastos genéricos.
    Placeholder para futura implementación de gastos varios.
    """
    st.subheader("Estado de Pago - Otros Proveedores")
    st.info("**Gastos Genéricos** - Otros costos del periodo que no son transporte ni disposición.")
    
    # Mostrar proveedores de otros tipos configurados
    all_contractors = contractor_service.get_all()
    other_contractors = [c for c in all_contractors 
                        if getattr(c, 'contractor_type', None) not in ['TRANSPORT', 'DISPOSAL', None]]
    
    if other_contractors:
        st.markdown("**Proveedores configurados:**")
        
        # Selector de proveedor
        contractor_options = {c.name: c.id for c in other_contractors}
        
        selected_contractor = st.selectbox(
            "Seleccione Proveedor",
            options=list(contractor_options.keys()),
            key="otros_settlement_selector"
        )
        
        st.markdown("---")
        
        # Selector de periodo
        year, month, calculate_btn = _render_period_selector("otros")
        
        if calculate_btn:
            st.info("🚧 **Funcionalidad en desarrollo**")
            st.markdown("""
            La metodología de cálculo para otros proveedores será más sencilla:
            - Registro manual de gastos por proveedor
            - Asociación a periodo de facturación
            - Sin cálculo automático por viajes/toneladas
            """)
    else:
        st.caption("No hay otros proveedores configurados.")
    
    st.markdown("---")
    st.markdown("""
    **Tipos de gastos que se podrán registrar:**
    
    - **Servicios varios**: Mantenciones, arriendos, etc.
    - **Mecánicos**: Reparaciones de equipos
    - **Insumos**: Materiales y suministros
    - **Otros**: Gastos no categorizados
    
    Estos gastos se sumarán al cálculo del costo total del periodo para determinar el margen real.
    """)
    
    st.caption("Configure proveedores en: **Configuración → Otros Proveedores**")


# ============================================
# UTILIDADES
# ============================================
def _render_export_button(df, filename: str, key_prefix: str):
    """Renderiza botón de exportación a Excel."""
    if df.empty:
        return
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Detalle', index=False)
    output.seek(0)
    
    st.download_button(
        label="📥 Descargar Excel",
        data=output,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"export_{key_prefix}",
        use_container_width=True
    )
