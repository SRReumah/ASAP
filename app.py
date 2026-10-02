import importlib.util
import json
import os
import sys
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------
# PAGE CONFIGURATION & ENTERPRISE STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="ASAP",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Font Hierarchy and UI Scaling
st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    
    div[data-testid="stRadio"] label p {
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        color: #e5e7eb !important;
        margin-bottom: 6px !important;
    }
    
    div[data-testid="stWidgetLabel"] p, label p {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #f3f4f6 !important;
    }
    
    .sidebar-subtext {
        color: #cbd5e1 !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        margin-top: 2px !important;
        margin-bottom: 20px !important;
        letter-spacing: 0.3px;
    }
    
    .status-badge-red {
        background-color: rgba(239, 68, 68, 0.12);
        border: 1px solid #ef4444;
        color: #fca5a5;
        padding: 14px 22px;
        border-radius: 8px;
        font-size: 1.05rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 24px;
    }
    
    .status-badge-green {
        background-color: rgba(16, 185, 129, 0.12);
        border: 1px solid #10b981;
        color: #6ee7b7;
        padding: 14px 22px;
        border-radius: 8px;
        font-size: 1.05rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 24px;
    }

    div[data-testid="stMetric"] {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 20px;
        border-radius: 10px;
    }
    
    div[data-testid="stMetricLabel"] p {
        font-size: 0.95rem !important;
        color: #9ca3af !important;
        font-weight: 600 !important;
    }
    
    div[data-testid="stMetricValue"] div {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #f3f4f6 !important;
    }

    button[data-baseweb="tab"] {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #9ca3af !important;
        padding: 12px 20px !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ef4444 !important;
        border-bottom-color: #ef4444 !important;
    }
</style>
""", unsafe_allow_html=True)

# Dynamic import for Member 2 module
spec_m2 = importlib.util.spec_from_file_location("m2_route_risk", os.path.join("src", "02_route_risk.py"))
m2_module = importlib.util.module_from_spec(spec_m2)
spec_m2.loader.exec_module(m2_module)
evaluate_route_telemetry = m2_module.evaluate_route_telemetry

# Dynamic import for Member 1 module
spec_m1 = importlib.util.spec_from_file_location("m1_lpp_allocation", os.path.join("src", "01_lpp_allocation.py"))
m1_module = importlib.util.module_from_spec(spec_m1)
spec_m1.loader.exec_module(m1_module)
run_lpp_allocation = m1_module.run_lpp_allocation

# Session state initializations
if "distress_node" not in st.session_state:
    st.session_state["distress_node"] = None
if "rain_slider" not in st.session_state:
    st.session_state["rain_slider"] = 0.0
if "flood_select" not in st.session_state:
    st.session_state["flood_select"] = "None"


def clear_all_alarms_callback():
    """Callback function executed BEFORE widgets are instantiated."""
    st.session_state["distress_node"] = None
    st.session_state["rain_slider"] = 0.0
    st.session_state["flood_select"] = "None"


# ---------------------------------------------------------
# SIDEBAR CONTROLS & RED BRANDING
# ---------------------------------------------------------
st.sidebar.markdown("<h1 style='color: #ef4444; font-size: 3.4rem; font-weight: 900; margin-bottom: 0px; letter-spacing: 1px;'>ASAP</h1>", unsafe_allow_html=True)
st.sidebar.markdown("<p class='sidebar-subtext'>Automated Supply Allocation Pipeline</p>", unsafe_allow_html=True)
st.sidebar.divider()

view_mode = st.sidebar.radio(
    "Select Interface View Role:",
    ["Command Center Dashboard", "Hospital Emergency Terminal"],
    index=0
)

st.sidebar.divider()

if view_mode == "Command Center Dashboard":
    st.sidebar.markdown("#### Environmental Controls")
    
    # Sync selectbox if emergency distress signal was broadcasted from phone unit
    flood_options = ["None", "H1 - Metro General", "H2 - St. Jude Clinic", "H3 - East Wing ER", "H4 - South Relief Hub"]
    if st.session_state.get("distress_node"):
        for opt in flood_options:
            if opt.startswith(st.session_state["distress_node"]):
                st.session_state["flood_select"] = opt
                break

    sim_rain = st.sidebar.slider("Simulate Regional Rain (mm)", 0.0, 100.0, step=5.0, key="rain_slider")

    flood_injection = st.sidebar.selectbox(
        "Inject Localized Obstacle",
        flood_options,
        key="flood_select"
    )

    selected_node_id = None
    if flood_injection != "None":
        selected_node_id = flood_injection.split(" - ")[0]
        st.session_state["distress_node"] = selected_node_id
    else:
        st.session_state["distress_node"] = None

    st.sidebar.button("CLEAR ALL ALARMS", use_container_width=True, on_click=clear_all_alarms_callback)

# ---------------------------------------------------------
# VIEW ROLE 2: HOSPITAL EMERGENCY TERMINAL
# ---------------------------------------------------------
if view_mode == "Hospital Emergency Terminal":
    st.markdown("## Hospital Field Operations Terminal")
    st.divider()
    
    selected_hosp = st.selectbox(
        "Select Local Station Node:",
        ["H1 - Metro General Hospital", "H2 - St. Jude Clinic", "H3 - East Wing ER", "H4 - South Relief Hub"]
    )
    h_code = selected_hosp.split(" - ")[0]
    
    st.markdown(f"""
    <div class="status-badge-red">
        CRITICAL ALERT: POWER GRID AND ACCESS EMERGENCY AT NODE [{h_code}]
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Generator Diesel Reserves", "15% Remaining", delta="-2.5 Hours Operational", delta_color="inverse")
    with col2:
        st.metric("ICU Emergency Supplies", "CRITICAL DEPLETION", delta="Immediate Supply Required")
        
    st.divider()
    
    if st.button("BROADCAST EMERGENCY DISTRESS SIGNAL", type="primary", use_container_width=True):
        st.session_state["distress_node"] = h_code
        st.session_state["flood_select"] = f"{h_code} - "
        st.success(f"Emergency Distress Signal Broadcasted for Node [{h_code}]. Central Dispatch Notified.")
        st.info("Switch view role in sidebar to 'Command Center Dashboard' to view dispatch response.")

