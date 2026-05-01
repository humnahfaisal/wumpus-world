"""
Knowledge-Based Agent for Wumpus World.

Uses a Propositional Logic KB with Resolution Refutation
to deduce safe cells before moving.
"""

from .logic import resolution_refutation


class KBAgent:
    def __init__(self, world):
        """
        Initialize the KB agent in a Wumpus World.

        Args:
            world: A WumpusWorld instance.
        """
        self.world = world
        self.position = (0, 0)
        self.alive = True
        self.has_gold = False
        self.visited = set()
        self.safe_cells = set()
        self.dangerous_cells = set()
        self.kb = set()  # set of frozensets — CNF clauses
        self.total_inference_steps = 0
        self.log = []
        self.path = [(0, 0)]
        self.percept_map = {}  # cell -> set of percepts
        self.step_count = 0

        # Visit starting cell
        self._visit(0, 0)

    # ------------------------------------------------------------------ #
    #  Literal helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _pit_lit(r, c):
        return f"P_{r}_{c}"

    @staticmethod
    def _wumpus_lit(r, c):
        return f"W_{r}_{c}"

    # ------------------------------------------------------------------ #
    #  TELL — update KB with percepts                                      #
    # ------------------------------------------------------------------ #

    def _visit(self, r, c):
        """Visit cell (r,c), perceive, and update the KB."""
        self.visited.add((r, c))
        self.safe_cells.add((r, c))

        # --- Check death ---
        if self.world.is_pit(r, c):
            self.alive = False
            self.dangerous_cells.add((r, c))
            self.log.append(f"DEATH  Agent fell into a pit at ({r},{c})!")
            return

        if self.world.is_wumpus(r, c):
            self.alive = False
            self.dangerous_cells.add((r, c))
            self.log.append(f"DEATH  Agent eaten by Wumpus at ({r},{c})!")
            return

        # --- Survived — add safe facts ---
        self.kb.add(frozenset({f"~{self._pit_lit(r, c)}"}))
        self.kb.add(frozenset({f"~{self._wumpus_lit(r, c)}"}))

        # --- Get percepts ---
        percepts = self.world.get_percepts(r, c)
        self.percept_map[(r, c)] = percepts

        if self.world.is_gold(r, c):
            self.has_gold = True
            self.log.append(f"GOLD  Agent found gold at ({r},{c})!")

        adjacent = self.world.get_adjacent(r, c)

        # --- Breeze logic ---
        if 'breeze' in percepts:
            # B_{r,c} is TRUE  =>  at least one adjacent cell has a pit
            # CNF clause: P_adj1 ∨ P_adj2 ∨ ...
            clause = frozenset({self._pit_lit(a[0], a[1]) for a in adjacent})
            self.kb.add(clause)
        else:
            # No breeze => NO adjacent cell has a pit
            # Unit clauses: ~P_adj for each adjacent cell
            for ar, ac in adjacent:
                self.kb.add(frozenset({f"~{self._pit_lit(ar, ac)}"}))

        # --- Stench logic ---
        if 'stench' in percepts:
            clause = frozenset({self._wumpus_lit(a[0], a[1]) for a in adjacent})
            self.kb.add(clause)
        else:
            for ar, ac in adjacent:
                self.kb.add(frozenset({f"~{self._wumpus_lit(ar, ac)}"}))

        percept_str = ', '.join(percepts) if percepts else 'none'
        self.log.append(
            f"VISIT  ({r},{c}) | Percepts: [{percept_str}] | KB: {len(self.kb)} clauses"
        )

    # ------------------------------------------------------------------ #
    #  ASK — query the KB using resolution refutation                      #
    # ------------------------------------------------------------------ #

    def _ask_safe(self, r, c):
        """Prove ~P_{r,c} AND ~W_{r,c} via resolution refutation."""
        if (r, c) in self.safe_cells:
            return True, 0
        if (r, c) in self.dangerous_cells:
            return False, 0

        steps = 0

        # Prove no pit
        pit_safe, s1 = resolution_refutation(
            self.kb, f"~{self._pit_lit(r, c)}"
        )
        steps += s1

        # Prove no wumpus
        wumpus_safe, s2 = resolution_refutation(
            self.kb, f"~{self._wumpus_lit(r, c)}"
        )
        steps += s2

        return (pit_safe and wumpus_safe), steps

    def _ask_dangerous(self, r, c):
        """Prove P_{r,c} OR W_{r,c} (cell definitely has a hazard)."""
        steps = 0

        has_pit, s1 = resolution_refutation(self.kb, self._pit_lit(r, c))
        steps += s1

        has_wumpus, s2 = resolution_refutation(self.kb, self._wumpus_lit(r, c))
        steps += s2

        return (has_pit or has_wumpus), steps

    # ------------------------------------------------------------------ #
    #  Agent step                                                          #
    # ------------------------------------------------------------------ #

    def step(self):
        """Agent takes one step. Returns updated state dict."""
        if not self.alive or self.has_gold:
            return self.get_state()

        self.step_count += 1

        # Find frontier (unvisited cells adjacent to any visited cell)
        frontier = set()
        for vr, vc in self.visited:
            for ar, ac in self.world.get_adjacent(vr, vc):
                if (ar, ac) not in self.visited:
                    frontier.add((ar, ac))

        if not frontier:
            self.log.append("DONE  No more frontier cells to explore.")
            return self.get_state()

        # Classify frontier cells
        safe_frontier = []
        for fr, fc in frontier:
            is_safe, steps = self._ask_safe(fr, fc)
            self.total_inference_steps += steps
            if is_safe:
                safe_frontier.append((fr, fc))
                self.safe_cells.add((fr, fc))
                self.log.append(
                    f"SAFE  ({fr},{fc}) proven safe ({steps} inference steps)"
                )
            else:
                is_dangerous, steps2 = self._ask_dangerous(fr, fc)
                self.total_inference_steps += steps2
                if is_dangerous:
                    self.dangerous_cells.add((fr, fc))
                    self.log.append(
                        f"DANGER  ({fr},{fc}) proven dangerous ({steps2} steps)"
                    )

        # Choose next move
        if safe_frontier:
            target = self._closest_cell(safe_frontier)
            self.log.append(f"MOVE  Moving to safe cell ({target[0]},{target[1]})")
        elif frontier - self.dangerous_cells:
            unknown = list(frontier - self.dangerous_cells)
            target = self._closest_cell(unknown)
            self.log.append(
                f"RISK  No proven safe cell. Risking ({target[0]},{target[1]})"
            )
        else:
            self.log.append("STUCK  All frontier cells are dangerous!")
            return self.get_state()

        # Move
        self.position = target
        self.path.append(target)
        self._visit(target[0], target[1])

        return self.get_state()

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _closest_cell(self, candidates):
        """Pick candidate closest (Manhattan) to current position."""
        r, c = self.position
        return min(candidates, key=lambda cell: abs(cell[0] - r) + abs(cell[1] - c))

    def get_state(self):
        """Return full game state as a serialisable dict."""
        frontier = set()
        for vr, vc in self.visited:
            for ar, ac in self.world.get_adjacent(vr, vc):
                if (ar, ac) not in self.visited:
                    frontier.add((ar, ac))

        game_over = (
            not self.alive
            or self.has_gold
            or not (frontier - self.dangerous_cells)
        )

        return {
            'grid': {
                'rows': self.world.rows,
                'cols': self.world.cols,
            },
            'agent': {
                'position': list(self.position),
                'alive': self.alive,
                'has_gold': self.has_gold,
            },
            'cells': {
                'visited': [list(c) for c in sorted(self.visited)],
                'safe': [list(c) for c in sorted(self.safe_cells)],
                'dangerous': [list(c) for c in sorted(self.dangerous_cells)],
                'frontier': [list(c) for c in sorted(frontier)],
            },
            'percepts': {
                'current': sorted(self.percept_map.get(self.position, set())),
                'map': {
                    f"{r},{c}": sorted(p)
                    for (r, c), p in self.percept_map.items()
                },
            },
            'hazards': self.world.to_dict(),
            'metrics': {
                'total_inference_steps': self.total_inference_steps,
                'cells_explored': len(self.visited),
                'kb_clauses': len(self.kb),
                'steps_taken': self.step_count,
            },
            'log': self.log[-30:],
            'game_over': game_over,
            'path': [list(p) for p in self.path],
        }
