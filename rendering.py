import json
from typing import Dict, List
from models import Node


def node_style(n: Node):
    if n.state == "FAULT":
        return {"color": "#8B0000", "fontcolor": "red", "fillcolor": "#FFE0E0"}
    if n.state == "ACTIVE":
        if n.kind == "tinyCore":
            return {"color": "#00FF00", "fillcolor": "#90EE90"}
        return {"color": "#00CED1", "fillcolor": "#AFEEEE"}
    if n.state == "CONFIGURED":
        return {"color": "#FFD700", "fillcolor": "#FFFACD"}
    return {"color": "#808080", "fillcolor": "#D3D3D3"}


def label_for(n: Node, view: str):
    if view == "Concept":
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
        is_active = nodes[src].bus_activity or nodes[dst].bus_activity
        width = 5 if is_active else 3
        color = "#00BFFF" if is_active else "#228B22"
        edges_data.append({"src": src, "dst": dst, "label": lbl, "width": width, "color": color})
    
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
            ctx.strokeStyle = e.color;
            ctx.lineWidth = e.width;
            ctx.stroke();
        }});
        
        nodes.forEach(n => {{
            drawOctagon(n.x, n.y, nodeSize, n.color, n.fillcolor);
            ctx.fillStyle = n.fontcolor;
            ctx.font = '11px Arial';
            ctx.textAlign = 'center';
            const lines = n.label.split('\\\\n');
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
        if n.state == "FAULT":
            return f"{n.name}\n\n⚠️ Oops!\nSomething went wrong."
        return f"{n.name}\n\nI am:\n{n.role}\n\nStatus:\n{n.state}"
    else:
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
