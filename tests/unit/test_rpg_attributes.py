"""
Tests unitarios para el sistema de atributos RPG.

Siguiendo TDD: estos tests se escriben ANTES de implementar el módulo.
"""
import pytest


class TestAttributeConstants:
    """Tests de constantes de atributos."""

    def test_attribute_names_exist(self):
        """Debe tener lista de nombres de atributos"""
        from core.rpg_attributes import ATTRIBUTE_NAMES

        assert isinstance(ATTRIBUTE_NAMES, (list, tuple))
        assert len(ATTRIBUTE_NAMES) == 5
        assert 'strength' in ATTRIBUTE_NAMES
        assert 'wisdom' in ATTRIBUTE_NAMES

    def test_attribute_ranges(self):
        """Debe definir rangos min/max para atributos"""
        from core.rpg_attributes import ATTRIBUTE_MIN, ATTRIBUTE_MAX

        assert ATTRIBUTE_MIN == 20
        assert ATTRIBUTE_MAX == 100

    def test_points_per_level(self):
        """Debe definir puntos ganados por nivel"""
        from core.rpg_attributes import POINTS_PER_LEVEL

        assert POINTS_PER_LEVEL == 5


class TestAttributeDescriptions:
    """Tests de descripciones de atributos."""

    def test_attribute_descriptions_exist(self):
        """Cada atributo debe tener descripción"""
        from core.rpg_attributes import ATTRIBUTE_DESCRIPTIONS

        assert isinstance(ATTRIBUTE_DESCRIPTIONS, dict)
        assert 'strength' in ATTRIBUTE_DESCRIPTIONS
        assert 'wisdom' in ATTRIBUTE_DESCRIPTIONS

    def test_all_attributes_have_descriptions(self):
        """Todos los atributos deben tener descripción"""
        from core.rpg_attributes import (
            ATTRIBUTE_NAMES,
            ATTRIBUTE_DESCRIPTIONS
        )

        for attr in ATTRIBUTE_NAMES:
            assert attr in ATTRIBUTE_DESCRIPTIONS
            assert len(ATTRIBUTE_DESCRIPTIONS[attr]) > 0


class TestAttributeModifiers:
    """Tests de modificadores de atributos."""

    def test_get_mutation_strength_modifier(self):
        """Debe calcular modificador de fuerza de mutación"""
        from core.rpg_attributes import get_mutation_strength_modifier

        # Strength alta = modificador alto
        modifier_high = get_mutation_strength_modifier(90)
        modifier_low = get_mutation_strength_modifier(30)

        assert modifier_high > modifier_low
        assert 0 <= modifier_low <= 1
        assert 0 <= modifier_high <= 1

    def test_get_wisdom_learning_rate(self):
        """Debe calcular tasa de aprendizaje basada en sabiduría"""
        from core.rpg_attributes import get_wisdom_learning_rate

        rate_high = get_wisdom_learning_rate(90)
        rate_low = get_wisdom_learning_rate(30)

        assert rate_high > rate_low
        assert 0 <= rate_low <= 1
        assert 0 <= rate_high <= 1

    def test_get_endurance_survival_bonus(self):
        """Debe calcular bonus de supervivencia por resistencia"""
        from core.rpg_attributes import get_endurance_survival_bonus

        bonus_high = get_endurance_survival_bonus(90)
        bonus_low = get_endurance_survival_bonus(30)

        assert bonus_high > bonus_low
        assert bonus_low >= 0
        assert bonus_high >= 0

    def test_get_dexterity_precision(self):
        """Debe calcular precisión basada en destreza"""
        from core.rpg_attributes import get_dexterity_precision

        precision_high = get_dexterity_precision(90)
        precision_low = get_dexterity_precision(30)

        assert precision_high < precision_low  # Menor = más preciso
        assert precision_low > 0
        assert precision_high > 0

    def test_get_luck_probability_boost(self):
        """Debe calcular boost de probabilidad por suerte"""
        from core.rpg_attributes import get_luck_probability_boost

        boost_high = get_luck_probability_boost(90)
        boost_low = get_luck_probability_boost(30)

        assert boost_high > boost_low
        assert 0 <= boost_low <= 0.5
        assert 0 <= boost_high <= 0.5


