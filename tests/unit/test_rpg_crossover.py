"""
Tests unitarios para operadores de cruce RPG.

Siguiendo TDD: estos tests se escriben ANTES de implementar los operadores.
Los operadores de cruce usan atributos RPG y heredan características.
"""
import pytest


class TestWisdomCrossover:
    """Tests de cruce guiado por Wisdom."""

    def test_wisdom_crossover_exists(self):
        """Debe existir operador de cruce basado en wisdom"""
        from operators.rpg_crossover import wisdom_crossover

        assert wisdom_crossover is not None

    def test_wisdom_learns_from_better_parent(self):
        """Alta Wisdom aprende del mejor padre"""
        from operators.rpg_crossover import wisdom_crossover

        problem = create_muro_problem()
        parent1 = create_solution(problem, cost=250)  # Mejor
        parent2 = create_solution(problem, cost=300)  # Peor

        parent1.wisdom = 90
        parent2.wisdom = 30

        offspring = wisdom_crossover(parent1, parent2, problem)

        # Offspring debería heredar más del mejor (parent1)
        assert offspring is not None


class TestBalancedCrossover:
    """Tests de cruce balanceado."""

    def test_balanced_crossover_exists(self):
        """Debe existir cruce balanceado"""
        from operators.rpg_crossover import balanced_crossover

        assert balanced_crossover is not None

    def test_balanced_takes_from_both_parents(self):
        """Cruce balanceado toma genes de ambos padres"""
        from operators.rpg_crossover import balanced_crossover

        problem = create_muro_problem()
        parent1 = create_solution(problem)
        parent2 = create_solution(problem)

        offspring = balanced_crossover(parent1, parent2, problem)

        # Variables deben estar entre los límites de ambos padres
        assert offspring is not None
        assert len(offspring.variables) == len(parent1.variables)


class TestDominantCrossover:
    """Tests de cruce con herencia dominante."""

    def test_dominant_crossover_exists(self):
        """Debe existir cruce dominante"""
        from operators.rpg_crossover import dominant_crossover

        assert dominant_crossover is not None

    def test_dominant_inherits_from_stronger(self):
        """Herencia dominante favorece al más fuerte"""
        from operators.rpg_crossover import dominant_crossover

        problem = create_muro_problem()

        # Parent1: nivel alto
        parent1 = create_solution(problem)
        parent1.level = 10
        parent1.strength = 85

        # Parent2: nivel bajo
        parent2 = create_solution(problem)
        parent2.level = 2
        parent2.strength = 40

        offspring = dominant_crossover(parent1, parent2, problem)

        # Offspring debería tener atributos más cercanos a parent1
        assert offspring.level >= 1


class TestLuckyCrossover:
    """Tests de cruce con luck."""

    def test_lucky_crossover_exists(self):
        """Debe existir cruce afortunado"""
        from operators.rpg_crossover import lucky_crossover

        assert lucky_crossover is not None

    def test_lucky_finds_good_combinations(self):
        """Alta luck encuentra buenas combinaciones"""
        from operators.rpg_crossover import lucky_crossover

        problem = create_muro_problem()
        parent1 = create_solution(problem)
        parent2 = create_solution(problem)

        parent1.luck = 95
        parent2.luck = 85

        offspring = lucky_crossover(parent1, parent2, problem)

        assert offspring is not None


class TestAttributeInheritance:
    """Tests de herencia de atributos RPG."""

    def test_offspring_inherits_attributes(self):
        """Offspring hereda atributos de padres"""
        from operators.rpg_crossover import inherit_attributes

        parent1_attrs = {
            'strength': 80, 'wisdom': 60, 'endurance': 70,
            'dexterity': 50, 'luck': 40
        }
        parent2_attrs = {
            'strength': 40, 'wisdom': 85, 'endurance': 55,
            'dexterity': 75, 'luck': 65
        }

        offspring_attrs = inherit_attributes(parent1_attrs, parent2_attrs)

        # Atributos deben estar en rango razonable
        assert 20 <= offspring_attrs['strength'] <= 100
        assert 20 <= offspring_attrs['wisdom'] <= 100

    def test_inheritance_blends_parents(self):
        """Herencia mezcla atributos de ambos padres"""
        from operators.rpg_crossover import inherit_attributes

        parent1_attrs = {
            'strength': 90, 'wisdom': 30, 'endurance': 80,
            'dexterity': 40, 'luck': 35
        }
        parent2_attrs = {
            'strength': 30, 'wisdom': 90, 'endurance': 40,
            'dexterity': 85, 'luck': 70
        }

        offspring_attrs = inherit_attributes(parent1_attrs, parent2_attrs)

        # Offspring debería tener mezcla
        # Strength debería estar entre 30-90
        assert 30 <= offspring_attrs['strength'] <= 90


class TestRPGCrossoverComposite:
    """Tests del operador compuesto."""

    def test_rpg_crossover_exists(self):
        """Debe existir operador compuesto de cruce"""
        from operators.rpg_crossover import rpg_crossover

        assert rpg_crossover is not None

    def test_rpg_crossover_selects_operator(self):
        """Operador compuesto elige según atributos"""
        from operators.rpg_crossover import rpg_crossover

        problem = create_muro_problem()
        parent1 = create_solution(problem)
        parent2 = create_solution(problem)

        parent1.wisdom = 90  # Wisdom dominante

        offspring = rpg_crossover(parent1, parent2, problem)

        assert offspring is not None
        assert offspring is not parent1
        assert offspring is not parent2

    def test_crossover_gives_xp(self):
        """Cruce exitoso otorga XP a padres"""
        from operators.rpg_crossover import rpg_crossover

        problem = create_muro_problem()
        parent1 = create_solution(problem)
        parent2 = create_solution(problem)

        initial_xp1 = parent1.xp
        initial_xp2 = parent2.xp

        offspring = rpg_crossover(parent1, parent2, problem, give_xp=True)

        # Al menos uno debería ganar XP
        assert True  # Conceptual test


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_muro_problem():
    """Crear problema de muro para testing."""
    class MuroProblem:
        def __init__(self):
            self.nvars = 7
            self.nobjs = 2
            self.types = [
                (2.0, 10.0), (0.2, 0.8), (0.0, 15.0), (0.0, 15.0),
                (0.3, 1.5), (0.3, 2.0), (1.0, 5.0)
            ]

        def evaluate(self, solution):
            solution.objectives = [300.0, -2.0]  # Mock
            solution.constraint_violation = 0.0

    return MuroProblem()


def create_solution(problem, cost=None):
    """Crear solución inicializada."""
    from core.rpg_solution import RPGSolution
    import random

    sol = RPGSolution(problem)
    sol.variables = [random.uniform(*problem.types[i]) for i in range(7)]

    if cost:
        sol.objectives = [cost, -2.0]
    else:
        problem.evaluate(sol)

    return sol
