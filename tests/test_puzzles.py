"""
Test puzzles for each of 16 sudoku solving techniques.

Each puzzle grid is in a state where the target technique is the FIRST (simplest)
applicable technique — simpler techniques have already been exhausted.

Sources:
- HoDoKu (hodoku.sourceforge.net) example puzzles for: naked_single, box_line_reduction,
  x_wing, swordfish, xy_wing, jellyfish, unique_rectangle, xyz_wing, forcing_chain
- SudokuWiki.org / HoDoKu starting puzzles solved forward to technique state for:
  hidden_single, naked_pair, naked_triple, hidden_pair, hidden_triple, pointing_pair,
  simple_coloring

Grid format: 9x9 list of lists, 0 = empty cell.
Cells are 0-indexed (row, col).
Eliminations: for placement techniques (naked/hidden single), "digit" is the value to place.
For elimination techniques, "digit" is the candidate to remove from "cell".

Some puzzles require "user_eliminated" — a dict of prior candidate eliminations that must be
passed to analyze() so the solver skips past simpler elimination-based techniques that would
otherwise fire first. This simulates a puzzle state where those simpler eliminations were
already applied in a previous step. Format: {"r<row>c<col>": [digits...]} (1-indexed).
"""

TECHNIQUE_TEST_PUZZLES = {
    "naked_single": [
        {
            # Source: HoDoKu example n101 (load format, pre-solved state)
            # R6C7 has only one candidate: 6
            "grid": [
                [4, 1, 2, 7, 3, 6, 5, 8, 9],
                [0, 0, 0, 0, 0, 0, 1, 0, 6],
                [5, 6, 8, 0, 1, 0, 3, 7, 0],
                [0, 0, 0, 8, 5, 0, 2, 1, 0],
                [1, 0, 0, 0, 0, 0, 0, 0, 8],
                [0, 8, 7, 0, 9, 0, 0, 0, 0],
                [0, 3, 0, 0, 7, 0, 8, 6, 5],
                [8, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 9, 0, 8, 4, 0, 1],
            ],
            "expected_technique": "naked_single",
            "expected_cells": [[5, 6]],
            "expected_eliminations": [{"cell": [5, 6], "digit": 6}],
        },
    ],
    "hidden_single": [
        {
            # Source: HoDoKu example h101, solved forward past naked singles
            # R3C7: digit 8 is the only candidate in its unit
            "grid": [
                [0, 0, 8, 0, 0, 7, 0, 0, 0],
                [0, 1, 6, 0, 8, 3, 0, 0, 0],
                [0, 0, 0, 0, 2, 0, 0, 5, 1],
                [1, 0, 7, 2, 9, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 4, 6, 3, 0, 7],
                [2, 9, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 8, 6, 0, 1, 4, 0],
                [0, 0, 0, 3, 0, 0, 7, 0, 0],
            ],
            "expected_technique": "hidden_single",
            "expected_cells": [[2, 6]],
            "expected_eliminations": [{"cell": [2, 6], "digit": 8}],
        },
    ],
    "naked_pair": [
        {
            # Source: HoDoKu example n201, solved forward past singles
            # R8C3 and R8C4 both have candidates {3, 9} -> eliminates 3 from R8C2
            "grid": [
                [7, 0, 0, 8, 4, 9, 0, 3, 0],
                [9, 2, 8, 1, 3, 5, 0, 0, 6],
                [4, 0, 0, 2, 6, 7, 0, 8, 9],
                [6, 4, 2, 7, 8, 3, 9, 5, 1],
                [3, 9, 7, 4, 5, 1, 6, 2, 8],
                [8, 1, 5, 6, 9, 2, 3, 0, 0],
                [2, 0, 4, 5, 1, 6, 0, 9, 3],
                [1, 0, 0, 0, 0, 8, 0, 6, 0],
                [5, 0, 0, 0, 0, 4, 0, 1, 0],
            ],
            "expected_technique": "naked_pair",
            "expected_cells": [[7, 2], [7, 3]],
            "expected_eliminations": [{"cell": [7, 1], "digit": 3}],
        },
    ],
    "naked_triple": [
        {
            # Source: puzzle "000801500003002000005000300090060020080020090060050040002000900000400200006508000"
            # Solved forward past singles. R7C5, R8C5, R9C5 form triple {1, 7, 9}
            # -> eliminates 7 and 9 from R2C5, and 7 and 9 from R3C5
            "grid": [
                [0, 0, 9, 8, 3, 1, 5, 0, 0],
                [0, 0, 3, 0, 0, 2, 0, 0, 0],
                [0, 0, 5, 0, 0, 0, 3, 0, 0],
                [0, 9, 0, 0, 6, 0, 0, 2, 0],
                [0, 8, 0, 0, 2, 0, 0, 9, 0],
                [2, 6, 0, 0, 5, 0, 0, 4, 0],
                [0, 0, 2, 0, 0, 0, 9, 0, 0],
                [0, 0, 8, 4, 0, 0, 2, 0, 0],
                [0, 0, 6, 5, 0, 8, 0, 0, 0],
            ],
            "expected_technique": "naked_triple",
            "expected_cells": [[6, 4], [7, 4], [8, 4]],
            "expected_eliminations": [
                {"cell": [1, 4], "digit": 7},
                {"cell": [1, 4], "digit": 9},
                {"cell": [2, 4], "digit": 7},
                {"cell": [2, 4], "digit": 9},
            ],
        },
    ],
    "hidden_pair": [
        {
            # Source: HoDoKu example h201, solved forward past singles/pairs/triples
            # R5C9 and R7C9 contain hidden pair {1, 9} -> eliminates 6 from R5C9
            "grid": [
                [0, 4, 9, 1, 3, 2, 0, 0, 0],
                [0, 8, 1, 4, 7, 9, 0, 0, 0],
                [3, 2, 7, 6, 8, 5, 9, 1, 4],
                [0, 9, 6, 0, 5, 1, 8, 0, 0],
                [0, 7, 5, 0, 2, 8, 0, 0, 0],
                [0, 3, 8, 0, 4, 6, 0, 0, 5],
                [8, 5, 3, 2, 6, 7, 0, 0, 0],
                [7, 1, 2, 8, 9, 4, 5, 6, 3],
                [9, 6, 4, 5, 1, 3, 0, 0, 0],
            ],
            "expected_technique": "hidden_pair",
            "expected_cells": [[4, 8], [6, 8]],
            "expected_eliminations": [{"cell": [4, 8], "digit": 6}],
        },
    ],
    "hidden_triple": [
        {
            # Source: HoDoKu example h301, solved forward past simpler techniques
            # R8C2, R9C2, R9C3 contain hidden triple {2, 4, 5}
            # -> eliminates 1 from R9C2, 6 from R9C3
            "grid": [
                [2, 8, 0, 0, 0, 0, 4, 7, 3],
                [5, 3, 4, 8, 2, 7, 1, 9, 6],
                [0, 7, 1, 0, 3, 4, 0, 8, 0],
                [3, 0, 0, 5, 0, 0, 0, 4, 0],
                [0, 0, 0, 3, 4, 0, 0, 6, 0],
                [4, 6, 0, 7, 9, 0, 3, 1, 0],
                [0, 9, 0, 2, 0, 3, 6, 5, 4],
                [0, 0, 3, 0, 0, 9, 8, 2, 1],
                [0, 0, 0, 0, 8, 0, 9, 3, 7],
            ],
            "expected_technique": "hidden_triple",
            "expected_cells": [[7, 1], [8, 1], [8, 2]],
            "expected_eliminations": [
                {"cell": [8, 1], "digit": 1},
                {"cell": [8, 2], "digit": 6},
            ],
        },
    ],
    "pointing_pair": [
        {
            # Source: HoDoKu example lc101, solved forward with elimination state
            # In Box 1, digit 5 only appears in R3C1 and R3C2 (same row)
            # -> eliminates 5 from R3C7 (rest of row 3)
            # Requires user_eliminated to skip past naked_triple that fires first
            "grid": [
                [9, 8, 4, 0, 0, 0, 0, 0, 0],
                [0, 0, 2, 5, 0, 0, 0, 4, 0],
                [0, 0, 1, 9, 0, 4, 0, 0, 2],
                [0, 0, 6, 0, 9, 7, 2, 3, 0],
                [0, 0, 3, 6, 0, 2, 0, 0, 0],
                [2, 0, 9, 0, 3, 5, 6, 1, 0],
                [1, 9, 5, 7, 6, 8, 4, 2, 3],
                [4, 2, 7, 3, 5, 1, 8, 9, 6],
                [6, 3, 8, 0, 0, 9, 7, 5, 1],
            ],
            "user_eliminated": {"r2c5": [7], "r2c7": [3], "r2c9": [7]},
            "expected_technique": "pointing_pair",
            "expected_cells": [[2, 0], [2, 1]],
            "expected_eliminations": [{"cell": [2, 6], "digit": 5}],
        },
    ],
    "box_line_reduction": [
        {
            # Source: HoDoKu example lc201 (Claiming / Locked Candidates Type 2)
            # In Row 2, digit 7 only appears in Box 1 (R2C2, R2C3)
            # -> eliminates 7 from R3C2 (rest of Box 1)
            "grid": [
                [3, 1, 8, 0, 0, 5, 4, 0, 6],
                [0, 0, 0, 6, 0, 3, 8, 1, 0],
                [0, 0, 6, 0, 8, 0, 5, 0, 3],
                [8, 6, 4, 9, 5, 2, 1, 3, 7],
                [1, 2, 3, 4, 7, 6, 9, 5, 8],
                [7, 9, 5, 3, 1, 8, 2, 6, 4],
                [0, 3, 0, 5, 0, 0, 7, 8, 0],
                [0, 0, 0, 0, 0, 7, 3, 0, 5],
                [0, 0, 0, 0, 3, 9, 6, 4, 1],
            ],
            "expected_technique": "box_line_reduction",
            "expected_cells": [[1, 1], [1, 2]],
            "expected_eliminations": [{"cell": [2, 1], "digit": 7}],
        },
    ],
    "x_wing": [
        {
            # Source: HoDoKu example bf201
            # Digit 5 forms X-Wing in Rows 2,5 / Columns 5,8
            # -> eliminates 5 from R4C5
            "grid": [
                [0, 4, 1, 7, 2, 9, 0, 3, 0],
                [7, 6, 9, 0, 0, 3, 4, 0, 2],
                [0, 3, 2, 6, 4, 0, 7, 1, 9],
                [4, 0, 3, 9, 0, 0, 1, 7, 0],
                [6, 0, 7, 0, 0, 4, 9, 0, 3],
                [1, 9, 5, 3, 7, 0, 0, 2, 4],
                [2, 1, 4, 5, 6, 7, 3, 9, 8],
                [3, 7, 6, 0, 9, 0, 5, 4, 1],
                [9, 5, 8, 4, 3, 1, 2, 6, 7],
            ],
            "expected_technique": "x_wing",
            "expected_cells": [[1, 4], [1, 7], [4, 4], [4, 7]],
            "expected_eliminations": [{"cell": [3, 4], "digit": 5}],
        },
    ],
    "swordfish": [
        {
            # Source: HoDoKu example bf301
            # Digit 2 forms Swordfish in Rows 2,3,9 / Columns 1,5,8
            # -> eliminates 2 from R7C1 and R6C8
            "grid": [
                [1, 6, 0, 5, 4, 3, 0, 7, 0],
                [0, 7, 8, 6, 0, 1, 4, 3, 5],
                [4, 3, 5, 8, 0, 7, 6, 0, 1],
                [7, 2, 0, 4, 5, 8, 0, 6, 9],
                [6, 0, 0, 9, 1, 2, 0, 5, 7],
                [0, 0, 0, 3, 7, 6, 0, 0, 4],
                [0, 1, 6, 0, 3, 0, 0, 4, 0],
                [3, 0, 0, 0, 8, 0, 0, 1, 6],
                [0, 0, 7, 1, 6, 4, 5, 0, 3],
            ],
            "expected_technique": "swordfish",
            "expected_cells": [[1, 0], [1, 4], [2, 4], [2, 7], [8, 0], [8, 7]],
            "expected_eliminations": [
                {"cell": [6, 0], "digit": 2},
                {"cell": [5, 7], "digit": 2},
            ],
        },
    ],
    "xy_wing": [
        {
            # Source: HoDoKu example xy01
            # Pivot R1C3 {5,7}, Wing1 R1C6 {2,5}, Wing2 R2C1 {2,7}
            # -> eliminates 2 from R2C6
            "grid": [
                [8, 0, 0, 3, 6, 0, 9, 0, 0],
                [0, 0, 9, 0, 1, 0, 8, 6, 3],
                [0, 6, 3, 0, 8, 9, 0, 0, 5],
                [9, 2, 4, 6, 7, 3, 1, 5, 8],
                [3, 8, 6, 9, 5, 1, 7, 2, 4],
                [5, 7, 1, 8, 2, 4, 3, 9, 6],
                [4, 3, 2, 1, 9, 6, 5, 8, 7],
                [6, 9, 8, 5, 3, 7, 0, 0, 0],
                [0, 0, 0, 2, 4, 8, 6, 3, 9],
            ],
            "expected_technique": "xy_wing",
            "expected_cells": [[0, 2], [0, 5], [1, 0]],
            "expected_eliminations": [{"cell": [1, 5], "digit": 2}],
        },
    ],
    "simple_coloring": [
        {
            # Source: HoDoKu example sc01, solved forward with elimination state
            # Simple coloring on digit 3: R1C9 sees both color groups
            # -> eliminates 3 from R1C9
            # Requires user_eliminated to skip past naked_triple that fires first
            "grid": [
                [2, 1, 4, 0, 0, 6, 0, 0, 0],
                [0, 0, 7, 9, 0, 2, 0, 0, 4],
                [0, 0, 0, 4, 0, 7, 0, 0, 0],
                [0, 0, 1, 8, 7, 0, 0, 3, 2],
                [0, 0, 2, 6, 9, 0, 0, 0, 0],
                [0, 4, 8, 0, 2, 1, 0, 0, 6],
                [4, 2, 0, 7, 0, 9, 8, 6, 1],
                [0, 0, 9, 1, 6, 8, 0, 0, 0],
                [1, 8, 6, 2, 4, 0, 0, 0, 9],
            ],
            "user_eliminated": {
                "r8c7": [3, 5, 7],
                "r8c8": [5, 7],
                "r3c7": [9],
                "r3c8": [9],
                "r8c9": [7],
            },
            "expected_technique": "simple_coloring",
            "expected_cells": [
                [0, 3], [5, 0], [4, 5], [8, 6], [6, 4],
                [2, 2], [5, 3], [8, 5], [7, 8], [6, 2],
            ],
            "expected_eliminations": [{"cell": [0, 8], "digit": 3}],
        },
    ],
    "jellyfish": [
        {
            # Source: HoDoKu example bf401
            # Digit 7 forms Jellyfish in Rows 3,4,6,7 / Columns 1,2,5,9
            # -> eliminates 7 from 9 cells in those columns
            "grid": [
                [2, 0, 0, 0, 0, 0, 0, 0, 3],
                [0, 8, 0, 0, 3, 0, 0, 5, 0],
                [0, 0, 3, 4, 0, 2, 1, 0, 0],
                [0, 0, 1, 2, 0, 5, 4, 0, 0],
                [0, 0, 0, 0, 9, 0, 0, 0, 0],
                [0, 0, 9, 3, 0, 8, 6, 0, 0],
                [0, 0, 2, 5, 0, 6, 9, 0, 0],
                [0, 9, 0, 0, 2, 0, 0, 7, 0],
                [4, 0, 0, 0, 0, 0, 0, 0, 1],
            ],
            "expected_technique": "jellyfish",
            "expected_cells": [
                [2, 0], [2, 1], [2, 4], [2, 8],
                [3, 0], [3, 1], [3, 4], [3, 8],
                [5, 0], [5, 1], [5, 4], [5, 8],
                [6, 0], [6, 1], [6, 4],
            ],
            "expected_eliminations": [
                {"cell": [1, 0], "digit": 7},
                {"cell": [4, 0], "digit": 7},
                {"cell": [0, 1], "digit": 7},
                {"cell": [4, 1], "digit": 7},
                {"cell": [8, 1], "digit": 7},
                {"cell": [0, 4], "digit": 7},
                {"cell": [8, 4], "digit": 7},
                {"cell": [1, 8], "digit": 7},
                {"cell": [4, 8], "digit": 7},
            ],
        },
    ],
    "unique_rectangle": [
        {
            # Source: HoDoKu example u101 (Type 1)
            # R2C2, R2C3, R6C2, R6C3 form UR with digits {8, 9}
            # R2C2 is the corner with extra candidates -> eliminate 8, 9 from it
            "grid": [
                [5, 0, 2, 0, 0, 8, 9, 6, 7],
                [1, 0, 0, 7, 0, 0, 4, 5, 2],
                [0, 6, 7, 5, 0, 0, 3, 8, 1],
                [2, 1, 3, 6, 5, 7, 8, 4, 9],
                [6, 5, 4, 8, 9, 1, 2, 7, 3],
                [7, 0, 0, 0, 0, 4, 6, 1, 5],
                [8, 2, 1, 9, 0, 0, 0, 3, 4],
                [3, 0, 6, 0, 0, 0, 0, 9, 8],
                [0, 0, 5, 0, 8, 3, 0, 2, 6],
            ],
            "expected_technique": "unique_rectangle",
            "expected_cells": [[1, 1], [1, 2], [5, 1], [5, 2]],
            "expected_eliminations": [
                {"cell": [1, 1], "digit": 8},
                {"cell": [1, 1], "digit": 9},
            ],
        },
    ],
    "xyz_wing": [
        {
            # Source: HoDoKu example xyz01
            # Pivot R7C2 {4,5,7}, Wing1 R2C2 {4,7}, Wing2 R7C1 {5,7}
            # -> eliminates 7 from R9C2
            "grid": [
                [8, 6, 9, 4, 5, 3, 7, 2, 1],
                [0, 0, 0, 9, 2, 1, 5, 6, 8],
                [2, 1, 5, 8, 0, 0, 4, 3, 9],
                [6, 2, 1, 5, 3, 4, 9, 8, 7],
                [4, 0, 7, 6, 1, 0, 3, 5, 2],
                [0, 0, 0, 2, 0, 0, 1, 4, 6],
                [0, 0, 0, 1, 0, 2, 8, 0, 3],
                [9, 3, 2, 7, 8, 5, 6, 1, 4],
                [1, 0, 0, 3, 4, 0, 2, 0, 5],
            ],
            "expected_technique": "xyz_wing",
            "expected_cells": [[6, 1], [1, 1], [6, 0]],
            "expected_eliminations": [{"cell": [8, 1], "digit": 7}],
        },
    ],
    "forcing_chain": [
        {
            # Source: HoDoKu example fcv01 (Forcing Chain Verity)
            # All candidates in R1C7 lead to the same conclusion: R1C7 = 4
            "grid": [
                [2, 7, 1, 8, 9, 6, 0, 0, 0],
                [9, 4, 3, 5, 2, 7, 6, 8, 1],
                [8, 5, 6, 3, 1, 4, 7, 9, 2],
                [4, 8, 0, 0, 0, 0, 0, 2, 0],
                [6, 3, 0, 0, 0, 0, 0, 0, 0],
                [5, 1, 0, 0, 0, 0, 0, 0, 0],
                [3, 9, 5, 0, 0, 0, 0, 7, 0],
                [7, 2, 4, 0, 3, 8, 5, 0, 9],
                [1, 6, 8, 0, 0, 0, 2, 4, 3],
            ],
            "expected_technique": "forcing_chain",
            "expected_cells": [[0, 6]],
            "expected_eliminations": [{"cell": [0, 6], "digit": 4}],
        },
    ],
}
