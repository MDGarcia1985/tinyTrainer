"""
tinyTrainer - Interactive training kit for embedded systems
Copyright (c) 2026 Michael Garcia

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import streamlit as st
import streamlit.components.v1 as components

from models.models import ROLES, init_nodes, init_edges
from simulations.simulation import tick_sim, set_role, activate_node, clear_fault
from ui.rendering import render_interactive_graph, oled_panel


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

def run():
    import streamlit.web.bootstrap as bootstrap
    from pathlib import Path

    app_path = Path(__file__).resolve()
    bootstrap.run(
        str(app_path),
        command_line="",
        args=[],
        flag_options={},
    )

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
        c1, c2, c3, c4 = st.columns([0.35, 0.30, 0.18, 0.17])
        with c1:
            st.write(f"**{n.name}**")
        with c2:
            new_role = st.selectbox("Role", ROLES, index=ROLES.index(n.role) if n.role in ROLES else 0, key=f"role_{n.name}")
            if new_role != n.role:
                set_role(st.session_state.nodes, n.name, new_role)
        with c3:
            if st.button("Activate", key=f"act_{n.name}"):
                activate_node(st.session_state.nodes, n.name)
        with c4:
            if n.state == "FAULT":
                if st.button("Clear", key=f"clr_{n.name}"):
                    clear_fault(st.session_state.nodes, n.name)

    st.divider()
    st.subheader("tinyMod OLED preview")

    pick = st.selectbox("Select a node", list(st.session_state.nodes.keys()), index=1)
    n = st.session_state.nodes[pick]
    st.code(oled_panel(n, st.session_state.view), language="text")

    st.caption("Tip: In PLC view, NODE ID + STATE + BUS activity is the industrial 'tells'. In Concept view, it's role-first and friendly.")
