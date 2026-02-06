import random
from dataclasses import dataclass, field
from typing import Dict, List
import json

import streamlit as st
import streamlit.components.v1 as components


# ----------------------------
# Data model
# ----------------------------
ROLES = ["UNASSIGNED", "DC motor", "vision", "6 DOF", "ELEVATION"]
STATES = ["UNASSIGNED", "CONFIGURED", "ACTIVE", "FAULT"]

@dataclass
class Node:
    name: str
    kind: str  # tinyCore / tinyMod / tinyHub / tinySwitch
    role: str = "UNASSIGNED"
    state: str = "UNASSIGNED"
    bus: str = "CAN"         # CAN or BLE (demo)
    node_id: int = 0
    heartbeat: bool = True
    bus_activity: bool = False
    fault_code: str = ""
    notes: str = ""
    x: float = 0.0
    y: float = 0.0


def init_nodes() -> Dict[str, Node]:
    # Matches your "drone" sketch vibe: core + 5 mods + hub + switch
    nodes = {
        "tinyCore": Node("tinyCore", "tinyCore", role="ARBITRATOR", state="ACTIVE", node_id=1, x=200, y=250),
        "tinyMod_UI": Node("tinyMod_UI", "tinyMod", role="UI/CONFIG", state="ACTIVE", node_id=2, x=400, y=100),
        "tinyMod_A": Node("tinyMod_A", "tinyMod", role="DC motor", state="CONFIGURED", node_id=3, x=400, y=200),
        "tinyMod_B": Node("tinyMod_B", "tinyMod", role="vision", state="CONFIGURED", node_id=4, x=400, y=300),
        "tinyMod_C": Node("tinyMod_C", "tinyMod", role="6 DOF", state="CONFIGURED", node_id=5, x=400, y=400),
        "tinyMod_D": Node("tinyMod_D", "tinyMod", role="ELEVATION", state="CONFIGURED", node_id=6, x=400, y=500),
        "tinyHub": Node("tinyHub", "tinyHub", role="IO EXPAND", state="ACTIVE", node_id=20, x=600, y=100),
        "tinySwitch": Node("tinySwitch", "tinySwitch", role="HMI INPUTS", state="ACTIVE", node_id=30, x=800, y=200),
    }
    return nodes


def init_edges() -> List[tuple]:
    # (src, dst, label)
    return [
        ("tinyCore", "tinyMod_UI", "bus"),
        ("tinyCore", "tinyMod_A", "bus"),
        ("tinyCore", "tinyMod_B", "bus"),
        ("tinyCore", "tinyMod_C", "bus"),
        ("tinyCore", "tinyMod_D", "bus"),
        ("tinyMod_UI", "tinyHub", "bus"),
        ("tinyHub", "tinySwitch", "IO"),
        ("tinyCore", "tinySwitch", "inputs"),
    ]


# ----------------------------
# Simulation helpers
# ----------------------------
def tick_sim(nodes: Dict[str, Node], activity_level: int):
    """Simulate heartbeat, bus activity, and occasional faults."""
    # Clear previous bus activity
    for n in nodes.values():
        n.bus_activity = False

    # Randomly mark some nodes as having bus activity
    mods = [n for n in nodes.values() if n.kind in ("tinyMod", "tinyHub", "tinyCore")]
    k = max(1, min(len(mods), activity_level))
    for n in random.sample(mods, k=k):
        n.bus_activity = True

    # Occasional fault injection (rare)
    if random.random() < 0.05:
        victim = random.choice([n for n in nodes.values() if n.kind == "tinyMod"])
        victim.state = "FAULT"
        victim.fault_code = random.choice(["E01_WATCHDOG", "E12_BUS_TIMEOUT", "E33_OVERCURRENT_SIM"])
    # Occasional recovery
    if random.random() < 0.08:
        for n in nodes.values():
            if n.state == "FAULT":
                n.state = "ACTIVE"
                n.fault_code = ""


def set_role(nodes: Dict[str, Node], node_name: str, role: str):
    n = nodes[node_name]
    n.role = role
    if role == "UNASSIGNED":
        n.state = "UNASSIGNED"
    else:
        # move toward configured/active
        n.state = "CONFIGURED" if n.state in ("UNASSIGNED",) else n.state


