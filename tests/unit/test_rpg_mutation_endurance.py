"""
Tests del mecanismo de estabilidad por Endurance en variación (D1->B).

Formalismo: la selección es fitness-pura y END actúa dentro de la VARIACIÓN.
Cuando la presión de selección es alta (proxy: generaciones de estancamiento
normalizadas, `pressure` en [0,1] pasado por el algoritmo):

- individuos con END alta conservan pasos compuestos (sigma estable),
- individuos con END baja reciben pasos amplificados/erráticos.

Sigma efectivo se escala por: 1 + pressure * (1 - estabilidad) * amplificacion
con estabilidad = endurance_normalizada * 0.8.
"""
import inspect

import pytest


class OneVarProblem:
    """Problema determinista de una variable: x -> [x, 10 - x]."""

    nvars = 1
    nobjs = 2
    nconstrs = 0
    types = [(0.0, 10.0)]
    directions = [-1, -1]

    def evaluate(self, solution):
        x = solution.variables[0]
        solution.objectives = [x, 10.0 - x]
        solution.constraint_violation = 0.0
        solution.evaluated = True


def make_end_dominant(problem, endurance, other=20.0):
    """Crear solución con endurance dominante (el resto de atributos igual)."""
    from core.rpg_solution import RPGSolution

    sol = RPGSolution(problem)
    sol.strength = other
    sol.wisdom = other
    sol.endurance = endurance
    sol.dexterity = other
    sol.luck = other
    sol.variables = [5.0]
    problem.evaluate(sol)
    return sol


def mean_abs_step(solution, mutate_fn, trials=80):
    """Magnitud media de mutación (paso efectivo) sobre varios intentos."""
    total = 0.0
    for _ in range(trials):
        offspring = mutate_fn(solution)
        total += abs(offspring.variables[0] - solution.variables[0])
    return total / trials


# ============================================================================
# ESTABILIDAD DE ENDURANCE (core/rpg_attributes.py)
# ============================================================================

class TestEnduranceStability:
    """estabilidad = endurance normalizada * 0.8 (patrón lineal existente)."""

    def test_stability_at_minimum_is_zero(self):
        from core.rpg_attributes import get_endurance_stability

        assert get_endurance_stability(20) == 0.0

    def test_stability_at_maximum_is_point_eight(self):
        from core.rpg_attributes import get_endurance_stability

        assert get_endurance_stability(100) == pytest.approx(0.8)

    def test_stability_is_monotonic(self):
        from core.rpg_attributes import get_endurance_stability

        values = [get_endurance_stability(e) for e in range(20, 101, 10)]

        assert values == sorted(values)


# ============================================================================
# FACTOR DE AMORTIGUACIÓN (operators/rpg_mutation.py)
# ============================================================================

class TestEnduranceDampingFactor:
    """sigma_efectivo = sigma * (1 + pressure * (1 - estabilidad) * amplif)."""

    def test_zero_pressure_is_identity_for_any_endurance(self):
        from operators.rpg_mutation import endurance_damping_factor

        for endurance in (20, 50, 100):
            assert endurance_damping_factor(endurance, pressure=0.0) == 1.0

    def test_high_pressure_low_endurance_max_amplification(self):
        from operators.rpg_mutation import endurance_damping_factor

        # END=20 -> estabilidad 0.0 -> factor = 1 + 1*(1-0)*2 = 3.0
        assert endurance_damping_factor(20, pressure=1.0) == pytest.approx(3.0)

    def test_high_pressure_high_endurance_composed_steps(self):
        from operators.rpg_mutation import endurance_damping_factor

        # END=100 -> estabilidad 0.8 -> factor = 1 + 1*(1-0.8)*2 = 1.4
        assert endurance_damping_factor(100, pressure=1.0) == pytest.approx(1.4)

    def test_factor_grows_with_pressure(self):
        from operators.rpg_mutation import endurance_damping_factor

        factors = [endurance_damping_factor(30, pressure=p / 10)
                   for p in range(11)]

        assert factors == sorted(factors)


# ============================================================================
# PASOS EFECTIVOS: END BAJA > END ALTA BAJO PRESIÓN
# ============================================================================

class TestEffectiveStepSizes:
    """Bajo presión alta, END baja produce pasos efectivos mayores."""

    def test_low_end_larger_steps_than_high_end_at_full_pressure(self):
        from operators.rpg_mutation import endurance_stability_mutation

        problem = OneVarProblem()
        low_end = make_end_dominant(problem, endurance=25.0)
        high_end = make_end_dominant(problem, endurance=95.0)

        # 400 trials: con el gate de mutación (0.3) y trials chicos la
        # separación entre medias no alcanza significancia estadística
        # estable (flaky ~3%); con 400 el gap es >4 sigma.
        mean_low = mean_abs_step(
            low_end,
            lambda s: endurance_stability_mutation(s, problem, pressure=1.0),
            trials=400)
        mean_high = mean_abs_step(
            high_end,
            lambda s: endurance_stability_mutation(s, problem, pressure=1.0),
            trials=400)

        assert mean_low > mean_high

    def test_rpg_mutate_end_branch_uses_damping_in_variation_mode(self):
        """La rama END-dominante usa el amortiguado explícito en variation:
        con END baja y presión alta produce pasos mayores que el fallback
        silencioso (adaptativa sin amortiguar) del modo legacy."""
        from operators.rpg_mutation import rpg_mutate

        problem = OneVarProblem()
        low_end = make_end_dominant(problem, endurance=25.0)

        mean_variation = mean_abs_step(
            low_end,
            lambda s: rpg_mutate(s, problem, pressure=1.0,
                                 endurance_mode='variation'))
        mean_legacy = mean_abs_step(
            low_end,
            lambda s: rpg_mutate(s, problem, pressure=1.0,
                                 endurance_mode='selection'))

        assert mean_variation > mean_legacy


# ============================================================================
# API DE RPG_MUTATE: DEFAULT, VALIDACIÓN
# ============================================================================

class TestRpgMutateEnduranceModeApi:
    """rpg_mutate acepta pressure y endurance_mode con defaults del
    formalismo."""

    def test_default_endurance_mode_is_variation(self):
        from operators.rpg_mutation import rpg_mutate

        params = inspect.signature(rpg_mutate).parameters

        assert 'endurance_mode' in params
        assert params['endurance_mode'].default == 'variation'

    def test_default_pressure_is_zero(self):
        from operators.rpg_mutation import rpg_mutate

        params = inspect.signature(rpg_mutate).parameters

        assert 'pressure' in params
        assert params['pressure'].default == 0.0

    def test_invalid_endurance_mode_raises(self):
        from operators.rpg_mutation import rpg_mutate

        problem = OneVarProblem()
        sol = make_end_dominant(problem, endurance=50.0)

        with pytest.raises(ValueError):
            rpg_mutate(sol, problem, endurance_mode='bogus')

    def test_end_dominant_variation_returns_valid_offspring(self):
        from operators.rpg_mutation import rpg_mutate

        problem = OneVarProblem()
        sol = make_end_dominant(problem, endurance=95.0)

        offspring = rpg_mutate(sol, problem, pressure=1.0,
                               endurance_mode='variation')

        assert offspring is not sol
        assert 0.0 <= offspring.variables[0] <= 10.0
        assert offspring.evaluated is False
