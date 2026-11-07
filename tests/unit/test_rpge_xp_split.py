"""
Tests del reparto 50/50 de XP de mentoría (decisión congelada D2->C).

Cuando un offspring producido por P mejora la solución de P (evento de
mejora) o domina a P (evento de dominancia), el XP ganado se reparte:

    parent_share = total // 2
    offspring_share = total - parent_share

- P recibe su parte como crédito conductual (mentor).
- El offspring recibe su parte como crédito de valor.

El evento existente "offspring domina al padre" se conserva (canal de
dominancia). La XP de supervivencia, frente de Pareto y breeding NO cambia.
"""
import pytest


class SplitProblem:
    """Problema determinista con mapeo de objetivos inyectable.

    Por defecto: x -> [x, 10 - x] (minimización, objetivos en conflicto).
    """

    nvars = 1
    nobjs = 2
    nconstrs = 0
    types = [(0.0, 10.0)]
    directions = [-1, -1]

    def __init__(self, obj_fn=None):
        self.obj_fn = obj_fn or (lambda x: [x, 10.0 - x])

    def evaluate(self, solution):
        solution.objectives = list(self.obj_fn(solution.variables[0]))
        solution.constraint_violation = 0.0
        solution.evaluated = True


def stub_mutate_factory(x, created):
    """Crear un rpg_mutate falso que devuelve un offspring con variable x
    y registra cada offspring creado en la lista `created`."""

    def stub_mutate(parent, problem, pareto_front=None, give_xp=False,
                    pressure=0.0, endurance_mode='variation'):
        child = parent.copy()
        child.variables = [x]
        created.append(child)
        return child

    return stub_mutate


def build_solutions(problem, parent_x, filler_x=9.5):
    """Crear [padre, relleno] con atributos explícitos y objetivos evaluados.

    El padre gana ambos torneos (2 offspring en population_size=2), así que
    recibe exactamente 2 * 10 de XP de supervivencia.
    """
    from core.rpg_solution import RPGSolution

    parent = RPGSolution(problem)
    parent.strength = parent.wisdom = parent.endurance = 50.0
    parent.dexterity = parent.luck = 50.0
    parent.variables = [parent_x]
    problem.evaluate(parent)

    filler = RPGSolution(problem)
    filler.strength = filler.wisdom = filler.endurance = 20.0
    filler.dexterity = filler.luck = 20.0
    filler.variables = [filler_x]
    problem.evaluate(filler)

    return parent, filler


def build_and_evolve(monkeypatch, algorithm, parent_x, child_x, obj_fn=None):
    """Montar el algoritmo con mutación controlada y evolucionar 1 generación.

    Retorna (algo, parent, filler, child) donde child es el offspring.
    """
    assert algorithm == 'rpge'
    import algorithms.rpge as mod
    algo = mod.RPGE(SplitProblem(obj_fn), population_size=2)

    parent, filler = build_solutions(algo.problem, parent_x)
    algo.population = [parent, filler]

    created = []
    monkeypatch.setattr(mod, 'rpg_mutate', stub_mutate_factory(child_x, created))
    algo.evolve_generation()

    assert len(created) == 2  # un offspring por miembro de la población
    return algo, parent, filler, created[0]


# ============================================================================
# REPARTO EN RPGE
# ============================================================================

class TestRpgeXpSplit:
    """Mejora y dominancia se reparten 50/50 entre padre y offspring."""

    def test_improvement_even_split(self, monkeypatch):
        """Padre 5.0 -> hijo 0.0: mejora exacta del 100% (ratio 1.0).

        total = int(30 * (1 + 1.0)) = 60 -> padre 30, hijo 30.
        El padre además tiene 20 de supervivencia (2 torneos ganados).
        """
        algo, parent, filler, child = build_and_evolve(
            monkeypatch, 'rpge', parent_x=5.0, child_x=0.0)

        # Hijo: [0, 10] no domina a [5, 5] -> solo evento de mejora
        assert parent.xp == 20 + 30
        assert child.xp == 30

    def test_improvement_odd_split_offspring_gets_remainder(self, monkeypatch):
        """Padre 8.0 -> hijo 4.0: mejora del 50% (ratio 0.5, float exacto).

        total = int(30 * 1.5) = 45 -> padre 22 (floor), hijo 23 (resto).
        """
        algo, parent, filler, child = build_and_evolve(
            monkeypatch, 'rpge', parent_x=8.0, child_x=4.0)

        assert parent.xp == 20 + 22
        assert child.xp == 23

    def test_dominance_split(self, monkeypatch):
        """Hijo [5, 4] domina a padre [5, 5] sin mejora en obj0.

        total = 20 -> padre 10, hijo 10.
        """
        dominance_obj_fn = lambda x: [5.0, 10.0 - x]
        algo, parent, filler, child = build_and_evolve(
            monkeypatch, 'rpge', parent_x=5.0, child_x=6.0,
            obj_fn=dominance_obj_fn)

        assert parent.xp == 20 + 10
        assert child.xp == 10

    def test_no_event_offspring_gets_no_xp(self, monkeypatch):
        """Hijo peor (sin mejora ni dominancia): el padre solo cobra
        supervivencia (20) y el hijo no cobra nada."""
        algo, parent, filler, child = build_and_evolve(
            monkeypatch, 'rpge', parent_x=5.0, child_x=6.0)

        assert parent.xp == 20
        assert child.xp == 0

    def test_survival_xp_unchanged(self, monkeypatch):
        """La XP de supervivencia se paga igual al ganador del torneo
        (2 torneos x 10 XP al padre) en el modo por defecto."""
        algo, parent, filler, child = build_and_evolve(
            monkeypatch, 'rpge', parent_x=5.0, child_x=6.0)

        assert parent.xp == 20
        assert child.xp == 0


# ============================================================================
# PARETO XP SIN CAMBIOS
# ============================================================================

class TestParetoXpUnchanged:
    """La XP de frente de Pareto sigue siendo 50 por generación."""

    def test_pareto_front_xp_is_50_per_member(self):
        from algorithms.rpge import RPGE

        problem = SplitProblem()
        rpge = RPGE(problem, population_size=2)

        parent, filler = build_solutions(problem, parent_x=5.0, filler_x=6.0)
        rpge.population = [parent, filler]

        rpge.update_pareto_front()

        # [5, 5] y [6, 4] son mutuamente no dominadas: ambas en el frente
        assert len(rpge.pareto_front) == 2
        assert parent.xp == 50
        assert filler.xp == 50
