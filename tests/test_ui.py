"""
UI-layer tests for tinyTrainer.

These tests focus on the parts of the UI that can be verified without launching Streamlit.

Why we do it this way:
- Streamlit files often execute UI code at import-time (page config, widgets, layout).
  That makes them difficult to import safely in pytest.
- The rendering helpers are pure functions. They are stable contracts that should not
  change unless we intentionally change the UI behavior.
"""

from models.models import Node
from ui.rendering import node_style, label_for, render_interactive_graph, oled_panel


def test_node_style_returns_expected_keys_for_fault_state():
    """
    A FAULT is a high-visibility state.

    We do not test exact colors here because color codes are UI tuning.
    We do test that the function provides the keys the renderer depends on.
    """
    n = Node("tinyMod_A", "tinyMod", state="FAULT")
    style = node_style(n)

    assert "color" in style
    assert "fillcolor" in style


def test_node_style_distinguishes_active_core_from_active_non_core():
    """
    The core node is treated as the "brains" of the system.

    In ACTIVE state, the tinyCore should look different from other ACTIVE nodes,
    so that the diagram communicates topology at a glance.
    """
    core = Node("tinyCore", "tinyCore", state="ACTIVE")
    mod = Node("tinyMod_A", "tinyMod", state="ACTIVE")

    core_style = node_style(core)
    mod_style = node_style(mod)

    assert core_style != mod_style


def test_label_for_concept_view_prioritizes_role_for_tinymod():
    """
    Concept view is for learning and communication.

    For tinyMod nodes, we want the label to show the role prominently so that a new
    reader understands what the module does without PLC-style detail.
    """
    n = Node("tinyMod_A", "tinyMod", role="DC motor", state="CONFIGURED", node_id=3)
    label = label_for(n, view="Concept")

    assert "tinyMod" in label
    assert "DC motor" in label


def test_label_for_concept_view_uses_friendly_descriptors_for_core():
    """
    Concept view deliberately avoids industrial jargon.

    The core is labeled with a friendly hint so the diagram reads like a system map,
    not like a fieldbus diagnostic screen.
    """
    n = Node("tinyCore", "tinyCore", role="ARBITRATOR", state="ACTIVE", node_id=1)
    label = label_for(n, view="Concept")

    assert "tinyCore" in label
    assert "(brains)" in label


def test_label_for_plc_view_includes_node_role_state_and_bus():
    """
    PLC view is meant to feel like industrial diagnostics.

    That means the label must include:
    - node identifier
    - role
    - state
    - bus type

    If we remove any of these, the PLC view stops being useful as a teaching tool.
    """
    n = Node("tinyMod_A", "tinyMod", role="DC motor", state="CONFIGURED", node_id=3, bus="CAN")
    label = label_for(n, view="PLC")

    assert "NODE 3" in label
    assert "ROLE:" in label
    assert "STATE:" in label
    assert "BUS:" in label


def test_oled_panel_concept_view_fault_message_is_human_readable():
    """
    The OLED panel in Concept view is written for a beginner.

    When a node faults, the message should be clearly understandable without
    needing to know error codes or internal state machines.
    """
    n = Node("tinyMod_A", "tinyMod", state="FAULT", role="DC motor", node_id=3)
    panel = oled_panel(n, view="Concept")

    assert "Oops!" in panel
    assert "Something went wrong." in panel


def test_oled_panel_plc_view_includes_fault_code_when_faulted():
    """
    PLC view exists to teach diagnosis.

    If a node is in FAULT state, the panel must show a fault code line.
    """
    n = Node(
        "tinyMod_A",
        "tinyMod",
        role="DC motor",
        state="FAULT",
        node_id=3,
        bus="CAN",
        fault_code="E01_WATCHDOG",
    )
    panel = oled_panel(n, view="PLC")

    assert "NODE 3" in panel
    assert "FC" in panel
    assert "E01_WATCHDOG" in panel


def test_render_interactive_graph_returns_html_with_canvas_and_script():
    """
    The graph renderer returns a self-contained HTML+JS bundle.

    We do not attempt to execute the JavaScript here.
    We only verify that the returned HTML has the expected building blocks:
    - a canvas element
    - a script section
    - serialized node data that includes node names
    """
    nodes = {
        "tinyCore": Node("tinyCore", "tinyCore", role="ARBITRATOR", state="ACTIVE", node_id=1, x=200, y=250),
        "tinyMod_A": Node("tinyMod_A", "tinyMod", role="DC motor", state="CONFIGURED", node_id=3, x=400, y=200),
    }
    edges = [("tinyCore", "tinyMod_A", "bus")]

    html = render_interactive_graph(nodes, edges, view="Concept")

    assert "<canvas" in html
    assert "<script>" in html
    assert "tinyCore" in html
    assert "tinyMod_A" in html


def test_render_interactive_graph_uses_different_node_sizes_for_concept_and_plc_views():
    """
    PLC view labels contain more text than Concept view labels.

    The renderer compensates by using a larger node size in PLC view.
    If this changes, PLC view labels will become cramped and unreadable.
    """
    nodes = {"A": Node("A", "tinyMod", node_id=1, x=100, y=100)}
    edges = []

    html_concept = render_interactive_graph(nodes, edges, view="Concept")
    html_plc = render_interactive_graph(nodes, edges, view="PLC")

    assert "const nodeSize = 52;" in html_concept
    assert "const nodeSize = 70;" in html_plc