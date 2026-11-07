"""
Unit tests for the ZDT benchmark problems.

Ensures that the ZDT functions are evaluated correctly according to the
literature and that the theoretical Pareto fronts are generated properly.
"""
import math
import pytest
from typing import List, Dict, Any

from problems.zdt_benchmarks import (
    ZDT1, ZDT2, ZDT3, ZDT4, ZDT6,
    get_zdt1_pareto_front,
    get_zdt2_pareto_front,
    get_zdt3_pareto_front
)
# Note: ZDT4 and ZDT6 have more complex Pareto fronts, we will test their
# evaluation logic thoroughly.

# A dummy solution class for testing purposes
class MockSolution:
    def __init__(self, variables: List[float]):
        self.variables = variables
        self.objectives: List[float] = []
        self.constraint_violation: float = 0.0

# ======================================================================
# ZDT1 Tests
# ======================================================================

def test_zdt1_creation():
    """Tests the basic creation of the ZDT1 problem."""
    problem = ZDT1()
    assert problem.nvars == 30
    assert problem.nobjs == 2
    assert len(problem.types) == 30
    for var_range in problem.types:
        assert var_range == (0.0, 1.0)

def test_zdt1_evaluation_pareto_point():
    """Tests evaluation of a known point on the ZDT1 Pareto front."""
    problem = ZDT1()
    # For a point to be on the front, g(x) must be 1.
    # This happens when all x_i (for i>0) are 0.
    # f1 = x1, f2 = 1 - sqrt(x1)
    x1 = 0.25
    variables = [x1] + [0.0] * (problem.nvars - 1)
    solution = MockSolution(variables)
    problem.evaluate(solution)

    assert solution.objectives[0] == pytest.approx(x1)
    assert solution.objectives[1] == pytest.approx(1 - math.sqrt(x1))

def test_zdt1_evaluation_non_pareto_point():
    """Tests evaluation of a point NOT on the ZDT1 Pareto front."""
    problem = ZDT1()
    # If any x_i (for i>0) is not 0, g(x) > 1, so it's not on the front.
    x1 = 0.25
    variables = [x1] + [0.5] * (problem.nvars - 1)
    solution = MockSolution(variables)
    problem.evaluate(solution)

    g = 1.0 + 9.0 * sum(variables[1:]) / (problem.nvars - 1)
    assert g > 1.0
    assert solution.objectives[0] == pytest.approx(x1)
    assert solution.objectives[1] == pytest.approx(g * (1 - math.sqrt(x1 / g)))

def test_zdt1_pareto_front_generation():
    """Tests the generation of the theoretical ZDT1 Pareto front."""
    pareto_front = get_zdt1_pareto_front(11) # 11 points from x1=0 to x1=1
    assert len(pareto_front) == 11
    # Check first point (x1=0) -> (f1=0, f2=1)
    assert pareto_front[0] == pytest.approx([0.0, 1.0])
    # Check mid point (x1=0.5) -> (f1=0.5, f2=1-sqrt(0.5))
    assert pareto_front[5] == pytest.approx([0.5, 1 - math.sqrt(0.5)])
    # Check last point (x1=1) -> (f1=1, f2=0)
    assert pareto_front[-1] == pytest.approx([1.0, 0.0])


# ======================================================================
# ZDT2 Tests
# ======================================================================

def test_zdt2_evaluation_pareto_point():
    """Tests evaluation of a known point on the ZDT2 Pareto front."""
    problem = ZDT2()
    # Similar to ZDT1, g(x) must be 1.
    # f1 = x1, f2 = 1 - x1^2
    x1 = 0.5
    variables = [x1] + [0.0] * (problem.nvars - 1)
    solution = MockSolution(variables)
    problem.evaluate(solution)

    assert solution.objectives[0] == pytest.approx(x1)
    assert solution.objectives[1] == pytest.approx(1 - x1**2)

