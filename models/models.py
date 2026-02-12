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

from dataclasses import dataclass
from typing import Dict, List

ROLES = ["UNASSIGNED", "DC motor", "vision", "6 DOF", "ELEVATION"]
STATES = ["UNASSIGNED", "CONFIGURED", "ACTIVE", "FAULT"]

@dataclass
class Node:
    name: str
    kind: str
    role: str = "UNASSIGNED"
    state: str = "UNASSIGNED"
    bus: str = "CAN"
    node_id: int = 0
    heartbeat: bool = True
    bus_activity: bool = False
    fault_code: str = ""
    notes: str = ""
    x: float = 0.0
    y: float = 0.0


def init_nodes() -> Dict[str, Node]:
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
