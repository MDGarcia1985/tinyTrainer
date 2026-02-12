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

"""
Core data models for tinyTrainer.

These are intentionally logic-light and behavior-free.
"""

from .models import Node, ROLES, STATES, init_nodes, init_edges

__all__ = [
    "Node",
    "ROLES",
    "STATES",
    "init_nodes",
    "init_edges",
]