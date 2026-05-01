# 🧠 Dynamic Wumpus World — Knowledge-Based Logic Agent

A web-based AI agent that navigates a Wumpus World grid using **Propositional Logic** and **Resolution Refutation** to deduce safe cells in real time.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-green?logo=flask)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 Project Overview

The agent operates in a dynamic grid environment containing hidden **Pits** and a **Wumpus**. It does **not** know hazard locations initially — instead, it receives percepts (**Breeze** near pits, **Stench** near Wumpus) and uses a **Knowledge Base (KB)** with **Propositional Logic** to infer which cells are safe before moving.

### Key Features

- **Dynamic Grid Sizing** — User-defined grid dimensions (3×3 to 10×10)
- **Random Hazard Placement** — Pits and Wumpus randomly placed each episode
- **Propositional Logic KB** — Agent maintains CNF clauses derived from percepts
- **Resolution Refutation** — Automated inference engine that converts KB to CNF and resolves clauses to prove cell safety
- **Real-Time Visualization** — Color-coded grid with animated agent movement
- **Metrics Dashboard** — Tracks inference steps, KB size, and cells explored


##  Algorithmic Implementation

### Knowledge Base (KB)

The agent maintains a **Propositional Logic KB** stored as a set of CNF clauses:

- When visiting cell `(r,c)` and surviving: `¬P_r_c` and `¬W_r_c` are added
- **Breeze at (r,c)**: adds clause `P_adj1 ∨ P_adj2 ∨ ...` (at least one adjacent cell has a pit)
- **No Breeze at (r,c)**: adds unit clauses `¬P_adj` for each adjacent cell
- Same logic applies for **Stench/Wumpus**

### Resolution Refutation

Before moving to an unvisited cell, the agent **ASK**s the KB:

1. To prove `¬P_{r,c}` (no pit): add `P_{r,c}` to KB, attempt to derive empty clause
2. To prove `¬W_{r,c}` (no wumpus): add `W_{r,c}` to KB, attempt to derive empty clause
3. Uses **Set-of-Support** strategy for efficient resolution
4. If empty clause (contradiction) is found → cell is **proven safe**

### Agent Strategy

1. Start at `(0,0)`, perceive environment, update KB
2. Identify frontier cells (unvisited, adjacent to visited)
3. Use Resolution Refutation to classify each frontier cell as Safe / Dangerous / Unknown
4. Move to the closest proven-safe cell
5. If no safe cell exists, take a calculated risk
6. Repeat until gold is found, agent dies, or no moves remain

---

## 🎨 Visualization

| Color | Meaning |
|-------|---------|
| 🔵 Blue (glowing) | Agent's current position |
| 🟢 Green | Proven safe cell |
| 🔵 Light Blue | Visited cell |
| 🟡 Amber (pulsing) | Frontier cell (unknown safety) |
| 🔴 Red | Confirmed dangerous cell |
| ⬜ Gray | Unknown / unvisited cell |

### Real-Time Metrics Dashboard

- **Agent Steps** — Number of moves taken
- **Cells Explored** — Total visited cells
- **Inference Steps** — Total resolution steps performed
- **KB Clauses** — Current number of clauses in the knowledge base


##  Technologies Used

| Technology | Purpose |
|-----------|---------|
| **Python** | Backend logic, AI agent, inference engine |
| **Flask** | Web server and REST API |
| **Vanilla JavaScript** | Frontend rendering and API communication |
| **HTML/CSS** | UI with dark glassmorphism theme |
| **Vercel** | Cloud deployment (Python serverless) |


