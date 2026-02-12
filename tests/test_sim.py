"""
Simulation tests for tinyTrainer.

These tests lock down behavior that matters in PLC-style systems:
- bus activity resets and is re-assigned on tick
- activity_level is clamped safely
- faults are injected predictably when forced
- state transition functions behave consistently
"""

import random

import pytest

from models.models import Node
from simulations.simulation import tick_sim, set_role, activate_node, clear_fault


def test_tick_sim_resets_bus_activity_before_setting_new_activity():
    nodes = {
        "tinyCore": Node("tinyCore", "tinyCore", bus_activity=True),
        "tinyHub": Node("tinyHub", "tinyHub", bus_activity=True),
        "tinyMod_A": Node("tinyMod_A", "tinyMod", bus_activity=True),
    }

    random.seed(1)
    tick_sim(nodes, activity_level=1)

    # Not all nodes should remain active because we reset first.
    assert not all(n.bus_activity for n in nodes.values())

    # At least one eligible node should be set active.
    assert any(n.bus_activity for n in nodes.values())


def test_tick_sim_activity_level_is_clamped_to_number_of_eligible_nodes():
    nodes = {
        "tinyCore": Node("tinyCore", "tinyCore"),
        "tinyHub": Node("tinyHub", "tinyHub"),
        "tinyMod_A": Node("tinyMod_A", "tinyMod"),
        "tinyMod_B": Node("tinyMod_B", "tinyMod"),
    }

    random.seed(2)
    tick_sim(nodes, activity_level=999)

    # Eligible kinds are tinyMod/tinyHub/tinyCore. Here, all nodes are eligible.
    assert all(n.bus_activity for n in nodes.values())


def test_tick_sim_never_selects_zero_nodes_even_if_activity_level_is_zero():
    nodes = {
        "tinyCore": Node("tinyCore", "tinyCore"),
        "tinyMod_A": Node("tinyMod_A", "tinyMod"),
    }

    random.seed(3)
    tick_sim(nodes, activity_level=0)

    # k is max(1, ...), so at least one node must be active.
    assert any(n.bus_activity for n in nodes.values())


def test_tick_sim_fault_injection_can_be_forced(monkeypatch):
    nodes = {
        "tinyMod_A": Node("tinyMod_A", "tinyMod", state="CONFIGURED"),
        "tinyMod_B": Node("tinyMod_B", "tinyMod", state="CONFIGURED"),
        "tinyCore": Node("tinyCore", "tinyCore", state="ACTIVE"),
    }

    # Force the probability branch: random.random() < 0.05
    monkeypatch.setattr(random, "random", lambda: 0.0)

    # Victim is chosen from tinyMod nodes only. We pick the first.
    def pick_first(seq):
        return seq[0]

    monkeypatch.setattr(random, "choice", pick_first)

    tick_sim(nodes, activity_level=1)

    assert nodes["tinyMod_A"].state == "FAULT"
    assert nodes["tinyMod_A"].fault_code in ("E01_WATCHDOG", "E12_BUS_TIMEOUT", "E33_OVERCURRENT_SIM")


def test_set_role_unassigned_forces_unassigned_state():
    nodes = {"A": Node("A", "tinyMod", role="DC motor", state="ACTIVE")}

    set_role(nodes, "A", "UNASSIGNED")

    assert nodes["A"].role == "UNASSIGNED"
    assert nodes["A"].state == "UNASSIGNED"


def test_set_role_from_unassigned_sets_configured_state():
    nodes = {"A": Node("A", "tinyMod", role="UNASSIGNED", state="UNASSIGNED")}

    set_role(nodes, "A", "DC motor")

    assert nodes["A"].role == "DC motor"
    assert nodes["A"].state == "CONFIGURED"


def test_set_role_does_not_downgrade_active_state_when_assigning_role():
    nodes = {"A": Node("A", "tinyMod", role="UNASSIGNED", state="ACTIVE")}

    set_role(nodes, "A", "vision")

    # Your code only auto-configures if state was UNASSIGNED.
    assert nodes["A"].role == "vision"
    assert nodes["A"].state == "ACTIVE"


def test_activate_node_only_activates_when_role_assigned_and_not_faulted():
    nodes = {
        "A": Node("A", "tinyMod", role="UNASSIGNED", state="CONFIGURED"),
        "B": Node("B", "tinyMod", role="DC motor", state="FAULT"),
        "C": Node("C", "tinyMod", role="DC motor", state="CONFIGURED"),
    }

    activate_node(nodes, "A")
    activate_node(nodes, "B")
    activate_node(nodes, "C")

    assert nodes["A"].state != "ACTIVE"
    assert nodes["B"].state == "FAULT"
    assert nodes["C"].state == "ACTIVE"


def test_clear_fault_is_noop_if_not_in_fault():
    nodes = {"A": Node("A", "tinyMod", role="DC motor", state="CONFIGURED", fault_code="")}

    clear_fault(nodes, "A")

    assert nodes["A"].state == "CONFIGURED"
    assert nodes["A"].fault_code == ""


def test_clear_fault_resets_fault_code_and_restores_state_to_configured():
    nodes = {"A": Node("A", "tinyMod", role="DC motor", state="FAULT", fault_code="E01_WATCHDOG")}

    clear_fault(nodes, "A")

    assert nodes["A"].fault_code == ""
    assert nodes["A"].state == "CONFIGURED"


def test_clear_fault_restores_unassigned_state_when_role_is_unassigned():
    nodes = {"A": Node("A", "tinyMod", role="UNASSIGNED", state="FAULT", fault_code="E12_BUS_TIMEOUT")}

    clear_fault(nodes, "A")

    assert nodes["A"].fault_code == ""
    assert nodes["A"].state == "UNASSIGNED"