"""
Tests unitarios para el sistema de clases RPG.

Siguiendo TDD: estos tests se escriben ANTES de implementar el módulo.
El sistema de clases asigna arquetipos según perfil de atributos: cinco
clases, una por sector del glifo de perfil del artículo (formalismo art01,
S3.7). Las clases no llevan multiplicadores: no tienen poder causal.
"""
import pytest


ATTRS = ['strength', 'wisdom', 'endurance', 'dexterity', 'luck']

# Orden canónico de los sectores (el de CLASS_PRIMARY_ATTRIBUTES y el de la
# tabla de clases del artículo): STR-END, END-DEX, DEX-LCK, LCK-WIS, WIS-STR.
CLASS_PAIRS = {
    'warrior': ('strength', 'endurance'),
    'monk': ('endurance', 'dexterity'),
    'rogue': ('dexterity', 'luck'),
    'scout': ('luck', 'wisdom'),
    'paladin': ('wisdom', 'strength'),
}


def sheet_for(pair, high=(90, 85), low=20):
    """Hoja de atributos con el par primario en ``high`` y el resto en ``low``."""
    attrs = {name: low for name in ATTRS}
    attrs[pair[0]], attrs[pair[1]] = high
    return attrs


class TestRPGClassDefinitions:
    """Tests de definiciones de clases RPG."""

    def test_rpg_classes_exist(self):
        """Debe tener definidas las 5 clases del esquema de cinco sectores"""
        from core.rpg_classes import RPGClassType

        for name in ('WARRIOR', 'MONK', 'ROGUE', 'SCOUT', 'PALADIN'):
            assert hasattr(RPGClassType, name), name

    def test_class_descriptions_exist(self):
        """Cada clase debe tener descripción"""
        from core.rpg_classes import CLASS_DESCRIPTIONS

        assert isinstance(CLASS_DESCRIPTIONS, dict)
        assert list(CLASS_DESCRIPTIONS) == list(CLASS_PAIRS)
        for name in CLASS_PAIRS:
            assert CLASS_DESCRIPTIONS[name].strip(), name

    def test_class_primary_attributes(self):
        """Cada clase define su par primario, en orden canónico"""
        from core.rpg_classes import CLASS_PRIMARY_ATTRIBUTES

        assert list(CLASS_PRIMARY_ATTRIBUTES) == list(CLASS_PAIRS)
        for name, pair in CLASS_PAIRS.items():
            assert list(CLASS_PRIMARY_ATTRIBUTES[name]) == list(pair), name

    def test_sector_pairs_are_the_cycle_edges(self):
        """Los cinco pares son las aristas del ciclo de canales: cada canal
        aparece exactamente en dos pares y ningún par se repite"""
        from core.rpg_classes import CLASS_PRIMARY_ATTRIBUTES

        pairs = [tuple(sorted(v)) for v in CLASS_PRIMARY_ATTRIBUTES.values()]
        assert len(set(pairs)) == 5
        for channel in ATTRS:
            assert sum(channel in pair for pair in pairs) == 2, channel


class TestClassAssignment:
    """Tests de asignación de clase según atributos."""

    def test_assign_warrior_class(self):
        """Alta Strength + Endurance = Warrior"""
        from core.rpg_classes import assign_rpg_class

        assert assign_rpg_class(sheet_for(CLASS_PAIRS['warrior'])) == 'warrior'

    def test_assign_monk_class(self):
        """Alta Endurance + Dexterity = Monk"""
        from core.rpg_classes import assign_rpg_class

        assert assign_rpg_class(sheet_for(CLASS_PAIRS['monk'])) == 'monk'

    def test_assign_rogue_class(self):
        """Alta Dexterity + Luck = Rogue"""
        from core.rpg_classes import assign_rpg_class

        assert assign_rpg_class(sheet_for(CLASS_PAIRS['rogue'])) == 'rogue'

    def test_assign_scout_class(self):
        """Alta Luck + Wisdom = Scout"""
        from core.rpg_classes import assign_rpg_class

        assert assign_rpg_class(sheet_for(CLASS_PAIRS['scout'])) == 'scout'

    def test_assign_paladin_class(self):
        """Alta Wisdom + Strength = Paladin"""
        from core.rpg_classes import assign_rpg_class

        assert assign_rpg_class(sheet_for(CLASS_PAIRS['paladin'])) == 'paladin'

    def test_balanced_attributes_resolve_to_warrior(self):
        """Todos los canales iguales: empate total, gana el orden canónico"""
        from core.rpg_classes import assign_rpg_class

        assert assign_rpg_class({name: 50 for name in ATTRS}) == 'warrior'
        assert assign_rpg_class({name: 100 for name in ATTRS}) == 'warrior'


