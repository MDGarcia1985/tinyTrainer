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

"""
Simulation package for tinyTrainer.

Intent:
- Expose the public simulation API in one place.
- Keep callers insulated from internal file structure.
- Avoid side effects at import time.

This package models PLC-style behavior:
- ticking simulated bus activity
- role assignment
- activation logic
- fault handling
"""

from .simulation import (
    tick_sim,
    set_role,
    activate_node,
    clear_fault,
)

__all__ = [
    "tick_sim",
    "set_role",
    "activate_node",
    "clear_fault",
]