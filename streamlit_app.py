import streamlit as st
import streamlit.components.v1 as components

from models import ROLES, init_nodes, init_edges
from simulation import tick_sim, set_role, activate_node
from rendering import render_interactive_graph, oled_panel


st.set_page_config(page_title="tinyTrainerKit Demo", layout="wide")

if "nodes" not in st.session_state:
    st.session_state.nodes = init_nodes()
if "edges" not in st.session_state:
    st.session_state.edges = init_edges()
if "view" not in st.session_state:
    st.session_state.view = "Concept"
if "activity" not in st.session_state:
    st.session_state.activity = 3

st.title("tinyTrainerKit — Concept ↔ PLC Demo")

colL, colR = st.columns([0.62, 0.38], gap="large")

with colL:
    top = st.columns([0.25, 0.25, 0.25, 0.25])
    with top[0]:
        st.session_state.view = st.radio("VIEW", ["Concept", "PLC"], horizontal=True, index=0 if st.session_state.view=="Concept" else 1)
    with top[1]:
        st.session_state.activity = st.slider("Bus activity", 1, 6, st.session_state.activity)
    with top[2]:
        if st.button("Tick simulation"):
            tick_sim(st.session_state.nodes, st.session_state.activity)
    with top[3]:
        if st.button("Reset"):
            st.session_state.nodes = init_nodes()

    html = render_interactive_graph(st.session_state.nodes, st.session_state.edges, st.session_state.view)
    components.html(html, height=720)

with colR:
    st.subheader("Assign tinyMod roles (software-defined)")

    mods = [n for n in st.session_state.nodes.values() if n.kind == "tinyMod"]
    for n in mods:
        c1, c2, c3 = st.columns([0.45, 0.35, 0.20])
        with c1:
            st.write(f"**{n.name}**")
        with c2:
            new_role = st.selectbox("Role", ROLES, index=ROLES.index(n.role) if n.role in ROLES else 0, key=f"role_{n.name}")
            if new_role != n.role:
                set_role(st.session_state.nodes, n.name, new_role)
        with c3:
            if st.button("Activate", key=f"act_{n.name}"):
                activate_node(st.session_state.nodes, n.name)

    st.divider()
    st.subheader("tinyMod OLED preview")

    pick = st.selectbox("Select a node", list(st.session_state.nodes.keys()), index=1)
    n = st.session_state.nodes[pick]
    st.code(oled_panel(n, st.session_state.view), language="text")

    st.caption("Tip: In PLC view, NODE ID + STATE + BUS activity is the industrial 'tells'. In Concept view, it's role-first and friendly.")
