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

import random
from typing import Dict
from ..models.models import Node


def tick_sim(nodes: Dict[str, Node], activity_level: int):
    """Simulate heartbeat, bus activity, and occasional faults."""
    for n in nodes.values():
        n.bus_activity = False

    mods = [n for n in nodes.values() if n.kind in ("tinyMod", "tinyHub", "tinyCore")]
    k = max(1, min(len(mods), activity_level))
    for n in random.sample(mods, k=k):
        n.bus_activity = True

    if random.random() < 0.05:
        victim = random.choice([n for n in nodes.values() if n.kind == "tinyMod"])
        victim.state = "FAULT"
        victim.fault_code = random.choice(["E01_WATCHDOG", "E12_BUS_TIMEOUT", "E33_OVERCURRENT_SIM"])


def set_role(nodes: Dict[str, Node], node_name: str, role: str):
    n = nodes[node_name]
    n.role = role
    if role == "UNASSIGNED":
        n.state = "UNASSIGNED"
    else:
        n.state = "CONFIGURED" if n.state in ("UNASSIGNED",) else n.state


def activate_node(nodes: Dict[str, Node], node_name: str):
    n = nodes[node_name]
    if n.state != "FAULT" and n.role != "UNASSIGNED":
        n.state = "ACTIVE"


def clear_fault(nodes: Dict[str, Node], node_name: str):
    """PLC-style ACK: clear FAULT and return to CONFIGURED (or UNASSIGNED)."""
    n = nodes[node_name]
    if n.state != "FAULT":
        return

    n.fault_code = ""
    n.state = "CONFIGURED" if n.role != "UNASSIGNED" else "UNASSIGNED"
