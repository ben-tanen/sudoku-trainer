"""
Sudoku solver engine with technique detection.

Does NOT solve the puzzle — identifies the simplest applicable technique
and returns structured output describing what it found.
"""

from __future__ import annotations

from app.models import TechniqueResult


# -- Helpers --

def get_candidates(grid: list[list[int]]) -> list[list[set[int]]]:
    """Compute candidate sets for every cell based on row/col/box constraints."""
    candidates = [[set() for _ in range(9)] for _ in range(9)]

    for r in range(9):
        for c in range(9):
            if grid[r][c] != 0:
                continue
            used = set()
            # Row
            for cc in range(9):
                if grid[r][cc]:
                    used.add(grid[r][cc])
            # Col
            for rr in range(9):
                if grid[rr][c]:
                    used.add(grid[rr][c])
            # Box
            br, bc = (r // 3) * 3, (c // 3) * 3
            for rr in range(br, br + 3):
                for cc in range(bc, bc + 3):
                    if grid[rr][cc]:
                        used.add(grid[rr][cc])
            candidates[r][c] = {d for d in range(1, 10) if d not in used}

    return candidates


def get_row_cells(r: int) -> list[tuple[int, int]]:
    return [(r, c) for c in range(9)]

def get_col_cells(c: int) -> list[tuple[int, int]]:
    return [(r, c) for r in range(9)]

def get_box_cells(box: int) -> list[tuple[int, int]]:
    br, bc = (box // 3) * 3, (box % 3) * 3
    return [(br + dr, bc + dc) for dr in range(3) for dc in range(3)]

def cell_box(r: int, c: int) -> int:
    return (r // 3) * 3 + c // 3

def all_units() -> list[tuple[str, list[tuple[int, int]]]]:
    """Return all 27 units (9 rows, 9 cols, 9 boxes) with labels."""
    units = []
    for r in range(9):
        units.append((f"Row {r + 1}", get_row_cells(r)))
    for c in range(9):
        units.append((f"Column {c + 1}", get_col_cells(c)))
    for b in range(9):
        units.append((f"Box {b + 1}", get_box_cells(b)))
    return units


# -- Technique Detectors --
# Each returns a TechniqueResult or None.
# They are called in order of difficulty; first match wins.

def find_naked_single(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Cell with exactly one candidate."""
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0 and len(candidates[r][c]) == 1:
                digit = next(iter(candidates[r][c]))
                return TechniqueResult(
                    technique_name="Naked Single",
                    technique_id="naked_single",
                    tier="beginner",
                    affected_cells=[[r, c]],
                    eliminations=[{"cell": [r, c], "digit": digit}],
                    explanation_context=(
                        f"R{r+1}C{c+1} has only one possible candidate: {digit}. "
                        f"All other digits are eliminated by the row, column, and box constraints."
                    ),
                )
    return None


def find_hidden_single(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Digit that can only go in one cell within a unit."""
    for unit_name, cells in all_units():
        for digit in range(1, 10):
            # Find cells in this unit where digit is a candidate
            positions = [(r, c) for r, c in cells if digit in candidates[r][c]]
            if len(positions) == 1:
                r, c = positions[0]
                return TechniqueResult(
                    technique_name="Hidden Single",
                    technique_id="hidden_single",
                    tier="beginner",
                    affected_cells=[[r, c]],
                    eliminations=[{"cell": [r, c], "digit": digit}],
                    explanation_context=(
                        f"In {unit_name}, the digit {digit} can only go in R{r+1}C{c+1}. "
                        f"No other cell in this unit has {digit} as a candidate."
                    ),
                )
    return None


# -- Intermediate Techniques --

def find_naked_pair(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Two cells in a unit with the same two candidates."""
    for unit_name, cells in all_units():
        # Get empty cells with exactly 2 candidates
        pairs = [(r, c) for r, c in cells if grid[r][c] == 0 and len(candidates[r][c]) == 2]
        for i in range(len(pairs)):
            for j in range(i + 1, len(pairs)):
                r1, c1 = pairs[i]
                r2, c2 = pairs[j]
                if candidates[r1][c1] == candidates[r2][c2]:
                    pair_digits = candidates[r1][c1]
                    # Check if there are eliminations in other cells
                    elims = []
                    for r, c in cells:
                        if (r, c) != (r1, c1) and (r, c) != (r2, c2) and grid[r][c] == 0:
                            for d in pair_digits:
                                if d in candidates[r][c]:
                                    elims.append({"cell": [r, c], "digit": d})
                    if elims:
                        digits = sorted(pair_digits)
                        return TechniqueResult(
                            technique_name="Naked Pair",
                            technique_id="naked_pair",
                            tier="intermediate",
                            affected_cells=[[r1, c1], [r2, c2]],
                            eliminations=elims,
                            explanation_context=(
                                f"In {unit_name}, R{r1+1}C{c1+1} and R{r2+1}C{c2+1} "
                                f"both have only candidates {{{digits[0]}, {digits[1]}}}. "
                                f"These digits can be eliminated from other cells in the unit."
                            ),
                        )
    return None


def find_naked_triple(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Three cells in a unit whose combined candidates form a set of exactly 3 digits."""
    from itertools import combinations

    for unit_name, cells in all_units():
        empties = [(r, c) for r, c in cells if grid[r][c] == 0 and 1 <= len(candidates[r][c]) <= 3]
        for combo in combinations(empties, 3):
            union = set()
            for r, c in combo:
                union |= candidates[r][c]
            if len(union) == 3:
                elims = []
                combo_set = set(combo)
                for r, c in cells:
                    if (r, c) not in combo_set and grid[r][c] == 0:
                        for d in union:
                            if d in candidates[r][c]:
                                elims.append({"cell": [r, c], "digit": d})
                if elims:
                    digits = sorted(union)
                    cell_strs = [f"R{r+1}C{c+1}" for r, c in combo]
                    return TechniqueResult(
                        technique_name="Naked Triple",
                        technique_id="naked_triple",
                        tier="intermediate",
                        affected_cells=[[r, c] for r, c in combo],
                        eliminations=elims,
                        explanation_context=(
                            f"In {unit_name}, {', '.join(cell_strs)} together contain "
                            f"only candidates {{{', '.join(map(str, digits))}}}. "
                            f"These digits can be eliminated from other cells in the unit."
                        ),
                    )
    return None


def find_hidden_pair(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Two digits that only appear in the same two cells in a unit."""
    from itertools import combinations

    for unit_name, cells in all_units():
        # Map digit → cells where it appears
        digit_cells: dict[int, list[tuple[int, int]]] = {}
        for r, c in cells:
            if grid[r][c] == 0:
                for d in candidates[r][c]:
                    digit_cells.setdefault(d, []).append((r, c))

        # Find two digits that appear in exactly the same two cells
        digits_in_two = [(d, set(cs)) for d, cs in digit_cells.items() if len(cs) == 2]
        for i in range(len(digits_in_two)):
            for j in range(i + 1, len(digits_in_two)):
                d1, cells1 = digits_in_two[i]
                d2, cells2 = digits_in_two[j]
                if cells1 == cells2:
                    pair_digits = {d1, d2}
                    elims = []
                    for r, c in cells1:
                        for d in candidates[r][c]:
                            if d not in pair_digits:
                                elims.append({"cell": [r, c], "digit": d})
                    if elims:
                        cell_list = sorted(cells1)
                        cell_strs = [f"R{r+1}C{c+1}" for r, c in cell_list]
                        return TechniqueResult(
                            technique_name="Hidden Pair",
                            technique_id="hidden_pair",
                            tier="intermediate",
                            affected_cells=[[r, c] for r, c in cell_list],
                            eliminations=elims,
                            explanation_context=(
                                f"In {unit_name}, digits {d1} and {d2} only appear in "
                                f"{cell_strs[0]} and {cell_strs[1]}. Other candidates "
                                f"can be eliminated from these cells."
                            ),
                        )
    return None


def find_hidden_triple(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Three digits that only appear in the same three cells in a unit."""
    from itertools import combinations

    for unit_name, cells in all_units():
        digit_cells: dict[int, set[tuple[int, int]]] = {}
        for r, c in cells:
            if grid[r][c] == 0:
                for d in candidates[r][c]:
                    digit_cells.setdefault(d, set()).add((r, c))

        # Find three digits whose combined cells form exactly 3 cells
        digit_list = [(d, cs) for d, cs in digit_cells.items() if 1 <= len(cs) <= 3]
        for combo in combinations(digit_list, 3):
            combined_cells = set()
            for _, cs in combo:
                combined_cells |= cs
            if len(combined_cells) == 3:
                triple_digits = {d for d, _ in combo}
                elims = []
                for r, c in combined_cells:
                    for d in candidates[r][c]:
                        if d not in triple_digits:
                            elims.append({"cell": [r, c], "digit": d})
                if elims:
                    cell_list = sorted(combined_cells)
                    cell_strs = [f"R{r+1}C{c+1}" for r, c in cell_list]
                    digits_str = ", ".join(str(d) for d in sorted(triple_digits))
                    return TechniqueResult(
                        technique_name="Hidden Triple",
                        technique_id="hidden_triple",
                        tier="intermediate",
                        affected_cells=[[r, c] for r, c in cell_list],
                        eliminations=elims,
                        explanation_context=(
                            f"In {unit_name}, digits {digits_str} only appear in "
                            f"{', '.join(cell_strs)}. Other candidates can be eliminated "
                            f"from these cells."
                        ),
                    )
    return None


def find_pointing_pair(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Candidates in a box restricted to one row or column → eliminate from rest of that row/col."""
    for box in range(9):
        box_cells = get_box_cells(box)
        digit_cells: dict[int, list[tuple[int, int]]] = {}
        for r, c in box_cells:
            if grid[r][c] == 0:
                for d in candidates[r][c]:
                    digit_cells.setdefault(d, []).append((r, c))

        for digit, cells in digit_cells.items():
            if len(cells) < 2:
                continue

            rows = {r for r, c in cells}
            cols = {c for r, c in cells}

            # All in one row?
            if len(rows) == 1:
                row = next(iter(rows))
                elims = []
                for c in range(9):
                    if (row, c) not in set(cells) and digit in candidates[row][c]:
                        elims.append({"cell": [row, c], "digit": digit})
                if elims:
                    cell_strs = [f"R{r+1}C{c+1}" for r, c in cells]
                    return TechniqueResult(
                        technique_name="Pointing Pair",
                        technique_id="pointing_pair",
                        tier="intermediate",
                        affected_cells=[[r, c] for r, c in cells],
                        eliminations=elims,
                        explanation_context=(
                            f"In Box {box + 1}, digit {digit} only appears in Row {row + 1} "
                            f"({', '.join(cell_strs)}). It can be eliminated from the rest of Row {row + 1}."
                        ),
                    )

            # All in one column?
            if len(cols) == 1:
                col = next(iter(cols))
                elims = []
                for r in range(9):
                    if (r, col) not in set(cells) and digit in candidates[r][col]:
                        elims.append({"cell": [r, col], "digit": digit})
                if elims:
                    cell_strs = [f"R{r+1}C{c+1}" for r, c in cells]
                    return TechniqueResult(
                        technique_name="Pointing Pair",
                        technique_id="pointing_pair",
                        tier="intermediate",
                        affected_cells=[[r, c] for r, c in cells],
                        eliminations=elims,
                        explanation_context=(
                            f"In Box {box + 1}, digit {digit} only appears in Column {col + 1} "
                            f"({', '.join(cell_strs)}). It can be eliminated from the rest of Column {col + 1}."
                        ),
                    )
    return None


def find_box_line_reduction(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Candidates in a row/col within one box → eliminate from rest of that box."""
    # Check rows
    for r in range(9):
        digit_cols: dict[int, list[int]] = {}
        for c in range(9):
            if grid[r][c] == 0:
                for d in candidates[r][c]:
                    digit_cols.setdefault(d, []).append(c)

        for digit, cols in digit_cols.items():
            if len(cols) < 2:
                continue
            boxes = {c // 3 for c in cols}
            if len(boxes) == 1:
                # All in one box
                box_col = next(iter(boxes)) * 3
                box_row = (r // 3) * 3
                elims = []
                cells_set = {(r, c) for c in cols}
                for rr in range(box_row, box_row + 3):
                    for cc in range(box_col, box_col + 3):
                        if (rr, cc) not in cells_set and digit in candidates[rr][cc]:
                            elims.append({"cell": [rr, cc], "digit": digit})
                if elims:
                    box_num = (r // 3) * 3 + next(iter(boxes)) + 1
                    cell_strs = [f"R{r+1}C{c+1}" for c in cols]
                    return TechniqueResult(
                        technique_name="Box/Line Reduction",
                        technique_id="box_line_reduction",
                        tier="intermediate",
                        affected_cells=[[r, c] for c in cols],
                        eliminations=elims,
                        explanation_context=(
                            f"In Row {r + 1}, digit {digit} only appears in Box {box_num} "
                            f"({', '.join(cell_strs)}). It can be eliminated from other "
                            f"cells in Box {box_num}."
                        ),
                    )

    # Check columns
    for c in range(9):
        digit_rows: dict[int, list[int]] = {}
        for r in range(9):
            if grid[r][c] == 0:
                for d in candidates[r][c]:
                    digit_rows.setdefault(d, []).append(r)

        for digit, rows in digit_rows.items():
            if len(rows) < 2:
                continue
            boxes = {r // 3 for r in rows}
            if len(boxes) == 1:
                box_row = next(iter(boxes)) * 3
                box_col = (c // 3) * 3
                elims = []
                cells_set = {(r, c) for r in rows}
                for rr in range(box_row, box_row + 3):
                    for cc in range(box_col, box_col + 3):
                        if (rr, cc) not in cells_set and digit in candidates[rr][cc]:
                            elims.append({"cell": [rr, cc], "digit": digit})
                if elims:
                    box_num = next(iter(boxes)) * 3 + c // 3 + 1
                    cell_strs = [f"R{r+1}C{c+1}" for r in rows]
                    return TechniqueResult(
                        technique_name="Box/Line Reduction",
                        technique_id="box_line_reduction",
                        tier="intermediate",
                        affected_cells=[[r, c] for r in rows],
                        eliminations=elims,
                        explanation_context=(
                            f"In Column {c + 1}, digit {digit} only appears in Box {box_num} "
                            f"({', '.join(cell_strs)}). It can be eliminated from other "
                            f"cells in Box {box_num}."
                        ),
                    )
    return None


# -- Advanced Techniques --

def find_x_wing(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Digit in exactly two cells in two rows, same two columns (or transpose)."""
    # Row-based X-Wing
    for digit in range(1, 10):
        # Find rows where digit appears in exactly 2 columns
        row_cols: dict[int, list[int]] = {}
        for r in range(9):
            cols = [c for c in range(9) if digit in candidates[r][c]]
            if len(cols) == 2:
                row_cols[r] = cols

        rows = list(row_cols.keys())
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                r1, r2 = rows[i], rows[j]
                if row_cols[r1] == row_cols[r2]:
                    c1, c2 = row_cols[r1]
                    elims = []
                    for r in range(9):
                        if r != r1 and r != r2:
                            if digit in candidates[r][c1]:
                                elims.append({"cell": [r, c1], "digit": digit})
                            if digit in candidates[r][c2]:
                                elims.append({"cell": [r, c2], "digit": digit})
                    if elims:
                        return TechniqueResult(
                            technique_name="X-Wing",
                            technique_id="x_wing",
                            tier="advanced",
                            affected_cells=[[r1, c1], [r1, c2], [r2, c1], [r2, c2]],
                            eliminations=elims,
                            explanation_context=(
                                f"Digit {digit} forms an X-Wing in Rows {r1+1} and {r2+1}, "
                                f"Columns {c1+1} and {c2+1}. It can be eliminated from "
                                f"other cells in those columns."
                            ),
                        )

    # Column-based X-Wing
    for digit in range(1, 10):
        col_rows: dict[int, list[int]] = {}
        for c in range(9):
            rows_list = [r for r in range(9) if digit in candidates[r][c]]
            if len(rows_list) == 2:
                col_rows[c] = rows_list

        cols = list(col_rows.keys())
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                c1, c2 = cols[i], cols[j]
                if col_rows[c1] == col_rows[c2]:
                    r1, r2 = col_rows[c1]
                    elims = []
                    for c in range(9):
                        if c != c1 and c != c2:
                            if digit in candidates[r1][c]:
                                elims.append({"cell": [r1, c], "digit": digit})
                            if digit in candidates[r2][c]:
                                elims.append({"cell": [r2, c], "digit": digit})
                    if elims:
                        return TechniqueResult(
                            technique_name="X-Wing",
                            technique_id="x_wing",
                            tier="advanced",
                            affected_cells=[[r1, c1], [r1, c2], [r2, c1], [r2, c2]],
                            eliminations=elims,
                            explanation_context=(
                                f"Digit {digit} forms an X-Wing in Columns {c1+1} and {c2+1}, "
                                f"Rows {r1+1} and {r2+1}. It can be eliminated from "
                                f"other cells in those rows."
                            ),
                        )
    return None


def _find_fish(
    grid: list[list[int]], candidates: list[list[set[int]]],
    size: int, name: str, technique_id: str, tier: str,
) -> TechniqueResult | None:
    """Generalized fish pattern (Swordfish=3, Jellyfish=4)."""
    from itertools import combinations

    for digit in range(1, 10):
        # Row-based
        row_cols: dict[int, set[int]] = {}
        for r in range(9):
            cols = {c for c in range(9) if digit in candidates[r][c]}
            if 2 <= len(cols) <= size:
                row_cols[r] = cols

        if len(row_cols) >= size:
            for row_combo in combinations(row_cols.keys(), size):
                col_union = set()
                for r in row_combo:
                    col_union |= row_cols[r]
                if len(col_union) == size:
                    elims = []
                    affected = []
                    for r in row_combo:
                        for c in row_cols[r]:
                            affected.append([r, c])
                    for c in col_union:
                        for r in range(9):
                            if r not in row_combo and digit in candidates[r][c]:
                                elims.append({"cell": [r, c], "digit": digit})
                    if elims:
                        rows_str = ", ".join(str(r + 1) for r in row_combo)
                        cols_str = ", ".join(str(c + 1) for c in sorted(col_union))
                        return TechniqueResult(
                            technique_name=name,
                            technique_id=technique_id,
                            tier=tier,
                            affected_cells=affected,
                            eliminations=elims,
                            explanation_context=(
                                f"Digit {digit} forms a {name} in Rows {rows_str}, "
                                f"Columns {cols_str}. It can be eliminated from other "
                                f"cells in those columns."
                            ),
                        )

        # Column-based
        col_rows: dict[int, set[int]] = {}
        for c in range(9):
            rows_set = {r for r in range(9) if digit in candidates[r][c]}
            if 2 <= len(rows_set) <= size:
                col_rows[c] = rows_set

        if len(col_rows) >= size:
            for col_combo in combinations(col_rows.keys(), size):
                row_union = set()
                for c in col_combo:
                    row_union |= col_rows[c]
                if len(row_union) == size:
                    elims = []
                    affected = []
                    for c in col_combo:
                        for r in col_rows[c]:
                            affected.append([r, c])
                    for r in row_union:
                        for c in range(9):
                            if c not in col_combo and digit in candidates[r][c]:
                                elims.append({"cell": [r, c], "digit": digit})
                    if elims:
                        cols_str = ", ".join(str(c + 1) for c in col_combo)
                        rows_str = ", ".join(str(r + 1) for r in sorted(row_union))
                        return TechniqueResult(
                            technique_name=name,
                            technique_id=technique_id,
                            tier=tier,
                            affected_cells=affected,
                            eliminations=elims,
                            explanation_context=(
                                f"Digit {digit} forms a {name} in Columns {cols_str}, "
                                f"Rows {rows_str}. It can be eliminated from other "
                                f"cells in those rows."
                            ),
                        )
    return None


def find_swordfish(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    return _find_fish(grid, candidates, 3, "Swordfish", "swordfish", "advanced")


def find_xy_wing(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Three bivalue cells: pivot shares one digit with each wing, wings share the third."""
    def sees(r1, c1, r2, c2):
        return r1 == r2 or c1 == c2 or cell_box(r1, c1) == cell_box(r2, c2)

    bivalue = [(r, c) for r in range(9) for c in range(9)
               if grid[r][c] == 0 and len(candidates[r][c]) == 2]

    for pr, pc in bivalue:
        pivot = candidates[pr][pc]
        a, b = sorted(pivot)

        for wr1, wc1 in bivalue:
            if (wr1, wc1) == (pr, pc):
                continue
            if not sees(pr, pc, wr1, wc1):
                continue
            wing1 = candidates[wr1][wc1]
            # Wing1 must share exactly one digit with pivot
            shared1 = pivot & wing1
            if len(shared1) != 1:
                continue

            for wr2, wc2 in bivalue:
                if (wr2, wc2) in ((pr, pc), (wr1, wc1)):
                    continue
                if not sees(pr, pc, wr2, wc2):
                    continue
                wing2 = candidates[wr2][wc2]
                shared2 = pivot & wing2
                if len(shared2) != 1:
                    continue
                if shared1 == shared2:
                    continue  # Wings must share different digits with pivot

                # The elimination digit is the one shared between the wings (not the pivot)
                elim_digits = (wing1 & wing2) - pivot
                if len(elim_digits) != 1:
                    continue
                elim_digit = next(iter(elim_digits))

                # Eliminate from cells that see both wings
                elims = []
                for r in range(9):
                    for c in range(9):
                        if (r, c) in ((pr, pc), (wr1, wc1), (wr2, wc2)):
                            continue
                        if grid[r][c] != 0 and elim_digit not in candidates[r][c]:
                            continue
                        if grid[r][c] == 0 and elim_digit in candidates[r][c]:
                            if sees(r, c, wr1, wc1) and sees(r, c, wr2, wc2):
                                elims.append({"cell": [r, c], "digit": elim_digit})

                if elims:
                    return TechniqueResult(
                        technique_name="XY-Wing",
                        technique_id="xy_wing",
                        tier="advanced",
                        affected_cells=[[pr, pc], [wr1, wc1], [wr2, wc2]],
                        eliminations=elims,
                        explanation_context=(
                            f"XY-Wing with pivot at R{pr+1}C{pc+1} {{{a},{b}}}, "
                            f"wings at R{wr1+1}C{wc1+1} and R{wr2+1}C{wc2+1}. "
                            f"Digit {elim_digit} can be eliminated from cells that "
                            f"see both wings."
                        ),
                    )
    return None


def find_simple_coloring(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Chain-based coloring of a single digit to find eliminations."""
    def sees(r1, c1, r2, c2):
        return r1 == r2 or c1 == c2 or cell_box(r1, c1) == cell_box(r2, c2)

    for digit in range(1, 10):
        # Build conjugate pair graph: cells where digit appears exactly twice in a unit
        cells_with_digit = [(r, c) for r in range(9) for c in range(9)
                           if digit in candidates[r][c]]

        if len(cells_with_digit) < 2:
            continue

        # Build adjacency via conjugate pairs (two cells in a unit where digit appears only in those two)
        adj: dict[tuple[int, int], list[tuple[int, int]]] = {cell: [] for cell in cells_with_digit}
        for _, unit_cells in all_units():
            unit_digit_cells = [(r, c) for r, c in unit_cells if digit in candidates[r][c]]
            if len(unit_digit_cells) == 2:
                a, b = unit_digit_cells
                adj[a].append(b)
                adj[b].append(a)

        # Color connected components
        visited: dict[tuple[int, int], int] = {}
        for start in cells_with_digit:
            if start in visited:
                continue
            if not adj[start]:
                continue

            # BFS coloring
            queue = [start]
            visited[start] = 0
            color_groups: list[list[tuple[int, int]]] = [[], []]
            color_groups[0].append(start)

            while queue:
                cell = queue.pop(0)
                color = visited[cell]
                for neighbor in adj[cell]:
                    if neighbor not in visited:
                        visited[neighbor] = 1 - color
                        color_groups[1 - color].append(neighbor)
                        queue.append(neighbor)

            if len(color_groups[0]) < 1 or len(color_groups[1]) < 1:
                continue

            # Rule 2: if a cell sees both colors, eliminate digit from it
            all_colored = set(color_groups[0]) | set(color_groups[1])
            for r, c in cells_with_digit:
                if (r, c) in all_colored:
                    continue
                sees_0 = any(sees(r, c, cr, cc) for cr, cc in color_groups[0])
                sees_1 = any(sees(r, c, cr, cc) for cr, cc in color_groups[1])
                if sees_0 and sees_1:
                    affected = [[cr, cc] for cr, cc in color_groups[0] + color_groups[1]]
                    return TechniqueResult(
                        technique_name="Simple Coloring",
                        technique_id="simple_coloring",
                        tier="advanced",
                        affected_cells=affected,
                        eliminations=[{"cell": [r, c], "digit": digit}],
                        explanation_context=(
                            f"Using simple coloring on digit {digit}: R{r+1}C{c+1} "
                            f"can see cells of both colors in a conjugate chain. "
                            f"Digit {digit} can be eliminated from R{r+1}C{c+1}."
                        ),
                    )

            # Rule 4: two cells of the same color see each other → that color is false
            for color_idx in range(2):
                group = color_groups[color_idx]
                contradiction = False
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        if sees(group[i][0], group[i][1], group[j][0], group[j][1]):
                            contradiction = True
                            break
                    if contradiction:
                        break
                if contradiction:
                    # The other color is true — eliminate digit from cells that see all of other color
                    false_group = color_groups[color_idx]
                    elims = [{"cell": [r, c], "digit": digit} for r, c in false_group]
                    if elims:
                        affected = [[r, c] for r, c in color_groups[0] + color_groups[1]]
                        return TechniqueResult(
                            technique_name="Simple Coloring",
                            technique_id="simple_coloring",
                            tier="advanced",
                            affected_cells=affected,
                            eliminations=elims,
                            explanation_context=(
                                f"Using simple coloring on digit {digit}: two cells of the same "
                                f"color see each other, creating a contradiction. "
                                f"Digit {digit} can be eliminated from the contradicted color group."
                            ),
                        )
    return None


# -- Expert Techniques --

def find_jellyfish(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    return _find_fish(grid, candidates, 4, "Jellyfish", "jellyfish", "expert")


def find_unique_rectangle(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Detect Type 1 Unique Rectangle: avoid deadly pattern with multiple solutions."""
    from itertools import combinations

    # Find bivalue cells with same two candidates
    bivalue: dict[tuple[int, ...], list[tuple[int, int]]] = {}
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0 and len(candidates[r][c]) == 2:
                key = tuple(sorted(candidates[r][c]))
                bivalue.setdefault(key, []).append((r, c))

    for digits, cells in bivalue.items():
        if len(cells) < 3:
            continue
        # Look for 3 cells forming 3 corners of a rectangle
        for combo in combinations(cells, 3):
            rows = {r for r, c in combo}
            cols = {c for r, c in combo}
            if len(rows) != 2 or len(cols) != 2:
                continue
            # Find the missing corner
            all_corners = [(r, c) for r in rows for c in cols]
            missing = [cell for cell in all_corners if cell not in combo]
            if len(missing) != 1:
                continue
            mr, mc = missing[0]
            if grid[mr][mc] != 0:
                continue
            # The missing corner must contain the pair digits plus extras
            if not candidates[mr][mc].issuperset(set(digits)):
                continue
            if len(candidates[mr][mc]) <= 2:
                continue  # Would be a deadly pattern

            # Type 1: eliminate the pair digits from the missing corner
            elims = [{"cell": [mr, mc], "digit": d} for d in digits]
            cell_strs = [f"R{r+1}C{c+1}" for r, c in combo]
            return TechniqueResult(
                technique_name="Unique Rectangle (Type 1)",
                technique_id="unique_rectangle",
                tier="expert",
                affected_cells=[[r, c] for r, c in all_corners],
                eliminations=elims,
                explanation_context=(
                    f"Cells {', '.join(cell_strs)} form three corners of a Unique Rectangle "
                    f"with digits {{{digits[0]}, {digits[1]}}}. To avoid a deadly pattern "
                    f"(multiple solutions), digits {digits[0]} and {digits[1]} can be "
                    f"eliminated from R{mr+1}C{mc+1}."
                ),
            )
    return None


def find_xyz_wing(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Pivot has 3 candidates XYZ, two wings with XZ and YZ. Eliminate Z from cells seeing all three."""
    def sees(r1, c1, r2, c2):
        return r1 == r2 or c1 == c2 or cell_box(r1, c1) == cell_box(r2, c2)

    trivalue = [(r, c) for r in range(9) for c in range(9)
                if grid[r][c] == 0 and len(candidates[r][c]) == 3]
    bivalue = [(r, c) for r in range(9) for c in range(9)
               if grid[r][c] == 0 and len(candidates[r][c]) == 2]

    for pr, pc in trivalue:
        pivot = candidates[pr][pc]  # {X, Y, Z}
        for wr1, wc1 in bivalue:
            if (wr1, wc1) == (pr, pc) or not sees(pr, pc, wr1, wc1):
                continue
            wing1 = candidates[wr1][wc1]
            if not wing1.issubset(pivot) or len(wing1) != 2:
                continue

            for wr2, wc2 in bivalue:
                if (wr2, wc2) in ((pr, pc), (wr1, wc1)):
                    continue
                if not sees(pr, pc, wr2, wc2):
                    continue
                wing2 = candidates[wr2][wc2]
                if not wing2.issubset(pivot) or len(wing2) != 2:
                    continue
                if wing1 == wing2:
                    continue
                # Combined must cover all three pivot digits
                if wing1 | wing2 != pivot:
                    continue
                # Z is the digit shared by both wings
                z_digits = wing1 & wing2
                if len(z_digits) != 1:
                    continue
                z = next(iter(z_digits))

                # Eliminate Z from cells that see all three
                elims = []
                for r in range(9):
                    for c in range(9):
                        if (r, c) in ((pr, pc), (wr1, wc1), (wr2, wc2)):
                            continue
                        if grid[r][c] == 0 and z in candidates[r][c]:
                            if sees(r, c, pr, pc) and sees(r, c, wr1, wc1) and sees(r, c, wr2, wc2):
                                elims.append({"cell": [r, c], "digit": z})

                if elims:
                    return TechniqueResult(
                        technique_name="XYZ-Wing",
                        technique_id="xyz_wing",
                        tier="expert",
                        affected_cells=[[pr, pc], [wr1, wc1], [wr2, wc2]],
                        eliminations=elims,
                        explanation_context=(
                            f"XYZ-Wing: pivot R{pr+1}C{pc+1} {set(pivot)} with wings "
                            f"R{wr1+1}C{wc1+1} {set(wing1)} and R{wr2+1}C{wc2+1} {set(wing2)}. "
                            f"Digit {z} can be eliminated from cells seeing all three."
                        ),
                    )
    return None


def find_forcing_chain(
    grid: list[list[int]], candidates: list[list[set[int]]]
) -> TechniqueResult | None:
    """Simple forcing chain: if all candidates in a cell lead to the same conclusion."""
    def sees(r1, c1, r2, c2):
        return r1 == r2 or c1 == c2 or cell_box(r1, c1) == cell_box(r2, c2)

    def propagate(grid_copy, cands, r, c, digit):
        """Try placing digit at (r,c) and propagate naked singles. Returns set of deductions or None if contradiction."""
        deductions = set()
        deductions.add((r, c, digit))
        queue = [(r, c, digit)]

        while queue:
            pr, pc, pd = queue.pop(0)
            # Eliminate pd from all peers
            for rr in range(9):
                for cc in range(9):
                    if (rr, cc) == (pr, pc):
                        continue
                    if not sees(pr, pc, rr, cc):
                        continue
                    if pd in cands[rr][cc]:
                        cands[rr][cc] = cands[rr][cc] - {pd}
                        if len(cands[rr][cc]) == 0:
                            return None  # Contradiction
                        if len(cands[rr][cc]) == 1:
                            new_digit = next(iter(cands[rr][cc]))
                            if (rr, cc, new_digit) not in deductions:
                                deductions.add((rr, cc, new_digit))
                                queue.append((rr, cc, new_digit))
        return deductions

    # Find bivalue cells (simpler chains)
    bivalue = [(r, c) for r in range(9) for c in range(9)
               if grid[r][c] == 0 and len(candidates[r][c]) == 2]

    for r, c in bivalue:
        cands_list = list(candidates[r][c])
        results = []
        for digit in cands_list:
            import copy
            cands_copy = [[candidates[rr][cc].copy() for cc in range(9)] for rr in range(9)]
            deductions = propagate(grid, cands_copy, r, c, digit)
            results.append(deductions)

        if any(d is None for d in results):
            # One branch leads to contradiction — the other must be true
            valid_idx = 0 if results[0] is not None else 1
            digit = cands_list[valid_idx]
            return TechniqueResult(
                technique_name="Forcing Chain",
                technique_id="forcing_chain",
                tier="expert",
                affected_cells=[[r, c]],
                eliminations=[{"cell": [r, c], "digit": digit}],
                explanation_context=(
                    f"Forcing chain starting from R{r+1}C{c+1}: assuming "
                    f"{cands_list[1 - valid_idx]} leads to a contradiction. "
                    f"Therefore R{r+1}C{c+1} must be {digit}."
                ),
            )

        if results[0] is not None and results[1] is not None:
            # Both branches agree on some conclusion
            common = results[0] & results[1]
            for cr, cc, cd in common:
                if (cr, cc) != (r, c):
                    return TechniqueResult(
                        technique_name="Forcing Chain",
                        technique_id="forcing_chain",
                        tier="expert",
                        affected_cells=[[r, c], [cr, cc]],
                        eliminations=[{"cell": [cr, cc], "digit": cd}],
                        explanation_context=(
                            f"Forcing chain: both candidates in R{r+1}C{c+1} "
                            f"lead to R{cr+1}C{cc+1} = {cd}."
                        ),
                    )
    return None


# -- Main Solver Interface --

# Technique order: simplest first
TECHNIQUES = [
    # Beginner
    ("naked_single", find_naked_single),
    ("hidden_single", find_hidden_single),
    # Intermediate
    ("naked_pair", find_naked_pair),
    ("naked_triple", find_naked_triple),
    ("hidden_pair", find_hidden_pair),
    ("hidden_triple", find_hidden_triple),
    ("pointing_pair", find_pointing_pair),
    ("box_line_reduction", find_box_line_reduction),
    # Advanced
    ("x_wing", find_x_wing),
    ("swordfish", find_swordfish),
    ("xy_wing", find_xy_wing),
    ("simple_coloring", find_simple_coloring),
    # Expert
    ("jellyfish", find_jellyfish),
    ("unique_rectangle", find_unique_rectangle),
    ("xyz_wing", find_xyz_wing),
    ("forcing_chain", find_forcing_chain),
]

TIER_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2, "expert": 3}


def analyze(grid: list[list[int]], skill_profile: dict[str, bool] | None = None) -> TechniqueResult | None:
    """Find the simplest applicable technique for the current grid state.

    If skill_profile is provided, still searches all techniques but the caller
    can use the tier info to decide how to present the result.
    """
    candidates = get_candidates(grid)

    for technique_id, finder in TECHNIQUES:
        result = finder(grid, candidates)
        if result is not None:
            return result

    return None
