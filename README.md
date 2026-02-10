# tinyTrainer

**tinyTrainer** is an interactive, visual training kit for embedded systems,
PLC-style logic, and distributed control architectures.

It is designed to bridge the gap between:
- conceptual system thinking
- industrial PLC mental models
- modern embedded / edge-compute workflows

The project emphasizes **clarity, state visibility, and fault-first design**
over abstraction-heavy frameworks.

---

## What tinyTrainer Is

- A **software-defined training environment** for modular embedded systems
- A **visual simulator** for roles, states, buses, and faults
- A **concept ↔ PLC dual-view model** to teach how real systems behave
- A foundation for future hardware-backed training kits

---

## What tinyTrainer Is *Not*

- Not a full PLC runtime
- Not a hardware abstraction framework
- Not a replacement for IEC 61131 tooling
- Not tied to a specific MCU, OS, or vendor

tinyTrainer is intentionally **educational-first**, with industrial realism.

---

## Project Structure

```text
tinytrainer/
├─ __main__.py          # Entry point (python -m tinytrainer)
├─ models/              # Core data structures and system state
├─ simulations/         # System behavior, ticks, and fault logic
├─ ui/                  # Rendering + Streamlit interface
├─ tools/               # Developer utilities (license headers, scripts)
├─ archive/             # Experiments and retired prototypes
└─ README.md

---

## Commenting Principles

This project treats comments as a **teaching and design tool**, not filler.

The following rules apply throughout the codebase:

- Comments are written in **plain language**, not shorthand.
- Comments must **not assume the reader’s skill level**.
- Comments should explain **intent and design decisions**, not just structure.
- If the code is **not immediately obvious**, it deserves a comment.
- If a section required **research, experimentation, or non-trivial reasoning**, it deserves a comment.
- **Globally universal conventions** (e.g., camelCase, snake_case, file layout)
  belong in the README or documentation — **not** inline comments.

The goal is for a motivated reader to understand *why* the system works the way it does,
not merely *what* the code is doing.