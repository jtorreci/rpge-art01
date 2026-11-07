"""
Tests del parámetro endurance_mode (decisión congelada D1->B).

Semántica congelada:
- "variation" (DEFAULT, formalismo de tesis): la selección es fitness-pura.
  END y combat_power NO influyen en la selección; END actúa solo dentro de
  la variación (estabilidad conductual, ver test_rpg_mutation_endurance.py).
- "selection" (legacy, variante pre-formalismo): preserva el comportamiento
  enviado originalmente: endurance*0.1 + combat_power*0.01 en el score de
  selección y desempates por combat_power en la selección ambiental híbrida.
"""
import pytest


class StubProblem:
    """Problema determinista mínimo compatible con los algoritmos.

    x -> [x, 10 - x] (minimización de ambos objetivos).
    """

    nvars = 1
    nobjs = 2
    nconstrs = 0
    types = [(0.0, 10.0)]
    directions = [-1, -1]  # platypus: minimizar ambos objetivos

    def evaluate(self, solution):
        x = solution.variables[0]
        solution.objectives = [x, 10.0 - x]
        solution.constraint_violation = 0.0
        solution.evaluated = True


def make_solution(problem, x, endurance=50.0, attribute_value=50.0, xp=0):
    """Crear solución con atributos explícitos y objetivos evaluados."""
    from core.rpg_solution import RPGSolution

    sol = RPGSolution(problem)
    sol.strength = attribute_value
    sol.wisdom = attribute_value
    sol.endurance = endurance
    sol.dexterity = attribute_value
    sol.luck = attribute_value
    sol.variables = [x]
    problem.evaluate(sol)
    if xp:
        sol.gain_xp(xp)
    return sol


def make_discriminating_pair(problem):
    """Par que discrimina ambos modos.

    good: mejor objetivo (obj0=2.0) pero END y combat_power mínimos.
    bad:  peor objetivo (obj0=3.0) pero END=100, todos los atributos a 100
          y nivel 3 (xp=500).

    En modo legacy el bonus de END (10.0) + combat_power (1.3) supera la
    diferencia de objetivo (1.0), así que 'bad' gana el torneo.
    En modo variation la selección es fitness-pura y gana 'good'.
    """
    good = make_solution(problem, x=2.0, endurance=20.0, attribute_value=20.0)
    bad = make_solution(problem, x=3.0, endurance=100.0,
                        attribute_value=100.0, xp=500)
    return good, bad


# ============================================================================
# CONSTRUCTOR: DEFAULT Y VALIDACIÓN
# ============================================================================

class TestEnduranceModeDefaultAndValidation:
    """Default 'variation' en los tres algoritmos y validación estricta."""

    def test_rpge_default_is_variation(self):
        from algorithms.rpge import RPGE

        rpge = RPGE(StubProblem(), population_size=5)

        assert rpge.endurance_mode == 'variation'

    def test_selection_mode_is_accepted(self):
        from algorithms.rpge import RPGE

        problem = StubProblem()

        assert RPGE(problem, endurance_mode='selection').endurance_mode == 'selection'

    def test_invalid_endurance_mode_raises(self):
        from algorithms.rpge import RPGE

        with pytest.raises(ValueError):
            RPGE(StubProblem(), endurance_mode='bogus')

# ============================================================================
# SELECCIÓN POR TORNEO: FITNESS-PURA VS LEGACY
# ============================================================================

class TestTournamentSelectionFitnessPure:
    """En variation el torneo ignora END y combat_power (solo objetivo)."""

    def test_rpge_variation_ignores_endurance_and_combat_power(self):
        from algorithms.rpge import RPGE

        problem = StubProblem()
        good, bad = make_discriminating_pair(problem)

        rpge = RPGE(problem, population_size=2, endurance_mode='variation')
        rpge.population = [good, bad]

        winner = rpge.tournament_selection()

        assert winner is good

    def test_rpge_selection_reproduces_legacy_scoring(self):
        from algorithms.rpge import RPGE

        problem = StubProblem()
        good, bad = make_discriminating_pair(problem)

        rpge = RPGE(problem, population_size=2, endurance_mode='selection')
        rpge.population = [good, bad]

        winner = rpge.tournament_selection()

        assert winner is bad

# ============================================================================
# SELECCIÓN AMBIENTAL HÍBRIDA: FITNESS-PURA VS COMBAT_POWER
# ============================================================================