class TestAttributeValidation:
    """Tests de validación de atributos."""

    def test_clamp_attribute(self):
        """Debe limitar atributo a rango válido"""
        from core.rpg_attributes import clamp_attribute

        assert clamp_attribute(150) == 100  # Tope superior
        assert clamp_attribute(10) == 20    # Tope inferior
        assert clamp_attribute(50) == 50    # Dentro de rango

    def test_is_valid_attribute_value(self):
        """Debe validar si valor es válido"""
        from core.rpg_attributes import is_valid_attribute_value

        assert is_valid_attribute_value(50) is True
        assert is_valid_attribute_value(20) is True
        assert is_valid_attribute_value(100) is True
        assert is_valid_attribute_value(150) is False
        assert is_valid_attribute_value(10) is False


class TestAttributeCategories:
    """Tests de categorización de atributos."""

    def test_get_attribute_category(self):
        """Debe categorizar atributo por valor"""
        from core.rpg_attributes import get_attribute_category

        assert get_attribute_category(90) == 'high'
        assert get_attribute_category(50) == 'medium'
        assert get_attribute_category(30) == 'low'

    def test_get_dominant_attribute_from_dict(self):
        """Debe identificar atributo dominante de dict"""
        from core.rpg_attributes import get_dominant_attribute_from_dict

        attrs = {
            'strength': 90,
            'wisdom': 40,
            'endurance': 50,
            'dexterity': 45,
            'luck': 35
        }

        dominant = get_dominant_attribute_from_dict(attrs)
        assert dominant == 'strength'


class TestAttributeDistribution:
    """Tests de distribución de atributos."""

    def test_distribute_points_randomly(self):
        """Debe distribuir puntos aleatoriamente"""
        from core.rpg_attributes import distribute_points_randomly

        initial = {
            'strength': 50,
            'wisdom': 50,
            'endurance': 50,
            'dexterity': 50,
            'luck': 50
        }

        result = distribute_points_randomly(initial.copy(), 10)

        # Suma debe aumentar en 10 (o menos si hay atributos en 100)
        initial_sum = sum(initial.values())
        result_sum = sum(result.values())

        assert result_sum > initial_sum
        assert result_sum <= initial_sum + 10

        # Ningún atributo debe superar 100
        for value in result.values():
            assert value <= 100

    def test_create_balanced_attributes(self):
        """Debe crear atributos balanceados"""
        from core.rpg_attributes import create_balanced_attributes

        attrs = create_balanced_attributes()

        assert len(attrs) == 5
        # Todos deberían estar cerca de 50
        for value in attrs.values():
            assert 45 <= value <= 55


class TestAttributeComparison:
    """Tests de comparación de atributos."""

    def test_compare_attribute_profiles(self):
        """Debe comparar perfiles de atributos"""
        from core.rpg_attributes import compare_attribute_profiles

        profile1 = {
            'strength': 90,
            'wisdom': 30,
            'endurance': 50,
            'dexterity': 40,
            'luck': 35
        }

        profile2 = {
            'strength': 30,
            'wisdom': 90,
            'endurance': 50,
            'dexterity': 40,
            'luck': 35
        }

        similarity = compare_attribute_profiles(profile1, profile2)

        assert 0 <= similarity <= 1
        assert similarity < 0.8  # No deberían ser muy similares

    def test_calculate_attribute_diversity(self):
        """Debe calcular diversidad de atributos"""
        from core.rpg_attributes import calculate_attribute_diversity

        # Atributos uniformes = baja diversidad
        uniform = {
            'strength': 50,
            'wisdom': 50,
            'endurance': 50,
            'dexterity': 50,
            'luck': 50
        }

        # Atributos diversos = alta diversidad
        diverse = {
            'strength': 20,
            'wisdom': 100,
            'endurance': 40,
            'dexterity': 80,
            'luck': 30
        }

        diversity_uniform = calculate_attribute_diversity(uniform)
        diversity_diverse = calculate_attribute_diversity(diverse)

        assert diversity_diverse > diversity_uniform
