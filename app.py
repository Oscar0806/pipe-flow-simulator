import streamlit as st
import plotly.graph_objects as go
import numpy as np
from flow_engine import (PIPE_FLUIDS, PIPE_MATERIALS,
    analyze_pipe, moody_chart_data, colebrook)
 
st.set_page_config(page_title="Pipe Flow Simulator", page_icon="🌊", layout="wide")
st.title("🌊 Pipe Flow & Fluid Dynamics Simulator")
st.markdown("**Darcy-Weisbach, Colebrook-White, Moody Chart – Fluid Dynamics**")
st.divider()
 
st.sidebar.header("💧 Fluid & Pipe")
fluid = st.sidebar.selectbox("Fluid", list(PIPE_FLUIDS.keys()))
material = st.sidebar.selectbox("Pipe material", list(PIPE_MATERIALS.keys()), index=1)
D_mm = st.sidebar.select_slider("Pipe diameter (mm)",
    [15,20,25,32,40,50,65,80,100,150,200,250,300], value=50)
L_m = st.sidebar.slider("Pipe length (m)", 1, 500, 100)
Q = st.sidebar.slider("Flow rate (m³/h)", 0.1, 100.0, 10.0, 0.5)
st.sidebar.header("🔧 Fittings")
n_e90 = st.sidebar.number_input("90° elbows", 0, 20, 4)
n_e45 = st.sidebar.number_input("45° elbows", 0, 20, 0)
n_gate = st.sidebar.number_input("Gate valves", 0, 10, 2)
n_globe = st.sidebar.number_input("Globe valves", 0, 10, 0)
n_entry = st.sidebar.number_input("Sharp entries", 0, 5, 1)
n_exit = st.sidebar.number_input("Exits", 0, 5, 1)
 
fittings = {}
if n_e90: fittings["90° elbow"]=n_e90
if n_e45: fittings["45° elbow"]=n_e45
if n_gate: fittings["Gate valve (open)"]=n_gate
if n_globe: fittings["Globe valve (open)"]=n_globe
if n_entry: fittings["Sharp entry"]=n_entry
if n_exit: fittings["Exit"]=n_exit
 
r = analyze_pipe(fluid, material, D_mm, L_m, Q, fittings)
 
c1,c2,c3,c4,c5 = st.columns(5)
with c1: st.metric("Reynolds", f"{r['Re']:,.0f}")
with c2: st.metric("Regime", r["regime"])
with c3: st.metric("ΔP total", f"{r['dp_total_Pa']:,.0f} Pa")
with c4: st.metric("Velocity", f"{r['V_m_s']:.2f} m/s")
with c5: st.metric("Pump power", f"{r['P_pump_W']:.1f} W")
st.divider()
 
col1, col2 = st.columns(2)
with col1:
    st.subheader("📈 Moody Chart")
    Re_range, moody = moody_chart_data()
    fig = go.Figure()
    labels = {0:"Smooth",1e-6:"1e-6",1e-5:"1e-5",5e-5:"5e-5",
        1e-4:"1e-4",5e-4:"5e-4",1e-3:"1e-3",5e-3:"5e-3",1e-2:"1e-2",5e-2:"5e-2"}
    for ed, f_vals in moody.items():
        fig.add_trace(go.Scatter(x=Re_range.tolist(),y=f_vals,mode="lines",
            name=f"ε/D={labels.get(ed,ed)}",line=dict(width=1.5)))
    fig.add_trace(go.Scatter(x=[r["Re"]],y=[r["f_darcy"]],mode="markers",
        name="YOUR OPERATING POINT",marker=dict(size=14,color="red",symbol="star")))
    fig.update_layout(xaxis_type="log",yaxis_type="log",
        xaxis_title="Reynolds number Re",yaxis_title="Darcy friction factor f",
        height=450,template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
 
with col2:
    st.subheader("🚀 Velocity Profile")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=r["v_profile"],y=r["r_profile"]*1000,
        mode="lines",fill="tozerox",line=dict(color="#3498DB",width=2),
        fillcolor="rgba(52,152,219,0.2)"))
    fig2.add_vline(x=r["V_m_s"],line_dash="dash",line_color="red",
        annotation_text=f"V_mean={r['V_m_s']:.2f} m/s")
    fig2.update_layout(xaxis_title="Velocity (m/s)",yaxis_title="Radial position (mm)",
        height=450,template="plotly_white")
    st.plotly_chart(fig2, use_container_width=True)
 
st.subheader("📊 Pressure Drop Breakdown")
col3, col4 = st.columns(2)
with col3:
    fig3 = go.Figure(go.Bar(x=["Friction","Fittings","Total"],
        y=[r["dp_friction_Pa"],r["dp_minor_Pa"],r["dp_total_Pa"]],
        marker_color=["#3498DB","#E67E22","#E74C3C"],
        text=[f"{r['dp_friction_Pa']:,.0f}",f"{r['dp_minor_Pa']:,.0f}",f"{r['dp_total_Pa']:,.0f}"],
        textposition="outside"))
    fig3.update_layout(yaxis_title="Pressure drop (Pa)",height=300,template="plotly_white")
    st.plotly_chart(fig3, use_container_width=True)
with col4:
    st.markdown("**Detailed Results**")
    st.markdown(f"- Darcy friction factor: **{r['f_darcy']:.6f}**")
    st.markdown(f"- Relative roughness ε/D: {r['eps_D']:.6f}")
    st.markdown(f"- Head loss (friction): {r['h_friction_m']:.3f} m")
    st.markdown(f"- Head loss (fittings): {r['h_minor_m']:.3f} m")
    st.markdown(f"- Head loss (total): **{r['h_total_m']:.3f} m**")
    st.markdown(f"- Pressure drop: **{r['dp_total_bar']:.4f} bar**")
    if r["fitting_details"]:
        st.markdown("**Fitting losses:**")
        for fd in r["fitting_details"]:
            st.markdown(f"  - {fd['count']}× {fd['fitting']}: K={fd['K']}, total={fd['K_total']:.1f}")
 
st.divider()
st.caption("Pipe Flow Simulator | Fluid Dynamics | Oscar Vincent Dbritto ")
