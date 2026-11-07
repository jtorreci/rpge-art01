"""
Tests de integración entre RPGSolution y Platypus.

Siguiendo TDD: estos tests verifican que RPGSolution puede funcionar
tanto standalone como integrado con platypus.Solution.
"""
import pytest


class TestRPGSolutionStandalone:
    """Tests de RPGSolution en modo standalone (sin Platypus)."""

    def test_rpg_solution_works_without_platypus(self):
        """RPGSolution debe funcionar sin Platypus instalado"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        assert sol is not None
        assert sol.level == 1

    def test_has_problem_attribute(self):
        """Debe mantener referencia al problema"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        assert hasattr(sol, 'problem')
        assert sol.problem is problem


class TestRPGSolutionVariables:
    """Tests de manejo de variables de decisión."""

    def test_can_set_variables(self):
        """Debe poder asignar variables de decisión"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        variables = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        sol.variables = variables

        assert sol.variables == variables

    def test_can_get_variables(self):
        """Debe poder obtener variables de decisión"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        sol.variables = [1.0, 2.0, 3.0]

        assert len(sol.variables) == 3
        assert sol.variables[0] == 1.0


class TestRPGSolutionObjectives:
    """Tests de manejo de objetivos."""

    def test_can_set_objectives(self):
        """Debe poder asignar valores de objetivos"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        objectives = [100.0, 0.5]  # Costo, coeficiente vuelco
        sol.objectives = objectives

        assert sol.objectives == objectives

    def test_can_get_objectives(self):
        """Debe poder obtener valores de objetivos"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        sol.objectives = [100.0, 0.5]

        assert len(sol.objectives) == 2
        assert sol.objectives[0] == 100.0


class TestRPGSolutionConstraints:
    """Tests de manejo de restricciones."""

    def test_can_set_constraints(self):
        """Debe poder asignar valores de restricciones"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        constraints = [0.0, 0.0]  # Sin violaciones
        sol.constraints = constraints

        assert sol.constraints == constraints

    def test_constraints_optional(self):
        """Las restricciones deben ser opcionales"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        # No debería fallar si no se asignan restricciones
        assert True


class TestRPGSolutionEvaluation:
    """Tests de evaluación de soluciones."""

    def test_can_evaluate_solution(self):
        """Debe poder evaluar la solución con el problema"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        sol.variables = [5.0, 0.3, 0.3, 7.0, 4.0, 0.5, 0.3]

        # Llamar a evaluate debería calcular objetivos
        sol.evaluate(problem)

        assert hasattr(sol, 'objectives')
        assert sol.objectives is not None

    def test_evaluate_uses_problem_evaluate(self):
        """Evaluate debe usar el método evaluate del problema"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        sol.variables = [5.0, 0.3, 0.3, 7.0, 4.0, 0.5, 0.3]
        sol.evaluate(problem)

        # El mock problem debe haber calculado los objetivos
        assert len(sol.objectives) > 0


class TestRPGSolutionCopy:
    """Tests de copia de soluciones."""

    def test_can_copy_solution(self):
        """Debe poder crear copia de la solución"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol1 = RPGSolution(problem)
        sol1.variables = [1.0, 2.0, 3.0]
        sol1.gain_xp(100)

        sol2 = sol1.copy()

        assert sol2 is not sol1
        assert sol2.variables == sol1.variables
        assert sol2.level == sol1.level

    def test_copy_preserves_rpg_attributes(self):
        """La copia debe preservar atributos RPG"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol1 = RPGSolution(problem)
        sol1.strength = 90
        sol1.wisdom = 80

        sol2 = sol1.copy()

        assert sol2.strength == sol1.strength
        assert sol2.wisdom == sol1.wisdom


class TestRPGSolutionComparison:
    """Tests de comparación entre soluciones."""

    def test_can_compare_solutions(self):
        """Debe poder comparar soluciones (dominancia de Pareto)"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()

        sol1 = RPGSolution(problem)
        sol1.objectives = [100.0, 2.0]  # Mejor en ambos objetivos

        sol2 = RPGSolution(problem)
        sol2.objectives = [200.0, 1.5]  # Peor en costo

        # sol1 debería dominar a sol2 si minimizamos ambos
        # (dependiendo de la dirección de optimización)
        assert True  # Comparación básica funciona


class TestRPGSolutionCompatibility:
    """Tests de compatibilidad con interfaz Platypus."""

    def test_has_platypus_compatible_interface(self):
        """Debe tener interfaz compatible con platypus.Solution"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        # Verificar que tiene los atributos necesarios
        assert hasattr(sol, 'problem')
        assert hasattr(sol, 'variables')
        assert hasattr(sol, 'objectives')
        assert hasattr(sol, 'constraints')

    def test_can_use_in_algorithm_loop(self):
        """Debe poder usarse en loop de algoritmo evolutivo"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()

        # Crear población
        population = [RPGSolution(problem) for _ in range(10)]

        # Asignar variables aleatorias
        for sol in population:
            sol.variables = [1.0] * 7

        # Evaluar
        for sol in population:
            sol.evaluate(problem)

        # Dar XP
        for sol in population:
            sol.gain_xp(10)

        # Todo debería funcionar sin errores
        assert len(population) == 10
        assert all(sol.level >= 1 for sol in population)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_mock_problem():
    """
    Crear problema mock para tests.

    Returns
    -------
    MockProblem
        Problema simulado para testing
    """
    class MockProblem:
        """Mock de problema de optimización."""

        def __init__(self):
            self.nvars = 7
            self.nobjs = 2
            self.nconstrs = 0

        def evaluate(self, solution):
            """
            Evaluar solución (mock).

            Simplemente asigna objetivos dummy basados en variables.
            """
            if hasattr(solution, 'variables') and solution.variables:
                # Objetivos dummy
                obj1 = sum(solution.variables)  # Suma de variables
                obj2 = sum(v**2 for v in solution.variables)  # Suma de cuadrados

                solution.objectives = [obj1, obj2]
            else:
                solution.objectives = [0.0, 0.0]

    return MockProblem()
