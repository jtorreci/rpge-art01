import math
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Any

# A base class for all ZDT problems to ensure a consistent interface.
class ZDT(ABC):
    """Abstract base class for ZDT problems."""
    def __init__(self, nvars: int, nobjs: int, types: List[Any]):
        self.nvars = nvars
        self.nobjs = nobjs
        self.types = types

    @abstractmethod
    def evaluate(self, solution: Any):
        """
        Evaluates a solution.

        This method must be implemented by each ZDT subclass. It takes a
        solution object and is expected to set the `objectives` attribute
        on it.

        Args:
            solution: An object with a `variables` attribute (list of floats).
        """
        pass

class ZDT1(ZDT):
    """
    Implementation of the ZDT1 benchmark problem.

    It is a 2-objective problem with 30 variables. The Pareto front is convex.
    """
    def __init__(self, nvars: int = 30):
        types = [(0.0, 1.0)] * nvars
        super().__init__(nvars, 2, types)

    def evaluate(self, solution: Any):
        x = solution.variables
        f1 = x[0]

        g = 1.0 + 9.0 * sum(x[1:]) / (self.nvars - 1)
        h = 1.0 - math.sqrt(f1 / g)
        f2 = g * h

        solution.objectives = [f1, f2]
        solution.constraint_violation = 0.0

class ZDT2(ZDT):
    """
    Implementation of the ZDT2 benchmark problem.

    A 2-objective problem with 30 variables. The Pareto front is non-convex.
    """
    def __init__(self, nvars: int = 30):
        types = [(0.0, 1.0)] * nvars
        super().__init__(nvars, 2, types)

    def evaluate(self, solution: Any):
        x = solution.variables
        f1 = x[0]

        g = 1.0 + 9.0 * sum(x[1:]) / (self.nvars - 1)
        h = 1.0 - (f1 / g)**2
        f2 = g * h

        solution.objectives = [f1, f2]
        solution.constraint_violation = 0.0

class ZDT3(ZDT):
    """
    Implementation of the ZDT3 benchmark problem.

    A 2-objective problem with 30 variables. The Pareto front is disconnected.
    """
    def __init__(self, nvars: int = 30):
        types = [(0.0, 1.0)] * nvars
        super().__init__(nvars, 2, types)

    def evaluate(self, solution: Any):
        x = solution.variables
        f1 = x[0]

        g = 1.0 + 9.0 * sum(x[1:]) / (self.nvars - 1)
        h = 1.0 - math.sqrt(f1 / g) - (f1 / g) * math.sin(10 * math.pi * f1)
        f2 = g * h

        solution.objectives = [f1, f2]
        solution.constraint_violation = 0.0

class ZDT4(ZDT):
    """
    Implementation of the ZDT4 benchmark problem.

    A 2-objective problem with 10 variables. It has many local Pareto fronts,
    making it difficult for algorithms to converge to the true global front.
    """
    def __init__(self, nvars: int = 10):
        types = [(0.0, 1.0)] + [(-5.0, 5.0)] * (nvars - 1)
        super().__init__(nvars, 2, types)

    def evaluate(self, solution: Any):
        x = solution.variables
        f1 = x[0]

        g_sum = sum(xi**2 - 10.0 * math.cos(4.0 * math.pi * xi) for xi in x[1:])
        g = 1.0 + 10.0 * (self.nvars - 1) + g_sum
        h = 1.0 - math.sqrt(f1 / g)
        f2 = g * h

        solution.objectives = [f1, f2]
        solution.constraint_violation = 0.0

class ZDT6(ZDT):
    """
    Implementation of the ZDT6 benchmark problem.

    A 2-objective problem with 10 variables. The Pareto front is non-convex
    and the density of solutions is non-uniform along the front.
    """
    def __init__(self, nvars: int = 10):
        types = [(0.0, 1.0)] * nvars
        super().__init__(nvars, 2, types)

    def evaluate(self, solution: Any):
        x = solution.variables
        f1 = 1.0 - math.exp(-4.0 * x[0]) * (math.sin(6.0 * math.pi * x[0])**6)

        g = 1.0 + 9.0 * (sum(x[1:]) / (self.nvars - 1))**0.25
        h = 1.0 - (f1 / g)**2
        f2 = g * h

        solution.objectives = [f1, f2]
        solution.constraint_violation = 0.0


# --- Theoretical Pareto Front Generators ---

def get_zdt1_pareto_front(n_points: int = 100) -> List[List[float]]:
    """Generates the theoretical Pareto front for ZDT1."""
    f1 = np.linspace(0, 1, n_points)
    f2 = 1 - np.sqrt(f1)
    return np.column_stack((f1, f2)).tolist()

def get_zdt2_pareto_front(n_points: int = 100) -> List[List[float]]:
    """Generates the theoretical Pareto front for ZDT2."""
    f1 = np.linspace(0, 1, n_points)
    f2 = 1 - f1**2
    return np.column_stack((f1, f2)).tolist()

def get_zdt3_pareto_front(n_points: int = 100) -> List[List[float]]:
    """Generates the theoretical Pareto front for ZDT3."""
    f1 = np.linspace(0, 1, n_points)
    f2 = 1 - np.sqrt(f1) - f1 * np.sin(10 * np.pi * f1)
    return np.column_stack((f1, f2)).tolist()

# Note: ZDT4 and ZDT6 fronts are similar to ZDT1 and ZDT2 respectively
# for g(x)=1, so we can reuse those generators for plotting reference.

def get_zdt4_pareto_front(n_points: int = 100) -> List[List[float]]:
    """Generates the theoretical Pareto front for ZDT4."""
    # The theoretical front for ZDT4 corresponds to g(x)=1
    return get_zdt1_pareto_front(n_points)

def get_zdt6_pareto_front(n_points: int = 100) -> List[List[float]]:
    """Generates the theoretical Pareto front for ZDT6."""
    # The theoretical front for ZDT6 has f2 = 1 - f1^2
    f1 = np.linspace(0, 1, n_points)
    f2 = 1 - f1**2
    # However, the range of f1 for ZDT6 is not [0, 1].
    # f1 = 1 - exp(-4x1)sin(6pi*x1)^6. The range is approx [0.28, 1].
    # For simplicity in plotting, we generate points across the full [0,1] range.
    return np.column_stack((f1, f2)).tolist()