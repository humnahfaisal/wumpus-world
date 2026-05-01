"""
Wumpus World Environment.

Manages the grid, hazard placement, and percept generation.
"""

import random


class WumpusWorld:
    def __init__(self, rows, cols, pit_prob=0.15, seed=None):
        """
        Create a new Wumpus World.

        Args:
            rows: Number of rows in the grid.
            cols: Number of columns in the grid.
            pit_prob: Probability of a pit in each non-start cell.
            seed: Optional random seed for reproducibility.
        """
        if seed is not None:
            random.seed(seed)

        self.rows = rows
        self.cols = cols
        self.pits = set()
        self.wumpus_pos = None
        self.gold_pos = None

        # Place pits (excluding start cell (0,0))
        for r in range(rows):
            for c in range(cols):
                if (r, c) == (0, 0):
                    continue
                if random.random() < pit_prob:
                    self.pits.add((r, c))

        # Place wumpus on a random non-start, non-pit cell
        available = [
            (r, c) for r in range(rows) for c in range(cols)
            if (r, c) != (0, 0) and (r, c) not in self.pits
        ]
        if available:
            self.wumpus_pos = random.choice(available)

        # Place gold on a random non-start, non-pit, non-wumpus cell
        available = [
            (r, c) for r in range(rows) for c in range(cols)
            if (r, c) != (0, 0) and (r, c) not in self.pits
            and (r, c) != self.wumpus_pos
        ]
        if available:
            self.gold_pos = random.choice(available)

    def get_adjacent(self, r, c):
        """Return list of valid adjacent cells (up, down, left, right)."""
        adj = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                adj.append((nr, nc))
        return adj

    def get_percepts(self, r, c):
        """Return set of percepts at cell (r, c)."""
        percepts = set()
        for ar, ac in self.get_adjacent(r, c):
            if (ar, ac) in self.pits:
                percepts.add('breeze')
            if (ar, ac) == self.wumpus_pos:
                percepts.add('stench')
        if (r, c) == self.gold_pos:
            percepts.add('glitter')
        return percepts

    def is_pit(self, r, c):
        return (r, c) in self.pits

    def is_wumpus(self, r, c):
        return (r, c) == self.wumpus_pos

    def is_gold(self, r, c):
        return (r, c) == self.gold_pos

    def to_dict(self):
        """Serialize for API responses."""
        return {
            'rows': self.rows,
            'cols': self.cols,
            'pits': [list(p) for p in self.pits],
            'wumpus': list(self.wumpus_pos) if self.wumpus_pos else None,
            'gold': list(self.gold_pos) if self.gold_pos else None,
        }
