"""
tinyTrainer – Interactive training kit for embedded systems
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

"""tinyTrainer - Interactive training kit for embedded systems."""
__version__ = "1.0.0"

"""
tiny_trainer package entry.

This file defines the public API for the core system.
UI entry points are intentionally not imported here to keep imports lightweight.
"""

from .models.models import Node, ROLES, STATES, init_nodes, init_edges
from .simulations.simulation import tick_sim, set_role, activate_node, clear_fault

__all__ = [
    "Node",
    "ROLES",
    "STATES",
    "init_nodes",
    "init_edges",
    "tick_sim",
    "set_role",
    "activate_node",
    "clear_fault",
]