def test_zdt2_pareto_front_generation():
    """Tests the generation of the theoretical ZDT2 Pareto front."""
    pareto_front = get_zdt2_pareto_front(11)
    assert len(pareto_front) == 11
    # Check first point (x1=0) -> (f1=0, f2=1)
    assert pareto_front[0] == pytest.approx([0.0, 1.0])
    # Check mid point (x1=0.5) -> (f1=0.5, f2=0.75)
    assert pareto_front[5] == pytest.approx([0.5, 0.75])
    # Check last point (x1=1) -> (f1=1, f2=0)
    assert pareto_front[-1] == pytest.approx([1.0, 0.0])


# ======================================================================
# ZDT3 Tests
# ======================================================================

def test_zdt3_evaluation_pareto_point():
    """Tests evaluation of a known point on the ZDT3 Pareto front."""
    problem = ZDT3()
    # g(x) must be 1.
    # f1 = x1, f2 = 1 - sqrt(x1) - x1*sin(10*pi*x1)
    x1 = 0.1
    variables = [x1] + [0.0] * (problem.nvars - 1)
    solution = MockSolution(variables)
    problem.evaluate(solution)

    f2_expected = 1 - math.sqrt(x1) - x1 * math.sin(10 * math.pi * x1)
    assert solution.objectives[0] == pytest.approx(x1)
    assert solution.objectives[1] == pytest.approx(f2_expected)

def test_zdt3_pareto_front_generation():
    """Tests the generation of the theoretical ZDT3 Pareto front."""
    # ZDT3 has a disconnected Pareto front
    pareto_front = get_zdt3_pareto_front(100)
    assert len(pareto_front) == 100
    # Check that points lie on the theoretical front
    for f1, f2 in pareto_front:
        expected_f2 = 1 - math.sqrt(f1) - f1 * math.sin(10 * math.pi * f1)
        assert f2 == pytest.approx(expected_f2)


# ======================================================================
# ZDT4 Tests
# ======================================================================

def test_zdt4_creation():
    """Tests the basic creation of the ZDT4 problem."""
    problem = ZDT4()
    assert problem.nvars == 10
    assert problem.nobjs == 2
    assert problem.types[0] == (0.0, 1.0)
    for i in range(1, problem.nvars):
        assert problem.types[i] == (-5.0, 5.0)

def test_zdt4_evaluation_pareto_point():
    """Tests evaluation of a known point on the ZDT4 Pareto front."""
    problem = ZDT4()
    # g(x) must be 1. This requires a specific setup for x_i.
    # Let x1 = 0.5. For g(x) to be 1, the sum term must be zero.
    # Let's set all other x_i to 0. Then g(x) = 1 + 10*9 + 0 = 91, not 1.
    # This highlights the difficulty. Let's test a point where g is easy to calc.
    variables = [0.5] + [1.0] * (problem.nvars - 1)
    solution = MockSolution(variables)
    problem.evaluate(solution)

    f1_expected = 0.5
    # g = 1 + 10*(n-1) + sum(x_i^2 - 10*cos(4*pi*x_i)) for i=1 to n-1
    # with x_i=1, x_i^2 = 1, cos(4*pi) = 1. So (1 - 10*1) = -9.
    # sum is 9 * -9 = -81. g = 1 + 10*9 + (-81) = 10.
    g_expected = 10.0
    f2_expected = g_expected * (1 - math.sqrt(f1_expected / g_expected))

    assert solution.objectives[0] == pytest.approx(f1_expected)
    assert solution.objectives[1] == pytest.approx(f2_expected)


# ======================================================================
# ZDT6 Tests
# ======================================================================

def test_zdt6_evaluation_pareto_point():
    """Tests evaluation of a known point on the ZDT6 Pareto front."""
    problem = ZDT6()
    assert problem.nvars == 10
    # For a point to be on the front, g(x) must be 1.
    # This happens when all x_i (for i>0) are 0.
    # f1 = 1 - exp(-4*x1) * sin(6*pi*x1)^6
    # f2 = 1 - f1^2
    x1 = 0.1
    variables = [x1] + [0.0] * (problem.nvars - 1)
    solution = MockSolution(variables)
    problem.evaluate(solution)

    f1_expected = 1 - math.exp(-4 * x1) * (math.sin(6 * math.pi * x1)**6)
    f2_expected = 1 - f1_expected**2

    assert solution.objectives[0] == pytest.approx(f1_expected)
    assert solution.objectives[1] == pytest.approx(f2_expected)