class TestClassBonuses:
    """Tests de rasgos por clase (sin multiplicadores)."""

    def test_class_bonus_has_no_numeric_values(self):
        """Ninguna clase devuelve multiplicadores: solo descripción"""
        from core.rpg_classes import get_class_bonus

        for name in CLASS_PAIRS:
            traits = get_class_bonus(name)
            assert traits, name
            for value in traits.values():
                assert not isinstance(value, (int, float)), (name, value)

    def test_class_bonus_description_matches_definitions(self):
        """La descripción corta existe para cada clase y es no vacía"""
        from core.rpg_classes import get_class_bonus

        for name in CLASS_PAIRS:
            assert get_class_bonus(name)['description'].strip(), name
        assert get_class_bonus('unknown') == {'description': ''}


class TestRPGSolutionClassIntegration:
    """Tests de integración con RPGSolution."""

    def test_solution_has_class_method(self):
        """RPGSolution debe tener método get_rpg_class()"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        assert hasattr(sol, 'get_rpg_class')

    def test_solution_get_class(self):
        """Debe retornar clase correcta según atributos"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        # Forzar perfil Warrior
        sol.strength = 90
        sol.endurance = 85
        sol.wisdom = 20
        sol.dexterity = 20
        sol.luck = 20

        assert sol.get_rpg_class() == 'warrior'

    def test_solution_class_bonus(self):
        """Debe poder obtener los rasgos de su clase, sin multiplicadores"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)

        sol.strength = 90
        sol.endurance = 85
        sol.wisdom = 20
        sol.dexterity = 20
        sol.luck = 20

        traits = sol.get_class_bonus()
        assert isinstance(traits, dict)
        assert 'description' in traits
        assert not any(isinstance(v, (int, float)) for v in traits.values())


class TestClassStatistics:
    """Tests de estadísticas por clase."""

    def test_count_classes_in_population(self):
        """Debe contar distribución de clases en población"""
        from core.rpg_classes import count_classes_in_population
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        population = [RPGSolution(problem) for _ in range(20)]

        class_counts = count_classes_in_population(population)

        assert isinstance(class_counts, dict)
        assert sum(class_counts.values()) == 20
        assert set(class_counts).issubset(set(CLASS_PAIRS))

    def test_get_dominant_class(self):
        """Debe identificar clase dominante en población"""
        from core.rpg_classes import get_dominant_class
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        population = []

        # Crear mayoría de Warriors
        for _ in range(10):
            sol = RPGSolution(problem)
            sol.strength = 90
            sol.endurance = 85
            population.append(sol)

        # Otros perfiles: nunca superan 175 (90 + 85) con el resto en [20, 80]
        for _ in range(5):
            sol = RPGSolution(problem)
            sol.wisdom = 90
            sol.dexterity = 85
            population.append(sol)

        assert get_dominant_class(population) == 'warrior'


class TestClassEvolution:
    """Tests de evolución de clases."""

    def test_class_can_change_with_leveling(self):
        """Clase puede cambiar al subir nivel y redistribuir atributos"""
        from core.rpg_solution import RPGSolution

        problem = create_mock_problem()
        sol = RPGSolution(problem)
        sol.get_rpg_class()  # Clase inicial

        # Subir muchos niveles (puede cambiar clase)
        for _ in range(50):
            sol.gain_xp(100)

        # Puede ser igual o diferente (depende de distribución aleatoria)
        assert sol.get_rpg_class() in list(CLASS_PAIRS)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_mock_problem():
    """Crear problema mock para testing."""
    class MockProblem:
        def __init__(self):
            self.nvars = 7
            self.nobjs = 2

    return MockProblem()
