"""Pixel figures that ride the crest.

Each cell is (column, row, role) on a small grid, where role names a colour from
the active theme. `board_row` is the row that should sit on the water line.
"""

SPRITES = {
    "surfer": {
        "board_row": 5,
        "cells": [
            (2, 0, "glint"), (3, 0, "glint"),
            (1, 1, "glint"), (2, 1, "glint"), (3, 1, "accent"), (4, 1, "glint"),
            (2, 2, "accent"), (3, 2, "accent"), (4, 2, "accent"), (5, 2, "glint"),
            (1, 3, "accent"), (2, 3, "accent"), (3, 3, "accent"),
            (2, 4, "accent"), (4, 4, "accent"),
            (0, 5, "glint"), (1, 5, "glint"), (2, 5, "glint"),
            (3, 5, "glint"), (4, 5, "glint"), (5, 5, "glint"),
            (6, 4, "hot"),
            (3, 6, "glint"),
        ],
    },
    "sail": {
        "board_row": 5,
        "cells": [
            (3, 0, "glint"),
            (2, 1, "accent"), (3, 1, "accent"),
            (1, 2, "accent"), (2, 2, "accent"), (3, 2, "accent"),
            (0, 3, "accent"), (1, 3, "accent"), (2, 3, "accent"), (3, 3, "accent"),
            (3, 4, "glint"),
            (0, 5, "glint"), (1, 5, "glint"), (2, 5, "glint"),
            (3, 5, "glint"), (4, 5, "glint"), (5, 5, "glint"),
            (6, 4, "hot"),
            (2, 6, "glint"), (3, 6, "glint"),
        ],
    },
    "buoy": {
        "board_row": 5,
        "cells": [
            (2, 1, "hot"), (3, 1, "hot"),
            (2, 2, "glint"), (3, 2, "glint"),
            (2, 3, "accent"), (3, 3, "accent"),
            (1, 4, "accent"), (2, 4, "accent"), (3, 4, "accent"), (4, 4, "accent"),
            (1, 5, "glint"), (2, 5, "glint"), (3, 5, "glint"), (4, 5, "glint"),
            (0, 6, "glint"), (5, 6, "glint"),
        ],
    },
    "flag": {
        "board_row": 5,
        "cells": [
            (1, 0, "glint"), (2, 0, "accent"), (3, 0, "accent"), (4, 0, "accent"), (5, 0, "hot"),
            (1, 1, "glint"), (2, 1, "accent"), (3, 1, "accent"), (4, 1, "accent"),
            (1, 2, "glint"), (2, 2, "accent"), (3, 2, "accent"),
            (1, 3, "glint"),
            (1, 4, "glint"),
            (0, 5, "glint"), (1, 5, "glint"), (2, 5, "glint"),
        ],
    },
    "none": {"board_row": 5, "cells": []},
}

DEFAULT = "surfer"


def get(name):
    return SPRITES.get((name or DEFAULT).strip().lower(), SPRITES[DEFAULT])


def preview(name):
    """ASCII view of a sprite, for eyeballing a design without rendering."""
    spec = get(name)
    cells = spec["cells"]
    if not cells:
        return "(empty)"
    w = max(c for c, _, _ in cells) + 1
    h = max(r for _, r, _ in cells) + 1
    grid = [["." for _ in range(w)] for _ in range(h)]
    for c, r, role in cells:
        grid[r][c] = {"accent": "#", "glint": "o", "hot": "*"}[role]
    return "\n".join(" ".join(row) for row in grid)