# ---------------------------------------------------------
# VIEW ROLE 1: COMMAND CENTER DASHBOARD
# ---------------------------------------------------------
else:
    csv_file = os.path.join("data", "city_nodes.csv")
    sim_rain_param = sim_rain if sim_rain > 0 else None

    # Member 2: Evaluate Telemetry & Mode
    nodes, auto_mode = evaluate_route_telemetry(
        csv_file, flood_override_node=selected_node_id, simulated_rain=sim_rain_param
    )

    # Member 1: Solve LPP Optimization
    allocation_result = run_lpp_allocation(nodes, target_mode=auto_mode)

    mode_name = allocation_result["dispatch_mode"]
    weight_cap = allocation_result["payload_weight_cap_kg"]
    allocations = allocation_result["allocations"]

    # SYSTEM STATUS BANNER
    st.markdown("## ASAP: Disaster Relief Command Center")
    
    if auto_mode == 1:
        st.markdown(f"""
        <div class="status-badge-red">
            DISPATCH MODE: AIR RELIEF DRONE ACTIVE | Route Obstacle / High Rainfall Detected | Payload Ceiling: {weight_cap:.0f} kg per run
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-badge-green">
            DISPATCH MODE: GROUND TRUCK ACTIVE | All Transit Vectors Clear | Payload Ceiling: {weight_cap:.0f} kg per run
        </div>
        """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # TOP ROW: NETWORK MAP & CARGO DISTRIBUTION
    # ---------------------------------------------------------
    col_left, col_right = st.columns([1.2, 1.0])

    with col_left:
        st.markdown("#### Network Route Topology")

        warehouse_lat, warehouse_lon = 27.7172, 85.3240
        fig_map = go.Figure()

        # Base Node (Amber Square)
        fig_map.add_trace(go.Scatter(
            x=[warehouse_lon],
            y=[warehouse_lat],
            mode="markers+text",
            marker=dict(size=22, color="#fbbf24", symbol="square", line=dict(width=2, color="#ffffff")),
            text=["<b>Base W1</b>"],
            textposition="top center",
            name="Central Warehouse Base",
            hoverinfo="text"
        ))

        # Plot Hospitals & Individual Route Statuses
        for h in nodes:
            h_lat = warehouse_lat + (0.015 if h["id"] == "H1" else -0.012 if h["id"] == "H2" else 0.008 if h["id"] == "H3" else -0.020)
            h_lon = warehouse_lon + (0.012 if h["id"] == "H1" else -0.015 if h["id"] == "H2" else 0.022 if h["id"] == "H3" else 0.005)
            
            is_blocked = (h["road_accessible"] == 0)
            
            if is_blocked:
                line_color = "#f43f5e"
                line_dash = "dot"
                marker_symbol = "circle-x"
                marker_color = "#f43f5e"
                status_txt = "BLOCKED / FLOODED"
            else:
                line_color = "#10b981"
                line_dash = "solid"
                marker_symbol = "circle"
                marker_color = "#10b981"
                status_txt = "CLEAR / OPEN"

            # Draw Route Line
            fig_map.add_trace(go.Scatter(
                x=[warehouse_lon, h_lon],
                y=[warehouse_lat, h_lat],
                mode="lines",
                line=dict(width=3, color=line_color, dash=line_dash),
                hoverinfo="none",
                showlegend=False
            ))

            # Draw Hospital Node
            fig_map.add_trace(go.Scatter(
                x=[h_lon],
                y=[h_lat],
                mode="markers+text",
                marker=dict(size=16, color=marker_color, symbol=marker_symbol, line=dict(width=2, color="#ffffff")),
                text=[f"<b>{h['id']}: {h['name']}</b><br>[{status_txt}]"],
                textposition="bottom center",
                name=f"Node {h['id']}",
                hoverinfo="text"
            ))

        fig_map.update_layout(
            template="plotly_dark",
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            xaxis=dict(title="Longitude (GPS)", showgrid=True, gridcolor="#1f2937", zeroline=False, fixedrange=True),
            yaxis=dict(title="Latitude (GPS)", showgrid=True, gridcolor="#1f2937", zeroline=False, fixedrange=True),
            margin=dict(l=20, r=20, t=20, b=20),
            height=410,
            showlegend=False
        )
        
        st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False, 'doubleClick': False})

    with col_right:
        st.markdown("#### Cargo Payload Distribution")

        h_names = []
        meds = []
        food = []
        fuel_kg = []

        for h_id, data in allocations.items():
            h_names.append(f"{h_id}: {data['name']}")
            meds.append(round(data['medical_kits'] * 12.0, 1))
            food.append(round(data['food_crates'] * 25.0, 1))
            fuel_kg.append(round(data['fuel_liters'] * 0.85, 1))

        fig_cargo = go.Figure()
        fig_cargo.add_trace(go.Bar(name="Generator Fuel (kg)", x=h_names, y=fuel_kg, marker_color="#38bdf8"))
        fig_cargo.add_trace(go.Bar(name="Medical Kits (kg)", x=h_names, y=meds, marker_color="#f43f5e"))
        fig_cargo.add_trace(go.Bar(name="Food Crates (kg)", x=h_names, y=food, marker_color="#34d399"))

        fig_cargo.update_layout(
            template="plotly_dark",
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            barmode="stack",
            height=410,
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(tickangle=-15, fixedrange=True),
            yaxis=dict(range=[0, 3400], title="Weight Delivered (kg)", gridcolor="#1f2937", fixedrange=True)
        )
        st.plotly_chart(fig_cargo, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False, 'doubleClick': False})

    st.divider()

    # ---------------------------------------------------------
    # MODULE BREAKDOWN TABS
    # ---------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "Member 1: LPP Allocation Matrix",
        "Member 2: Telemetry & Route Assessment",
        "Member 3: Inventory Control & EOQ",
        "Member 4: PERT Dispatch Schedule"
    ])

    with tab1:
        st.markdown("##### Member 1: Optimized Cargo Allocation Matrix (PuLP Solver)")
        
        table_rows = []
        for h_id, data in allocations.items():
            table_rows.append({
                "Node ID": h_id,
                "Hospital Name": data["name"],
                "Fuel Delivered": f"{data['fuel_liters']} L",
                "Meds Delivered": f"{data['medical_kits']} Kits",
                "Food Delivered": f"{data['food_crates']} Crates",
                "Total Payload Weight": f"{data['delivered_weight_kg']} kg",
                "Road Accessibility": "OPEN" if data["road_accessible"] == 1 else "BLOCKED",
                "Displacement Distance": f"{data['distance_km']} km"
            })
        
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("##### Member 2: Telemetry & Route Assessment Engine")
        st.markdown(f"**Dispatch Transport Mode:** `{mode_name}` | **Rainfall Parameter:** `{sim_rain} mm`")
        
        telemetry_rows = []
        for h in nodes:
            telemetry_rows.append({
                "Hospital Station": f"{h['id']} - {h['name']}",
                "Displacement Distance": f"{h['distance']} km",
                "Priority Score": f"Urgency Level {h['urgency']}",
                "Road Status": "Clear (Road Open)" if h['road_accessible'] == 1 else "BLOCKED (Inaccessible)",
                "Routed Dispatch Mode": "GROUND TRUCK" if h['road_accessible'] == 1 and auto_mode == 0 else "AIR RELIEF DRONE"
            })
        st.dataframe(pd.DataFrame(telemetry_rows), use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("##### Member 3: Inventory Control & Generator Reserves")
        col_m3_1, col_m3_2, col_m3_3 = st.columns(3)
        
        total_fuel = sum(d['fuel_liters'] for d in allocations.values())
        total_meds = sum(d['medical_kits'] for d in allocations.values())
        total_food = sum(d['food_crates'] for d in allocations.values())
        
        with col_m3_1:
            st.metric("Total Fuel Dispatched", f"{total_fuel} Liters", delta="Central Reserve Ceiling: 2000 L")
        with col_m3_2:
            st.metric("Total Med Kits Dispatched", f"{total_meds} Kits", delta="Central Reserve Ceiling: 600 Kits")
        with col_m3_3:
            st.metric("Total Food Crates Dispatched", f"{total_food} Crates", delta="Central Reserve Ceiling: 1000 Crates")

    with tab4:
        st.markdown("##### Member 4: PERT Critical Path Timeline")
        
        if auto_mode == 1:
            st.info("AIR DRONE DISPATCH SCHEDULE: Critical Path loop duration is 76.33 minutes (Sequence: Cargo Loading -> Flight Transit -> Winch Offload -> Fuel Ingest).")
        else:
            st.info("GROUND TRUCK DISPATCH SCHEDULE: Critical Path loop duration is 115.00 minutes (Sequence: Cargo Loading -> Highway Transit -> Offloading).")
