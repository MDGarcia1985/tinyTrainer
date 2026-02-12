"""
Model tests for tinyTrainer.

These tests treat the data model as a public contract:
- Node names and core topology should remain stable unless intentionally changed.
- Edges must reference valid nodes.
- Node identifiers and coordinates should be present and consistent.
"""

from models.models import Node, ROLES, STATES, init_nodes, init_edges


def test_roles_and_states_are_non_empty_lists():
    assert isinstance(ROLES, list)
    assert isinstance(STATES, list)
    assert len(ROLES) > 0
    assert len(STATES) > 0


def test_node_defaults_are_sane():
    n = Node(name="X", kind="tinyMod")
    assert n.role == "UNASSIGNED"
    assert n.state == "UNASSIGNED"
    assert n.bus == "CAN"
    assert n.node_id == 0
    assert n.heartbeat is True
    assert n.bus_activity is False
    assert n.fault_code == ""
    assert n.notes == ""
    assert n.x == 0.0
    assert n.y == 0.0


def test_init_nodes_contains_expected_keys():
    nodes = init_nodes()

    expected = {
        "tinyCore",
        "tinyMod_UI",
        "tinyMod_A",
        "tinyMod_B",
        "tinyMod_C",
        "tinyMod_D",
        "tinyHub",
        "tinySwitch",
    }

    assert set(nodes.keys()) == expected


def test_init_nodes_have_unique_node_ids():
    nodes = init_nodes()
    node_ids = [n.node_id for n in nodes.values()]

    # IDs should be set and unique for PLC-style view clarity.
    assert all(isinstance(i, int) for i in node_ids)
    assert all(i > 0 for i in node_ids)
    assert len(node_ids) == len(set(node_ids))


def test_init_nodes_have_valid_positions():
    nodes = init_nodes()

    # Positions are used for rendering and should be numeric.
    for n in nodes.values():
        assert isinstance(n.x, (int, float))
        assert isinstance(n.y, (int, float))

    # Spot-check a couple known placements (locks down the demo layout).
    assert nodes["tinyCore"].x == 200
    assert nodes["tinyCore"].y == 250
    assert nodes["tinySwitch"].x == 800
    assert nodes["tinySwitch"].y == 200


def test_init_nodes_have_expected_kinds():
    nodes = init_nodes()

    assert nodes["tinyCore"].kind == "tinyCore"
    assert nodes["tinyHub"].kind == "tinyHub"
    assert nodes["tinySwitch"].kind == "tinySwitch"

    # All tinyMod_* nodes should be kind "tinyMod"
    for k in ("tinyMod_UI", "tinyMod_A", "tinyMod_B", "tinyMod_C", "tinyMod_D"):
        assert nodes[k].kind == "tinyMod"


def test_init_edges_is_non_empty_and_well_formed():
    edges = init_edges()

    assert isinstance(edges, list)
    assert len(edges) > 0

    for e in edges:
        assert isinstance(e, tuple)
        assert len(e) == 3

        src, dst, label = e
        assert isinstance(src, str)
        assert isinstance(dst, str)
        assert isinstance(label, str)
        assert label != ""


def test_init_edges_reference_existing_nodes():
    nodes = init_nodes()
    edges = init_edges()

    for src, dst, _label in edges:
        assert src in nodes
        assert dst in nodes


def test_init_edges_contains_expected_links():
    edges = set(init_edges())

    # These are key “backbone” links in your demo topology.
    assert ("tinyCore", "tinyMod_A", "bus") in edges
    assert ("tinyMod_UI", "tinyHub", "bus") in edges
    assert ("tinyHub", "tinySwitch", "IO") in edges
    assert ("tinyCore", "tinySwitch", "inputs") in edges
