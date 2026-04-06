"""
Tests that verify the solver correctly detects each technique
using the curated test puzzles.
"""
import pytest

from app.solver import analyze
from tests.test_puzzles import TECHNIQUE_TEST_PUZZLES


ALL_TECHNIQUES = [
    "naked_single",
    "hidden_single",
    "naked_pair",
    "naked_triple",
    "hidden_pair",
    "hidden_triple",
    "pointing_pair",
    "box_line_reduction",
    "x_wing",
    "swordfish",
    "xy_wing",
    "simple_coloring",
    "jellyfish",
    "unique_rectangle",
    "xyz_wing",
    "forcing_chain",
]


def _analyze_case(case):
    """Run analyze() with optional user_eliminated from the test case."""
    grid = case["grid"]
    user_eliminated = case.get("user_eliminated")
    return analyze(grid, user_eliminated=user_eliminated)


@pytest.mark.parametrize("technique_id", ALL_TECHNIQUES)
def test_technique_detection(technique_id):
    """For each technique, verify the solver detects it as the first applicable technique."""
    assert technique_id in TECHNIQUE_TEST_PUZZLES, (
        f"No test puzzle defined for {technique_id}"
    )
    for i, case in enumerate(TECHNIQUE_TEST_PUZZLES[technique_id]):
        result = _analyze_case(case)

        assert result is not None, (
            f"Solver found no technique for {technique_id} case {i}"
        )
        assert result.technique_id == case["expected_technique"], (
            f"Expected {case['expected_technique']}, got {result.technique_id} "
            f"for {technique_id} case {i}"
        )


@pytest.mark.parametrize("technique_id", ALL_TECHNIQUES)
def test_technique_cells(technique_id):
    """Verify the solver identifies the correct affected cells."""
    for i, case in enumerate(TECHNIQUE_TEST_PUZZLES[technique_id]):
        result = _analyze_case(case)

        assert result is not None
        assert sorted(map(tuple, result.affected_cells)) == sorted(
            map(tuple, case["expected_cells"])
        ), (
            f"Expected cells {case['expected_cells']}, got {result.affected_cells} "
            f"for {technique_id} case {i}"
        )


@pytest.mark.parametrize("technique_id", ALL_TECHNIQUES)
def test_technique_eliminations(technique_id):
    """Verify the solver produces the correct eliminations."""
    for i, case in enumerate(TECHNIQUE_TEST_PUZZLES[technique_id]):
        result = _analyze_case(case)

        assert result is not None

        # Normalize for comparison
        def norm_elim(e):
            return (tuple(e["cell"]), e["digit"])

        expected = sorted(norm_elim(e) for e in case["expected_eliminations"])
        actual = sorted(norm_elim(e) for e in result.eliminations)

        assert actual == expected, (
            f"Expected eliminations {case['expected_eliminations']}, "
            f"got {result.eliminations} for {technique_id} case {i}"
        )
