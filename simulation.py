import random
from typing import Dict
from models import Node


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
        n.state = "CONFIGURED" if n.state in ("UNASSIGNED",) else n.state


def activate_node(nodes: Dict[str, Node], node_name: str):
    n = nodes[node_name]
    if n.state != "FAULT" and n.role != "UNASSIGNED":
        n.state = "ACTIVE"