def activate_node(nodes: Dict[str, Node], node_name: str):
    n = nodes[node_name]
    if n.state != "FAULT" and n.role != "UNASSIGNED":
        n.state = "ACTIVE"


# ----------------------------
# Rendering
# ----------------------------
def node_style(n: Node):
    # Light mint green to grayscale gradient
    if n.state == "FAULT":
        return {"color": "red", "fontcolor": "red", "fillcolor": "#FFE0E0"}
    if n.kind == "tinyCore":
        return {"color": "#98D8C8", "fillcolor": "#C8F0E8"}
    if n.kind == "tinyMod":
        return {"color": "#A8B8B0", "fillcolor": "#D8E8E0"}
    if n.kind == "tinyHub":
        return {"color": "#909890", "fillcolor": "#C0C8C0"}
    if n.kind == "tinySwitch":
        return {"color": "#787878", "fillcolor": "#B0B0B0"}
    return {"color": "gray", "fillcolor": "#D0D0D0"}

def label_for(n: Node, view: str):
    # view is "Concept" or "PLC"
    if view == "Concept":
        # friendly identity: role-first, no IDs
        if n.kind == "tinyMod":
            return f"{n.kind}\n{n.role}"
        if n.kind == "tinyCore":
            return "tinyCore\n(brains)"
        if n.kind == "tinyHub":
            return "tinyHub\n(more ports)"
        if n.kind == "tinySwitch":
            return "tinySwitch\n(buttons)"
        return n.name
    else:
        # PLC view: IDs + state + bus + role
        base = f"{n.kind}  NODE {n.node_id}"
        role = f"ROLE: {n.role}"
        stt = f"STATE: {n.state}"
        bus = f"BUS: {n.bus}"
        return f"{base}\n{role}\n{stt}\n{bus}"

def render_interactive_graph(nodes: Dict[str, Node], edges: List[tuple], view: str):
    nodes_data = []
    for n in nodes.values():
        sty = node_style(n)
        nodes_data.append({
            "name": n.name,
            "label": label_for(n, view),
            "x": n.x,
            "y": n.y,
            "color": sty.get("color", "gray"),
            "fillcolor": sty.get("fillcolor", "white"),
            "fontcolor": sty.get("fontcolor", "black")
        })
    
    edges_data = []
    for (src, dst, lbl) in edges:
        width = 5 if (nodes[src].bus_activity or nodes[dst].bus_activity) else 3
        edges_data.append({"src": src, "dst": dst, "label": lbl, "width": width})
    
    node_size = 70 if view == "PLC" else 52
    
    html = f"""
    <canvas id="canvas" width="1200" height="700" style="border:1px solid #333;"></canvas>
    <script>
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    let nodes = {json.dumps(nodes_data)};
    let edges = {json.dumps(edges_data)};
    let dragging = null;
    const nodeSize = {node_size};
    
    function drawGrid() {{
        ctx.strokeStyle = '#8B0000';
        ctx.lineWidth = 0.5;
        for(let x = 0; x < canvas.width; x += 50) {{
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }}
        for(let y = 0; y < canvas.height; y += 50) {{
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }}
    }}
    
    function pointInOctagon(px, py, x, y, size) {{
        return Math.hypot(px - x, py - y) < size;
    }}
    
    function checkNodeOverlap(x, y, exclude) {{
        for(let n of nodes) {{
            if(n !== exclude && Math.hypot(n.x - x, n.y - y) < nodeSize * 2) {{
                return true;
            }}
        }}
        return false;
    }}
    
    function adjustCurveToAvoidNodes(src, dst, cx, cy) {{
        for(let n of nodes) {{
            if(n !== src && n !== dst) {{
                if(Math.hypot(n.x - cx, n.y - cy) < nodeSize + 20) {{
                    const dx = cx - n.x;
                    const dy = cy - n.y;
                    const dist = Math.hypot(dx, dy);
                    const push = nodeSize + 20 - dist;
                    cx += (dx / dist) * push;
                    cy += (dy / dist) * push;
                }}
            }}
        }}
        return {{cx, cy}};
    }}
    
    function drawOctagon(x, y, size, color, fillcolor) {{
        ctx.beginPath();
        for(let i = 0; i < 8; i++) {{
            const angle = (i * Math.PI / 4) - Math.PI / 8;
            const px = x + size * Math.cos(angle);
            const py = y + size * Math.sin(angle);
            if(i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        }}
        ctx.closePath();
        ctx.fillStyle = fillcolor;
        ctx.fill();
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.stroke();
        
        // Draw connection ports (2 per side)
        for(let i = 0; i < 8; i++) {{
            const angle = (i * Math.PI / 4) - Math.PI / 8;
            const baseX = x + size * Math.cos(angle);
            const baseY = y + size * Math.sin(angle);
            const perpAngle = angle + Math.PI / 2;
            
            for(let offset of [-0.3, 0.3]) {{
                const portX = baseX + offset * size * 0.4 * Math.cos(perpAngle);
                const portY = baseY + offset * size * 0.4 * Math.sin(perpAngle);
                ctx.beginPath();
                ctx.arc(portX, portY, 3, 0, Math.PI * 2);
                ctx.fillStyle = '#228B22';
                ctx.fill();
                ctx.strokeStyle = '#1a5f1a';
                ctx.lineWidth = 1;
                ctx.stroke();
            }}
        }}
    }}
    
    function draw() {{
        ctx.fillStyle = '#4A4E52';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        drawGrid();
        
        edges.forEach(e => {{
            const src = nodes.find(n => n.name === e.src);
            const dst = nodes.find(n => n.name === e.dst);
            let mx = (src.x + dst.x) / 2;
            let my = (src.y + dst.y) / 2;
            const dx = dst.x - src.x;
            const dy = dst.y - src.y;
            const offset = Math.min(50, Math.sqrt(dx*dx + dy*dy) * 0.2);
            let cx = mx - dy / Math.sqrt(dx*dx + dy*dy) * offset;
            let cy = my + dx / Math.sqrt(dx*dx + dy*dy) * offset;
            
            const adjusted = adjustCurveToAvoidNodes(src, dst, cx, cy);
            cx = adjusted.cx;
            cy = adjusted.cy;
            
            ctx.beginPath();
            ctx.moveTo(src.x, src.y);
            ctx.quadraticCurveTo(cx, cy, dst.x, dst.y);
            ctx.strokeStyle = '#228B22';
            ctx.lineWidth = e.width;
            ctx.stroke();
        }});
        
        nodes.forEach(n => {{
            drawOctagon(n.x, n.y, nodeSize, n.color, n.fillcolor);
            ctx.fillStyle = n.fontcolor;
            ctx.font = '11px Arial';
            ctx.textAlign = 'center';
            const lines = n.label.split('\\n');
            lines.forEach((line, i) => {{
                ctx.fillText(line, n.x, n.y - 10 + i * 14);
            }});
        }});
    }}
    
    canvas.onmousedown = e => {{
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        dragging = nodes.find(n => Math.hypot(n.x - mx, n.y - my) < nodeSize);
    }};
    
    canvas.onmousemove = e => {{
        if(dragging) {{
            const rect = canvas.getBoundingClientRect();
            const newX = e.clientX - rect.left;
            const newY = e.clientY - rect.top;
            
            if(!checkNodeOverlap(newX, newY, dragging)) {{
                dragging.x = newX;
                dragging.y = newY;
            }}
            draw();
        }}
    }};
    
    canvas.onmouseup = () => {{ dragging = null; }};
    draw();
    </script>
    """
    return html


def oled_panel(n: Node, view: str) -> str:
    if view == "Concept":
        # simple, kid-friendly
        if n.state == "FAULT":
            return f"{n.name}\n\n⚠️ Oops!\nSomething went wrong."
        return f"{n.name}\n\nI am:\n{n.role}\n\nStatus:\n{n.state}"
    else:
        # PLC-ish
        lines = [
            f"NODE {n.node_id}",
            f"KIND: {n.kind}",
            f"BUS : {n.bus}",
            f"ROLE: {n.role}",
            f"STATE:{n.state}",
            f"HB  : {'OK' if n.heartbeat else 'NO'}",
            f"COMM: {'TX/RX' if n.bus_activity else 'IDLE'}",
        ]
        if n.state == "FAULT":
            lines.append(f"FC  : {n.fault_code or 'E??'}")
        return "\n".join(lines)


# ----------------------------
# Streamlit app
# ----------------------------
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

    st.caption("Tip: In PLC view, NODE ID + STATE + BUS activity is the industrial 'tells'. In Concept view, it’s role-first and friendly.")
